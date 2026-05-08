# MVP 1 Status

Last updated: 2026-05-06

## Completed In This Pass

- Added MVP1 claim-grounding schemas:
  - `PaperSection`
  - `PaperChunk`
  - `ExtractedPaper`
  - `ClaimExtractionResult`
  - `ClaimReviewBundle`
- Extended `PaperClaim` with `risk_flags`.
- Extended `GateDecision.target_type` to support claim/artifact review gates.
- Added section detection and chunking utility.
- Added structured-output retry and JSON fallback parsing to `LLMService`.
- Added claim extraction service and `claim_extraction_v1` prompt.
- Added deterministic MVP1 reviewers:
  - `ClaimEvidenceReviewer`
  - `PaperFidelityReviewer`
  - `Arbiter`
- Integrated `p2s run --stage claim_extraction`.
- Added claim review output:
  - `runs/{project_id}/claims.json`
  - `runs/{project_id}/reviews/claim_review_rev001.json`
- Added a clear CLI error when `OPENAI_API_KEY` is not configured for real LLM stages.

## Current Verification

Automated verification passed with the bundled Codex Python runtime:

```text
69 passed, 1 known pytest cache warning
```

The warning is the known Windows pytest cache permission issue already tracked in `ISSUES.md`.

## Not Yet Verified

- Real-paper `claim_extraction` content quality.

The current implementation intentionally does not require the key for unit tests or fake-client pipeline verification.

## Day 10 Real-Paper Smoke

Completed with `paper.pdf` as `mvp1_real_smoke`:

```text
extraction: done
claim_extraction: done
claims: 8
outputs:
  runs/mvp1_real_smoke/claims.json
  runs/mvp1_real_smoke/reviews/claim_review_rev001.json
```

The first gate result was `needs_review` because `ClaimEvidenceReviewer` found several evidence spans that did not directly match `extracted_text.md`. After improving reviewer normalization for PDF line breaks, hyphenation, special spacing, and short-quote fuzzy matching, the same `claims.json` now passes with zero failed reviews.

## Day 11 Cleanup

- Confirmed `pytest-cache-files-*` directories were manually removed once. The root cause is not fixed, so pytest may recreate them after later test runs; see `ISSUES.md`.
- Updated docs to clarify project-local `.env` usage for `OPENAI_API_KEY`.
- Added diagnostics for LLM request errors and increased default LLM timeout.
- Reduced real-paper claim extraction input to prioritized chunks under a source token budget to avoid oversized requests.
- Fixed async client cleanup after real OpenAI calls.
- Improved evidence matching so PDF line breaks do not cause false evidence failures.

## Remaining MVP1 Gap

The MVP1 claim-grounding loop is now minimally viable. Remaining quality work is no longer a blocker: broaden the golden dataset and add more real papers to calibrate reviewer false positives/negatives.

## MVP1 Hardening Backlog

These items are useful but not required for MVP1 completion:

- Golden bad cases directory:
  - Current reviewer tests cover missing evidence, unsupported evidence, overhype, PDF line breaks, hyphenation, and fuzzy matching.
  - Tier 2 reviewer logic is covered with inline fixtures in test code, so the behavior is tested.
  - Still missing the planned standalone `tests/golden/bad_claims/*.json` fixture layout from `IMPLEMENTATION_PLAN_MVP1_v2.md`; creating those JSON fixtures is a hardening/task-organization item, not an untested reviewer behavior gap.
- More real-paper smoke tests:
  - Current real smoke uses one paper: `paper.pdf`.
  - Run 2-3 more PDFs to calibrate reviewer false positives and false negatives.
- Section detection quality:
  - Current heading detection is regex-based and good enough for MVP1.
  - Complex publisher layouts may create repeated headings, column-order artifacts, or misplaced chunks.
- Claim type distribution:
  - Current real smoke produced 8 claims, but most were labeled `method`.
  - Future prompt/schema tuning should encourage a better mix of `contribution`, `method`, `result`, and `limitation` when supported by the paper.
- Pytest cache artifact:
  - `pytest-cache-files-*` can still reappear after test runs because of the known Windows cache permission issue.
  - This remains non-blocking and is tracked in `ISSUES.md`.

## MVP1 Completion Position

MVP1 should be considered minimally complete. The recommended next product step is either:

- `MVP1 hardening`: add golden fixtures and 2-3 more real-paper smoke cases.
- `MVP2A`: start claim-grounded script generation from `claims.json`.

## Next Step

```bash
python -m p2s_core.cli status --project mvp1_real_smoke
```

Expected result: `extraction` and `claim_extraction` are both `done`.
