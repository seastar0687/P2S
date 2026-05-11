from __future__ import annotations

from pathlib import Path

from p2s_core.models import CompositionQualityResult, CompositionResult, SegmentQualityResult
from p2s_core.services.ffprobe_utils import duration_from_probe, pixel_format, probe_media, stream_codec


def check_composition_quality(
    run_dir: Path,
    project_id: str,
    composition: CompositionResult,
    segment_results: list[SegmentQualityResult],
    *,
    runner=None,
) -> CompositionQualityResult:
    output_path = composition.output_path or "final/output.mp4"
    path = run_dir / output_path
    warnings: list[str] = []
    exists = path.exists()
    file_size = path.stat().st_size if exists else None
    pass_gate = True

    if not exists:
        return CompositionQualityResult(
            project_id=project_id,
            output_path=output_path,
            exists=False,
            pass_gate=False,
            warnings=["final MP4 is missing"],
        )
    if file_size == 0:
        pass_gate = False
        warnings.append("final MP4 is empty")

    probe = probe_media(path, runner=runner)
    duration = duration_from_probe(probe)
    ffprobe_readable = duration is not None
    if duration is None:
        warnings.append("ffprobe unavailable or final duration unreadable")

    readable_segment_durations = [
        item.duration_sec for item in segment_results if item.duration_sec is not None
    ]
    expected_duration = (
        sum(readable_segment_durations)
        if len(readable_segment_durations) == len(segment_results) and segment_results
        else None
    )
    duration_delta = None
    if duration is not None and expected_duration is not None:
        duration_delta = abs(duration - expected_duration)
        if duration_delta > 1.0:
            warnings.append(f"final/segments duration delta is high: {duration_delta:.2f}s")
    if probe is not None and duration is None and expected_duration is not None:
        pass_gate = False
        warnings.append("final duration unreadable even though ffprobe returned metadata")

    codec_video = stream_codec(probe, "video") if probe else None
    codec_audio = stream_codec(probe, "audio") if probe else None
    pix_fmt = pixel_format(probe) if probe else None
    if probe and not codec_video:
        warnings.append("video codec metadata unavailable")
    if probe and not codec_audio:
        warnings.append("audio codec metadata unavailable")
    if codec_video and codec_video != "h264":
        warnings.append(f"video codec may have compatibility risk: {codec_video}")
    if pix_fmt and pix_fmt != "yuv420p":
        warnings.append(f"pixel format may have compatibility risk: {pix_fmt}")

    return CompositionQualityResult(
        project_id=project_id,
        output_path=output_path,
        exists=True,
        file_size_bytes=file_size,
        duration_sec=duration,
        expected_duration_sec=expected_duration,
        duration_delta_sec=duration_delta,
        ffprobe_readable=ffprobe_readable,
        codec_video=codec_video,
        codec_audio=codec_audio,
        pixel_format=pix_fmt,
        pass_gate=pass_gate,
        warnings=warnings,
    )
