from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import GeneratedAudio, GeneratedSegment, GeneratedVisual, SceneAssetPlan


class SegmentCompositionError(RuntimeError):
    """Raised when ffmpeg cannot compose a scene segment."""


def compose_segment(
    run_dir: Path,
    plan: SceneAssetPlan,
    audio: GeneratedAudio,
    visual: GeneratedVisual,
    *,
    runner=None,
) -> GeneratedSegment:
    output_path = Path(plan.render_plan.output_segment_placeholder or f"segments/{plan.scene_id}.mp4")
    if output_path.is_absolute():
        raise SegmentCompositionError("segment output path must be relative to run_dir")
    if output_path.parts[0] != "segments":
        output_path = Path("segments") / output_path.name
    absolute_output = run_dir / output_path
    absolute_output.parent.mkdir(parents=True, exist_ok=True)

    width, height = visual.width, visual.height
    fps = plan.render_plan.fps or 30
    command = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(run_dir / visual.output_path),
        "-i",
        str(run_dir / audio.output_path),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(absolute_output),
    ]
    run_command(command, runner=runner)
    if not absolute_output.exists() or absolute_output.stat().st_size == 0:
        raise SegmentCompositionError(f"segment output missing or empty: {absolute_output}")
    return GeneratedSegment(
        scene_id=plan.scene_id,
        audio_path=audio.output_path,
        visual_path=visual.output_path,
        output_path=output_path.as_posix(),
        duration_sec=audio.duration_sec,
        ffmpeg_command=command,
        generation_status="done",
        created_at=_utc_now(),
    )


def run_command(command: list[str], *, runner=None) -> subprocess.CompletedProcess:
    runner = runner or subprocess.run
    completed = runner(command, capture_output=True, text=True)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() if completed.stderr else ""
        raise SegmentCompositionError(f"command failed ({completed.returncode}): {' '.join(command)}\n{stderr}")
    return completed


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
