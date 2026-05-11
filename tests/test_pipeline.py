from pathlib import Path

import fitz

from p2s_core.pipelines import PaperSummaryPipeline, StageAlreadyDoneError
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "pipeline"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_pdf(path: Path, text: str = "Pipeline extraction text.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def make_pipeline() -> PaperSummaryPipeline:
    return PaperSummaryPipeline(
        personas_dir=ROOT / "p2s_core" / "personas",
        styles_dir=ROOT / "p2s_core" / "styles",
    )


def test_setup_project_copies_pdf_and_saves_state(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)
    pipeline = make_pipeline()

    state = pipeline.setup_project(pdf_path, project_id="2026-05-06_pipeline")

    assert (runs_dir / state.project_id / "source.pdf").exists()
    assert (runs_dir / state.project_id / "project_state.json").exists()
    assert state.persona["persona_id"] == "seina"
    assert state.style["style_id"] == "rigorous_science_short"
    assert state.stages["extraction"].status == "pending"


def test_run_extraction_stage_creates_snapshot_and_output(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path, "Pipeline stage text.")
    pipeline = make_pipeline()
    state = pipeline.setup_project(pdf_path, project_id="2026-05-06_run")

    updated = pipeline.run_stage(state.project_id, "extraction")

    revisions = persistence.list_revisions(state.project_id)
    output_path = runs_dir / updated.project_id / updated.extraction.text_md
    assert len(revisions) == 1
    assert updated.stages["extraction"].status == "done"
    assert updated.stages["extraction"].started_at is not None
    assert updated.stages["extraction"].finished_at is not None
    assert output_path.exists()
    assert "Pipeline stage text." in output_path.read_text(encoding="utf-8")


def test_run_done_stage_requires_force(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)
    pipeline = make_pipeline()
    state = pipeline.setup_project(pdf_path, project_id="2026-05-06_done")
    pipeline.run_stage(state.project_id, "extraction")

    try:
        pipeline.run_stage(state.project_id, "extraction")
    except StageAlreadyDoneError as exc:
        assert "force=True" in str(exc)
    else:
        raise AssertionError("Expected StageAlreadyDoneError")


def test_run_claim_extraction_stage_uses_mvp1_service(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    pdf_path = TEST_RUNS_DIR / "input.pdf"
    make_pdf(pdf_path)
    pipeline = make_pipeline()
    state = pipeline.setup_project(pdf_path, project_id="2026-05-06_unimplemented")
    state.stages["extraction"].status = "done"
    persistence.save_state(state)

    def fake_claim_stage(current_state):
        current_state.stages["claim_extraction"].status = "needs_review"
        current_state.stages["claim_extraction"].output_paths = ["claims.json"]
        return current_state

    from p2s_core.pipelines import paper_summary

    monkeypatch.setattr(paper_summary.claim_extraction, "run_claim_extraction_stage", fake_claim_stage)

    updated = pipeline.run_stage(state.project_id, "claim_extraction")

    assert updated.stages["claim_extraction"].status == "needs_review"
    assert updated.stages["claim_extraction"].finished_at is not None
