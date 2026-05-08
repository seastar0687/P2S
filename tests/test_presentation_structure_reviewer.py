from p2s_core.models import SceneDraft
from p2s_core.reviewers.presentation_structure import PresentationStructureReviewer
from p2s_core.services.persona_style import load_presentation_profile
from p2s_core.services.presentation_planning import build_presentation_plan


def test_presentation_structure_fullscreen_ratio_high_fail():
    profile = load_presentation_profile()
    scenes = [
        _scene("scene_001", visual_focus="asset_fullscreen", presenter_mode="minimized", asset_policy="required"),
        _scene("scene_002", visual_focus="asset_fullscreen", presenter_mode="minimized", asset_policy="required"),
        _scene("scene_003", visual_focus="presenter", presenter_mode="speaking_on_camera", asset_policy="none"),
    ]
    plan = build_presentation_plan("demo", scenes, profile)

    review = PresentationStructureReviewer().review(scenes, plan, profile)[0]

    assert not review.pass_gate
    assert review.severity == "high"


def test_presentation_structure_all_required_assets_warning():
    profile = load_presentation_profile()
    scenes = [
        _scene("scene_001", asset_policy="required"),
        _scene("scene_002", asset_policy="required"),
    ]
    plan = build_presentation_plan("demo", scenes, profile)

    review = PresentationStructureReviewer().review(scenes, plan, profile)[0]

    assert review.pass_gate
    assert review.severity == "medium"
    assert any("Every scene requires" in finding for finding in review.findings)


def _scene(
    scene_id,
    visual_focus="supporting_asset",
    presenter_mode="speaking_with_overlay",
    asset_policy="optional",
):
    return SceneDraft(
        scene_id=scene_id,
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="A grounded method.",
        subtitle_text="Method.",
        target_duration_sec=6,
        presenter_mode=presenter_mode,
        visual_focus=visual_focus,
        asset_policy=asset_policy,
        asset_intent="A diagram.",
        asset_type_hint="diagram" if asset_policy != "none" else "none",
    )
