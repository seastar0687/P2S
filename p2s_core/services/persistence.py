from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import ProjectState


RUNS_DIR = Path("runs")
STATE_FILENAME = "project_state.json"


def project_dir(project_id: str) -> Path:
    return RUNS_DIR / project_id


def state_path(project_id: str, filename: str = STATE_FILENAME) -> Path:
    return project_dir(project_id) / filename


def load_state(project_id: str) -> ProjectState:
    path = state_path(project_id)
    return ProjectState.model_validate_json(path.read_text(encoding="utf-8"))


def save_state(state: ProjectState) -> None:
    path = state_path(state.project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def snapshot(project_id: str, filename: str = STATE_FILENAME) -> str:
    source_path = state_path(project_id, filename)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    if filename == STATE_FILENAME:
        snapshot_name = f"project_state_{timestamp}.json"
    else:
        source = Path(filename)
        snapshot_name = f"{source.stem}_{timestamp}{source.suffix}"

    snapshot_path = source_path.with_name(snapshot_name)
    shutil.copy2(source_path, snapshot_path)
    return str(snapshot_path)


def list_revisions(project_id: str) -> list[str]:
    directory = project_dir(project_id)
    if not directory.exists():
        return []

    return sorted(str(path) for path in directory.glob("project_state_*.json"))
