from p2s_core.models import (
    AudioQualityResult,
    CompositionQualityResult,
    FallbackQualityReport,
    MediaQualityReport,
    SegmentQualityResult,
    SubtitleReadabilityResult,
    VisualLayoutQualityResult,
)


def test_media_quality_schemas_roundtrip():
    audio = AudioQualityResult(scene_id="s1", audio_path="audio/s1.wav", exists=True, pass_gate=True)
    subtitle = SubtitleReadabilityResult(scene_id="s1", subtitle_text="Short", char_count=5, estimated_lines=1, pass_gate=True)
    visual = VisualLayoutQualityResult(scene_id="s1", visual_path="assets/s1.png", pass_gate=True)
    segment = SegmentQualityResult(scene_id="s1", segment_path="segments/s1.mp4", exists=True, pass_gate=True)
    composition = CompositionQualityResult(project_id="p", output_path="final/output.mp4", exists=True, pass_gate=True)
    fallback = FallbackQualityReport(
        scene_count=1,
        fallback_visual_count=0,
        fallback_ratio=0,
        fallback_by_reason={"unknown_fallback": 0},
        quality_level="good",
    )
    report = MediaQualityReport(
        project_id="p",
        audio_results=[audio],
        subtitle_results=[subtitle],
        visual_layout_results=[visual],
        segment_results=[segment],
        composition_result=composition,
        fallback_quality=fallback,
        pass_gate=True,
        created_at="2026-05-11T00:00:00Z",
    )

    assert MediaQualityReport.model_validate_json(report.model_dump_json()).project_id == "p"
