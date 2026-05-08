from pathlib import Path

from click.testing import CliRunner

from p2s_core import cli as cli_module
from p2s_core.pipelines import PaperSummaryPipeline, StagePrerequisiteError
from p2s_core.services import persistence
from tests.test_mvp2a_pipeline_smoke import make_project
from tests.test_mvp2a_fixtures import reset_runs


ROOT = Path(__file__).resolve().parents[1]


def test_llm_quality_rewrite_requires_presentation_planning_done(monkeypatch):
    runs_dir = reset_runs(ROOT, "llm_quality_rewrite_dependency")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "llm_quality_rewrite_dependency"
    state = make_project(runs_dir, project_id)
    state.stages["narrative_planning"].status = "done"
    state.stages["presentation_planning"].status = "pending"
    persistence.save_state(state)
    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )

    try:
        pipeline.run_stage(project_id, "llm_quality_rewrite")
    except StagePrerequisiteError as exc:
        assert "presentation_planning" in str(exc)
    else:
        raise AssertionError("Expected StagePrerequisiteError")


def test_cli_llm_quality_rewrite_missing_key_returns_clear_error(monkeypatch):
    runs_dir = reset_runs(ROOT, "llm_quality_rewrite_cli_missing_key")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "llm_quality_rewrite_cli_missing_key"
    state = make_project(runs_dir, project_id)
    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )
    pipeline.run_stage(project_id, "narrative_planning")
    pipeline.run_stage(project_id, "presentation_planning")

    import p2s_core.services.llm_quality_rewrite as rewrite_module

    monkeypatch.setattr(
        rewrite_module,
        "load_config",
        lambda path="config.yaml": {"llm": {"provider": "openai", "api_key": ""}},
    )

    result = CliRunner().invoke(
        cli_module.cli,
        ["run", "--stage", "llm_quality_rewrite", "--project", project_id],
    )

    assert result.exit_code != 0
    assert "OPENAI_API_KEY" in result.output


def test_pipeline_marks_rewrite_guardrail_violation_rejected(monkeypatch):
    runs_dir = reset_runs(ROOT, "llm_quality_rewrite_guardrail_status")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "llm_quality_rewrite_guardrail_status"
    make_project(runs_dir, project_id)
    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )
    pipeline.run_stage(project_id, "narrative_planning")
    pipeline.run_stage(project_id, "presentation_planning")

    import p2s_core.pipelines.paper_summary as paper_summary_module

    def reject_rewrite(state):
        raise paper_summary_module.llm_quality_rewrite.RewriteGuardrailError("immutable field changed")

    monkeypatch.setattr(
        paper_summary_module.llm_quality_rewrite,
        "run_llm_quality_rewrite_stage",
        reject_rewrite,
    )

    try:
        pipeline.run_stage(project_id, "llm_quality_rewrite")
    except paper_summary_module.llm_quality_rewrite.RewriteGuardrailError:
        pass
    else:
        raise AssertionError("Expected RewriteGuardrailError")

    state = persistence.load_state(project_id)
    assert state.stages["llm_quality_rewrite"].status == "rejected"
    assert state.active_scene_source == "scenes.json"
