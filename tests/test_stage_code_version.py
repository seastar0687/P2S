from pathlib import Path

import fitz

from p2s_core.models import CodeVersion
from p2s_core.pipelines import PaperSummaryPipeline
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "stage_code_version"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Code version stage smoke.")
    doc.save(path)
    doc.close()


def test_stage_execution_writes_stage_code_version(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)
    pipeline = PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )
    state = pipeline.setup_project(pdf_path, project_id="code_version_stage")

    updated = pipeline.run_stage(state.project_id, "extraction")

    assert isinstance(updated.stages["extraction"].code_version, CodeVersion)
    assert isinstance(updated.code_version, CodeVersion)
