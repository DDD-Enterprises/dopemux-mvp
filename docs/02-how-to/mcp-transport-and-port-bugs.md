---
id: mcp-transport-and-port-bugs
title: MCP Transport Misconfiguration and Port Collision Reference
type: reference
owner: dopemux-infra
date: 2026-07-06
author: '@hu3mann'
last_review: '2026-07-06'
next_review: '2026-10-05'
prelude: MCP Transport Misconfiguration and Port Collision Reference (how-to) for
  dopemux documentation and developer workflows.
---
# MCP Transport Misconfiguration and Port Collision Reference

This document describes three confirmed bugs that were discovered during the `dNh_CRM`
workspace MCP connectivity investigation (2026-07-06) and the authoritative fixes
applied to `dopemux-mvp`.

> [!IMPORTANT]
> **Repo-aware doctor (TP-DMX-MCP-RUNTIME-001)** is the pre-start truth gate:
> `dopemux mcp doctor --repo <path> [--json]`. It loads the target
> `.envrc.dopemux-mcp`, validates catalog transports, reports `%100` hash
> birthday-risk / missing rebind, compose lifecycle hazards (fixed
> `mcp-conport` name, relative `./.dopemux` volume), and refuses to treat
> unlabeled listening ports as owned. It does **not** start or stop containers.
>
> **Config repair (TP-DMX-MCP-RUNTIME-003):** fix transport mismatches without
> hand-editing every worktree:
> `dopemux mcp repair-config --repo <path> --dry-run --json` then `--apply`.
> Preserves custom mcpServers entries; never mutates `~/.claude.json`.
> Runtime start remains `dopemux mcp start --repo <path>` (Packet 002).

---

## Transport Architecture — What is Correct

> [!IMPORTANT]
> **The canonical `mcp_catalog.yaml` and `.mcp.json` are CORRECT.**
> `dope-memory` and `task-orchestrator` use `transport: http` / `"type": "http"` which
> means **MCP Streamable HTTP** — not legacy SSE.  An earlier hotfix that switched
> these to `"type": "sse"` was **wrong** and caused connection failures.

| Server | Transport | Protocol | Client call |
|---|---|---|---|
| `conport` | `sse` | Server-Sent Events | `GET /sse` with `Accept: text/event-stream` |
| `dope-memory` | `http` | Streamable HTTP (FastMCP `http_app()`) | `POST /mcp` with JSON-RPC body |
| `task-orchestrator` | `http` | Streamable HTTP (Ktor) | `POST /mcp` with JSON-RPC body |
| `pal`, `serena`, `dope-context` | `http` | Streamable HTTP | `POST /mcp` with JSON-RPC body |
| `desktop-commander` | `sse` | Server-Sent Events | `GET /sse` with `Accept: text/event-stream` |

### Verifying a Streamable HTTP server

```bash
# dope-memory (replace port with actual DOPE_MEMORY_PORT from .envrc.dopemux-mcp)
curl -X POST http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
# Expected: JSON-RPC response body (200 OK)
# NOT expected: 406 Not Acceptable (that happens only on a GET to a Streamable HTTP endpoint)

# task-orchestrator
curl -X POST http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

### Verifying an SSE server

```bash
# conport
curl -N -s -X GET http://localhost:${CONPORT_MCP_PORT:-3005}/sse \
  -H "Accept: text/event-stream"
# Expected: event stream opens, first event is "endpoint"
```

### The 406 error explained

A `406 Not Acceptable: Client must accept text/event-stream` response from `/mcp`
means you sent a **GET** to a **Streamable HTTP** endpoint.  This is **not** a bug
in the server — it is correct rejection of the wrong method.  The fix is to POST
JSON-RPC, not to switch the transport type to `sse`.

---

## Bug 1: Transport Mismatch (Mis-applied SSE Hotfix)

**Status**: Root cause identified; canonical files are correct; hotfix reverted.

**What happened**: During the `dNh_CRM` debugging session, `curl -X GET /mcp`
returned `406`.  This was misinterpreted as "the server is SSE, not HTTP".  A
`sed` replacement switched all `transport: http` entries in `mcp_catalog.yaml` to
`transport: sse`, and `.mcp.json` was also patched to `"type": "sse"`.

**Why this was wrong**: The 406 is *expected* for a Streamable HTTP endpoint when
a GET is sent.  The real protocol (`"type": "http"`) was already correct.  Switching
to `"type": "sse"` caused the client to open an SSE GET stream against an endpoint
that expects JSON-RPC POSTs, causing immediate protocol mismatch.

**Correct configuration** (already in repo):
```json
{
  "dope-memory":       { "type": "http", "url": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp" },
  "task-orchestrator": { "type": "http", "url": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp" },
  "conport":           { "type": "sse",  "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse" }
}
```

---

## Bug 2: Port Collision via Hash Offset (Fixed in mcp_commands.py)

**Status**: **FIXED** — `_allocate_ports` now pre-seeds singleton reserved ports.

**Root cause**: `dopemux mcp init` computes per-worktree ports by hashing the
workspace path and taking `hash % 100` as an offset added to each service's
`default_port_base`.  The collision check only detected *intra-worktree*
collisions; it never checked whether the computed port was already occupied by a
**singleton** service that has a statically-declared port in the catalog.

For workspace `dNh_CRM`, the hash offset was `+5`:
- `CONPORT_HTTP_PORT` base `3004` → `3009` → **collides with `gpt-researcher` at `3009`**

**Fix applied** (`src/dopemux/commands/mcp_commands.py`):

The new `_singleton_reserved_ports()` helper collects all singleton-declared ports
at init time and pre-seeds `seen_ports` before any per-worktree allocation runs.
Any hash-offset that would land on a singleton port now raises a clear error instead
of silently colliding at Docker bind time.

**Workaround** (if you hit this in an existing workspace):
```bash
# Manually set safe ports in .envrc.dopemux-mcp
# Then restart the containers with the new ports
export CONPORT_HTTP_PORT=3040
export CONPORT_MCP_PORT=3041
export DOPE_MEMORY_PORT=3060
```

---

## Bug 3: `wrapper-singleton` Port Offset (Fixed in mcp_commands.py)

**Status**: **FIXED** — `_allocate_ports` skips hash offset for `wrapper-singleton`.

**Root cause**: `task-orchestrator` is declared with `management_model: wrapper-singleton`,
meaning a single instance runs globally and manages per-repo state internally.  Its
port is fixed — there is no per-worktree isolation.  However, `dopemux mcp init`
applied the workspace hash offset anyway, generating `TASK_ORCHESTRATOR_HTTP_PORT=7895`
(offset `+5`) while the singleton was listening on `7890`.

**Fix applied**: The inner loop in `_allocate_ports` now checks
`management_model == "wrapper-singleton"` and, when true, uses `default_port_base`
directly (no `_port_for` hash call) for the primary port variable.  Extra port vars
are also skipped for wrapper-singletons.

**Workaround** (if you hit this in an existing workspace):
```bash
# In .envrc.dopemux-mcp, override back to the fixed port:
export TASK_ORCHESTRATOR_HTTP_PORT=7890
```

---

## Quick Diagnosis Checklist

If MCP servers are not connecting:

1. **Check transport type**: Is `.mcp.json` using `"type": "http"` for `dope-memory`
   and `task-orchestrator`?  (It should be.)

2. **Check port variables**: Source the envrc and verify ports are free:
   ```bash
   source .envrc.dopemux-mcp
   dopemux mcp doctor
   ```

3. **Probe the server directly** with the correct method:
   ```bash
   # Streamable HTTP
   curl -X POST http://localhost:$DOPE_MEMORY_PORT/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'

   # SSE
   curl -N -s http://localhost:$CONPORT_MCP_PORT/sse -H "Accept: text/event-stream"
   ```

4. **Tail container logs** during a connection attempt:
   ```bash
   docker logs -f dopemux-dope-memory-1 2>&1 | grep -i "mcp\|error\|exception"
   docker logs -f dopemux-task-orchestrator 2>&1 | grep -i "mcp\|error\|exception"
   ```

5. **Run the health report**:
   ```bash
   ./mcp_server_health_report.sh
   ```
