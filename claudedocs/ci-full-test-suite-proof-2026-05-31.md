# CI full test suite proof - 2026-05-31

## Scope

- Task Packet: `task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json`
- Branch: `fix/ci-full-test-suite`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-ci-full-test-suite`
- Base branch: `main`
- Target: make the full Repo Truth Extractor suite and auditor-router tests blocking CI gates.

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

## Validation

PASS:

- `find . -path "*/tests/test_*.py" | head -20`
- `PYTHONPATH=src pytest tests/auditor_router -q --tb=short`
  - Result: 50 passed.
- `PYTHONPATH=src uv run --frozen pytest tests/auditor_router/ -q --tb=short --disable-warnings --no-cov`
  - Result: 50 passed.
- `PYTHONPATH=src pytest services/repo-truth-extractor/tests/ -q --tb=short --disable-warnings --no-cov`
  - Result: passed with documented XFAILs.
- `PYTHONPATH=src uv run --frozen pytest services/repo-truth-extractor/tests/ -q --tb=short --disable-warnings --no-cov`
  - Result: passed with documented XFAILs.
- Workflow YAML parse via Python `yaml.safe_load`.
- `python -m json.tool task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json >/dev/null`
- `python -m jsonschema -i task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `git diff --check`
- PAL codereview with `gpt-5-codex`
  - Result: no issues found.
- `pre-commit run --files .github/workflows/ci-complete.yml task-packets/INDEX.md task-packets/generated/TP-CI-FULL-TEST-SUITE-001.json claudedocs/ci-full-test-suite-proof-2026-05-31.md`
  - Result: passed.

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
