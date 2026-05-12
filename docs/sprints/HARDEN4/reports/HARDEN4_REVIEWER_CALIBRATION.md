# HARDEN-4 Reviewer Calibration

Created at: 2026-05-12T08:16:07.535739+00:00

## Summary
- case_count: 10
- passed_count: 10
- failed_count: 0
- false_negative_risk_count: 0
- false_positive_risk_count: 0
- pass_gate: True

## Cases
- arbiter_blocking_matrix: pass (expected=reject, actual=reject)
- critical_prompt_injection: pass (expected=reject, actual=reject)
- good_case: pass (expected=pass, actual=pass)
- media_quality_fail: pass (expected=human_check, actual=human_check)
- missing_limitation: pass (expected=human_check, actual=human_check)
- overhype_blocking: pass (expected=human_check, actual=human_check)
- overhype_warning: pass (expected=pass, actual=pass)
- prompt_injection: pass (expected=human_check, actual=human_check)
- unsupported_claim: pass (expected=human_check, actual=human_check)
- visual_mismatch: pass (expected=human_check, actual=human_check)

## Reviewer Notes
- VisualAlignmentReviewer: HARDEN-4 v1 checks artifact and metadata consistency, not semantic image understanding.
