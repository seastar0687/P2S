from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSpan(BaseModel):
    """A text span in the source paper that supports a claim."""

    section: str
    text: str
    page: int | None = None
    confidence: Literal["direct", "inferred", "weak"] = "direct"


class SuggestedFix(BaseModel):
    """An actionable reviewer suggestion."""

    target_type: Literal[
        "claim",
        "scene",
        "voice_text",
        "subtitle_text",
        "visual_prompt",
        "tts",
        "template",
        "field",
    ]
    target_id: str
    target_field: str | None = None
    fix_type: Literal["rewrite", "regenerate", "delete", "lock", "human_check"]
    suggestion: str
    example: str | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    auto_applicable: bool = False


class VisualIdentityProfile(BaseModel):
    """Visual consistency assets for a persona."""

    face_ref_path: str | None = None
    outfit_ref_path: str | None = None
    color_palette_path: str | None = None
    style_tags: list[str] = Field(default_factory=list)
    forbidden_visual_elements: list[str] = Field(default_factory=list)
    prompt_prefix: str | None = None
    notes: str | None = None
