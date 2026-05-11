from pathlib import Path
import subprocess

import pytest

from p2s_core.models import (
    AssetPlanBundle,
    AssetPlanQualityReport,
    ProjectSource,
    ProjectState,
    RenderPlan,
    SceneAssetPlan,
    TTSPlan,
    VisualAssetPlan,
    default_stages,
)
from p2s_core.pipelines import PaperSummaryPipeline
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "mvp2c_thin"


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_state(project_id: str) -> ProjectState:
    stages = default_stages()
    stages["asset_preparation"].status = "done"
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-11T00:00:00Z",
        source=ProjectSource(pdf_path=f"runs/{project_id}/source.pdf"),
        persona={"persona_id": "seina", "voice": {"default_voice": "persona_voice"}},
        style={"style_id": "rigorous_science_short"},
        stages=stages,
    )


def make_scene(scene_id: str = "scene_001") -> SceneAssetPlan:
    return SceneAssetPlan(
        scene_id=scene_id,
        purpose="test",
        claim_ids=[],
        voice_text="voice",
        subtitle_text="subtitle",
        presenter_mode="off_screen",
        visual_focus="text_card",
        asset_policy="optional",
        asset_type_hint="none",
        background_mode="static_clean",
        tts_plan=TTSPlan(
            backend="fake",
            text=f"Audio text for {scene_id}.",
            output_path=f"audio/{scene_id}.wav",
            estimated_duration_sec=0.6,
        ),
        visual_plan=VisualAssetPlan(
            enabled=True,
            asset_source="text_card",
            asset_type_hint="none",
            fallback_chain=["text_card", "static_background"],
            output_placeholder=f"assets/{scene_id}_textcard.png",
        ),
        render_plan=RenderPlan(
            template_hint="text_card",
            layout_mode="text_card",
            resolution="320x480",
            background_mode="static_clean",
            output_segment_placeholder=f"segments/{scene_id}.mp4",
        ),
    )


def write_project(runs_dir: Path, project_id: str = "mvp2c_project") -> Path:
    run_dir = runs_dir / project_id
    run_dir.mkdir(parents=True)
    persistence.save_state(make_state(project_id))
    bundle = AssetPlanBundle(
        project_id=project_id,
        scene_source="scenes.json",
        plans=[make_scene("scene_001"), make_scene("scene_002")],
        quality_report=AssetPlanQualityReport(
            scene_count=2,
            tts_enabled_count=2,
            visual_enabled_count=2,
            required_asset_count=0,
            optional_asset_count=2,
            no_asset_count=0,
            paper_figure_count=0,
            diagram_prompt_count=0,
            metaphor_prompt_count=0,
            text_card_count=2,
            static_background_count=0,
        ),
        created_at="2026-05-11T00:00:00Z",
    )
    (run_dir / "asset_plan.json").write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    return run_dir


def fake_subprocess_run(command, capture_output=True, text=True, **kwargs):
    if command[0] == "git":
        if "rev-parse" in command and "--abbrev-ref" in command:
            return subprocess.CompletedProcess(command, 0, "test-branch\n", "")
        if "rev-parse" in command:
            return subprocess.CompletedProcess(command, 0, "abcdef0\n", "")
        if "status" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
    if command[0] == "ffprobe":
        return subprocess.CompletedProcess(command, 0, '{"format":{"duration":"1.2"}}', "")
    output = Path(command[-1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"mp4")
    return subprocess.CompletedProcess(command, 0, "", "")


def test_pipeline_asset_generation_and_composition(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    monkeypatch.setattr("p2s_core.services.segment_composer.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("p2s_core.services.video_service.subprocess.run", fake_subprocess_run)
    project_id = "mvp2c_project"
    run_dir = write_project(runs_dir, project_id)
    pipeline = PaperSummaryPipeline()

    after_assets = pipeline.run_stage(project_id, "asset_generation")
    after_composition = pipeline.run_stage(project_id, "composition")

    assert after_assets.stages["asset_generation"].status == "done"
    assert (run_dir / "audio" / "scene_001.wav").exists()
    assert (run_dir / "assets" / "scene_001_textcard.png").exists()
    assert (run_dir / "segments" / "scene_001.mp4").exists()
    assert (run_dir / "media_metadata" / "audio.json").exists()
    assert after_composition.stages["composition"].status == "done"
    assert after_composition.final_video["path"] == "final/output.mp4"
    assert (run_dir / "final" / "output.mp4").exists()


def test_asset_generation_missing_asset_plan_fails(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "missing_asset_plan"
    (runs_dir / project_id).mkdir(parents=True)
    persistence.save_state(make_state(project_id))

    with pytest.raises(FileNotFoundError):
        PaperSummaryPipeline().run_stage(project_id, "asset_generation")


def test_old_project_migration_has_media_stage_keys():
    state = ProjectState.model_validate(
        {
            "project_id": "old",
            "created_at": "2026-05-11T00:00:00Z",
            "source": {"pdf_path": "runs/old/source.pdf"},
            "persona": {},
            "style": {},
            "stages": {"asset_preparation": {"status": "done"}},
        }
    )

    assert state.stages["asset_preparation"].status == "done"
    assert state.stages["asset_generation"].status == "pending"
    assert state.stages["composition"].status == "pending"
    assert state.stages["media_quality_check"].status == "pending"
