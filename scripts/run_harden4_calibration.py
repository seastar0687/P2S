from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from p2s_core.services.reviewer_calibration import run_calibration_suite

SUITE_ROOT = ROOT / "tests" / "golden" / "final_review"
REPORT_DIR = ROOT / "docs" / "sprints" / "HARDEN4" / "reports"
TEMP_ROOT = ROOT / ".test_runs" / "harden4_manual_calibration"


def main() -> None:
    if TEMP_ROOT.exists():
        shutil.rmtree(TEMP_ROOT)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_calibration_suite(SUITE_ROOT, temp_root=TEMP_ROOT)
    json_path = REPORT_DIR / "reviewer_calibration_report.json"
    md_path = REPORT_DIR / "HARDEN4_REVIEWER_CALIBRATION.md"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")
    print(f"case_count: {report.case_count}")
    print(f"passed_count: {report.passed_count}")
    print(f"failed_count: {report.failed_count}")
    print(f"false_negative_risk_count: {report.false_negative_risk_count}")
    print(f"false_positive_risk_count: {report.false_positive_risk_count}")
    print(f"pass_gate: {report.pass_gate}")
    print(f"json: {json_path.relative_to(ROOT)}")
    print(f"markdown: {md_path.relative_to(ROOT)}")


def _markdown_report(report) -> str:
    lines = [
        "# HARDEN-4 Reviewer Calibration",
        "",
        f"Created at: {report.created_at}",
        "",
        "## Summary",
        f"- case_count: {report.case_count}",
        f"- passed_count: {report.passed_count}",
        f"- failed_count: {report.failed_count}",
        f"- false_negative_risk_count: {report.false_negative_risk_count}",
        f"- false_positive_risk_count: {report.false_positive_risk_count}",
        f"- pass_gate: {report.pass_gate}",
        "",
        "## Cases",
    ]
    for result in report.results:
        lines.append(
            f"- {result.case_id}: {'pass' if result.passed else 'fail'} "
            f"(expected={result.expected_status}, actual={result.actual_status})"
        )
        if result.missing_expected_findings:
            lines.append(f"  - missing_expected_findings: {', '.join(result.missing_expected_findings)}")
        if result.unexpected_blocking_findings:
            lines.append(f"  - unexpected_blocking_findings: {', '.join(result.unexpected_blocking_findings)}")
        for note in result.notes:
            lines.append(f"  - note: {note}")
    lines.extend(
        [
            "",
            "## Reviewer Notes",
        ]
    )
    for reviewer, notes in report.reviewer_notes.items():
        for note in notes:
            lines.append(f"- {reviewer}: {note}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
