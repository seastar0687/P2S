import subprocess
from pathlib import Path

from p2s_core.models import CompositionResult, SegmentQualityResult
from p2s_core.services.composition_quality import check_composition_quality


def test_final_output_quality_reads_codecs(tmp_path: Path):
    path = tmp_path / "final" / "output.mp4"
    path.parent.mkdir()
    path.write_bytes(b"mp4")

    def runner(command, capture_output, text):
        return subprocess.CompletedProcess(
            command,
            0,
            '{"format":{"duration":"2.0"},"streams":[{"codec_type":"video","codec_name":"h264","pix_fmt":"yuv420p"},{"codec_type":"audio","codec_name":"aac"}]}',
            "",
        )

    result = check_composition_quality(
        tmp_path,
        "p",
        CompositionResult(project_id="p", segment_paths=["segments/s1.mp4"], output_path="final/output.mp4", created_at="now"),
        [SegmentQualityResult(scene_id="s1", segment_path="segments/s1.mp4", exists=True, duration_sec=2.0, pass_gate=True)],
        runner=runner,
    )

    assert result.pass_gate is True
    assert result.codec_video == "h264"
    assert result.pixel_format == "yuv420p"


def test_missing_empty_and_ffprobe_warning(tmp_path: Path):
    empty_path = tmp_path / "final" / "empty.mp4"
    empty_path.parent.mkdir()
    empty_path.write_bytes(b"")

    missing = check_composition_quality(
        tmp_path,
        "p",
        CompositionResult(project_id="p", segment_paths=[], output_path="final/missing.mp4", created_at="now"),
        [],
    )
    unavailable = check_composition_quality(
        tmp_path,
        "p",
        CompositionResult(project_id="p", segment_paths=[], output_path="final/empty.mp4", created_at="now"),
        [],
        runner=lambda command, capture_output, text: subprocess.CompletedProcess(command, 1, "", "no ffprobe"),
    )

    assert missing.pass_gate is False
    assert unavailable.pass_gate is False
    assert any("ffprobe unavailable" in warning for warning in unavailable.warnings)


def test_ffprobe_metadata_without_duration_fails_when_segments_are_readable(tmp_path: Path):
    path = tmp_path / "final" / "output.mp4"
    path.parent.mkdir()
    path.write_bytes(b"mp4")

    result = check_composition_quality(
        tmp_path,
        "p",
        CompositionResult(project_id="p", segment_paths=["segments/s1.mp4"], output_path="final/output.mp4", created_at="now"),
        [SegmentQualityResult(scene_id="s1", segment_path="segments/s1.mp4", exists=True, duration_sec=1.0, pass_gate=True)],
        runner=lambda command, capture_output, text: subprocess.CompletedProcess(command, 0, '{"streams":[]}', ""),
    )

    assert result.pass_gate is False
    assert any("duration unreadable" in warning for warning in result.warnings)
