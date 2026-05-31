# CI full test suite proof - 2026-05-31

## Scope

- Task Packet: `task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json`
- Branch: `fix/ci-full-test-suite`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-ci-full-test-suite`
- Base branch: `main`
- Target: make the full Repo Truth Extractor suite and auditor-router tests blocking CI gates.
- PR URL: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/759`
- Original implementation head before repair pass: `759da14eb9c4aee9aec0614f3b8f6725f85cbc07`
- Current base merged during repair pass: `origin/main` at `309a12a9f8d6ea4f399854f9079205a8b5dd134a`
- Exact final pushed PR head is GitHub PR #759 `headRefOid` after the repair commit is pushed.

## Observed State

- `.github/workflows/ci-complete.yml` already had an `extractor-full` job, but it was named advisory, trapped the pytest exit code, and exited 0 even when the suite failed.
- `tests/auditor_router/` was not present in the CI workflow.
- `PYTHONPATH=src pytest tests/auditor_router -q --tb=short` passed locally, so no import repair was needed in this slice.
- `PYTHONPATH=src pytest services/repo-truth-extractor/tests/ -q --tb=short --disable-warnings --no-cov` passed locally with documented XFAILs.

## Change

- Renamed `extractor-full` from advisory to blocking and removed the `set +e` / `exit 0` trap.
- Changed the full RTE CI command to:
  - `PYTHONPATH=src uv run --frozen pytest services/repo-truth-extractor/tests/ -q --tb=short --disable-warnings --no-cov`
- Added a blocking `auditor-router` CI job:
  - `PYTHONPATH=src uv run --frozen pytest tests/auditor_router/ -q --tb=short --disable-warnings --no-cov`
- Added both jobs to `ci-summary` `needs` and PR gate status evaluation.
- Added Task Packet and index row for replayability.

## Repair Pass - 2026-05-31

- Merged current `origin/main` into `fix/ci-full-test-suite` and preserved the `TP-CI-FULL-TEST-SUITE-001` index row alongside already-merged task packet rows.
- Added the required `CHANGELOG.md` entry for the blocking CI gate change.
- Updated this proof record with PR URL, observed implementation/base SHAs, and validation exit codes.
- Rechecked the prior `extractor-full` failures after current-base merge:
  - The four prescan cases returned expected XFAIL, not XPASS.
  - `test_v4_help_does_not_expose_s_extra_steps` passed.

## Validation

PASS:

- `find . -path "*/tests/test_*.py" | head -20`
  - Exit code: 0.
- `PYTHONPATH=src pytest tests/auditor_router -q --tb=short`
  - Result: 50 passed.
  - Exit code: 0.
- `PYTHONPATH=src uv run --frozen pytest tests/auditor_router/ -q --tb=short --disable-warnings --no-cov`
  - Result: 52 passed on the current-base repair branch.
  - Exit code: 0.
- `PYTHONPATH=src pytest services/repo-truth-extractor/tests/ -q --tb=short --disable-warnings --no-cov`
  - Result: passed with documented XFAILs.
  - Exit code: 0.
- `PYTHONPATH=src uv run --frozen pytest services/repo-truth-extractor/tests/ -q --tb=short --disable-warnings --no-cov`
  - Result: passed with documented XFAILs on the current-base repair branch.
  - Exit code: 0.
- Workflow YAML parse via Python `yaml.safe_load`.
  - Exit code: 0.
- `python -m json.tool task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json >/dev/null`
  - Exit code: 0.
- `python -m jsonschema -i task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Exit code: 0.
- `git diff --check`
  - Exit code: 0.
- PAL codereview with `gpt-5-codex`
  - Result: no issues found.
  - Exit code: 0.
- `pre-commit run --files .github/workflows/ci-complete.yml CHANGELOG.md task-packets/INDEX.md task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json claudedocs/ci-full-test-suite-proof-2026-05-31.md`
  - Result: passed.
  - Exit code: 0.

Repair-pass validation:

- `PYTHONPATH=src uv run --frozen pytest services/repo-truth-extractor/tests/test_code_prescan_truthfulness.py::test_code_prescan_emits_dotted_relative_python_imports services/repo-truth-extractor/tests/test_code_prescan_truthfulness.py::test_code_prescan_api_surface_detection_avoids_substring_false_positives services/repo-truth-extractor/tests/test_code_prescan_truthfulness.py::test_code_prescan_arrow_function_signatures_match_symbol_coverage services/repo-truth-extractor/tests/test_prescan_e2e_smoke.py::test_prescan_real_repo_full_and_incremental_smoke services/repo-truth-extractor/tests/test_phase_s_step_selection.py::test_v4_help_does_not_expose_s_extra_steps -q --tb=short --disable-warnings --no-cov`
  - Result: 1 passed, 4 xfailed.
  - Exit code: 0.

WARN:

- `actionlint` is not installed locally, so workflow semantic validation is limited to YAML parse plus command review.
- Running `uv run` created ignored local `.venv`, `.pytest_cache`, and `__pycache__` artifacts; none are staged.

NOT_RUN:

- Live GitHub Actions execution before PR creation.
- Docker/integration tests.
- Real provider/API-key tests.

## Residual Risk

- Branch protection truth remains `UNKNOWN`; this workflow assumes `ci-summary` continues to be the required aggregate PR gate.
- The full RTE lane increases required PR CI runtime.
- Existing XFAILs remain intentionally documented failures, not passing assertions.
