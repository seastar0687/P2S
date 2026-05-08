from __future__ import annotations

from collections import defaultdict

from p2s_core.models import GateDecision, ReviewResult
from p2s_core.reviewers.base import utc_now


class Arbiter:
    name = "Arbiter"

    def decide(self, reviews: list[ReviewResult], total_claims: int) -> GateDecision:
        by_claim: dict[str, list[ReviewResult]] = defaultdict(list)
        for review in reviews:
            by_claim[review.target_id].append(review)

        rejected = 0
        needs_review = 0
        medium_fails = 0
        blocking: list[str] = []

        for claim_id, claim_reviews in by_claim.items():
            severities = [review.severity for review in claim_reviews if not review.pass_gate]
            if "critical" in severities:
                rejected += 1
                blocking.append(f"{claim_id}: critical fail")
            elif "high" in severities:
                needs_review += 1
                blocking.append(f"{claim_id}: high fail")
            elif "medium" in severities:
                medium_fails += 1

        denominator = max(1, total_claims)
        if rejected / denominator > 0.30:
            status = "reject"
        elif rejected or needs_review or medium_fails >= 3:
            status = "human_check"
        else:
            status = "pass"

        return GateDecision(
            gate_name="claim_extraction_gate",
            target_type="artifact",
            target_id="claim_extraction",
            status=status,
            blocking_issues=blocking,
            human_notes=[] if status == "pass" else ["Review claim-level findings before continuing."],
            aggregated_scores=self._aggregate_scores(reviews),
            contributing_reviews=[review.review_id for review in reviews],
            created_at=utc_now(),
        )

    @staticmethod
    def _aggregate_scores(reviews: list[ReviewResult]) -> dict[str, float]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for review in reviews:
            grouped[review.reviewer].append(review.score)
        return {
            reviewer: sum(scores) / len(scores)
            for reviewer, scores in grouped.items()
            if scores
        }
