from pathlib import Path

from p2s_core.services.golden_case_loader import load_golden_cases
from p2s_core.services.reviewer_calibration import run_calibration_case


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "golden" / "final_review"


def _run(case_id: str, tmp_path: Path):
    case = next(case for case in load_golden_cases(GOLDEN_ROOT) if case.case_id == case_id)
    return run_calibration_case(GOLDEN_ROOT / case.case_id, case, temp_root=tmp_path)


def test_overhype_warning_passes_gate(tmp_path: Path):
    result = _run("overhype_warning", tmp_path)
    assert result.passed is True
    assert result.actual_status == "pass"


def test_overhype_blocking_requires_human_check(tmp_path: Path):
    result = _run("overhype_blocking", tmp_path)
    assert result.passed is True
    assert result.actual_status == "human_check"


def test_prompt_injection_blocks(tmp_path: Path):
    result = _run("prompt_injection", tmp_path)
    assert result.passed is True
    assert result.actual_status == "human_check"


def test_critical_prompt_injection_rejects(tmp_path: Path):
    result = _run("critical_prompt_injection", tmp_path)
    assert result.passed is True
    assert result.actual_status == "reject"
