---
id: task-orchestrator-http-singleton-cutover
title: Task Orchestrator HTTP Singleton Cutover
type: reference
owner: '@hu3mann'
date: '2026-06-14'
prelude: Migration and rollback notes for replacing the per-client task-orchestrator
  stdio launcher with one HTTP singleton per workspace.
author: '@hu3mann'
last_review: '2026-06-14'
next_review: '2026-09-12'
---
# Task Orchestrator HTTP Singleton Cutover

## Scope

This cutover changes only the Claude MCP client connection model for `task-orchestrator`:

- before: `.mcp.json` launches `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh` per MCP client;
- after: `.mcp.json` connects to `http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp`;
- startup: `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh` starts one Docker container for the workspace;
- rollback: `scripts/mcp-wrappers/task-orchestrator-rollback-stdio.sh` stops the HTTP singleton, then `.mcp.json` can be reverted to stdio.

The script intentionally reuses the stdio wrapper's `--print-resolution` output for workspace identity and state paths. It does not independently reimplement the workspace hash, project root, data directory, or config root derivation.

## State Carry-Over

The stdio wrapper derives:

- `state_id`: `<sanitized-project-basename>-<first-16-of-sha256(project_root)>`
- `data_dir`: `${XDG_DATA_HOME:-$HOME/.local/share}/dopemux-mission-control/task-orchestrator/<state_id>`
- `database_path`: `<data_dir>/current-tasks.db`

The HTTP singleton mounts the same `data_dir` at `/app/data` and sets:

- `DATABASE_PATH=/app/data/current-tasks.db`
- `MCP_TRANSPORT=http`
- `MCP_PORT=${TASK_ORCHESTRATOR_HTTP_PORT:-7890}`
- `USE_FLYWAY=true`

Loaded task trees therefore carry over when both launchers resolve the same project root.

## Cutover Procedure

1. Confirm `.mcp.json` contains the HTTP task-orchestrator entry.
2. Start or converge the singleton:

   ```bash
   scripts/mcp-wrappers/task-orchestrator-http-singleton.sh
   ```

3. Reconnect the MCP client session so it reads `.mcp.json`.
4. Verify the endpoint:

   ```bash
   curl -fsS -X POST "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp" \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}' |
     grep -q serverInfo
   ```

5. Verify singleton count:

   ```bash
   docker ps --format '{{.Names}}' | grep '^task-orchestrator-'
   ```

Expected result: one `task-orchestrator-<state_id>` container for the workspace.

## Dry-Run Validation

The dry-run path performs no Docker writes:

```bash
bash tests/mcp_wrappers/test_orchestrator_http_singleton.sh --dry-run
```

It verifies:

- `.mcp.json` uses `type=http`;
- no stdio `command` or `args` remain in the task-orchestrator entry;
- the URL is loopback-bound;
- the singleton script emits a Docker command with `MCP_TRANSPORT=http`;
- rollback instructions are present.

## Two-Session Coexistence Procedure

For a live operator validation, run:

1. Start the singleton once with `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh`.
2. Open two Claude/Codex sessions for the same workspace after the `.mcp.json` HTTP entry is active.
3. In each session, call a read-only task-orchestrator tool such as `get_context`.
4. Confirm `docker ps --format '{{.Names}}'` shows exactly one `task-orchestrator-<state_id>` container.

This proves client coexistence for the observed workspace. It does not prove every future multi-host or port-policy scenario.

## Rollback

Run:

```bash
scripts/mcp-wrappers/task-orchestrator-rollback-stdio.sh
```

Then revert the task-orchestrator entry in `.mcp.json` to:

```json
{
  "type": "stdio",
  "command": "scripts/mcp-wrappers/task-orchestrator-current-stdio.sh",
  "args": [],
  "env": {
    "TASK_ORCHESTRATOR_PROJECT_ROOT": "${TASK_ORCHESTRATOR_PROJECT_ROOT:-}",
    "DOPEMUX_PROJECT_ROOT": "${DOPEMUX_PROJECT_ROOT:-}",
    "DOPEMUX_WORKSPACE_ROOT": "${DOPEMUX_WORKSPACE_ROOT:-}"
  },
  "description": "Current 13-tool MCP Task Orchestrator with repo-scoped SQLite state"
}
```

Reconnect the MCP client session after reverting.

## Known Unknowns

- Port policy for multiple simultaneous workspaces on one host remains explicit operator configuration via `TASK_ORCHESTRATOR_HTTP_PORT`.
- Live two-session validation requires two real client sessions and is not exercised by dry-run CI.
- The SessionStart health probe already detects HTTP MCP entries by port, but its generic remediation wording is not changed in this packet because `.claude/hooks/mcp_health_probe.py` is outside the allowlist.
