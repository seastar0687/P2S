# IMPLEMENTATION PLAN - P2S HARDEN-3: Media Quality / Composition

This sprint is implemented from `docs/current/IMPLEMENTATION_PLAN_HARDEN3_MEDIA_QUALITY.md`.

## Contract

HARDEN-3 is a report-first media quality hardening sprint on top of MVP2C-thin outputs. It reads existing media artifacts and writes:

```text
runs/{project_id}/media_quality_report.json
```

It does not regenerate audio, re-render visuals, rewrite subtitles, normalize loudness, or recompose final video.

## Scope

- Add media quality schemas.
- Add report-only validators for audio, subtitles, visuals, segments, composition, and fallback quality.
- Add `media_quality_check` stage after `composition`.
- Add CLI support for `run --stage media_quality_check`.
- Add HARDEN-3 tests and smoke documentation.

## Explicit Non-Goals

- No ComfyUI / RunningHub / Stable Diffusion / AI image generation.
- No VRM, lip sync, Playwright template system, Streamlit UI, BGM, or full reviewer committee.
- No auto-fix loop in first pass.

## Acceptance

- `media_quality_report.json` is produced.
- Valid MVP2C-thin fake-backend smoke passes the gate.
- Missing final MP4 fails the gate.
- Full pytest regression passes.
- Post-HARDEN-3 route is explicitly chosen or deferred in `HARDEN3_STATUS.md`.
