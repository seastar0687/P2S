from __future__ import annotations

from p2s_core.models import PresentationPlan, PresentationProfile, ReviewResult, SceneDraft, SuggestedFix
from p2s_core.reviewers.base import utc_now


class PresentationStructureReviewer:
    name = "PresentationStructureReviewer"

    def review(
        self,
        scenes: list[SceneDraft],
        plan: PresentationPlan,
        profile: PresentationProfile,
    ) -> list[ReviewResult]:
        findings: list[str] = []
        fixes: list[SuggestedFix] = []
        severity = "low"
        score = 1.0

        if profile.presenter_priority == "high" and plan.presenter_visibility_ratio < profile.presenter_min_visibility_ratio:
            findings.append("Presenter visibility ratio is below profile minimum.")
            fixes.append(_fix("presentation_planning", "Increase presenter-visible scenes.", "high"))
            severity = _max_severity(severity, "high")
            score = min(score, 0.2)

        if plan.fullscreen_asset_ratio > profile.fullscreen_asset_max_ratio:
            findings.append("Fullscreen asset ratio exceeds profile maximum.")
            fixes.append(_fix("presentation_planning", "Reduce asset_fullscreen scenes.", "high"))
            severity = _max_severity(severity, "high")
            score = min(score, 0.2)

        required_count = sum(1 for scene in scenes if scene.asset_policy == "required")
        if scenes and required_count == len(scenes) and not profile.require_asset_every_scene:
            findings.append("Every scene requires an asset under a sparse presenter-first profile.")
            fixes.append(_fix("presentation_planning", "Make some scenes presenter-only or optional asset scenes.", "medium"))
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        fullscreen_count = sum(1 for scene in scenes if scene.visual_focus == "asset_fullscreen")
        if scenes and fullscreen_count > max(1, len(scenes) // 3):
            findings.append("Too many scenes suppress presenter with fullscreen assets.")
            fixes.append(_fix("presentation_planning", "Prefer supporting_asset or split for most asset scenes.", "medium"))
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        background_modes = {scene.background_mode for scene in scenes}
        if len(background_modes) > 1 and any(not scene.notes_for_render for scene in scenes):
            findings.append("Background modes vary without render notes explaining the variation.")
            fixes.append(_fix("presentation_planning", "Use consistent background modes or add render notes.", "medium"))
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        return [
            ReviewResult(
                review_id="presentation_structure_stage",
                target_type="presentation",
                target_id="presentation_planning",
                reviewer=self.name,
                score=score,
                pass_gate=_severity_rank(severity) < _severity_rank("high"),
                severity=severity,
                findings=findings,
                suggested_fixes=fixes,
                created_at=utc_now(),
                reviewer_prompt_version="presentation_structure_v1",
            )
        ]


def _fix(target_id: str, suggestion: str, priority: str) -> SuggestedFix:
    return SuggestedFix(
        target_type="field",
        target_id=target_id,
        fix_type="human_check",
        suggestion=suggestion,
        priority=priority,
    )


def _max_severity(current: str, candidate: str) -> str:
    return candidate if _severity_rank(candidate) > _severity_rank(current) else current


def _severity_rank(severity: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}[severity]
