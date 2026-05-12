from __future__ import annotations

from pathlib import Path

from p2s_core.models import AssetPlanBundle, GeneratedVisual, ReviewerFinding, ReviewerSummary
from p2s_core.reviewers.final_arbiter import summarize_findings


class VisualAlignmentReviewer:
    name = "VisualAlignmentReviewer"

    def review(
        self,
        run_dir: Path,
        asset_plan: AssetPlanBundle,
        *,
        visual_metadata: list[GeneratedVisual] | None = None,
        figures: list[dict] | None = None,
        metadata_missing: bool = False,
        figures_missing: bool = False,
    ) -> ReviewerSummary:
        findings: list[ReviewerFinding] = []
        visual_map = {item.scene_id: item for item in visual_metadata or []}
        figure_ids = _figure_ids(figures or [])

        if metadata_missing:
            findings.append(
                self._finding(
                    "project",
                    "media_visual_metadata",
                    "medium",
                    "artifact_missing",
                    "media_metadata/visuals.json is missing; visual alignment uses asset_plan only.",
                )
            )
        if figures_missing:
            findings.append(
                self._finding(
                    "project",
                    "figures",
                    "medium",
                    "artifact_missing",
                    "figures.json is missing; paper figure ids cannot be fully validated.",
                )
            )

        for plan in asset_plan.plans:
            visual_plan = plan.visual_plan
            generated = visual_map.get(plan.scene_id)
            output_path = _visual_output_path(generated, visual_plan.output_placeholder)
            artifact_exists = bool(output_path and (run_dir / output_path).exists())

            if visual_plan.enabled and not artifact_exists and plan.asset_policy == "required":
                findings.append(
                    self._finding(
                        "visual",
                        plan.scene_id,
                        "high",
                        "artifact_missing",
                        f"Required visual artifact is missing for {plan.scene_id}.",
                        blocking=True,
                    )
                )
            elif visual_plan.enabled and generated is None and visual_metadata is not None:
                findings.append(
                    self._finding(
                        "visual",
                        plan.scene_id,
                        "medium",
                        "artifact_missing",
                        f"Visual metadata is missing for {plan.scene_id}.",
                    )
                )

            if visual_plan.asset_source == "text_card" and plan.asset_type_hint in {
                "paper_figure",
                "diagram",
                "metaphor_image",
                "chart",
            }:
                findings.append(
                    self._finding(
                        "scene",
                        plan.scene_id,
                        "medium",
                        "fallback_quality",
                        f"{plan.asset_type_hint} visual fell back to text_card.",
                    )
                )

            if visual_plan.asset_source == "paper_figure":
                for figure_id in visual_plan.selected_figure_ids:
                    if figures is not None and figure_id not in figure_ids:
                        findings.append(
                            self._finding(
                                "visual",
                                plan.scene_id,
                                "high" if not artifact_exists else "medium",
                                "visual_mismatch",
                                f"Selected paper figure id does not exist in figures metadata: {figure_id}",
                                blocking=not artifact_exists,
                            )
                        )

            if generated and generated.asset_source != visual_plan.asset_source:
                findings.append(
                    self._finding(
                        "visual",
                        plan.scene_id,
                        "high",
                        "visual_mismatch",
                        f"Generated visual source {generated.asset_source!r} does not match asset_plan source {visual_plan.asset_source!r}.",
                    )
                )

        return summarize_findings(self.name, findings)

    def _finding(
        self,
        target_type: str,
        target_id: str,
        severity: str,
        category: str,
        message: str,
        *,
        blocking: bool = False,
    ) -> ReviewerFinding:
        return ReviewerFinding(
            finding_id=f"{self.name}:{target_id}:{category}:{len(message)}",
            reviewer=self.name,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            category=category,
            message=message,
            blocking=blocking,
        )


def _visual_output_path(generated: GeneratedVisual | None, placeholder: str | None) -> str | None:
    if generated is not None:
        return generated.output_path
    return placeholder


def _figure_ids(figures: list[dict]) -> set[str]:
    ids: set[str] = set()
    for index, figure in enumerate(figures, start=1):
        ids.add(
            str(
                figure.get("figure_id")
                or figure.get("id")
                or figure.get("name")
                or figure.get("path")
                or f"figure_{index:03d}"
            )
        )
    return ids
