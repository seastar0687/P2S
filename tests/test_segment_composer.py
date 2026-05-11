import subprocess
from pathlib import Path

import pytest

from p2s_core.models import GeneratedAudio, GeneratedVisual
from p2s_core.services.segment_composer import SegmentCompositionError, compose_segment
from tests.test_visual_placeholder import make_plan


def test_builds_ffmpeg_command_and_writes_segment(tmp_path: Path):
    plan = make_plan()
    (tmp_path / "audio").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "audio" / "scene_001.wav").write_bytes(b"wav")
    (tmp_path / "assets" / "scene_001_textcard.png").write_bytes(b"png")

    def fake_run(command, capture_output, text):
        Path(command[-1]).write_bytes(b"mp4")
        return subprocess.CompletedProcess(command, 0, "", "")

    segment = compose_segment(
        tmp_path,
        plan,
        GeneratedAudio(scene_id="scene_001", text="x", backend="fake", output_path="audio/scene_001.wav", created_at="now"),
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="assets/scene_001_textcard.png", created_at="now"),
        runner=fake_run,
    )

    assert segment.output_path == "segments/scene_001.mp4"
    assert "ffmpeg" in segment.ffmpeg_command[0]


def test_ffmpeg_failure_returns_useful_error(tmp_path: Path):
    def fail_run(command, capture_output, text):
        return subprocess.CompletedProcess(command, 1, "", "bad ffmpeg")

    with pytest.raises(SegmentCompositionError, match="bad ffmpeg"):
        compose_segment(
            tmp_path,
            make_plan(),
            GeneratedAudio(scene_id="scene_001", text="x", backend="fake", output_path="audio/scene_001.wav", created_at="now"),
            GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="assets/scene_001_textcard.png", created_at="now"),
            runner=fail_run,
        )
