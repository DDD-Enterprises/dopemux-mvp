---
id: mcp-just-works-design-2026-11-05
title: Dopemux MCP "Just Works" Design — Milestone 1 (any checkout, zero typing)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-05'
last_review: '2026-11-05'
next_review: '2026-12-05'
status: APPROVED by owner 2026-11-05 ("approved"); D5 resolved as Option A on the author's recommendation; nothing built yet
prelude: Design for making dopemux MCP sidecars, identity, hooks and cleanup work in any checkout of any project (git-made or Claude-made worktrees, any shell) with zero typing, on today's interim fleet architecture. Written from the owner's brief ("I want everything to just work") after the 2026-11-04 multi-project / multi-worktree readiness audit. Milestone 2 (the ruled end state of the 2026-07-28 fleet design) is referenced, not designed here.
---
# ━━━◆ Ø ◆━━━

Status: written 2026-11-05 and APPROVED by the owner the same day (reply: "approved", after the §9 list and the D5 recommendation were presented; D5 therefore resolved as Option A). Not a plan: the plan is produced by `superpowers:writing-plans` and executed as a MacroPacket under AGENTS.md. No code, config, container, registry or lease was changed by writing this document. The document is untracked on a dirty `main`; committing it is the owner's call.

Inputs: `docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md` (the audit), `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md` (the accepted fleet design, "July design" below), Claude Code docs fetched 2026-11-05 (`mcp.md`, `hooks.md`, `worktrees.md`, `env-vars.md`, `settings-reference.md`), and the brainstorming conversation with the owner on 2026-11-05.

## 1. Intent and why

The owner's brief, verbatim: "i want everything to just work."

Concretely: open Claude Code, Codex or any other runner in any checkout, whether a fresh `git worktree add`, a worktree Claude Code created, or a repo that has been set up once, and `conport`, `dope-memory` and `task-orchestrator` are connected to the right instance, the lifecycle hooks run, and nothing had to be typed, sourced, copied or exported. When a worktree goes away, its containers and leases go with it.

Why now. The 2026-11-04 audit found that today a developer must follow seven manual rules (a specific binary with `--repo` every time, a clean shell, one command at a time, never `mcp init` in a worktree, hand-provisioned ConPort tenants, hand-delivered ports, manual teardown) and that four defects have no fix in flight: identity flips with the shell environment, `mcp init` targets the wrong checkout, no ports reach a session in a git-made worktree, and every lifecycle hook crashes in a linked worktree. The owner runs four projects with live sidecars and has 25 linked worktrees, none of which has working configuration.

Every one of the seven rules traces to one choice: identity and ports are delivered through the shell environment. Milestone 1 replaces that channel with a launcher that reads the checkout.

## 2. Milestones

| Milestone | What it delivers | Architecture | Status |
|---|---|---|---|
| **M1 (this document)** | Any checkout of any set-up project works with zero typing; a never-set-up project needs exactly one command; task-orchestrator refuses loudly when another project owns it | Today's interim classes: conport and dope-memory per worktree, one task-orchestrator on reserved port 7890, shared redis-events | Owner confirmed the split 2026-11-05 ("yes") |
| **M2** | The July design's ruled end state: one ConPort per project shared by its worktrees (P-18, P-19), one dope-memory per host (P-17), one task-orchestrator per project on a leased port (P-24, new ADR first), project-prefixed redis-events (P-21), shared serena (P-20) | End state | Not designed here; M1 must be a strict precursor of it, never a fork |

Two projects running `/dx:*` against their own task-orchestrator at the same time belongs to M2 (P-24). The owner agreed.

## 3. Goals, non-goals, anti-goals

### 3.1 Goals (M1)

- **G1 Zero typing in any checkout of a set-up project.** Git-made and Claude-made worktrees alike, from any shell, regardless of which `DOPEMUX_*` or `TASK_ORCHESTRATOR_*` variables happen to be exported.
- **G2 Identity from the checkout only.** Project from the git common dir, instance from the worktree path. Ambient environment never changes identity for any command.
- **G3 Find-or-start.** The launcher finds this checkout's healthy sidecars or starts them on demand with a visible cold-start notice and a bounded wait.
- **G4 Task-orchestrator is correct or refused.** Forward only when the running jar provably serves this project; otherwise the server fails to connect with a named reason and remedy, visible in the runner's MCP status. Never kill-and-replace.
- **G5 Hooks run in every worktree.** Including the DCP hard-deny guard and the health probes that fail open today.
- **G6 One command for a brand-new project.** `dopemux mcp init` run once from anywhere inside the repo, idempotent, safe to re-run, and it does everything (images, tenant, client config). After that, G1 applies.
- **G7 ConPort tenants provisioned automatically**, credentials kept outside the repo, legacy hand-made tenants adopted rather than replaced.
- **G8 Cleanup without a daemon.** A removed or idle worktree's sidecars are stopped and its leases released by the next reap pass, whichever session triggers it.
- **G9 Concurrency safe.** Two runners opening the same checkout at once, or two sessions in two worktrees, never corrupt the registries or double-start.

### 3.2 Non-goals (M1)

- **N1** Sharing one ConPort across worktrees, one dope-memory across the host, or one task-orchestrator per project. These are M2 (P-17, P-18, P-19, P-24).
- **N2** Project-prefixed redis-events (P-21). redis-events stays the shared stream it is today, with the contamination risk the July design records.
- **N3** Serena. No container exists today; M1 does not add one (P-20).
- **N4** `multi_project_singleton` for task-orchestrator. Ruled NOT authorized (July §10.1).
- **N5** Zero typing for a repo that has never been set up. One `dopemux mcp init` is the floor, because the runner needs a `.mcp.json` in that repo.
- **N6** Any always-running process. Reaping is hook-triggered (July §6.2).
- **N7** Changing MCP transports of the servers themselves. The launcher bridges; the containers keep SSE and streamable HTTP as they are.
- **N8** Automatic hand-off of the task-orchestrator between projects. Moving it is one typed command, `dopemux mcp switch-project`, until P-24 gives each project its own.

### 3.3 Anti-goals (a failure even if it works)

- **A1** Silently answering for the wrong project. The audit found 7890 held by dNh_CRM while dopemux-mvp sessions pointed at it.
- **A2** Starting containers for a directory that is not a dopemux-managed checkout.
- **A3** Touching another checkout's files. `mcp init --force` from a worktree rewriting main's config is the audit's defect 2.
- **A4** Credentials in tracked files, in prompts, or in the repo at all.
- **A5** Yanking a container out from under a connected session because an idle timer fired.
- **A6** A second allocation brain. `doctor` already warns `DUAL_ALLOCATION_BRAINS`; the launcher must call the existing lifecycle start path.

## 4. Constraints

- **C1 Governance.** Every slice is a MacroPacket child with a write allowlist, PR route, independent L3 audit and proof bundle (AGENTS.md §5, §9). Contract-sensitive surfaces touched: `.mcp.json` (rendered by the catalog; never hand-edited), `.claude/settings.json` hooks, `mcp_catalog`, hook scripts. Canonical-writer inspection before editing each.
- **C2 The July design is the authority for the end state.** M1 reuses its identity rules (P-02: project from git common dir), its resource policy (§6.2: on-demand start, hook-triggered reaping, no daemon), and its `init` rule (§7: `init` never mutates docker). Where M1 ships something the July design also specifies, M1 ships the July version, not a parallel one.
- **C3 All runners.** Logic lives in the dopemux CLI; per-runner adapters stay thin. A stdio launcher is the one MCP shape every runner supports (Codex: stdio and streamable HTTP only).
- **C4 Host facts.** Docker Desktop; one shared `dopemux-postgres-age`; reserved 7890 owned by whichever project started last; `main` is dirty (147 modified files), so work happens in `<repo>/.worktrees/`, where hooks crash until D6 lands. Interim for the builder: symlink main's `.venv` into the worktree (untested) or land D6 first.
- **C5 Claude Code facts (docs, 2026-11-05).** `WorktreeCreate` does not fire for `git worktree add` run through Bash, and configuring it replaces default creation and disables `.worktreeinclude`. `WorktreeRemove` fires only for hook-created worktrees. Whether a settings `env` block feeds `${VAR}` expansion in `.mcp.json` is undocumented. After entering a worktree, hook-input `cwd` is the worktree root while `CLAUDE_PROJECT_DIR` stays at the original root. MCP servers bind at session start; `/mcp reconnect all` exists (v2.1.284+). `SessionStart` hooks run before MCP servers are available and block the first response.
- **C6 Prerequisite PRs.** #1459 (pre-build sidecar images), #1456 (host-path env defaults, registry reconcile; mergeable UNKNOWN, so rebase or fold), #1439 (native-hooks register writes the event-keyed schema). All three are audited; merge is owner-gated.

## 5. Decisions

Each item below is decided for the builder. Items marked **(owner to check)** are the author's calls that the owner has not explicitly agreed to; see §9.

### D1 One stable `dopemux` on PATH **(owner to check)**

Install the CLI once as an editable uv tool from the dopemux-mvp checkout:

```bash
uv tool install --editable /Users/hue/code/dopemux-mvp
```

That makes `~/.local/bin/dopemux` always track the checkout, replacing today's symlink into a non-editable install under `~/.dopemux/venv` (35 commits stale at the audit, and without the MCP SDK). The `mcp` SDK moves from the optional `services` extra into the core `dependencies` of `pyproject.toml`, because the launcher is core CLI behaviour; `uv.lock` is regenerated in the same change. Every `.mcp.json` launcher entry and every hook dispatcher calls `dopemux` by name. `dopemux doctor` gains a check that the PATH binary is an editable install of a checkout at or after the current HEAD, with the exact remedy command. No other repo needs a venv.

Why: the launcher must run in repos that have no Python environment of their own, and the hooks defect is at root the same problem.

Blast radius and rollback. A stale or missing PATH binary would fail every launcher in every project at once, so: the renderer emits `"command": "${DOPEMUX_BIN:-dopemux}"` in `.mcp.json` (Claude Code expands `${VAR:-default}` in `command`) and the equivalent override in each other runner's rendered config as that format allows (the existing renderer already targets Codex and the Copilot proxy), giving an override without editing a tracked file; `init` and `doctor` verify the binary before anything else; rollback is reverting the renderer and regenerating, which restores today's URL entries. Worktrees on branches that predate the renderer change keep the URL form and stay in today's state until their branch takes the change; that is accepted, since they are no worse off than now.

### D2 The launcher

Every `.mcp.json` server entry rendered by the catalog becomes a stdio command:

```json
{ "type": "stdio", "command": "dopemux", "args": ["mcp", "launch", "conport"] }
```

The renderer (`src/dopemux/mcp/fleet_catalog.py` / `src/dopemux/mcp/mcp_json.py`) owns this change. `.mcp.json` stays tracked and identical in every checkout of a repo, which is what makes worktrees free.

`dopemux mcp launch <server>` does, in order:

1. **Root.** `--root <path>` if given, else the process working directory. Refuse (non-zero exit, one-line reason) if the root is not inside a git work tree or the repo's `.mcp.json` is not dopemux-rendered. (A2)
2. **Identity** per D3.
3. **Lock** per D7.
4. **Find-or-start** through the existing `lifecycle.py` start path, never a new one (A6), with the cold-start policy of D4.
5. **Attach record** per D8.
6. **Bridge** stdio to the sidecar with one mechanism for all three servers: a proxy built on the official `mcp` SDK (installed in the repo venv at 1.29; verified 2026-11-05 that `mcp.client.sse`, `mcp.client.streamable_http` and `mcp.server.stdio` import) that serves stdio to the runner and holds a client session to the sidecar. Client transport per server: SSE (`/sse`) for `conport`, streamable HTTP (`/mcp`) for `dope-memory` and `task-orchestrator`. Sessions, notifications and streamed responses are the SDK's job, not ours. `fastmcp` is pinned in `pyproject.toml` but is not installed in the default venv, so its `as_proxy` helper is not assumed; the builder may use it only if the dependency is made unconditional in the same packet.
   - The hand-rolled `src/dopemux/mcp/http_stdio_bridge.py` is not used by the launcher: it sends a single POST per line and cannot carry notifications, session ids or event-stream responses. It stays in place because `src/dopemux/config/manager.py:721` still renders it into the legacy docker-mode client config and a test asserts that; removing it is a separate cleanup.
   - The catalog gains a per-server client-shape field (`client: launcher`) on the three per-worktree entries, in both `mcp_catalog.yaml` and the packaged `src/dopemux/mcp/default_catalog.yaml` that other repos render from. `transport` and `url_template` keep describing the sidecar itself, which the launcher uses to build the backend URL from the leased port. The renderer emits the stdio launcher entry when `client: launcher` is set; `doctor`'s transport check and the `.mcp.json` repair planner compare the file against the client shape, not the sidecar transport, so a launcher entry is never a `TRANSPORT_MISMATCH`. The committed `.mcp.json` and `mcp-proxy-config.copilot.yaml` are regenerated in the same change because parity tests compare them byte for byte. Codex rendering is unchanged in M1: the per-worktree servers are not rendered into `.codex/config.toml` today, and adding them is outside this design.
   - **Ports come from leases, not the env file.** Today the lifecycle reads ports only from `.envrc.dopemux-mcp` and blocks with `ENVRC_MISSING` when it is absent, which is exactly a fresh worktree. The lifecycle resolves ports from the lease registry for `(project_id, worktree)` and, when none exist, allocates them with the same `port_allocator.allocate_ports` that `init` uses, under the registry lock. `ENVRC_MISSING` stops being a blocker. `init` still writes the env file for humans.
   - **Warm path.** A full `run_lifecycle` call runs a doctor pass and `docker ps` every time, which is seconds. The launcher first reads the registry entry for this worktree and service and probes the backend with an SDK `initialize`; if that succeeds it bridges at once. Only on failure does it take the lock and call the lifecycle start path.
   - No `docker exec`. The in-repo `docker/mcp-servers-source/conport/server.py` does run as a stdio FastMCP that proxies to the container's REST port, but it offers nothing the SDK proxy does not, needs a docker exec per session, and reads no per-session identity (it has no reference to `DOPEMUX_INSTANCE_ID`). `scripts/mcp-wrappers/conport-wrapper.sh` is not a model either: it launches the upstream `context-portal-mcp` package, a split-storage shadow twin that packets `DMX-MCPINT-HRD-CONPORTWRAP-005` and `DMX-FLEET-P0-005` already mark for repointing.
   - ConPort instance identity stays per container in M1, exactly as today. Per-request identity is P-18 (M2).
   - **Task-orchestrator ownership proof.** The MCP `initialize` handshake yields only `serverInfo.name` (`src/dopemux/mcp/task_orchestrator_identity.py:221-270`) and the upstream jar has no `/info` or `/health`, so the jar cannot prove which project it serves. The proof is the Docker labels on the container that publishes 7890, evaluated by the existing `task_orchestrator_identity.match_target` over `identity_from_docker_labels`: realpath equality of `dopemux.project_root` with this project's root plus the normalised `dopemux.project_id`, the same decision the lifecycle preflight already makes. `OK` forwards; `WRONG_PROJECT`, `UNKNOWN` and `CONFLICT` refuse. `dopemux.project_root` is the label the wrapper already writes and already keys its own refusal on (`task-orchestrator-http-singleton.sh:78-80, 207-210`); `dopemux.workspace_id` is the starter's worktree path and must not be used for the comparison. The lifecycle passes the wrapper a `project_root` equal to the git common dir parent, never a worktree path, so a jar started from any worktree is recognised by every checkout of that project; the audit found two worktree-labelled orchestrator identity files on disk, which is the failure this rule prevents. Registry entries and the wrapper's identity file are corroboration only, never proof. Mismatch, missing labels, or a listener that is not a labelled container all **refuse** (fail closed, per repo doctrine).
   - **Refusal shape.** The launcher exits non-zero with the existing finding codes and a remedy on stderr: `TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT <owner project_root>; run dopemux mcp switch-project here to take it over`, or `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER; run dopemux mcp doctor`. These are the codes the wrapper and `evaluate_fixed_port_state` already emit; no new names. The runner then shows the server as failed with that text, which is honest and needs no fake server. `conport` and `dope-memory` are unaffected.
   - **Who starts the jar.** When nothing listens on 7890 the launcher starts it through the existing lifecycle path (`task-orchestrator-http-singleton.sh`), the same as the other sidecars. It never kills, replaces, adopts or restarts another project's running jar (G4, A1, July §10.1). The wrapper's existing behaviour of replacing this same project's own container when its image, port or env has drifted is an upgrade path and stays. Moving the orchestrator between projects is the one typed command M1 keeps: `dopemux mcp switch-project`, implemented as the July §7 transitional command (stop the owner's jar through lifecycle, release, start this project's). This is consistent with the agreed split: two projects served at once is M2.

**Root resolution must be measured first.** `.mcp.json` is tracked and identical in every checkout, so it cannot carry a per-worktree `--root`; the launcher depends on the working directory each runner gives a stdio child. The first task of the launcher slice is a probe entry that records `cwd` and environment from Claude Code and Codex in a main checkout, a git-made worktree and a Claude-made worktree. If a runner uses a fixed directory, the renderer emits a per-runner `--root` argument from that runner's own variable (for Claude Code `${CLAUDE_PROJECT_DIR:-.}`, which the docs say is set in the server's environment), and the probe result is recorded in the packet.

The launcher never reads `.envrc.dopemux-mcp`, `.claude/settings.local.json` or ambient `DOPEMUX_*` variables.

### D3 Identity from git only

- `project_id` = `<slug>-<sha256(git common dir parent)[:16]>`, i.e. the July design's P-02 rule, as `ProjectIdentity.project_id` in `src/dopemux/mcp/project_identity.py:36-47` already computes it. (`src/dopemux/mcp/identity.py` is the registry-backed execution-identity resolver and by design never derives an id from cwd; it is not touched by M1.)
- `instance_id` = hash of the resolved worktree path. `workspace_id` = the worktree path.
- `HOST_CODE_PARENT_DIR` and `HOST_PROJECT_RELATIVE_PATH` are derived from the checkout path, never read from the environment.
- `launch`, `start`, `stop`, `up`, `down`, `doctor`, `status`, `init` and `repair-config` ignore ambient `DOPEMUX_WORKSPACE_ROOT`, `DOPEMUX_PROJECT_ROOT`, `DOPEMUX_INSTANCE_ID`, `DOPEMUX_WORKSPACE_ID` and `TASK_ORCHESTRATOR_PROJECT_ROOT`. One escape hatch, `--trust-env`, exists for tests and is never set by any hook or launcher. This retires the forced override in `src/dopemux/mcp/runtime_state.py:116-137` and the env-beats-git precedence in `src/dopemux/mcp/project_identity.py:122-129` (audit defect 1).
- `src/dopemux/worktree_commands.py:get_repo_root` becomes git-first (audit defect 2).
- `mcp init` gains `--repo`; `--force` touches only the target checkout and never removes credentials, because credentials no longer live in the repo (D5).

### D4 Cold-start policy **(owner to check)**

| Situation | Launcher behaviour |
|---|---|
| Sidecar healthy | bridge immediately (warm, well under the July §6.3 200 ms target) |
| Container exists, stopped, image present | start it, wait up to `DOPEMUX_LAUNCH_WAIT` (default 25 s, chosen to sit under the runner's MCP startup timeout; builder confirms Claude Code and Codex defaults), print progress lines to stderr, then bridge |
| Image absent | kick a detached build logged under the instance runtime dir, exit non-zero with "building <server> image, retry with /mcp reconnect in a few minutes". Never block the session on a multi-minute build |
| Wait exceeded | exit non-zero with "still starting, run /mcp reconnect all" |
| Foreign container on the lease port | exit non-zero with the ownership finding and the `doctor` remedy; never evict |

New project: `dopemux mcp init` is the one command (G6, N5). It pre-builds the two sidecar images synchronously with a progress banner (#1459), provisions the tenant (D5), renders `.mcp.json`, and never starts containers (July §7). After it, the first session's launchers do the cold start inside their wait budget.

### D5 ConPort tenants **(owner to check)**

On a project's first start the lifecycle resolves credentials in this order:

1. `~/.dopemux/mcp/projects/<project_id>/secrets.env` (mode 0600).
2. Else legacy `CONPORT_DB_*` in the checkout's `.envrc.dopemux-mcp`: copy them into (1) once, then proceed. This adopts the hand-made tenants of dNh_CRM, adOps and dopeClaw without touching their data.
3. Else provision a new database and login role with `CONNECT` revoked from `PUBLIC`, by porting `scripts/migration/provision_conport_project_db.sh` into the lifecycle. Order is psql-then-adopt, because the ConPort migration gate self-deadlocks on a fresh database when run gate-first. Administration happens the way the script does it today: `docker exec` into the `dopemux-postgres-age` container as the bootstrap superuser (`provision_conport_project_db.sh:110-118`). That ties provisioning to the host singleton's container name, which is already how the lifecycle finds it; no new credential is stored anywhere. The script's final "adopt" and "verify" steps run the migration gate inside a ConPort container, which does not exist yet for a new tenant, so provisioning is two phases: the database phase (role, database, extensions, schema and SQL migrations as the role) runs before the sidecar starts, and the gate phase runs by `docker exec` into this instance's own conport container once it is up. Re-running provisioning must never rotate a password that is already in the secrets file, and the password is never printed.

Double provisioning is prevented by the project-level lock (D7). Containers receive credentials through compose environment sourced from the secrets file. `.envrc.dopemux-mcp` is no longer read by any command; `init` may still generate it for humans with a header saying it is informational only, which also makes the direnv walk-up into nested worktrees harmless.

**Legacy history detection.** Today every unprovisioned project silently falls back to the shared `dopemux_knowledge_graph` database (`compose.yml` `CONPORT_DB_NAME` default). Before provisioning, the lifecycle counts rows for this project's workspace path in the shared database's workspace-scoped tables (the builder enumerates them from the sealed `schema.sql`), using the same superuser exec. Zero rows: provision a fresh tenant. Rows present: the project has history in the shared store and **keeps using the shared database in M1** (Option A, approved by the owner 2026-11-05 on the author's recommendation): the lifecycle records `CONPORT_LEGACY_SHARED_STORE` for that project, `doctor` reports it as WARN with the migration remedy, no project wall exists for it, and its rows move to a tenant in M2 (P-18 acceptance c). Nothing breaks on day one. The rejected alternative was to refuse ConPort for such projects until migrated.

Migrating or quarantining shared-store rows is M2.

### D6 Hooks in every worktree

`.claude/hooks/run_native_hooks.sh`:

- Derives the checkout from the hook JSON `cwd` field, not from `CLAUDE_PROJECT_DIR` (which stays at the original root after entering a worktree) and not from the script's own `git rev-parse --show-toplevel`.
- Resolves what to run in this order: if the checkout itself contains `src/dopemux/claude/native_hooks.py` (a dopemux-mvp checkout), run that file with the first interpreter found at `<checkout>/.venv/bin/python` or `<git common dir parent>/.venv/bin/python`, so in-repo hook changes apply in the checkout being edited; otherwise `dopemux native-hooks run` from `dopemux` on PATH, then `~/.local/bin/dopemux`; otherwise fail open with one stderr line and exit 0. Exit code 2 from the hook passes through unchanged. (`native-hooks run` is a new entry point: today the hook module is stdin-only with no CLI.)
- `native-hooks register` also registers `SubagentStart` (omitted today) and writes the event-keyed schema (#1439).
- Hook caches stay per checkout under `<checkout>/.claude/`.

### D7 Locks

- `flock` on `~/.dopemux/mcp/runtime/<slug>-<worktree_hash>/launch.lock` around find-or-start. That directory is the per-worktree runtime dir the lifecycle already uses for `mcp.env`, `compose.override.yml` and `start-plan.json`; "instance" in this document means that `(project_id, worktree_hash)` pair, not the per-service `dopemux.instance_id` label.
- `flock` on `~/.dopemux/mcp/runtime/registry.lock` around every read-modify-write of `port-leases.json` and `instances.json` (they are atomic-replace but unlocked today). Because a lifecycle start loads the registry before docker starts and saves after them, the lock must not span that window: the early load is read-only, and the registry is reloaded under the lock immediately before the final upserts and save, so concurrent starts merge instead of overwriting.
- `flock` on `~/.dopemux/mcp/projects/<project_id>/provision.lock` around D5.
- `flock` on `~/.dopemux/mcp/runtime/reserved-7890.lock`, host-wide, around the task-orchestrator check-then-start. The per-instance lock is the wrong granularity there: two worktrees of one project, or two projects, have different instance ids and would both see 7890 free and both start a jar. Under this lock the launcher uses a **start-only** path that refuses if anything foreign listens. `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh` already behaves that way for foreign owners (`refuse_foreign_port_owner`, "no docker rm foreign") and only removes its own project's stale containers before starting, so the launcher calls it as is. Stopping another project's jar happens only inside `switch-project`, through that project's lifecycle `stop`, never through the wrapper.

`fcntl.flock` on macOS and Linux only; Windows and network filesystems are out of scope for this host. This retires the "one command at a time" rule (G9).

### D8 Liveness and cleanup, reap-only **(owner to check)**

- Each launcher writes `~/.dopemux/mcp/runtime/<slug>-<worktree_hash>/attached/<pid>` on start and removes it on exit. Stale entries (pid gone) count as detached.
- **Reap rule**: an instance is reaped when it has zero live attachments AND (its worktree path no longer exists OR it has been idle at least 20 minutes since the last detach). Reaping stops the instance's sidecars, releases its leases and removes its runtime dir. Host singletons and the reserved task-orchestrator are never reaped by this rule.
- **Which containers belong to an instance** is decided by Docker labels, `dopemux.managed=true` with matching `dopemux.project_id` and `dopemux.worktree_hash`, listed with `docker ps -a --filter label=...` so stopped containers are seen too, joined with the registry entry, never by container name: `mcp-conport` and friends are the legacy default names from `compose.yml` and are not instance containers. A container without matching labels is never touched by reap.
- **Race with a starting launcher**: reap takes the instance's `launch.lock` (D7) and re-reads attachments under it before stopping anything; a launcher writes its attach record under the same lock before it starts containers. So a launcher mid-start is always visible to a concurrent reap.
- Reap runs at the `SessionEnd` hook, at the start of every launcher, and at the `Stop` hook throttled to once per 10 minutes per host through a timestamp file, because `Stop` fires at the end of every turn. It runs before the handlers' early returns. Bounded and lock-protected. Never a daemon (N6). The `WorktreeRemove` hook, when present, also triggers a reap, but nothing depends on it.
- Why not take over `WorktreeCreate`: it replaces Claude's creation behaviour and disables `.worktreeinclude`, and git-made worktrees never trigger it. Reap-only treats both kinds identically.
- Why attachments rather than an idle timer alone: a connected session is never cut off (A5).

### D9 Prerequisite PRs

Land #1459, #1456 (rebase or fold if it no longer merges) and #1439 before the launcher packet. #1440 (docs) follows M1's doc update. #1460 (test hygiene) is optional.

### D10 Documentation

AGENTS.md §12 and the "Setting up MCP in a new repo" block in `.claude/CLAUDE.md` change to the one-command recipe. `docs/02-how-to/mcp-setup-other-repos.md` is rewritten. `.claude/WORKTREE_MCP_SETUP.md` and the `.envrc` steps are retired. The audit report's §5 recipe is superseded by a pointer.

### D11 Known M1 limitation: mid-session worktree entry **(owner to check)**

MCP servers bind at session start. Entering a worktree mid-session with `EnterWorktree` keeps the original checkout's launchers until the user runs `/mcp reconnect all`, and the reconnect still runs in the session's original working directory unless the runner restarts the stdio command from the new one. The builder verifies which, and the docs state the result plainly. A session opened in the worktree is the supported path.

### D12 Interim cost

Two containers per worktree plus the shared task-orchestrator, bounded by D8. This is the July design's interim state and is accepted for M1.

## 6. Acceptance: what "just works" means, testably

All from a shell that has main's `.envrc.dopemux-mcp` sourced AND from a clean `env -i` shell; both must give identical results.

- **T1** Fresh `git worktree add` of dopemux-mvp, open a session: `conport`, `dope-memory` connect; identity is main's `project_id` with a distinct `instance_id`; nothing typed.
- **T2** Same for a worktree Claude Code created with `EnterWorktree` or `--worktree`.
- **T3** Same for Codex in the same worktree, concurrently with T1's session: one set of sidecars, no registry corruption, both sessions served.
- **T4** A never-set-up repo: `dopemux mcp init` once, then a session connects; its tenant database and role exist; its credentials are only under `~/.dopemux` with mode 0600; no `CONPORT_DB_*` in any repo file.
- **T5** A project with a hand-made tenant (dNh_CRM): first launch adopts the existing credentials and the existing data is visible; no new database was created.
- **T6** `task-orchestrator` owned by another project: the launcher exits with `TASK_ORCHESTRATOR_OWNED_BY_OTHER_PROJECT` naming the owner path, the runner shows the server as failed with that text, `conport` and `dope-memory` are connected, and the jar's container id is unchanged. Then `dopemux mcp switch-project` in this project followed by `/mcp reconnect all` connects it, and the other project's launcher now refuses in the same way.
- **T6b** Nothing on 7890: the launcher starts the jar through the lifecycle path and connects; a second launcher started concurrently does not start a second jar.
- **T7** Every lifecycle hook runs in T1's worktree: the DCP hard-deny guard blocks a red-lane edit; `hook_status.json` shows the events; no `ModuleNotFoundError`.
- **T8** Remove T1's worktree with `git worktree remove` and end the session: after the next reap, its containers are gone, its leases released, its runtime dir removed; main's sidecars untouched.
- **T9** `dopemux mcp init --force --repo <worktree>` changes nothing in main's checkout.
- **T10** Image absent: the launcher exits with the "building" message within 5 s, a build is running detached, and a later `/mcp reconnect all` connects.
- **T11** Two launchers started within 100 ms for the same stopped instance: exactly one start, both bridge.

## 7. Milestone 2 pointer

M2 is the July design's packet table (§9), run in this order because the owner runs several projects at once: P-24 (project-scoped task-orchestrator; ADR first), then P-17 and P-18 (fail-closed identity in dope-memory and ConPort), P-19 (flip the sharing classes), P-21 (redis-events), P-20 (serena), with the lifecycle packets P-05 through P-16 as the July critical path requires. M1's launcher, locks and reap are what P-08, P-09, P-10 and P-16 assume exist. Nothing in M1 may make M2 harder; the builder flags any such conflict as a stop condition.

## 8. Left to the builder

- The root-resolution probe and its result per runner (D2).
- Proxy construction details on the `mcp` SDK: client transport options, reconnect behaviour, how `initialize` from the runner maps onto the client session (D2).
- Exact wait, retry and timeout values, and the runner startup timeouts they must sit under (D4).
- Exact finding codes and messages, matching the existing taxonomy in `lifecycle.py` and `doctor.py`.
- Whether `launch` is a new subcommand on the `mcp` group or an extension of `ensure`; keep the `mcp_commands.py` convention.
- The secrets file format and how compose receives it (env file vs rendered overlay).
- Packet decomposition and order, test strategy per packet, and the proof bundles. Suggested slices: (1) hooks D6, (2) identity D3 plus `init --repo`, (3) launcher D2 with D4 and D7 plus `switch-project`, (4) tenants D5, (5) reap D8, (6) docs D10. Slices 1 and 2 are independent and start now; 3 depends on 2 and on #1459 and #1456, which are folded into slice 3 if they no longer merge cleanly rather than waited for; 4 and 5 depend on 3.
- Docs wording.

## 9. Calls the owner should check

These were decided by the author to keep the design complete; none was explicitly agreed in conversation.

**Resolved 2026-11-05:**

- **D5 legacy projects.** Keep a project with rows in the shared `dopemux_knowledge_graph` database working on that database in M1 with a `doctor` WARN (Option A). Owner replied "approved" to the document with this recommendation attached.

**Changed after that approval, later on 2026-11-05, from code facts surfaced by the builder check and three tracing lanes. These were not on screen when the owner approved and need the owner's confirmation before anything is built:**

- a. The `mcp` SDK moves from the optional `services` extra into core `dependencies`, with `uv.lock` regenerated (D1). Today's PATH binary is a non-editable install without the SDK.
- b. The catalog gains `client: launcher` on the three per-worktree entries, in both catalog files; `.mcp.json` and the Copilot proxy config are regenerated; the doctor transport check and repair planner compare against the client shape (D2). Without this every launcher entry is a blocking `TRANSPORT_MISMATCH`.
- c. The lifecycle resolves ports from leases and allocates them itself when a worktree has none; `ENVRC_MISSING` stops blocking (D2). Without this a fresh worktree can never start.
- d. The launcher has a warm path that reads the registry record and probes the backend before touching the lifecycle (D2).
- e. Orchestrator ownership uses the existing `match_target` over `dopemux.project_root` and `dopemux.project_id`, with the existing finding codes; the wrapper may still replace this same project's drifted container (D2).
- f. The hand-rolled bridge stays in place for the legacy config renderer; it is simply not used by the launcher (D2).
- g. Locks: a host-wide `reserved-7890.lock`; the registry is reloaded under lock just before the final save instead of locking across docker starts; lock and attach files live in the existing `<slug>-<worktree_hash>` runtime dir; reap joins on `dopemux.project_id` plus `dopemux.worktree_hash` over `docker ps -a` (D7, D8).
- h. The hook dispatcher runs a dopemux-mvp checkout's own hook file first, then the installed `dopemux native-hooks run`, a new entry point (D6).
- i. The `Stop` hook reap is throttled to once per 10 minutes; `SessionEnd` is not (D8).
- j. Provisioning is two-phase (database before the sidecar starts, migration gate inside the new container after), never rotates an existing password, and legacy detection uses the project root, its basename and all worktree paths as aliases (D5).
- k. Codex rendering of the per-worktree servers is unchanged in M1; the launcher reaches Claude Code and the Copilot proxy config (C3 narrowed).

**Author's calls, approved with the document on 2026-11-05:**

1. **D1** Install `dopemux` on PATH as an editable uv tool from the dopemux-mvp checkout, retiring the hand wrapper at `~/.local/bin/dopemux`; rendered command is `${DOPEMUX_BIN:-dopemux}`.
2. **D2** One proxy on the official `mcp` SDK for all three servers (SSE to conport, streamable HTTP to the others), retiring the hand-rolled bridge; no `docker exec`.
3. **D2** Task-orchestrator ownership is proven by the container's `dopemux.project_root` label and refused when unknown; the launcher may start the jar when 7890 is free but never replaces one; moving it between projects is the one typed command `dopemux mcp switch-project`.
4. **D4** Brand-new projects still need one `dopemux mcp init`; image builds are never run inside a session's launcher.
5. **D5** Tenants are created automatically in the shared Postgres on first start, by superuser exec into the postgres container as the existing script does; legacy hand-made tenants are adopted.
6. **D8** Cleanup is reap-only at session stop, driven by attached launchers plus a 20 minute idle window; no `WorktreeCreate` takeover.
7. **D11** Mid-session `EnterWorktree` is a documented limitation in M1.

## 10. References

- Audit: `docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md`
- Fleet design (accepted, supervisor rulings §10): `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md`
- Code: `src/dopemux/mcp/{runtime_state,project_identity,identity,lifecycle,docker_runtime,port_allocator,http_stdio_bridge,fleet_catalog,mcp_json}.py`, `src/dopemux/commands/mcp_commands.py`, `src/dopemux/worktree_commands.py`, `.claude/hooks/run_native_hooks.sh`, `scripts/mcp-wrappers/conport-wrapper.sh`, `scripts/migration/provision_conport_project_db.sh`, `compose.yml`
- PRs: #1459, #1456, #1439, #1440, #1460
- Claude Code docs (2026-11-05): `code.claude.com/docs/en/{mcp,hooks,worktrees,env-vars,settings-reference,settings}.md`

## Implementation amendments (2026-11-07)

Appended after the final whole-branch review of Milestone 1; the approved text above is unchanged. Where the two differ, this section records what was built.

- **T6 finding codes.** The launcher refuses a foreign orchestrator with `TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT` (the remedy names the owner path) and an unlabeled or unknown `:7890` owner with `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER`. Both are the lifecycle's existing codes (§9 e). `TASK_ORCHESTRATOR_OWNED_BY_OTHER_PROJECT` was not built.
- **Images are shared per service and Dockerfile version.** The image is `dopemux-<service>:<key>`, where `<key>` hashes the dopemux-mvp checkout path and the service's Dockerfile bytes. Every worktree and project that runs that checkout shares it (one key per checkout path and Dockerfile version); the compose override and a build-only override set it as `image:`. T1 holds for every later worktree of that checkout. The first launch per checkout and Dockerfile version still builds (`LAUNCH_IMAGE_BUILDING`, one detached build per service, guarded by `<runtime_dir>/build-<service>.pid`). Sidecar source edits that leave the Dockerfile unchanged need a forced rebuild (`docker image rm` the tag; recipe in the how-to). Reap never removes images.
- **T3 (Codex) is out of scope and NOT_RUN.** Per §9 k, the per-worktree servers are not rendered into Codex's config in M1, so T3 was not run.
- **`switch-project`.** It stops and removes the owner's orchestrator container with `docker stop` and `docker rm` under the reserved `:7890` lock, not through the lifecycle stop: the wrapper's data dir is a bind mount, so removing the container loses no data. It then marks the owner's runtime-registry entry `stopped` (registry lock inside the reserved lock) and starts this project's orchestrator through the lifecycle.
- **Reconnect guard.** Before every reconnect, never before the first session, the stdio proxy runs a guard that re-proves the backend's owner from Docker labels. For the task-orchestrator it repeats the launcher's owner verdict (`TASK_ORCHESTRATOR_START_BLOCKED_*`). For `conport` and `dope-memory`, the container publishing the backend port must carry `dopemux.managed=true` and this instance's `dopemux.project_id` and `dopemux.worktree_hash` (`LAUNCH_BACKEND_OWNER_CHANGED`). On a refusal nothing is resent, the waiting request gets `-32000 "<code>: <remedy>"`, the line goes to stderr and the proxy exits 1. A guard that fails for any other reason counts as a refusal (`LAUNCH_RECONNECT_GUARD_FAILED`).
- **Reconnect budget.** The proxy reconnects at most once per 60 s window, and retries a refusing backend with backoff (0.25 s doubling, capped at 2 s) for up to 10 s. A later restart in the same session heals; two drops inside one window end the proxy. Each request is still sent at most twice (one resend after "Session terminated").
- **Reap kill switch and the SessionEnd timeout.** Every automatic reap path (the Stop/SubagentStop and SessionEnd hooks, and each launcher) checks a kill switch first: the file `<runtime root>/reap.disabled` or `DOPEMUX_MCP_REAP=0`/`off`/`false`. The explicit `dopemux mcp reap --apply` ignores it with a note. `.claude/settings.json` gives the SessionEnd hook `"timeout": 60`, because SessionEnd hooks otherwise share a 1.5 s budget (Claude Code docs, read 2026-11-05). Deadlines: Stop 60 s, SessionEnd 45 s, launcher 8 s.
- **D5, unknown history fails closed.** When the shared store's row count for a project cannot be read (Postgres or docker down), the history is unknown, not "has history". A start refuses `conport` with `CONPORT_TENANT_UNKNOWN_HISTORY` and changes nothing; `doctor` reports INFO `CONPORT_TENANT_UNVERIFIED`. Option A (`legacy_shared`) applies only to a project whose rows were counted.
- **D5, no plaintext password to Postgres.** `CREATE ROLE` receives a SCRAM-SHA-256 verifier (RFC 5802/7677, 4096 iterations, 16-byte random salt). The plaintext stays only in the 0600 secrets file, for the client.
- **Superseded: "`.envrc.dopemux-mcp` is no longer read by any command" (design D5, `claudedocs/mcp-just-works-design-2026-11-05.md` line 160).** dopemux still reads the file itself: `init` re-reads its ports and legacy `CONPORT_DB_*` (`init --force` keeps them), the first ConPort tenant resolution adopts legacy `CONPORT_DB_*` from it once (`legacy_envrc`), and `doctor` and each sidecar start take its ports. Nothing needs it sourced, and identity never comes from it; the generated header says so.
- **`init` fails closed on unknown history too.** When Postgres does not answer, `dopemux mcp init` stops with `FAIL CONPORT_TENANT_UNKNOWN_HISTORY` before building any image and changes nothing in the tenant store; the `.mcp.json` it already wrote stays.
- **Owner guard checkpoints (audit F1; supersedes "never before the first session" in the reconnect-guard bullet above).** The guard runs before every backend connect, the first session included, and again right after each `initialize`, before the session carries any runner request. The launcher's own launch-time check runs under the reserved `:7890` lock, which is released before the proxy starts; the first-session checkpoint catches a `switch-project` in that interval, and the post-`initialize` checkpoint closes the interval between a passing guard and the connect. When the first session is refused, the proxy answers the runner's `initialize` and gives its first request the `-32000 "<code>: <remedy>"` error, then exits 1.
- **Automatic reaps never wait (audit F3).** `maybe_reap` takes each instance lock non-blocking (a busy instance is skipped as `locked`) and bounds the initial `docker ps -a` by `min(cmd_timeout_s, time left)`; a timed-out inspection skips the run. A run that attempted no candidate or whose inspection timed out leaves `reap.last` as it was. The explicit `dopemux mcp reap --apply` still waits for locks.
- **Reap re-checks eligibility and never waits on the registry lock (audit 2).** Under each instance lock, after pruning dead attach records, the reap evaluates the plan's predicate again on current state (no live attachment AND a missing worktree or `idle_s` since `last_detach`); a candidate that no longer qualifies is skipped as `stale` with no docker call and no state change. On automatic runs the final registry/lease update waits for the registry lock at most `min(time left, 2 s)`, with both registries updated under one acquisition; when it stays busy the candidate is skipped as `registry_busy` (containers already removed; registry, leases and runtime dir untouched), and a later run finishes it, as a state-only candidate once the worktree is gone. `dopemux mcp reap --apply` waits for every lock.
- **A failed state save keeps the runtime dir (codex F1).** `_release_state` returns the registry/lease save errors it records (a corrupt file left as is, an `OSError`). When any is returned after every container was removed, the candidate is skipped as `state_error` and never counted as reaped: the containers are gone and the runtime dir stays. Unlike `registry_busy`, the state may be partly updated: the runtime registry and the lease file are saved one after the other with no rollback (`save_states_locked`), so the one that saved is updated (with a corrupt lease file the entries are still marked stopped) and the failing one stays as it was. As with `registry_busy`, a later run finishes it as a state-only candidate once the worktree is gone (after a person fixes a corrupt file). The partial-docker-failure path still never removes the dir or counts as reaped.
- **CLI start/restart are serialized against the reaper (codex F2).** `run_lifecycle` takes `hold_instance_lock` (default `True`). A non-dry `start` or `restart` runs its worktree-scoped services (every selected service except the task-orchestrator) under one `instance_lock(runtime_dir)` acquisition, a restart's stop and start included; `stop` keeps its lock as before (`_stop_services` never takes the reserved lock). The task-orchestrator part runs outside that lock, after it is released (a restart stops it before the lock is taken and starts it after), writes nothing into the runtime dir when it runs beside worktree services, and the parts merge into what one call returns. Fix round 1: once the lock is held and before the worktree part runs, the mutable facts (runtime registry, docker snapshot, ports and every finding derived from them, `_mutable_facts`, the helper the unlocked preflight uses too) are taken again and passed to the worktree part, so a reap that finished while the run waited for the lock is seen instead of a stale snapshot; the task-orchestrator owner gate is preflight-only and is not re-run under the lock (the orchestrator part never runs under it, and its start re-checks the owner under the reserved lock itself). A missing image is built before the lock is taken (`_prebuild_images`; a restart includes the sidecars it will stop and start again), so a long build does not hold `launch.lock` against the worktree's launchers, except when a reap removed the containers while the run waited and the image is missing too: that build runs under the lock. Build inputs that cannot be written are an `IMAGE_BUILD_FAILED` for that service, not an exception. Fix round 2: a restart's start half reads docker after the stops (the pre-stop snapshot still listed the sidecars just stopped as running, so a restart stopped them and started nothing, a defect older than this cycle), for the orchestrator half too; and when the re-check under the lock blocks a split restart after the orchestrator half stopped a running orchestrator, that orchestrator is started again outside the lock and the worktree part is reported blocked (not when its stop failed: a failed stop starts nothing). Fix round 3: the orchestrator stop of a split restart reads docker again after the pre-build, and a CLI `stop` re-takes the mutable facts under its instance lock too, so a reap that finished while it waited leaves nothing to stop (`already_stopped`, PASS) instead of a `docker stop` of names that are gone. Fix round 4: every docker re-read this branch adds fails closed: an unreadable docker is `DOCKER_UNAVAILABLE` (a stop then releases nothing and keeps the runtime dir; a restart blocks before stopping anything when the orchestrator's read fails, and a half whose later read fails is FAIL and starts nothing), never the preflight snapshot instead. Residual: the orchestrator branch's own re-inspect under `:7890`, older than this cycle, treats an unreadable docker as no owner and relies on the port probe. Why the split: the reserved `:7890` lock and the instance lock are never nested (neither is taken while the other is held; `locks.py` states this rule, which D7 above does not), and `switch-project` calls the lifecycle while holding the reserved lock; holding `launch.lock` around the orchestrator's start, which takes the reserved lock, would be instance before reserved on the CLI path against reserved before instance there, a deadlock. The launcher passes `hold_instance_lock=False` (`ensure_backend` already holds the instance lock; `ensure_orchestrator` holds the reserved lock); dry runs never lock. Residual (low): the orchestrator start is not serialized against a reap's runtime-dir removal. Since the final review a start without a compose sidecar writes nothing into the runtime dir, and the reaper never touches orchestrator containers, registry entries or leases.
- **Crashed launchers make an instance idle (Codex P2).** Planning measures idle time from the newer of `last_detach` and the newest dead attach record (`_effective_last_detach`), so an instance whose only launcher was SIGKILLed or lost with the host becomes an idle candidate. Planning stays read-only: nothing is pruned or stamped until the instance lock is held, where pruning stamps `last_detach` and the re-check uses the same helper.
- **Build-only runtime dirs are reaped (acceptance finding 2).** Each launcher writes `<runtime_dir>/instance.json` (`project_id`, `worktree_hash`, `worktree_root`, `project_root`, `written_at`; atomic, 0600) under the instance lock at attach time when it is missing or differs; a write failure prints one stderr line and never refuses the launch. `plan_reap` adds a third, dir-only candidate source: a marked dir that names itself (`runtime_dir_for_paths`), whose pair has no registry entry and no managed container, whose worktree is gone, with no live attachment and no live detached build (`build-*.pid` alive and younger than the build budget), becomes a state-only `worktree_missing` candidate (`dir_only`). Never on idle (owner ruling: a container-less dir costs nothing). Under the instance lock the re-check re-evaluates the worktree-gone, live-attachment and live-build conditions (never idle); it does not re-check that the pair still has no registry entry or container. A marker whose `worktree_root` is not absolute is ignored. Dirs without a marker (older launchers) are never candidates.
- **T7 evidence.** The native hooks do not write `hook_status.json`; that file belongs to the legacy monitor (`~/.dopemux/hook_status.json`). They emit content-free `native_hook_activity` events to the Redis stream `dopemux:events` (`DOPEMUX_ACTIVITY_EVENT_STREAM`), rate-limited per session and switchable off. T7's observable evidence is the red-lane hard-deny (exit 2 with its message), SessionStart/Stop exit 0, no `ModuleNotFoundError`, and, when Redis is up and events are enabled, those activity events.
- **`--repo` loads the target checkout's catalog (PR #1503 review batch, Task A).** `init`, `start`, `stop`, `restart`, `status`, `up --repo`, `down --repo`, `switch-project` and `repair-config` with `--repo`, and `launch --root`, read the MCP catalog of the checkout they act on (`$DOPEMUX_MCP_CATALOG` when set, else that checkout's repo-local catalog, else the bundled one). Deferred, not a pure reorder: `doctor --repo`, `doctor --profile --repo` and `profile show --repo` still load the caller's catalog.
- **D5, a resume never replays a committed migration that cannot be re-run (Codex P2, PR #1503 review).** When the tenant schema already exists, the database phase reconciles the migrations whose statements cannot be re-run (001 and 002: one `BEGIN`/`COMMIT` each, with a bare `CREATE VIEW` or `CREATE TRIGGER`) against the database before replaying them: it probes the last object each one's transaction creates (one of the objects the sealed gate's `migration_schema_errors` checks for that version, which is enough because the migration is one transaction; `MIGRATION_APPLIED_PROBES`). One whose object exists is checkpointed, not resent; a probe that fails (psql error, no marker, any answer but true or false) refuses with `CONPORT_TENANT_PROVISION_FAILED` and runs nothing further. The re-runnable migrations (003, 004, 007, 008: only `IF NOT EXISTS`/`IF EXISTS` forms, `ON CONFLICT` inserts, `SET NOT NULL`, no-op updates, `ANALYZE` and read-only `DO` checks) are simply replayed, which also completes 003 or 004 (neither is one transaction) when a kill left it half applied; a static scan of the sealed SQL in the tests keeps that classification current. A fresh database is not probed. This fixes the Codex review finding on PR #1503: a migration that committed before its checkpoint was written was replayed, and 001/002's `CREATE VIEW` and `CREATE TRIGGER` then failed every later start with an already-exists error.
- **State-only candidates also qualify on idle (Task B5, Codex connector review of `357f6ab99`).** A registry pair with no container left but unfinished state (a running entry, active leases or a runtime dir) is now planned on the same predicate as a container candidate: no live attachment AND (its worktree is gone OR `idle_s` has passed since the effective last detach). A leftover of an idle reap (a reap killed after `docker rm`, `registry_busy`, `state_error`) is therefore finished by a later run while the checkout still exists. This supersedes "a later run finishes it, as a state-only candidate once the worktree is gone" in the audit-2 bullet and the same clause in the codex F1 bullet above. Under the instance lock `_still_eligible` re-evaluates both reasons, and `_reap_one` treats an idle state-only candidate like a `worktree_missing` one (no docker call, state released, runtime dir removed); dir-only (marker) candidates stay `worktree_missing`-only.
- **A live detached build excludes every candidate kind (Task B5 round 1).** `plan_reap` skips any container, state-only or dir-only pair whose runtime dir holds a live detached image build (`_live_build`: a `build-<service>.pid` whose pid is alive and that is at most `build_timeout_secs()` old), whatever its reason, and `_still_eligible` under the instance lock returns false while such a build is live, so a build that started between plan and apply leaves the candidate `stale` with no docker call and no state change. This extends to container and state-only candidates the exclusion the build-only runtime dirs bullet above gave dir-only candidates.
- **State-only candidates: a container check under the lock, and idle needs real state (Task B5 round 2).** Under the instance lock, after the re-check and before anything is released, a state-only or dir-only candidate runs one `docker ps -a` filtered by its pair's `dopemux.project_id` and `dopemux.worktree_hash` (bounded like every docker call of the run); a listed container (a CLI start since the plan) or a failed or timed-out call skips it as `stale`, so a just-started instance is never released and orphaned. On the `idle` reason a state-only pair now needs a running non-orchestrator entry or an active lease; a runtime dir alone qualifies only on `worktree_missing`, as for dir-only candidates. This narrows "unfinished state (a running entry, active leases or a runtime dir)" in the Task B5 bullet above for idle pairs.
