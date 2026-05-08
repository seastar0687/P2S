from __future__ import annotations

from typing import Literal, get_args

from pydantic import BaseModel, Field


PresenterMode = Literal[
    "speaking_on_camera",
    "speaking_with_overlay",
    "silent_presence",
    "minimized",
    "off_screen",
]
VisualFocus = Literal[
    "presenter",
    "supporting_asset",
    "split",
    "asset_fullscreen",
    "text_card",
]
AssetPolicy = Literal["none", "optional", "required"]
AssetTypeHint = Literal[
    "none",
    "paper_figure",
    "diagram",
    "metaphor_image",
    "chart",
]
BackgroundMode = Literal[
    "static_clean",
    "static_thematic",
    "simple_gradient",
    "custom",
]
VisualType = Literal[
    "paper_figure",
    "diagram",
    "metaphor_image",
    "character",
    "static_template",
]


ScenePurpose = Literal["hook", "problem", "method", "result", "limitation", "takeaway", "transition"]


class VoiceDirection(BaseModel):
    emotion: Literal["neutral", "curious", "excited", "serious", "gentle", "warning"]
    speed: float | None = None
    pause_points: list[str] = Field(default_factory=list)
    emphasis_words: list[str] = Field(default_factory=list)
    pronunciation_notes: dict[str, str] = Field(default_factory=dict)


class SceneDraft(BaseModel):
    scene_id: str
    purpose: ScenePurpose
    claim_ids: list[str]
    voice_text: str
    subtitle_text: str
    target_duration_sec: float
    presenter_mode: PresenterMode = "speaking_on_camera"
    visual_focus: VisualFocus = "presenter"
    asset_policy: AssetPolicy = "optional"
    asset_intent: str | None = None
    asset_type_hint: AssetTypeHint = "none"
    background_mode: BackgroundMode = "static_clean"
    notes_for_render: str | None = None
    visual_intent: str | None = None
    visual_type: str | None = None
    risk_flags: list[str] = Field(default_factory=list)


class Scene(BaseModel):
    scene_id: str
    purpose: ScenePurpose
    claim_ids: list[str]
    voice_text: str
    subtitle_text: str
    presenter_mode: PresenterMode = "speaking_on_camera"
    visual_focus: VisualFocus = "presenter"
    asset_policy: AssetPolicy = "optional"
    asset_intent: str | None = None
    asset_type_hint: AssetTypeHint = "none"
    background_mode: BackgroundMode = "static_clean"
    visual_prompt: str | None = None
    selected_figure_ids: list[str] = Field(default_factory=list)
    character_presence: str | None = None
    character_expression: str | None = None
    character_motion: str | None = None
    style_notes: list[str] = Field(default_factory=list)
    voice_direction: VoiceDirection | None = None
    target_duration_sec: float | None = None
    audio_path: str | None = None
    audio_duration_sec: float | None = None
    asset_paths: list[str] = Field(default_factory=list)
    locked_fields: list[str] = Field(default_factory=list)
    review_status: dict[str, str] = Field(default_factory=dict)
    visual_type: str | None = None


def visual_type_values() -> tuple[str, ...]:
    return get_args(VisualType)
