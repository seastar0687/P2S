from __future__ import annotations

import shutil
from pathlib import Path

from p2s_core.models import ExpectedGateOutcome, ExpectedReviewerFinding, GoldenReviewCase


class GoldenCaseLoaderError(ValueError):
    """Raised when a HARDEN-4 golden case is missing or invalid."""


def load_golden_cases(root: Path | str) -> list[GoldenReviewCase]:
    root = Path(root)
    case_paths = sorted(root.glob("*/case.json"))
    cases: list[GoldenReviewCase] = []
    for path in case_paths:
        case = GoldenReviewCase.model_validate_json(path.read_text(encoding="utf-8"))
        _validate_case_paths(path.parent, case)
        cases.append(case)
    if not cases:
        raise GoldenCaseLoaderError(f"No golden cases found under {root}")
    return cases


def load_expected_gate(case_dir: Path, case: GoldenReviewCase) -> ExpectedGateOutcome:
    return ExpectedGateOutcome.model_validate_json(
        (case_dir / case.expected_gate_path).read_text(encoding="utf-8")
    )


def load_expected_findings(case_dir: Path, case: GoldenReviewCase) -> list[ExpectedReviewerFinding]:
    if not case.expected_findings_path:
        return []
    raw = (case_dir / case.expected_findings_path).read_text(encoding="utf-8")
    import json

    data = json.loads(raw)
    if not isinstance(data, list):
        raise GoldenCaseLoaderError(f"expected findings must be a list: {case_dir / case.expected_findings_path}")
    return [ExpectedReviewerFinding.model_validate(item) for item in data]


def copy_input_to_temp(case_dir: Path, case: GoldenReviewCase, temp_root: Path) -> Path:
    source = case_dir / case.input_dir
    target = temp_root / case.case_id
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def _validate_case_paths(case_dir: Path, case: GoldenReviewCase) -> None:
    input_dir = case_dir / case.input_dir
    if not input_dir.is_dir():
        raise GoldenCaseLoaderError(f"input_dir not found for {case.case_id}: {input_dir}")
    expected_gate = case_dir / case.expected_gate_path
    if not expected_gate.exists():
        raise GoldenCaseLoaderError(f"expected_gate.json not found for {case.case_id}: {expected_gate}")
    load_expected_gate(case_dir, case)
    if case.expected_findings_path:
        expected_findings = case_dir / case.expected_findings_path
        if not expected_findings.exists():
            raise GoldenCaseLoaderError(
                f"expected_findings.json not found for {case.case_id}: {expected_findings}"
            )
        load_expected_findings(case_dir, case)
