# P2S

P2S is a claim-grounded, review-guided paper-to-short-video research prototype. The current MVP 0 focus is not video generation yet; it is the reliable project skeleton for paper ingestion, project state, persona/style packages, and a minimal CLI flow.

## Install

Use Python 3.11 and install the MVP dependencies. In this Windows workspace, prefer the project-local venv:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
```

Windows/Codex environment notes and venv repair steps are in `docs/current/WINDOWS_ENVIRONMENT.md`.

OpenAI is not required for the current extraction flow. When a real LLM smoke test or MVP 1 claim/script generation needs it, copy `.env.example` to the project-local `.env` file and set:

```text
OPENAI_API_KEY=sk-your-key
```

Do not put real keys in `.env.example`.
The runtime loads this project-local `.env` before resolving `${OPENAI_API_KEY}` in `config.yaml`, so a global Windows environment variable is not required.

## Hello World

Run the MVP 0 paper extraction chain:

```powershell
.\.venv-win\Scripts\python.exe -m p2s_core.cli init paper.pdf --id demo_project
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage extraction --project demo_project
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project demo_project
```

Expected outputs:

- `runs/demo_project/source.pdf`
- `runs/demo_project/project_state.json`
- `runs/demo_project/project_state_YYYYMMDDTHHMMSS.json`
- `runs/demo_project/extracted_text.md`

MVP 1 adds `claim_extraction`, which requires `OPENAI_API_KEY` for real LLM runs.
The automated tests use fake clients and do not require an OpenAI key.

## Documents

Project documents follow the v8 architecture document management layout:

- `docs/current/`: current implementation references, including the active architecture spec, research direction, and issue tracker.
- `docs/sprints/`: historical sprint plans and status snapshots. Treat these as records of what was decided at the time.
- `docs/archive/`: retired architecture specs and migration logs for comparison only.

Start with `docs/current/P2S_redesign_architecture_v8.md` for the active architecture, and use `docs/sprints/` only when you need historical MVP context.

## CLI

```powershell
.\.venv-win\Scripts\python.exe -m p2s_core.cli init <pdf_path> [--persona seina] [--style rigorous_science_short] [--id <project_id>]
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage extraction [--project <project_id>] [--force]
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage claim_extraction [--project <project_id>] [--force]
.\.venv-win\Scripts\python.exe -m p2s_core.cli status [--project <project_id>]
.\.venv-win\Scripts\python.exe -m p2s_core.cli validate-personas
.\.venv-win\Scripts\python.exe -m p2s_core.cli validate-styles
```

If `run` or `status` does not receive `--project`, it uses the newest project under `runs/` that contains `project_state.json`.

## Tests

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

The current suite covers schema roundtrips, persistence, LLM service request behavior with a fake client, persona/style loading, compatibility checks, PDF extraction, pipeline behavior, CLI behavior, and the sprint contract smoke tests in `tests/test_pipeline_smoke.py`.

## Known Issue

On the current Windows workspace, pytest can leave permission-denied `pytest-cache-files-*` directories. Tests still pass, and the directories are ignored by `.gitignore` and `.ignore`. Track updates in `docs/current/ISSUES.md`.
