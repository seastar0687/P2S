# MVP2A-2 Real LLM Smoke

Date: 2026-05-08

## Command

```text
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage llm_quality_rewrite --project mvp1_real_smoke --force
```

The first sandboxed attempt failed with a network `ConnectError`. The first real network attempt reached the API but was rejected because the LLM did not echo the expected `project_id`. The prompt/payload was tightened to include and require the exact `project_id`, then the smoke was rerun with `--force`.

## Result

```text
project id: mvp1_real_smoke
stage result: done
active_scene_source: scenes_rewritten.json
decision: accepted
```

Created outputs:

```text
runs/mvp1_real_smoke/scenes_rewritten.json
runs/mvp1_real_smoke/reviews/llm_quality_rewrite_review_rev001.json
```

Review gate:

```text
status: pass
summary: Presentation gate passed.
review_count: 15
blocking_issues: []
human_notes: []
```

## Safety Checks

```text
scenes.json exists: yes
presentation_plan.json exists: yes
scene_count_original: 7
scene_count_rewritten: 7
immutable_mismatches: []
text_changed_scenes: scene_001..scene_007
asset_plan.json created: no
audio/ created: no
assets/ created: no
frames/ created: no
segments/ created: no
final/ created: no
```

`runs/` remains ignored by Git and was not committed.

## Regression

```text
.\.venv-win\Scripts\python.exe -m pytest tests\ -v
```

Result:

```text
116 passed
```

## Notes

- The real smoke was accepted after the prompt/payload fix.
- `project_state.code_version` and `stages.llm_quality_rewrite.code_version` recorded `05989ff main dirty`, which is expected because local code/docs changes were not committed before the smoke.
- MVP2B must consume `project_state.active_scene_source`, which now points to `scenes_rewritten.json` for this project.

