from pathlib import Path

import fitz
from click.testing import CliRunner

from p2s_core import cli as cli_module
from p2s_core.models import ProjectState
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "pipeline_smoke"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_pdf(path: Path, text: str = "Pipeline smoke text.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def init_project(runs_dir: Path, project_id: str, text: str = "Pipeline smoke text."):
    pdf_path = TEST_RUNS_DIR / f"{project_id}.pdf"
    make_pdf(pdf_path, text)
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["init", str(pdf_path), "--id", project_id])
    assert result.exit_code == 0
    return runner, runs_dir / project_id


def test_init_creates_project_state(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)

    _, project_dir = init_project(runs_dir, "2026-05-06_smoke_init")
    state_path = project_dir / "project_state.json"

    assert (project_dir / "source.pdf").exists()
    assert state_path.exists()
    state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
    assert state.persona["persona_id"] == "seina"
    assert state.style["style_id"] == "rigorous_science_short"
    assert state.stages["extraction"].status == "pending"


def test_run_extraction_stage(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    runner, project_dir = init_project(
        runs_dir,
        "2026-05-06_smoke_run",
        text="Pipeline smoke extraction body.",
    )

    result = runner.invoke(
        cli_module.cli,
        ["run", "--stage", "extraction", "--project", "2026-05-06_smoke_run"],
    )
    state = ProjectState.model_validate_json(
        (project_dir / "project_state.json").read_text(encoding="utf-8")
    )

    assert result.exit_code == 0
    assert state.stages["extraction"].status == "done"
    assert state.extraction.text_md is not None
    assert "Pipeline smoke extraction body." in (project_dir / state.extraction.text_md).read_text(
        encoding="utf-8"
    )


def test_status_command_after_init(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    runner, _ = init_project(runs_dir, "2026-05-06_smoke_status")

    result = runner.invoke(
        cli_module.cli,
        ["status", "--project", "2026-05-06_smoke_status"],
    )

    assert result.exit_code == 0
    assert "Project: 2026-05-06_smoke_status" in result.output
    assert "extraction" in result.output
    assert "pending" in result.output


def test_run_claim_extraction_without_key_returns_clear_error(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    runner, _ = init_project(runs_dir, "2026-05-06_smoke_unimplemented")
    runner.invoke(
        cli_module.cli,
        ["run", "--stage", "extraction", "--project", "2026-05-06_smoke_unimplemented"],
    )
    from p2s_core.services import claim_extraction

    monkeypatch.setattr(
        claim_extraction,
        "load_config",
        lambda path="config.yaml": {"llm": {"provider": "openai", "api_key": ""}},
    )

    result = runner.invoke(
        cli_module.cli,
        [
            "run",
            "--stage",
            "claim_extraction",
            "--project",
            "2026-05-06_smoke_unimplemented",
        ],
    )

    assert result.exit_code != 0
    assert "OPENAI_API_KEY is not set" in result.output
