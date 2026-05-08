from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from p2s_core.models.review import GateDecision, ReviewResult
from p2s_core.models.scene import AssetPolicy, AssetTypeHint, BackgroundMode, PresenterMode, VisualFocus
from p2s_core.models.scene import SceneDraft, ScenePurpose


class NarrativeArcItem(BaseModel):
    purpose: ScenePurpose
    claim_ids: list[str]
    intent: str


class NarrativePlan(BaseModel):
    project_id: str
    target_duration_sec: int
    language: str
    audience: str
    selected_claim_ids: list[str]
    narrative_arc: list[NarrativeArcItem]
    omitted_claim_ids: list[str] = Field(default_factory=list)
    rationale: str
    risk_flags: list[str] = Field(default_factory=list)
    created_at: str


class ScenesBundle(BaseModel):
    project_id: str
    scenes: list[SceneDraft]
    created_at: str


class PresentationProfile(BaseModel):
    """Replaceable presenter, asset, and background strategy for a video."""

    profile_id: str
    name: str
    description: str
    presenter_priority: Literal["low", "medium", "high"]
    default_background_mode: BackgroundMode
    require_asset_every_scene: bool = False
    asset_insertion_policy: Literal["only_when_helpful", "balanced", "asset_rich"] = (
        "only_when_helpful"
    )
    presenter_min_visibility_ratio: float = 0.6
    fullscreen_asset_allowed: bool = True
    fullscreen_asset_max_ratio: float = 0.25
    allow_repeated_background: bool = True


class PresentationScene(BaseModel):
    """Per-scene presentation plan keyed by SceneDraft.scene_id."""

    scene_id: str
    scene_type: Literal[
        "presenter_only",
        "presenter_with_overlay",
        "asset_focus",
        "transition_or_card",
    ]
    presenter_mode: PresenterMode
    visual_focus: VisualFocus
    asset_policy: AssetPolicy
    asset_type_hint: AssetTypeHint
    background_mode: BackgroundMode
    estimated_asset_duration_sec: float | None = None
    render_notes: str | None = None


class PresentationPlan(BaseModel):
    """Complete presentation plan persisted as presentation_plan.json."""

    project_id: str
    profile_id: str
    scenes: list[PresentationScene]
    presenter_visibility_ratio: float
    asset_scene_ratio: float
    fullscreen_asset_ratio: float
    created_at: str
    quality_report: dict = Field(default_factory=dict)


class PresentationReviewBundle(BaseModel):
    project_id: str
    target_stage: Literal["presentation_planning", "llm_quality_rewrite"] = "presentation_planning"
    reviews: list[ReviewResult]
    gate_decision: GateDecision
    created_at: str
