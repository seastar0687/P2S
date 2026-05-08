from pathlib import Path

import fitz
from click.testing import CliRunner

from p2s_core import cli as cli_module
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "cli"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_pdf(path: Path, text: str = "CLI extraction text.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_cli_init_creates_project_state(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)

    result = CliRunner().invoke(
        cli_module.cli,
        ["init", str(pdf_path), "--id", "2026-05-06_cli"],
    )

    assert result.exit_code == 0
    assert "Created project: 2026-05-06_cli" in result.output
    assert (runs_dir / "2026-05-06_cli" / "project_state.json").exists()
    assert (runs_dir / "2026-05-06_cli" / "source.pdf").exists()


def test_cli_run_extraction_stage(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path, "CLI run extraction text.")
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["init", str(pdf_path), "--id", "2026-05-06_run"])

    result = runner.invoke(
        cli_module.cli,
        ["run", "--stage", "extraction", "--project", "2026-05-06_run"],
    )

    output_path = runs_dir / "2026-05-06_run" / "extracted_text.md"
    assert result.exit_code == 0
    assert "status: done" in result.output
    assert output_path.exists()
    assert "CLI run extraction text." in output_path.read_text(encoding="utf-8")


def test_cli_status_uses_explicit_project(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["init", str(pdf_path), "--id", "2026-05-06_status"])

    result = runner.invoke(cli_module.cli, ["status", "--project", "2026-05-06_status"])

    assert result.exit_code == 0
    assert "Project: 2026-05-06_status" in result.output
    assert "extraction" in result.output
    assert "pending" in result.output


def test_cli_run_claim_extraction_without_key_returns_clear_error(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["init", str(pdf_path), "--id", "2026-05-06_claim"])
    runner.invoke(cli_module.cli, ["run", "--stage", "extraction", "--project", "2026-05-06_claim"])
    from p2s_core.services import claim_extraction

    monkeypatch.setattr(
        claim_extraction,
        "load_config",
        lambda path="config.yaml": {"llm": {"provider": "openai", "api_key": ""}},
    )

    result = runner.invoke(
        cli_module.cli,
        ["run", "--stage", "claim_extraction", "--project", "2026-05-06_claim"],
    )

    assert result.exit_code != 0
    assert "OPENAI_API_KEY is not set" in result.output


def test_cli_validate_personas_and_styles():
    runner = CliRunner()

    persona_result = runner.invoke(cli_module.cli, ["validate-personas"])
    style_result = runner.invoke(cli_module.cli, ["validate-styles"])

    assert persona_result.exit_code == 0
    assert "seina" in persona_result.output
    assert style_result.exit_code == 0
    assert "rigorous_science_short" in style_result.output
