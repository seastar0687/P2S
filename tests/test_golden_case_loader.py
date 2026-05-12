import shutil
from pathlib import Path

import pytest

from p2s_core.services.golden_case_loader import (
    GoldenCaseLoaderError,
    copy_input_to_temp,
    load_expected_findings,
    load_expected_gate,
    load_golden_cases,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "golden" / "final_review"


def test_loads_all_golden_cases():
    cases = load_golden_cases(GOLDEN_ROOT)
    assert {case.case_id for case in cases} >= {
        "good_case",
        "unsupported_claim",
        "overhype_warning",
        "overhype_blocking",
        "prompt_injection",
        "critical_prompt_injection",
        "visual_mismatch",
        "media_quality_fail",
        "missing_limitation",
        "arbiter_blocking_matrix",
    }


def test_load_expected_gate_and_findings():
    case = next(case for case in load_golden_cases(GOLDEN_ROOT) if case.case_id == "prompt_injection")
    case_dir = GOLDEN_ROOT / case.case_id
    assert load_expected_gate(case_dir, case).expected_status == "human_check"
    assert load_expected_findings(case_dir, case)[0].category == "prompt_injection"


def test_missing_expected_gate_fails_clearly(tmp_path: Path):
    source = GOLDEN_ROOT / "good_case"
    target = tmp_path / "good_case"
    shutil.copytree(source, target)
    (target / "expected_gate.json").unlink()
    with pytest.raises(GoldenCaseLoaderError, match="expected_gate"):
        load_golden_cases(tmp_path)


def test_temp_copy_does_not_mutate_source_fixture(tmp_path: Path):
    case = next(case for case in load_golden_cases(GOLDEN_ROOT) if case.case_id == "good_case")
    copied = copy_input_to_temp(GOLDEN_ROOT / case.case_id, case, tmp_path)
    (copied / "mutated.txt").write_text("changed", encoding="utf-8")
    assert not (GOLDEN_ROOT / case.case_id / case.input_dir / "mutated.txt").exists()
