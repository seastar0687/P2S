from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


Confidence = Literal["high", "medium", "low"]


class ExtractedSection(BaseModel):
    section_id: str
    title: str
    normalized_title: str
    level: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    text: str
    char_start: int | None = None
    char_end: int | None = None
    confidence: Confidence = "medium"
    detection_method: str = "regex"
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def title_must_not_be_empty(self) -> "ExtractedSection":
        if not self.title.strip():
            raise ValueError("section title must not be empty")
        return self


class ExtractedFigure(BaseModel):
    figure_id: str
    page: int | None = None
    image_path: str | None = None
    caption: str | None = None
    caption_source: Literal["direct", "nearby_text", "inferred", "missing"] = "missing"
    bbox: list[float] | None = None
    width: float | None = None
    height: float | None = None
    confidence: Confidence = "low"
    extraction_method: str = "pymupdf"
    risk_flags: list[str] = Field(default_factory=list)
    notes: str | None = None


class ExtractedTable(BaseModel):
    table_id: str
    page: int | None = None
    image_path: str | None = None
    caption: str | None = None
    caption_source: Literal["direct", "nearby_text", "inferred", "missing"] = "missing"
    extraction_method: str = "pymupdf_image"
    confidence: Confidence = "low"
    notes: str | None = None


class ExtractionQualityReport(BaseModel):
    project_id: str
    text_char_count: int
    page_count: int | None = None
    section_count: int
    detected_section_titles: list[str]
    missing_expected_sections: list[str]
    figure_count: int
    figures_with_caption_count: int
    figures_without_caption_count: int
    table_count: int
    tables_with_caption_count: int
    tables_without_caption_count: int
    normalization_applied: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    quality_level: Literal["good", "acceptable", "poor", "failed"]
    created_at: str


class EvidenceMatchReport(BaseModel):
    claim_id: str
    evidence_text: str
    matched: bool
    match_score: float
    match_method: Literal[
        "exact",
        "normalized_exact",
        "fuzzy",
        "short_quote",
        "not_found",
    ]
    matched_section: str | None = None
    matched_page: int | None = None
    warnings: list[str] = Field(default_factory=list)


class EvidenceMatchReportBundle(BaseModel):
    project_id: str
    reports: list[EvidenceMatchReport]
    created_at: str


class RealPaperSmokeReport(BaseModel):
    project_id: str
    paper_name: str
    stages_run: list[str]
    extraction_quality: ExtractionQualityReport
    claim_count: int
    failed_claim_review_count: int
    asset_plan_warning_count: int
    key_warnings: list[str] = Field(default_factory=list)
    passed: bool
    notes: str | None = None
    created_at: str
