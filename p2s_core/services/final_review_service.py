from __future__ import annotations

import json
from pathlib import Path

from p2s_core.models import (
    AssetPlanBundle,
    FinalReviewBundle,
    GeneratedVisual,
    MediaQualityReport,
    ProjectState,
    ReviewerFinding,
    ReviewerSummary,
    ScenesBundle,
)
from p2s_core.reviewers.base import utc_now
from p2s_core.reviewers.devil_advocate import DevilAdvocateReviewer
from p2s_core.reviewers.final_arbiter import FinalArbiter, summarize_findings
from p2s_core.reviewers.final_video import FinalVideoReviewer
from p2s_core.reviewers.paper_fidelity_final import PaperFidelityFinalReviewer
from p2s_core.reviewers.subtitle_readability import SubtitleReadabilityFinalReviewer
from p2s_core.reviewers.visual_alignment import VisualAlignmentReviewer
from p2s_core.services import persistence
from p2s_core.services.narrative_planning import load_project_claims
from p2s_core.services.review_bundle_writer import next_review_paths, write_final_review_outputs


class FinalReviewError(ValueError):
    """Raised when MVP3 final review cannot resolve required inputs."""


INPUT_RESOLVER_REVIEWER = "FinalReviewInputResolver"


def run_final_review_stage(state: ProjectState) -> ProjectState:
    run_dir = persistence.project_dir(state.project_id)
    _require_file(run_dir / persistence.STATE_FILENAME, "project_state.json")
    _require_file(run_dir / "claims.json", "claims.json")
    _require_file(run_dir / "asset_plan.json", "asset_plan.json")
    final_video_path = state.final_video.get("path") or "final/output.mp4"
    _require_file(run_dir / final_video_path, final_video_path)

    claims = load_project_claims(state, run_dir)
    scene_source, scenes_bundle, input_findings = _load_active_scenes(run_dir, state)
    asset_plan = AssetPlanBundle.model_validate_json((run_dir / "asset_plan.json").read_text(encoding="utf-8"))
    media_quality_report, media_quality_missing = _load_optional_model(run_dir / "media_quality_report.json", MediaQualityReport)
    visual_metadata, visual_metadata_missing = _load_optional_visual_metadata(run_dir)
    figures, figures_missing = _load_optional_figures(run_dir, state)

    if not (run_dir / "media_generation_report.json").exists():
        input_findings.append(
            _input_warning(
                "media_generation_report_missing",
                "media_generation_report.json is missing; generation summary is unavailable.",
            )
        )

    _, _, review_id = next_review_paths(run_dir)
    summaries: list[ReviewerSummary] = []
    if input_findings:
        summaries.append(summarize_findings(INPUT_RESOLVER_REVIEWER, input_findings))

    summaries.extend(
        [
            PaperFidelityFinalReviewer().review(claims, _load_extracted_text(run_dir, state), scenes_bundle.scenes),
            VisualAlignmentReviewer().review(
                run_dir,
                asset_plan,
                visual_metadata=visual_metadata,
                figures=figures,
                metadata_missing=visual_metadata_missing,
                figures_missing=figures_missing,
            ),
            SubtitleReadabilityFinalReviewer().review(media_quality_report),
            FinalVideoReviewer().review(
                run_dir,
                final_video_path=final_video_path,
                media_quality_report=media_quality_report,
                media_quality_missing=media_quality_missing,
            ),
            DevilAdvocateReviewer().review(scenes_bundle.scenes),
        ]
    )

    all_findings = [finding for summary in summaries for finding in summary.findings]
    blocking = [finding for finding in all_findings if finding.blocking]
    warnings = [
        finding
        for finding in all_findings
        if not finding.blocking and finding.severity != "info"
    ]
    bundle = FinalReviewBundle(
        project_id=state.project_id,
        review_id=review_id,
        active_scene_source=scene_source,
        final_video_path=final_video_path,
        reviewer_summaries=summaries,
        media_quality_report_path="media_quality_report.json" if media_quality_report else None,
        total_findings=len(all_findings),
        blocking_issues=blocking,
        warnings=warnings,
        created_at=utc_now(),
    )
    decision = FinalArbiter().decide(bundle)
    review_path, gate_path = write_final_review_outputs(run_dir, bundle, decision)

    stage = state.stages["final_review"]
    stage.status = "done" if decision.status == "pass" else "needs_review"
    stage.output_paths = [review_path, gate_path]
    stage.error = None if decision.status == "pass" else decision.rationale
    return state


def _load_active_scenes(run_dir: Path, state: ProjectState) -> tuple[str, ScenesBundle, list[ReviewerFinding]]:
    requested_source = state.active_scene_source or "scenes.json"
    requested_path = run_dir / requested_source
    if requested_path.exists():
        return requested_source, ScenesBundle.model_validate_json(requested_path.read_text(encoding="utf-8")), []

    fallback_path = run_dir / "scenes.json"
    if requested_source != "scenes.json" and fallback_path.exists():
        warning = _input_warning(
            "active_scene_source_fallback",
            f"active_scene_source {requested_source!r} was missing; fell back to 'scenes.json'.",
            target_id="active_scene_source",
        )
        return "scenes.json", ScenesBundle.model_validate_json(fallback_path.read_text(encoding="utf-8")), [warning]

    raise FileNotFoundError(
        f"Active scene source not found: {requested_path}. Fallback scenes.json was not available."
    )


def _load_optional_model(path: Path, model_type):
    if not path.exists():
        return None, True
    return model_type.model_validate_json(path.read_text(encoding="utf-8")), False


def _load_optional_visual_metadata(run_dir: Path) -> tuple[list[GeneratedVisual] | None, bool]:
    path = run_dir / "media_metadata" / "visuals.json"
    if not path.exists():
        return None, True
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise FinalReviewError(f"media visual metadata must be a list: {path}")
    return [GeneratedVisual.model_validate(item) for item in raw], False


def _load_optional_figures(run_dir: Path, state: ProjectState) -> tuple[list[dict] | None, bool]:
    candidates: list[Path] = []
    if state.extraction.figures_path:
        figures_path = Path(state.extraction.figures_path)
        candidates.append(figures_path if figures_path.is_absolute() else run_dir / figures_path)
    candidates.append(run_dir / "figures.json")
    for path in candidates:
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise FinalReviewError(f"figures metadata must be a list: {path}")
            return raw, False
    if state.extraction.figures:
        return list(state.extraction.figures), False
    return None, True


def _load_extracted_text(run_dir: Path, state: ProjectState) -> str:
    for relative in [state.extraction.normalized_text_md, state.extraction.text_md]:
        if not relative:
            continue
        path = Path(relative)
        resolved = path if path.is_absolute() else run_dir / path
        if resolved.exists():
            return resolved.read_text(encoding="utf-8")
    return ""


def _require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required final review input missing: {label}")


def _input_warning(
    suffix: str,
    message: str,
    *,
    target_id: str = "project",
) -> ReviewerFinding:
    return ReviewerFinding(
        finding_id=f"{INPUT_RESOLVER_REVIEWER}:{suffix}",
        reviewer=INPUT_RESOLVER_REVIEWER,
        target_type="project",
        target_id=target_id,
        severity="medium",
        category="artifact_missing",
        message=message,
        blocking=False,
    )
