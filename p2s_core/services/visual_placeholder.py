from __future__ import annotations

import json
import textwrap
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import GeneratedVisual, SceneAssetPlan


class VisualGenerationError(RuntimeError):
    """Raised when MVP2C-thin cannot create a visual placeholder."""


def generate_scene_visual(run_dir: Path, plan: SceneAssetPlan, figures: list[dict] | None = None) -> GeneratedVisual:
    figures = figures or []
    width, height = parse_resolution(plan.render_plan.resolution)
    asset_source = plan.visual_plan.asset_source
    output_path = _visual_output_path(plan, asset_source)
    absolute_output = run_dir / output_path
    _ensure_inside_run_dir(run_dir, absolute_output)
    absolute_output.parent.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    source_path = None
    fallback_level = None
    resolved_source = asset_source
    text = _visual_text(plan)

    if asset_source == "paper_figure":
        figure = _selected_figure(plan, figures)
        if figure and figure.get("image_path"):
            source_path = str(figure["image_path"])
            _render_paper_figure(run_dir / source_path, absolute_output, text, width, height)
        else:
            fallback_level = "text_card"
            resolved_source = "text_card"
            warnings.append("paper_figure unavailable in thin mode; fell back to text_card.")
            _render_text_card(absolute_output, text, width, height)
    elif asset_source in {"diagram_prompt", "metaphor_image_prompt", "chart_prompt"}:
        fallback_level = "text_card"
        resolved_source = "text_card"
        warnings.append(f"{asset_source} unsupported in thin mode; fell back to text_card.")
        _render_text_card(absolute_output, text, width, height)
    elif asset_source == "text_card":
        _render_text_card(absolute_output, text, width, height)
    else:
        _render_static_background(absolute_output, text, width, height)

    return GeneratedVisual(
        scene_id=plan.scene_id,
        asset_source=resolved_source,
        output_path=output_path.as_posix(),
        source_path=source_path,
        fallback_level=fallback_level,
        width=width,
        height=height,
        generation_status="fallback" if fallback_level else "done",
        warnings=warnings,
        created_at=_utc_now(),
    )


def load_figures(run_dir: Path) -> list[dict]:
    path = run_dir / "figures.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def parse_resolution(value: str | None) -> tuple[int, int]:
    if value:
        parts = value.lower().split("x")
        if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
            width, height = int(parts[0]), int(parts[1])
            if width > 0 and height > 0:
                return width, height
    return 1080, 1920


def _visual_output_path(plan: SceneAssetPlan, asset_source: str) -> Path:
    placeholder = plan.visual_plan.output_placeholder
    if placeholder:
        path = Path(placeholder)
        if path.parts and path.parts[0] == "assets":
            return path.with_suffix(".png")
    suffix = "figure" if asset_source == "paper_figure" else "textcard"
    return Path("assets") / f"{plan.scene_id}_{suffix}.png"


def _visual_text(plan: SceneAssetPlan) -> str:
    text = plan.subtitle_text.strip() or plan.tts_plan.text.strip()
    if not text:
        return plan.scene_id
    return text.split("。")[0][:120]


def _selected_figure(plan: SceneAssetPlan, figures: list[dict]) -> dict | None:
    selected = set(plan.visual_plan.selected_figure_ids)
    for figure in figures:
        if figure.get("figure_id") in selected:
            return figure
    return None


def _render_text_card(path: Path, text: str, width: int, height: int) -> None:
    _render_with_pillow_or_fitz(path, text, width, height, mode="text_card")


def _render_static_background(path: Path, text: str, width: int, height: int) -> None:
    _render_with_pillow_or_fitz(path, text, width, height, mode="static")


def _render_paper_figure(source: Path, path: Path, text: str, width: int, height: int) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        _render_with_pillow_or_fitz(path, text, width, height, mode="text_card")
        return

    canvas = Image.new("RGB", (width, height), (246, 247, 241))
    draw = ImageDraw.Draw(canvas)
    try:
        figure = Image.open(source).convert("RGB")
        figure.thumbnail((int(width * 0.86), int(height * 0.62)))
        x = (width - figure.width) // 2
        y = int(height * 0.16)
        canvas.paste(figure, (x, y))
    except Exception:
        draw.rectangle([int(width * 0.12), int(height * 0.18), int(width * 0.88), int(height * 0.62)], outline=(70, 76, 84), width=4)
    _draw_centered_text(draw, text, width, int(height * 0.74), fill=(25, 30, 35))
    canvas.save(path)


def _render_with_pillow_or_fitz(path: Path, text: str, width: int, height: int, *, mode: str) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        _render_with_fitz(path, text, width, height)
        return

    background = (244, 246, 248) if mode == "text_card" else (238, 241, 236)
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    if mode == "text_card":
        margin = int(width * 0.1)
        draw.rounded_rectangle([margin, int(height * 0.32), width - margin, int(height * 0.62)], radius=24, fill=(255, 255, 255), outline=(198, 204, 210), width=3)
        _draw_centered_text(draw, text, width, int(height * 0.42), fill=(23, 29, 36))
    else:
        _draw_centered_text(draw, text, width, int(height * 0.46), fill=(23, 29, 36))
    image.save(path)


def _render_with_fitz(path: Path, text: str, width: int, height: int) -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.draw_rect(fitz.Rect(0, 0, width, height), color=(0.95, 0.96, 0.95), fill=(0.95, 0.96, 0.95))
    wrapped = "\n".join(textwrap.wrap(text, width=22))
    page.insert_textbox(fitz.Rect(width * 0.12, height * 0.35, width * 0.88, height * 0.65), wrapped, fontsize=max(24, width // 24), align=1)
    pix = page.get_pixmap(alpha=False)
    pix.save(path)
    doc.close()


def _draw_centered_text(draw, text: str, width: int, y: int, *, fill) -> None:
    wrapped = "\n".join(textwrap.wrap(text, width=18))
    try:
        bbox = draw.multiline_textbbox((0, 0), wrapped, spacing=10)
        text_width = bbox[2] - bbox[0]
    except AttributeError:
        text_width = min(width, len(text) * 14)
    draw.multiline_text(((width - text_width) / 2, y), wrapped, fill=fill, spacing=10, align="center")


def _ensure_inside_run_dir(run_dir: Path, path: Path) -> None:
    root = run_dir.resolve()
    resolved = path.resolve()
    if root != resolved and root not in resolved.parents:
        raise VisualGenerationError(f"visual output path points outside run_dir: {path}")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
