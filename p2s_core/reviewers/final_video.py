from __future__ import annotations

from pathlib import Path

from p2s_core.models import MediaQualityReport, ReviewerFinding, ReviewerSummary
from p2s_core.reviewers.final_arbiter import summarize_findings


class FinalVideoReviewer:
    name = "FinalVideoReviewer"

    def review(
        self,
        run_dir: Path,
        *,
        final_video_path: str | None,
        media_quality_report: MediaQualityReport | None,
        media_quality_missing: bool = False,
    ) -> ReviewerSummary:
        findings: list[ReviewerFinding] = []
        resolved_video = final_video_path or "final/output.mp4"
        if not (run_dir / resolved_video).exists():
            findings.append(
                self._finding(
                    "final_video_missing",
                    "final_video",
                    "final_video",
                    "critical",
                    "artifact_missing",
                    f"Final video is missing: {resolved_video}",
                    blocking=True,
                    suggested_fix="Run composition again before final review.",
                )
            )

        if media_quality_missing:
            findings.append(
                self._finding(
                    "media_quality_missing",
                    "project",
                    "media_quality_report",
                    "medium",
                    "media_quality",
                    "media_quality_report.json is missing; final media quality checks were skipped.",
                )
            )
        elif media_quality_report is not None:
            if not media_quality_report.pass_gate:
                findings.append(
                    self._finding(
                        "media_quality_failed",
                        "project",
                        "media_quality_report",
                        "high",
                        "media_quality",
                        "media_quality_report.json did not pass its gate.",
                        blocking=True,
                        evidence_refs=media_quality_report.blocking_issues,
                        suggested_fix="Inspect media_quality_report.json before publishing.",
                    )
                )
            if media_quality_report.fallback_quality.quality_level == "minimal":
                findings.append(
                    self._finding(
                        "fallback_quality_minimal",
                        "project",
                        "fallback_quality",
                        "high",
                        "fallback_quality",
                        "Fallback visual quality is minimal.",
                    )
                )
            for index, warning in enumerate(media_quality_report.warnings, start=1):
                if "loudness" in warning.lower():
                    findings.append(
                        self._finding(
                            f"media_quality_warning_{index:03d}",
                            "project",
                            "media_quality_report",
                            "medium",
                            "media_quality",
                            warning,
                        )
                    )

        return summarize_findings(self.name, findings)

    def _finding(
        self,
        suffix: str,
        target_type: str,
        target_id: str,
        severity: str,
        category: str,
        message: str,
        *,
        blocking: bool = False,
        evidence_refs: list[str] | None = None,
        suggested_fix: str | None = None,
    ) -> ReviewerFinding:
        return ReviewerFinding(
            finding_id=f"{self.name}:{suffix}",
            reviewer=self.name,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            category=category,
            message=message,
            evidence_refs=evidence_refs or [],
            suggested_fix=suggested_fix,
            blocking=blocking,
        )
