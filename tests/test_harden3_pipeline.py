import json
import subprocess
from pathlib import Path

import pytest

from p2s_core.pipelines import PaperSummaryPipeline, StagePrerequisiteError
from p2s_core.services import persistence
from tests.test_mvp2c_thin_pipeline import fake_subprocess_run, make_state, reset_test_runs, write_project


def _ffprobe_run(command, capture_output=True, text=True, **kwargs):
    if command[0] == "ffprobe":
        return subprocess.CompletedProcess(
            command,
            0,
            '{"format":{"duration":"1.2"},"streams":[{"codec_type":"video","codec_name":"h264","pix_fmt":"yuv420p"},{"codec_type":"audio","codec_name":"aac"}]}',
            "",
        )
    return fake_subprocess_run(command, capture_output=capture_output, text=text, **kwargs)


def test_media_quality_check_writes_report_after_composition(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    monkeypatch.setattr("p2s_core.services.segment_composer.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("p2s_core.services.video_service.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("p2s_core.services.ffprobe_utils.subprocess.run", _ffprobe_run)
    project_id = "harden3_project"
    run_dir = write_project(runs_dir, project_id)
    pipeline = PaperSummaryPipeline()
    pipeline.run_stage(project_id, "asset_generation")
    pipeline.run_stage(project_id, "composition")

    state = pipeline.run_stage(project_id, "media_quality_check")
    report = json.loads((run_dir / "media_quality_report.json").read_text(encoding="utf-8"))

    assert state.stages["media_quality_check"].status == "done"
    assert state.assets["media_quality_report"] == "media_quality_report.json"
    assert report["pass_gate"] is True
    assert len(report["audio_results"]) == 2


def test_media_quality_check_requires_composition(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "requires_composition"
    write_project(runs_dir, project_id)
    state = make_state(project_id)
    state.stages["asset_preparation"].status = "done"
    persistence.save_state(state)

    with pytest.raises(StagePrerequisiteError):
        PaperSummaryPipeline().run_stage(project_id, "media_quality_check")


def test_missing_final_output_fails_gate_but_writes_report(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    monkeypatch.setattr("p2s_core.services.segment_composer.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("p2s_core.services.video_service.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("p2s_core.services.ffprobe_utils.subprocess.run", _ffprobe_run)
    project_id = "missing_final"
    run_dir = write_project(runs_dir, project_id)
    pipeline = PaperSummaryPipeline()
    pipeline.run_stage(project_id, "asset_generation")
    pipeline.run_stage(project_id, "composition")
    (run_dir / "final" / "output.mp4").unlink()

    state = pipeline.run_stage(project_id, "media_quality_check")
    report = json.loads((run_dir / "media_quality_report.json").read_text(encoding="utf-8"))

    assert state.stages["media_quality_check"].status == "needs_review"
    assert report["pass_gate"] is False
    assert any("composition" in issue for issue in report["blocking_issues"])
