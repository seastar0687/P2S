from p2s_core.models import (
    ExpectedGateOutcome,
    ExpectedReviewerFinding,
    GoldenReviewCase,
    ReviewerCalibrationReport,
    ReviewerCalibrationResult,
    SEVERITY_ORDER,
)
from p2s_core.models.reviewer_calibration import severity_satisfies


def test_reviewer_calibration_schemas_roundtrip():
    case = GoldenReviewCase(
        case_id="good_case",
        case_type="good",
        description="ok",
        input_dir="input",
        expected_gate_path="expected_gate.json",
    )
    finding = ExpectedReviewerFinding(category="overhype", severity_at_least="medium")
    gate = ExpectedGateOutcome(expected_status="pass")
    result = ReviewerCalibrationResult(
        case_id="good_case",
        passed=True,
        expected_status="pass",
        actual_status="pass",
    )
    report = ReviewerCalibrationReport(
        case_count=1,
        passed_count=1,
        failed_count=0,
        false_negative_risk_count=0,
        false_positive_risk_count=0,
        results=[result],
        pass_gate=True,
        created_at="2026-05-12T00:00:00Z",
    )

    assert GoldenReviewCase.model_validate_json(case.model_dump_json()).case_id == "good_case"
    assert ExpectedReviewerFinding.model_validate_json(finding.model_dump_json()).category == "overhype"
    assert ExpectedGateOutcome.model_validate_json(gate.model_dump_json()).expected_status == "pass"
    assert ReviewerCalibrationResult.model_validate_json(result.model_dump_json()).passed is True
    assert ReviewerCalibrationReport.model_validate_json(report.model_dump_json()).pass_gate is True


def test_severity_order_and_comparison():
    assert set(SEVERITY_ORDER) == {"info", "low", "medium", "high", "critical"}
    assert SEVERITY_ORDER["critical"] > SEVERITY_ORDER["high"] > SEVERITY_ORDER["medium"] > SEVERITY_ORDER["low"] > SEVERITY_ORDER["info"]
    assert severity_satisfies("critical", "high")
    assert severity_satisfies("high", "high")
    assert not severity_satisfies("medium", "high")
