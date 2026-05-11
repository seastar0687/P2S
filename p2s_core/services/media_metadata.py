from __future__ import annotations

from pathlib import Path

from p2s_core.models import CompositionResult, GeneratedAudio, GeneratedSegment, GeneratedVisual


def write_media_metadata(
    run_dir: Path,
    *,
    audio: list[GeneratedAudio] | None = None,
    visuals: list[GeneratedVisual] | None = None,
    segments: list[GeneratedSegment] | None = None,
    composition: CompositionResult | None = None,
) -> dict[str, str]:
    metadata_dir = run_dir / "media_metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    if audio is not None:
        path = metadata_dir / "audio.json"
        path.write_text("[" + ",\n".join(item.model_dump_json(indent=2) for item in audio) + "]", encoding="utf-8")
        paths["audio_manifest"] = "media_metadata/audio.json"
    if visuals is not None:
        path = metadata_dir / "visuals.json"
        path.write_text("[" + ",\n".join(item.model_dump_json(indent=2) for item in visuals) + "]", encoding="utf-8")
        paths["visual_manifest"] = "media_metadata/visuals.json"
    if segments is not None:
        path = metadata_dir / "segments.json"
        path.write_text("[" + ",\n".join(item.model_dump_json(indent=2) for item in segments) + "]", encoding="utf-8")
        paths["segment_manifest"] = "media_metadata/segments.json"
    if composition is not None:
        path = metadata_dir / "composition.json"
        path.write_text(composition.model_dump_json(indent=2), encoding="utf-8")
        paths["composition_manifest"] = "media_metadata/composition.json"
    return paths
