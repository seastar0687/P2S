from p2s_core.models import NarrativeArcItem, NarrativePlan, SceneDraft
from p2s_core.services.persona_style import load_presentation_profile
from p2s_core.services.presentation_planning import build_presentation_plan, build_scenes_bundle
from tests.test_mvp2a_fixtures import make_claim, make_state


def make_plan():
    return NarrativePlan(
        project_id="mvp2a_presentation",
        target_duration_sec=60,
        language="zh-TW",
        audience="general_science",
        selected_claim_ids=["claim_001", "claim_002"],
        narrative_arc=[
            NarrativeArcItem(purpose="hook", claim_ids=["claim_001"], intent="hook"),
            NarrativeArcItem(purpose="method", claim_ids=["claim_002"], intent="method"),
            NarrativeArcItem(purpose="takeaway", claim_ids=["claim_001"], intent="takeaway"),
        ],
        omitted_claim_ids=[],
        rationale="test",
        created_at="2026-05-08T00:00:00Z",
    )


def test_presentation_planning_produces_string_scene_ids_and_valid_claims():
    state = make_state("mvp2a_presentation")
    claims = [
        make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5),
        make_claim("claim_002", "The method compares two encoders.", "method", 4),
    ]
    profile = load_presentation_profile()

    bundle = build_scenes_bundle(state, claims, make_plan(), profile)

    assert [scene.scene_id for scene in bundle.scenes] == ["scene_001", "scene_002", "scene_003"]
    assert all(scene.claim_ids for scene in bundle.scenes if scene.purpose != "transition")
    assert all(isinstance(scene.scene_id, str) for scene in bundle.scenes)


def test_presenter_first_does_not_require_every_scene_asset():
    state = make_state("mvp2a_presentation")
    claims = [
        make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5),
        make_claim("claim_002", "The method compares two encoders.", "method", 4),
    ]
    profile = load_presentation_profile()

    bundle = build_scenes_bundle(state, claims, make_plan(), profile)

    assert any(scene.asset_policy == "none" for scene in bundle.scenes)
    assert not all(scene.asset_policy == "required" for scene in bundle.scenes)
    assert all(scene.background_mode == "static_clean" for scene in bundle.scenes)


def test_presentation_plan_ratios_are_computed():
    profile = load_presentation_profile()
    scenes = [
        SceneDraft(
            scene_id="scene_001",
            purpose="hook",
            claim_ids=["claim_001"],
            voice_text="A grounded hook.",
            subtitle_text="Grounded.",
            target_duration_sec=5,
            asset_policy="none",
            visual_focus="presenter",
        ),
        SceneDraft(
            scene_id="scene_002",
            purpose="method",
            claim_ids=["claim_002"],
            voice_text="A grounded method.",
            subtitle_text="Method.",
            target_duration_sec=8,
            presenter_mode="speaking_with_overlay",
            asset_policy="optional",
            visual_focus="supporting_asset",
            asset_type_hint="diagram",
        ),
    ]

    plan = build_presentation_plan("mvp2a_presentation", scenes, profile)

    assert plan.presenter_visibility_ratio == 1.0
    assert plan.asset_scene_ratio == 0.5
    assert plan.fullscreen_asset_ratio == 0.0
    assert plan.quality_report["scene_count"] == 2
