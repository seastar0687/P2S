# MVP 0 Status

Last updated: 2026-05-06

## Completed

- Day 1: project scaffold, `requirements.txt`, `config.yaml`, package layout, persona/style placeholder folders.
- Day 2-3: Pydantic schemas and schema roundtrip tests.
- Day 4: `project_state.json` persistence with load/save/snapshot/list revisions.
- Day 5: minimal OpenAI-only `LLMService` with fake-client tests.
- Day 6: persona/style YAML loaders, package validation, deterministic compatibility check.
- Day 7: `seina` and `rigorous_science_short` package content plus reserved MVP directories/files.
- Day 8: PyMuPDF plain-text PDF extraction.
- Day 9: `BasePipeline` and `PaperSummaryPipeline` for setup and extraction.
- Day 10: Click CLI for `init`, `run`, `status`, `validate-personas`, and `validate-styles`.
- Day 11: sprint contract smoke tests and manual CLI smoke.
- Day 12: README/status documentation cleanup.
- Day 13-14: final MVP0 verification and cleanup.

## Current Verification

The final MVP0 automated verification passed:

```text
45 passed, 1 known pytest cache warning
```

Manual CLI smoke also passed with `runs/2026-05-06_manual_smoke`, producing `source.pdf`, `project_state.json`, one snapshot, and `extracted_text.md`.

## Not In MVP 0

- Claim extraction
- Script generation
- Reviewer committee
- TTS, image, video generation
- Streamlit or web UI
- OCR, section detection, figure/table extraction
- Provider switching beyond OpenAI in `LLMService`

## Next Step

MVP0 is ready for sprint review. If continuing into the next sprint, start MVP1 planning for claim extraction and evidence mapping. OpenAI API key setup is not needed until real LLM smoke tests or MVP1 LLM stages.
