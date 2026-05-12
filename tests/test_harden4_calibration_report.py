from pathlib import Path

from p2s_core.models import ReviewerCalibrationResult
from p2s_core.services.reviewer_calibration import run_calibration_suite


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "golden" / "final_review"


def test_calibration_report_counts_cases_and_passes_thresholds(tmp_path: Path):
    report = run_calibration_suite(GOLDEN_ROOT, temp_root=tmp_path)

    assert report.case_count >= 10
    assert report.failed_count == 0
    assert report.false_negative_risk_count == 0
    assert report.false_positive_risk_count <= 1
    assert report.pass_gate is True


def test_false_negative_and_false_positive_definitions_are_explicit():
    false_negative = ReviewerCalibrationResult(
        case_id="unsafe",
        passed=False,
        expected_status="human_check",
        actual_status="pass",
        unexpected_pass=True,
    )
    false_positive = ReviewerCalibrationResult(
        case_id="good",
        passed=False,
        expected_status="pass",
        actual_status="human_check",
        unexpected_reject=True,
    )

    assert false_negative.unexpected_pass is True
    assert false_positive.unexpected_reject is True
