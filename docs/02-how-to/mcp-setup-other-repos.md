---
id: mcp-setup-other-repos
title: Running Dopemux MCP Servers in Other Projects
type: how-to
owner: dopemux-infra
date: 2026-07-06
author: '@hu3mann'
last_review: '2026-07-07'
next_review: '2026-10-05'
prelude: Running Dopemux MCP Servers in Other Projects (how-to) for dopemux documentation
  and developer workflows.
---
# Running Dopemux MCP Servers in Other Projects

This guide explains how to connect `conport`, `dope-memory`, and `task-orchestrator`
MCP servers to any project — a new repo, a git worktree of another project, or a
plain directory — using **dopemux** or manually (for Claude Code / vanilla code use).

---

## Prerequisites

Before you begin, make sure:

1. **Dopemux services are running** (from the `dopemux-mvp` repo):
   ```bash
   cd ~/code/dopemux-mvp
   dopemux mcp up          # starts Docker Compose MCP stack
   # or for the full stack:
   dopemux mcp start-all
   ```

2. **Docker is running** and the MCP containers are healthy:
   ```bash
   docker ps | grep dopemux
   # or
   dopemux mcp status
   ```

3. **Your target workspace directory** is a git repository (required for `dopemux mcp init`).
   If it is not a git repo yet, `git init` first.

---

## Part 1: Using Dopemux (Recommended)

### Step 1 — Navigate to your project

```bash
cd ~/code/your-other-project   # must be a git repo
```

### Step 2 — Initialise MCP config for the workspace

```bash
dopemux mcp init
```

This command:
- Reads `mcp_catalog.yaml` from the `dopemux-mvp` repo
- Generates a `.mcp.json` in your project root with `conport`, `dope-memory`, and
  `task-orchestrator` entries using `${VAR}` placeholders
- Writes `.envrc.dopemux-mcp` with stable, collision-checked port numbers unique
  to this workspace path

Example output:
```
✅ Wrote .mcp.json
✅ Wrote .envrc.dopemux-mcp
Worktree:   /Users/hue/code/your-other-project
Instance:   a3f2
  CONPORT_HTTP_PORT=3044  (free)
  CONPORT_MCP_PORT=3045   (free)
  DOPE_MEMORY_PORT=3064   (free)
  TASK_ORCHESTRATOR_HTTP_PORT=7890  (wrapper-singleton, fixed)
```

> [!NOTE]
> **Port allocation is deterministic**: the same workspace path always gets the same
> ports.  `wrapper-singleton` services (like `task-orchestrator`) always use their
> fixed port regardless of workspace.

### Step 3 — Load the port variables into your shell

The quickest way is to source the file directly:
```bash
source .envrc.dopemux-mcp
```

Or, for persistent loading with `direnv`:
```bash
# Add to .envrc in your project
echo 'source .envrc.dopemux-mcp' >> .envrc
direnv allow
```

### Step 4 — Start per-worktree containers

> [!CAUTION]
> **Unsafe until Packet 002 (repo-aware start).** Injecting another project's
> `.envrc.dopemux-mcp` into `dopemux-mvp` compose is a known lifecycle hazard:
>
> 1. **Container name collision** — `compose.yml` defaults
>    `container_name: ${CONPORT_CONTAINER_NAME:-mcp-conport}`, so a foreign-repo
>    `up` can **replace** the primary ConPort container if the name is still default.
> 2. **dope-memory state bleed** — volume `./.dopemux:/data` is **relative to
>    compose cwd**. Starting dope-memory from `dopemux-mvp` binds
>    `dopemux-mvp/.dopemux`, not the target repo.
> 3. **Ownership is unproven** — a listening port is **not** proof the service
>    belongs to your project. Unlabeled containers are `UNKNOWN`, not healthy.
>
> Prefer diagnosing first. Do **not** treat `mcp init` as runtime isolation.

```bash
# Read-only truth gate (any cwd; does not start/stop containers):
dopemux mcp doctor --repo ~/code/your-other-project
dopemux mcp doctor --repo ~/code/your-other-project --json
```

Repo-aware `dopemux mcp start/up --repo` is **not** implemented yet (Packet 002).

<details>
<summary>Legacy / high-risk compose path (not recommended)</summary>

```bash
# From dopemux-mvp — DANGEROUS for foreign repos without unique names + absolute volumes:
cd ~/code/dopemux-mvp
env $(cat ~/code/your-other-project/.envrc.dopemux-mcp | grep -v '^#' | xargs) \
  docker compose -f compose.yml up -d conport dope-memory
```
</details>

### Step 5 — Verify connectivity

```bash
# Repo-aware doctor (loads target .envrc.dopemux-mcp; no container mutations):
dopemux mcp doctor --repo ~/code/your-other-project

# Full health report with transport-aware probing:
~/code/dopemux-mvp/mcp_server_health_report.sh
```

### Step 6 — Open Claude Code (or agy)

```bash
# In your project directory (with envrc sourced):
claude    # Claude Code
# or
agy       # Antigravity CLI
```

Both clients read `.mcp.json` at session startup. Claude Code expands the `${VAR:-default}`
placeholders using the environment; `agy` does the same.

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

### Step 2 — Start Docker services

From the `dopemux-mvp` directory:
```bash
cd ~/code/dopemux-mvp

# Start conport for your workspace
CONPORT_HTTP_PORT=3044 CONPORT_INFO_PORT=4044 CONPORT_MCP_PORT=3045 \
DOPEMUX_WORKSPACE_ID=/Users/hue/code/your-other-project \
  docker compose -f compose.yml up -d conport

# Start dope-memory for your workspace
DOPE_MEMORY_PORT=3064 \
DOPE_MEMORY_WORKSPACE_ID=your-other-project \
DOPE_MEMORY_INSTANCE_ID=a3f2 \
  docker compose -f compose.yml up -d dope-memory

# task-orchestrator is a singleton — start it once:
docker compose -f compose.yml up -d task-orchestrator
```

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
3. Make sure the Docker containers are running (see Part 2, Step 2).
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
