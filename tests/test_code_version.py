import subprocess
from pathlib import Path

from p2s_core.models import CodeVersion
from p2s_core.services.code_version import capture_code_version


ROOT = Path(__file__).resolve().parents[1]


def test_capture_code_version_returns_code_version_in_git_repo():
    code_version = capture_code_version(ROOT)

    assert isinstance(code_version, CodeVersion)
    if code_version.source == "git":
        assert code_version.commit
        assert len(code_version.commit) == 7
        assert code_version.branch
        assert code_version.dirty in {True, False}
    else:
        assert code_version.commit is None
        assert code_version.branch is None
        assert code_version.dirty is None


def test_capture_code_version_returns_unknown_on_git_failure(monkeypatch):
    def fail_run(*args, **kwargs):
        raise subprocess.SubprocessError("git unavailable")

    monkeypatch.setattr(subprocess, "run", fail_run)

    code_version = capture_code_version(ROOT)

    assert code_version.source == "unknown"
    assert code_version.commit is None
    assert code_version.branch is None
    assert code_version.dirty is None


def test_capture_code_version_records_dirty_state(monkeypatch):
    def fake_run(args, **kwargs):
        command = args[1:]
        if command == ["rev-parse", "--short=7", "HEAD"]:
            stdout = "abc1234\n"
        elif command == ["rev-parse", "--abbrev-ref", "HEAD"]:
            stdout = "main\n"
        elif command == ["status", "--porcelain"]:
            stdout = " M p2s_core/models/project_state.py\n"
        else:
            raise AssertionError(f"unexpected git command: {command}")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    code_version = capture_code_version(ROOT)

    assert code_version.source == "git"
    assert code_version.commit == "abc1234"
    assert code_version.branch == "main"
    assert code_version.dirty is True
