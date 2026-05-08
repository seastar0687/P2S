from pathlib import Path

from click.testing import CliRunner

from p2s_core import cli as cli_module
from p2s_core.models import ClaimExtractionResult
from p2s_core.pipelines import PaperSummaryPipeline, StagePrerequisiteError
from p2s_core.services import persistence
from tests.test_mvp2a_fixtures import make_claim, make_state, reset_runs


ROOT = Path(__file__).resolve().parents[1]


def make_project(runs_dir: Path, project_id: str):
    project_dir = runs_dir / project_id
    project_dir.mkdir(parents=True)
    state = make_state(project_id)
    state.stages["extraction"].status = "done"
    state.stages["claim_extraction"].status = "done"
    persistence.save_state(state)
    claims = ClaimExtractionResult(
        project_id=project_id,
        claims=[
            make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5),
            make_claim("claim_002", "The method compares two encoders.", "method", 4),
            make_claim("claim_003", "The method improves accuracy on one benchmark.", "result", 4),
        ],
        source_chunk_ids=["chunk_001"],
        created_at="2026-05-08T00:00:00Z",
    )
    (project_dir / "claims.json").write_text(claims.model_dump_json(indent=2), encoding="utf-8")
    (project_dir / "extracted_text.md").write_text("Fake extracted text.", encoding="utf-8")
    return state


def test_mvp2a_pipeline_smoke_creates_outputs(monkeypatch):
    runs_dir = reset_runs(ROOT, "mvp2a_pipeline")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "mvp2a_pipeline"
    make_project(runs_dir, project_id)

    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )
    state = pipeline.run_stage(project_id, "narrative_planning")
    state = pipeline.run_stage(project_id, "presentation_planning")

    project_dir = runs_dir / project_id
    assert (project_dir / "narrative_plan.json").exists()
    assert (project_dir / "scenes.json").exists()
    assert (project_dir / "presentation_plan.json").exists()
    assert (project_dir / "reviews" / "presentation_review_rev001.json").exists()
    assert not (project_dir / "asset_plan.json").exists()
    assert state.stages["narrative_planning"].status == "done"
    assert state.stages["presentation_planning"].status == "done"


def test_presentation_planning_before_narrative_fails_gracefully(monkeypatch):
    runs_dir = reset_runs(ROOT, "mvp2a_dependency")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "mvp2a_dependency"
    make_project(runs_dir, project_id)
    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )

    try:
        pipeline.run_stage(project_id, "presentation_planning")
    except StagePrerequisiteError as exc:
        assert "narrative_planning" in str(exc)
    else:
        raise AssertionError("Expected StagePrerequisiteError")


def test_pipeline_adds_missing_current_stage_keys_for_old_projects(monkeypatch):
    runs_dir = reset_runs(ROOT, "mvp2a_stage_migration")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "mvp2a_stage_migration"
    state = make_project(runs_dir, project_id)
    del state.stages["presentation_planning"]
    del state.stages["llm_quality_rewrite"]
    state.active_scene_source = ""
    persistence.save_state(state)
    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )

    updated = pipeline.run_stage(project_id, "narrative_planning")

    assert "presentation_planning" in updated.stages
    assert "llm_quality_rewrite" in updated.stages
    assert updated.active_scene_source == "scenes.json"
    assert updated.stages["narrative_planning"].status == "done"


def test_cli_run_narrative_and_presentation_stages(monkeypatch):
    runs_dir = reset_runs(ROOT, "mvp2a_cli")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "mvp2a_cli"
    make_project(runs_dir, project_id)
    runner = CliRunner()

    narrative = runner.invoke(
        cli_module.cli,
        ["run", "--stage", "narrative_planning", "--project", project_id],
    )
    presentation = runner.invoke(
        cli_module.cli,
        ["run", "--stage", "presentation_planning", "--project", project_id],
    )

    assert narrative.exit_code == 0
    assert "status: done" in narrative.output
    assert presentation.exit_code == 0
    assert "presentation_plan.json" in presentation.output
