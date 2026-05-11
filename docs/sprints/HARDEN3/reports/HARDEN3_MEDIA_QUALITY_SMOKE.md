# HARDEN-3 Media Quality Smoke

Date: 2026-05-11

## Command

```powershell
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage media_quality_check --project mvp2c_thin_smoke
```

## Result

```text
Running stage: media_quality_check
  -> status: done
  -> media_quality_report.json
  -> pass_gate: True
  -> blocking_issues: 0
  -> warnings: 2
```

## Report Highlights

- Audio: two WAV files exist, are non-empty, and have readable duration.
- Subtitles: two subtitles pass estimated readability checks.
- Visuals: two PNG text cards exist and match expected resolution.
- Segments: two MP4 segments exist, are non-empty, and have ffprobe-readable duration.
- Composition: `final/output.mp4` exists, is non-empty, ffprobe-readable, and reports h264/aac/yuv420p.
- Fallback: `fallback_ratio = 0.0`, `quality_level = good`.

## Warnings

- Loudness metrics are unavailable in the report-only HARDEN-3 baseline.

## Acceptance Note

The fake-backend MVP2C-thin smoke project passes HARDEN-3 media quality gate. Real Edge-TTS remains covered by MVP2C-thin conditional smoke status and is not re-run by this report-only stage.
