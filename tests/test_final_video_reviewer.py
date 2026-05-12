from pathlib import Path

from p2s_core.models import (
    CompositionQualityResult,
    FallbackQualityReport,
    MediaQualityReport,
)
from p2s_core.reviewers.final_video import FinalVideoReviewer


def _report(pass_gate=True, quality_level="good", warnings=None):
    return MediaQualityReport(
        project_id="p",
        audio_results=[],
        subtitle_results=[],
        visual_layout_results=[],
        segment_results=[],
        composition_result=CompositionQualityResult(project_id="p", output_path="final/output.mp4", exists=True, pass_gate=True),
        fallback_quality=FallbackQualityReport(scene_count=1, fallback_visual_count=0, fallback_ratio=0, quality_level=quality_level),
        pass_gate=pass_gate,
        blocking_issues=[] if pass_gate else ["composition: failed"],
        warnings=warnings or [],
        created_at="2026-05-12T00:00:00Z",
    )


def test_media_quality_passes_when_video_exists(tmp_path: Path):
    (tmp_path / "final").mkdir()
    (tmp_path / "final" / "output.mp4").write_bytes(b"mp4")
    summary = FinalVideoReviewer().review(tmp_path, final_video_path="final/output.mp4", media_quality_report=_report())
    assert summary.pass_gate is True


def test_media_quality_failure_blocks(tmp_path: Path):
    (tmp_path / "final").mkdir()
    (tmp_path / "final" / "output.mp4").write_bytes(b"mp4")
    summary = FinalVideoReviewer().review(tmp_path, final_video_path="final/output.mp4", media_quality_report=_report(False))
    assert summary.pass_gate is False
    assert any(f.blocking for f in summary.findings)


def test_missing_final_video_is_critical_blocking(tmp_path: Path):
    summary = FinalVideoReviewer().review(tmp_path, final_video_path="final/output.mp4", media_quality_report=_report())
    assert summary.pass_gate is False
    assert any(f.severity == "critical" for f in summary.findings)


def test_loudness_unavailable_warning_is_preserved(tmp_path: Path):
    (tmp_path / "final").mkdir()
    (tmp_path / "final" / "output.mp4").write_bytes(b"mp4")
    summary = FinalVideoReviewer().review(
        tmp_path,
        final_video_path="final/output.mp4",
        media_quality_report=_report(warnings=["loudness unavailable"]),
    )
    assert summary.pass_gate is True
    assert any("loudness" in f.message for f in summary.findings)


def test_fallback_quality_minimal_warns_not_rejects(tmp_path: Path):
    (tmp_path / "final").mkdir()
    (tmp_path / "final" / "output.mp4").write_bytes(b"mp4")
    summary = FinalVideoReviewer().review(
        tmp_path,
        final_video_path="final/output.mp4",
        media_quality_report=_report(quality_level="minimal"),
    )
    assert summary.pass_gate is True
    assert any(f.category == "fallback_quality" for f in summary.findings)
