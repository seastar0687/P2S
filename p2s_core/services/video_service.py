from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import CompositionResult, GeneratedSegment
from p2s_core.services.segment_composer import run_command


class VideoCompositionError(RuntimeError):
    """Raised when MVP2C-thin cannot create final/output.mp4."""


def compose_final_video(
    run_dir: Path,
    project_id: str,
    segments: list[GeneratedSegment],
    *,
    runner=None,
) -> CompositionResult:
    if not segments:
        raise VideoCompositionError("no segments available for composition")
    final_dir = run_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path("final/output.mp4")
    concat_file = final_dir / "segments.txt"
    lines = []
    for segment in segments:
        segment_path = run_dir / segment.output_path
        if not segment_path.exists():
            raise VideoCompositionError(f"missing segment: {segment.output_path}")
        lines.append(f"file '{segment_path.resolve().as_posix()}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(run_dir / output_path),
    ]
    try:
        run_command(command, runner=runner)
    except Exception as exc:
        raise VideoCompositionError(str(exc)) from exc
    absolute_output = run_dir / output_path
    if not absolute_output.exists() or absolute_output.stat().st_size == 0:
        raise VideoCompositionError(f"final output missing or empty: {absolute_output}")
    return CompositionResult(
        project_id=project_id,
        segment_paths=[segment.output_path for segment in segments],
        output_path=output_path.as_posix(),
        duration_sec=probe_duration(absolute_output),
        ffmpeg_command=command,
        generation_status="done",
        warnings=[],
        created_at=_utc_now(),
    )


def probe_duration(path: Path) -> float | None:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            return None
        data = json.loads(completed.stdout)
        return round(float(data["format"]["duration"]), 3)
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
