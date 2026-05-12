from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


FindingSeverity = Literal["info", "low", "medium", "high", "critical"]
FindingCategory = Literal[
    "unsupported_claim",
    "missing_evidence",
    "overhype",
    "limitation_missing",
    "visual_mismatch",
    "subtitle_readability",
    "media_quality",
    "fallback_quality",
    "style_violation",
    "prompt_injection",
    "artifact_missing",
    "other",
]
FindingTargetType = Literal[
    "claim",
    "scene",
    "asset_plan",
    "visual",
    "subtitle",
    "audio",
    "segment",
    "final_video",
    "project",
]


class ReviewerFinding(BaseModel):
    finding_id: str
    reviewer: str
    target_type: FindingTargetType
    target_id: str
    severity: FindingSeverity
    category: FindingCategory
    message: str
    evidence_refs: list[str] = Field(default_factory=list)
    suggested_fix: str | None = None
    blocking: bool = False


class ReviewerSummary(BaseModel):
    reviewer: str
    pass_gate: bool
    score: float | None = None
    findings: list[ReviewerFinding] = Field(default_factory=list)
    blocking_count: int = 0
    warning_count: int = 0
    created_at: str
    reviewer_version: str = "mvp3_v1"


class FinalReviewBundle(BaseModel):
    project_id: str
    review_id: str
    active_scene_source: str
    final_video_path: str | None = None
    reviewer_summaries: list[ReviewerSummary]
    media_quality_report_path: str | None = None
    total_findings: int
    blocking_issues: list[ReviewerFinding] = Field(default_factory=list)
    warnings: list[ReviewerFinding] = Field(default_factory=list)
    created_at: str
    version: str = "mvp3_v1"


class FinalGateDecision(BaseModel):
    project_id: str
    gate_name: str = "final_review_gate"
    review_id: str
    status: Literal["pass", "revise", "human_check", "reject"]
    blocking_issues: list[ReviewerFinding] = Field(default_factory=list)
    warning_count: int = 0
    reviewer_statuses: dict[str, str] = Field(default_factory=dict)
    rationale: str
    created_at: str
    version: str = "mvp3_v1"
