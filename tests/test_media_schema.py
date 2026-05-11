from p2s_core.models import (
    CompositionResult,
    GeneratedAudio,
    GeneratedSegment,
    GeneratedVisual,
    MediaGenerationReport,
)


def test_media_schemas_roundtrip():
    audio = GeneratedAudio(
        scene_id="scene_001",
        text="Hello",
        backend="fake",
        output_path="audio/scene_001.wav",
        duration_sec=0.75,
        created_at="2026-05-11T00:00:00Z",
    )
    visual = GeneratedVisual(
        scene_id="scene_001",
        asset_source="text_card",
        output_path="assets/scene_001_textcard.png",
        created_at="2026-05-11T00:00:00Z",
    )
    segment = GeneratedSegment(
        scene_id="scene_001",
        audio_path=audio.output_path,
        visual_path=visual.output_path,
        output_path="segments/scene_001.mp4",
        created_at="2026-05-11T00:00:00Z",
    )
    composition = CompositionResult(
        project_id="media",
        segment_paths=[segment.output_path],
        output_path="final/output.mp4",
        created_at="2026-05-11T00:00:00Z",
    )
    report = MediaGenerationReport(
        project_id="media",
        scene_count=1,
        audio_count=1,
        visual_count=1,
        segment_count=1,
        fallback_visual_count=0,
        failed_scene_count=0,
        created_at="2026-05-11T00:00:00Z",
    )

    assert GeneratedAudio.model_validate_json(audio.model_dump_json()).output_path == "audio/scene_001.wav"
    assert GeneratedVisual.model_validate_json(visual.model_dump_json()).asset_source == "text_card"
    assert GeneratedSegment.model_validate_json(segment.model_dump_json()).scene_id == "scene_001"
    assert CompositionResult.model_validate_json(composition.model_dump_json()).output_path == "final/output.mp4"
    assert MediaGenerationReport.model_validate_json(report.model_dump_json()).segment_count == 1
