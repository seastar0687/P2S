# IMPLEMENTATION_NOTE_CODE_VERSION_METADATA.md

> Version: v0.1  
> Status: Hardening Note  
> Depends on: `P2S_redesign_architecture_v8.1.md`（存放於 `docs/current/`）  
> Scope: Add code-version provenance metadata to `project_state.json` and each executed stage.  
> Not a new MVP stage.

---

## 0. Purpose

P2S currently keeps code, tests, docs, and templates in Git, while generated project artifacts live under `runs/{project_id}/` and are intentionally excluded from Git. This is correct, because `runs/` may contain PDFs, extracted paper text, LLM outputs, review results, images, audio, video, API responses, and possibly sensitive or copyrighted material.

However, generated artifacts still need provenance:

```text
Which code commit produced this claims.json / scenes.json / presentation_plan.json?
Was the working tree clean?
Which branch was used?
Did different stages run under different commits?
```

This note defines a lightweight code-version tracking mechanism for `project_state.json`.

---

## 1. Scope Boundary

### 1.1 In Scope

Implement:

```text
ProjectState.code_version
StageState.code_version
capture_code_version() helper
stage-runner integration
tests for git / no-git / dirty-safe behavior
old-project migration compatibility
```

### 1.2 Out of Scope

Do not implement:

```text
✗ Uploading runs/ to GitHub
✗ Committing generated artifacts
✗ DVC / MLflow / Weights & Biases integration
✗ Database-backed artifact tracking
✗ Hashing every output artifact
✗ Full reproducibility lockfile
✗ Blocking stage execution when dirty=true
```

This is provenance metadata, not artifact version control.

---

## 2. Schema Changes

### 2.1 Add `CodeVersion`

Recommended location:

```text
p2s_core/models/project_state.py
```

Schema:

```python
class CodeVersion(BaseModel):
    commit: str | None = None
    branch: str | None = None
    dirty: bool | None = None
    captured_at: str
    source: Literal["git", "unknown"] = "git"
```

Field meanings:

```text
commit      = current git commit hash, preferably short hash or full hash consistently.
branch      = current branch name.
dirty       = whether there are uncommitted changes.
captured_at = UTC timestamp when metadata was captured.
source      = "git" if detected from git; "unknown" if git is unavailable or not a repo.
```

### 2.2 Update `ProjectState`

Add:

```python
code_version: CodeVersion | None = None
```

Meaning:

```text
ProjectState.code_version records the most recent code version observed when the state was saved or migrated.
```

### 2.3 Update `StageState`

Add:

```python
code_version: CodeVersion | None = None
```

Meaning:

```text
StageState.code_version records the code version that executed that specific stage.
```

When debugging stage outputs, prefer `stages.<stage_name>.code_version` over the top-level `project_state.code_version`.

---

## 3. Implementation Details

### 3.1 Helper Module

Recommended location:

```text
p2s_core/services/code_version.py
```

Alternative acceptable location:

```text
p2s_core/utils/git_info.py
```

Minimum API:

```python
def capture_code_version(repo_root: Path | None = None) -> CodeVersion:
    """Return current git metadata. Never raises for normal no-git cases."""
```

Expected behavior:

```text
- Use subprocess to call git.
- Resolve repo root from current working directory if not provided.
- commit: `git rev-parse --short HEAD`（統一用 7-char short hash，與 CLI status 顯示格式一致）
- branch: `git rev-parse --abbrev-ref HEAD`.
  detached HEAD 狀態（例如 CI shallow clone）會回傳 "HEAD"，此時 branch = "HEAD" 視為合法值，不視為錯誤。
- dirty: true if `git status --porcelain` has output.
- On any expected failure, return CodeVersion(source="unknown", commit=None, branch=None, dirty=None, captured_at=now).
```

Expected failures include:

```text
- git command not installed
- current directory is not a git repo
- subprocess timeout
- permission error
- detached worktree oddities that prevent branch detection
```

No expected failure should crash the P2S pipeline.

---

## 4. Stage Runner Integration

When running a stage:

```text
1. Capture code version before the stage starts.
2. Write it into `stages.<stage_name>.code_version`.
3. Execute the stage.
4. Save outputs and project_state as usual.
```

Recommended pseudocode:

```python
def run_stage(project_id: str, stage_name: str) -> None:
    state = load_state(project_id)
    code_version = capture_code_version()

    stage = state.ensure_stage(stage_name)
    stage.code_version = code_version
    stage.status = "running"
    stage.started_at = utc_now()
    save_state(state)

    try:
        outputs = execute_stage(stage_name, state)
        stage.status = "done"
        stage.output_paths = outputs
        stage.finished_at = utc_now()
    except ExpectedStageDependencyError as exc:
        stage.status = "failed"
        stage.error = str(exc)
        raise
    finally:
        state.code_version = capture_code_version()
        save_state(state)
```

`dirty=true` must not block execution. It is a warning/provenance signal only.

---

## 5. Migration Behavior

Old projects may not contain either field. They must remain readable.

Migration rule:

```text
If ProjectState.code_version is missing:
  set to None or capture current code_version during status migration.

If any StageState.code_version is missing:
  leave as None unless that stage is executed again.
```

Do not infer historical stage commits retroactively. It is better to leave unknown than to write misleading metadata.

---

## 6. CLI / Status Display

`p2s status` may show a compact code version summary:

```text
Project code version: 05989ff main clean

Stages:
  extraction              done        05989ff clean
  claim_extraction        done        05989ff clean
  presentation_planning   done        abc1234 dirty
  llm_quality_rewrite     pending     -
```

This display is useful but optional for first implementation. The schema and stage-runner write are required.

---

## 7. Tests

Add or update tests:

```text
tests/test_code_version.py
tests/test_project_state_migration.py
tests/test_stage_code_version.py
```

Required test cases:

```text
T1. capture_code_version() returns a CodeVersion object and never crashes.
T2. In a git repo, source should be "git" and commit should be non-empty (7-char short hash). Branch may be "HEAD" in detached HEAD environments (e.g. CI shallow clone); this is valid and should not fail the test.
T3. In a simulated no-git environment, source should be "unknown" and pipeline should not crash.
T4. Stage execution writes stages.<stage>.code_version.
T5. Old project_state without code_version loads successfully.
T6. Old StageState without code_version loads successfully.
T7. Dirty state is recorded when detectable, but does not fail the stage.
```

No test should require network access.

---

## 8. Acceptance Checklist

This hardening task is accepted when:

```text
□ ProjectState has optional code_version.
□ StageState has optional code_version.
□ capture_code_version() exists and handles no-git cases safely.
□ Stage runner writes code_version for executed stages.
□ Existing MVP0/MVP1/MVP2A tests still pass.
□ Old project_state files still load.
□ runs/ remains excluded from Git.
□ status docs mention that code_version is provenance metadata, not artifact sync.
```

---

## 9. One-Sentence Summary

> Code-version metadata lets every generated P2S artifact be traced back to the code commit that produced it, without committing `runs/` artifacts to Git.
