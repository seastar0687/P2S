import subprocess
from pathlib import Path

from p2s_core.models import GeneratedAudio, GeneratedSegment
from p2s_core.services.segment_quality import check_segment_quality


def test_existing_segment_passes_with_duration(tmp_path: Path):
    path = tmp_path / "segments" / "s1.mp4"
    path.parent.mkdir()
    path.write_bytes(b"mp4")

    def runner(command, capture_output, text):
        return subprocess.CompletedProcess(command, 0, '{"format":{"duration":"1.0"}}', "")

    result = check_segment_quality(
        tmp_path,
        GeneratedSegment(scene_id="s1", audio_path="audio/s1.wav", visual_path="assets/s1.png", output_path="segments/s1.mp4", created_at="now"),
        GeneratedAudio(scene_id="s1", text="x", backend="fake", output_path="audio/s1.wav", duration_sec=1.0, created_at="now"),
        runner=runner,
    )

    assert result.pass_gate is True
    assert result.duration_sec == 1.0


def test_missing_empty_and_delta_warning(tmp_path: Path):
    empty_path = tmp_path / "segments" / "empty.mp4"
    empty_path.parent.mkdir()
    empty_path.write_bytes(b"")
    missing = GeneratedSegment(scene_id="missing", audio_path="a", visual_path="v", output_path="segments/missing.mp4", created_at="now")
    empty = GeneratedSegment(scene_id="empty", audio_path="a", visual_path="v", output_path="segments/empty.mp4", created_at="now")

    def runner(command, capture_output, text):
        return subprocess.CompletedProcess(command, 0, '{"format":{"duration":"5.0"}}', "")

    delta = check_segment_quality(
        tmp_path,
        empty,
        GeneratedAudio(scene_id="empty", text="x", backend="fake", output_path="a", duration_sec=1.0, created_at="now"),
        runner=runner,
    )
    assert check_segment_quality(tmp_path, missing).pass_gate is False
    assert delta.pass_gate is False
    assert any("delta" in warning for warning in delta.warnings)
