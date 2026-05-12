from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SEVERITY_ORDER: dict[str, int] = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class GoldenReviewCase(BaseModel):
    case_id: str
    case_type: Literal[
        "good",
        "unsupported_claim",
        "overhype",
        "missing_limitation",
        "visual_mismatch",
        "media_quality_fail",
        "prompt_injection",
        "arbiter_matrix",
    ]
    description: str
    input_dir: str
    expected_gate_path: str
    expected_findings_path: str | None = None
    tags: list[str] = Field(default_factory=list)


class ExpectedReviewerFinding(BaseModel):
    reviewer: str | None = None
    category: str
    target_type: str | None = None
    target_id: str | None = None
    severity_at_least: Literal["info", "low", "medium", "high", "critical"] | None = None
    blocking: bool | None = None
    must_contain_message: list[str] = Field(default_factory=list)


class ExpectedGateOutcome(BaseModel):
    expected_status: Literal["pass", "human_check", "reject"]
    must_have_blocking_categories: list[str] = Field(default_factory=list)
    must_not_have_blocking_categories: list[str] = Field(default_factory=list)
    allowed_warning_categories: list[str] = Field(default_factory=list)
    notes: str | None = None


class ReviewerCalibrationResult(BaseModel):
    case_id: str
    passed: bool
    expected_status: str
    actual_status: str
    missing_expected_findings: list[str] = Field(default_factory=list)
    unexpected_blocking_findings: list[str] = Field(default_factory=list)
    unexpected_pass: bool = False
    unexpected_reject: bool = False
    notes: list[str] = Field(default_factory=list)


class ReviewerCalibrationReport(BaseModel):
    suite_id: str = "harden4_v1"
    case_count: int
    passed_count: int
    failed_count: int
    false_negative_risk_count: int
    false_positive_risk_count: int
    results: list[ReviewerCalibrationResult]
    reviewer_notes: dict[str, list[str]] = Field(default_factory=dict)
    pass_gate: bool
    created_at: str


def severity_satisfies(actual: str, minimum: str | None) -> bool:
    if minimum is None:
        return True
    return SEVERITY_ORDER[actual] >= SEVERITY_ORDER[minimum]
