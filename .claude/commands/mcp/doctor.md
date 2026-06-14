---
description: "MCP fleet health: wraps `dopemux mcp doctor`, probes singletons, detects leaked task-orchestrator containers, offers safe prune"
arguments: "[--prune] [--json]"
allowed-tools: ["Bash", "Read", "Grep"]
model: "claude-sonnet-4-5"
---

# /mcp:doctor — MCP Fleet Health Sweep

Full-fleet MCP health check. Wraps the existing `dopemux mcp doctor` CLI (declared-server
checks) and adds the three things it doesn't do: leaked-container detection/prune,
singleton probing, and compose-service status.

Use when MCP calls are timing out, tools are returning unexpected errors, or after a
multi-client session that may have spun up extra task-orchestrator containers.

---

## Phase 1 — Declared-server sweep

Run the existing CLI and capture its output verbatim:
```bash
dopemux mcp doctor
```
This already checks env vars, port listening, and stdio runner for every server
declared in the worktree's `.mcp.json`. Do not re-derive what it already covers.

Report its exit code and stdout under heading **Declared servers**.

---

## Phase 2 — Singleton sweep

Read `mcp_catalog.yaml` (Read tool) and extract all servers where `scope: singleton`.
For each http/sse singleton, probe TCP reachability:
```bash
curl -s -o /dev/null -w '%{http_code}' --max-time 2 <url-from-catalog>
# Any HTTP response (including 405/406) = listening; connection refused/timeout = down.
# desktop-commander exposes a /health endpoint — use it for a cleaner check.
```

If a singleton is down, the fix is its `docker_compose_service` from the catalog:
```bash
docker compose up -d <service>
```

Report each singleton: name / scope / transport / status / fix (if down).

---

## Phase 3 — Leaked-container sweep (headline feature)

Container-naming pattern from `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh:141`:
```
task-orchestrator-<workspace-slug>-<16-char-sha256>
```
The wrapper assigns one deterministic container per workspace and removes stale ones on
start. Multiple containers = prior sessions didn't clean up (SQLite-contention spiral).

```bash
docker ps --format '{{.ID}}\t{{.Names}}\t{{.RunningFor}}' \
  | grep 'task-orchestrator-' || true
```

Interpret results:
- 0 containers → task-orchestrator running stdio-less (may be fine if HTTP transport)
- 1 container → normal; show its name and uptime
- 2 containers → flag as stale accumulation
- ≥3 containers → **name the SQLite-contention spiral**: "Multiple stdio containers contend
  on the shared per-workspace SQLite DB. This causes MCP tool timeouts and retries."

**Without `--prune`**: print the exact `docker kill <id>` command for each non-newest
container — but do NOT run it. "Run these to prune stale containers:"

**With `--prune`**: kill all but the newest container one at a time:
```bash
# Sort by running-for, keep newest (smallest uptime), kill the rest:
docker kill <id>   # one call per stale container
```
Use `docker kill` (single ID, NOT batched). Do NOT use `docker stop` or `docker rm -f` —
those 404 on Docker Desktop 29.4.1 when containers are in this state.
Skip the container with the smallest "running for" value (likely the live session's).

After prune, verify with a second `docker ps | grep task-orchestrator` and report the
final count.

---

## Phase 4 — Compose status

```bash
docker compose ps --format json 2>/dev/null
```
10-second timeout — if exceeded or output is empty, report **NOT_RUN** (cold Docker).

Cross-reference against `docker_compose_service` values in `mcp_catalog.yaml`.
Services in `starting` or `health: starting` state → report as **cold-start grace**
(known race — see BETA-MCP-02), not failure.

---

## Phase 5 — Report

One consolidated table:
| Server | Scope | Transport | Check | Status | Fix |
|--------|-------|-----------|-------|--------|-----|

Status icons: ✅ healthy · ⚠️ degraded · ❌ down · ⏳ cold-start · NOT_RUN skipped

ADHD: list max 3 fix actions prominently with their exact commands; collapse the rest.

`--json` flag: emit the full table as JSON for statusline/automation consumption:
```json
{
  "servers": {"<name>": {"status": "up|down|unknown", "fix": "..."}},
  "leaked_containers": <int>,
  "compose_status": {...}
}
```

---

## Error Handling

- `dopemux mcp doctor` not found → note it, proceed with remaining phases
- `docker` not available → skip Phases 3 and 4 with NOT_RUN note
- `mcp_catalog.yaml` not readable → skip Phase 2 singleton sweep

---

## Notes for Claude

- **Never run `docker kill` without `--prune`** — without the flag, print commands only.
- The durable fix for container leaks is the HTTP-singleton transport cutover
  (`MCP_TRANSPORT=http`, POC-verified 2026-05-31). This doctor command is the mitigation
  until that cutover packet runs.
- The leaked-container check belongs inside `dopemux mcp doctor` CLI eventually — this
  skill validates the check before that promotion.
- Model: `claude-sonnet-4-5` per routing policy.
