from pathlib import Path

import pytest

from p2s_core.models import ProjectSource, ProjectState, SceneAssetPlan, default_stages
from p2s_core.models.asset_plan import RenderPlan, TTSPlan, VisualAssetPlan
from p2s_core.services.tts_service import TTSGenerationError, generate_scene_audio, read_wav_duration


def make_state() -> ProjectState:
    return ProjectState(
        project_id="tts",
        created_at="2026-05-11T00:00:00Z",
        source=ProjectSource(pdf_path="runs/tts/source.pdf"),
        persona={"voice": {"default_voice": "persona_voice"}},
        style={"style_id": "style"},
        stages=default_stages(),
    )


def make_plan(**tts_overrides) -> SceneAssetPlan:
    tts = {
        "backend": "fake",
        "voice": None,
        "speed": 1.0,
        "text": "Exact TTS text.",
        "output_path": "audio/scene_001.wav",
        "estimated_duration_sec": 1.2,
    }
    tts.update(tts_overrides)
    return SceneAssetPlan(
        scene_id="scene_001",
        purpose="test",
        claim_ids=[],
        voice_text="voice",
        subtitle_text="subtitle",
        presenter_mode="off_screen",
        visual_focus="text_card",
        asset_policy="optional",
        asset_type_hint="none",
        background_mode="static_clean",
        tts_plan=TTSPlan(**tts),
        visual_plan=VisualAssetPlan(enabled=True, asset_source="text_card", asset_type_hint="none", fallback_chain=["text_card"]),
        render_plan=RenderPlan(template_hint="text_card", layout_mode="text_card", background_mode="static_clean", output_segment_placeholder="segments/scene_001.mp4"),
    )


def test_fake_backend_writes_valid_wav_and_reads_duration(tmp_path: Path):
    result = generate_scene_audio(tmp_path, make_plan(voice="scene_voice"), make_state())

    assert result.output_path == "audio/scene_001.wav"
    assert result.text == "Exact TTS text."
    assert result.voice == "scene_voice"
    assert result.duration_sec and result.duration_sec > 0
    assert read_wav_duration(tmp_path / result.output_path) == result.duration_sec


def test_voice_fallback_order_uses_persona_voice(tmp_path: Path):
    result = generate_scene_audio(tmp_path, make_plan(), make_state())

    assert result.voice == "persona_voice"


def test_duration_fallback_when_reader_returns_none(tmp_path: Path):
    result = generate_scene_audio(tmp_path, make_plan(estimated_duration_sec=2.5), make_state(), duration_reader=lambda _: None)

    assert result.duration_sec == 2.5
    assert result.warnings


def test_failure_after_retries_raises(tmp_path: Path):
    with pytest.raises(TTSGenerationError):
        generate_scene_audio(tmp_path, make_plan(backend="unsupported"), make_state(), retries=1)
