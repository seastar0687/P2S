from pathlib import Path

from p2s_core.services.evidence_matching import load_evidence_source, match_evidence


SOURCE = "Results\n\nThe proposed method improves accuracy by 5 percent on the benchmark dataset."


def test_exact_and_normalized_matches():
    assert match_evidence("improves accuracy by 5 percent", SOURCE).match_method == "exact"
    report = match_evidence(
        "The proposed method improves accuracy by 5 percent on the benchmark dataset.",
        "The proposed method improves accuracy by 5 percent\non the benchmark dataset.",
    )

    assert report.matched
    assert report.match_method == "normalized_exact"


def test_hyphenation_and_fuzzy_matches():
    source = "Subliminal learning requires that the stu-\ndent starts similar to the teacher."
    report = match_evidence(
        "Subliminal learning requires that the student starts similar to the teacher.",
        source,
    )

    assert report.matched


def test_short_quote_match_and_not_found():
    assert match_evidence("benchmark dataset", SOURCE).matched
    assert not match_evidence("completely unrelated sentence", SOURCE).matched


def test_false_positive_guard():
    source = "The model improves calibration on a benchmark."
    report = match_evidence("The model improves accuracy on a benchmark.", source)

    assert not report.matched


def test_load_evidence_source_prefers_normalized_but_falls_back_to_raw(tmp_path: Path):
    (tmp_path / "extracted_text.md").write_text("raw", encoding="utf-8")
    assert load_evidence_source(tmp_path, "missing.md", "extracted_text.md") == "raw"
    (tmp_path / "extracted_text_normalized.md").write_text("normalized", encoding="utf-8")
    assert load_evidence_source(tmp_path, "extracted_text_normalized.md", "extracted_text.md") == "normalized"
