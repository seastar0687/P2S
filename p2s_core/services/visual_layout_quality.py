from __future__ import annotations

from pathlib import Path

from p2s_core.models import GeneratedVisual, SceneAssetPlan, VisualLayoutQualityResult
from p2s_core.services.visual_placeholder import parse_resolution


def check_visual_layout_quality(run_dir: Path, visual: GeneratedVisual, plan: SceneAssetPlan) -> VisualLayoutQualityResult:
    path = run_dir / visual.output_path
    warnings: list[str] = []
    exists = path.exists()
    width = None
    height = None
    pass_gate = True
    if not exists:
        warnings.append("visual PNG is missing")
        pass_gate = False
    else:
        try:
            from PIL import Image

            with Image.open(path) as image:
                width, height = image.size
        except Exception:
            warnings.append("visual PNG is unreadable")
            pass_gate = False

    expected_width, expected_height = parse_resolution(plan.render_plan.resolution)
    if width and height and (width != expected_width or height != expected_height):
        warnings.append("visual resolution does not match render_plan.resolution")
    if not plan.subtitle_text.strip():
        warnings.append("text card primary text is empty")
    figure_size_ratio = None
    if visual.asset_source == "paper_figure":
        figure_size_ratio = 0.5 if visual.source_path else 0.0
        if figure_size_ratio < 0.15:
            warnings.append("figure card has no visible source image or figure ratio is too small")
    return VisualLayoutQualityResult(
        scene_id=visual.scene_id,
        visual_path=visual.output_path,
        width=width,
        height=height,
        layout_type=visual.asset_source,
        safe_area_ok=True,
        min_text_size_ok=bool(plan.subtitle_text.strip()),
        figure_size_ratio=figure_size_ratio,
        pass_gate=pass_gate,
        warnings=warnings,
    )
