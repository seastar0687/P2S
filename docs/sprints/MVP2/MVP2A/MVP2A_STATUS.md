# MVP 2A Status

Last updated: 2026-05-08

## Completed In This Pass

- Day 1: Added MVP2A output schemas:
  - `NarrativeArcItem`
  - `NarrativePlan`
  - `ScenesBundle`
  - `PresentationReviewBundle`
- Day 1: Extended review targets so presentation-stage reviews can use `target_type="presentation"`.
- Day 2: Completed `presenter_first_default` presentation profile package examples.
- Day 2: Added presentation profile loading and validation helpers.
- Day 3: Added deterministic `narrative_planning` service.
- Day 4: Integrated `p2s run --stage narrative_planning`.
- Day 5: Added deterministic `presentation_planning` service.
- Day 6: Added MVP2A deterministic reviewers:
  - `ScriptGroundingReviewer`
  - `StyleRuleReviewer`
  - `PresentationStructureReviewer`
- Day 7: Added `presentation_gate` and `PresentationReviewBundle` output.
- Day 8: Integrated `p2s run --stage presentation_planning`.
- Day 9: Added fake-project MVP2A pipeline smoke tests.
- Day 11: Added this MVP2A status document.
- Day 12: Added non-destructive stage-key migration for older MVP1 projects missing current MVP2A stage keys.

## Current Verification

Automated verification passed with the project-local Windows runtime:

```text
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

Current result:

```text
108 passed
```

## Manual Real-Paper Smoke

Manual smoke status:

```text
project: mvp1_real_smoke
narrative_planning: done
presentation_planning: done
scene_count: 7
presentation_gate: pass
asset_plan.json: not created
```

Expected MVP2A outputs:

```text
runs/{project_id}/narrative_plan.json
runs/{project_id}/scenes.json
runs/{project_id}/presentation_plan.json
runs/{project_id}/reviews/presentation_review_rev001.json
```

## Not In MVP2A

- TTS generation
- Edge-TTS integration
- VRM rendering
- lip sync or motion generation
- image generation
- ComfyUI / RunningHub calls
- HTML frame rendering
- ffmpeg segment generation
- final video composition
- Streamlit UI
- `asset_plan.json`
- auto-fix loop
- LLM-backed narrative or presentation planning
- persona acquisition

## Remaining MVP2A Gap

MVP2A is deterministic-first. The generated text is intentionally simple and conservative. Content quality tuning and LLM-backed planning are deferred until after the stable artifact and review contracts are accepted.

## MVP2A Hardening Backlog

- Add golden JSON fixtures for presentation bad cases.
- Add 2-3 additional real-paper smoke runs.
- Add configurable presentation profile selection when more profiles exist.
- Replace deterministic wording with LLM-backed planning behind the same schemas.
- Calibrate `StyleRuleReviewer` thresholds with real generated scenes.
- MVP2A-2 LLM quality rewrite is now implemented as a separate post-presentation stage; see `docs/sprints/MVP2/MVP2A_2_STATUS.md`.

## Known Issues

- The Windows pytest cache permission issue remains mitigated and tracked in `docs/current/ISSUES.md`.
- Use `.\.venv-win\Scripts\python.exe` for all tests and CLI commands, per `docs/current/WINDOWS_ENVIRONMENT.md`.

## Next Step

After MVP2A acceptance, proceed to MVP2B:

```text
presentation_plan.json + scenes.json
→ asset_plan.json
→ TTS plan placeholders
→ visual asset preparation
```

MVP2B should read `project_state.active_scene_source` rather than hardcoding `scenes.json`, because MVP2A-2 may promote `scenes_rewritten.json` after gate approval.

Do not begin actual media generation until MVP2C.
