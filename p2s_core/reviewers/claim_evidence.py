from __future__ import annotations

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

            from p2s_core.services.evidence_matching import match_evidence

            match = match_evidence(
                span.text,
                extracted_text,
                claim_id=claim.claim_id,
                section_hint=span.section,
            )
            if not match.matched:
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


def _max_severity(current: str, candidate: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return candidate if order[candidate] > order[current] else current
