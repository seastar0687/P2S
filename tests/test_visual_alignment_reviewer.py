from pathlib import Path

from p2s_core.models import (
    AssetPlanBundle,
    AssetPlanQualityReport,
    GeneratedVisual,
    RenderPlan,
    SceneAssetPlan,
    TTSPlan,
    VisualAssetPlan,
)
from p2s_core.reviewers.visual_alignment import VisualAlignmentReviewer


def _plan(asset_source="text_card", asset_type_hint="none", policy="optional", selected=None):
    return AssetPlanBundle(
        project_id="p",
        scene_source="scenes.json",
        plans=[
            SceneAssetPlan(
                scene_id="scene_001",
                purpose="method",
                claim_ids=[],
                voice_text="voice",
                subtitle_text="subtitle",
                presenter_mode="off_screen",
                visual_focus="text_card",
                asset_policy=policy,
                asset_type_hint=asset_type_hint,
                background_mode="static_clean",
                tts_plan=TTSPlan(text="voice", output_path="audio/scene_001.wav"),
                visual_plan=VisualAssetPlan(
                    enabled=True,
                    asset_source=asset_source,
                    asset_type_hint=asset_type_hint,
                    selected_figure_ids=selected or [],
                    fallback_chain=["text_card"],
                    output_placeholder="assets/scene_001.png",
                ),
                render_plan=RenderPlan(
                    template_hint="text_card",
                    layout_mode="text_card",
                    background_mode="static_clean",
                    output_segment_placeholder="segments/scene_001.mp4",
                ),
            )
        ],
        quality_report=AssetPlanQualityReport(
            scene_count=1,
            tts_enabled_count=1,
            visual_enabled_count=1,
            required_asset_count=1 if policy == "required" else 0,
            optional_asset_count=1 if policy == "optional" else 0,
            no_asset_count=0,
            paper_figure_count=1 if asset_source == "paper_figure" else 0,
            diagram_prompt_count=0,
            metaphor_prompt_count=0,
            text_card_count=1 if asset_source == "text_card" else 0,
            static_background_count=0,
        ),
        created_at="2026-05-12T00:00:00Z",
    )


def _visual(source="text_card"):
    return GeneratedVisual(
        scene_id="scene_001",
        asset_source=source,
        output_path="assets/scene_001.png",
        created_at="2026-05-12T00:00:00Z",
    )


def test_existing_visual_metadata_passes(tmp_path: Path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "scene_001.png").write_bytes(b"png")
    summary = VisualAlignmentReviewer().review(tmp_path, _plan(), visual_metadata=[_visual()], figures=[])
    assert summary.pass_gate is True


def test_missing_required_visual_artifact_blocks(tmp_path: Path):
    summary = VisualAlignmentReviewer().review(tmp_path, _plan(policy="required"), visual_metadata=[], figures=[])
    assert summary.pass_gate is False


def test_paper_figure_fallback_to_text_card_warns(tmp_path: Path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "scene_001.png").write_bytes(b"png")
    summary = VisualAlignmentReviewer().review(
        tmp_path,
        _plan(asset_source="text_card", asset_type_hint="paper_figure"),
        visual_metadata=[_visual()],
        figures=[],
    )
    assert summary.pass_gate is True
    assert any(f.category == "fallback_quality" for f in summary.findings)


def test_missing_selected_figure_id_warns_when_artifact_exists(tmp_path: Path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "scene_001.png").write_bytes(b"png")
    summary = VisualAlignmentReviewer().review(
        tmp_path,
        _plan(asset_source="paper_figure", asset_type_hint="paper_figure", selected=["fig_missing"]),
        visual_metadata=[_visual("paper_figure")],
        figures=[{"figure_id": "fig_001"}],
    )
    assert summary.pass_gate is True
    assert any(f.category == "visual_mismatch" for f in summary.findings)


def test_diagram_fallback_warns(tmp_path: Path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "scene_001.png").write_bytes(b"png")
    summary = VisualAlignmentReviewer().review(
        tmp_path,
        _plan(asset_source="text_card", asset_type_hint="diagram"),
        visual_metadata=[_visual()],
        figures=[],
    )
    assert summary.pass_gate is True
    assert any(f.category == "fallback_quality" for f in summary.findings)
