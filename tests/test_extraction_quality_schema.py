from p2s_core.models import (
    EvidenceMatchReport,
    EvidenceMatchReportBundle,
    ExtractedFigure,
    ExtractedSection,
    ExtractedTable,
    ExtractionQualityReport,
    ProjectState,
    RealPaperSmokeReport,
)


def test_harden1_schema_roundtrips():
    section = ExtractedSection(
        section_id="section_001",
        title="Abstract",
        normalized_title="abstract",
        text="Abstract text.",
    )
    figure = ExtractedFigure(figure_id="fig_001", page=1, caption="Figure 1. Result.")
    table = ExtractedTable(table_id="table_001", page=1, caption="Table 1. Values.")
    quality = ExtractionQualityReport(
        project_id="schema",
        text_char_count=1000,
        page_count=1,
        section_count=1,
        detected_section_titles=["Abstract"],
        missing_expected_sections=[],
        figure_count=1,
        figures_with_caption_count=1,
        figures_without_caption_count=0,
        table_count=1,
        tables_with_caption_count=1,
        tables_without_caption_count=0,
        quality_level="good",
        created_at="2026-05-11T00:00:00Z",
    )
    evidence = EvidenceMatchReport(
        claim_id="claim_001",
        evidence_text="Evidence text.",
        matched=True,
        match_score=1.0,
        match_method="exact",
    )
    bundle = EvidenceMatchReportBundle(
        project_id="schema",
        reports=[evidence],
        created_at="2026-05-11T00:00:00Z",
    )
    smoke = RealPaperSmokeReport(
        project_id="schema",
        paper_name="paper.pdf",
        stages_run=["extraction"],
        extraction_quality=quality,
        claim_count=0,
        failed_claim_review_count=0,
        asset_plan_warning_count=0,
        passed=True,
        created_at="2026-05-11T00:00:00Z",
    )

    assert ExtractedSection.model_validate_json(section.model_dump_json()).section_id == "section_001"
    assert ExtractedFigure.model_validate_json(figure.model_dump_json()).figure_id == "fig_001"
    assert ExtractedTable.model_validate_json(table.model_dump_json()).table_id == "table_001"
    assert ExtractionQualityReport.model_validate_json(quality.model_dump_json()).quality_level == "good"
    assert EvidenceMatchReportBundle.model_validate_json(bundle.model_dump_json()).reports[0].matched
    assert RealPaperSmokeReport.model_validate_json(smoke.model_dump_json()).passed


def test_old_project_state_without_harden1_fields_loads():
    state = ProjectState.model_validate(
        {
            "project_id": "old",
            "created_at": "2026-05-11T00:00:00Z",
            "source": {"pdf_path": "runs/old/source.pdf"},
            "persona": {"persona_id": "seina"},
            "style": {"style_id": "rigorous_science_short"},
            "extraction": {"text_md": "extracted_text.md"},
            "stages": {},
        }
    )

    assert state.extraction.sections_path is None
    assert state.extraction.figures == []
