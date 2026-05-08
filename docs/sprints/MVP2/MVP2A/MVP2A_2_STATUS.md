# MVP 2A-2 Status

Last updated: 2026-05-08

## Completed In This Pass

- Day 1: Added `llm_quality_rewrite` to the project stage contract after `presentation_planning`.
- Day 1: Added `ProjectState.active_scene_source`, defaulting to `scenes.json` for new and migrated projects.
- Day 1: Added structured rewrite schemas:
  - `SceneRewritePatch`
  - `SceneRewriteResult`
- Day 2: Added `llm_quality_rewrite` service.
- Day 2: The service reads deterministic `scenes.json`, `claims.json`, `presentation_plan.json`, persona/style state, and the default presentation profile.
- Day 2: The LLM prompt exposes immutable skeleton fields and allows edits only to:
  - `voice_text`
  - `subtitle_text`
  - `asset_intent`
  - `notes_for_render`
- Day 3: Added patch guardrails for exact scene id coverage, duplicate/unknown scene ids, immutable field preservation, and required asset rules.
- Day 4: Re-runs MVP2A reviewers on the rewritten candidate:
  - `ScriptGroundingReviewer`
  - `StyleRuleReviewer`
  - `PresentationStructureReviewer`
  - `presentation_gate`
- Day 4: Writes `reviews/llm_quality_rewrite_review_rev001.json`.
- Day 4: Promotes `active_scene_source = "scenes_rewritten.json"` only when the rewrite gate passes.
- Day 5: Integrated CLI/pipeline stage:
  - `run --stage llm_quality_rewrite`
- Day 6: Added fake LLM tests for successful promotion, immutable-field attacks, unsupported claim wording, overlong subtitles, missing API key, dependency failures, and old-project migration.
- Day 7: Added this MVP2A-2 status document.

## Current Verification

Focused MVP2A-2 verification passed:

```text
.\.venv-win\Scripts\python.exe -m pytest tests\test_schema.py tests\test_llm_quality_rewrite.py tests\test_llm_quality_rewrite_pipeline.py tests\test_mvp2a_pipeline_smoke.py tests\test_presentation_gate.py -v
```

Current result:

```text
31 passed
```

Full regression also passed:

```text
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

Current result:

```text
116 passed
```

CLI status migration check:

```text
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp1_real_smoke
```

Relevant stage order:

```text
presentation_planning  done
llm_quality_rewrite    done
asset_preparation      pending
```

## Manual Real-Paper Smoke

Real LLM smoke completed and accepted:

- project: `mvp1_real_smoke`
- command: `.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage llm_quality_rewrite --project mvp1_real_smoke --force`
- result: `llm_quality_rewrite = done`
- active scene source: `scenes_rewritten.json`
- gate: `pass`
- regression: `116 passed`
- report: `docs/sprints/MVP2/MVP2A/MVP2A_2_REAL_LLM_SMOKE.md`

## Output Contracts

New outputs:

```text
runs/{project_id}/scenes_rewritten.json
runs/{project_id}/reviews/llm_quality_rewrite_review_rev001.json
```

Preserved baseline:

```text
runs/{project_id}/scenes.json
runs/{project_id}/presentation_plan.json
```

MVP2A-2 never overwrites `scenes.json` and never rewrites presentation ratios.

Code-version metadata from architecture v8.1 is provenance only: `project_state.code_version` and `stages.<stage>.code_version` record Git commit/branch/dirty state, while generated `runs/` artifacts remain outside Git.

## Not In MVP2A-2

- TTS generation
- image generation
- VRM rendering
- ffmpeg
- Streamlit UI
- `asset_plan.json`
- media artifacts
- LLM changes to scene skeleton fields
- LLM changes to presentation ratios

## Remaining MVP2A-2 Gap

- Rewrite prompt quality can be further calibrated with 2-3 additional real papers.
- The current implementation uses a single `scenes_rewritten.json` candidate artifact; multi-revision rewrite history is deferred.

## MVP2B Note

MVP2B must read `project_state.active_scene_source` instead of hardcoding `scenes.json`.

This lets MVP2B consume deterministic scenes by default, while automatically using `scenes_rewritten.json` when the LLM rewrite gate has passed.
