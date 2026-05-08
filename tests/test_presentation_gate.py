from p2s_core.models import ReviewResult
from p2s_core.reviewers.presentation_gate import decide_presentation_gate


def test_presentation_gate_passes_clean_reviews():
    gate = decide_presentation_gate([_review("clean", "low", True)])

    assert gate.status == "pass"
    assert gate.summary == "Presentation gate passed."


def test_presentation_gate_rejects_critical_failure():
    gate = decide_presentation_gate([_review("bad", "critical", False)])

    assert gate.status == "reject"
    assert gate.blocking_issues


def test_presentation_gate_human_check_for_high_failure():
    gate = decide_presentation_gate([_review("risky", "high", False)])

    assert gate.status == "human_check"
    assert gate.blocking_issues


def test_presentation_gate_human_check_for_medium_warning():
    gate = decide_presentation_gate([_review("warning", "medium", True)])

    assert gate.status == "human_check"
    assert gate.human_notes


def _review(review_id: str, severity: str, pass_gate: bool):
    return ReviewResult(
        review_id=review_id,
        target_type="scene",
        target_id="scene_001",
        reviewer="FakeReviewer",
        score=1.0 if pass_gate else 0.0,
        pass_gate=pass_gate,
        severity=severity,
        findings=[] if pass_gate and severity == "low" else ["finding"],
        created_at="2026-05-08T00:00:00Z",
    )
