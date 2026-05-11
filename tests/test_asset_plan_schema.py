import pytest
from pydantic import ValidationError

from p2s_core.models import (
    AssetPlanBundle,
    AssetPlanQualityReport,
    RenderPlan,
    SceneAssetPlan,
    TTSPlan,
    VisualAssetPlan,
)


def test_asset_plan_bundle_roundtrip():
    bundle = AssetPlanBundle(
        project_id="schema_project",
        scene_source="scenes.json",
        created_at="2026-05-08T00:00:00Z",
        plans=[
            SceneAssetPlan(
                scene_id="scene_001",
                purpose="hook",
                claim_ids=["claim_001"],
                voice_text="Hello",
                subtitle_text="Hello",
                presenter_mode="speaking_on_camera",
                visual_focus="presenter",
                asset_policy="optional",
                asset_type_hint="none",
                background_mode="static_clean",
                tts_plan=TTSPlan(text="Hello", output_path="audio/scene_001.wav"),
                visual_plan=VisualAssetPlan(
                    enabled=False,
                    asset_source="none",
                    asset_type_hint="none",
                    fallback_chain=["text_card", "static_background"],
                ),
                render_plan=RenderPlan(
                    template_hint="presenter_only_clean",
                    layout_mode="presenter_only",
                    background_mode="static_clean",
                    output_segment_placeholder="segments/scene_001.mp4",
                ),
            )
        ],
        quality_report=AssetPlanQualityReport(
            scene_count=1,
            tts_enabled_count=1,
            visual_enabled_count=0,
            required_asset_count=0,
            optional_asset_count=1,
            no_asset_count=0,
            paper_figure_count=0,
            diagram_prompt_count=0,
            metaphor_prompt_count=0,
            text_card_count=0,
            static_background_count=0,
        ),
    )

    loaded = AssetPlanBundle.model_validate_json(bundle.model_dump_json())

    assert loaded.version == "mvp2b_v1"
    assert loaded.plans[0].tts_plan.placeholder_only is True
    assert loaded.quality_report.optional_asset_count == 1
    assert loaded.quality_report.visual_enabled_count == 0


def test_visual_asset_plan_rejects_unknown_source():
    with pytest.raises(ValidationError):
        VisualAssetPlan(
            enabled=True,
            asset_source="html_diagram",
            asset_type_hint="diagram",
            fallback_chain=["html_diagram"],
        )


def test_render_plan_rejects_unknown_layout_mode():
    with pytest.raises(ValidationError):
        RenderPlan(
            template_hint="bad",
            layout_mode="floating_panel",
            background_mode="static_clean",
            output_segment_placeholder="segments/scene_001.mp4",
        )


def test_quality_report_keeps_policy_counts_independent_from_resolved_visuals():
    report = AssetPlanQualityReport(
        scene_count=2,
        tts_enabled_count=2,
        visual_enabled_count=1,
        required_asset_count=0,
        optional_asset_count=1,
        no_asset_count=1,
        paper_figure_count=0,
        diagram_prompt_count=0,
        metaphor_prompt_count=0,
        text_card_count=1,
        static_background_count=0,
    )

    assert report.no_asset_count == 1
    assert report.optional_asset_count == 1
    assert report.visual_enabled_count == 1
