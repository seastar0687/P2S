from pathlib import Path

import fitz

from p2s_core.models import ProjectSource, ProjectState, default_stages
from p2s_core.services import paper_extraction, persistence
from p2s_core.services.asset_preparation import prepare_assets_for_project
from tests.test_asset_preparation_service import scene, write_project


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "harden1_pipeline"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_pdf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def make_state(project_id: str, pdf_path: Path) -> ProjectState:
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-11T00:00:00Z",
        source=ProjectSource(pdf_path=str(pdf_path)),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        stages=default_stages(),
    )


def test_extraction_writes_harden1_artifacts_and_path_references(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "extract_artifacts"
    pdf_path = runs_dir / project_id / "source.pdf"
    make_pdf(pdf_path, "Abstract\nThis is a long enough abstract. " * 30 + "\nIntroduction\nMore text.")

    updated = paper_extraction.run_extraction_stage(make_state(project_id, pdf_path))
    run_dir = runs_dir / project_id

    assert (run_dir / "extraction_quality_report.json").exists()
    assert (run_dir / "sections.json").exists()
    assert (run_dir / "figures.json").exists()
    assert updated.extraction.text_md == "extracted_text.md"
    assert updated.extraction.sections_path == "sections.json"
    assert updated.extraction.figures_path == "figures.json"
    assert updated.extraction.sections == []
    assert updated.extraction.figures == []


def test_asset_preparation_reads_figures_json_when_present():
    root = reset_test_runs()
    run_dir = root / "asset_reads_figures_path"
    run_dir.mkdir(parents=True)
    state = write_project(
        run_dir,
        [scene(asset_policy="required", asset_type_hint="paper_figure")],
        figures=[],
    )
    (run_dir / "figures.json").write_text(
        '[{"figure_id":"fig_001","caption":"Teacher model transmits traits through numbers.","image_path":null}]',
        encoding="utf-8",
    )
    state.extraction.figures_path = "figures.json"

    bundle = prepare_assets_for_project(run_dir, state)

    assert bundle.plans[0].visual_plan.selected_figure_ids == ["fig_001"]


def test_old_project_without_figures_json_warns_not_crashes():
    root = reset_test_runs()
    run_dir = root / "old_without_figures_json"
    run_dir.mkdir(parents=True)
    state = write_project(run_dir, [scene(asset_policy="required", asset_type_hint="paper_figure")], figures=[])

    bundle = prepare_assets_for_project(run_dir, state)

    assert "No figure metadata found" in bundle.quality_report.warnings[0]
