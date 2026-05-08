from __future__ import annotations

from collections import defaultdict

from p2s_core.models import GateDecision, ReviewResult
from p2s_core.reviewers.base import utc_now


def decide_presentation_gate(reviews: list[ReviewResult]) -> GateDecision:
    failing = [review for review in reviews if not review.pass_gate]
    critical = [review for review in reviews if review.severity == "critical"]
    high = [review for review in reviews if review.severity == "high"]
    medium = [review for review in reviews if review.severity == "medium"]

    if critical:
        status = "reject"
        summary = "Presentation gate rejected due to critical grounding or asset contract failures."
    elif high:
        status = "human_check"
        summary = "Presentation gate requires human review due to high-severity findings."
    elif medium:
        status = "human_check"
        summary = "Presentation gate requires human review due to medium-severity warnings."
    else:
        status = "pass"
        summary = "Presentation gate passed."

    blocking = [
        f"{review.target_id}: {finding}"
        for review in critical + high
        for finding in review.findings
    ]
    human_notes = [
        f"{review.target_id}: {finding}"
        for review in medium
        for finding in review.findings
    ]

    return GateDecision(
        gate_name="presentation_gate",
        target_type="presentation",
        target_id="presentation_planning",
        status=status,
        summary=summary,
        blocking_issues=blocking,
        human_notes=human_notes,
        aggregated_scores=_aggregate_scores(reviews),
        contributing_reviews=[review.review_id for review in reviews],
        created_at=utc_now(),
    )


def _aggregate_scores(reviews: list[ReviewResult]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for review in reviews:
        grouped[review.reviewer].append(review.score)
    return {
        reviewer: sum(scores) / len(scores)
        for reviewer, scores in grouped.items()
        if scores
    }
