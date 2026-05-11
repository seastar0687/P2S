from pathlib import Path

from p2s_core.models import SceneAssetPlan
from p2s_core.models.asset_plan import RenderPlan, TTSPlan, VisualAssetPlan
from p2s_core.services.visual_placeholder import generate_scene_visual


def make_plan(asset_source: str = "text_card", **visual_overrides) -> SceneAssetPlan:
    visual = {
        "enabled": True,
        "asset_source": asset_source,
        "asset_type_hint": "none",
        "fallback_chain": ["text_card", "static_background"],
        "selected_figure_ids": [],
        "output_placeholder": "assets/scene_001_textcard.png",
    }
    visual.update(visual_overrides)
    return SceneAssetPlan(
        scene_id="scene_001",
        purpose="test",
        claim_ids=[],
        voice_text="voice",
        subtitle_text="A compact subtitle.",
        presenter_mode="off_screen",
        visual_focus="text_card",
        asset_policy="optional",
        asset_type_hint="none",
        background_mode="static_clean",
        tts_plan=TTSPlan(text="voice", output_path="audio/scene_001.wav"),
        visual_plan=VisualAssetPlan(**visual),
        render_plan=RenderPlan(template_hint="text_card", layout_mode="text_card", resolution="320x480", background_mode="static_clean", output_segment_placeholder="segments/scene_001.mp4"),
    )


def test_text_card_png_is_generated(tmp_path: Path):
    visual = generate_scene_visual(tmp_path, make_plan())

    assert visual.output_path == "assets/scene_001_textcard.png"
    assert (tmp_path / visual.output_path).exists()
    assert visual.width == 320
    assert visual.height == 480


def test_static_background_png_is_generated(tmp_path: Path):
    visual = generate_scene_visual(tmp_path, make_plan("none", output_placeholder="assets/scene_001_bg.png"))

    assert (tmp_path / visual.output_path).exists()


def test_paper_figure_with_image_path_uses_canvas(tmp_path: Path):
    source = tmp_path / "figures" / "fig_001.png"
    source.parent.mkdir()
    generate_scene_visual(tmp_path, make_plan()).model_dump()
    (tmp_path / "assets" / "scene_001_textcard.png").replace(source)
    plan = make_plan(
        "paper_figure",
        selected_figure_ids=["fig_001"],
        output_placeholder="assets/scene_001_figure.png",
    )
    visual = generate_scene_visual(tmp_path, plan, [{"figure_id": "fig_001", "image_path": "figures/fig_001.png"}])

    assert visual.asset_source == "paper_figure"
    assert visual.source_path == "figures/fig_001.png"
    assert (tmp_path / visual.output_path).exists()


def test_caption_without_image_falls_back_to_text_card(tmp_path: Path):
    plan = make_plan("paper_figure", selected_figure_ids=["fig_001"])
    visual = generate_scene_visual(tmp_path, plan, [{"figure_id": "fig_001", "caption": "Figure 1."}])

    assert visual.generation_status == "fallback"
    assert visual.asset_source == "text_card"


def test_unsupported_prompt_sources_fall_back(tmp_path: Path):
    visual = generate_scene_visual(tmp_path, make_plan("diagram_prompt"))

    assert visual.generation_status == "fallback"
    assert visual.asset_source == "text_card"
