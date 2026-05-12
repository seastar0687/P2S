import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from p2s_core import cli as cli_module
from p2s_core.models import (
    AssetPlanBundle,
    AssetPlanQualityReport,
    PaperClaim,
    ProjectSource,
    ProjectState,
    RenderPlan,
    SceneAssetPlan,
    SceneDraft,
    ScenesBundle,
    StageState,
    TTSPlan,
    VisualAssetPlan,
    default_stages,
)
from p2s_core.models.common import EvidenceSpan
from p2s_core.pipelines import PaperSummaryPipeline
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "mvp3_final_review"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def _claim() -> PaperClaim:
    return PaperClaim(
        claim_id="claim_001",
        claim_text="Teacher models can transmit traits through numbers.",
        claim_type="method",
        source_section="method",
        evidence_spans=[
            EvidenceSpan(
                section="method",
                text="Teacher models can transmit traits through numbers.",
                confidence="direct",
            )
        ],
        certainty="explicit",
        importance=4,
    )


def _scene() -> SceneDraft:
    return SceneDraft(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="教師模型可能透過數字傳遞特徵。",
        subtitle_text="數字可能傳遞特徵。",
        target_duration_sec=5,
        presenter_mode="off_screen",
        visual_focus="text_card",
        asset_policy="optional",
        asset_type_hint="none",
    )


def _asset_plan(project_id: str) -> AssetPlanBundle:
    scene = _scene()
    return AssetPlanBundle(
        project_id=project_id,
        scene_source="scenes.json",
        plans=[
            SceneAssetPlan(
                scene_id=scene.scene_id,
                purpose=scene.purpose,
                claim_ids=scene.claim_ids,
                voice_text=scene.voice_text,
                subtitle_text=scene.subtitle_text,
                presenter_mode=scene.presenter_mode,
                visual_focus=scene.visual_focus,
                asset_policy=scene.asset_policy,
                asset_type_hint=scene.asset_type_hint,
                background_mode=scene.background_mode,
                tts_plan=TTSPlan(text=scene.voice_text, output_path="audio/scene_001.wav"),
                visual_plan=VisualAssetPlan(
                    enabled=True,
                    asset_source="text_card",
                    asset_type_hint="none",
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
            required_asset_count=0,
            optional_asset_count=1,
            no_asset_count=0,
            paper_figure_count=0,
            diagram_prompt_count=0,
            metaphor_prompt_count=0,
            text_card_count=1,
            static_background_count=0,
        ),
        created_at="2026-05-12T00:00:00Z",
    )


def write_project(runs_dir: Path, project_id: str = "mvp3_project") -> Path:
    run_dir = runs_dir / project_id
    run_dir.mkdir(parents=True)
    stages = default_stages()
    stages["composition"] = StageState(status="done")
    state = ProjectState(
        project_id=project_id,
        created_at="2026-05-12T00:00:00Z",
        source=ProjectSource(pdf_path=str(run_dir / "source.pdf")),
        persona={"persona_id": "seina"},
        style={"style_id": "rigorous_science_short"},
        claims=[_claim()],
        stages=stages,
    )
    state.extraction.text_md = "extracted_text.md"
    (run_dir / "source.pdf").write_text("pdf", encoding="utf-8")
    (run_dir / "claims.json").write_text(f"[{_claim().model_dump_json()}]", encoding="utf-8")
    (run_dir / "extracted_text.md").write_text(
        "Teacher models can transmit traits through numbers.",
        encoding="utf-8",
    )
    (run_dir / "scenes.json").write_text(
        ScenesBundle(project_id=project_id, scenes=[_scene()], created_at="2026-05-12T00:00:00Z").model_dump_json(indent=2),
        encoding="utf-8",
    )
    (run_dir / "asset_plan.json").write_text(_asset_plan(project_id).model_dump_json(indent=2), encoding="utf-8")
    (run_dir / "assets").mkdir()
    (run_dir / "assets" / "scene_001.png").write_bytes(b"png")
    (run_dir / "final").mkdir()
    (run_dir / "final" / "output.mp4").write_bytes(b"mp4")
    persistence.save_state(state)
    return run_dir


def test_final_review_stage_writes_outputs_and_stage_done(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    run_dir = write_project(runs_dir)

    state = PaperSummaryPipeline().run_stage("mvp3_project", "final_review")

    assert state.stages["final_review"].status == "done"
    assert (run_dir / "reviews" / "final_review_rev001.json").exists()
    assert (run_dir / "reviews" / "final_gate_decision_rev001.json").exists()
    gate = json.loads((run_dir / "reviews" / "final_gate_decision_rev001.json").read_text(encoding="utf-8"))
    assert gate["status"] == "pass"


def test_final_review_revision_numbering_writes_rev002(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    run_dir = write_project(runs_dir, "mvp3_rev")
    pipeline = PaperSummaryPipeline()

    pipeline.run_stage("mvp3_rev", "final_review")
    pipeline.run_stage("mvp3_rev", "final_review", force=True)

    assert (run_dir / "reviews" / "final_review_rev001.json").exists()
    assert (run_dir / "reviews" / "final_review_rev002.json").exists()


def test_final_review_missing_final_video_fails(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    run_dir = write_project(runs_dir, "missing_video")
    (run_dir / "final" / "output.mp4").unlink()

    with pytest.raises(FileNotFoundError):
        PaperSummaryPipeline().run_stage("missing_video", "final_review")


def test_active_scene_source_fallback_warning(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    run_dir = write_project(runs_dir, "scene_fallback")
    state = persistence.load_state("scene_fallback")
    state.active_scene_source = "scenes_rewritten.json"
    persistence.save_state(state)

    PaperSummaryPipeline().run_stage("scene_fallback", "final_review")
    bundle = json.loads((run_dir / "reviews" / "final_review_rev001.json").read_text(encoding="utf-8"))

    assert any("fell back" in warning["message"] for warning in bundle["warnings"])


def test_cli_run_final_review_prints_summary(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    write_project(runs_dir, "mvp3_cli")

    result = CliRunner().invoke(cli_module.cli, ["run", "--stage", "final_review", "--project", "mvp3_cli"])

    assert result.exit_code == 0
    assert "gate_status: pass" in result.output
    assert "blocking_issues: 0" in result.output
