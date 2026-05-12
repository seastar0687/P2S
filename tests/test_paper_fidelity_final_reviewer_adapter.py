from p2s_core.models import PaperClaim, ReviewResult
from p2s_core.models.common import EvidenceSpan, SuggestedFix
from p2s_core.reviewers.paper_fidelity_final import PaperFidelityFinalReviewer


def _claim():
    return PaperClaim(
        claim_id="claim_001",
        claim_text="The method improves accuracy.",
        claim_type="result",
        source_section="results",
        evidence_spans=[
            EvidenceSpan(section="results", text="The method improves accuracy by 5%.", confidence="direct")
        ],
        certainty="explicit",
        importance=4,
    )


def test_adapter_maps_failed_review_to_blocking_finding():
    review = ReviewResult(
        review_id="claim_evidence_claim_001",
        target_type="claim",
        target_id="claim_001",
        reviewer="ClaimEvidenceReviewer",
        score=0.2,
        pass_gate=False,
        severity="high",
        findings=["Evidence span does not match extracted_text.md."],
        suggested_fixes=[
            SuggestedFix(
                target_type="claim",
                target_id="claim_001",
                fix_type="human_check",
                suggestion="Fix evidence.",
                priority="high",
            )
        ],
        created_at="2026-05-12T00:00:00Z",
    )

    findings = PaperFidelityFinalReviewer().convert_review(review)

    assert findings[0].blocking is True
    assert findings[0].severity == "high"
    assert findings[0].suggested_fix == "Fix evidence."


def test_adapter_review_passes_grounded_claim():
    claim = _claim()
    summary = PaperFidelityFinalReviewer().review([claim], "The method improves accuracy by 5%.")
    assert summary.pass_gate is True
