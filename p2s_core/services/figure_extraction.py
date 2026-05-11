from __future__ import annotations

import re
from pathlib import Path

from p2s_core.models import ExtractedFigure, ExtractedTable


CAPTION_RE = re.compile(
    r"^\s*((?:fig(?:ure)?\.?|圖)\s*\d+[A-Za-z]?|(?:table|表)\s*\d+[A-Za-z]?)\s*[:.\-]?\s*(.+)",
    re.IGNORECASE,
)


def extract_figure_and_table_metadata(pdf_path: str | Path, run_dir: Path) -> tuple[list[ExtractedFigure], list[ExtractedTable]]:
    import fitz

    figures_dir = run_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    figures: list[ExtractedFigure] = []
    tables: list[ExtractedTable] = []

    with fitz.open(str(pdf_path)) as doc:
        for page_index, page in enumerate(doc, start=1):
            captions = extract_captions_from_text(page.get_text() or "")
            image_blocks = [
                block
                for block in page.get_text("dict").get("blocks", [])
                if block.get("type") == 1 and block.get("image")
            ]

            for block in image_blocks:
                fig_id = f"fig_{len(figures) + 1:03d}"
                ext = block.get("ext") or "png"
                image_name = f"{fig_id}.{ext}"
                image_path = figures_dir / image_name
                image_path.write_bytes(block["image"])
                caption = _claim_nearest_caption(captions, kind="figure")
                figures.append(
                    ExtractedFigure(
                        figure_id=fig_id,
                        page=page_index,
                        image_path=str(Path("figures") / image_name),
                        caption=caption,
                        caption_source="nearby_text" if caption else "missing",
                        bbox=[float(value) for value in block.get("bbox", [])] or None,
                        width=float(block.get("width") or 0) or None,
                        height=float(block.get("height") or 0) or None,
                        confidence="medium" if caption else "low",
                        risk_flags=[] if caption else ["missing_caption"],
                    )
                )

            for caption in captions:
                if caption["kind"] == "figure" and not image_blocks:
                    figures.append(
                        ExtractedFigure(
                            figure_id=f"fig_{len(figures) + 1:03d}",
                            page=page_index,
                            image_path=None,
                            caption=caption["text"],
                            caption_source="direct",
                            confidence="low",
                            risk_flags=["caption_without_image"],
                            notes="Caption metadata found but no image block was extracted.",
                        )
                    )
                elif caption["kind"] == "table":
                    tables.append(
                        ExtractedTable(
                            table_id=f"table_{len(tables) + 1:03d}",
                            page=page_index,
                            image_path=None,
                            caption=caption["text"],
                            caption_source="direct",
                            confidence="low",
                            notes="HARDEN-1 stores table caption metadata only.",
                        )
                    )

    return figures, tables


def extract_captions_from_text(text: str) -> list[dict[str, str]]:
    captions: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = CAPTION_RE.match(line)
        if not match:
            continue
        prefix = match.group(1).lower()
        kind = "table" if prefix.startswith("table") or prefix.startswith("表") else "figure"
        captions.append({"kind": kind, "text": line})
    return captions


def _claim_nearest_caption(captions: list[dict[str, str]], kind: str) -> str | None:
    for caption in captions:
        if caption["kind"] == kind:
            return caption["text"]
    return None


def validate_figure_paths(run_dir: Path, figures: list[dict]) -> None:
    root = run_dir.resolve()
    seen: set[str] = set()
    for figure in figures:
        figure_id = str(figure.get("figure_id") or "")
        if figure_id in seen:
            raise ValueError(f"duplicate figure_id: {figure_id}")
        seen.add(figure_id)
        image_path = figure.get("image_path")
        if not image_path:
            continue
        resolved = (run_dir / image_path).resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError(f"figure image_path points outside run_dir: {image_path}")
