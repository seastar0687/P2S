from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import CodeVersion


def capture_code_version(repo_root: Path | None = None) -> CodeVersion:
    """Return current git metadata; normal no-git cases never raise."""
    captured_at = datetime.now(UTC).isoformat()
    cwd = repo_root or Path.cwd()
    try:
        commit = _git(["rev-parse", "--short=7", "HEAD"], cwd)
        branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
        status = _git(["status", "--porcelain"], cwd)
    except (OSError, subprocess.SubprocessError):
        return CodeVersion(
            commit=None,
            branch=None,
            dirty=None,
            captured_at=captured_at,
            source="unknown",
        )

    return CodeVersion(
        commit=commit or None,
        branch=branch or None,
        dirty=bool(status),
        captured_at=captured_at,
        source="git",
    )


def _git(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=5,
        check=True,
    )
    return completed.stdout.strip()
