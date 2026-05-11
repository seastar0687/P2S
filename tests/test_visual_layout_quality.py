from pathlib import Path

from PIL import Image

from p2s_core.models import GeneratedVisual
from p2s_core.services.visual_layout_quality import check_visual_layout_quality
from tests.test_mvp2c_thin_pipeline import make_scene


def test_valid_png_passes(tmp_path: Path):
    path = tmp_path / "assets" / "s.png"
    path.parent.mkdir()
    Image.new("RGB", (320, 480), "white").save(path)

    result = check_visual_layout_quality(
        tmp_path,
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="assets/s.png", width=320, height=480, created_at="now"),
        make_scene(),
    )

    assert result.pass_gate is True


def test_missing_unreadable_and_resolution_mismatch(tmp_path: Path):
    plan = make_scene()
    unreadable = tmp_path / "assets" / "bad.png"
    unreadable.parent.mkdir()
    unreadable.write_text("not png", encoding="utf-8")

    missing_result = check_visual_layout_quality(
        tmp_path,
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="assets/missing.png", created_at="now"),
        plan,
    )
    bad_result = check_visual_layout_quality(
        tmp_path,
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="assets/bad.png", created_at="now"),
        plan,
    )
    assert missing_result.pass_gate is False
    assert bad_result.pass_gate is False


def test_empty_text_and_tiny_figure_warn(tmp_path: Path):
    path = tmp_path / "assets" / "figure.png"
    path.parent.mkdir()
    Image.new("RGB", (320, 480), "white").save(path)
    plan = make_scene()
    plan.subtitle_text = ""

    result = check_visual_layout_quality(
        tmp_path,
        GeneratedVisual(scene_id="scene_001", asset_source="paper_figure", output_path="assets/figure.png", source_path=None, created_at="now"),
        plan,
    )

    assert any("empty" in warning for warning in result.warnings)
    assert result.figure_size_ratio == 0.0
