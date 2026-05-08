from p2s_core.services.text_chunking import build_extracted_paper, detect_sections


def test_detect_sections_from_common_headings():
    text = """Abstract

This paper introduces a method.

1 Introduction

The problem is important.

Methods

We train two encoders."""

    sections = detect_sections(text)

    assert [section.section_type for section in sections] == ["abstract", "introduction", "method"]
    assert sections[0].title == "Abstract"
    assert "two encoders" in sections[2].text


def test_build_extracted_paper_creates_chunks_under_budget():
    text = """Abstract

This paper introduces a method.

Results

The method improves accuracy by 5 percent."""

    paper = build_extracted_paper("demo", text, max_tokens_per_chunk=20)

    assert paper.project_id == "demo"
    assert paper.sections
    assert paper.chunks
    assert all(chunk.token_estimate <= 20 for chunk in paper.chunks)


def test_empty_text_raises_clear_error():
    try:
        build_extracted_paper("demo", "  ")
    except ValueError as exc:
        assert "extracted_text.md is empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
