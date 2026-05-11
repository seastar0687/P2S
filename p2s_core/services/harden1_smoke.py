from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import ProjectSource, ProjectState, RealPaperSmokeReport, default_stages
from p2s_core.models.extraction import ExtractionQualityReport
from p2s_core.services import paper_extraction, persistence


def run_harden1_smoke_set(
    pdf_dir: str | Path = "tests/fixtures/papers/harden1",
    *,
    project_prefix: str = "harden1_smoke",
    summary_path: str | Path = "docs/sprints/HARDEN1/reports/HARDEN1_REAL_PAPER_SMOKE.md",
) -> list[RealPaperSmokeReport]:
    pdf_root = Path(pdf_dir)
    if not pdf_root.exists():
        if str(pdf_dir) == "tests/fixtures/papers/harden1":
            pdf_root = _create_synthetic_smoke_pdfs()
        else:
            raise FileNotFoundError(f"HARDEN-1 smoke fixture directory not found: {pdf_root}")
    pdf_paths = sorted(pdf_root.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found for HARDEN-1 smoke set: {pdf_root}")

    reports: list[RealPaperSmokeReport] = []
    for index, pdf_path in enumerate(pdf_paths, start=1):
        project_id = f"{project_prefix}_{index:03d}"
        run_dir = persistence.project_dir(project_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        copied_pdf = run_dir / "source.pdf"
        shutil.copy2(pdf_path, copied_pdf)
        state = ProjectState(
            project_id=project_id,
            created_at=_utc_now(),
            source=ProjectSource(pdf_path=str(copied_pdf)),
            persona={"persona_id": "seina", "version": "0.1.0"},
            style={"style_id": "rigorous_science_short", "version": "0.1.0"},
            stages=default_stages(),
        )
        updated = paper_extraction.run_extraction_stage(state)
        persistence.save_state(updated)
        quality = ExtractionQualityReport.model_validate_json(
            (run_dir / "extraction_quality_report.json").read_text(encoding="utf-8")
        )
        report = RealPaperSmokeReport(
            project_id=project_id,
            paper_name=pdf_path.name,
            stages_run=["extraction"],
            extraction_quality=quality,
            claim_count=0,
            failed_claim_review_count=0,
            asset_plan_warning_count=0,
            key_warnings=quality.warnings,
            passed=quality.quality_level != "failed",
            notes="Fixture smoke runs extraction hardening only; LLM and media stages are out of scope.",
            created_at=_utc_now(),
        )
        (run_dir / "harden1_smoke_report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        reports.append(report)

    summary_path = Path(summary_path)
    reports_dir = summary_path.parent
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(_render_summary(reports), encoding="utf-8")
    return reports


def _create_synthetic_smoke_pdfs() -> Path:
    import fitz

    pdf_root = Path(".test_runs/harden1_smoke_fixtures")
    pdf_root.mkdir(parents=True, exist_ok=True)
    samples = {
        "paper_a_simple.pdf": (
            "Abstract\n"
            + "This synthetic paper has clear sections and enough text for extraction quality checks. " * 12
            + "\nIntroduction\n"
            + "The introduction explains the study background and contribution. " * 10
        ),
        "paper_b_figures.pdf": (
            "Abstract\n"
            + "This synthetic paper includes figure caption metadata for HARDEN-1 smoke. " * 10
            + "\nMethods\n"
            + "Figure 1. Teacher model transmits traits through numbers.\n"
            + "The methods section describes how the figure should be selected downstream. " * 10
        ),
        "paper_c_linebreaks.pdf": (
            "ABSTRACT\n"
            + "This synthetic paper contains messy line breaks and hyphenated trans-\nformer terms. " * 12
            + "\nRESULTS\n"
            + "The results demonstrate stable extraction behavior across noisy layout text. " * 10
        ),
    }
    for filename, text in samples.items():
        path = pdf_root / filename
        if path.exists():
            continue
        doc = fitz.open()
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(72, 72, 520, 760), text, fontsize=11)
        doc.save(path)
        doc.close()
    return pdf_root


def _render_summary(reports: list[RealPaperSmokeReport]) -> str:
    lines = [
        "# HARDEN-1 Real Paper Smoke",
        "",
        "| Paper | Project | Quality | Sections | Figures | Warnings | Passed |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for report in reports:
        quality = report.extraction_quality
        lines.append(
            "| "
            f"{report.paper_name} | {report.project_id} | {quality.quality_level} | "
            f"{quality.section_count} | {quality.figure_count} | {len(report.key_warnings)} | "
            f"{'yes' if report.passed else 'no'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
