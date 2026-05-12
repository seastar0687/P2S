from __future__ import annotations

from p2s_core.models import MediaQualityReport, ReviewerFinding, ReviewerSummary
from p2s_core.reviewers.final_arbiter import summarize_findings


class SubtitleReadabilityFinalReviewer:
    name = "SubtitleReadabilityFinalReviewer"

    def review(self, media_quality_report: MediaQualityReport | None) -> ReviewerSummary:
        findings: list[ReviewerFinding] = []
        if media_quality_report is None:
            return summarize_findings(self.name, findings)

        for item in media_quality_report.subtitle_results:
            if not item.safe_area_ok:
                findings.append(
                    self._finding(
                        item.scene_id,
                        "high",
                        "Subtitle safe area check failed.",
                        blocking=True,
                    )
                )
            if item.too_long:
                findings.append(self._finding(item.scene_id, "medium", "Subtitle is too long."))
            if not item.subtitle_text.strip():
                findings.append(self._finding(item.scene_id, "medium", "Subtitle text is empty."))
            for warning in item.warnings:
                findings.append(self._finding(item.scene_id, "medium", warning))

        return summarize_findings(self.name, findings)

    def _finding(
        self,
        scene_id: str,
        severity: str,
        message: str,
        *,
        blocking: bool = False,
    ) -> ReviewerFinding:
        return ReviewerFinding(
            finding_id=f"{self.name}:{scene_id}:{len(message)}",
            reviewer=self.name,
            target_type="subtitle",
            target_id=scene_id,
            severity=severity,
            category="subtitle_readability",
            message=message,
            blocking=blocking,
        )
