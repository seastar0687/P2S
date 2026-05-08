from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class SceneRewritePatch(BaseModel):
    """LLM-editable fields for one SceneDraft."""

    model_config = ConfigDict(extra="forbid")

    scene_id: str
    voice_text: str
    subtitle_text: str
    asset_intent: str | None = None
    notes_for_render: str | None = None


class SceneRewriteResult(BaseModel):
    """Structured LLM rewrite response for a complete scenes bundle."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    patches: list[SceneRewritePatch]
    rewrite_model: str | None = None
    prompt_version: str = "llm_quality_rewrite_v1"
    quality_notes: list[str] = Field(default_factory=list)
