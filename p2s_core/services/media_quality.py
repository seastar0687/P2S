from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import (
    CompositionResult,
    GeneratedAudio,
    GeneratedSegment,
    GeneratedVisual,
    MediaQualityReport,
    ProjectState,
)
import p2s_core.services.persistence as persistence
from p2s_core.services.audio_quality import check_audio_quality
from p2s_core.services.composition_quality import check_composition_quality
from p2s_core.services.fallback_quality import build_fallback_quality_report
from p2s_core.services.media_generation import load_asset_plan
from p2s_core.services.segment_quality import check_segment_quality
from p2s_core.services.subtitle_quality import check_subtitle_readability
from p2s_core.services.visual_layout_quality import check_visual_layout_quality


class MediaQualityError(RuntimeError):
    """Raised when HARDEN-3 media quality inputs are missing or invalid."""


def run_media_quality_check_stage(state: ProjectState, *, command_runner=None) -> ProjectState:
    run_dir = persistence.project_dir(state.project_id)
    report = build_media_quality_report(run_dir, state.project_id, runner=command_runner)
    output_path = run_dir / "media_quality_report.json"
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    state.assets["media_quality_report"] = "media_quality_report.json"
    stage = state.stages["media_quality_check"]
    stage.status = "done" if report.pass_gate else "needs_review"
    stage.output_paths = ["media_quality_report.json"]
    stage.error = None if report.pass_gate else "; ".join(report.blocking_issues)
    return state


def build_media_quality_report(run_dir: Path, project_id: str, *, runner=None) -> MediaQualityReport:
    asset_plan = load_asset_plan(run_dir)
    _require_file(run_dir / "media_generation_report.json")
    audio_items = _load_list(run_dir / "media_metadata" / "audio.json", GeneratedAudio)
    visual_items = _load_list(run_dir / "media_metadata" / "visuals.json", GeneratedVisual)
    segment_items = _load_list(run_dir / "media_metadata" / "segments.json", GeneratedSegment)
    composition = _load_model(run_dir / "media_metadata" / "composition.json", CompositionResult)
    audio_map = {item.scene_id: item for item in audio_items}
    visual_map = {item.scene_id: item for item in visual_items}
    segment_map = {item.scene_id: item for item in segment_items}

    audio_results = [check_audio_quality(run_dir, item) for item in audio_items]
    subtitle_results = [check_subtitle_readability(plan) for plan in asset_plan.plans]
    visual_results = [
        check_visual_layout_quality(run_dir, visual_map[plan.scene_id], plan)
        for plan in asset_plan.plans
        if plan.scene_id in visual_map
    ]
    segment_results = [
        check_segment_quality(run_dir, segment_map[plan.scene_id], audio_map.get(plan.scene_id), runner=runner)
        for plan in asset_plan.plans
        if plan.scene_id in segment_map
    ]
    composition_result = check_composition_quality(
        run_dir,
        project_id,
        composition,
        segment_results,
        runner=runner,
    )
    fallback_quality = build_fallback_quality_report(asset_plan, visual_items, _load_optional_figures(run_dir))

    warnings = _collect_warnings(
        audio_results,
        subtitle_results,
        visual_results,
        segment_results,
        [composition_result, fallback_quality],
    )
    blocking_issues = _collect_blocking_issues(
        audio_results,
        subtitle_results,
        visual_results,
        segment_results,
        composition_result,
        expected_scene_ids=[plan.scene_id for plan in asset_plan.plans],
        audio_map=audio_map,
        visual_map=visual_map,
        segment_map=segment_map,
    )
    pass_gate = not blocking_issues

    return MediaQualityReport(
        project_id=project_id,
        audio_results=audio_results,
        subtitle_results=subtitle_results,
        visual_layout_results=visual_results,
        segment_results=segment_results,
        composition_result=composition_result,
        fallback_quality=fallback_quality,
        pass_gate=pass_gate,
        blocking_issues=blocking_issues,
        warnings=warnings,
        created_at=datetime.now(UTC).isoformat(),
    )


def _load_model(path: Path, model_type):
    _require_file(path)
    return model_type.model_validate_json(path.read_text(encoding="utf-8"))


def _load_list(path: Path, model_type):
    _require_file(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise MediaQualityError(f"required metadata is not a list: {path}")
    return [model_type.model_validate(item) for item in raw]


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required media quality input missing: {path}")


def _load_optional_figures(run_dir: Path) -> list[dict]:
    path = run_dir / "figures.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else []


def _collect_warnings(*groups) -> list[str]:
    warnings: list[str] = []
    for group in groups:
        for item in group:
            warnings.extend(getattr(item, "warnings", []))
    return warnings


def _collect_blocking_issues(
    audio_results,
    subtitle_results,
    visual_results,
    segment_results,
    composition_result,
    *,
    expected_scene_ids: list[str],
    audio_map: dict[str, GeneratedAudio],
    visual_map: dict[str, GeneratedVisual],
    segment_map: dict[str, GeneratedSegment],
) -> list[str]:
    issues: list[str] = []
    for scene_id in expected_scene_ids:
        if scene_id not in audio_map:
            issues.append(f"{scene_id}: missing audio metadata")
        if scene_id not in visual_map:
            issues.append(f"{scene_id}: missing visual metadata")
        if scene_id not in segment_map:
            issues.append(f"{scene_id}: missing segment metadata")
    for item in [*audio_results, *subtitle_results, *visual_results, *segment_results]:
        if not item.pass_gate:
            issues.append(f"{item.scene_id}: media quality gate failed")
    if not composition_result.pass_gate:
        issues.append("composition: media quality gate failed")
    return issues
