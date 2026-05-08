from __future__ import annotations

from pathlib import Path

from p2s_core.models import (
    NarrativePlan,
    PaperClaim,
    PresentationPlan,
    PresentationProfile,
    PresentationScene,
    ProjectState,
    SceneDraft,
    ScenesBundle,
)
from p2s_core.models.scene import ScenePurpose
from p2s_core.reviewers.presentation_structure import PresentationStructureReviewer
from p2s_core.reviewers.script_grounding import ScriptGroundingReviewer
from p2s_core.reviewers.style_rule import StyleRuleReviewer
from p2s_core.reviewers.presentation_gate import decide_presentation_gate
from p2s_core.models import PresentationReviewBundle
import p2s_core.services.persistence as persistence
from p2s_core.services.narrative_planning import load_project_claims, utc_now
from p2s_core.services.persona_style import load_presentation_profile


def run_presentation_planning_stage(state: ProjectState) -> ProjectState:
    project_dir = persistence.project_dir(state.project_id)
    claims = load_project_claims(state, project_dir)
    narrative_plan = load_narrative_plan(state, project_dir)
    profile = load_presentation_profile()

    scenes_bundle = build_scenes_bundle(state, claims, narrative_plan, profile)
    presentation_plan = build_presentation_plan(state.project_id, scenes_bundle.scenes, profile)
    review_bundle = review_presentation_plan(
        state=state,
        claims=claims,
        scenes_bundle=scenes_bundle,
        presentation_plan=presentation_plan,
        profile=profile,
    )

    (project_dir / "scenes.json").write_text(scenes_bundle.model_dump_json(indent=2), encoding="utf-8")
    (project_dir / "presentation_plan.json").write_text(
        presentation_plan.model_dump_json(indent=2),
        encoding="utf-8",
    )
    reviews_dir = project_dir / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    review_path = reviews_dir / "presentation_review_rev001.json"
    review_path.write_text(review_bundle.model_dump_json(indent=2), encoding="utf-8")

    state.presentation_plan = presentation_plan.model_dump()
    state.script["scenes"] = [scene.model_dump() for scene in scenes_bundle.scenes]
    state.reviews.extend(review_bundle.reviews)
    stage = state.stages["presentation_planning"]
    stage.output_paths = [
        "scenes.json",
        "presentation_plan.json",
        "reviews/presentation_review_rev001.json",
    ]
    if review_bundle.gate_decision.status == "pass":
        stage.status = "done"
    elif review_bundle.gate_decision.status == "human_check":
        stage.status = "needs_review"
    else:
        stage.status = "rejected"
    return state


def load_narrative_plan(state: ProjectState, project_dir: Path | None = None) -> NarrativePlan:
    if state.narrative_plan:
        return NarrativePlan.model_validate(state.narrative_plan)

    project_dir = project_dir or persistence.project_dir(state.project_id)
    path = project_dir / "narrative_plan.json"
    if not path.exists():
        raise FileNotFoundError(f"narrative_plan.json not found: {path}")
    return NarrativePlan.model_validate_json(path.read_text(encoding="utf-8"))


def build_scenes_bundle(
    state: ProjectState,
    claims: list[PaperClaim],
    narrative_plan: NarrativePlan,
    profile: PresentationProfile,
) -> ScenesBundle:
    claim_map = {claim.claim_id: claim for claim in claims}
    max_voice_chars = int(state.style.get("sentence_rules", {}).get("max_voice_chars_per_scene", 55))
    max_subtitle_chars = int(state.style.get("subtitle_rules", {}).get("max_subtitle_chars", 24))
    scene_count = max(1, len(narrative_plan.narrative_arc))
    duration = max(4.0, min(12.0, narrative_plan.target_duration_sec / scene_count))
    scenes: list[SceneDraft] = []

    for index, item in enumerate(narrative_plan.narrative_arc, start=1):
        linked_claims = [claim_map[claim_id] for claim_id in item.claim_ids if claim_id in claim_map]
        scene_id = f"scene_{index:03d}"
        voice_text = _voice_text(item.purpose, linked_claims, max_voice_chars)
        subtitle_text = _subtitle_text(voice_text, max_subtitle_chars)
        fields = _presentation_fields(item.purpose, linked_claims, profile)
        scenes.append(
            SceneDraft(
                scene_id=scene_id,
                purpose=item.purpose,
                claim_ids=item.claim_ids,
                voice_text=voice_text,
                subtitle_text=subtitle_text,
                target_duration_sec=round(duration, 2),
                presenter_mode=fields["presenter_mode"],
                visual_focus=fields["visual_focus"],
                asset_policy=fields["asset_policy"],
                asset_intent=fields["asset_intent"],
                asset_type_hint=fields["asset_type_hint"],
                background_mode=profile.default_background_mode,
                notes_for_render=fields["notes_for_render"],
                risk_flags=[],
            )
        )

    return ScenesBundle(project_id=state.project_id, scenes=scenes, created_at=utc_now())


def build_presentation_plan(
    project_id: str,
    scenes: list[SceneDraft],
    profile: PresentationProfile,
) -> PresentationPlan:
    presentation_scenes = [_to_presentation_scene(scene) for scene in scenes]
    total = max(1, len(scenes))
    presenter_visible = sum(1 for scene in scenes if scene.presenter_mode != "off_screen")
    asset_scenes = sum(1 for scene in scenes if scene.asset_policy != "none")
    fullscreen_scenes = sum(1 for scene in scenes if scene.visual_focus == "asset_fullscreen")
    total_duration = sum(scene.target_duration_sec for scene in scenes)

    return PresentationPlan(
        project_id=project_id,
        profile_id=profile.profile_id,
        scenes=presentation_scenes,
        presenter_visibility_ratio=round(presenter_visible / total, 3),
        asset_scene_ratio=round(asset_scenes / total, 3),
        fullscreen_asset_ratio=round(fullscreen_scenes / total, 3),
        created_at=utc_now(),
        quality_report={
            "scene_count": len(scenes),
            "estimated_total_duration_sec": round(total_duration, 2),
            "profile_policy": profile.asset_insertion_policy,
        },
    )


def review_presentation_plan(
    state: ProjectState,
    claims: list[PaperClaim],
    scenes_bundle: ScenesBundle,
    presentation_plan: PresentationPlan,
    profile: PresentationProfile,
) -> PresentationReviewBundle:
    reviews = []
    reviews.extend(ScriptGroundingReviewer().review(scenes_bundle.scenes, claims))
    reviews.extend(StyleRuleReviewer().review(scenes_bundle.scenes, state.style))
    reviews.extend(PresentationStructureReviewer().review(scenes_bundle.scenes, presentation_plan, profile))
    gate_decision = decide_presentation_gate(reviews)
    return PresentationReviewBundle(
        project_id=state.project_id,
        reviews=reviews,
        gate_decision=gate_decision,
        created_at=utc_now(),
    )


def _voice_text(purpose: ScenePurpose, claims: list[PaperClaim], max_chars: int) -> str:
    if not claims:
        return "接著，我們把前面的重點連起來。"
    prefix = {
        "hook": "這篇研究的關鍵是：",
        "problem": "研究問題是：",
        "method": "方法重點是：",
        "result": "主要結果是：",
        "limitation": "限制在於：",
        "takeaway": "所以可以記住：",
        "transition": "",
    }[purpose]
    text = prefix + claims[0].claim_text
    return _truncate(text, max_chars)


def _subtitle_text(voice_text: str, max_chars: int) -> str:
    budget = max(4, min(max_chars, len(voice_text) - 1 if len(voice_text) > 1 else max_chars))
    return _truncate(voice_text, budget)


def _presentation_fields(
    purpose: ScenePurpose,
    claims: list[PaperClaim],
    profile: PresentationProfile,
) -> dict:
    claim_type = claims[0].claim_type if claims else "background"
    if purpose in {"hook", "takeaway", "transition", "problem"}:
        return {
            "presenter_mode": "speaking_on_camera",
            "visual_focus": "presenter" if purpose != "transition" else "text_card",
            "asset_policy": "none",
            "asset_intent": None,
            "asset_type_hint": "none",
            "notes_for_render": "Presenter-first scene; no supporting asset required.",
        }
    if purpose == "method" or claim_type in {"method", "contribution"}:
        return {
            "presenter_mode": "speaking_with_overlay",
            "visual_focus": "supporting_asset",
            "asset_policy": "optional",
            "asset_intent": "Use a simple diagram only if it clarifies the method.",
            "asset_type_hint": "diagram",
            "notes_for_render": "Keep presenter visible; asset is supporting.",
        }
    if purpose == "result" or claim_type == "result":
        return {
            "presenter_mode": "speaking_with_overlay",
            "visual_focus": "supporting_asset",
            "asset_policy": "optional",
            "asset_intent": "Use a chart or paper figure only if it directly supports the result.",
            "asset_type_hint": "chart",
            "notes_for_render": "Avoid fullscreen unless later asset planning requires it.",
        }
    return {
        "presenter_mode": "speaking_on_camera",
        "visual_focus": "presenter",
        "asset_policy": "none",
        "asset_intent": None,
        "asset_type_hint": "none",
        "notes_for_render": f"Use {profile.default_background_mode} background.",
    }


def _to_presentation_scene(scene: SceneDraft) -> PresentationScene:
    if scene.purpose == "transition" or scene.visual_focus == "text_card":
        scene_type = "transition_or_card"
    elif scene.visual_focus == "asset_fullscreen":
        scene_type = "asset_focus"
    elif scene.asset_policy != "none":
        scene_type = "presenter_with_overlay"
    else:
        scene_type = "presenter_only"

    return PresentationScene(
        scene_id=scene.scene_id,
        scene_type=scene_type,
        presenter_mode=scene.presenter_mode,
        visual_focus=scene.visual_focus,
        asset_policy=scene.asset_policy,
        asset_type_hint=scene.asset_type_hint,
        background_mode=scene.background_mode,
        estimated_asset_duration_sec=scene.target_duration_sec if scene.asset_policy == "required" else None,
        render_notes=scene.notes_for_render,
    )


def _truncate(text: str, max_chars: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    if max_chars <= 1:
        return clean[:max_chars]
    return clean[: max_chars - 1].rstrip() + "…"
