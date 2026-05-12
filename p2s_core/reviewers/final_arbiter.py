from __future__ import annotations

from p2s_core.models import FinalGateDecision, FinalReviewBundle, ReviewerSummary
from p2s_core.reviewers.base import utc_now


class FinalArbiter:
    name = "FinalArbiter"

    def decide(self, bundle: FinalReviewBundle) -> FinalGateDecision:
        blocking = list(bundle.blocking_issues)
        reviewer_statuses = {
            summary.reviewer: "pass" if summary.pass_gate else "fail"
            for summary in bundle.reviewer_summaries
        }
        failing_reviewers = [
            summary.reviewer for summary in bundle.reviewer_summaries if not summary.pass_gate
        ]

        if any(finding.severity == "critical" for finding in blocking):
            status = "reject"
            rationale = (
                f"Rejected because {len(blocking)} blocking issue(s) include a critical finding."
            )
        elif blocking:
            status = "human_check"
            rationale = f"Human check required because {len(blocking)} blocking issue(s) were found."
        elif failing_reviewers:
            status = "human_check"
            rationale = "Human check required because reviewer(s) failed without blocking findings: " + ", ".join(failing_reviewers)
        else:
            status = "pass"
            rationale = f"Passed final review with {len(bundle.warnings)} warning(s)."

        return FinalGateDecision(
            project_id=bundle.project_id,
            review_id=bundle.review_id,
            status=status,
            blocking_issues=blocking,
            warning_count=len(bundle.warnings),
            reviewer_statuses=reviewer_statuses,
            rationale=rationale,
            created_at=utc_now(),
        )


def summarize_findings(reviewer: str, findings, *, score: float | None = None) -> ReviewerSummary:
    blocking_count = sum(1 for finding in findings if finding.blocking)
    warning_count = sum(1 for finding in findings if not finding.blocking and finding.severity != "info")
    return ReviewerSummary(
        reviewer=reviewer,
        pass_gate=blocking_count == 0,
        score=score,
        findings=list(findings),
        blocking_count=blocking_count,
        warning_count=warning_count,
        created_at=utc_now(),
    )
