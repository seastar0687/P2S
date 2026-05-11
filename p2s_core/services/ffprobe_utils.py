from __future__ import annotations

import json
import subprocess
from pathlib import Path


def probe_media(path: Path, *, runner=None) -> dict | None:
    runner = runner or subprocess.run
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,codec_name,pix_fmt",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = runner(command, capture_output=True, text=True)
        if completed.returncode != 0:
            return None
        return json.loads(completed.stdout)
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


def duration_from_probe(data: dict | None) -> float | None:
    if not data:
        return None
    try:
        return round(float(data["format"]["duration"]), 3)
    except (KeyError, TypeError, ValueError):
        return None


def stream_codec(data: dict | None, codec_type: str) -> str | None:
    if not data:
        return None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == codec_type:
            return stream.get("codec_name")
    return None


def pixel_format(data: dict | None) -> str | None:
    if not data:
        return None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream.get("pix_fmt")
    return None
