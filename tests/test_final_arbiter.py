from p2s_core.models import FinalReviewBundle, ReviewerFinding, ReviewerSummary
from p2s_core.reviewers.final_arbiter import FinalArbiter


def _finding(severity="medium", blocking=False):
    return ReviewerFinding(
        finding_id=f"{severity}_{blocking}",
        reviewer="R",
        target_type="scene",
        target_id="s1",
        severity=severity,
        category="other",
        message="issue",
        blocking=blocking,
    )


def _bundle(findings=None, pass_gate=True):
    findings = findings or []
    summary = ReviewerSummary(
        reviewer="R",
        pass_gate=pass_gate,
        findings=findings,
        blocking_count=sum(1 for f in findings if f.blocking),
        warning_count=sum(1 for f in findings if not f.blocking and f.severity != "info"),
        created_at="2026-05-12T00:00:00Z",
    )
    return FinalReviewBundle(
        project_id="p",
        review_id="final_review_rev001",
        active_scene_source="scenes.json",
        reviewer_summaries=[summary],
        total_findings=len(findings),
        blocking_issues=[f for f in findings if f.blocking],
        warnings=[f for f in findings if not f.blocking and f.severity != "info"],
        created_at="2026-05-12T00:00:00Z",
    )


def test_no_blocking_passes():
    assert FinalArbiter().decide(_bundle()).status == "pass"


def test_critical_blocking_rejects():
    assert FinalArbiter().decide(_bundle([_finding("critical", True)])).status == "reject"


def test_any_noncritical_blocking_requires_human_check():
    for severity in ["high", "medium", "low"]:
        assert FinalArbiter().decide(_bundle([_finding(severity, True)])).status == "human_check"


def test_reviewer_fail_without_blocking_requires_human_check():
    assert FinalArbiter().decide(_bundle([], pass_gate=False)).status == "human_check"


def test_warnings_only_pass():
    assert FinalArbiter().decide(_bundle([_finding("medium", False)])).status == "pass"
