from __future__ import annotations

import re

from p2s_core.models import PaperClaim, ReviewResult, SceneDraft, SuggestedFix
from p2s_core.reviewers.base import utc_now


FORBIDDEN_UNSUPPORTED_PHRASES = (
    "證明",
    "完全解決",
    "革命性",
    "guarantee",
    "proves",
    "revolutionary",
    "completely solves",
    "革命性",
)


class ScriptGroundingReviewer:
    name = "ScriptGroundingReviewer"

    def review(self, scenes: list[SceneDraft], claims: list[PaperClaim]) -> list[ReviewResult]:
        claim_map = {claim.claim_id: claim for claim in claims}
        return [self._review_scene(scene, claim_map) for scene in scenes]

    def _review_scene(self, scene: SceneDraft, claim_map: dict[str, PaperClaim]) -> ReviewResult:
        findings: list[str] = []
        fixes: list[SuggestedFix] = []
        severity = "low"
        score = 1.0

        if scene.purpose != "transition" and not scene.claim_ids:
            findings.append("Non-transition scene has no claim_ids.")
            fixes.append(_fix(scene.scene_id, "claim_ids", "Attach at least one grounded claim or make this a transition scene.", "critical"))
            severity = _max_severity(severity, "critical")
            score = min(score, 0.0)

        invalid_ids = [claim_id for claim_id in scene.claim_ids if claim_id not in claim_map]
        if invalid_ids:
            findings.append(f"Scene references unknown claim ids: {invalid_ids}.")
            fixes.append(_fix(scene.scene_id, "claim_ids", "Remove unknown claim ids or regenerate from valid claims.", "critical"))
            severity = _max_severity(severity, "critical")
            score = min(score, 0.0)

        if scene.asset_policy == "required" and (not scene.asset_intent or scene.asset_type_hint == "none"):
            findings.append("Required asset scene is missing asset_intent or asset_type_hint.")
            fixes.append(_fix(scene.scene_id, "asset_intent", "Add concrete asset intent and non-none asset_type_hint.", "critical"))
            severity = _max_severity(severity, "critical")
            score = min(score, 0.0)

        unsupported_phrase = _unsupported_phrase(scene, claim_map)
        if unsupported_phrase:
            findings.append(f"Unsupported high-certainty phrase appears in voice_text: {unsupported_phrase}.")
            fixes.append(_fix(scene.scene_id, "voice_text", "Rewrite without unsupported certainty or hype.", "high"))
            severity = _max_severity(severity, "high")
            score = min(score, 0.2)

        if scene.purpose == "transition" and _looks_factual(scene.voice_text):
            findings.append("Transition scene appears to introduce a factual or numerical claim.")
            fixes.append(_fix(scene.scene_id, "voice_text", "Keep transition text connective and non-factual.", "high"))
            severity = _max_severity(severity, "high")
            score = min(score, 0.2)

        return ReviewResult(
            review_id=f"script_grounding_{scene.scene_id}",
            target_type="scene",
            target_id=scene.scene_id,
            reviewer=self.name,
            score=score if not findings else min(score, 0.8),
            pass_gate=not any(_severity_rank(item) >= _severity_rank("high") for item in [severity]),
            severity=severity,
            findings=findings,
            suggested_fixes=fixes,
            evidence_refs=scene.claim_ids,
            created_at=utc_now(),
            reviewer_prompt_version="script_grounding_v1",
        )


def _unsupported_phrase(scene: SceneDraft, claim_map: dict[str, PaperClaim]) -> str | None:
    linked_text = " ".join(
        claim_map[claim_id].claim_text
        for claim_id in scene.claim_ids
        if claim_id in claim_map
    ).lower()
    voice = scene.voice_text.lower()
    for phrase in FORBIDDEN_UNSUPPORTED_PHRASES:
        if _contains_phrase(voice, phrase) and not _contains_phrase(linked_text, phrase):
            return phrase
    return None


def _contains_phrase(text: str, phrase: str) -> bool:
    phrase_lower = phrase.lower()
    if phrase_lower.isascii():
        return re.search(rf"\b{re.escape(phrase_lower)}\b", text) is not None
    return phrase_lower in text


def _looks_factual(text: str) -> bool:
    if re.search(r"\d", text):
        return True
    return any(keyword in text.lower() for keyword in ("improve", "achieve", "accuracy", "證明", "提升", "降低"))


def _fix(target_id: str, field: str, suggestion: str, priority: str) -> SuggestedFix:
    return SuggestedFix(
        target_type="scene",
        target_id=target_id,
        target_field=field,
        fix_type="rewrite" if field == "voice_text" else "human_check",
        suggestion=suggestion,
        priority=priority,
    )


def _max_severity(current: str, candidate: str) -> str:
    return candidate if _severity_rank(candidate) > _severity_rank(current) else current


def _severity_rank(severity: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}[severity]
