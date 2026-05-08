from __future__ import annotations

import asyncio
from pathlib import Path

from p2s_core.config import load_config
from p2s_core.models import (
    PaperClaim,
    PresentationPlan,
    PresentationProfile,
    PresentationReviewBundle,
    ProjectState,
    SceneDraft,
    SceneRewritePatch,
    SceneRewriteResult,
    ScenesBundle,
)
from p2s_core.reviewers.presentation_gate import decide_presentation_gate
from p2s_core.reviewers.presentation_structure import PresentationStructureReviewer
from p2s_core.reviewers.script_grounding import ScriptGroundingReviewer
from p2s_core.reviewers.style_rule import StyleRuleReviewer
import p2s_core.services.persistence as persistence
from p2s_core.services.llm_service import LLMService
from p2s_core.services.narrative_planning import load_project_claims, utc_now
from p2s_core.services.persona_style import load_presentation_profile
from p2s_core.services.presentation_planning import build_presentation_plan


IMMUTABLE_FIELDS = (
    "scene_id",
    "purpose",
    "claim_ids",
    "presenter_mode",
    "visual_focus",
    "asset_policy",
    "asset_type_hint",
    "background_mode",
    "target_duration_sec",
)


class RewriteGuardrailError(ValueError):
    """Raised when an LLM rewrite violates the MVP2A-2 contract."""


def run_llm_quality_rewrite_stage(
    state: ProjectState,
    llm: LLMService | None = None,
    config_path: str | Path = "config.yaml",
) -> ProjectState:
    project_dir = persistence.project_dir(state.project_id)
    scenes_bundle = load_scenes_bundle(project_dir)
    claims = load_project_claims(state, project_dir)
    profile = load_presentation_profile()
    presentation_plan = load_presentation_plan(project_dir)

    own_llm = llm is None
    if llm is None:
        config = load_config(config_path)
        if not config.get("llm", {}).get("api_key"):
            raise ValueError("OPENAI_API_KEY is not set. Please configure it before LLM rewrite stages.")
        llm = LLMService(config)

    result = asyncio.run(_rewrite_and_close_if_needed(state, scenes_bundle, claims, llm, own_llm))
    if result.project_id != state.project_id:
        raise RewriteGuardrailError("LLM rewrite project_id does not match the current project.")

    rewritten_scenes = apply_rewrite_result(scenes_bundle.scenes, result)
    rewritten_bundle = ScenesBundle(
        project_id=state.project_id,
        scenes=rewritten_scenes,
        created_at=utc_now(),
    )
    rewritten_plan = build_presentation_plan(state.project_id, rewritten_scenes, profile)
    # Keep deterministic ratios as the contract source. The rebuilt plan is used only to feed reviewers
    # with the same skeleton-derived structure.
    rewritten_plan.presenter_visibility_ratio = presentation_plan.presenter_visibility_ratio
    rewritten_plan.asset_scene_ratio = presentation_plan.asset_scene_ratio
    rewritten_plan.fullscreen_asset_ratio = presentation_plan.fullscreen_asset_ratio

    review_bundle = review_rewritten_scenes(state, claims, rewritten_scenes, rewritten_plan, profile)

    scenes_path = project_dir / "scenes_rewritten.json"
    scenes_path.write_text(rewritten_bundle.model_dump_json(indent=2), encoding="utf-8")
    reviews_dir = project_dir / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    review_path = reviews_dir / "llm_quality_rewrite_review_rev001.json"
    review_path.write_text(review_bundle.model_dump_json(indent=2), encoding="utf-8")

    stage = state.stages["llm_quality_rewrite"]
    stage.output_paths = [
        "scenes_rewritten.json",
        "reviews/llm_quality_rewrite_review_rev001.json",
    ]
    state.reviews.extend(review_bundle.reviews)
    if review_bundle.gate_decision.status == "pass":
        stage.status = "done"
        state.active_scene_source = "scenes_rewritten.json"
        state.script["scenes"] = [scene.model_dump() for scene in rewritten_scenes]
    elif review_bundle.gate_decision.status == "human_check":
        stage.status = "needs_review"
    else:
        stage.status = "rejected"
    return state


def load_scenes_bundle(project_dir: Path) -> ScenesBundle:
    path = project_dir / "scenes.json"
    if not path.exists():
        raise FileNotFoundError(f"scenes.json not found: {path}")
    return ScenesBundle.model_validate_json(path.read_text(encoding="utf-8"))


def load_presentation_plan(project_dir: Path) -> PresentationPlan:
    path = project_dir / "presentation_plan.json"
    if not path.exists():
        raise FileNotFoundError(f"presentation_plan.json not found: {path}")
    return PresentationPlan.model_validate_json(path.read_text(encoding="utf-8"))


async def rewrite_scenes_with_llm(
    state: ProjectState,
    scenes_bundle: ScenesBundle,
    claims: list[PaperClaim],
    llm: LLMService,
) -> SceneRewriteResult:
    result = await llm.complete(
        [
            {"role": "system", "content": _rewrite_system_prompt(state)},
            {"role": "user", "content": _rewrite_user_payload(scenes_bundle, claims, state)},
        ],
        response_type=SceneRewriteResult,
        temperature=0.2,
        debug_dir=persistence.project_dir(state.project_id) / "debug",
    )
    if not isinstance(result, SceneRewriteResult):
        raise TypeError("LLMService returned unexpected non-SceneRewriteResult")
    return result


def apply_rewrite_result(
    original_scenes: list[SceneDraft],
    result: SceneRewriteResult,
) -> list[SceneDraft]:
    original_ids = [scene.scene_id for scene in original_scenes]
    patch_ids = [patch.scene_id for patch in result.patches]
    if len(set(patch_ids)) != len(patch_ids):
        raise RewriteGuardrailError("LLM rewrite returned duplicate scene_id values.")
    if set(patch_ids) != set(original_ids):
        raise RewriteGuardrailError("LLM rewrite scene_id set does not match deterministic scenes.")

    patch_map = {patch.scene_id: patch for patch in result.patches}
    rewritten = []
    for scene in original_scenes:
        patch = patch_map[scene.scene_id]
        updated = scene.model_copy(
            update={
                "voice_text": patch.voice_text,
                "subtitle_text": patch.subtitle_text,
                "asset_intent": patch.asset_intent,
                "notes_for_render": patch.notes_for_render,
            }
        )
        _assert_immutable_fields(scene, updated)
        _assert_required_asset_contract(updated)
        rewritten.append(updated)
    return rewritten


def review_rewritten_scenes(
    state: ProjectState,
    claims: list[PaperClaim],
    scenes: list[SceneDraft],
    presentation_plan: PresentationPlan,
    profile: PresentationProfile,
) -> PresentationReviewBundle:
    reviews = []
    reviews.extend(ScriptGroundingReviewer().review(scenes, claims))
    reviews.extend(StyleRuleReviewer().review(scenes, state.style))
    reviews.extend(PresentationStructureReviewer().review(scenes, presentation_plan, profile))
    gate_decision = decide_presentation_gate(reviews)
    return PresentationReviewBundle(
        project_id=state.project_id,
        target_stage="llm_quality_rewrite",
        reviews=reviews,
        gate_decision=gate_decision,
        created_at=utc_now(),
    )


async def _rewrite_and_close_if_needed(
    state: ProjectState,
    scenes_bundle: ScenesBundle,
    claims: list[PaperClaim],
    llm: LLMService,
    own_llm: bool,
) -> SceneRewriteResult:
    try:
        return await rewrite_scenes_with_llm(state, scenes_bundle, claims, llm)
    finally:
        if own_llm:
            await llm.aclose()


def _assert_immutable_fields(original: SceneDraft, rewritten: SceneDraft) -> None:
    changed = [
        field
        for field in IMMUTABLE_FIELDS
        if getattr(original, field) != getattr(rewritten, field)
    ]
    if changed:
        raise RewriteGuardrailError(f"LLM rewrite changed immutable fields: {changed}")


def _assert_required_asset_contract(scene: SceneDraft) -> None:
    if scene.asset_policy == "required" and (not scene.asset_intent or scene.asset_type_hint == "none"):
        raise RewriteGuardrailError(f"Required asset contract violated for {scene.scene_id}.")


def _rewrite_system_prompt(state: ProjectState) -> str:
    return (
        "You rewrite short scientific video scene text for clarity and naturalness. "
        "You may modify only voice_text, subtitle_text, asset_intent, and notes_for_render. "
        "Do not add unsupported claims, hype, stronger certainty, new numbers, or new claims. "
        "Do not change scene ids or presentation skeleton. "
        "Echo the exact project_id from the user payload in your JSON response. "
        "Return only JSON matching the requested schema. "
        f"Language: {state.settings.language}. Audience: {state.settings.target_audience}."
    )


def _rewrite_user_payload(scenes_bundle: ScenesBundle, claims: list[PaperClaim], state: ProjectState) -> str:
    claim_map = {claim.claim_id: claim for claim in claims}
    payload = {
        "project_id": state.project_id,
        "style": {
            "style_id": state.style.get("style_id"),
            "sentence_rules": state.style.get("sentence_rules", {}),
            "subtitle_rules": state.style.get("subtitle_rules", {}),
        },
        "editable_fields": ["voice_text", "subtitle_text", "asset_intent", "notes_for_render"],
        "immutable_fields": list(IMMUTABLE_FIELDS),
        "scenes": [
            {
                "scene_id": scene.scene_id,
                "purpose": scene.purpose,
                "claim_ids": scene.claim_ids,
                "voice_text": scene.voice_text,
                "subtitle_text": scene.subtitle_text,
                "asset_intent": scene.asset_intent,
                "notes_for_render": scene.notes_for_render,
                "presentation_skeleton": {
                    field: getattr(scene, field)
                    for field in IMMUTABLE_FIELDS
                },
                "linked_claims": [
                    {
                        "claim_id": claim_id,
                        "claim_text": claim_map[claim_id].claim_text,
                        "evidence": [span.text for span in claim_map[claim_id].evidence_spans[:2]],
                    }
                    for claim_id in scene.claim_ids
                    if claim_id in claim_map
                ],
            }
            for scene in scenes_bundle.scenes
        ],
    }
    return str(payload)
