from pathlib import Path

from p2s_core.services.golden_case_loader import load_golden_cases
from p2s_core.services.reviewer_calibration import run_calibration_case


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "golden" / "final_review"


def test_missing_visual_artifact_blocks(tmp_path: Path):
    case = next(case for case in load_golden_cases(GOLDEN_ROOT) if case.case_id == "visual_mismatch")
    result = run_calibration_case(GOLDEN_ROOT / case.case_id, case, temp_root=tmp_path)
    assert result.passed is True
    assert result.actual_status == "human_check"


def test_media_quality_fail_does_not_pass(tmp_path: Path):
    case = next(case for case in load_golden_cases(GOLDEN_ROOT) if case.case_id == "media_quality_fail")
    result = run_calibration_case(GOLDEN_ROOT / case.case_id, case, temp_root=tmp_path)
    assert result.passed is True
    assert result.actual_status == "human_check"
