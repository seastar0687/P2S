# HARDEN-1 Status

Last updated: 2026-05-11

## Contract complete
- Extraction / figure / quality / evidence smoke schemas implemented.
- Extraction stage writes raw text, normalized text, sections, figures, tables, and quality report artifacts.
- Project state stores extraction artifact path references and quality summary instead of embedded section / figure / table content.
- Claim evidence review uses a shared evidence matching helper and writes `evidence_match_report.json`.
- Asset preparation reads `figures.json` when available and preserves old-project fallback behavior.

## Current verification
- Focused tests added for schema, text normalization, section detection, caption matching, figure metadata, evidence matching, integration, and smoke runner.
- Full regression should be run with `.\.venv-win\Scripts\python.exe -m pytest tests/ -v`.
- Manual smoke target remains `mvp1_real_smoke` or generated HARDEN-1 fixture PDFs.

## Known quality gaps
- Figure extraction is a deterministic PyMuPDF baseline and may miss vector-only figures.
- Table handling stores caption metadata first; full table structure extraction is out of scope.
- Section detection is regex / heading based and does not perform LLM layout understanding.
- Real-paper smoke can use synthetic PDFs when repo-safe real PDFs are unavailable.

## Hardening backlog
- HARDEN-2 remains active and should cover scene quality, presentation consistency, asset plan semantic/aesthetic quality, and scene/media mismatch.
- HARDEN-3 remains mandatory after MVP2C-thin for media timing, subtitle readability, composition, and loudness.

## Recommended next step
- Complete HARDEN-1 verification and manual smoke.
- Then proceed to MVP2C-thin, not MVP2C-full.
- Re-evaluate HARDEN-2 after MVP2C-thin / HARDEN-3 with concrete media outputs.
