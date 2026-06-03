# BETA-INSTALL-02 Claude Review Cleanup Proof

## Scope

- PR: #735
- Branch: `fix/beta-install-02-dopemux-network`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-pr735-claude-review`
- Task Packet: `task-packets/generated/TP-BETA-INSTALL-02-CLAUDE-REVIEW-001.json`

## Review Inputs

- Claude review verdict: `APPROVE_WITH_NITS`
- User instruction: integrate all Claude review suggestions before merge

## Applied Suggestions

- Removed the `CONPORT_DB_PATH` test path from `test_today_panel_sqlite_operational_error_fallback` and aligned the patch target with the current UI data-source module.
- Changed `scripts/setup.sh` from create-and-grep idempotency to check-then-create `dopemux-network` handling, avoiding false success when Docker fails unexpectedly.

## Validation

PASS:

- `python -m json.tool task-packets/generated/TP-BETA-INSTALL-02-CLAUDE-REVIEW-001.json >/dev/null` exit 0
- `python -m jsonschema -i task-packets/generated/TP-BETA-INSTALL-02-CLAUDE-REVIEW-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exit 0
- `bash -n scripts/setup.sh` exit 0
- `python -m pytest tests/unit/orchestrator/test_data_sources.py::TestUIDataSources::test_today_panel_sqlite_operational_error_fallback -q` exit 0
- `git diff --check` exit 0
- `pre-commit run --files scripts/setup.sh tests/unit/orchestrator/test_data_sources.py CHANGELOG.md task-packets/INDEX.md task-packets/generated/TP-BETA-INSTALL-02-CLAUDE-REVIEW-001.json claudedocs/beta-install-02-claude-review-proof-2026-05-31.md` exit 0

FAIL:

- Initial targeted pytest run failed after removing the env-var path while still patching `dopemux.orchestrator.idempotency.sqlite3.connect`; current `get_today_data()` uses `dopemux.orchestrator.ui.data_sources.sqlite3.connect`.

NOT_RUN:

- Live Docker install/startup validation is intentionally `NOT_RUN` because it mutates local runtime state and is outside this review-cleanup slice.
