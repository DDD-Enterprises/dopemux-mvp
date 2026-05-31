---
id: manage-mcp-servers
title: Manage MCP Servers (Global Singletons + Project/Worktree Instances)
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-06'
last_review: '2026-05-06'
next_review: '2026-08-06'
prelude: How to declare MCP servers once globally, scaffold worktree configs in seconds via `dopemux mcp init`, and keep global and local MCP launch surfaces in sync with the catalog.
---

# Manage MCP Servers

Dopemux MCP servers split into three operational categories:

- **Singletons** — stateless, workspace-independent. One running instance is shared across every project and every worktree. Declared in `~/.claude.json` `mcpServers`. Examples: `pal`, `serena`, `dope-context`, `desktop-commander`, `exa`, `gpt-researcher`, `MCP_DOCKER`.
- **Per-worktree** — stateful or workspace-scoped. Each worktree gets its own instance with its own port, container, and storage volume. Declared in `<worktree>/.mcp.json` with env-var-driven port allocation. Examples: `conport`, `dope-memory`.
- **Repo-scoped stdio** — launched from each worktree or Codex session, but backed by one durable state directory per local git repository. `task-orchestrator` uses this model.

The preferred source of truth is `mcp_catalog.yaml` at the repo root. If a repo does not have that file, `dopemux mcp` falls back to the bundled default catalog. Set `DOPEMUX_MCP_CATALOG=/path/to/mcp_catalog.yaml` to use an explicit catalog.

## Codex local availability

Codex does not read `~/.claude.json`, `~/.gemini/settings.json`, or Dopemux `.mcp.json` as active MCP configuration. For Codex, the local recovery surface is:

- `/Users/hue/plugins/dopemux-mission-control` - home-local Codex plugin with the PAL and Task Orchestrator MCP definitions.
- `~/.codex/config.toml` - direct `mcp_servers.pal` and `mcp_servers.task-orchestrator` entries so the tools are available even before plugin marketplace reload.

The validated Task Orchestrator MCP runtime for Codex is the current 13-tool upstream container launched by `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`. That script resolves the current local git repository and stores state under `~/.local/share/dopemux-mission-control/task-orchestrator/<repo-id>/current-tasks.db`.

The repo-owned distribution for that local plugin lives at `plugins/dopemux-mission-control/`. Use it as the source of truth for the local install at `/Users/hue/plugins/dopemux-mission-control`.

Codex may launch required MCP servers from a non-project process cwd and without project-root env vars. The launcher therefore resolves roots in this order: explicit workspace/project env vars, current git cwd, explicit `TASK_ORCHESTRATOR_PROJECT_ROOT` / `DOPEMUX_PROJECT_ROOT`, then the active Codex session metadata cwd under `~/.codex/sessions`. The Codex session fallback is only a startup recovery path; it does not outrank explicit env or git cwd resolution.

Do not point Codex or generated config at `services/task-orchestrator/task_orchestrator/app.py`; that entrypoint is an unsupported runtime variant.

## Bootstrap a fresh worktree

```bash
git worktree add ../dopemux-feat-x feature/x
cd ../dopemux-feat-x
dopemux mcp init
```

`init` writes:

- `.mcp.json` — Claude Code reads this at session start; declares the local servers from the catalog defaults (`conport`, `dope-memory`, `task-orchestrator`).
- `.envrc.dopemux-mcp` — exports `DOPEMUX_WORKSPACE_ROOT`, `DOPEMUX_PROJECT_ROOT`, `TASK_ORCHESTRATOR_PROJECT_ROOT`, `DOPEMUX_INSTANCE_ID`, and `DOPEMUX_PORT_*` for worktree-scoped servers.

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

Open Claude Code in this directory; `/mcp` should list the singletons (from `~/.claude.json`) plus the local servers (from `.mcp.json`).

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

`task-orchestrator` is different: it is stdio and does not allocate a port. Its durable SQLite state key is derived from the local git repository common directory, so linked worktrees for one repository share one Task Orchestrator DB.

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
- Stdio Task Orchestrator can resolve its repo-scoped state directory with `--print-resolution`.
- Locally-declared servers are still present in the catalog (no orphaned entries).

If `doctor` reports an env var unset, you forgot to source `.envrc.dopemux-mcp` (or direnv hasn't reloaded).

If `doctor` reports `nothing listening on :PORT`, the container isn't running for this worktree. Check `dopemux mcp status`, then `dopemux mcp up`. If multiple worktrees both expect the same port (you'll see the conflict in `lsof -i :PORT`), the compose-side env-var mapping is missing — see the *Compose-side requirement* section.

If `doctor` reports a Task Orchestrator resolution failure, confirm the command exists and run:

```bash
/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution
```

That command does not start Docker; it only prints the resolved worktree root, project root, state id, data directory, and database path.

To exercise the Codex fallback specifically, run from a non-git directory with no task-orchestrator root env set:

```bash
cd /tmp
env -u TASK_ORCHESTRATOR_WORKSPACE_ROOT -u DOPEMUX_WORKSPACE_ROOT -u CODEX_WORKSPACE_ROOT -u CODEX_PROJECT_ROOT -u TASK_ORCHESTRATOR_PROJECT_ROOT -u DOPEMUX_PROJECT_ROOT \
  /Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution
```

## What's NOT touched

The `mcp-proxy-config.json` / `mcp-proxy-config.yaml` files at the repo root are **not** Claude Code config — they're a separate ingress registry for the Dopemux MCP proxy/gateway service. The `dopemux mcp` CLI does not read or write them.

PR #575's runtime fixes for `desktop-commander` (pinned `fastmcp==2.14.7`) and `gpt-researcher` (pinned `gpt-researcher==0.14.8`) live in the Dockerfiles under `docker/mcp-servers-source/` and are independent of this CLI.

The Compose service named `task-orchestrator` is the Dopemux FastAPI workflow service on port `8000`. It is not the same runtime as the upstream 13-tool stdio MCP Task Orchestrator launched for Codex and local MCP clients.
