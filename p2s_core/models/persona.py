from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from p2s_core.models.common import VisualIdentityProfile


class VRMProfile(BaseModel):
    vrm_path: str
    renderer_backend: Literal["unity", "three_vrm", "blender", "none"] = "three_vrm"
    default_expression: str = "neutral"
    default_motion: str = "idle"
    expression_map: dict[str, str] = Field(default_factory=dict)
    motion_map: dict[str, str] = Field(default_factory=dict)
    camera_presets: dict[str, dict] = Field(default_factory=dict)
    lip_sync_backend: Literal["rhubarb", "viseme", "model_based", "none"] = "rhubarb"
    notes: str | None = None


class VoiceProfile(BaseModel):
    voice_id: str
    backend: Literal[
        "edge_tts",
        "gpt_sovits",
        "index_tts",
        "cosyvoice",
        "fish_speech",
        "chattts",
        "custom",
    ]
    model_path: str | None = None
    config_path: str | None = None
    default_voice: str | None = None
    default_speed: float = 1.0
    default_pitch: float | None = None
    default_energy: str = "medium"
    supported_emotions: list[str] = Field(default_factory=list)
    reference_audio: dict[str, str] = Field(default_factory=dict)
    training_data_manifest: str | None = None
    license_notes: str | None = None


class PersonaProfile(BaseModel):
    persona_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    role: str
    positioning: str
    personality_traits: list[str]
    speaking_style_summary: str
    relationship_to_audience: str
    allowed_emotional_range: list[str]
    catchphrases: list[str] = Field(default_factory=list)
    forbidden_behaviors: list[str] = Field(default_factory=list)
    prompt_profile_path: str | None = None
    speaking_rules_path: str | None = None
    example_paths: list[str] = Field(default_factory=list)
    vrm: VRMProfile | None = None
    voice: VoiceProfile | None = None
    visual_identity: VisualIdentityProfile | None = None
    version: str
    created_at: str
    updated_at: str
