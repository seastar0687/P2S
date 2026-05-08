from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StyleProfile(BaseModel):
    style_id: str
    name: str
    summary: str
    target_platforms: list[Literal["youtube_shorts", "tiktok", "reels", "bilibili", "slides"]]
    target_audience: str
    language: str
    narrative_structure: list[str]
    pacing: Literal["slow", "moderate", "fast"]
    humor_level: int
    rigor_level: int
    metaphor_level: int
    allowed_rhetorical_devices: list[str] = Field(default_factory=list)
    forbidden_rhetorical_devices: list[str] = Field(default_factory=list)
    sentence_rules: dict = Field(default_factory=dict)
    subtitle_rules: dict = Field(default_factory=dict)
    hook_rules: dict = Field(default_factory=dict)
    transition_rules: dict = Field(default_factory=dict)
    limitation_rules: dict = Field(default_factory=dict)
    prompt_guide_path: str
    example_paths: list[str] = Field(default_factory=list)
    forbidden_phrases_path: str | None = None
    rewrite_rules_path: str | None = None
    rubric_path: str | None = None
    version: str
