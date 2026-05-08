from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PaperSection(BaseModel):
    section_id: str
    title: str
    section_type: Literal[
        "abstract",
        "introduction",
        "background",
        "method",
        "experiment",
        "result",
        "discussion",
        "limitation",
        "conclusion",
        "unknown",
    ] = "unknown"
    text: str
    start_char: int | None = None
    end_char: int | None = None
    page_start: int | None = None
    page_end: int | None = None


class PaperChunk(BaseModel):
    chunk_id: str
    section_id: str
    section_type: str
    text: str
    char_start: int | None = None
    char_end: int | None = None
    token_estimate: int | None = None


class ExtractedPaper(BaseModel):
    project_id: str
    sections: list[PaperSection] = Field(default_factory=list)
    chunks: list[PaperChunk] = Field(default_factory=list)

