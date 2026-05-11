from __future__ import annotations

from collections import Counter

from p2s_core.models import AssetPlanBundle, FallbackQualityReport, GeneratedVisual

FALLBACK_REASONS = (
    "no_figure_metadata",
    "caption_only_figure",
    "diagram_prompt_fallback",
    "metaphor_image_fallback",
    "chart_prompt_fallback",
    "unknown_fallback",
)


def build_fallback_quality_report(
    asset_plan: AssetPlanBundle,
    visuals: list[GeneratedVisual],
    figures: list[dict] | None = None,
) -> FallbackQualityReport:
    visual_map = {item.scene_id: item for item in visuals}
    figure_map = {str(item.get("figure_id") or item.get("id")): item for item in figures or []}
    reason_counts: Counter[str] = Counter({reason: 0 for reason in FALLBACK_REASONS})
    scenes_using_fallback: list[str] = []
    warnings: list[str] = []

    for plan in asset_plan.plans:
        visual = visual_map.get(plan.scene_id)
        if not visual or visual.generation_status != "fallback":
            continue
        reason = _classify_fallback_reason(plan.visual_plan.asset_source, plan.visual_plan.selected_figure_ids, figure_map)
        reason_counts[reason] += 1
        scenes_using_fallback.append(plan.scene_id)

    scene_count = len(asset_plan.plans)
    fallback_count = len(scenes_using_fallback)
    fallback_ratio = fallback_count / scene_count if scene_count else 0.0
    if fallback_ratio == 0:
        quality_level = "good"
    elif fallback_ratio <= 0.3:
        quality_level = "acceptable"
    elif fallback_ratio <= 0.7:
        quality_level = "degraded"
    else:
        quality_level = "minimal"
    if fallback_count:
        warnings.append(f"{fallback_count}/{scene_count} visuals used fallback rendering.")

    return FallbackQualityReport(
        scene_count=scene_count,
        fallback_visual_count=fallback_count,
        fallback_ratio=fallback_ratio,
        fallback_by_reason=dict(reason_counts),
        scenes_using_fallback=scenes_using_fallback,
        quality_level=quality_level,
        warnings=warnings,
    )


def _classify_fallback_reason(asset_source: str, figure_ids: list[str], figure_map: dict[str, dict]) -> str:
    if asset_source == "diagram_prompt":
        return "diagram_prompt_fallback"
    if asset_source == "metaphor_image_prompt":
        return "metaphor_image_fallback"
    if asset_source == "chart_prompt":
        return "chart_prompt_fallback"
    if asset_source == "paper_figure":
        if not figure_map:
            return "no_figure_metadata"
        for figure_id in figure_ids:
            figure = figure_map.get(figure_id)
            if figure and not figure.get("image_path"):
                return "caption_only_figure"
        return "unknown_fallback"
    return "unknown_fallback"
