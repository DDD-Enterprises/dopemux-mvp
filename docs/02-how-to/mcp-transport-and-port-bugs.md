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
>
> **Port leases (TP-DMX-MCP-RUNTIME-004):** hash offsets are *preferred* only.
> Assignment uses `~/.dopemux/mcp/runtime/port-leases.json` (override
> `DOPEMUX_MCP_PORT_LEASE_REGISTRY`), reserved singleton protection, live TCP
> probes, and rebind when preferred ports are unsafe. Dry-run / `persist=False`
> never write leases. Fixed-port `task-orchestrator` (7890) reuses or blocks —
> it does not rebind.
>
> >
> **006R remediation:** Task Orchestrator port `7890` is a **reserved host singleton**
> (never project-leased). Invalid fixture leases on reserved ports are reconciled via
> `dopemux mcp leases reconcile --apply`. Doctor recognizes compose-project sidecars
> (e.g. `mcp-conport_dnh_crm_*`) and **refuses** main-stack dope-memory when target is
> another repo. Upstream TO jar has no REST `/info`/`/health` — use container name,
> data path, labels, and MCP transport.
>
> **TO identity (TP-DMX-MCP-RUNTIME-005):** prove project ownership of `:7890`
> before treating TO as ready. Trust order: HTTP `/info` identity → Docker labels
> → runtime registry → wrapper metadata
> (`~/.dopemux/mcp/runtime/<id>/task-orchestrator.identity.json`). Port-only
> is UNKNOWN. Wrong project blocks start; foreign runtimes are never stopped.

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

## Bug 4: Compose required-variable guard breaks mcp up/start from a clean shell (Fixed in docker_runtime.py / mcp_commands.py)

**Status**: **FIXED** in W01 of MACRO-DMX-MCP-LIFECYCLE-REPAIR-001 (commit `6895e8d4e`).
The guard itself came from commit `0994ce8a0` (2026-09-04), which made the
dope-context workspace mount read-only and fail-closed. Source audit:
`docs/05-audit-reports/dopemux-cross-repo-readiness-audit-2026-10-16.md`, section 6.

**Symptom**: From a shell where `HOST_CODE_PARENT_DIR` is not exported, `dopemux mcp`
lifecycle commands fail before any container starts:
```text
required variable HOST_CODE_PARENT_DIR is missing a value
MCP start: FAIL — conport: failed
```

**Cause**: `compose.yml` line 423 marks the dope-context mount source as required
(`${HOST_CODE_PARENT_DIR:?...}`), and lines 406-408 interpolate
`HOST_CODE_PARENT_DIR` and `HOST_PROJECT_RELATIVE_PATH`. Compose interpolates the
whole file for any single-service command, so one unset variable fails `conport`
and every other service too. Before W01 the lifecycle passed only `os.environ` plus
the parse-only `DOPECON_BRIDGE_TOKEN` placeholder (`env_with_compose_interpolation`),
so the two host-path variables were missing unless the operator had exported them.

**Fix**: `env_with_compose_interpolation()` in `src/dopemux/mcp/docker_runtime.py`
now derives `HOST_CODE_PARENT_DIR` (the parent of the checkout) and
`HOST_PROJECT_RELATIVE_PATH` (the checkout directory name) from `product_root()`
when they are unset or blank. A non-blank operator value always wins. If the
product root cannot be found, both stay unset and compose still fails closed.
Every `docker compose -f compose.yml` call in `src/dopemux/commands/mcp_commands.py`
passes this env. Call sites that can start `dope-context` disable the derived
defaults (`host_path_defaults=False`), so the dope-context mount source is never
supplied silently. Those paths still need the variable set explicitly.

Raw `docker compose` does not derive anything. It still needs both variables
exported (see `.env.example`). On checkouts that predate W01, prefix them on the one
command. Use placeholders, not real paths:
```bash
HOST_CODE_PARENT_DIR=<parent of checkouts> HOST_PROJECT_RELATIVE_PATH=<checkout dir name> dopemux mcp start --repo <checkout>
```

**Verify**:
```bash
# Drift gate for the compose required-variable set (run from the repo root)
.venv/bin/python -m pytest tests/arch/test_compose_required_vars.py

# Raw compose from a shell without the variables still fails closed (read-only)
env -u HOST_CODE_PARENT_DIR -u HOST_PROJECT_RELATIVE_PATH docker compose -f compose.yml config postgres
```
The first command should pass. The second should fail with the
`required variable ... is missing a value` message, which shows the guard is still
in place for raw compose. It should succeed once both variables are exported.

---

## Bug 5: Stale running entries in instances.json had no reconcile path (Fixed: dopemux mcp registry reconcile)

**Status**: **FIXED** in W02 of MACRO-DMX-MCP-LIFECYCLE-REPAIR-001 (commit `1f8498a7b`).

**Symptom**: `instances.json` (the MCP runtime registry) keeps entries with status
`running` after their containers are gone, so the registry reports instances as
running when they are not.

**Cause**: Nothing reconciled the registry against Docker. `mcp status --repo` never
writes the registry. `mcp stop` marks an entry stopped only after an actual
`docker stop`. `mcp leases reconcile` covers port leases only. No supported command
cleared entries whose containers had exited on their own, for example after a host
restart or manual container removal.

**Fix**: `RuntimeRegistry.find_stale_running()` and `reconcile_stale_running()` in
`src/dopemux/mcp/runtime_registry.py`, exposed as
`dopemux mcp registry reconcile --dry-run | --apply [--json]`:
- Lists `running` entries whose containers are absent from `docker ps`.
- `--apply` first copies the registry to `instances.json.backup-<UTC stamp>`, then
  marks each stale entry `stopped` with a `NOT_RUNNING` probe record.
- Entries are never deleted, and containers are never touched.
- Fails closed when the registry is unreadable or Docker is unavailable.
- `--apply` rewrites `instances.json` without a cross-process lock. Never run it
  concurrently with `dopemux mcp start/stop/restart/up/down` or another reconcile.

```bash
dopemux mcp registry reconcile --dry-run   # plan only, writes nothing
dopemux mcp registry reconcile --apply     # backs up first, then marks stale entries stopped
```

**Verify**:
```bash
dopemux mcp registry reconcile --dry-run --json   # review the plan
# after --apply, an instances.json.backup-<UTC stamp> file sits beside the registry
.venv/bin/python -m pytest tests/unit/test_mcp_runtime_registry.py tests/unit/test_mcp_commands_lifecycle.py
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

6. **Compose reports a missing host-path variable** (`required variable HOST_CODE_PARENT_DIR
   is missing a value`): run `dopemux mcp` from the checkout so the variables are derived,
   or export them for raw `docker compose`. See Bug 4.

7. **Registry shows `running` for containers that are gone**: run
   `dopemux mcp registry reconcile --dry-run`, then `--apply` only when no lifecycle
   command is running. See Bug 5.
