from p2s_core.models import GeneratedVisual
from p2s_core.services.fallback_quality import build_fallback_quality_report
from tests.test_mvp2c_thin_pipeline import make_scene
from p2s_core.models import AssetPlanBundle, AssetPlanQualityReport


def _bundle(sources):
    plans = []
    for index, source in enumerate(sources, start=1):
        plan = make_scene(f"scene_{index:03d}")
        plan.visual_plan.asset_source = source
        plan.visual_plan.selected_figure_ids = ["fig_001"] if source == "paper_figure" else []
        plans.append(plan)
    return AssetPlanBundle(
        project_id="p",
        scene_source="scenes.json",
        plans=plans,
        quality_report=AssetPlanQualityReport(
            scene_count=len(plans),
            tts_enabled_count=len(plans),
            visual_enabled_count=len(plans),
            required_asset_count=0,
            optional_asset_count=len(plans),
            no_asset_count=0,
            paper_figure_count=0,
            diagram_prompt_count=0,
            metaphor_prompt_count=0,
            text_card_count=0,
            static_background_count=0,
        ),
        created_at="now",
    )


def test_fallback_ratio_levels_and_reason_counts():
    bundle = _bundle(["paper_figure", "diagram_prompt", "text_card"])
    visuals = [
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="a.png", generation_status="fallback", created_at="now"),
        GeneratedVisual(scene_id="scene_002", asset_source="text_card", output_path="b.png", generation_status="fallback", created_at="now"),
        GeneratedVisual(scene_id="scene_003", asset_source="text_card", output_path="c.png", created_at="now"),
    ]

    report = build_fallback_quality_report(bundle, visuals, figures=[])

    assert report.quality_level == "degraded"
    assert report.fallback_by_reason["no_figure_metadata"] == 1
    assert report.fallback_by_reason["diagram_prompt_fallback"] == 1


def test_fallback_ratio_good_acceptable_and_minimal_levels():
    assert build_fallback_quality_report(_bundle(["text_card"]), [
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="a.png", created_at="now"),
    ]).quality_level == "good"

    acceptable = build_fallback_quality_report(_bundle(["diagram_prompt", "text_card", "text_card", "text_card"]), [
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="a.png", generation_status="fallback", created_at="now"),
        GeneratedVisual(scene_id="scene_002", asset_source="text_card", output_path="b.png", created_at="now"),
        GeneratedVisual(scene_id="scene_003", asset_source="text_card", output_path="c.png", created_at="now"),
        GeneratedVisual(scene_id="scene_004", asset_source="text_card", output_path="d.png", created_at="now"),
    ])
    assert acceptable.quality_level == "acceptable"

    minimal = build_fallback_quality_report(_bundle(["diagram_prompt", "chart_prompt"]), [
        GeneratedVisual(scene_id="scene_001", asset_source="text_card", output_path="a.png", generation_status="fallback", created_at="now"),
        GeneratedVisual(scene_id="scene_002", asset_source="text_card", output_path="b.png", generation_status="fallback", created_at="now"),
    ])
    assert minimal.quality_level == "minimal"
