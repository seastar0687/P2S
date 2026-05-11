from pathlib import Path

import fitz

from p2s_core.services import persistence
from p2s_core.services.harden1_smoke import run_harden1_smoke_set


def make_pdf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_harden1_smoke_runner_writes_reports(tmp_path: Path, monkeypatch):
    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    fixture_dir = tmp_path / "papers"
    make_pdf(fixture_dir / "paper_a.pdf", "Abstract\n" + "A" * 600)
    make_pdf(fixture_dir / "paper_b.pdf", "Introduction\n" + "B" * 600)

    reports = run_harden1_smoke_set(
        fixture_dir,
        project_prefix="test_harden1",
        summary_path=tmp_path / "HARDEN1_REAL_PAPER_SMOKE.md",
    )

    assert len(reports) == 2
    assert (runs_dir / "test_harden1_001" / "harden1_smoke_report.json").exists()
    assert reports[0].extraction_quality.section_count >= 1
