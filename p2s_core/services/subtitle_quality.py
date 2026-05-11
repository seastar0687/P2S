from __future__ import annotations

import math

from p2s_core.models import SceneAssetPlan, SubtitleReadabilityResult


def check_subtitle_readability(plan: SceneAssetPlan, *, chars_per_line: int = 14) -> SubtitleReadabilityResult:
    text = plan.subtitle_text.strip()
    char_count = len(text)
    estimated_lines = max(1, math.ceil(char_count / chars_per_line)) if text else 0
    warnings: list[str] = []
    too_long = False
    safe_area_ok = True
    if not text:
        warnings.append("subtitle_text is empty")
    if char_count > 28:
        warnings.append("subtitle_text is longer than 28 characters")
        too_long = True
    if estimated_lines > 2:
        warnings.append("subtitle_text is estimated to need more than 2 lines")
    if estimated_lines > 3 or char_count > 50:
        warnings.append("subtitle_text exceeds safe-area heuristic")
        safe_area_ok = False
    return SubtitleReadabilityResult(
        scene_id=plan.scene_id,
        subtitle_text=text,
        char_count=char_count,
        estimated_lines=estimated_lines,
        font_size=None,
        safe_area_ok=safe_area_ok,
        too_long=too_long,
        pass_gate=safe_area_ok,
        warnings=warnings,
    )
