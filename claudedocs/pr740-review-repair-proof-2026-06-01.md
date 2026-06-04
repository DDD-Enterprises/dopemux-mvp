# PR 740 Review Repair Proof

## Scope

- PR: #740
- Local branch: `codex/pr740-review-repair-20260601`
- Target PR branch: `fix/beta-cli-01-decisions-subcommands`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-pr740-review-repair`
- Task Packet: `task-packets/generated/TP-BETA-CLI-01-DECISIONS-REVIEW-001.json`

## Review Inputs

- Claude Code Review: `REQUEST_CHANGES`
- Codex review threads: string ConPort IDs and GET decision limit propagation
- Copilot review threads: ConPort HTTP port, styled table call shape, string IDs, nested POST response ID, registration test update, and limit propagation
- User instruction: integrate all Claude review suggestions before merge

## Applied Changes

- Changed decisions REST calls to use `CONPORT_URL` or `CONPORT_HTTP_PORT` default `3004`, not `CONPORT_MCP_PORT`.
- Passed `limit` to `GET /api/decisions` and used a bounded lookup window for `show`, `query`, `review`, and `update-outcome`.
- Accepted string decision IDs and compared decision IDs as strings.
- Fixed `styled_table` usage by passing columns positionally.
- Validated referenced decisions before append-only review/outcome writes.
- Read created decision IDs from the nested `decision.id` response shape.
- Updated user-facing wording from graph-link claims to append-only references.
- Added focused unit coverage for decisions list, show, query, review, update-outcome, ConPort rejection handling, and command registration.

## Validation

PASS:

- `python -m json.tool task-packets/generated/TP-BETA-CLI-01-DECISIONS-REVIEW-001.json >/dev/null` exit 0
- `python -m jsonschema -i task-packets/generated/TP-BETA-CLI-01-DECISIONS-REVIEW-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exit 0
- `python -m pytest tests/unit/test_decisions_commands.py tests/unit/test_cli_audit_remediations.py::test_decisions_subcommands_are_registered -q` exit 0
- `python -m pytest tests/unit/test_cli_audit_remediations.py tests/unit/test_decisions_commands.py -q` exit 0
- `git diff --check` exit 0
- `pre-commit run --files src/dopemux/commands/decisions_commands.py tests/unit/test_decisions_commands.py tests/unit/test_cli_audit_remediations.py CHANGELOG.md task-packets/INDEX.md task-packets/generated/TP-BETA-CLI-01-DECISIONS-REVIEW-001.json claudedocs/pr740-review-repair-proof-2026-06-01.md` exit 0

NOT_RUN:

- Live ConPort/Docker runtime validation is intentionally `NOT_RUN`; this review repair uses mocked HTTP calls and does not start local services.
