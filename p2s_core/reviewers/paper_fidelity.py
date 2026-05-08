from __future__ import annotations

import re

from p2s_core.models import PaperClaim, ReviewResult, SuggestedFix
from p2s_core.reviewers.base import utc_now


HYPE_TERMS = [
    "證明",
    "完全解決",
    "革命性",
    "顛覆",
    "guarantee",
    "proves",
    "revolutionizes",
    "completely solves",
]


class PaperFidelityReviewer:
    name = "PaperFidelityReviewer"

    def review(self, claim: PaperClaim) -> ReviewResult:
        findings: list[str] = []
        fixes: list[SuggestedFix] = []
        pass_gate = True
        severity = "low"
        score = 1.0
        evidence_text = " ".join(span.text for span in claim.evidence_spans).lower()
        claim_text = claim.claim_text.lower()

        for term in HYPE_TERMS:
            if term.lower() in claim_text and term.lower() not in evidence_text:
                findings.append(f"Claim contains unsupported hype term: {term}")
                pass_gate = False
                severity = "high"
                score = min(score, 0.2)

        if claim.claim_type == "result" and not _contains_result_signal(evidence_text):
            findings.append("Result claim lacks numeric, comparative, or experimental evidence signal.")
            pass_gate = False
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        if claim.claim_type == "limitation" and claim.source_section.lower() not in {
            "limitation",
            "discussion",
            "conclusion",
            "limitations",
        }:
            findings.append("Limitation claim comes from a less typical section; human check recommended.")
            severity = _max_severity(severity, "medium")
            score = min(score, 0.7)

        if claim.certainty == "weak" and claim.importance >= 4:
            findings.append("High-importance claim is marked weak certainty.")
            pass_gate = False
            severity = _max_severity(severity, "high")
            score = min(score, 0.3)

        if not pass_gate:
            fixes.append(
                SuggestedFix(
                    target_type="claim",
                    target_id=claim.claim_id,
                    fix_type="rewrite",
                    suggestion="Narrow or rewrite this claim so it stays within the evidence.",
                    priority="high",
                )
            )

        return ReviewResult(
            review_id=f"paper_fidelity_{claim.claim_id}",
            target_type="claim",
            target_id=claim.claim_id,
            reviewer=self.name,
            score=score,
            pass_gate=pass_gate,
            severity=severity,
            findings=findings,
            suggested_fixes=fixes,
            created_at=utc_now(),
            reviewer_prompt_version="paper_fidelity_v1",
        )


def _contains_result_signal(text: str) -> bool:
    return bool(re.search(r"\d|%|better|higher|lower|improve|outperform|achieve|accuracy|score", text))


def _max_severity(current: str, candidate: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return candidate if order[candidate] > order[current] else current
