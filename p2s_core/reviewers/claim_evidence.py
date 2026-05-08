from __future__ import annotations

import difflib
import re

from p2s_core.models import PaperClaim, ReviewResult, SuggestedFix
from p2s_core.reviewers.base import utc_now


class ClaimEvidenceReviewer:
    name = "ClaimEvidenceReviewer"

    def review(self, claim: PaperClaim, extracted_text: str) -> ReviewResult:
        findings: list[str] = []
        fixes: list[SuggestedFix] = []
        severity = "low"
        pass_gate = True
        score = 1.0

        if not claim.evidence_spans:
            findings.append("Claim has no evidence_spans.")
            fixes.append(self._fix(claim.claim_id, "Add a direct evidence span or remove this claim."))
            return self._result(claim, 0.0, False, "critical", findings, fixes)

        for span in claim.evidence_spans:
            if not span.text.strip():
                findings.append("Evidence span text is empty.")
                pass_gate = False
                severity = _max_severity(severity, "critical")
                score = min(score, 0.0)
                continue

            if not _has_minimum_length(span.text):
                findings.append("Evidence span is too short to support the claim.")
                pass_gate = False
                severity = _max_severity(severity, "medium")
                score = min(score, 0.5)

            if span.confidence == "weak":
                findings.append("Evidence confidence is weak.")
                pass_gate = False
                severity = _max_severity(severity, "medium")
                score = min(score, 0.5)

            if not _evidence_matches_source(span.text, extracted_text):
                findings.append("Evidence span does not match extracted_text.md.")
                pass_gate = False
                severity = _max_severity(severity, "high")
                score = min(score, 0.2)

        if not pass_gate:
            fixes.append(self._fix(claim.claim_id, "Replace weak or unmatched evidence with a direct source span."))

        return self._result(claim, score, pass_gate, severity, findings, fixes)

    def _result(self, claim, score, pass_gate, severity, findings, fixes):
        return ReviewResult(
            review_id=f"claim_evidence_{claim.claim_id}",
            target_type="claim",
            target_id=claim.claim_id,
            reviewer=self.name,
            score=score,
            pass_gate=pass_gate,
            severity=severity,
            findings=findings,
            suggested_fixes=fixes,
            created_at=utc_now(),
            reviewer_prompt_version="claim_evidence_v1",
        )

    @staticmethod
    def _fix(target_id: str, suggestion: str) -> SuggestedFix:
        return SuggestedFix(
            target_type="claim",
            target_id=target_id,
            fix_type="human_check",
            suggestion=suggestion,
            priority="high",
        )


def _has_minimum_length(text: str) -> bool:
    if len(text.strip()) >= 30:
        return True
    return len(re.findall(r"[A-Za-z0-9_]+", text)) >= 8


def _evidence_matches_source(evidence_text: str, extracted_text: str) -> bool:
    if evidence_text in extracted_text:
        return True
    normalized_evidence = _normalize_text(evidence_text)
    normalized_source = _normalize_text(extracted_text)
    if normalized_evidence in normalized_source:
        return True
    relaxed_evidence = _relaxed_text(normalized_evidence)
    relaxed_source = _relaxed_text(normalized_source)
    if relaxed_evidence in relaxed_source:
        return True
    if _windowed_fuzzy_match(relaxed_evidence, relaxed_source):
        return True
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", extracted_text) if item.strip()]
    if not paragraphs:
        return False
    return max(
        difflib.SequenceMatcher(None, normalized_evidence, _normalize_text(paragraph)).ratio()
        for paragraph in paragraphs
    ) >= 0.85


def _normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\u2009", " ").replace("\u00a0", " ")
    text = re.sub(r"([A-Za-z])-\s+([a-z])", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip()


def _relaxed_text(text: str) -> str:
    text = _normalize_text(text).lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text).strip()


def _windowed_fuzzy_match(evidence_text: str, source_text: str) -> bool:
    evidence_words = evidence_text.split()
    source_words = source_text.split()
    if not evidence_words or not source_words:
        return False

    window_size = len(evidence_words)
    if window_size > len(source_words):
        return False

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
                return True
    return best_ratio >= threshold


def _max_severity(current: str, candidate: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return candidate if order[candidate] > order[current] else current
