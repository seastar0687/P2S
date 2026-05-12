from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import (
    AssetPlanBundle,
    ExpectedGateOutcome,
    ExpectedReviewerFinding,
    FinalReviewBundle,
    GeneratedVisual,
    GoldenReviewCase,
    MediaQualityReport,
    PaperClaim,
    ProjectState,
    ReviewerCalibrationReport,
    ReviewerCalibrationResult,
    ReviewerFinding,
    ReviewerSummary,
    ScenesBundle,
)
from p2s_core.models.reviewer_calibration import severity_satisfies
from p2s_core.reviewers.devil_advocate import DevilAdvocateReviewer
from p2s_core.reviewers.final_arbiter import FinalArbiter
from p2s_core.reviewers.final_video import FinalVideoReviewer
from p2s_core.reviewers.paper_fidelity_final import PaperFidelityFinalReviewer
from p2s_core.reviewers.subtitle_readability import SubtitleReadabilityFinalReviewer
from p2s_core.reviewers.visual_alignment import VisualAlignmentReviewer
from p2s_core.services.golden_case_loader import (
    copy_input_to_temp,
    load_expected_findings,
    load_expected_gate,
    load_golden_cases,
)


def run_calibration_suite(
    suite_root: Path | str,
    *,
    temp_root: Path,
) -> ReviewerCalibrationReport:
    suite_root = Path(suite_root)
    cases = load_golden_cases(suite_root)
    results = [
        run_calibration_case(suite_root / case.case_id, case, temp_root=temp_root)
        for case in cases
    ]
    false_negative_count = sum(1 for result in results if result.unexpected_pass)
    false_positive_count = sum(1 for result in results if result.unexpected_reject)
    passed_count = sum(1 for result in results if result.passed)
    critical_prompt_rejects = any(
        result.case_id == "critical_prompt_injection" and result.actual_status == "reject"
        for result in results
    )
    media_quality_not_pass = any(
        result.case_id == "media_quality_fail" and result.actual_status != "pass"
        for result in results
    )
    good_case_passes = any(
        result.case_id == "good_case" and result.actual_status == "pass" and result.passed
        for result in results
    )
    pass_gate = (
        false_negative_count == 0
        and false_positive_count <= 1
        and good_case_passes
        and critical_prompt_rejects
        and media_quality_not_pass
        and passed_count == len(results)
    )
    return ReviewerCalibrationReport(
        case_count=len(results),
        passed_count=passed_count,
        failed_count=len(results) - passed_count,
        false_negative_risk_count=false_negative_count,
        false_positive_risk_count=false_positive_count,
        results=results,
        reviewer_notes={
            "VisualAlignmentReviewer": [
                "HARDEN-4 v1 checks artifact and metadata consistency, not semantic image understanding."
            ]
        },
        pass_gate=pass_gate,
        created_at=datetime.now(UTC).isoformat(),
    )


def run_calibration_case(
    case_dir: Path,
    case: GoldenReviewCase,
    *,
    temp_root: Path,
) -> ReviewerCalibrationResult:
    run_dir = copy_input_to_temp(case_dir, case, temp_root)
    expected_gate = load_expected_gate(case_dir, case)
    expected_findings = load_expected_findings(case_dir, case)
    bundle, status = review_fixture(run_dir)
    all_findings = [finding for summary in bundle.reviewer_summaries for finding in summary.findings]
    missing = [
        _expected_finding_label(expected)
        for expected in expected_findings
        if not _matches_any_expected(all_findings, expected)
    ]
    unexpected_blocking = _unexpected_blocking_labels(all_findings, expected_gate)
    notes: list[str] = []
    if status != expected_gate.expected_status:
        notes.append(f"Expected status {expected_gate.expected_status}, got {status}.")
    for category in expected_gate.must_have_blocking_categories:
        if category not in {finding.category for finding in bundle.blocking_issues}:
            missing.append(f"blocking:{category}")
    for category in expected_gate.must_not_have_blocking_categories:
        if category in {finding.category for finding in bundle.blocking_issues}:
            unexpected_blocking.append(category)

    unexpected_pass = expected_gate.expected_status in {"human_check", "reject"} and status == "pass"
    unexpected_reject = expected_gate.expected_status == "pass" and status in {"human_check", "reject"}
    passed = (
        status == expected_gate.expected_status
        and not missing
        and not unexpected_blocking
        and not unexpected_pass
        and not unexpected_reject
    )
    return ReviewerCalibrationResult(
        case_id=case.case_id,
        passed=passed,
        expected_status=expected_gate.expected_status,
        actual_status=status,
        missing_expected_findings=missing,
        unexpected_blocking_findings=unexpected_blocking,
        unexpected_pass=unexpected_pass,
        unexpected_reject=unexpected_reject,
        notes=notes,
    )


def review_fixture(run_dir: Path) -> tuple[FinalReviewBundle, str]:
    state = ProjectState.model_validate_json((run_dir / "project_state.json").read_text(encoding="utf-8"))
    claims = _load_claims(run_dir, state)
    scenes = ScenesBundle.model_validate_json((run_dir / (state.active_scene_source or "scenes.json")).read_text(encoding="utf-8"))
    asset_plan = AssetPlanBundle.model_validate_json((run_dir / "asset_plan.json").read_text(encoding="utf-8"))
    media_quality = _load_optional_model(run_dir / "media_quality_report.json", MediaQualityReport)
    visuals = _load_visuals(run_dir / "media_metadata" / "visuals.json")
    figures = _load_optional_json_list(run_dir / "figures.json")
    extracted_text = _load_extracted_text(run_dir, state)
    final_video_path = state.final_video.get("path") or "final/output.mp4"

    summaries: list[ReviewerSummary] = [
        PaperFidelityFinalReviewer().review(claims, extracted_text, scenes.scenes),
        VisualAlignmentReviewer().review(
            run_dir,
            asset_plan,
            visual_metadata=visuals,
            figures=figures,
            metadata_missing=visuals is None,
            figures_missing=figures is None,
        ),
        SubtitleReadabilityFinalReviewer().review(media_quality),
        FinalVideoReviewer().review(
            run_dir,
            final_video_path=final_video_path,
            media_quality_report=media_quality,
            media_quality_missing=media_quality is None,
        ),
        DevilAdvocateReviewer().review(scenes.scenes),
    ]
    all_findings = [finding for summary in summaries for finding in summary.findings]
    bundle = FinalReviewBundle(
        project_id=state.project_id,
        review_id="calibration_review",
        active_scene_source=state.active_scene_source,
        final_video_path=final_video_path,
        reviewer_summaries=summaries,
        media_quality_report_path="media_quality_report.json" if media_quality else None,
        total_findings=len(all_findings),
        blocking_issues=[finding for finding in all_findings if finding.blocking],
        warnings=[finding for finding in all_findings if not finding.blocking and finding.severity != "info"],
        created_at=datetime.now(UTC).isoformat(),
    )
    return bundle, FinalArbiter().decide(bundle).status


def _matches_any_expected(findings: list[ReviewerFinding], expected: ExpectedReviewerFinding) -> bool:
    for finding in findings:
        if expected.reviewer and finding.reviewer != expected.reviewer:
            continue
        if finding.category != expected.category:
            continue
        if expected.target_type and finding.target_type != expected.target_type:
            continue
        if expected.target_id and finding.target_id != expected.target_id:
            continue
        if expected.blocking is not None and finding.blocking != expected.blocking:
            continue
        if not severity_satisfies(finding.severity, expected.severity_at_least):
            continue
        if any(keyword not in finding.message for keyword in expected.must_contain_message):
            continue
        return True
    return False


def _unexpected_blocking_labels(
    findings: list[ReviewerFinding],
    expected_gate: ExpectedGateOutcome,
) -> list[str]:
    allowed = set(expected_gate.must_have_blocking_categories)
    if expected_gate.expected_status != "pass":
        return []
    return sorted({finding.category for finding in findings if finding.blocking and finding.category not in allowed})


def _expected_finding_label(expected: ExpectedReviewerFinding) -> str:
    parts = [expected.reviewer or "*", expected.category]
    if expected.target_id:
        parts.append(expected.target_id)
    return ":".join(parts)


def _load_claims(run_dir: Path, state: ProjectState) -> list[PaperClaim]:
    if state.claims:
        return state.claims
    raw = json.loads((run_dir / "claims.json").read_text(encoding="utf-8"))
    return [PaperClaim.model_validate(item) for item in raw]


def _load_optional_model(path: Path, model_type):
    if not path.exists():
        return None
    return model_type.model_validate_json(path.read_text(encoding="utf-8"))


def _load_visuals(path: Path) -> list[GeneratedVisual] | None:
    raw = _load_optional_json_list(path)
    if raw is None:
        return None
    return [GeneratedVisual.model_validate(item) for item in raw]


def _load_optional_json_list(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def _load_extracted_text(run_dir: Path, state: ProjectState) -> str:
    if not state.extraction.text_md:
        return ""
    path = run_dir / state.extraction.text_md
    return path.read_text(encoding="utf-8") if path.exists() else ""
