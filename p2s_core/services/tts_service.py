from __future__ import annotations

import asyncio
import math
import wave
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import GeneratedAudio, ProjectState, SceneAssetPlan


class TTSGenerationError(RuntimeError):
    """Raised when MVP2C-thin cannot generate required scene audio."""


def generate_scene_audio(
    run_dir: Path,
    plan: SceneAssetPlan,
    state: ProjectState,
    *,
    backend: str | None = None,
    retries: int = 2,
    duration_reader= None,
) -> GeneratedAudio:
    backend = backend or plan.tts_plan.backend or "edge_tts"
    output_path = Path(plan.tts_plan.output_path or f"audio/{plan.scene_id}.wav")
    if output_path.is_absolute():
        raise TTSGenerationError("audio output path must be relative to run_dir")
    if output_path.parts[0] != "audio":
        output_path = Path("audio") / output_path.name
    absolute_output = run_dir / output_path
    absolute_output.parent.mkdir(parents=True, exist_ok=True)

    voice = resolve_voice(plan, state)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if backend == "fake":
                write_silent_wav(absolute_output, duration_sec=max(0.5, plan.tts_plan.estimated_duration_sec or 0.75))
            elif backend == "edge_tts":
                asyncio.run(_edge_tts_to_wav(plan.tts_plan.text, voice, plan.tts_plan.speed, absolute_output))
            else:
                raise TTSGenerationError(f"Unsupported TTS backend: {backend}")
            break
        except Exception as exc:  # noqa: BLE001 - surface backend failures with retries.
            last_error = exc
            if attempt >= retries:
                raise TTSGenerationError(f"TTS generation failed for {plan.scene_id}: {exc}") from exc

    reader = duration_reader or read_wav_duration
    duration = reader(absolute_output)
    warnings: list[str] = []
    if duration is None:
        duration = plan.tts_plan.estimated_duration_sec
        warnings.append("Could not read wav duration; used estimated duration fallback.")

    return GeneratedAudio(
        scene_id=plan.scene_id,
        text=plan.tts_plan.text,
        backend=backend,
        voice=voice,
        speed=plan.tts_plan.speed,
        output_path=output_path.as_posix(),
        duration_sec=duration,
        placeholder=backend == "fake",
        generation_status="done",
        warnings=warnings,
        created_at=_utc_now(),
    )


def resolve_voice(plan: SceneAssetPlan, state: ProjectState, config: dict | None = None) -> str:
    config = config or {}
    voice_profile = state.persona.get("voice") or {}
    return (
        plan.tts_plan.voice
        or voice_profile.get("default_voice")
        or config.get("tts", {}).get("default_voice")
        or "zh-TW-HsiaoChenNeural"
    )


def write_silent_wav(path: Path, *, duration_sec: float = 0.75, sample_rate: int = 16000) -> None:
    frames = max(1, math.ceil(duration_sec * sample_rate))
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\x00\x00" * frames)


def read_wav_duration(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as audio:
            frames = audio.getnframes()
            rate = audio.getframerate()
            if rate <= 0:
                return None
            return round(frames / float(rate), 3)
    except (wave.Error, OSError, EOFError):
        return None


async def _edge_tts_to_wav(text: str, voice: str, speed: float, output_path: Path) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise TTSGenerationError("edge-tts is not installed") from exc

    rate = _edge_rate(speed)
    temp_mp3 = output_path.with_suffix(".mp3")
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(temp_mp3))
    if output_path.suffix.lower() == ".mp3":
        return
    from p2s_core.services.segment_composer import run_command

    run_command(["ffmpeg", "-y", "-i", str(temp_mp3), str(output_path)])
    temp_mp3.unlink(missing_ok=True)


def _edge_rate(speed: float) -> str:
    if abs(speed - 1.0) < 0.01:
        return "+0%"
    percent = int(round((speed - 1.0) * 100))
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent}%"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
