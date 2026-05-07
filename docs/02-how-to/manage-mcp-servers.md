---
id: manage-mcp-servers
title: Manage MCP Servers (Global Singletons + Per-Worktree Instances)
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-06'
last_review: '2026-05-06'
next_review: '2026-08-06'
prelude: How to declare MCP servers once globally, scaffold per-worktree configs in seconds via `dopemux mcp init`, and keep `~/.claude.json` and `.mcp.json` in sync with the catalog.
---

# Manage MCP Servers

Dopemux MCP servers split into two categories:

- **Singletons** — stateless, workspace-independent. One running instance is shared across every project and every worktree. Declared in `~/.claude.json` `mcpServers`. Examples: `pal`, `serena`, `dope-context`, `desktop-commander`, `exa`, `gpt-researcher`, `MCP_DOCKER`.
- **Per-worktree** — stateful or workspace-scoped. Each worktree gets its own instance with its own port, container, and storage volume. Declared in `<worktree>/.mcp.json` with env-var-driven port allocation. Examples: `conport`, `dope-memory`, `task-orchestrator`.

The single source of truth for which server is which is `mcp_catalog.yaml` at the repo root. The `dopemux mcp` CLI reads it.

## Bootstrap a fresh worktree

```bash
git worktree add ../dopemux-feat-x feature/x
cd ../dopemux-feat-x
dopemux mcp init
```

`init` writes:

- `.mcp.json` — Claude Code reads this at session start; declares the per-worktree servers from the catalog defaults (`conport`, `dope-memory`, `task-orchestrator`).
- `.envrc.dopemux-mcp` — exports `DOPEMUX_WORKSPACE_ID`, `DOPEMUX_INSTANCE_ID`, and `DOPEMUX_PORT_*` for each per-worktree server.

Source the env file (one of):

```bash
# Option A — direnv users: source from your existing .envrc
echo 'source ./.envrc.dopemux-mcp' >> .envrc && direnv allow

# Option B — manual
source ./.envrc.dopemux-mcp
```

Start the per-worktree containers, then verify:

```bash
dopemux mcp up
dopemux mcp doctor
```

Open Claude Code in this directory; `/mcp` should list the singletons (from `~/.claude.json`) plus the per-worktree servers (from `.mcp.json`).

## Add or remove servers in a worktree

```bash
# Add a per-worktree server from the catalog
dopemux mcp add dope-memory

# Drop one
dopemux mcp remove task-orchestrator
```

`add` only accepts names declared `scope: per-worktree` in the catalog. To add a new singleton, edit `mcp_catalog.yaml` and run `dopemux mcp sync-globals --apply`.

## Reconcile global singletons

`sync-globals` compares the singletons in `mcp_catalog.yaml` against `~/.claude.json` `mcpServers` and shows the diff. By default it's a dry-run.

```bash
dopemux mcp sync-globals             # show planned changes
dopemux mcp sync-globals --apply     # write (creates a timestamped backup first)
```

Backups are written next to the original file as `~/.claude.json.backup-<UTC-timestamp>`.

## Inventory and inspection

```bash
dopemux mcp list
```

Shows three sections:

1. **Catalog** — every server defined in `mcp_catalog.yaml`, with scope and transport.
2. **Global** — what `~/.claude.json` `mcpServers` currently declares.
3. **Local** — what the current worktree's `.mcp.json` declares.

Servers that appear in both global and local are flagged as duplicates. Servers that appear in a config but not in the catalog are flagged "(not in catalog)" — usually a sign of drift to clean up.

## Port allocation

Per-worktree ports are deterministic:

```
port = default_port_base + (sha1(worktree_abspath)[:4]_hex % 100)
```

So the same worktree always gets the same port across reboots, and two different worktrees get different offsets within a 100-port window per service. `init` checks ports against `lsof` and reports `(free)` or `(in use)`.

If you ever hit a real collision (vanishingly rare in practice), bump `default_port_base` for the conflicting service in `mcp_catalog.yaml` by 100 and re-run `dopemux mcp init --force`.

## Compose-side requirement

For multiple worktrees to coexist with isolated container ports, `compose.yml` must publish the host port via the env vars set by `init` — for example:

```yaml
services:
  conport:
    ports:
      - "${DOPEMUX_PORT_CONPORT:-3005}:3005"
```

If `compose.yml` still has hardcoded port mappings, only one worktree can run that service at a time. This is tracked as a follow-up; the catalog and CLI are ready for it.

## Adding a new MCP server to the catalog

1. Edit `mcp_catalog.yaml`. Use this minimum shape:

   ```yaml
   servers:
     my-mcp:
       scope: singleton          # or per-worktree
       transport: http           # or sse / stdio
       url: "http://localhost:30NN/mcp"   # for http/sse
       # OR for stdio:
       # command: docker
       # args: ["exec", "-i", "container-name", "python", "/app/server.py"]
       requires_env: ["MY_API_KEY"]
       optional_env: ["OPTIONAL_THING"]
       description: "What this MCP does"
   ```

   For per-worktree entries, add `default_port_base: <int>` and `port_var: DOPEMUX_PORT_<NAME>`, and use `url_template` instead of `url` with `${DOPEMUX_PORT_<NAME>}` substitution.

2. If singleton: `dopemux mcp sync-globals --apply`.
3. If per-worktree: `dopemux mcp add my-mcp` in each worktree that needs it (or add to `defaults.per_worktree` so future `init` calls pick it up automatically).

## Troubleshooting

`dopemux mcp doctor` is the first stop. It checks:

- `.mcp.json` and `.envrc.dopemux-mcp` exist.
- Required env vars for each declared per-worktree server are set in the current shell.
- Allocated ports have something listening (i.e., the container is up).
- Locally-declared servers are still present in the catalog (no orphaned entries).

If `doctor` reports an env var unset, you forgot to source `.envrc.dopemux-mcp` (or direnv hasn't reloaded).

If `doctor` reports `nothing listening on :PORT`, the container isn't running for this worktree. Check `dopemux mcp status`, then `dopemux mcp up`. If multiple worktrees both expect the same port (you'll see the conflict in `lsof -i :PORT`), the compose-side env-var mapping is missing — see the *Compose-side requirement* section.

## What's NOT touched

The `mcp-proxy-config.json` / `mcp-proxy-config.yaml` files at the repo root are **not** Claude Code config — they're a separate ingress registry for the Dopemux MCP proxy/gateway service. The `dopemux mcp` CLI does not read or write them.

PR #575's runtime fixes for `desktop-commander` (pinned `fastmcp==2.14.7`) and `gpt-researcher` (pinned `gpt-researcher==0.14.8`) live in the Dockerfiles under `docker/mcp-servers-source/` and are independent of this CLI.
