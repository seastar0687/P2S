from p2s_core.models import SceneDraft
from p2s_core.reviewers.script_grounding import ScriptGroundingReviewer
from tests.test_mvp2a_fixtures import make_claim


def test_script_grounding_unknown_claim_id_critical_fail():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_missing"],
        voice_text="The method compares encoders.",
        subtitle_text="Compares encoders.",
        target_duration_sec=6,
    )

    review = ScriptGroundingReviewer().review([scene], [make_claim("claim_001", "The method compares encoders.")])[0]

    assert not review.pass_gate
    assert review.severity == "critical"


def test_script_grounding_non_transition_without_claim_id_critical_fail():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=[],
        voice_text="The method compares encoders.",
        subtitle_text="Compares encoders.",
        target_duration_sec=6,
    )

    review = ScriptGroundingReviewer().review([scene], [make_claim("claim_001", "The method compares encoders.")])[0]

    assert not review.pass_gate
    assert review.severity == "critical"


def test_script_grounding_unsupported_phrase_high_fail():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="result",
        claim_ids=["claim_001"],
        voice_text="This proves the method completely solves the task.",
        subtitle_text="It proves it.",
        target_duration_sec=6,
    )

    review = ScriptGroundingReviewer().review([scene], [make_claim("claim_001", "The method improves one benchmark.")])[0]

    assert not review.pass_gate
    assert review.severity == "high"


def test_script_grounding_required_asset_without_intent_critical_fail():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="The method compares encoders.",
        subtitle_text="Compares encoders.",
        target_duration_sec=6,
        asset_policy="required",
        asset_type_hint="none",
    )

    review = ScriptGroundingReviewer().review([scene], [make_claim("claim_001", "The method compares encoders.")])[0]

    assert not review.pass_gate
    assert review.severity == "critical"
