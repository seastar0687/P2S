from pathlib import Path

import pytest

from p2s_core.models import (
    PaperClaim,
    PresentationPlan,
    PresentationScene,
    ProjectSource,
    ProjectState,
    SceneDraft,
    ScenesBundle,
    StageState,
)
from p2s_core.models.common import EvidenceSpan
from p2s_core.services.asset_preparation import AssetPreparationError, prepare_assets_for_project


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "asset_preparation_service"


def reset_test_dir() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR


def claim(claim_id: str = "claim_001", text: str = "A teacher model transmits traits through numbers.") -> PaperClaim:
    return PaperClaim(
        claim_id=claim_id,
        claim_text=text,
        claim_type="method",
        source_section="method",
        evidence_spans=[EvidenceSpan(section="method", text=text, confidence="direct")],
        certainty="explicit",
        importance=5,
    )


def scene(
    scene_id: str = "scene_001",
    *,
    asset_policy: str = "optional",
    asset_type_hint: str = "none",
    asset_intent: str | None = None,
    presenter_mode: str = "speaking_on_camera",
    visual_focus: str = "presenter",
) -> SceneDraft:
    return SceneDraft(
        scene_id=scene_id,
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="方法重點是：教師模型可能透過數字傳遞特徵。",
        subtitle_text="方法：數字傳遞特徵。",
        target_duration_sec=8.0,
        presenter_mode=presenter_mode,
        visual_focus=visual_focus,
        asset_policy=asset_policy,
        asset_type_hint=asset_type_hint,
        asset_intent=asset_intent,
        background_mode="static_clean",
    )


def make_state(project_id: str, *, active_scene_source: str = "scenes.json") -> ProjectState:
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-08T00:00:00Z",
        source=ProjectSource(pdf_path=f"runs/{project_id}/source.pdf"),
        persona={
            "persona_id": "seina",
            "version": "0.1.0",
            "voice": {
                "backend": "edge_tts",
                "default_voice": "zh-TW-HsiaoChenNeural",
                "default_speed": 1.0,
            },
        },
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        claims=[claim()],
        active_scene_source=active_scene_source,
        stages={
            "presentation_planning": StageState(status="done"),
        },
    )


def write_project(
    run_dir: Path,
    scenes: list[SceneDraft],
    *,
    scene_filename: str = "scenes.json",
    figures: list[dict] | None = None,
) -> ProjectState:
    state = make_state(run_dir.name, active_scene_source=scene_filename)
    state.extraction.figures = figures or []
    ScenesBundle(
        project_id=state.project_id,
        scenes=scenes,
        created_at="2026-05-08T00:00:00Z",
    ).model_dump_json(indent=2)
    (run_dir / scene_filename).write_text(
        ScenesBundle(
            project_id=state.project_id,
            scenes=scenes,
            created_at="2026-05-08T00:00:00Z",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    presentation = PresentationPlan(
        project_id=state.project_id,
        profile_id="presenter_first_default",
        scenes=[
            PresentationScene(
                scene_id=item.scene_id,
                scene_type="presenter_with_overlay" if item.asset_policy != "none" else "presenter_only",
                presenter_mode=item.presenter_mode,
                visual_focus=item.visual_focus,
                asset_policy=item.asset_policy,
                asset_type_hint=item.asset_type_hint,
                background_mode=item.background_mode,
            )
            for item in scenes
        ],
        presenter_visibility_ratio=1.0,
        asset_scene_ratio=1.0,
        fullscreen_asset_ratio=0.0,
        created_at="2026-05-08T00:00:00Z",
    )
    (run_dir / "presentation_plan.json").write_text(presentation.model_dump_json(indent=2), encoding="utf-8")
    (run_dir / "claims.json").write_text(f"[{claim().model_dump_json()}]", encoding="utf-8")
    return state


def test_builds_asset_plan_from_scenes_json():
    root = reset_test_dir()
    run_dir = root / "from_scenes"
    run_dir.mkdir()
    state = write_project(run_dir, [scene(asset_policy="none")])

    bundle = prepare_assets_for_project(run_dir, state)

    assert (run_dir / "asset_plan.json").exists()
    assert bundle.scene_source == "scenes.json"
    assert bundle.plans[0].tts_plan.text == bundle.plans[0].voice_text
    assert bundle.plans[0].visual_plan.asset_source == "none"
    assert bundle.plans[0].visual_plan.output_placeholder is None


def test_builds_asset_plan_from_scenes_rewritten():
    root = reset_test_dir()
    run_dir = root / "from_rewritten"
    run_dir.mkdir()
    state = write_project(run_dir, [scene(asset_type_hint="diagram")], scene_filename="scenes_rewritten.json")

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.scene_source == "scenes_rewritten.json"
    assert bundle.plans[0].visual_plan.asset_source == "diagram_prompt"


def test_missing_rewritten_source_falls_back_to_scenes_json_with_warning():
    root = reset_test_dir()
    run_dir = root / "fallback"
    run_dir.mkdir()
    state = write_project(run_dir, [scene(asset_policy="none")])
    state.active_scene_source = "scenes_rewritten.json"

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.scene_source == "scenes.json"
    assert "fell back to 'scenes.json'" in bundle.quality_report.warnings[0]


def test_missing_active_source_and_missing_scenes_json_fails():
    root = reset_test_dir()
    run_dir = root / "missing"
    run_dir.mkdir()
    state = make_state(run_dir.name, active_scene_source="scenes_rewritten.json")
    (run_dir / "claims.json").write_text(f"[{claim().model_dump_json()}]", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        prepare_assets_for_project(run_dir, state)


def test_scene_id_mismatch_fails():
    root = reset_test_dir()
    run_dir = root / "mismatch"
    run_dir.mkdir()
    state = write_project(run_dir, [scene("scene_001")])
    presentation = PresentationPlan.model_validate_json(
        (run_dir / "presentation_plan.json").read_text(encoding="utf-8")
    )
    presentation.scenes[0].scene_id = "scene_999"
    (run_dir / "presentation_plan.json").write_text(presentation.model_dump_json(indent=2), encoding="utf-8")

    with pytest.raises(AssetPreparationError):
        prepare_assets_for_project(run_dir, state)


def test_duplicate_scene_id_fails():
    root = reset_test_dir()
    run_dir = root / "duplicate"
    run_dir.mkdir()
    state = write_project(run_dir, [scene("scene_001"), scene("scene_001")])

    with pytest.raises(AssetPreparationError):
        prepare_assets_for_project(run_dir, state)


@pytest.mark.parametrize(
    ("asset_type_hint", "expected_source", "expected_placeholder"),
    [
        ("diagram", "diagram_prompt", "assets/scene_001_diagram.png"),
        ("metaphor_image", "metaphor_image_prompt", "assets/scene_001_metaphor.png"),
        ("chart", "chart_prompt", "assets/scene_001_chart.png"),
    ],
)
def test_prompt_visual_plans(asset_type_hint, expected_source, expected_placeholder):
    root = reset_test_dir()
    run_dir = root / f"prompt_{asset_type_hint}"
    run_dir.mkdir()
    state = write_project(run_dir, [scene(asset_type_hint=asset_type_hint, asset_intent="Explain transfer.")])

    bundle = prepare_assets_for_project(run_dir, state)

    visual = bundle.plans[0].visual_plan
    assert visual.asset_source == expected_source
    assert visual.visual_prompt
    assert visual.output_placeholder == expected_placeholder


def test_required_paper_figure_without_match_stays_paper_figure_and_warns():
    root = reset_test_dir()
    run_dir = root / "required_figure_missing"
    run_dir.mkdir()
    state = write_project(
        run_dir,
        [scene(asset_policy="required", asset_type_hint="paper_figure")],
        figures=[{"figure_id": "fig_001", "caption": "Completely unrelated image."}],
    )

    bundle = prepare_assets_for_project(run_dir, state)

    visual = bundle.plans[0].visual_plan
    assert visual.asset_source == "paper_figure"
    assert visual.selected_figure_ids == []
    assert visual.output_placeholder == "assets/scene_001_figure.png"
    assert bundle.quality_report.paper_figure_count == 1
    assert bundle.plans[0].warnings


def test_optional_paper_figure_without_match_downgrades_to_text_card():
    root = reset_test_dir()
    run_dir = root / "optional_figure_missing"
    run_dir.mkdir()
    state = write_project(
        run_dir,
        [scene(asset_policy="optional", asset_type_hint="paper_figure")],
        figures=[{"figure_id": "fig_001", "caption": "Unrelated caption."}],
    )

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.plans[0].visual_plan.asset_source == "text_card"
    assert bundle.quality_report.text_card_count == 1
    assert bundle.quality_report.optional_asset_count == 1


def test_paper_figure_with_caption_match_selects_figure():
    root = reset_test_dir()
    run_dir = root / "figure_match"
    run_dir.mkdir()
    state = write_project(
        run_dir,
        [scene(asset_policy="required", asset_type_hint="paper_figure")],
        figures=[{"figure_id": "fig_001", "caption": "Teacher model transmits traits through numbers."}],
    )

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.plans[0].visual_plan.asset_source == "paper_figure"
    assert bundle.plans[0].visual_plan.selected_figure_ids == ["fig_001"]
    assert bundle.plans[0].warnings == []


def test_required_asset_with_no_type_becomes_text_card_with_warning():
    root = reset_test_dir()
    run_dir = root / "required_no_type"
    run_dir.mkdir()
    state = write_project(run_dir, [scene(asset_policy="required", asset_type_hint="none")])

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.plans[0].visual_plan.asset_source == "text_card"
    assert bundle.quality_report.required_asset_count == 1
    assert bundle.plans[0].warnings


def test_output_placeholder_rules_for_none_and_non_none_sources():
    root = reset_test_dir()
    run_dir = root / "placeholders"
    run_dir.mkdir()
    state = write_project(
        run_dir,
        [
            scene("scene_001", asset_policy="none"),
            scene("scene_002", asset_type_hint="diagram"),
        ],
    )

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.plans[0].visual_plan.output_placeholder is None
    assert bundle.plans[1].visual_plan.output_placeholder == "assets/scene_002_diagram.png"


def test_off_screen_presenter_with_presenter_focus_warns_and_uses_text_card_layout():
    root = reset_test_dir()
    run_dir = root / "offscreen"
    run_dir.mkdir()
    state = write_project(
        run_dir,
        [scene(asset_policy="none", presenter_mode="off_screen", visual_focus="presenter")],
    )

    bundle = prepare_assets_for_project(run_dir, state)

    plan = bundle.plans[0]
    assert plan.render_plan.layout_mode == "text_card"
    assert plan.render_plan.template_hint == "text_card_clean"
    assert plan.warnings
