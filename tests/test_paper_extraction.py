from pathlib import Path

import fitz

from p2s_core.models import ProjectSource, ProjectState, default_stages
from p2s_core.services import paper_extraction, persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "paper_extraction"


def make_pdf(path: Path, pages: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def make_state(project_id: str, pdf_path: Path) -> ProjectState:
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-06T00:00:00Z",
        source=ProjectSource(pdf_path=str(pdf_path)),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        stages=default_stages(),
    )


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def test_extract_text_reads_pdf_pages():
    runs_dir = reset_test_runs()
    pdf_path = runs_dir / "paper.pdf"
    make_pdf(pdf_path, ["First page claim.", "Second page method."])

    text = paper_extraction.extract_text(pdf_path)

    assert "First page claim." in text
    assert "Second page method." in text


def test_run_extraction_stage_writes_text_and_updates_state(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "2026-05-06_extract"
    pdf_path = runs_dir / project_id / "source.pdf"
    make_pdf(pdf_path, ["Extraction smoke test text."])
    state = make_state(project_id, pdf_path)

    updated = paper_extraction.run_extraction_stage(state)
    output_path = Path(updated.extraction.text_md)

    assert updated.stages["extraction"].status == "done"
    assert updated.stages["extraction"].output_paths == [str(output_path)]
    assert output_path.exists()
    assert "Extraction smoke test text." in output_path.read_text(encoding="utf-8")
    assert output_path == runs_dir / project_id / "extracted_text.md"
