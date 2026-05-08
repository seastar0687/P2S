# Windows / Codex Environment Notes

This workspace uses a Windows-specific Python setup to keep Codex sessions stable.

## Recommended Runtime

Use the project-local virtual environment:

```powershell
.\.venv-win\Scripts\python.exe
```

Common commands:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
.\.venv-win\Scripts\python.exe -m p2s_core.cli status
```

## Why This Exists

In this workspace, new Codex conversations may not reliably access:

```text
C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe
```

When `.venv-win` is built from that user-local Python, its launchers can fail with:

```text
Unable to create process using '"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" ...'
```

To avoid that, the workspace keeps a local Python runtime:

```text
.python311/
```

`.venv-win/` should be built from `.python311/python.exe`, so it remains usable from future Codex sessions.

## Repair `.venv-win`

If `.venv-win` breaks, rebuild it from the workspace-local runtime:

```powershell
Remove-Item -LiteralPath .\.venv-win -Recurse -Force
.\.python311\python.exe -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-win\Scripts\python.exe -m pytest tests\test_schema.py
```

Expected verification:

```text
Python 3.11.9
12 passed
```

## Network / Pip Notes

Codex sandboxed commands may block pip network access. If dependency installation fails with socket or network permission errors, rerun:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
```

with sandbox escalation.

## Avoid MSYS Python for This Project

The default `python` on PATH may be:

```text
C:\msys64\ucrt64\bin\python.exe
```

That Python is currently 3.10 and can fall back to source builds for packages such as `pymupdf`, causing build and certificate problems. Prefer `.venv-win\Scripts\python.exe`.

## Pytest Cache Issue

Pytest may create permission-denied `pytest-cache-files-*` directories in this Windows workspace. Tests can still pass. These paths are ignored by `.gitignore` and `.ignore`; updates are tracked in `docs/current/ISSUES.md`.
