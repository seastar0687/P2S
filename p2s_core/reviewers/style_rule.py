from __future__ import annotations

import re
from pathlib import Path

from p2s_core.models import ReviewResult, SceneDraft, SuggestedFix
from p2s_core.reviewers.base import utc_now


ABSOLUTE_HOOK_PHRASES = ("完全", "絕對", "guarantee", "proves", "absolutely")


class StyleRuleReviewer:
    name = "StyleRuleReviewer"

    def review(self, scenes: list[SceneDraft], style: dict) -> list[ReviewResult]:
        forbidden = _load_forbidden_phrases(style)
        max_voice_chars = int(style.get("sentence_rules", {}).get("max_voice_chars_per_scene", 55))
        max_subtitle_chars = int(style.get("subtitle_rules", {}).get("max_subtitle_chars", 24))
        return [
            self._review_scene(scene, forbidden, max_voice_chars, max_subtitle_chars)
            for scene in scenes
        ]

    def _review_scene(
        self,
        scene: SceneDraft,
        forbidden: list[str],
        max_voice_chars: int,
        max_subtitle_chars: int,
    ) -> ReviewResult:
        findings: list[str] = []
        fixes: list[SuggestedFix] = []
        severity = "low"
        score = 1.0
        voice_lower = scene.voice_text.lower()

        for phrase in forbidden:
            if _contains_phrase(voice_lower, phrase):
                findings.append(f"Forbidden style phrase appears in voice_text: {phrase}.")
                fixes.append(_fix(scene.scene_id, "voice_text", "Remove forbidden style phrase.", "high"))
                severity = _max_severity(severity, "high")
                score = min(score, 0.2)

        if len(scene.voice_text) > max_voice_chars:
            findings.append("voice_text exceeds style max_voice_chars_per_scene.")
            fixes.append(_fix(scene.scene_id, "voice_text", "Shorten voice_text for short-form pacing.", "medium"))
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        if len(scene.subtitle_text) > max_subtitle_chars:
            findings.append("subtitle_text exceeds style max_subtitle_chars.")
            fixes.append(_fix(scene.scene_id, "subtitle_text", "Shorten subtitle_text.", "medium"))
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        if len(scene.subtitle_text) >= len(scene.voice_text):
            findings.append("subtitle_text should be shorter than voice_text.")
            fixes.append(_fix(scene.scene_id, "subtitle_text", "Make subtitle_text shorter than voice_text.", "medium"))
            severity = _max_severity(severity, "medium")
            score = min(score, 0.6)

        if scene.purpose == "hook" and any(phrase in voice_lower for phrase in ABSOLUTE_HOOK_PHRASES):
            findings.append("Hook uses unsupported absolute phrasing.")
            fixes.append(_fix(scene.scene_id, "voice_text", "Use a grounded, non-absolute hook.", "high"))
            severity = _max_severity(severity, "high")
            score = min(score, 0.2)

        return ReviewResult(
            review_id=f"style_rule_{scene.scene_id}",
            target_type="scene",
            target_id=scene.scene_id,
            reviewer=self.name,
            score=score,
            pass_gate=_severity_rank(severity) < _severity_rank("high"),
            severity=severity,
            findings=findings,
            suggested_fixes=fixes,
            created_at=utc_now(),
            reviewer_prompt_version="style_rule_v1",
        )


def _load_forbidden_phrases(style: dict) -> list[str]:
    path = style.get("forbidden_phrases_path")
    style_id = style.get("style_id")
    candidates = []
    if path and style_id:
        candidates.append(Path("p2s_core/styles") / style_id / path)
    if path:
        candidates.append(Path(path))

    for candidate in candidates:
        if candidate.exists():
            phrases = []
            for line in candidate.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    phrases.append(stripped)
            return phrases
    return []


def _contains_phrase(text: str, phrase: str) -> bool:
    phrase_lower = phrase.lower()
    if phrase_lower.isascii():
        return re.search(rf"\b{re.escape(phrase_lower)}\b", text) is not None
    return phrase_lower in text


def _fix(target_id: str, field: str, suggestion: str, priority: str) -> SuggestedFix:
    return SuggestedFix(
        target_type="scene",
        target_id=target_id,
        target_field=field,
        fix_type="rewrite",
        suggestion=suggestion,
        priority=priority,
    )


def _max_severity(current: str, candidate: str) -> str:
    return candidate if _severity_rank(candidate) > _severity_rank(current) else current


def _severity_rank(severity: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}[severity]
