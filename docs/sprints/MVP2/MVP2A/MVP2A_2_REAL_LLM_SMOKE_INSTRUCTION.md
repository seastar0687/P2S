# MVP2A-2 Real LLM Smoke Test Instruction

> Purpose: Verify that the implemented `llm_quality_rewrite` stage can run once with a real LLM API, produce valid rewrite artifacts, re-run MVP2A reviewers, and update `project_state.active_scene_source` only when the gate passes.

---

## 0. Context

MVP2A is already accepted. It produces deterministic presentation planning outputs:

```text
claims.json
→ narrative_plan.json
→ scenes.json
→ presentation_plan.json
→ reviews/presentation_review_rev001.json
```

MVP2A-2 is an optional post-presentation quality rewrite stage:

```text
scenes.json
→ llm_quality_rewrite
→ scenes_rewritten.json
→ reviews/llm_quality_rewrite_review_rev001.json
```

The LLM is allowed to improve only:

```text
voice_text
subtitle_text
asset_intent
notes_for_render
```

The LLM must not modify immutable skeleton fields:

```text
scene_id
claim_ids
purpose
presenter_mode
visual_focus
asset_policy
asset_type_hint
background_mode
presentation ratios
```

If the rewrite passes review, promote:

```text
project_state.active_scene_source = "scenes_rewritten.json"
```

If it fails review, keep:

```text
project_state.active_scene_source = "scenes.json"
```

---

## 1. Preconditions

Run this from the P2S project root.

Use the Windows project-local environment:

```powershell
.\.venv-win\Scripts\python.exe
```

Required project:

```text
runs/mvp1_real_smoke/
```

This project should already have MVP2A outputs:

```text
runs/mvp1_real_smoke/claims.json
runs/mvp1_real_smoke/scenes.json
runs/mvp1_real_smoke/presentation_plan.json
runs/mvp1_real_smoke/reviews/presentation_review_rev001.json
```

Check that `OPENAI_API_KEY` is available through `.env` or environment variable.

Do not commit `runs/` to Git.

---

## 2. Commands to Run

### 2.1 Optional: verify current status

```powershell
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp1_real_smoke
```

Expected relevant stage order:

```text
presentation_planning  done
llm_quality_rewrite    pending
asset_preparation      pending
```

### 2.2 Run real LLM smoke

```powershell
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage llm_quality_rewrite --project mvp1_real_smoke
```

### 2.3 Check status after run

```powershell
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp1_real_smoke
```

### 2.4 Run regression tests after smoke

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

---

## 3. Expected Outputs

After the smoke command, these files may be created:

```text
runs/mvp1_real_smoke/scenes_rewritten.json
runs/mvp1_real_smoke/reviews/llm_quality_rewrite_review_rev001.json
```

`scenes.json` must never be overwritten.

`presentation_plan.json` must not be rewritten.

No MVP2B or MVP2C outputs should be created:

```text
asset_plan.json
audio/
assets/
frames/
segments/
final/output.mp4
```

---

## 4. Accepted Outcomes

### Outcome A — Pass / promoted

Condition:

```text
llm_quality_rewrite = done
```

Expected:

```text
project_state.active_scene_source = "scenes_rewritten.json"
```

Meaning:

```text
The LLM rewrite passed all guardrails and reviewer gates.
MVP2B should consume scenes_rewritten.json through active_scene_source.
```

### Outcome B — Needs review or rejected / safe fallback

Condition:

```text
llm_quality_rewrite = needs_review
```

or

```text
llm_quality_rewrite = rejected
```

Expected:

```text
project_state.active_scene_source = "scenes.json"
```

Meaning:

```text
The LLM rewrite ran but did not pass review.
This is acceptable. The deterministic MVP2A output remains active.
Record reviewer findings in the status note.
```

### Outcome C — Failed / needs debugging

Condition:

```text
llm_quality_rewrite = failed
```

Likely causes:

```text
OPENAI_API_KEY missing
LLM request failed
timeout
LLM returned malformed JSON
schema validation failed
patch guardrail rejected unexpected structure
```

Meaning:

```text
This requires debugging before accepting MVP2A-2.
Do not proceed as if LLM rewrite is accepted.
```

---

## 5. Required Checks

After the smoke, verify:

```text
□ scenes.json still exists and was not overwritten.
□ presentation_plan.json still exists and was not rewritten.
□ If scenes_rewritten.json exists, it preserves immutable fields.
□ reviews/llm_quality_rewrite_review_rev001.json exists if the stage reached review.
□ project_state.active_scene_source is correct:
   - scenes_rewritten.json only if gate passed
   - scenes.json otherwise
□ No asset_plan.json was created.
□ No audio/assets/frames/segments/final video outputs were created.
□ Full tests still pass.
```

---

## 6. Status Update Required

After running, update or create a short status note, for example:

```text
docs/sprints/MVP2/MVP2A_2_REAL_LLM_SMOKE.md
```

Include:

```text
date
command used
project id
stage result: done / needs_review / rejected / failed
active_scene_source after run
created outputs
review gate summary
any error message
test result after smoke
decision: accepted / accepted with fallback / needs fix
```

---

## 7. Decision Rule

Use this rule:

```text
If stage = done and active_scene_source = scenes_rewritten.json:
  MVP2A-2 real LLM smoke accepted.

If stage = needs_review or rejected and active_scene_source = scenes.json:
  MVP2A-2 smoke completed with safe fallback.
  MVP2B may proceed if this behavior is documented.

If stage = failed:
  Fix before accepting MVP2A-2.
```

---

## 8. Reminder for MVP2B

MVP2B must not hardcode:

```text
scenes.json
```

It must read:

```text
project_state.active_scene_source
```

so that it can consume either deterministic scenes or LLM-rewritten scenes.
