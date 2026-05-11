from pathlib import Path

from p2s_core.models import GeneratedAudio, ProjectSource, ProjectState, default_stages
from p2s_core.services.audio_quality import check_audio_quality
from p2s_core.services.tts_service import generate_scene_audio
from tests.test_tts_service_thin import make_plan


def test_valid_wav_passes_with_duration(tmp_path: Path):
    state = ProjectState(
        project_id="p",
        created_at="2026-05-11T00:00:00Z",
        source=ProjectSource(pdf_path="source.pdf"),
        persona={},
        style={},
        stages=default_stages(),
    )
    audio = generate_scene_audio(tmp_path, make_plan(), state, backend="fake")

    result = check_audio_quality(tmp_path, audio)

    assert result.pass_gate is True
    assert result.duration_sec and result.duration_sec > 0
    assert any("loudness unavailable" in warning for warning in result.warnings)


def test_missing_and_empty_audio_fail(tmp_path: Path):
    missing = GeneratedAudio(scene_id="s1", text="x", backend="fake", output_path="audio/missing.wav", created_at="now")
    empty_path = tmp_path / "audio" / "empty.wav"
    empty_path.parent.mkdir()
    empty_path.write_bytes(b"")
    empty = GeneratedAudio(scene_id="s2", text="x", backend="fake", output_path="audio/empty.wav", created_at="now")

    assert check_audio_quality(tmp_path, missing).pass_gate is False
    assert check_audio_quality(tmp_path, empty).pass_gate is False
