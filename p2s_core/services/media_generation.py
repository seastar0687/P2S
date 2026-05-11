from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import (
    AssetPlanBundle,
    GeneratedAudio,
    GeneratedSegment,
    GeneratedVisual,
    MediaGenerationReport,
    ProjectState,
)
import p2s_core.services.persistence as persistence
from p2s_core.services.media_metadata import write_media_metadata
from p2s_core.services.segment_composer import compose_segment
from p2s_core.services.tts_service import generate_scene_audio
from p2s_core.services.visual_placeholder import generate_scene_visual, load_figures
from p2s_core.services.video_service import compose_final_video


class MediaGenerationError(RuntimeError):
    """Raised when MVP2C-thin media generation fails."""


def run_asset_generation_stage(
    state: ProjectState,
    *,
    tts_backend: str | None = None,
    command_runner=None,
) -> ProjectState:
    run_dir = persistence.project_dir(state.project_id)
    asset_plan = load_asset_plan(run_dir)
    figures = load_figures(run_dir)
    audio_items: list[GeneratedAudio] = []
    visual_items: list[GeneratedVisual] = []
    segment_items: list[GeneratedSegment] = []
    warnings: list[str] = []
    if not figures:
        warnings.append("figures.json missing or empty; paper_figure scenes will use fallback visuals.")

    for plan in asset_plan.plans:
        audio = generate_scene_audio(run_dir, plan, state, backend=tts_backend)
        visual = generate_scene_visual(run_dir, plan, figures)
        segment = compose_segment(run_dir, plan, audio, visual, runner=command_runner)
        audio_items.append(audio)
        visual_items.append(visual)
        segment_items.append(segment)
        warnings.extend(audio.warnings)
        warnings.extend(visual.warnings)
        warnings.extend(segment.warnings)

    metadata_paths = write_media_metadata(
        run_dir,
        audio=audio_items,
        visuals=visual_items,
        segments=segment_items,
    )
    report = MediaGenerationReport(
        project_id=state.project_id,
        scene_count=len(asset_plan.plans),
        audio_count=len(audio_items),
        visual_count=len(visual_items),
        segment_count=len(segment_items),
        fallback_visual_count=sum(1 for item in visual_items if item.generation_status == "fallback"),
        failed_scene_count=0,
        warnings=warnings,
        created_at=_utc_now(),
    )
    (run_dir / "media_generation_report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    state.assets.update(metadata_paths)
    state.assets["media_generation_report"] = "media_generation_report.json"
    state.stages["asset_generation"].status = "done"
    state.stages["asset_generation"].output_paths = [
        "media_metadata/audio.json",
        "media_metadata/visuals.json",
        "media_metadata/segments.json",
        "media_generation_report.json",
    ]
    return state


def run_composition_stage(state: ProjectState, *, command_runner=None) -> ProjectState:
    run_dir = persistence.project_dir(state.project_id)
    asset_plan = load_asset_plan(run_dir)
    segments = load_segments_manifest(run_dir)
    order = [plan.scene_id for plan in asset_plan.plans]
    segment_map = {segment.scene_id: segment for segment in segments}
    ordered_segments = []
    for scene_id in order:
        if scene_id not in segment_map:
            raise MediaGenerationError(f"missing segment metadata for scene: {scene_id}")
        ordered_segments.append(segment_map[scene_id])
    result = compose_final_video(run_dir, state.project_id, ordered_segments, runner=command_runner)
    metadata_paths = write_media_metadata(run_dir, composition=result)

    report_path = run_dir / "media_generation_report.json"
    if report_path.exists():
        report = MediaGenerationReport.model_validate_json(report_path.read_text(encoding="utf-8"))
        report.final_video_path = result.output_path
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    state.assets.update(metadata_paths)
    state.final_video = {"path": result.output_path, "status": "draft"}
    state.stages["composition"].status = "done"
    state.stages["composition"].output_paths = [result.output_path, "media_metadata/composition.json"]
    return state


def load_asset_plan(run_dir: Path) -> AssetPlanBundle:
    path = run_dir / "asset_plan.json"
    if not path.exists():
        raise FileNotFoundError(f"asset_plan.json not found: {path}")
    return AssetPlanBundle.model_validate_json(path.read_text(encoding="utf-8"))


def load_segments_manifest(run_dir: Path) -> list[GeneratedSegment]:
    path = run_dir / "media_metadata" / "segments.json"
    if not path.exists():
        raise FileNotFoundError(f"segments manifest not found: {path}")
    import json

    return [GeneratedSegment.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
