import subprocess
from pathlib import Path

import pytest

from p2s_core.models import GeneratedSegment
from p2s_core.services.video_service import VideoCompositionError, compose_final_video


def segment(scene_id: str) -> GeneratedSegment:
    return GeneratedSegment(
        scene_id=scene_id,
        audio_path=f"audio/{scene_id}.wav",
        visual_path=f"assets/{scene_id}.png",
        output_path=f"segments/{scene_id}.mp4",
        created_at="now",
    )


def test_concat_command_writes_final_output_in_order(tmp_path: Path):
    (tmp_path / "segments").mkdir()
    (tmp_path / "segments" / "scene_001.mp4").write_bytes(b"one")
    (tmp_path / "segments" / "scene_002.mp4").write_bytes(b"two")

    def fake_run(command, capture_output, text):
        Path(command[-1]).write_bytes(b"final")
        return subprocess.CompletedProcess(command, 0, "", "")

    result = compose_final_video(tmp_path, "project", [segment("scene_001"), segment("scene_002")], runner=fake_run)

    assert result.output_path == "final/output.mp4"
    assert result.segment_paths == ["segments/scene_001.mp4", "segments/scene_002.mp4"]
    assert (tmp_path / result.output_path).exists()


def test_missing_segment_fails(tmp_path: Path):
    with pytest.raises(VideoCompositionError, match="missing segment"):
        compose_final_video(tmp_path, "project", [segment("missing")])
