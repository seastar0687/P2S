from __future__ import annotations

import difflib
import re
from pathlib import Path

from p2s_core.models import EvidenceMatchReport
from p2s_core.services.text_normalization import normalize_text, relaxed_text


def load_evidence_source(run_dir: Path, normalized_path: str | None, raw_path: str | None) -> str:
    for candidate in (normalized_path, raw_path):
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = run_dir / path
        if path.exists():
            return path.read_text(encoding="utf-8")
    raw = run_dir / "extracted_text.md"
    if raw.exists():
        return raw.read_text(encoding="utf-8")
    raise FileNotFoundError(f"No extracted text source found under {run_dir}")


def match_evidence(
    evidence_text: str,
    source_text: str,
    *,
    claim_id: str = "unknown",
    section_hint: str | None = None,
) -> EvidenceMatchReport:
    warnings: list[str] = []
    evidence = evidence_text.strip()
    if not evidence:
        return EvidenceMatchReport(
            claim_id=claim_id,
            evidence_text=evidence_text,
            matched=False,
            match_score=0.0,
            match_method="not_found",
            matched_section=section_hint,
            warnings=["Evidence span text is empty."],
        )

    if evidence in source_text:
        return _report(claim_id, evidence_text, True, 1.0, "exact", section_hint, warnings)

    normalized_evidence = normalize_text(evidence)
    normalized_source = normalize_text(source_text)
    if normalized_evidence in normalized_source:
        return _report(claim_id, evidence_text, True, 1.0, "normalized_exact", section_hint, warnings)

    relaxed_evidence = relaxed_text(normalized_evidence)
    relaxed_source = relaxed_text(normalized_source)
    if relaxed_evidence and relaxed_evidence in relaxed_source:
        return _report(claim_id, evidence_text, True, 0.98, "normalized_exact", section_hint, warnings)

    words = relaxed_evidence.split()
    if len(words) < 8:
        matched, score = _short_quote_match(words, relaxed_source.split())
        if matched:
            warnings.append("short quote match used")
            return _report(claim_id, evidence_text, True, score, "short_quote", section_hint, warnings)
    else:
        matched, score = _windowed_fuzzy_match(relaxed_evidence, relaxed_source)
        if matched:
            warnings.append("fuzzy match used")
            return _report(claim_id, evidence_text, True, score, "fuzzy", section_hint, warnings)

    paragraph_score = _best_paragraph_score(normalized_evidence, normalized_source)
    if paragraph_score >= 0.90:
        warnings.append("fuzzy paragraph match used")
        return _report(claim_id, evidence_text, True, paragraph_score, "fuzzy", section_hint, warnings)

    return _report(
        claim_id,
        evidence_text,
        False,
        max(paragraph_score, 0.0),
        "not_found",
        section_hint,
        ["Evidence span was not found in extracted text."],
    )


def evidence_matches_source(evidence_text: str, source_text: str) -> bool:
    return match_evidence(evidence_text, source_text).matched


def _report(claim_id, evidence_text, matched, score, method, section, warnings):
    return EvidenceMatchReport(
        claim_id=claim_id,
        evidence_text=evidence_text,
        matched=matched,
        match_score=round(float(score), 4),
        match_method=method,
        matched_section=section,
        warnings=warnings,
    )


def _short_quote_match(evidence_words: list[str], source_words: list[str]) -> tuple[bool, float]:
    if not evidence_words or len(evidence_words) > len(source_words):
        return False, 0.0
    if len(evidence_words) < 3:
        return False, 0.0
    evidence = " ".join(evidence_words)
    best = 0.0
    window = len(evidence_words)
    for start in range(0, len(source_words) - window + 1):
        candidate = " ".join(source_words[start : start + window])
        ratio = difflib.SequenceMatcher(None, evidence, candidate).ratio()
        best = max(best, ratio)
        if ratio >= 0.92:
            return True, ratio
    return False, best


def _windowed_fuzzy_match(evidence_text: str, source_text: str) -> tuple[bool, float]:
    evidence_words = evidence_text.split()
    source_words = source_text.split()
    if not evidence_words or not source_words:
        return False, 0.0
    window_size = len(evidence_words)
    if window_size > len(source_words):
        return False, 0.0

    threshold = 0.90 if window_size < 12 else 0.85
    step = max(1, window_size // 4)
    best_ratio = 0.0
    for start in range(0, len(source_words) - window_size + 1, step):
        for extra in (-4, 0, 4):
            end = min(len(source_words), start + window_size + extra)
            if end <= start:
                continue
            candidate = " ".join(source_words[start:end])
            ratio = difflib.SequenceMatcher(None, evidence_text, candidate).ratio()
            best_ratio = max(best_ratio, ratio)
            if ratio >= threshold:
                return True, ratio
    return False, best_ratio


def _best_paragraph_score(evidence_text: str, source_text: str) -> float:
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", source_text) if item.strip()]
    if not paragraphs:
        return 0.0
    return max(difflib.SequenceMatcher(None, evidence_text, normalize_text(paragraph)).ratio() for paragraph in paragraphs)
