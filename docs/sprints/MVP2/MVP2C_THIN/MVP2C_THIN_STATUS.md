# MVP2C-thin Status

Last updated: 2026-05-11

## Contract complete
- Media schemas, thin TTS, visual placeholder, segment composition, final composition, and pipeline stages implemented.
- `asset_generation` writes audio, visual, segment, media metadata, and media generation report artifacts.
- `composition` writes `final/output.mp4` and updates `project_state.final_video.path`.

## Current verification
- Focused MVP2C-thin tests passed.
- Full regression passed: `179 passed`.
- Fake-backend CLI smoke passed and produced `runs/mvp2c_thin_smoke/final/output.mp4`.

## Known quality gaps
- Visuals are deterministic placeholders, not polished media.
- Diagram, metaphor, and chart prompts fall back to text cards.
- Paper figures require extracted image paths; caption-only figures fall back to text cards.
- Real Edge-TTS smoke has not been run due to network constraints; the acceptance criterion for real smoke is conditionally accepted and must be re-run when network access is available.

## Hardening backlog
- HARDEN-3 must evaluate media timing, subtitle readability, segment composition, and audio loudness.
- HARDEN-3 must evaluate text-card / figure-card layout quality.
- HARDEN-3 must evaluate final MP4 compatibility across players and platforms.
- HARDEN-3 must evaluate fallback quality reporting so fallback paths remain visible.

## Recommended next step
- HARDEN-3: Media Quality / Composition.
