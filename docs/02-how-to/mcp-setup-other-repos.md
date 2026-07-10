---
id: mcp-setup-other-repos
title: Running Dopemux MCP Servers in Other Projects
type: how-to
owner: dopemux-infra
date: 2026-07-06
author: '@hu3mann'
last_review: '2026-07-09'
next_review: '2026-10-05'
prelude: Running Dopemux MCP Servers in Other Projects (how-to) for dopemux documentation
  and developer workflows.
---
# Running Dopemux MCP Servers in Other Projects

This guide explains how to connect `conport`, `dope-memory`, and `task-orchestrator`
MCP servers to any project — a new repo, a git worktree of another project, or a
plain directory — using **dopemux** (recommended) or carefully documented manual steps.

**Primary operator flow (safe):**

```bash
cd ~/code/your-other-project
dopemux mcp init
dopemux mcp repair-config --dry-run
dopemux mcp repair-config --apply
dopemux mcp start
source .envrc.dopemux-mcp
claude
dopemux mcp doctor
```

Target repos do **not** need their own `compose.yml`. `dopemux mcp start` is home-aware
(labeled sidecars + runtime registry). `doctor` / `status` load the target repo's
`.envrc.dopemux-mcp` and do not require compose in cwd.

> [!CAUTION]
> **UNSAFE_DOC_RECIPE_REMOVED.** Do **not** start another repo's MCP services by
> `cd`ing into `dopemux-mvp` and injecting that repo's env into `docker compose up`.
> That pattern can replace primary `mcp-conport` and bind the wrong `.dopemux` volume.
> Always use `dopemux mcp start --repo <target>` from the safe flow above.

---

## Prerequisites

1. **Shared infrastructure** (postgres, redis, etc.) is already running from the primary
   dopemux stack once. Sidecar start uses `--no-deps` and does not re-home those services.
2. **Docker is running**.
3. **Target workspace** is a git repository (`dopemux mcp init` requires git).
   If it is not a git repo yet, `git init` first.

---

## Part 1: Using Dopemux (Recommended)

### Step 1 — Navigate to your project

```bash
cd ~/code/your-other-project   # must be a git repo
```

### Step 2 — Initialise MCP config

```bash
dopemux mcp init
```

This command:
- Reads the catalog (`mcp_catalog.yaml` or bundled default)
- Generates `.mcp.json` with catalog-owned services (`conport`, `dope-memory`,
  `task-orchestrator`) using `${VAR}` placeholders
- Writes `.envrc.dopemux-mcp` with deterministic ports for this workspace path

> [!NOTE]
> **Port allocation (Packet 004):** preferred ports still use
> `base + sha1(path)[:4] % 100` (or existing envrc values), but assignment goes
> through the **lease registry** (`~/.dopemux/mcp/runtime/port-leases.json`).
> Reserved singletons, active foreign leases, and live TCP sockets force **rebind**
> to the next safe port. Override registry path with
> `DOPEMUX_MCP_PORT_LEASE_REGISTRY` (tests must never use the real home registry).
> `wrapper-singleton` services (e.g. `task-orchestrator` on `7890`) are fixed —
> free/same-project reuse or **block**, never rebind.

### Step 3 — Repair config (previewable)

```bash
dopemux mcp repair-config --dry-run --json   # plan only; writes nothing
dopemux mcp repair-config --apply            # local files only
```

What `repair-config` does:

- Fixes catalog-owned transport mismatches (e.g. dope-memory / task-orchestrator
  must be `"type": "http"`, conport stays `"sse"`)
- Regenerates or patches `.envrc.dopemux-mcp` using the same allocator as `init`
- Creates/updates `.claude/WORKTREE_MCP_SETUP.md` (agent bootstrap)
- **Preserves** unknown/custom `.mcp.json` entries
- **Never** mutates `~/.claude.json` (use `dopemux mcp sync-globals` explicitly)
- **Never** starts or stops containers

### Step 4 — Start sidecars (repo-aware reconciler)

```bash
dopemux mcp start
# or from any cwd:
dopemux mcp start --repo ~/code/your-other-project
dopemux mcp start --repo ~/code/your-other-project --dry-run --json
```

What `mcp start` does:

- Runs doctor preflight; **blocks** on transport mismatch, unlabeled port owners,
  wrong-project containers
- Generates compose override with **unique container names** and **absolute** target
  `.dopemux` volume
- Sets `dopemux.managed=true` + project labels
- Writes operational registry: `~/.dopemux/mcp/runtime/instances.json`
- Does **not** adopt unlabeled containers

```bash
dopemux mcp status --repo ~/code/your-other-project --json
dopemux mcp stop --repo ~/code/your-other-project
# Compatibility: mcp up/down --repo → start/stop
```

### Step 5 — Source env and verify

```bash
source .envrc.dopemux-mcp
# or: echo 'source .envrc.dopemux-mcp' >> .envrc && direnv allow

dopemux mcp doctor --repo ~/code/your-other-project
dopemux mcp status --repo ~/code/your-other-project
```

Ownership is proven by labels/registry/probes — not by "port is listening" alone.

### Step 6 — Open Claude Code (or agy)

```bash
claude    # Claude Code
# or
agy       # Antigravity CLI
```

Both clients read `.mcp.json` at session startup and expand `${VAR:-default}` from the
environment.

---

## Global singletons vs local project services

| Surface | Command | Mutates |
|---------|---------|---------|
| Local `.mcp.json` + `.envrc.dopemux-mcp` | `mcp init`, `mcp repair-config` | Target repo only |
| Global `~/.claude.json` singletons | `mcp sync-globals` (explicit `--apply`) | Home global config |
| Runtime containers | `mcp start` / `stop` / `status` | Docker + runtime registry |

`repair-config` does **not** call `sync-globals`. Keep local ConPort/dope-memory in the
target worktree; do not duplicate them into global config.

---

## Fleet / many worktrees

```bash
dopemux mcp fleet init --repo ~/code/your-project \
  --worktrees ~/code/your-project --worktrees ~/code/your-project-wt-feature \
  --dry-run --json

dopemux mcp fleet init --repo ~/code/your-project \
  --worktrees ~/code/your-project --worktrees ~/code/your-project-wt-feature \
  --apply

dopemux mcp fleet doctor --repo ~/code/your-project \
  --worktrees ~/code/your-project --worktrees ~/code/your-project-wt-feature \
  --json
```

Fleet commands never start containers and never modify `~/.claude.json`.

---

## Current limitations

* Preferred ports still derive from hash `%100` — leases rebind on conflict (no longer silent).
* `task-orchestrator` fixed port `7890` blocks multi-project simultaneous use when another
  project holds the lease (see RUNTIME-005 for deeper TO identity work).
* Unlabeled existing containers are not adopted automatically.
* Lease prune is not automatic; doctor may report `LEASE_STALE` without deleting.

---

## Part 2: Manual Setup (Without dopemux CLI)

Use this approach when you cannot or don't want to use `dopemux mcp init`, or when
you need to wire MCP into a non-git directory, a CI environment, or a vanilla
Claude Code project.

### Step 1 — Pick ports

Choose ports that don't collide with any running services.  Recommended ranges:
- `conport`: HTTP `304X`, MCP `304X+1`
- `dope-memory`: `306X`
- `task-orchestrator`: always `7890` (fixed singleton)

```bash
export CONPORT_HTTP_PORT=3044
export CONPORT_INFO_PORT=4044
export CONPORT_MCP_PORT=3045
export DOPE_MEMORY_PORT=3064
export TASK_ORCHESTRATOR_HTTP_PORT=7890
export DOPEMUX_WORKSPACE_ID=/Users/hue/code/your-other-project
export DOPE_MEMORY_WORKSPACE_ID=your-other-project   # short name
export DOPE_MEMORY_INSTANCE_ID=a3f2                  # any 4-char hash
```

Save these to `.envrc.dopemux-mcp` in your project root and `source` it.

### Step 2 — Start Docker services (prefer dopemux)

Prefer the reconciler even for partial manual setups:

```bash
# After .envrc.dopemux-mcp and .mcp.json exist:
dopemux mcp start --repo ~/code/your-other-project
```

> [!CAUTION]
> Do **not** start sidecars by injecting another project's env into
> `dopemux-mvp/compose.yml`. Use `dopemux mcp start --repo <target>` so
> container names, labels, and `.dopemux` volumes stay project-scoped.

### Step 3 — Write `.mcp.json`

Create this file in your **project root** (not in `dopemux-mvp`):

```json
{
  "mcpServers": {
    "conport": {
      "type": "sse",
      "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
      "env": {
        "DOPEMUX_WORKSPACE_ID": "${DOPEMUX_WORKSPACE_ID:-}"
      },
      "description": "Decisions, progress, knowledge graph (per-workspace)"
    },
    "dope-memory": {
      "type": "http",
      "url": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
      "env": {
        "DOPE_MEMORY_WORKSPACE_ID": "${DOPE_MEMORY_WORKSPACE_ID:-}",
        "DOPE_MEMORY_INSTANCE_ID": "${DOPE_MEMORY_INSTANCE_ID:-}"
      },
      "description": "Temporal chronicle (per-workspace)"
    },
    "task-orchestrator": {
      "type": "http",
      "url": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
      "env": {
        "TASK_ORCHESTRATOR_PROJECT_ROOT": "${TASK_ORCHESTRATOR_PROJECT_ROOT:-}",
        "TASK_ORCHESTRATOR_HTTP_PORT": "${TASK_ORCHESTRATOR_HTTP_PORT:-7890}"
      },
      "description": "Task orchestrator (singleton, repo-scoped SQLite)"
    }
  }
}
```

> [!IMPORTANT]
> **Transport types are critical:**
> - `"type": "http"` means **Streamable HTTP** — client sends JSON-RPC POST requests
> - `"type": "sse"` means **Server-Sent Events** — client opens a GET event stream
>
> Do **not** switch `dope-memory` or `task-orchestrator` to `"type": "sse"` — they
> speak Streamable HTTP.  Getting a `406 Not Acceptable` on a GET probe is **correct**
> behaviour, not a bug.

### Step 4 — Test connectivity

```bash
source .envrc.dopemux-mcp

# Test dope-memory (Streamable HTTP — must POST):
curl -X POST http://localhost:$DOPE_MEMORY_PORT/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'

# Test conport (SSE — must GET with event-stream header):
curl -N -s http://localhost:$CONPORT_MCP_PORT/sse \
  -H "Accept: text/event-stream" &
sleep 1 && kill %1   # should print event: endpoint

# Test task-orchestrator (Streamable HTTP):
curl -X POST http://127.0.0.1:$TASK_ORCHESTRATOR_HTTP_PORT/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

---

## Part 3: Running in Vanilla Claude Code (no dopemux)

If you are using plain Claude Code without any dopemux tooling:

1. Write the `.mcp.json` manually (see Part 2, Step 3).
2. Set your environment variables in your shell profile or `.env`:
   ```bash
   export CONPORT_MCP_PORT=3045
   export DOPE_MEMORY_PORT=3064
   export TASK_ORCHESTRATOR_HTTP_PORT=7890
   export DOPEMUX_WORKSPACE_ID="$(pwd)"
   export DOPE_MEMORY_WORKSPACE_ID="$(basename $(pwd))"
   ```
3. Make sure the Docker sidecars are running via `dopemux mcp start --repo .`
   (see Part 2, Step 2).
4. Launch `claude` from the project directory — it reads `.mcp.json` at startup.
5. Verify with `/mcp` in the Claude Code session.

### Singleton singletons (already running)

If `pal`, `serena`, or `dope-context` are running as singletons in your global
`~/.claude.json`, they are available in any project automatically — no per-project
configuration needed.  Run:

```bash
dopemux mcp sync-globals --apply   # adds singletons to ~/.claude.json
```

Or add them manually to `~/.claude.json`:
```json
{
  "mcpServers": {
    "pal":       { "type": "http", "url": "http://localhost:3003/mcp" },
    "serena":    { "type": "http", "url": "http://localhost:3006/mcp" },
    "dope-context": { "type": "http", "url": "http://localhost:3010/mcp" }
  }
}
```

---

## Troubleshooting

### `Connection refused` on startup

The container is not running on the expected port.

```bash
docker ps | grep dopemux-dope-memory    # check running
source .envrc.dopemux-mcp
echo $DOPE_MEMORY_PORT                  # verify port var is set
docker logs dopemux-dope-memory-1       # inspect startup logs
```

### `406 Not Acceptable: Client must accept text/event-stream`

You (or your client) sent a **GET** to a Streamable HTTP endpoint.  This is the
**correct** server response; the fix is to send a **POST** with a JSON-RPC body.
Check that `.mcp.json` uses `"type": "http"`, not `"type": "sse"`, for `dope-memory`
and `task-orchestrator`.

### Port collision on `dopemux mcp init`

```
Internal port collision: conport.CONPORT_HTTP_PORT and singleton:gpt-researcher both map to :3009
```

This means the workspace hash offset landed on a singleton's reserved port.  The
new version of `_allocate_ports` detects this and raises an error instead of
silently colliding.  Fix: adjust `default_port_base` for the conflicting service
in `mcp_catalog.yaml`, or use a workspace path that produces a different hash.

### `task-orchestrator` never connects

1. Verify the singleton is running: `docker ps | grep task-orchestrator`
2. Verify the port is **not** hash-offset: `echo $TASK_ORCHESTRATOR_HTTP_PORT`
   — it should always be `7890`, never `7890+N`.
3. Re-run `dopemux mcp init --force` with the fixed dopemux version.

### Session starts but tools show as unavailable

Source the env file *before* starting Claude Code:
```bash
source .envrc.dopemux-mcp && claude
```

Claude Code expands `${VAR:-default}` from the **shell environment** at session
startup.  If the vars are not set, it uses the defaults (which may not match the
running containers).

---

## Reference: Port Layout

| Variable | Default | Notes |
|---|---|---|
| `CONPORT_HTTP_PORT` | `3004` | Conport REST/health |
| `CONPORT_INFO_PORT` | `4004` | Conport info page |
| `CONPORT_MCP_PORT`  | `3005` | Conport SSE endpoint `/sse` |
| `DOPE_MEMORY_PORT`  | `3020` | Dope-memory Streamable HTTP `/mcp` |
| `TASK_ORCHESTRATOR_HTTP_PORT` | `7890` | **Always fixed** (wrapper-singleton) |
| `pal`               | `3003` | Singleton, static |
| `serena`            | `3006` | Singleton, static |
| `dope-context`      | `3010` | Singleton, static |
| `desktop-commander` | `3012` | Singleton, static (SSE) |

Per-worktree ports are offset by `sha1(workspace_path)[:4] % 100` from their base.
The `task-orchestrator` default is always `7890` with no offset.

---

**Last updated**: 2026-07-06
**See also**: [mcp-transport-and-port-bugs.md](mcp-transport-and-port-bugs.md) · [mcp-troubleshooting.md](mcp-troubleshooting.md)
