from p2s_core.models import FinalGateDecision, FinalReviewBundle, ReviewerFinding, ReviewerSummary


def test_final_review_schemas_roundtrip():
    finding = ReviewerFinding(
        finding_id="f1",
        reviewer="Reviewer",
        target_type="scene",
        target_id="scene_001",
        severity="medium",
        category="overhype",
        message="Too strong.",
    )
    summary = ReviewerSummary(
        reviewer="Reviewer",
        pass_gate=True,
        findings=[finding],
        warning_count=1,
        created_at="2026-05-12T00:00:00Z",
    )
    bundle = FinalReviewBundle(
        project_id="p",
        review_id="final_review_rev001",
        active_scene_source="scenes.json",
        reviewer_summaries=[summary],
        total_findings=1,
        warnings=[finding],
        created_at="2026-05-12T00:00:00Z",
    )
    decision = FinalGateDecision(
        project_id="p",
        review_id=bundle.review_id,
        status="pass",
        warning_count=1,
        rationale="ok",
        created_at="2026-05-12T00:00:00Z",
    )

    assert ReviewerFinding.model_validate_json(finding.model_dump_json()).finding_id == "f1"
    assert ReviewerSummary.model_validate_json(summary.model_dump_json()).reviewer == "Reviewer"
    assert FinalReviewBundle.model_validate_json(bundle.model_dump_json()).review_id == "final_review_rev001"
    assert FinalGateDecision.model_validate_json(decision.model_dump_json()).status == "pass"
