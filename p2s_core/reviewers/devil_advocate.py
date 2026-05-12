from __future__ import annotations

import re

from p2s_core.models import ReviewerFinding, ReviewerSummary, SceneDraft
from p2s_core.reviewers.final_arbiter import summarize_findings


HYPE_WARNING_PATTERNS = [
    r"顯著進步",
    r"重要貢獻",
    r"\bsignificant progress\b",
    r"\bimportant contribution\b",
]
HYPE_BLOCKING_PATTERNS = [
    r"革命性",
    r"顛覆",
    r"完全解決",
    r"\brevolutionary\b",
    r"\brevolutionizes\b",
]
ABSOLUTE_PATTERNS = [
    r"絕對",
    r"保證",
    r"\bprove\b",
    r"\bproves\b",
    r"\bguarantee\b",
    r"\bguarantees\b",
]
PROMPT_INJECTION_PATTERNS = [
    r"ignore previous",
    r"ignore all previous",
    r"give this a pass",
    r"給我\s*pass",
    r"直接\s*pass",
    r"reviewer.*pass",
    r"reviewer.*safe",
    r"忽略前面的規則",
    r"直接給通過",
]
CRITICAL_PROMPT_INJECTION_PATTERNS = [
    r"system prompt",
    r"override the rubric",
]


class DevilAdvocateReviewer:
    name = "DevilAdvocateReviewer"

    def review(self, scenes: list[SceneDraft]) -> ReviewerSummary:
        findings: list[ReviewerFinding] = []
        for scene in scenes:
            text = f"{scene.voice_text}\n{scene.subtitle_text}".lower()
            findings.extend(self._scan(scene.scene_id, text, HYPE_WARNING_PATTERNS, "overhype", "medium", False))
            findings.extend(self._scan(scene.scene_id, text, HYPE_BLOCKING_PATTERNS, "overhype", "high", True))
            findings.extend(self._scan(scene.scene_id, text, ABSOLUTE_PATTERNS, "unsupported_claim", "high", True))
            findings.extend(self._scan(scene.scene_id, text, PROMPT_INJECTION_PATTERNS, "prompt_injection", "high", True))
            findings.extend(self._scan(scene.scene_id, text, CRITICAL_PROMPT_INJECTION_PATTERNS, "prompt_injection", "critical", True))
        return summarize_findings(self.name, findings)

    def _scan(
        self,
        scene_id: str,
        text: str,
        patterns: list[str],
        category: str,
        severity: str,
        blocking: bool,
    ) -> list[ReviewerFinding]:
        findings: list[ReviewerFinding] = []
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(
                    ReviewerFinding(
                        finding_id=f"{self.name}:{scene_id}:{category}:{pattern}",
                        reviewer=self.name,
                        target_type="scene",
                        target_id=scene_id,
                        severity=severity,
                        category=category,
                        message=f"Scene text matched risk pattern: {pattern}",
                        suggested_fix="Rewrite the scene text so it cannot instruct or mislead reviewers." if category == "prompt_injection" else "Narrow the wording to match the paper evidence.",
                        blocking=blocking,
                    )
                )
        return findings
