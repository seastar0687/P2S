from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AudioQualityResult(BaseModel):
    scene_id: str
    audio_path: str
    exists: bool
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    loudness_lufs: float | None = None
    peak_dbfs: float | None = None
    silence_ratio: float | None = None
    pass_gate: bool
    warnings: list[str] = Field(default_factory=list)


class SubtitleReadabilityResult(BaseModel):
    scene_id: str
    subtitle_text: str
    char_count: int
    estimated_lines: int
    font_size: int | None = None
    safe_area_ok: bool = True
    too_long: bool = False
    pass_gate: bool
    warnings: list[str] = Field(default_factory=list)


class VisualLayoutQualityResult(BaseModel):
    scene_id: str
    visual_path: str
    width: int | None = None
    height: int | None = None
    layout_type: str | None = None
    text_bbox: list[int] | None = None
    figure_bbox: list[int] | None = None
    safe_area_ok: bool = True
    min_text_size_ok: bool = True
    figure_size_ratio: float | None = None
    pass_gate: bool
    warnings: list[str] = Field(default_factory=list)


class SegmentQualityResult(BaseModel):
    scene_id: str
    segment_path: str
    exists: bool
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    audio_duration_sec: float | None = None
    duration_delta_sec: float | None = None
    ffprobe_readable: bool = False
    pass_gate: bool
    warnings: list[str] = Field(default_factory=list)


class CompositionQualityResult(BaseModel):
    project_id: str
    output_path: str
    exists: bool
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    expected_duration_sec: float | None = None
    duration_delta_sec: float | None = None
    ffprobe_readable: bool = False
    codec_video: str | None = None
    codec_audio: str | None = None
    pixel_format: str | None = None
    pass_gate: bool
    warnings: list[str] = Field(default_factory=list)


class FallbackQualityReport(BaseModel):
    scene_count: int
    fallback_visual_count: int
    fallback_ratio: float
    fallback_by_reason: dict[str, int] = Field(default_factory=dict)
    scenes_using_fallback: list[str] = Field(default_factory=list)
    quality_level: Literal["good", "acceptable", "degraded", "minimal"]
    warnings: list[str] = Field(default_factory=list)


class MediaQualityReport(BaseModel):
    project_id: str
    audio_results: list[AudioQualityResult]
    subtitle_results: list[SubtitleReadabilityResult]
    visual_layout_results: list[VisualLayoutQualityResult]
    segment_results: list[SegmentQualityResult]
    composition_result: CompositionQualityResult
    fallback_quality: FallbackQualityReport
    pass_gate: bool
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: str
