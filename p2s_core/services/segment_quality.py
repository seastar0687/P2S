from __future__ import annotations

from pathlib import Path

from p2s_core.models import GeneratedAudio, GeneratedSegment, SegmentQualityResult
from p2s_core.services.ffprobe_utils import duration_from_probe, probe_media


def check_segment_quality(
    run_dir: Path,
    segment: GeneratedSegment,
    audio: GeneratedAudio | None = None,
    *,
    runner=None,
) -> SegmentQualityResult:
    path = run_dir / segment.output_path
    warnings: list[str] = []
    exists = path.exists()
    file_size = path.stat().st_size if exists else None
    pass_gate = True

    if not exists:
        return SegmentQualityResult(
            scene_id=segment.scene_id,
            segment_path=segment.output_path,
            exists=False,
            pass_gate=False,
            warnings=["segment file is missing"],
        )
    if file_size == 0:
        pass_gate = False
        warnings.append("segment file is empty")

    probe = probe_media(path, runner=runner)
    duration = duration_from_probe(probe)
    if duration is None:
        warnings.append("ffprobe unavailable or segment duration unreadable")

    audio_duration = audio.duration_sec if audio else None
    duration_delta = None
    if duration is not None and audio_duration is not None:
        duration_delta = abs(duration - audio_duration)
        if duration_delta > 1.0:
            warnings.append(f"segment/audio duration delta is high: {duration_delta:.2f}s")

    return SegmentQualityResult(
        scene_id=segment.scene_id,
        segment_path=segment.output_path,
        exists=True,
        file_size_bytes=file_size,
        duration_sec=duration,
        audio_duration_sec=audio_duration,
        duration_delta_sec=duration_delta,
        ffprobe_readable=duration is not None,
        pass_gate=pass_gate,
        warnings=warnings,
    )
