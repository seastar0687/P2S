from p2s_core.models import ProjectSource, ProjectState, StageState


def test_old_project_state_without_code_version_loads_successfully():
    raw = {
        "project_id": "old_project",
        "created_at": "2026-05-08T00:00:00Z",
        "source": {"pdf_path": "runs/old_project/source.pdf"},
        "persona": {"persona_id": "seina", "version": "0.1.0"},
        "style": {"style_id": "rigorous_science_short", "version": "0.1.0"},
        "stages": {
            "extraction": {
                "status": "done",
                "started_at": None,
                "finished_at": "2026-05-08T00:01:00Z",
                "output_paths": ["extracted_text.md"],
                "error": None,
                "revision_count": 0,
            }
        },
    }

    state = ProjectState.model_validate(raw)

    assert state.code_version is None
    assert state.stages["extraction"].code_version is None
    assert "llm_quality_rewrite" in state.stages


def test_stage_state_without_code_version_defaults_to_none():
    stage = StageState(status="pending")

    assert stage.code_version is None


def test_project_state_accepts_code_version_roundtrip_shape():
    state = ProjectState(
        project_id="code_version_project",
        created_at="2026-05-08T00:00:00Z",
        source=ProjectSource(pdf_path="runs/code_version_project/source.pdf"),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        stages={"extraction": StageState(status="pending")},
    )

    loaded = ProjectState.model_validate_json(state.model_dump_json())

    assert loaded.code_version is None
    assert loaded.stages["extraction"].code_version is None
