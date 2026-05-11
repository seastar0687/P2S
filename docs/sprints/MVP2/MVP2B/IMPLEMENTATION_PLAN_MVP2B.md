# MVP2B Implementation Plan

MVP2B implements deterministic asset and render preparation for projects that have passed MVP2A presentation planning.

## Scope

- Read `project_state.active_scene_source`.
- Build `asset_plan.json` from the active scenes, `presentation_plan.json`, `claims.json`, persona voice settings, and optional figure metadata.
- Produce TTS placeholders, visual placeholders, fallback chains, render template hints, and deterministic quality warnings.
- Do not call LLMs, TTS, image generation, Playwright, ffmpeg, or any real media backend.

## Key Artifacts

- `p2s_core/models/asset_plan.py`
- `p2s_core/services/asset_preparation.py`
- `runs/{project_id}/asset_plan.json`

## Stage Contract

`asset_preparation` requires `presentation_planning == done`, but does not require `llm_quality_rewrite == done`.

Scene source resolution:

```text
requested = project_state.active_scene_source or "scenes.json"
if requested exists: use it
elif requested != "scenes.json" and scenes.json exists: use scenes.json with warning
else: fail
```

The active scene ids must exactly match `presentation_plan.json`.

## Acceptance Checks

- Every scene has exactly one `SceneAssetPlan`.
- Every scene has a TTS placeholder plan.
- `tts_plan.text == scene.voice_text`.
- Visual plans respect `asset_policy` and `asset_type_hint`.
- Output placeholders are set for all resolved visual sources except `none`.
- Required visual fallbacks produce explicit warnings.
- `asset_plan.quality_report` includes policy counts and resolved source counts.
- CLI supports `run --stage asset_preparation`.
- Full regression passes with the project-local Windows runtime.
