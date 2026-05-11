from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


GenerationStatus = Literal["done", "failed", "fallback"]


class GeneratedAudio(BaseModel):
    scene_id: str
    text: str
    backend: str
    voice: str | None = None
    speed: float = 1.0
    output_path: str
    duration_sec: float | None = None
    placeholder: bool = False
    generation_status: GenerationStatus = "done"
    warnings: list[str] = Field(default_factory=list)
    created_at: str


class GeneratedVisual(BaseModel):
    scene_id: str
    asset_source: str
    output_path: str
    source_path: str | None = None
    fallback_level: str | None = None
    width: int = 1080
    height: int = 1920
    generation_status: GenerationStatus = "done"
    warnings: list[str] = Field(default_factory=list)
    created_at: str


class GeneratedSegment(BaseModel):
    scene_id: str
    audio_path: str
    visual_path: str
    output_path: str
    duration_sec: float | None = None
    ffmpeg_command: list[str] = Field(default_factory=list)
    generation_status: Literal["done", "failed"] = "done"
    warnings: list[str] = Field(default_factory=list)
    created_at: str


class CompositionResult(BaseModel):
    project_id: str
    segment_paths: list[str]
    output_path: str
    subtitle_path: str | None = None
    duration_sec: float | None = None
    ffmpeg_command: list[str] = Field(default_factory=list)
    generation_status: Literal["done", "failed"] = "done"
    warnings: list[str] = Field(default_factory=list)
    created_at: str


class MediaGenerationReport(BaseModel):
    project_id: str
    scene_count: int
    audio_count: int
    visual_count: int
    segment_count: int
    fallback_visual_count: int
    failed_scene_count: int
    final_video_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: str
