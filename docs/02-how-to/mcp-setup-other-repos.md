---
id: mcp-setup-other-repos
title: Running Dopemux MCP Servers in Other Projects
type: how-to
owner: dopemux-infra
date: '2026-11-06'
author: '@hu3mann'
last_review: '2026-11-06'
next_review: '2027-02-04'
prelude: Running Dopemux MCP Servers in Other Projects (how-to) for dopemux documentation
  and developer workflows.
---
# Running Dopemux MCP Servers in Other Projects

This guide connects the `conport`, `dope-memory` and `task-orchestrator` MCP servers to any
git project: a new repo, another worktree of a project you already set up, or a worktree
that Claude Code made for you.

**The whole recipe.** Once per host, then once per new project. Nothing per worktree, and
nothing to source in a shell:

```bash
# once per host: install the CLI as an editable tool from your dopemux-mvp checkout
uv tool install --editable ~/code/dopemux-mvp

# once per new project
dopemux mcp init --repo ~/code/your-project     # tenant + images; writes .mcp.json
git -C ~/code/your-project add .mcp.json && git -C ~/code/your-project commit -m "chore: dopemux MCP launcher entries"

# every session, in any worktree of that project
cd ~/code/your-project            # or any worktree of it
claude
```

That is all. Every worktree of the project carries the same committed `.mcp.json`, so a
new `git worktree add` (or a worktree Claude Code creates) needs no setup command.

> [!CAUTION]
> **UNSAFE_DOC_RECIPE_REMOVED.** Do **not** start another repo's MCP services by
> `cd`ing into `dopemux-mvp` and injecting that repo's env into `docker compose up`.
> That pattern can replace primary `mcp-conport` and bind the wrong `.dopemux` volume.
> Let the launcher (or `dopemux mcp start --repo <target>`) start sidecars.

---

## How it works

`dopemux mcp init` renders each per-worktree server as a **stdio launcher entry**, not as a
URL:

```json
"conport": {
  "type": "stdio",
  "command": "${DOPEMUX_BIN:-dopemux}",
  "args": ["mcp", "launch", "conport"]
}
```

When the client connects, `dopemux mcp launch <name>`:

1. takes the git top-level of its working directory (Claude Code starts the child in the
   session directory, so that is the checkout you opened the session in) and refuses
   outside git, or when `.mcp.json` has no dopemux launcher entry for that server;
2. derives the identity (`project_id`, worktree hash) **from git only**; ambient
   `DOPEMUX_*` and `TASK_ORCHESTRATOR_*` variables and the env file are not read;
3. finds this worktree's running sidecar (registry record plus an MCP probe) and, if there
   is none, starts it through the same lifecycle that `dopemux mcp start` uses, under a
   per-worktree lock so two simultaneous launchers start it once;
4. writes an attach record, then proxies stdio to the sidecar (SSE for `conport`,
   Streamable HTTP for `dope-memory` and `task-orchestrator`; the backend transports are
   unchanged, only the client side is stdio).

Refusals are one line `CODE: remedy` on stderr with exit code 3.

### Host prerequisite: one stable `dopemux` on PATH

Every launcher entry runs `${DOPEMUX_BIN:-dopemux}`. The `dopemux` on PATH must be an
editable install of your dopemux-mvp checkout; a stale copy would break every project at
once. `dopemux mcp doctor` reports `DOPEMUX_BIN_NOT_EDITABLE` and prints the exact remedy,
`uv tool install --editable <your dopemux-mvp checkout>`. To point one session at a different
binary without editing the tracked `.mcp.json`, export `DOPEMUX_BIN=/path/to/dopemux`
before starting the client.

### Once per new project: `dopemux mcp init --repo <path>`

```bash
dopemux mcp init --repo ~/code/your-project
```

Run it from any directory; `--repo` names the target (default: the git checkout of the
current directory). It:

- writes `.mcp.json` with the launcher entries for the catalog's per-worktree servers
  (`--profile NAME` and `--with SERVER` adjust the set; it never selects "all");
- writes `.envrc.dopemux-mcp` for humans (see below);
- resolves or provisions the **ConPort tenant** and prints its source word (never the
  credentials);
- **pre-builds the `conport` and `dope-memory` images** synchronously, with a progress
  banner and a log at `~/.dopemux/mcp/runtime/<slug>-<worktree-hash>/build.log`; the
  build budget is `DOPEMUX_MCP_BUILD_TIMEOUT_SECS` (default 1800);
- never starts a container.

If `.envrc.dopemux-mcp` already exists, or `.mcp.json` exists and differs from the catalog
template, `init` stops and asks for `--force`. `--force` rewrites the files in the target checkout only and keeps any
`CONPORT_DB_*` lines it finds in the previous env file.

Commit `.mcp.json`. Do not commit `.envrc.dopemux-mcp`: it can carry `CONPORT_DB_*` values
preserved from an older setup.

### Every worktree and session: nothing to type

Open the session in the checkout, or let the runner make a worktree. The launchers run on
connect. Two things are expected the first time:

- **Approve the project servers once.** Claude Code asks once to approve the servers in a
  project's `.mcp.json`; a new project's servers show `Pending approval` in `claude mcp list`
  until the first interactive session approves them (observed). That is Claude Code's prompt,
  not a launcher failure.
- **A new worktree builds its images once.** Images are per compose project, so the first
  launch in a worktree with no image prints `LAUNCH_IMAGE_BUILDING` and exits while a
  detached build runs (about 2.5 minutes observed on 2026-11-05; the build log path is
  printed). When the build finishes, run `/mcp reconnect all` in the session. Running
  `dopemux mcp init --repo <worktree>` first pre-builds them instead.

The launcher waits up to 25 s for a starting sidecar (`DOPEMUX_LAUNCH_WAIT`, or
`dopemux mcp launch --wait SECONDS`), inside Claude Code's 30 s MCP connect limit (`MCP_TIMEOUT` defaults to 30 s; Claude Code
environment-variable reference, read 2026-11-05). If that is exceeded it exits with `LAUNCH_WAIT_EXCEEDED`; run
`/mcp reconnect all`.

`claude mcp list` shows `CONNECTION_CLOSED` for a refused launcher (observed with Claude Code
2.1.318) and hides the stderr remedy. To see the code and remedy, run the launcher by hand from the checkout:

```bash
cd ~/code/your-project && dopemux mcp launch conport
```

(A successful run waits for an MCP client on stdin and prints SDK telemetry lines on
stderr; both are harmless. Press Ctrl-C.)

### Launcher refusal codes

| Code | Meaning and remedy |
|---|---|
| `LAUNCH_ROOT_NOT_GIT` | Working directory is not inside a git work tree. Start the session in a checkout. |
| `LAUNCH_MCP_JSON_NOT_MANAGED` | `.mcp.json` has no dopemux launcher entry for this server. Run `dopemux mcp repair-config --apply`. |
| `LAUNCH_SERVICE_UNKNOWN` | The name is not a launcher service in the catalog. Run `dopemux mcp doctor`. |
| `LAUNCH_CATALOG_INVALID` | The MCP catalog failed to load; the message names the problem. |
| `PROJECT_IDENTITY_UNKNOWN` | Git identity could not be resolved. Run `dopemux mcp doctor`. |
| `LAUNCH_IMAGE_BUILDING` | Image missing; a detached build started. Retry with `/mcp reconnect all` in a few minutes. |
| `LAUNCH_WAIT_EXCEEDED` | Sidecar still starting after the wait. Run `/mcp reconnect all`. |
| `LAUNCH_START_FAILED` | The lifecycle start failed; the line carries the tail of its stderr. Run `dopemux mcp doctor`. |
| `TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT` | Another project owns `:7890`. Run `dopemux mcp switch-project` here. |
| `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER` | `:7890` is held by something that is not a labeled task-orchestrator container. Run `dopemux mcp doctor`. |

Lifecycle findings (for example `CONPORT_TENANT_GATE_FAILED`, `IMAGE_BUILD_FAILED`) can also
surface through `LAUNCH_START_FAILED` or `dopemux mcp doctor`.

---

## The task-orchestrator is one per host: `switch-project`

The task-orchestrator listens on the fixed port `7890`, and one project owns it at a time.
Ownership is proven from the Docker labels of the container that publishes `7890`, never from
"the port answers". A launcher in a project that does not own it refuses with
`TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT`; it never stops another project's
orchestrator. `conport` and `dope-memory` are unaffected.

To move the orchestrator to the project you are in:

```bash
dopemux mcp switch-project            # asks before stopping the current owner
dopemux mcp switch-project --yes      # no prompt
dopemux mcp switch-project --repo ~/code/other-project
```

Then run `/mcp reconnect all` in the session. The command refuses when `:7890` is held by
anything that is not a managed task-orchestrator container.

---

## Cleanup: `dopemux mcp reap`

Each connected launcher leaves an attach record under
`~/.dopemux/mcp/runtime/<slug>-<worktree-hash>/attached/`. A worktree's sidecars are reaped
when no launcher is attached **and** either its directory no longer exists or it has been idle
for 20 minutes since the last launcher detached.

```bash
dopemux mcp reap                 # dry run (default): lists what would be reaped
dopemux mcp reap --apply         # stop and remove those containers, release leases, remove runtime dir
dopemux mcp reap --json          # machine-readable output (stdout is pure JSON)
```

Safety rules: containers are matched by `dopemux.managed`, `dopemux.project_id` and
`dopemux.worktree_hash` labels plus a runtime-registry entry; `project` and `singleton`
scope containers (the task-orchestrator, host singletons) are never touched.
A full `dopemux mcp stop` for a worktree also releases its leases and removes its runtime dir.

Reaping also runs automatically, bounded and never as a daemon: at the `Stop` and
`SubagentStop` hooks (throttled to once per 600 s through
`~/.dopemux/mcp/runtime/reap.last`), at `SessionEnd` (unthrottled, at most one instance), and at
every launcher start (throttled the same way, at most one instance). Hook runs stop at most 3 candidates with
`docker stop --time 5`; the launcher stops at most 1 with `--time 3`. `SessionEnd` hooks share a
1.5 s budget unless the hook sets `timeout` (Claude Code hooks and environment-variable
references, read 2026-11-05), so `.claude/settings.json` sets `"timeout": 60` on that hook entry
(`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` is the alternative). A reap interrupted after
`docker rm` is finished by the next run.

**Kill switch for automatic reaping:** create the file
`~/.dopemux/mcp/runtime/reap.disabled`, or set `DOPEMUX_MCP_REAP=0` (also `off`/`false`).
The explicit `dopemux mcp reap --apply` ignores the kill switch and prints a note on stderr.

An instance recorded by an older launcher (no `last_detach` file) is reaped only when its
worktree path is missing. A worktree on an unmounted volume looks missing, so its sidecars
get reaped; the next launch recreates them.

---

## ConPort tenants

ConPort stores its data per project. On a project's first start, the credentials are resolved in
this order, and `init` prints which one applied:

| Source word | Meaning |
|---|---|
| `secrets` | Existing `~/.dopemux/mcp/projects/<project_id>/secrets.env` (mode 0600, directory 0700). |
| `legacy_envrc` | `CONPORT_DB_*` found in the checkout's `.envrc.dopemux-mcp` (or the main checkout's) were copied into the secrets file once. |
| `provisioned` | A new database and login role were created in the host Postgres (`CONNECT` revoked from `PUBLIC`), then the migration gate adopted the schema. |
| `legacy_shared` | The project already has rows in the shared `dopemux_knowledge_graph` store, so it keeps using it. |

`legacy_shared` is reported by `dopemux mcp doctor` as the WARN `CONPORT_LEGACY_SHARED_STORE`:
that project has no per-project wall yet, and moving its rows to a tenant is a later milestone
(M2). Nothing needs doing now. If Postgres does not answer, `doctor` reports
`CONPORT_TENANT_UNVERIFIED`.

Provisioning never prints, logs or rotates a password. If a login role already exists but the
project has no secrets file, `init` fails closed with `ROLE_EXISTS_WITHOUT_SECRETS` and names
the secrets path to restore from backup. `CONPORT_TENANT_GATE_FAILED` also names the secrets
file. An interrupted provisioning resumes where it stopped on the next `init` or start.

---

## The env file is informational

`.envrc.dopemux-mcp` is still written by `init`, so humans can read the ports and ids, but
**nothing you do needs it sourced** and the launcher ignores it. Credentials live in
`~/.dopemux/mcp/projects/<project_id>/secrets.env`, not in the repo (`git grep CONPORT_DB_`
in a project set up this way finds nothing).

Ambient `DOPEMUX_WORKSPACE_ROOT`, `DOPEMUX_PROJECT_ROOT`, `DOPEMUX_INSTANCE_ID`,
`DOPEMUX_WORKSPACE_ID` and `TASK_ORCHESTRATOR_PROJECT_ROOT` are ignored by `launch`, `start`,
`stop`, `status`, `doctor`, `init` and `repair-config`. A shell that still has another project's
env file sourced therefore cannot redirect them. The escape hatch is `--trust-env` on those
commands (meant for tests; no hook or launcher sets it).

The legacy cwd-compose forms (`dopemux mcp up|down|logs` without `--repo`) still run on your
shell environment; they are not part of this recipe.

---

## Sidecar restarts

If a backend sidecar restarts during a session, the proxy reconnects and resends the rejected
request once, so the first restart of a backend heals itself. A request that was in flight
during the restart gets an error and is not retried. A **second** restart of the same backend
in the same session ends that proxy; run `/mcp reconnect <name>` (or `all`).

---

## Other commands you may still use

| Surface | Command | Mutates |
|---------|---------|---------|
| Local `.mcp.json` + `.envrc.dopemux-mcp` | `mcp init`, `mcp repair-config --dry-run` / `--apply` | Target repo only |
| Sidecars by hand | `mcp start`, `mcp stop`, `mcp status` (each takes `--repo`, `--dry-run`, `--json`) | Docker + runtime registry |
| Orchestrator owner | `mcp switch-project` | The container on `:7890` |
| Idle or removed worktrees | `mcp reap` | Containers, leases, runtime dirs |
| Global `~/.claude.json` singletons | `mcp sync-globals` (explicit `--apply`) | Home global config |

`repair-config` repairs a hand-edited or pre-launcher `.mcp.json` back to the catalog shape,
preserves unknown custom entries, never starts or stops containers and never touches
`~/.claude.json`. It also writes a short agent note to `.claude/WORKTREE_MCP_SETUP.md` in the target repo. Target repos do not need their own `compose.yml`; `mcp start` is home-aware
(labeled sidecars plus the runtime registry at `~/.dopemux/mcp/runtime/instances.json`).

Notes for `mcp start`:

- It runs a doctor preflight and **blocks** on unlabeled port owners and wrong-project
  containers; it does not adopt unlabeled containers.
- `HOST_CODE_PARENT_DIR` / `HOST_PROJECT_RELATIVE_PATH` (required by `compose.yml`
  interpolation) default to the dopemux-mvp checkout's parent directory and basename when
  unset; explicit values are kept. Commands that can start `dope-context` (`mcp up` with it in
  the service set, `mcp start-all`, `mcp ensure --full`) do not apply the defaults, so its
  `/workspaces` mount still fails closed until you export both variables.
- A missing image is built before `up` (`IMAGE_MISSING_WILL_BUILD` in `--dry-run`). Budgets:
  `DOPEMUX_MCP_BUILD_TIMEOUT_SECS` (default 1800) and `DOPEMUX_MCP_UP_TIMEOUT_SECS`
  (default 180). A failed build stops that service before `up` (`IMAGE_BUILD_FAILED`).

> [!NOTE]
> **Port allocation:** preferred ports use `base + sha1(path)[:4] % 100`, but assignment goes
> through the **lease registry** (`~/.dopemux/mcp/runtime/port-leases.json`). Reserved
> singletons, active foreign leases and live TCP sockets force a **rebind** to the next safe
> port. Override the registry path with `DOPEMUX_MCP_PORT_LEASE_REGISTRY` (tests must never
> use the real home registry). `wrapper-singleton` services (`task-orchestrator` on `7890`)
> are fixed: free or same-project reuse, or **block**; never rebind.

Fleet commands plan many worktrees at once and never start containers or modify
`~/.claude.json`:

```bash
dopemux mcp fleet init --repo ~/code/your-project \
  --worktrees ~/code/your-project --worktrees ~/code/your-project-wt-feature --dry-run --json
dopemux mcp fleet doctor --repo ~/code/your-project \
  --worktrees ~/code/your-project --worktrees ~/code/your-project-wt-feature --json
```

---

## Current limitations (M1)

* **Mid-session `EnterWorktree` needs `/mcp reconnect all`.** MCP servers bind at session start.
  Entering a worktree mid-session keeps the original checkout's launchers until you run
  `/mcp reconnect all`; whether the reconnect then runs from the new directory was not
  measured (`claudedocs/mcp-launch-root-probe-2026-11-05.md`, case 4, NOT_RUN). A session
  opened in the worktree is the supported path.
* **One task-orchestrator per host.** Only one project owns `:7890`; others refuse until
  `dopemux mcp switch-project`. Serving two projects at once is a later milestone.
* **Worktrees on branches that predate the change keep URL entries** in their `.mcp.json`
  (needing the old env-var setup) until the branch takes the launcher change and you run
  `dopemux mcp repair-config --apply`.
* **Codex is not rendered.** The per-worktree servers are not written into `.codex/config.toml`,
  and whether Codex starts a stdio launcher in the right directory was not measured (NOT_RUN in
  the same probe). Do not rely on these launchers from Codex.
* **Cost: two sidecar containers per worktree** (`conport`, `dope-memory`) plus the one
  orchestrator, bounded by reap.
* A first launch in a new worktree is a full image build (images are per compose project).
* A project that already has rows in the shared ConPort store stays on it (`legacy_shared`).
* Preferred ports still derive from hash `%100`; leases rebind on conflict.
* Lease prune is not automatic; `doctor` may report `LEASE_STALE` without deleting.
* Unlabeled existing containers are never adopted.

---

## Manual setup and vanilla Claude Code (no dopemux CLI)

The launcher needs the dopemux CLI. Without it, the project servers cannot be started for you,
and you take on the work the launcher does:

1. Start the sidecars yourself (prefer `dopemux mcp start --repo <target>`; never inject another
   project's env into `dopemux-mvp/compose.yml`).
2. Write a URL-style `.mcp.json` (below) whose `${VAR:-default}` placeholders Claude Code expands
   from **the environment it was started with**, so export the ports in your shell profile or
   process manager before starting the client. The defaults only match containers on the
   default ports.
3. Check with `/mcp` in the session.

```json
{
  "mcpServers": {
    "conport": {
      "type": "sse",
      "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
      "description": "Decisions, progress, knowledge graph (per-workspace)"
    },
    "dope-memory": {
      "type": "http",
      "url": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
      "description": "Temporal chronicle (per-workspace)"
    },
    "task-orchestrator": {
      "type": "http",
      "url": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
      "description": "Task orchestrator (host singleton)"
    }
  }
}
```

> [!IMPORTANT]
> **Transport types are critical** for URL entries:
> - `"type": "http"` means **Streamable HTTP**: the client sends JSON-RPC POST requests.
> - `"type": "sse"` means **Server-Sent Events**: the client opens a GET event stream.
>
> Do **not** switch `dope-memory` or `task-orchestrator` to `"type": "sse"`. A `406 Not
> Acceptable` on a GET probe is **correct** behaviour, not a bug.

Probe the sidecars with the transport they speak (ports from `dopemux mcp status --json`):

```bash
# Streamable HTTP (dope-memory, task-orchestrator): must POST
curl -X POST http://localhost:$DOPE_MEMORY_PORT/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'

# SSE (conport): must GET with the event-stream header; expect `event: endpoint`
curl -N -s --max-time 2 http://localhost:$CONPORT_MCP_PORT/sse -H "Accept: text/event-stream"
```

### Global singletons (`pal`, `serena`, `dope-context`)

If these run as host singletons, add them to `~/.claude.json` once and every project sees them:

```bash
dopemux mcp sync-globals --apply
```

---

## Troubleshooting

### A server shows `CONNECTION_CLOSED` or "Pending approval"

"Pending approval" is Claude Code waiting for you to approve the project `.mcp.json` servers
once. `CONNECTION_CLOSED` means the launcher exited; run it by hand from the checkout to see
the `CODE: remedy` line (see the table above):

```bash
dopemux mcp launch conport
```

### `LAUNCH_IMAGE_BUILDING` again and again

The build is still running, or it failed. Read `~/.dopemux/mcp/runtime/<slug>-<worktree-hash>/build.log`.
`dopemux mcp init --repo <worktree>` builds synchronously and prints the failure.

### Sidecar running but the tools are missing

Run `/mcp reconnect all`. If the launcher exited because the orchestrator belongs to another
project, run `dopemux mcp switch-project` first.

### `406 Not Acceptable: Client must accept text/event-stream`

You (or your client) sent a **GET** to a Streamable HTTP endpoint. This is the **correct**
server response; send a **POST** with a JSON-RPC body instead.

### Port collision on `dopemux mcp init`

```
Internal port collision: conport.CONPORT_HTTP_PORT and singleton:gpt-researcher both map to :3009
```

The workspace hash offset landed on a singleton's reserved port. `_allocate_ports` raises
instead of silently colliding. Fix: adjust `default_port_base` for the conflicting service in
`mcp_catalog.yaml`, or use a workspace path that hashes differently.

### Debug sequence

`dopemux mcp doctor --repo <path>` (add `--json` for the full report) -> run the launcher by
hand -> probe the sidecar with the right transport -> `docker logs` the container
(`docker ps --format '{{.Names}}' | grep -E 'conport|dope-memory|task-orchestrator'`) ->
`./mcp_server_health_report.sh`.

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

Per-worktree ports are offset by `sha1(workspace_path)[:4] % 100` from their base and leased;
`mcp status --json` shows the ports actually in use. The `task-orchestrator` default is always
`7890` with no offset.

---

**Last updated**: 2026-11-06
**See also**: [mcp-transport-and-port-bugs.md](mcp-transport-and-port-bugs.md) · [mcp-troubleshooting.md](mcp-troubleshooting.md) · design `claudedocs/mcp-just-works-design-2026-11-05.md`
