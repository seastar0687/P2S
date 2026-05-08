# P2S Issue Log

This file tracks environment, tooling, test, dependency, and spec-alignment issues found during MVP implementation. Update this log whenever a known issue changes status, gains a workaround, or reappears in a later step.

## P2S-ISSUE-001: pytest-cache-files-mnin8krq permission-denied cache directory

- Status: mitigated
- First seen: 2026-05-06
- Symptom: Running pytest in the current Windows workspace created an empty `pytest-cache-files-mnin8krq` directory that denied recursive listing, ACL inspection, and deletion.
- Impact: Tests still passed, but recursive file enumeration and cleanup commands can fail if they try to enter the directory.
- Workaround: Ignore `pytest-cache-files-*/` in `.gitignore` and `.ignore`; use `rg --files` after ignore rules are present.
- Next action: Recheck after a stable project-local Python environment is created. If the issue no longer reproduces, mark this resolved and note the working environment.
- Update history:
  - 2026-05-06: Issue created after MVP0 Day 1 scaffold verification.
  - 2026-05-06: Reproduced during MVP0 Day 2 schema test verification as `pytest-cache-files-hdilwqwh`; tests still passed.
  - 2026-05-06: During persistence tests, pytest also failed to create `tmp_path` under `C:\Users\user\AppData\Local\Temp\pytest-of-user`; tests were adjusted to use workspace-local `.test_runs/`.
  - 2026-05-06: Reproduced after persistence tests as `pytest-cache-files-lgl4fgeo`; full test suite passed with warning.
  - 2026-05-06: Reproduced after LLMService tests as `pytest-cache-files-bdn599k2`; full test suite passed with warning.
  - 2026-05-06: Reproduced after persona/style loader tests as `pytest-cache-files-ofyl0jci`; full test suite passed with warning.
  - 2026-05-06: Reproduced after Day 7 persona/style package content tests as `pytest-cache-files-oigtp6kn`; full test suite passed with warning.
  - 2026-05-06: Reproduced after Day 8 PyMuPDF extraction tests as `pytest-cache-files-n06_ilkx`; full test suite passed with warning.
  - 2026-05-06: Reproduced after Day 9 pipeline tests as `pytest-cache-files-bwktglvp`; full test suite passed with warning.
  - 2026-05-06: Reproduced after Day 10 CLI tests as `pytest-cache-files-6bei76xr`; full test suite passed with warning.
  - 2026-05-06: Reproduced after Day 11 pipeline smoke tests as `pytest-cache-files-0zs1qvqo`; full test suite passed with warning.
  - 2026-05-06: Reproduced during final MVP0 verification as `pytest-cache-files-m_wcxcm6`; full test suite passed with warning.
  - 2026-05-06: **Mitigated**. Reproduced 12 times across all MVP0 days; tests always passed. Root cause is Windows temp directory ACL restriction, unrelated to program logic. `.gitignore` workaround is in place. Status changed from `open` to `mitigated`. Reopen only if tests begin to fail due to this issue.
  - 2026-05-06: During MVP1 Day 11 cleanup, user manually removed all `pytest-cache-files-*` directories; current count is 0. The issue remains `mitigated` because pytest may recreate these directories on future runs.
