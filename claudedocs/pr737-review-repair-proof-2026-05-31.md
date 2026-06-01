# PR 737 Review Repair Proof

## Scope

- PR: #737
- Local branch: `codex/pr737-review-repair-20260601`
- Target PR branch: `fix/beta-install-01-mcp-01-mcp-json`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-pr737-review-repair`
- Task Packet: `task-packets/generated/TP-BETA-INSTALL-01-MCP-01-REVIEW-001.json`

## Review Inputs

- Claude Code Review: `REQUEST_CHANGES`
- Codex review threads: tracked launcher path and catalog URL default sync
- Copilot review threads: untracked `plugins/dopemux-mission-control` path in `.mcp.json`, `mcp_catalog.yaml`, and docs
- User instruction: integrate all Claude review suggestions before merge

## Applied Changes

- Added tracked Task Orchestrator launcher wrapper: `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh`
- Added tracked logback config required by the wrapper: `scripts/mcp-wrappers/task-orchestrator-logback.xml`
- Updated `.mcp.json`, `mcp_catalog.yaml`, `src/dopemux/mcp/default_catalog.yaml`, and Task Orchestrator reference docs away from untracked plugin paths.
- Synced catalog SSE defaults to `http://localhost:${CONPORT_MCP_PORT:-3005}/mcp` and `http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp`.
- Added non-skipped launcher resolution coverage and a catalog-template equality regression for checked-in `.mcp.json`.

## Validation

PASS:

- `python -m json.tool .mcp.json >/dev/null` exit 0
- YAML parse for `mcp_catalog.yaml` and `src/dopemux/mcp/default_catalog.yaml` exit 0
- `python -m json.tool task-packets/generated/TP-BETA-INSTALL-01-MCP-01-REVIEW-001.json >/dev/null` exit 0
- `python -m jsonschema -i task-packets/generated/TP-BETA-INSTALL-01-MCP-01-REVIEW-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exit 0
- `bash -n scripts/mcp-wrappers/task-orchestrator-current-stdio.sh` exit 0
- `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh --print-resolution` exit 0
- `python -m pytest tests/unit/test_task_orchestrator_launcher.py tests/unit/test_mcp_commands_catalog.py::test_mcp_init_keeps_matching_committed_template_and_writes_envrc tests/unit/test_mcp_commands_catalog.py::test_committed_mcp_json_matches_root_catalog_defaults -q` exit 0
- `git diff --check` exit 0
- `pre-commit run --files .mcp.json mcp_catalog.yaml src/dopemux/mcp/default_catalog.yaml scripts/mcp-wrappers/task-orchestrator-current-stdio.sh scripts/mcp-wrappers/task-orchestrator-logback.xml tests/unit/test_task_orchestrator_launcher.py tests/unit/test_mcp_commands_catalog.py docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md CHANGELOG.md task-packets/INDEX.md task-packets/generated/TP-BETA-INSTALL-01-MCP-01-REVIEW-001.json claudedocs/pr737-review-repair-proof-2026-05-31.md` exit 0

NOT_RUN:

- Live Docker Task Orchestrator startup is intentionally `NOT_RUN` because it would start or replace a local container and is outside this review-repair slice.
