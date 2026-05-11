from __future__ import annotations

from pathlib import Path

from p2s_core.models import AudioQualityResult, GeneratedAudio
from p2s_core.services.tts_service import read_wav_duration


def check_audio_quality(run_dir: Path, audio: GeneratedAudio) -> AudioQualityResult:
    path = run_dir / audio.output_path
    warnings: list[str] = []
    exists = path.exists()
    size = path.stat().st_size if exists else None
    duration = read_wav_duration(path) if exists and size else None
    pass_gate = True
    if not exists:
        warnings.append("audio file is missing")
        pass_gate = False
    elif not size:
        warnings.append("audio file is empty")
        pass_gate = False
    elif duration is None:
        warnings.append("audio duration is not readable")
        pass_gate = False
    elif duration <= 0.3:
        warnings.append("audio duration is too short")
        pass_gate = False
    warnings.append("loudness unavailable in report-only HARDEN-3 baseline")
    return AudioQualityResult(
        scene_id=audio.scene_id,
        audio_path=audio.output_path,
        exists=exists,
        file_size_bytes=size,
        duration_sec=duration,
        loudness_lufs=None,
        peak_dbfs=None,
        silence_ratio=None,
        pass_gate=pass_gate,
        warnings=warnings,
    )
