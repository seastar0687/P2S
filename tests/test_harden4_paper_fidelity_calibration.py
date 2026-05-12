from pathlib import Path

from p2s_core.services.golden_case_loader import copy_input_to_temp, load_golden_cases
from p2s_core.services.reviewer_calibration import run_calibration_case, review_fixture


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "golden" / "final_review"


def _case(case_id: str):
    return next(case for case in load_golden_cases(GOLDEN_ROOT) if case.case_id == case_id)


def test_missing_limitation_is_caught(tmp_path: Path):
    case = _case("missing_limitation")
    result = run_calibration_case(GOLDEN_ROOT / case.case_id, case, temp_root=tmp_path)
    assert result.passed is True
    assert result.actual_status == "human_check"


def test_good_case_has_no_blocking_issue(tmp_path: Path):
    case = _case("good_case")
    run_dir = copy_input_to_temp(GOLDEN_ROOT / case.case_id, case, tmp_path)
    bundle, status = review_fixture(run_dir)
    assert status == "pass"
    assert bundle.blocking_issues == []
