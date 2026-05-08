from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from p2s_core.models.common import SuggestedFix


class ReviewResult(BaseModel):
    review_id: str
    target_type: Literal[
        "claim",
        "script",
        "scene",
        "presentation",
        "visual",
        "tts",
        "subtitle",
        "segment",
        "final_video",
    ]
    target_id: str
    reviewer: str
    score: float
    pass_gate: bool
    severity: Literal["low", "medium", "high", "critical"] = "low"
    findings: list[str] = Field(default_factory=list)
    suggested_fixes: list[SuggestedFix] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: str
    reviewer_model: str | None = None
    reviewer_prompt_version: str | None = None


class GateDecision(BaseModel):
    gate_name: str
    target_type: Literal[
        "claim",
        "artifact",
        "script",
        "scene",
        "presentation",
        "visual",
        "tts",
        "final_video",
    ]
    target_id: str
    status: Literal["pass", "revise", "human_check", "reject"]
    summary: str | None = None
    blocking_issues: list[str] = Field(default_factory=list)
    auto_fix_plan: list[SuggestedFix] = Field(default_factory=list)
    human_notes: list[str] = Field(default_factory=list)
    aggregated_scores: dict[str, float] = Field(default_factory=dict)
    contributing_reviews: list[str] = Field(default_factory=list)
    revision_count: int = 0
    created_at: str
