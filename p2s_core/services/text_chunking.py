from __future__ import annotations

import re

from p2s_core.models import ExtractedPaper, PaperChunk, PaperSection


SECTION_PATTERNS = [
    ("abstract", re.compile(r"^\s*abstract\s*$", re.IGNORECASE)),
    ("introduction", re.compile(r"^\s*(\d+\.?\s*)?introduction\s*$", re.IGNORECASE)),
    ("background", re.compile(r"^\s*(\d+\.?\s*)?(background|related work)\s*$", re.IGNORECASE)),
    ("method", re.compile(r"^\s*(\d+\.?\s*)?(method|methods|methodology|approach)\s*$", re.IGNORECASE)),
    ("experiment", re.compile(r"^\s*(\d+\.?\s*)?(experiment|experiments|evaluation)\s*$", re.IGNORECASE)),
    ("result", re.compile(r"^\s*(\d+\.?\s*)?(result|results)\s*$", re.IGNORECASE)),
    ("discussion", re.compile(r"^\s*(\d+\.?\s*)?discussion\s*$", re.IGNORECASE)),
    ("limitation", re.compile(r"^\s*(\d+\.?\s*)?limitations?\s*$", re.IGNORECASE)),
    ("conclusion", re.compile(r"^\s*(\d+\.?\s*)?conclusions?\s*$", re.IGNORECASE)),
]


def build_extracted_paper(
    project_id: str,
    text: str,
    max_tokens_per_chunk: int = 800,
) -> ExtractedPaper:
    if not text or not text.strip():
        raise ValueError("extracted_text.md is empty")

    sections = detect_sections(text)
    chunks = chunk_sections(sections, max_tokens_per_chunk=max_tokens_per_chunk)
    return ExtractedPaper(project_id=project_id, sections=sections, chunks=chunks)


def detect_sections(text: str) -> list[PaperSection]:
    lines = text.splitlines()
    headings: list[tuple[int, str, str]] = []
    cursor = 0

    for line in lines:
        clean = line.strip()
        section_type = classify_heading(clean)
        if section_type:
            headings.append((cursor, clean, section_type))
        cursor += len(line) + 1

    if not headings:
        return [
            PaperSection(
                section_id="section_001",
                title="Full Text",
                section_type="unknown",
                text=text.strip(),
                start_char=0,
                end_char=len(text),
            )
        ]

    sections: list[PaperSection] = []
    for index, (start, title, section_type) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        body_start = start + len(title)
        body = text[body_start:end].strip()
        if not body:
            continue
        sections.append(
            PaperSection(
                section_id=f"section_{len(sections) + 1:03d}",
                title=title,
                section_type=section_type,
                text=body,
                start_char=body_start,
                end_char=end,
            )
        )

    if not sections:
        return [
            PaperSection(
                section_id="section_001",
                title="Full Text",
                section_type="unknown",
                text=text.strip(),
                start_char=0,
                end_char=len(text),
            )
        ]
    return sections


def classify_heading(line: str) -> str | None:
    if len(line) > 80:
        return None
    for section_type, pattern in SECTION_PATTERNS:
        if pattern.match(line):
            return section_type
    return None


def chunk_sections(
    sections: list[PaperSection],
    max_tokens_per_chunk: int = 800,
) -> list[PaperChunk]:
    chunks: list[PaperChunk] = []
    for section in sections:
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n", section.text) if item.strip()]
        current: list[str] = []
        current_tokens = 0

        for paragraph in paragraphs or [section.text]:
            tokens = estimate_tokens(paragraph)
            if current and current_tokens + tokens > max_tokens_per_chunk:
                chunks.append(_make_chunk(len(chunks) + 1, section, "\n\n".join(current)))
                current = [paragraph]
                current_tokens = tokens
            else:
                current.append(paragraph)
                current_tokens += tokens

        if current:
            chunks.append(_make_chunk(len(chunks) + 1, section, "\n\n".join(current)))

    return chunks


def estimate_tokens(text: str) -> int:
    ascii_words = re.findall(r"[A-Za-z0-9_]+", text)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    return max(1, len(ascii_words) + len(cjk_chars))


def _make_chunk(index: int, section: PaperSection, text: str) -> PaperChunk:
    return PaperChunk(
        chunk_id=f"chunk_{index:03d}",
        section_id=section.section_id,
        section_type=section.section_type,
        text=text,
        char_start=section.start_char,
        char_end=section.end_char,
        token_estimate=estimate_tokens(text),
    )
