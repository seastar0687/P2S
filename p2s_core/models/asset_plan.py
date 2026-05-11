from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AssetSource = Literal[
    "none",
    "paper_figure",
    "diagram_prompt",
    "metaphor_image_prompt",
    "chart_prompt",
    "text_card",
    "static_background",
]

LayoutMode = Literal[
    "presenter_only",
    "presenter_with_overlay",
    "asset_focus",
    "text_card",
    "static_clean",
]


class TTSPlan(BaseModel):
    enabled: bool = True
    backend: str = "edge_tts"
    voice: str | None = None
    speed: float = 1.0
    pitch: float | None = None
    emotion: str | None = None
    text: str
    output_path: str
    estimated_duration_sec: float | None = None
    placeholder_only: bool = True
    notes: str | None = None


class VisualAssetPlan(BaseModel):
    enabled: bool
    asset_source: AssetSource
    asset_type_hint: str
    asset_intent: str | None = None
    selected_figure_ids: list[str] = Field(default_factory=list)
    figure_selection_reason: str | None = None
    visual_prompt: str | None = None
    fallback_chain: list[str]
    output_placeholder: str | None = None
    risk_flags: list[str] = Field(default_factory=list)
    notes: str | None = None


class RenderPlan(BaseModel):
    template_hint: str
    layout_mode: LayoutMode
    resolution: str = "1080x1920"
    fps: int = 30
    background_mode: str
    subtitle_mode: str = "one_sentence"
    output_segment_placeholder: str
    notes: str | None = None


class SceneAssetPlan(BaseModel):
    scene_id: str
    purpose: str
    claim_ids: list[str]
    voice_text: str
    subtitle_text: str
    presenter_mode: str
    visual_focus: str
    asset_policy: str
    asset_type_hint: str
    background_mode: str
    tts_plan: TTSPlan
    visual_plan: VisualAssetPlan
    render_plan: RenderPlan
    warnings: list[str] = Field(default_factory=list)
    notes: str | None = None


class AssetPlanQualityReport(BaseModel):
    scene_count: int
    tts_enabled_count: int
    visual_enabled_count: int
    required_asset_count: int
    optional_asset_count: int
    no_asset_count: int
    paper_figure_count: int
    diagram_prompt_count: int
    metaphor_prompt_count: int
    text_card_count: int
    static_background_count: int
    warnings: list[str] = Field(default_factory=list)


class AssetPlanBundle(BaseModel):
    project_id: str
    scene_source: str
    presentation_plan_path: str = "presentation_plan.json"
    plans: list[SceneAssetPlan]
    quality_report: AssetPlanQualityReport
    created_at: str
    version: str = "mvp2b_v1"
