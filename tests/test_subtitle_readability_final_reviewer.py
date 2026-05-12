from p2s_core.models import (
    CompositionQualityResult,
    FallbackQualityReport,
    MediaQualityReport,
    SubtitleReadabilityResult,
)
from p2s_core.reviewers.subtitle_readability import SubtitleReadabilityFinalReviewer


def _report(subtitle: SubtitleReadabilityResult) -> MediaQualityReport:
    return MediaQualityReport(
        project_id="p",
        audio_results=[],
        subtitle_results=[subtitle],
        visual_layout_results=[],
        segment_results=[],
        composition_result=CompositionQualityResult(project_id="p", output_path="final/output.mp4", exists=True, pass_gate=True),
        fallback_quality=FallbackQualityReport(scene_count=1, fallback_visual_count=0, fallback_ratio=0, quality_level="good"),
        pass_gate=True,
        created_at="2026-05-12T00:00:00Z",
    )


def test_safe_area_failure_blocks():
    subtitle = SubtitleReadabilityResult(
        scene_id="scene_001",
        subtitle_text="text",
        char_count=4,
        estimated_lines=1,
        safe_area_ok=False,
        pass_gate=False,
    )
    summary = SubtitleReadabilityFinalReviewer().review(_report(subtitle))
    assert summary.pass_gate is False
    assert any(f.blocking for f in summary.findings)


def test_too_long_subtitle_warns():
    subtitle = SubtitleReadabilityResult(
        scene_id="scene_001",
        subtitle_text="long text",
        char_count=80,
        estimated_lines=3,
        too_long=True,
        pass_gate=True,
    )
    summary = SubtitleReadabilityFinalReviewer().review(_report(subtitle))
    assert summary.pass_gate is True
    assert summary.warning_count == 1
