from p2s_core.services.paper_extraction import detect_sections


def test_detects_common_and_numbered_sections():
    sections = detect_sections("Abstract\nPaper summary.\n\n1 Introduction\nIntro text.\n\nII. Results\nResult text.")

    assert [section.normalized_title for section in sections] == ["abstract", "introduction", "results"]


def test_uppercase_heading_detection():
    sections = detect_sections("METHODS\nMethod text.\n\nCONCLUSION\nDone.")

    assert [section.normalized_title for section in sections] == ["methods", "conclusion"]


def test_fallback_full_text_when_no_sections():
    sections = detect_sections("No obvious headings here, just text.")

    assert sections[0].title == "Full Text"
    assert sections[0].confidence == "low"


def test_avoids_figure_caption_as_section_and_repeated_header_footer():
    text = "\n".join(
        [
            "Paper Header",
            "Abstract",
            "Summary.",
            "Paper Header",
            "Figure 1. Not a section.",
            "Introduction",
            "Intro.",
            "Paper Header",
        ]
    )

    sections = detect_sections(text)

    assert "figure_1_not_a_section" not in [section.normalized_title for section in sections]
    assert "paper_header" not in [section.normalized_title for section in sections]
