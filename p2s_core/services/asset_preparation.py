from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any

from p2s_core.models import (
    AssetPlanBundle,
    AssetPlanQualityReport,
    PaperClaim,
    PresentationPlan,
    ProjectState,
    RenderPlan,
    SceneAssetPlan,
    SceneDraft,
    ScenesBundle,
    TTSPlan,
    VisualAssetPlan,
)
from p2s_core.services.narrative_planning import load_project_claims, utc_now
from p2s_core.services.figure_extraction import validate_figure_paths
import p2s_core.services.persistence as persistence


class AssetPreparationError(ValueError):
    """Raised when MVP2B cannot build a valid deterministic asset plan."""


def prepare_assets_for_project(
    run_dir: Path,
    state: ProjectState,
    config: dict | None = None,
) -> AssetPlanBundle:
    """Create asset_plan.json from the active scene source and presentation plan."""

    config = config or {}
    scene_source, scenes_bundle, source_warnings = _load_active_scenes(run_dir, state)
    presentation_plan = _load_presentation_plan(run_dir)
    _require_claims_json(run_dir, state)
    claims = load_project_claims(state, run_dir)
    figures = _load_figures(run_dir, state)
    warnings = list(source_warnings)
    if not figures:
        warnings.append("No figure metadata found; paper_figure selection will use fallback behavior.")

    _validate_alignment(scenes_bundle, presentation_plan)

    claim_map = {claim.claim_id: claim for claim in claims}
    plans = [
        _build_scene_plan(scene, claim_map, figures, state, config)
        for scene in scenes_bundle.scenes
    ]
    warnings.extend(warning for plan in plans for warning in plan.warnings)

    bundle = AssetPlanBundle(
        project_id=state.project_id,
        scene_source=scene_source,
        plans=plans,
        quality_report=_quality_report(plans, warnings),
        created_at=utc_now(),
    )
    (run_dir / "asset_plan.json").write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    return bundle


def run_asset_preparation_stage(state: ProjectState, config: dict | None = None) -> ProjectState:
    run_dir = persistence.project_dir(state.project_id)
    bundle = prepare_assets_for_project(run_dir, state, config=config)

    state.asset_plan = bundle.model_dump()
    stage = state.stages["asset_preparation"]
    stage.status = "done"
    stage.output_paths = ["asset_plan.json"]
    return state


def _load_figures(run_dir: Path, state: ProjectState) -> list[dict]:
    figures_path = getattr(state.extraction, "figures_path", None)
    if figures_path:
        path = Path(figures_path)
        if not path.is_absolute():
            path = run_dir / path
        if path.exists():
            figures = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(figures, list):
                raise AssetPreparationError(f"figures metadata must be a list: {path}")
            validate_figure_paths(run_dir, figures)
            return figures
    return list(state.extraction.figures or [])


def _load_active_scenes(run_dir: Path, state: ProjectState) -> tuple[str, ScenesBundle, list[str]]:
    requested_source = state.active_scene_source or "scenes.json"
    requested_path = run_dir / requested_source
    if requested_path.exists():
        return requested_source, _load_scenes_bundle(requested_path), []

    fallback_path = run_dir / "scenes.json"
    if requested_source != "scenes.json" and fallback_path.exists():
        warning = (
            f"active_scene_source {requested_source!r} was missing; "
            "fell back to 'scenes.json'."
        )
        return "scenes.json", _load_scenes_bundle(fallback_path), [warning]

    raise FileNotFoundError(
        f"Active scene source not found: {requested_path}. Fallback scenes.json was not available."
    )


def _load_scenes_bundle(path: Path) -> ScenesBundle:
    return ScenesBundle.model_validate_json(path.read_text(encoding="utf-8"))


def _load_presentation_plan(run_dir: Path) -> PresentationPlan:
    path = run_dir / "presentation_plan.json"
    if not path.exists():
        raise FileNotFoundError(f"presentation_plan.json not found: {path}")
    return PresentationPlan.model_validate_json(path.read_text(encoding="utf-8"))


def _require_claims_json(run_dir: Path, state: ProjectState) -> None:
    if not (run_dir / "claims.json").exists() and not state.claims:
        raise FileNotFoundError(f"claims.json not found: {run_dir / 'claims.json'}")


def _validate_alignment(scenes_bundle: ScenesBundle, presentation_plan: PresentationPlan) -> None:
    scene_ids = [scene.scene_id for scene in scenes_bundle.scenes]
    presentation_ids = [scene.scene_id for scene in presentation_plan.scenes]
    _assert_no_duplicates(scene_ids, "active scene source")
    _assert_no_duplicates(presentation_ids, "presentation_plan.json")
    if set(scene_ids) != set(presentation_ids):
        raise AssetPreparationError(
            "Scene id mismatch between active scene source and presentation_plan.json."
        )
    if scene_ids != presentation_ids:
        raise AssetPreparationError(
            "Scene order mismatch between active scene source and presentation_plan.json."
        )


def _assert_no_duplicates(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise AssetPreparationError(f"Duplicated scene_id values in {label}: {duplicates}")


def _build_scene_plan(
    scene: SceneDraft,
    claim_map: dict[str, PaperClaim],
    figures: list[dict],
    state: ProjectState,
    config: dict[str, Any],
) -> SceneAssetPlan:
    warnings: list[str] = []
    visual_plan = _build_visual_plan(scene, claim_map, figures, warnings)
    render_plan = _build_render_plan(scene, warnings)

    return SceneAssetPlan(
        scene_id=scene.scene_id,
        purpose=scene.purpose,
        claim_ids=scene.claim_ids,
        voice_text=scene.voice_text,
        subtitle_text=scene.subtitle_text,
        presenter_mode=scene.presenter_mode,
        visual_focus=scene.visual_focus,
        asset_policy=scene.asset_policy,
        asset_type_hint=scene.asset_type_hint,
        background_mode=scene.background_mode,
        tts_plan=_build_tts_plan(scene, state, config),
        visual_plan=visual_plan,
        render_plan=render_plan,
        warnings=warnings,
        notes=scene.notes_for_render,
    )


def _build_tts_plan(scene: SceneDraft, state: ProjectState, config: dict[str, Any]) -> TTSPlan:
    voice_profile = state.persona.get("voice") or {}
    voice = (
        voice_profile.get("default_voice")
        or config.get("tts", {}).get("default_voice")
        or "zh-TW-HsiaoChenNeural"
    )
    speed = voice_profile.get("default_speed") or config.get("tts", {}).get("default_speed") or 1.0
    pitch = voice_profile.get("default_pitch") or config.get("tts", {}).get("default_pitch")
    emotion = None
    voice_direction = getattr(scene, "voice_direction", None)
    if voice_direction:
        emotion = voice_direction.emotion

    return TTSPlan(
        voice=voice,
        speed=float(speed),
        pitch=pitch,
        emotion=emotion,
        text=scene.voice_text,
        output_path=f"audio/{scene.scene_id}.wav",
        estimated_duration_sec=_estimate_duration(scene.voice_text),
        notes="MVP2B placeholder only; actual synthesis in MVP2C.",
    )


def _estimate_duration(text: str) -> float:
    return round(max(2.0, len(text) / 4.5), 2)


def _build_visual_plan(
    scene: SceneDraft,
    claim_map: dict[str, PaperClaim],
    figures: list[dict],
    warnings: list[str],
) -> VisualAssetPlan:
    if scene.asset_policy == "none":
        return VisualAssetPlan(
            enabled=False,
            asset_source="none",
            asset_type_hint=scene.asset_type_hint,
            asset_intent=scene.asset_intent,
            fallback_chain=["text_card", "static_background"],
            output_placeholder=None,
            notes="No external visual asset needed.",
        )

    if scene.asset_type_hint == "paper_figure":
        selected, reason = _select_figures(scene, claim_map, figures)
        if selected:
            return _visual(
                scene,
                asset_source="paper_figure",
                fallback_chain=["paper_figure", "text_card", "static_background"],
                selected_figure_ids=selected,
                figure_selection_reason=reason,
            )
        warning = f"{scene.scene_id}: paper_figure requested but no matching figure metadata was found."
        warnings.append(warning)
        if scene.asset_policy == "required":
            return _visual(
                scene,
                asset_source="paper_figure",
                fallback_chain=["paper_figure", "text_card", "static_background"],
                selected_figure_ids=[],
                figure_selection_reason="No figure caption metadata matched the scene.",
                risk_flags=["missing_required_figure"],
            )
        return _visual(
            scene,
            asset_source="text_card",
            fallback_chain=["paper_figure", "text_card", "static_background"],
            notes="Optional paper figure downgraded to text_card.",
        )

    if scene.asset_type_hint == "diagram":
        return _visual(
            scene,
            asset_source="diagram_prompt",
            visual_prompt=(
                "Create a clean educational diagram for this scene: "
                f"{scene.asset_intent or scene.voice_text}. Use minimal labels, no decorative clutter."
            ),
            fallback_chain=["html_diagram", "text_card", "static_background"],
        )

    if scene.asset_type_hint == "metaphor_image":
        return _visual(
            scene,
            asset_source="metaphor_image_prompt",
            visual_prompt=(
                "Create a restrained metaphor image for this scientific idea: "
                f"{scene.asset_intent or scene.voice_text}. Avoid unsupported claims or dramatic styling."
            ),
            fallback_chain=["ai_generated", "text_card", "static_background"],
        )

    if scene.asset_type_hint == "chart":
        return _visual(
            scene,
            asset_source="chart_prompt",
            visual_prompt=(
                "Create a simple chart-style visual plan for this scene without inventing numbers: "
                f"{scene.asset_intent or scene.voice_text}."
            ),
            fallback_chain=["html_diagram", "text_card", "static_background"],
        )

    if scene.asset_policy == "required":
        warnings.append(
            f"{scene.scene_id}: asset_policy=required but asset_type_hint=none; treating as text_card."
        )
        return _visual(
            scene,
            asset_source="text_card",
            fallback_chain=["text_card", "static_background"],
            risk_flags=["required_asset_without_type"],
        )

    return _visual(
        scene,
        asset_source="text_card",
        fallback_chain=["text_card", "static_background"],
        notes="Optional scene with no concrete asset type uses a text_card placeholder.",
    )


def _visual(
    scene: SceneDraft,
    asset_source: str,
    fallback_chain: list[str],
    selected_figure_ids: list[str] | None = None,
    figure_selection_reason: str | None = None,
    visual_prompt: str | None = None,
    risk_flags: list[str] | None = None,
    notes: str | None = None,
) -> VisualAssetPlan:
    return VisualAssetPlan(
        enabled=asset_source != "none",
        asset_source=asset_source,
        asset_type_hint=scene.asset_type_hint,
        asset_intent=scene.asset_intent,
        selected_figure_ids=selected_figure_ids or [],
        figure_selection_reason=figure_selection_reason,
        visual_prompt=visual_prompt,
        fallback_chain=fallback_chain,
        output_placeholder=_output_placeholder(scene.scene_id, asset_source),
        risk_flags=risk_flags or [],
        notes=notes,
    )


def _select_figures(
    scene: SceneDraft,
    claim_map: dict[str, PaperClaim],
    figures: list[dict],
) -> tuple[list[str], str | None]:
    query = " ".join(
        [
            scene.asset_intent or "",
            scene.voice_text,
            " ".join(
                claim_map[claim_id].claim_text
                for claim_id in scene.claim_ids
                if claim_id in claim_map
            ),
        ]
    )
    query_tokens = _tokens(query)
    best_id = None
    best_score = 0
    best_caption = ""
    for index, figure in enumerate(figures, start=1):
        caption = str(
            figure.get("caption")
            or figure.get("title")
            or figure.get("text")
            or figure.get("description")
            or ""
        )
        score = len(query_tokens & _tokens(caption))
        if score > best_score:
            best_score = score
            best_id = _figure_id(figure, index)
            best_caption = caption
    if not best_id or best_score <= 0:
        return [], None
    return [best_id], f"Selected by token overlap score {best_score}: {best_caption[:80]}"


def _figure_id(figure: dict, index: int) -> str:
    return str(
        figure.get("figure_id")
        or figure.get("id")
        or figure.get("name")
        or figure.get("path")
        or f"figure_{index:03d}"
    )


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text)
        if len(token.strip()) > 0
    }


def _build_render_plan(scene: SceneDraft, warnings: list[str]) -> RenderPlan:
    template_hint, layout_mode = _template_and_layout(scene.visual_focus)
    if scene.presenter_mode == "off_screen" and scene.visual_focus == "presenter":
        warnings.append(
            f"{scene.scene_id}: presenter_mode=off_screen conflicts with visual_focus=presenter; using text_card layout."
        )
        template_hint = "text_card_clean"
        layout_mode = "text_card"

    return RenderPlan(
        template_hint=template_hint,
        layout_mode=layout_mode,
        background_mode=scene.background_mode,
        output_segment_placeholder=f"segments/{scene.scene_id}.mp4",
    )


def _template_and_layout(visual_focus: str) -> tuple[str, str]:
    mapping = {
        "presenter": ("presenter_only_clean", "presenter_only"),
        "supporting_asset": ("presenter_with_overlay_clean", "presenter_with_overlay"),
        "split": ("split_presenter_asset_clean", "presenter_with_overlay"),
        "asset_fullscreen": ("asset_fullscreen_caption_clean", "asset_focus"),
        "text_card": ("text_card_clean", "text_card"),
    }
    return mapping.get(visual_focus, ("static_clean", "static_clean"))


def _output_placeholder(scene_id: str, asset_source: str) -> str | None:
    suffixes = {
        "paper_figure": "figure",
        "diagram_prompt": "diagram",
        "metaphor_image_prompt": "metaphor",
        "chart_prompt": "chart",
        "text_card": "textcard",
        "static_background": "bg",
    }
    suffix = suffixes.get(asset_source)
    if not suffix:
        return None
    return f"assets/{scene_id}_{suffix}.png"


def _quality_report(plans: list[SceneAssetPlan], warnings: list[str]) -> AssetPlanQualityReport:
    return AssetPlanQualityReport(
        scene_count=len(plans),
        tts_enabled_count=sum(1 for plan in plans if plan.tts_plan.enabled),
        visual_enabled_count=sum(1 for plan in plans if plan.visual_plan.enabled),
        required_asset_count=sum(1 for plan in plans if plan.asset_policy == "required"),
        optional_asset_count=sum(1 for plan in plans if plan.asset_policy == "optional"),
        no_asset_count=sum(1 for plan in plans if plan.asset_policy == "none"),
        paper_figure_count=_count_source(plans, "paper_figure"),
        diagram_prompt_count=_count_source(plans, "diagram_prompt"),
        metaphor_prompt_count=_count_source(plans, "metaphor_image_prompt"),
        text_card_count=_count_source(plans, "text_card"),
        static_background_count=_count_source(plans, "static_background"),
        warnings=warnings,
    )


def _count_source(plans: list[SceneAssetPlan], asset_source: str) -> int:
    return sum(1 for plan in plans if plan.visual_plan.asset_source == asset_source)
