# HARDEN-4 Status

Last updated: 2026-05-12

## Contract complete
- Reviewer calibration schemas and severity ordering are implemented.
- Golden final_review cases exist under `tests/golden/final_review/`.
- Golden case loader and calibration service are implemented with temp-copy fixture isolation.
- Manual calibration runner writes JSON and Markdown reports under `docs/sprints/HARDEN4/reports/`.

## Current verification
- Focused HARDEN-4 tests passed:
  `.\.venv-win\Scripts\python.exe -m pytest tests/test_reviewer_calibration_schema.py tests/test_golden_case_loader.py tests/test_harden4_calibration_report.py tests/test_harden4_final_arbiter_calibration.py tests/test_harden4_paper_fidelity_calibration.py tests/test_harden4_devil_advocate_calibration.py tests/test_harden4_visual_alignment_calibration.py tests/test_harden4_prompt_injection_expansion.py -v`
  -> `18 passed`
- Full regression passed:
  `.\.venv-win\Scripts\python.exe -m pytest tests/ -v`
  -> `247 passed`
- Manual calibration passed:
  `.\.venv-win\Scripts\python.exe scripts\run_harden4_calibration.py`
  -> `case_count: 10`, `passed_count: 10`, `failed_count: 0`, `false_negative_risk_count: 0`, `false_positive_risk_count: 0`, `pass_gate: True`
- Manual final_review smoke still passes:
  `.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage final_review --project mvp2c_thin_smoke --force`
  -> `status: done`, `gate_status: pass`, `blocking_issues: 0`, `warnings: 3`
  -> `reviews\final_review_rev002.json`, `reviews\final_gate_decision_rev002.json`
- HARDEN-4 acceptance status: accepted for HARDEN-4 v1 reviewer calibration.

## Known quality gaps
- Visual alignment remains metadata/artifact based, not semantic image understanding.
- Golden fixtures are small surgical cases, not a real-paper benchmark set.
- LLM reviewer calibration remains out of scope; tests use deterministic reviewers only.

## Hardening backlog
- Real-paper reviewer calibration remains future work.
- Add richer semantic visual alignment once image understanding is introduced.
- Expand prompt-injection and unsupported-claim golden cases as real failures are found.

## Recommended next step
- Proceed to MVP4 inspection UI prototype unless project priority shifts back to MVP2C-full media generation.
