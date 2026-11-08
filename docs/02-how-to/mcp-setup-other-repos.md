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
   `DOPEMUX_*` and `TASK_ORCHESTRATOR_*` variables and the env file are not used for it;
3. finds this worktree's running sidecar (registry record plus an MCP probe) and, if there
   is none, starts it through the same lifecycle that `dopemux mcp start` uses, under a
   per-worktree lock so two simultaneous launchers start it once;
4. writes an attach record, then proxies stdio to the sidecar (SSE for `conport`,
   Streamable HTTP for `dope-memory` and `task-orchestrator`; the backend transports are
   unchanged, only the client side is stdio). Before every backend connect, the first one
   included, and again right after each `initialize`, the proxy re-proves the backend's owner
   from Docker labels (see [Sidecar restarts](#sidecar-restarts)).

Refusals are one line `CODE: remedy` on stderr with exit code 3. A launcher stopped with
SIGTERM or SIGHUP still removes its attach record (exit 143 or 129).

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
current directory; any directory inside a checkout is accepted and normalized to its root). It:

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
- **The first launch from a dopemux checkout builds the images once.** There is one image per
  service and Dockerfile version, `dopemux-<service>:<key>`, where `<key>` hashes the
  dopemux-mvp checkout path and the service's Dockerfile bytes; it is shared by every worktree
  and project that runs the same dopemux checkout (one key per checkout path and Dockerfile
  version). So the first launch with that checkout (and the first after that Dockerfile
  changes) prints `LAUNCH_IMAGE_BUILDING` and exits while one detached build per service runs
  (about 2.5 minutes observed on 2026-11-05; the build log path is printed); later worktrees
  reuse the image. When the build finishes, run `/mcp reconnect all` in the session. Running
  `dopemux mcp init --repo <checkout>` first pre-builds them instead. Sidecar source edits
  that leave the Dockerfile unchanged need a [forced rebuild](#force-a-rebuild).

The launcher waits up to 25 s for a starting sidecar (`DOPEMUX_LAUNCH_WAIT`, or
`dopemux mcp launch --wait SECONDS`), inside Claude Code's 30 s MCP connect limit (`MCP_TIMEOUT` defaults to 30 s; Claude Code
environment-variable reference, read 2026-11-05). If that is exceeded it exits with `LAUNCH_WAIT_EXCEEDED`; run
`/mcp reconnect all`.

`claude mcp list` shows `CONNECTION_CLOSED` for a refused launcher (observed with Claude Code
2.1.318) and hides the stderr remedy. To see the code and remedy, run the launcher by hand from the checkout:

```bash
cd ~/code/your-project && dopemux mcp launch conport
```

(A successful run waits for an MCP client on stdin; the SDK's own INFO lines are kept off
stderr. Press Ctrl-C.)

### Launcher refusal codes

Each code is printed as one `CODE: remedy` line. `LAUNCH_IMAGE_BUILDING` first prints one more
line, `dopemux mcp launch: building <image>; log <path>` (or `... is still building (pid N);
log <path>` while a build runs).

| Code | Meaning and remedy |
|---|---|
| `LAUNCH_ROOT_NOT_GIT` | Working directory is not inside a git work tree. Start the session in a checkout. |
| `LAUNCH_MCP_JSON_NOT_MANAGED` | `.mcp.json` has no dopemux launcher entry for this server. Run `dopemux mcp repair-config --apply`. |
| `LAUNCH_SERVICE_UNKNOWN` | The name is not a launcher service in the catalog. Run `dopemux mcp doctor`. |
| `LAUNCH_CATALOG_INVALID` | The MCP catalog failed to load; the message names the problem. |
| `PROJECT_IDENTITY_UNKNOWN` | Git identity could not be resolved. Run `dopemux mcp doctor`. |
| `LAUNCH_IMAGE_BUILDING` | Image missing; one detached build of that service started (its pid is in `build-<service>.pid` in the worktree's runtime dir; a launch of the same service during that build starts no second one, and `conport` and `dope-memory` may build at the same time). Retry with `/mcp reconnect all` in a few minutes. |
| `LAUNCH_WAIT_EXCEEDED` | Sidecar still starting after the wait. Run `/mcp reconnect all`. |
| `LAUNCH_START_FAILED` | The lifecycle start failed; the line carries the tail of its stderr. Run `dopemux mcp doctor`. |
| `LAUNCH_BACKEND_PORT_UNKNOWN` | The start reported no port for the server, so the launcher refuses rather than guess the default port. Run `dopemux mcp doctor`. |
| `LAUNCH_IO_ERROR` | A file or lock under the runtime dir could not be written (disk full, permissions, a lock that never settled). Retry; run `dopemux mcp doctor` if it persists. |
| `LAUNCH_BACKEND_OWNER_CHANGED` | On a reconnect, the container publishing this worktree's `conport` or `dope-memory` port is not this worktree's (labels `dopemux.managed`, `dopemux.project_id`, `dopemux.worktree_hash`). Nothing was resent. Run `/mcp reconnect <name>`. |
| `LAUNCH_RECONNECT_GUARD_FAILED` | The reconnect owner check itself failed (for example Docker did not answer); treated as a refusal. Run `dopemux mcp doctor`, then `/mcp reconnect <name>`. |
| `TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT` | Another project owns `:7890`. Run `dopemux mcp switch-project` here. |
| `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER` | `:7890` is held by something that is not a labeled task-orchestrator container. Run `dopemux mcp doctor`. |

Lifecycle findings with severity FAIL print under their own code (for example
`CONPORT_TENANT_UNKNOWN_HISTORY`, `CONPORT_TENANT_GATE_FAILED`); others surface through
`LAUNCH_START_FAILED` or `dopemux mcp doctor`.

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
anything that is not a managed task-orchestrator container. It stops and removes the old
owner's container with `docker stop` and `docker rm` under the host-wide `:7890` lock, marks
that owner's runtime-registry entry `stopped`, and starts this project's orchestrator through
the lifecycle. A session still connected to the old owner gets
`TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT` on its next request instead of being served by
the new owner.

---

## Cleanup: `dopemux mcp reap`

Each connected launcher leaves an attach record under
`~/.dopemux/mcp/runtime/<slug>-<worktree-hash>/attached/`. A worktree's sidecars are reaped
when no launcher is attached **and** either its directory no longer exists or it has been idle
for 20 minutes since the last launcher detached, and never while a detached image build is
running in its runtime dir.

```bash
dopemux mcp reap                 # dry run (default): lists what would be reaped
dopemux mcp reap --apply         # stop and remove those containers, release leases, remove runtime dir
dopemux mcp reap --json          # machine-readable output (stdout is pure JSON)
```

Safety rules: containers are matched by `dopemux.managed`, `dopemux.project_id` and
`dopemux.worktree_hash` labels plus a runtime-registry entry; `project` and `singleton`
scope containers (the task-orchestrator, host singletons) are never touched.
A full `dopemux mcp stop` for a worktree also releases its leases and removes its runtime dir,
unless a launcher is still attached (then the dir stays and the stop warns).

Reaping also runs automatically, bounded and never as a daemon. "Throttled" means at most
once per 600 s, through `~/.dopemux/mcp/runtime/reap.last`:

| Trigger | Throttle | Candidates per run | `docker stop` grace | Per docker call | Deadline |
|---|---|---|---|---|---|
| `Stop` and `SubagentStop` hooks | throttled | at most 3 | `--time 5` | 20 s | 60 s |
| `SessionEnd` hook | none | 1 | `--time 3` | 10 s | 45 s |
| every launcher start | throttled | 1 | `--time 2` | 3 s | 8 s |

Automatic runs never wait on a lock and cap every docker call:

- Every docker call, the initial `docker ps -a` included, gets at most its per-call timeout
  and never more than the time left before the deadline. A timed-out `docker ps -a` skips
  the run.
- An instance whose lock is held (a launcher is attaching to it or starting it, or a CLI
  `start`, `restart` or `stop` holds it) is skipped as `locked`.
- The final registry and lease update waits at most 2 s (or the time left) for the
  registry lock. If it stays busy, the instance is skipped as `registry_busy`: its
  containers are already removed, its registry entries, leases and runtime dir are left
  as they were, and a later run finishes it as a state-only candidate (once it has been
  idle 20 minutes, or when the worktree is gone; a start of the worktree before that
  rewrites them).
- Under its lock each candidate is checked again, first pruning dead attach records (which
  can stamp `last_detach` from them); when it no longer qualifies there is no docker call and
  no other change: a launcher attached by then skips it as `attached`; otherwise it is
  skipped as `stale` when its worktree is present and it has not been idle for 20 minutes (a
  launcher that attached and left since the plan restarts that clock). Any candidate is also
  skipped as `stale` while a detached image build is running in its runtime dir, and a
  build-only runtime dir (below) when its worktree is back. A candidate with no container
  left (a state-only or build-only one) is skipped as `stale` when `docker ps -a` lists a
  container for it again (a start since the plan) or does not answer.

Skipped instances are retried at the next run. A run that could start none of its
candidates, or whose `docker ps -a` timed out, leaves the `reap.last` throttle as it was.
Only the explicit `dopemux mcp reap --apply` waits for locks. Reaping never removes
images (they are shared). `SessionEnd` hooks share a
1.5 s budget unless the hook sets `timeout` (Claude Code hooks and environment-variable
references, read 2026-11-05), so `.claude/settings.json` sets `"timeout": 60` on that hook entry
(`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` is the alternative). A reap interrupted after
`docker rm` is finished by the next run. On any run, a registry or lease save that fails (a
corrupt file is left as is) skips the instance as `state_error`: its containers are already
removed and its runtime dir stays. The runtime registry and the lease file are saved one after
the other with no rollback, so the one that saved is updated (with a corrupt lease file the
entries are still marked stopped) and the failing one stays as it was. A later run finishes
it as a state-only candidate (once it has been idle 20 minutes, or when the worktree is gone;
a corrupt file needs a person first); a start of the worktree before that rewrites the state.

**Kill switch for automatic reaping:** create the file
`~/.dopemux/mcp/runtime/reap.disabled`, or set `DOPEMUX_MCP_REAP=0` (also `off`/`false`).
The explicit `dopemux mcp reap --apply` ignores the kill switch and prints a note on stderr.

An instance with neither a `last_detach` file nor a dead attach record (one recorded by an
older launcher) is reaped only when its worktree path is missing. A launcher killed outright
(SIGKILL) leaves a dead attach record; the record's attach time (its mtime, which nothing
refreshes) counts as the last detach, so the instance still goes idle, and when a later reap
or full `stop` prunes it, `last_detach` takes that time. A worktree
on an unmounted volume looks missing, so its sidecars get reaped; the next launch recreates
them. A removed worktree's runtime dir that a launcher created is reaped even when no sidecar
ever started (a launch that only built an image), because each launcher marks the dir with
`instance.json`. Such a dir is left while a detached image build may still be running, and
automatic runs see it only while the runtime registry lists at least one instance (no run sees
it while that registry file is missing or unreadable).

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
| (refused) `CONPORT_TENANT_UNKNOWN_HISTORY` | Postgres (or docker) did not answer, so whether the project has rows in the shared store is unknown. A start refuses `conport` with this FAIL and changes nothing; start `dopemux-postgres-age` or fix docker, then retry. |

`legacy_shared` is reported by `dopemux mcp doctor` as the WARN `CONPORT_LEGACY_SHARED_STORE`:
that project has no per-project wall yet, and moving its rows to a tenant is a later milestone
(M2). Nothing needs doing now. If Postgres does not answer, `doctor` reports the INFO
`CONPORT_TENANT_UNVERIFIED` and a start reports `CONPORT_TENANT_UNKNOWN_HISTORY`. `init` stops
with the same `FAIL CONPORT_TENANT_UNKNOWN_HISTORY` before building any image (the `.mcp.json`
it already wrote stays); start Postgres and run `init` again.

Provisioning never prints, logs or rotates a password. `CREATE ROLE` receives a SCRAM-SHA-256
verifier, not the password, so the plaintext never reaches Postgres or its log; only the
secrets file holds it, for the client. If a login role already exists but the
project has no secrets file, `init` fails closed with `ROLE_EXISTS_WITHOUT_SECRETS` and names
the secrets path to restore from backup. `CONPORT_TENANT_GATE_FAILED` also names the secrets
file. An interrupted provisioning resumes where it stopped on the next `init` or start.
A migration whose statements cannot be re-run (001, 002) and that committed before its
checkpoint was written (a kill, a failed state-file write) is detected from the object it
created and skipped; the re-runnable ones are simply replayed, which also completes one a
kill left half applied.

---

## The env file is informational

`.envrc.dopemux-mcp` is still written by `init`, so humans can read the ports and ids, and
**nothing you do needs it sourced**. dopemux reads it itself: `init`, `doctor` and each sidecar
start (including the one a launcher runs) take its ports, and the first ConPort tenant
resolution adopts legacy `CONPORT_DB_*` from it once (`legacy_envrc`). Identity never comes
from it. Credentials live in `~/.dopemux/mcp/projects/<project_id>/secrets.env`, not in the
repo (`git grep CONPORT_DB_` in a project set up this way finds nothing).

Ambient `DOPEMUX_WORKSPACE_ROOT`, `DOPEMUX_PROJECT_ROOT`, `DOPEMUX_INSTANCE_ID`,
`DOPEMUX_WORKSPACE_ID` and `TASK_ORCHESTRATOR_PROJECT_ROOT` are always ignored by `launch`,
and by `start`, `stop`, `restart`, `up --repo`, `status`, `doctor`, `init` and `repair-config`
unless you pass `--trust-env` to them (`launch` has no such option). `start`, `stop`,
`restart`, `up --repo` and `status` also drop ambient port, container-name and `CONPORT_DB_*`
exports before the lifecycle runs, so a lease is never beaten by another checkout's export.
A shell that still has another project's env file sourced therefore cannot redirect them.
`--trust-env` is meant for tests; no hook or launcher sets it.

The legacy cwd-compose forms (`dopemux mcp up|down|logs` without `--repo`) still run on your
shell environment; they are not part of this recipe.

---

## Sidecar restarts

If a backend sidecar restarts during a session, the proxy reconnects and resends the rejected
request once. While the backend refuses connections the proxy retries with backoff (0.25 s,
doubling, at most 2 s apart) for up to 10 s. A request that was in flight during the restart
gets an error and is not retried.

The proxy reconnects at most once per 60 s window: a later restart in the same session heals
too, but a backend that drops twice inside one window ends that proxy (exit 1); run
`/mcp reconnect <name>` (or `all`).

The proxy re-proves who owns the backend port from Docker labels at two checkpoints for
every backend session, the first one included: immediately before the connect, and right
after `initialize`, before any request is sent on that session. The launch-time check runs
under the host-wide `:7890` lock, which is released before the proxy starts, so a
`switch-project` from another project in between is caught at the first session too. The
task-orchestrator must still be this project's (`TASK_ORCHESTRATOR_START_BLOCKED_*`
otherwise), and `conport`/`dope-memory` must still be this worktree's
(`LAUNCH_BACKEND_OWNER_CHANGED` otherwise). On a refusal nothing is sent or resent on that
session, the waiting request (or, when the first session is refused, the runner's first
request) gets the `CODE: remedy` text as its error, the same line goes to stderr and the proxy
exits 1.

---

## Other commands you may still use

| Surface | Command | Mutates |
|---------|---------|---------|
| Local `.mcp.json` + `.envrc.dopemux-mcp` | `mcp init`, `mcp repair-config --dry-run` / `--apply` | Target repo only |
| Sidecars by hand | `mcp start`, `mcp stop`, `mcp restart` (each takes `--repo`, `--services`, `--dry-run`, `--json`, `--trust-env`); `mcp status` (`--repo`, `--json`, `--legacy-compose`, `--trust-env`) | Docker + runtime registry |
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
* A launcher killed with SIGKILL counts as detached at its attach time (the mtime of the dead
  attach record it leaves, which nothing refreshes), so once no other launcher is attached its
  instance can be reaped as idle 20 minutes after that time, even if the launcher ran longer.
* The first launch per dopemux checkout and Dockerfile version is a full image build; later
  worktrees and projects that run the same checkout reuse the shared image (one key per
  checkout path and Dockerfile version). A change to sidecar source code that leaves
  its Dockerfile alone is not picked up until you [force a rebuild](#force-a-rebuild).
* **The Copilot proxy config (`mcp-proxy-config.copilot.yaml`) is rendered but NOT_RUN /
  unverified**: `dopemux mcp generate` writes the launcher entries into it, and no Copilot
  session has been run against them.
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

The build is still running (the extra stderr line says `is still building (pid N)`), or it
failed. Read `~/.dopemux/mcp/runtime/<slug>-<worktree-hash>/build.log`.
`dopemux mcp init --repo <worktree>` builds synchronously and prints the failure.

### Force a rebuild

The image key covers the service's Dockerfile, not the rest of its source. After editing
sidecar code (for example under `docker/mcp-servers/conport/` or
`services/working-memory-assistant/`) without touching the Dockerfile, remove the image so
the next launch builds it again:

```bash
docker images 'dopemux-*'                 # lists dopemux-conport:<key>, dopemux-dope-memory:<key>
docker image rm dopemux-conport:<key>
```

The `<key>` is also printed by the launcher: `dopemux mcp launch conport` shows
`building dopemux-conport:<key>` (or `... is still building`) in its `LAUNCH_IMAGE_BUILDING`
output. Then run `/mcp reconnect all`: the launch prints `LAUNCH_IMAGE_BUILDING` while it
rebuilds, and the next reconnect after the build connects. `dopemux mcp init --repo <checkout>`
rebuilds synchronously instead.

Docker refuses to remove an image that a container was created from (running or stopped)
unless you add `--force`, which only removes the tag. Containers created from the old image
keep running it until they are recreated, for example with
`dopemux mcp restart --repo <checkout> --services conport` (not measured).

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

## Rollback

To go back to the pre-launcher setup (URL entries plus a sourced env file):

1. Put the old CLI back: `uv tool uninstall dopemux`, then install the older dopemux-mvp
   checkout (`uv tool install --editable <old checkout>`), or re-point `~/.local/bin/dopemux`
   at the old binary.
2. With that old tool, run `dopemux mcp repair-config --apply` in each project to turn the
   launcher entries in `.mcp.json` back into URL entries.
3. If the old flow must reach a tenant this version provisioned, copy the three `CONPORT_DB_*`
   lines from `~/.dopemux/mcp/projects/<project_id>/secrets.env` into the project's
   `.envrc.dopemux-mcp` by hand (never commit that file).
4. Keep `~/.dopemux/mcp/projects/*`. Deleting a project's secrets file while its login role
   exists makes the next provisioning fail closed with `ROLE_EXISTS_WITHOUT_SECRETS`.
5. The runtime registry (`instances.json`) and the lease registry (`port-leases.json`) keep
   their formats, so the old tool reads them as they are.
6. Delete `~/.dopemux/mcp/runtime/reap.disabled` only if you intend automatic reaping to run.

The shared `dopemux-<service>:<key>` images can stay; the old tool builds its own
per-project images next to them.

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
