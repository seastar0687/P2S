from pathlib import Path

from click.testing import CliRunner

from p2s_core import cli as cli_module
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
from p2s_core.pipelines import PaperSummaryPipeline
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "asset_preparation_pipeline"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_claim() -> PaperClaim:
    return PaperClaim(
        claim_id="claim_001",
        claim_text="Teacher models can transmit traits through numbers.",
        claim_type="method",
        source_section="method",
        evidence_spans=[
            EvidenceSpan(
                section="method",
                text="Teacher models can transmit traits through numbers.",
                confidence="direct",
            )
        ],
        certainty="explicit",
        importance=5,
    )


def make_scene() -> SceneDraft:
    return SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="方法重點是：教師模型可能透過數字傳遞特徵。",
        subtitle_text="方法：數字傳遞特徵。",
        target_duration_sec=8.0,
        presenter_mode="speaking_with_overlay",
        visual_focus="supporting_asset",
        asset_policy="optional",
        asset_type_hint="diagram",
        asset_intent="Explain trait transfer.",
        background_mode="static_clean",
    )


def write_ready_project(runs_dir: Path, project_id: str = "asset_pipeline") -> ProjectState:
    project_dir = runs_dir / project_id
    project_dir.mkdir(parents=True)
    scene = make_scene()
    claim = make_claim()
    state = ProjectState(
        project_id=project_id,
        created_at="2026-05-08T00:00:00Z",
        source=ProjectSource(pdf_path=str(project_dir / "source.pdf")),
        persona={
            "persona_id": "seina",
            "version": "0.1.0",
            "voice": {"backend": "edge_tts", "default_voice": "zh-TW-HsiaoChenNeural"},
        },
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        claims=[claim],
        stages={
            "extraction": StageState(status="done"),
            "claim_extraction": StageState(status="done"),
            "narrative_planning": StageState(status="done"),
            "presentation_planning": StageState(status="done"),
            "llm_quality_rewrite": StageState(status="pending"),
        },
    )
    (project_dir / "source.pdf").write_text("placeholder", encoding="utf-8")
    (project_dir / "claims.json").write_text(f"[{claim.model_dump_json()}]", encoding="utf-8")
    (project_dir / "scenes.json").write_text(
        ScenesBundle(
            project_id=project_id,
            scenes=[scene],
            created_at="2026-05-08T00:00:00Z",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    (project_dir / "presentation_plan.json").write_text(
        PresentationPlan(
            project_id=project_id,
            profile_id="presenter_first_default",
            scenes=[
                PresentationScene(
                    scene_id=scene.scene_id,
                    scene_type="presenter_with_overlay",
                    presenter_mode=scene.presenter_mode,
                    visual_focus=scene.visual_focus,
                    asset_policy=scene.asset_policy,
                    asset_type_hint=scene.asset_type_hint,
                    background_mode=scene.background_mode,
                )
            ],
            presenter_visibility_ratio=1.0,
            asset_scene_ratio=1.0,
            fullscreen_asset_ratio=0.0,
            created_at="2026-05-08T00:00:00Z",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    persistence.save_state(state)
    return state


def test_pipeline_run_asset_preparation_writes_plan_and_stage_done(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    state = write_ready_project(runs_dir)

    updated = PaperSummaryPipeline().run_stage(state.project_id, "asset_preparation")

    assert (runs_dir / state.project_id / "asset_plan.json").exists()
    assert updated.stages["asset_preparation"].status == "done"
    assert updated.stages["asset_preparation"].output_paths == ["asset_plan.json"]
    assert updated.stages["llm_quality_rewrite"].status == "pending"


def test_cli_run_asset_preparation_prints_mvp2b_summary(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    state = write_ready_project(runs_dir, project_id="asset_cli")

    result = CliRunner().invoke(
        cli_module.cli,
        ["run", "--stage", "asset_preparation", "--project", state.project_id],
    )

    assert result.exit_code == 0
    assert "status: done" in result.output
    assert "scene_source: scenes.json" in result.output
    assert "scene_count: 1" in result.output
    assert "warnings:" in result.output


def test_force_rewrites_asset_plan(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    state = write_ready_project(runs_dir, project_id="asset_force")
    pipeline = PaperSummaryPipeline()
    pipeline.run_stage(state.project_id, "asset_preparation")
    asset_path = runs_dir / state.project_id / "asset_plan.json"
    asset_path.write_text("corrupted", encoding="utf-8")

    updated = pipeline.run_stage(state.project_id, "asset_preparation", force=True)

    assert updated.stages["asset_preparation"].status == "done"
    assert "mvp2b_v1" in asset_path.read_text(encoding="utf-8")


def test_status_shows_asset_preparation_and_migration_preserves_rewrite_status(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "asset_status"
    state = write_ready_project(runs_dir, project_id=project_id)
    state.stages["llm_quality_rewrite"].status = "done"
    state.stages.pop("asset_preparation")
    persistence.save_state(state)

    result = CliRunner().invoke(cli_module.cli, ["status", "--project", project_id])
    loaded = persistence.load_state(project_id)

    assert result.exit_code == 0
    assert "asset_preparation" in result.output
    assert loaded.stages["llm_quality_rewrite"].status == "done"
