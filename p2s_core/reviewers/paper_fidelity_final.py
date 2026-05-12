from __future__ import annotations

from p2s_core.models import PaperClaim, ReviewerFinding, ReviewerSummary, SceneDraft
from p2s_core.models.review import ReviewResult
from p2s_core.reviewers.claim_evidence import ClaimEvidenceReviewer
from p2s_core.reviewers.final_arbiter import summarize_findings
from p2s_core.reviewers.paper_fidelity import PaperFidelityReviewer


class PaperFidelityFinalReviewer:
    name = "PaperFidelityFinalReviewer"

    def __init__(self) -> None:
        self.claim_evidence = ClaimEvidenceReviewer()
        self.paper_fidelity = PaperFidelityReviewer()

    def review(
        self,
        claims: list[PaperClaim],
        extracted_text: str,
        scenes: list[SceneDraft] | None = None,
    ) -> ReviewerSummary:
        findings: list[ReviewerFinding] = []
        for claim in claims:
            findings.extend(self.convert_review(self.claim_evidence.review(claim, extracted_text)))
            findings.extend(self.convert_review(self.paper_fidelity.review(claim)))
        findings.extend(self._review_limitation_coverage(claims, scenes or []))
        return summarize_findings(self.name, findings)

    def convert_review(self, review: ReviewResult) -> list[ReviewerFinding]:
        if not review.findings and review.pass_gate:
            return [
                ReviewerFinding(
                    finding_id=f"{self.name}:{review.review_id}:pass",
                    reviewer=self.name,
                    target_type=review.target_type,
                    target_id=review.target_id,
                    severity="info",
                    category="other",
                    message=f"{review.reviewer} passed.",
                    evidence_refs=review.evidence_refs,
                    blocking=False,
                )
            ]

        converted: list[ReviewerFinding] = []
        for index, message in enumerate(review.findings or ["Reviewer gate failed."], start=1):
            converted.append(
                ReviewerFinding(
                    finding_id=f"{self.name}:{review.review_id}:{index:03d}",
                    reviewer=self.name,
                    target_type=review.target_type,
                    target_id=review.target_id,
                    severity=_severity(review),
                    category=_category(message),
                    message=f"{review.reviewer}: {message}",
                    evidence_refs=review.evidence_refs,
                    suggested_fix=_suggested_fix(review),
                    blocking=not review.pass_gate,
                )
            )
        return converted

    def _review_limitation_coverage(
        self,
        claims: list[PaperClaim],
        scenes: list[SceneDraft],
    ) -> list[ReviewerFinding]:
        limitation_claims = [claim for claim in claims if claim.claim_type == "limitation"]
        if not limitation_claims or not scenes:
            return []

        covered_claim_ids = {
            claim_id
            for scene in scenes
            for claim_id in scene.claim_ids
            if scene.purpose == "limitation" or "limit" in scene.voice_text.lower() or "限制" in scene.voice_text
        }
        findings: list[ReviewerFinding] = []
        for claim in limitation_claims:
            if claim.claim_id in covered_claim_ids:
                continue
            blocking = claim.importance >= 4
            findings.append(
                ReviewerFinding(
                    finding_id=f"{self.name}:limitation_missing:{claim.claim_id}",
                    reviewer=self.name,
                    target_type="claim",
                    target_id=claim.claim_id,
                    severity="high" if blocking else "medium",
                    category="limitation_missing",
                    message=f"Limitation claim is not represented in final scenes: {claim.claim_id}",
                    suggested_fix="Add or restore a limitation scene before publishing.",
                    blocking=blocking,
                )
            )
        return findings


def _severity(review: ReviewResult) -> str:
    if review.pass_gate:
        return "info"
    return review.severity


def _category(message: str) -> str:
    lower = message.lower()
    if "evidence" in lower:
        return "missing_evidence"
    if "hype" in lower or "unsupported" in lower:
        return "unsupported_claim"
    return "unsupported_claim"


def _suggested_fix(review: ReviewResult) -> str | None:
    if not review.suggested_fixes:
        return None
    return review.suggested_fixes[0].suggestion
