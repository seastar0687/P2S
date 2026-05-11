from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime
import re

from p2s_core.models import ExtractedSection, ExtractionQualityReport, ProjectState
from p2s_core.services.figure_extraction import extract_figure_and_table_metadata
from p2s_core.services import persistence
from p2s_core.services.text_normalization import normalize_text


def extract_text(pdf_path: str | Path) -> str:
    """Extract plain text from a PDF with PyMuPDF."""

    import fitz

    with fitz.open(str(pdf_path)) as doc:
        return "\n\n".join(page.get_text() for page in doc)


def page_count(pdf_path: str | Path) -> int | None:
    import fitz

    with fitz.open(str(pdf_path)) as doc:
        return len(doc)


def run_extraction_stage(state: ProjectState) -> ProjectState:
    run_dir = persistence.project_dir(state.project_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    text = extract_text(state.source.pdf_path)
    normalized_text = normalize_text(text)

    text_path = run_dir / "extracted_text.md"
    normalized_path = run_dir / "extracted_text_normalized.md"
    sections_path = run_dir / "sections.json"
    figures_path = run_dir / "figures.json"
    tables_path = run_dir / "tables.json"
    quality_path = run_dir / "extraction_quality_report.json"

    text_path.write_text(text, encoding="utf-8")
    normalized_path.write_text(normalized_text, encoding="utf-8")

    sections = detect_sections(text)
    figures, tables = extract_figure_and_table_metadata(state.source.pdf_path, run_dir)

    sections_path.write_text(
        "[" + ",\n".join(section.model_dump_json(indent=2) for section in sections) + "]",
        encoding="utf-8",
    )
    figures_path.write_text(
        "[" + ",\n".join(figure.model_dump_json(indent=2) for figure in figures) + "]",
        encoding="utf-8",
    )
    tables_path.write_text(
        "[" + ",\n".join(table.model_dump_json(indent=2) for table in tables) + "]",
        encoding="utf-8",
    )

    report = build_quality_report(
        project_id=state.project_id,
        text=normalized_text,
        page_count_value=page_count(state.source.pdf_path),
        sections=sections,
        figures=[figure.model_dump() for figure in figures],
        tables=[table.model_dump() for table in tables],
    )
    quality_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    state.extraction.text_md = "extracted_text.md"
    state.extraction.normalized_text_md = "extracted_text_normalized.md"
    state.extraction.sections_path = "sections.json"
    state.extraction.figures_path = "figures.json"
    state.extraction.tables_path = "tables.json"
    state.extraction.quality_report = {
        "path": "extraction_quality_report.json",
        "quality_level": report.quality_level,
    }
    state.extraction.sections = []
    state.extraction.figures = []
    state.extraction.tables = []
    state.stages["extraction"].status = "done"
    state.stages["extraction"].output_paths = [
        "extracted_text.md",
        "extracted_text_normalized.md",
        "sections.json",
        "figures.json",
        "tables.json",
        "extraction_quality_report.json",
    ]
    return state


SECTION_RE = re.compile(
    r"^\s*(?:(?P<number>(?:\d+(?:\.\d+)*|[IVX]+)\.?)\s+)?(?P<title>"
    r"abstract|introduction|related work|background|method|methods|experiments?|results?|"
    r"discussion|limitations?|conclusion|conclusions)\s*$",
    re.IGNORECASE,
)


def detect_sections(text: str) -> list[ExtractedSection]:
    lines = text.splitlines()
    candidates: list[tuple[int, str, int | None, str]] = []
    repeated = _repeated_lines(lines)
    char_offset = 0
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if stripped and stripped not in repeated and not _looks_like_caption(stripped):
            match = SECTION_RE.match(stripped)
            if match:
                level = 1 if match.group("number") else None
                candidates.append((char_offset, stripped, level, "regex"))
            elif _looks_like_upper_heading(stripped):
                candidates.append((char_offset, stripped.title(), None, "uppercase"))
        char_offset += len(line) + 1

    sections: list[ExtractedSection] = []
    for index, (start, title, level, method) in enumerate(candidates):
        end = candidates[index + 1][0] if index + 1 < len(candidates) else len(text)
        body = normalize_text(text[start:end])
        sections.append(
            ExtractedSection(
                section_id=f"section_{index + 1:03d}",
                title=title,
                normalized_title=_normalize_section_title(title),
                level=level,
                text=body,
                char_start=start,
                char_end=end,
                confidence="high" if method == "regex" else "medium",
                detection_method=method,
            )
        )

    if not sections:
        return [
            ExtractedSection(
                section_id="section_001",
                title="Full Text",
                normalized_title="full_text",
                text=normalize_text(text),
                char_start=0,
                char_end=len(text),
                confidence="low",
                detection_method="fallback",
                warnings=["No reliable section headings detected."],
            )
        ]
    return sections


def build_quality_report(
    *,
    project_id: str,
    text: str,
    page_count_value: int | None,
    sections: list[ExtractedSection],
    figures: list[dict],
    tables: list[dict],
) -> ExtractionQualityReport:
    warnings: list[str] = []
    titles = [section.normalized_title for section in sections]
    missing = [
        expected
        for expected in ("abstract", "introduction")
        if not any(expected in title for title in titles)
    ]
    if missing:
        warnings.append(f"Missing expected sections: {', '.join(missing)}")
    if not figures:
        warnings.append("No figure metadata found.")
    figures_with_caption = sum(1 for figure in figures if figure.get("caption"))
    tables_with_caption = sum(1 for table in tables if table.get("caption"))
    if figures and figures_with_caption < len(figures):
        warnings.append("Some figures are missing captions.")

    if len(text) < 500:
        quality = "failed"
        warnings.append("Extracted text is shorter than 500 characters.")
    elif missing:
        quality = "acceptable"
    elif figures and figures_with_caption == len(figures):
        quality = "good"
    else:
        quality = "acceptable"

    return ExtractionQualityReport(
        project_id=project_id,
        text_char_count=len(text),
        page_count=page_count_value,
        section_count=len(sections),
        detected_section_titles=[section.title for section in sections],
        missing_expected_sections=missing,
        figure_count=len(figures),
        figures_with_caption_count=figures_with_caption,
        figures_without_caption_count=len(figures) - figures_with_caption,
        table_count=len(tables),
        tables_with_caption_count=tables_with_caption,
        tables_without_caption_count=len(tables) - tables_with_caption,
        normalization_applied=["unicode_nfkc", "hyphenation", "line_breaks", "whitespace"],
        warnings=warnings,
        quality_level=quality,
        created_at=datetime.now(UTC).isoformat(),
    )


def _normalize_section_title(title: str) -> str:
    title = re.sub(r"^\s*(?:\d+(?:\.\d+)*|[IVX]+)\.?\s+", "", title, flags=re.IGNORECASE)
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _looks_like_caption(line: str) -> bool:
    return bool(re.match(r"^\s*(fig(?:ure)?\.?|table|圖|表)\s*\d+", line, re.IGNORECASE))


def _looks_like_upper_heading(line: str) -> bool:
    if len(line) > 40 or len(line) < 4:
        return False
    if _looks_like_caption(line):
        return False
    letters = [char for char in line if char.isalpha()]
    return bool(letters) and all(char.isupper() for char in letters)


def _repeated_lines(lines: list[str]) -> set[str]:
    counts: dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        if len(stripped) >= 4:
            counts[stripped] = counts.get(stripped, 0) + 1
    return {line for line, count in counts.items() if count >= 3}
