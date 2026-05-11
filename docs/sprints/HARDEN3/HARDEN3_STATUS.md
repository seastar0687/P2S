# HARDEN-3 Status

Last updated: 2026-05-11

## Contract Complete

- Added HARDEN-3 media quality schemas and exports.
- Added report-only validators for audio, subtitles, visual PNG/layout baseline, segments, final composition, and fallback quality.
- Added `media_quality_check` stage with dependency on `composition == done`.
- Added CLI summary output for `media_quality_check`.
- Added `media_quality_report.json` output at project run root.
- Preserved report-only behavior: no media regeneration, no subtitle rewrite, no loudness normalization, no recomposition.

## Current Verification

- Focused HARDEN-3 tests: passed (`18 passed`).
- Manual smoke on `mvp2c_thin_smoke`: passed.
- Full regression: passed after implementation (`197 passed`).

## Smoke Summary

- Project: `mvp2c_thin_smoke`
- Command: `.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage media_quality_check --project mvp2c_thin_smoke`
- Stage status: `done`
- `pass_gate`: `true`
- Blocking issues: `0`
- Warnings: `2`
- Warning type: loudness unavailable in report-only HARDEN-3 baseline.
- Final MP4: exists, non-empty, ffprobe-readable, h264/aac/yuv420p.

## Known Quality Gaps

- Loudness is reported as unavailable; HARDEN-3 does not yet measure LUFS, peak, or silence ratio.
- Subtitle safe-area is estimated from character counts, not pixel-rendered bounding boxes.
- Text-card / figure-card layout quality is baseline-only; it validates PNG readability and coarse metadata, not visual polish.
- Figure-card sizing uses available metadata rather than rendered visual detection.
- Final MP4 compatibility is checked through best-effort codec metadata only; cross-player/platform playback remains manual.
- Fallback quality reporting is visible but does not trigger auto-repair or regeneration.

## Hardening Backlog

- Add real loudness and silence analysis.
- Add rendered subtitle/text bounding-box measurement.
- Add richer figure-card layout metrics.
- Add cross-player/platform final MP4 compatibility smoke.
- Add fallback quality trend reporting across runs.
- Add optional media quality dashboard in a later UI sprint.

## Recommended Next Step

Defer the route decision until this branch is reviewed with current MVP2C-thin artifacts. The clean next candidates remain:

- `MVP2C-full` if the priority is richer media generation.
- `MVP3 reviewer committee` if the priority is final-video factual and visual alignment review.
- `MVP4 inspection UI prototype` if the priority is manual inspection and artifact navigation.
