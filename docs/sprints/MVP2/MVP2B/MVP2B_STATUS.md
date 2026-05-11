# MVP 2B Status

Last updated: 2026-05-08

## Completed

- Added MVP2B asset plan schemas:
  - `AssetPlanBundle`
  - `SceneAssetPlan`
  - `TTSPlan`
  - `VisualAssetPlan`
  - `RenderPlan`
  - `AssetPlanQualityReport`
- Added deterministic `asset_preparation` service.
- Integrated `run --stage asset_preparation`.
- Preserved the MVP2A-2 contract by reading `project_state.active_scene_source`.
- Added fallback-with-warning behavior when a non-default active scene source is missing.
- Added visual planning rules for `none`, `paper_figure`, `diagram`, `metaphor_image`, `chart`, and required-without-type cases.
- Added TTS placeholder plans only; no real audio generation occurs.
- Added render placeholder plans only; no Playwright or ffmpeg work occurs.
- Added focused schema, service, pipeline, and CLI tests.

## Verification

Focused MVP2B tests:

```text
.\.venv-win\Scripts\python.exe -m pytest tests\test_asset_plan_schema.py tests\test_asset_preparation_service.py tests\test_asset_preparation_pipeline.py -v
```

Result:

```text
23 passed
```

Full regression:

```text
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

Result:

```text
139 passed
```

## Manual Real-Paper Smoke

Project:

```text
mvp1_real_smoke
```

Command:

```text
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage asset_preparation --project mvp1_real_smoke
```

Result:

```text
asset_preparation: done
asset_plan.json: created
scene_source: scenes_rewritten.json
scene_count: 7
plan_count: 7
warnings: 1
```

Warning:

```text
No figure metadata found; paper_figure selection will use fallback behavior.
```

This warning is expected for the current smoke project because extraction has no figure metadata.

## Not In MVP2B

- Real TTS generation
- Image generation
- VRM rendering
- lip sync or motion generation
- HTML frame rendering
- Playwright rendering
- ffmpeg segment generation
- final video composition
- Streamlit UI
- LLM-backed asset planning

## Next Step

Proceed to MVP2C after acceptance:

```text
asset_plan.json
→ audio/*.wav
→ assets/*.png|mp4
→ frames/*.png
→ segments/*.mp4
→ final/output.mp4
```
