from p2s_core.models import SceneDraft
from p2s_core.reviewers.style_rule import StyleRuleReviewer
from tests.test_mvp2a_fixtures import make_state


def test_style_rule_forbidden_phrase_high_fail():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="hook",
        claim_ids=["claim_001"],
        voice_text="這篇研究是革命性的突破。",
        subtitle_text="革命性突破",
        target_duration_sec=6,
    )

    review = StyleRuleReviewer().review([scene], make_state().style)[0]

    assert not review.pass_gate
    assert review.severity == "high"


def test_style_rule_subtitle_too_long_medium_warning():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="This method compares representations before prediction.",
        subtitle_text="This subtitle is definitely too long for the selected short style.",
        target_duration_sec=6,
    )

    review = StyleRuleReviewer().review([scene], make_state().style)[0]

    assert review.pass_gate
    assert review.severity == "medium"


def test_style_rule_subtitle_must_be_shorter_than_voice():
    scene = SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="Short text.",
        subtitle_text="This subtitle is longer than the voice text.",
        target_duration_sec=6,
    )

    review = StyleRuleReviewer().review([scene], make_state().style)[0]

    assert review.severity == "medium"
    assert any("shorter" in finding for finding in review.findings)
