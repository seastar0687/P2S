from pathlib import Path
import shutil

from p2s_core.models import ProjectSource, ProjectState, default_stages
from p2s_core.services import persistence


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "persistence"


def make_state(project_id: str = "2026-05-06_persist") -> ProjectState:
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-06T00:00:00Z",
        source=ProjectSource(pdf_path=f"runs/{project_id}/source.pdf"),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        stages=default_stages(),
    )


def reset_test_runs() -> Path:
    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def test_save_and_load_state(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    state = make_state()

    persistence.save_state(state)
    loaded = persistence.load_state(state.project_id)

    assert loaded == state
    assert (runs_dir / state.project_id / "project_state.json").exists()


def test_save_state_does_not_create_snapshot(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    state = make_state()

    persistence.save_state(state)

    assert persistence.list_revisions(state.project_id) == []


def test_snapshot_copies_current_state(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    state = make_state()
    persistence.save_state(state)

    snapshot_path = Path(persistence.snapshot(state.project_id))
    revisions = persistence.list_revisions(state.project_id)

    assert snapshot_path.exists()
    assert snapshot_path.name.startswith("project_state_")
    assert snapshot_path.name.endswith(".json")
    assert revisions == [str(snapshot_path)]
    assert ProjectState.model_validate_json(snapshot_path.read_text(encoding="utf-8")) == state


def test_snapshot_supports_custom_filename(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "2026-05-06_custom"
    project_dir = runs_dir / project_id
    project_dir.mkdir(parents=True)
    (project_dir / "notes.json").write_text('{"ok": true}', encoding="utf-8")

    snapshot_path = Path(persistence.snapshot(project_id, filename="notes.json"))

    assert snapshot_path.exists()
    assert snapshot_path.name.startswith("notes_")
    assert snapshot_path.read_text(encoding="utf-8") == '{"ok": true}'


def test_list_revisions_missing_project_returns_empty_list(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)

    assert persistence.list_revisions("missing") == []
