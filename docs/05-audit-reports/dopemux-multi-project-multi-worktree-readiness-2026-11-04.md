---
id: dopemux-multi-project-multi-worktree-readiness-2026-11-04
title: Dopemux Multi-Project / Multi-Worktree Readiness Audit (2026-11-04)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-04'
last_review: '2026-11-04'
next_review: '2026-12-04'
prelude: Read-only audit of whether dopemux (main @ 75dacb43f) is ready for several projects and several worktrees of one project to run concurrent Claude Code sessions. Covers the MCP fleet lifecycle, identity and ports, the setup and maintenance command surface, host-global state, lifecycle hooks and the three plugins. Gives a verdict per scenario, a developer setup recipe as the code actually requires it, and one limitations table. Nothing was mutated by the audit.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Audit complete. No repo file (other than this report), container, registry, lease, or global config was changed. Every command marked MUTATING below is a recommendation, not something that was run. Supersedes nothing; extends `dopemux-cross-repo-readiness-audit-2026-10-16.md`, whose §4 findings (Q1–Q7, H1) are **unchanged at HEAD** (`git diff --stat 95e95bee8..HEAD` on every cited file is empty; the only MCP-touching commit since is 93050d135 / #1447, `fleet_catalog.py` only) and are cited here rather than re-derived.

## 0. Verdict (read this first)

**Multi-project (separate repos): usable today for ConPort + dope-memory, with manual steps the CLI does not perform, and one project at a time for task-orchestrator.** Four repos are running it right now (dopemux-mvp, dNh_CRM, adOps, dopeClaw: eight healthy sidecars, §2). What makes it work is outside the CLI: per-project ConPort tenants provisioned by hand, env delivery by a user-level bootstrap script, image pre-builds, and two environment variables the compose file requires. The gated items from October (ConPort tenant model P-18, redis-events P-21, task-orchestrator P-24, Serena P-20) have not moved; none of the five fix PRs (#1456, #1459, #1460, #1439, #1440) has merged.

**Multi-worktree (several worktrees of one project): not ready.** The design intends worktrees of one project to share that project's records and its task-orchestrator. On HEAD:

1. **Identity depends on the shell's environment, not only on git.** A linked worktree resolves to the *same* project as main only from a clean shell. From a shell that has loaded main's `.envrc.dopemux-mcp` (which direnv does for every nested worktree, because `.envrc` is gitignored and direnv walks up), the same worktree becomes a *separate project* named after its directory, inherits main's instance id and ports, and every start is blocked on port and container ownership conflicts (§3.2, DEFECT, no PR).
2. **`mcp init` without `--repo` targets the wrong checkout from that shell**, and the `--force` the error message recommends would rewrite main's env file and strip its hand-added ConPort tenant credentials (§3.3, DEFECT, no PR).
3. **Sessions in manually created worktrees have no MCP ports at all.** None of the 25 linked worktrees has a generated env file; `.mcp.json` then falls back to 3005/3020/7890. Nothing listens on 3005 or 3020 (ConPort and dope-memory fail closed), but 7890 is dNh_CRM's task-orchestrator, so `/dx:*` in such a session talks to another project (§3.4). The four worktrees Claude Code itself created carry a byte copy of main's `.claude/settings.local.json`, so they *would* attach to main's sidecars if Claude Code applies that file's `env` to `.mcp.json` interpolation; whether it does is unverified, and how the copy got there is UNKNOWN (no `.worktreeinclude`, no `WorktreeCreate` hook).
4. **Lifecycle hooks crash in every linked worktree.** The dispatcher looks for `.venv` relative to the worktree, falls back to the PATH `python3`, which lacks pydantic; probe output: `ModuleNotFoundError: No module named 'pydantic'`. The DCP hard-deny guard, the untracked-work probe and the health probe never run there (§3.5, DEFECT, no PR).
5. **A second worktree's ConPort lands on the legacy shared database**, not on main's tenant, because no writer emits `CONPORT_DB_*`; its dope-memory chronicle is a separate file. Worktrees therefore do *not* share records (§3.6, GATED P-18/P-19).

**Concurrent sessions:** per-checkout hook caches only produce duplicate advisories (LOW). Host-global races are real but bounded: lifecycle registries are atomic-write but unlocked (run `mcp init`/`start` one at a time), `~/.dopemux/hook_status.json` is last-writer-wins, nine orphan `monitor_daemon.py` processes are live now, and `~/.claude.json` / `~/.claude/settings.json` are rewritten whole by `sync-globals`, `dopemux start`, `routing`, and `native-hooks register` (§5).

**Host-wide, not multi-project, but blocking "all features" today:** no Serena container exists and `mcp-dope-context` publishes no host port, so `~/.claude.json` sends every session to `localhost:3006` and `localhost:3010` and both fail to connect (§2).

## 1. Scope and method

Read-only. Six delegated agents (five read-only lanes and one independent verifier) plus supervisor measurements:

| Lane | Model / effort | Subject | Output |
|---|---|---|---|
| L0 | claude-haiku-5-5 medium | inventories: catalog, tests, gitignore, docs, plugin hooks, home-dir writers, `.claude/hooks` | 7 tables |
| LA | claude-sonnet-5-5 medium | lifecycle, identity, ports, registries, stale-state maintenance | Q-A1..A7 |
| LB | claude-sonnet-5-5 medium | `dopemux init`, `wire-conport`, `worktrees`, `instances`, every `mcp` subcommand, docs vs code, PATH binary | Q-B1..B7 + recipe |
| LC | claude-sonnet-5-5 medium | host-global state, hook dispatcher, monitor daemon, plugins, statusline | Q-C1..C7 + concurrency matrix |
| Guide | claude-haiku-5-5 | Claude Code worktree/settings docs | 3 answers, 2 UNKNOWN |
| Supervisor | claude-fable-5-1 xhigh | live measurements (§2), dry-runs, verification of lane claims, synthesis | this report |

Requested models above are selectors; observed execution identity is UNKNOWN (no runtime receipts). Commands run: `docker ps/inspect/port`, `git worktree list`, `lsof`, `mcp status`, `mcp doctor --repo . --json`, `mcp control-plane identity/reconcile`, `mcp leases reconcile --dry-run`, `mcp start --dry-run --json` (write-free: `docker_runtime.py:386-387`, `lifecycle.py:1302`), `mcp repair-config --dry-run`, `instances list` (creates `<cwd>/.dopemux/instances_cache.json`, gitignored), one hook dispatcher probe from a worktree. Not run: `dopemux init`, `mcp init`, `mcp start`, `repair-config --apply`, `fleet init`, `dopemux doctor` (it execs `scripts/taskx doctor`, effects UNKNOWN).

## 2. Host state observed (2026-11-04)

**Containers** (`docker ps -a`): four projects each with a healthy `conport` + `dope-memory` pair: dopemux-mvp `dcd6` (3007/3019/4005; 3054), dNh_CRM `8d6d` (3041/3040/4040; 3024), adOps `a22d` (3022/3021/4021; 3037), dopeClaw `6be9` (3017/3018/4029; 3045). One task-orchestrator, `task-orchestrator-dnh_crm-9a4e9aa8a329cdd5`, on 127.0.0.1:7890. Host singletons up: postgres-age, redis-events :6379, redis-primary :6380, mcp-pal :3003, mcp-pal-stdio, qdrant, dope-decision-graph-bridge :3016, gptr :3009, desktop-commander :3012, litellm. **`mcp-dope-context` is up but publishes no host port** (`docker port` empty). **No serena container exists.**

**Listeners on the `.mcp.json` fallback ports:** 3004, 3005, 3020 → nothing. 7890 → dNh_CRM's orchestrator.

**Worktrees:** 26 entries in `git worktree list` (main + 25 linked: 7 under `.worktrees/`, 4 under `.claude/worktrees/`, 5 sibling dirs, 9 under `~/Documents/{Codex,ChatGPT}`, `~/.codex`, `~/LocalWork`). Config presence: `.envrc.dopemux-mcp` in **0/25**; `.claude/settings.local.json` in 4/25 (the `.claude/worktrees/*` ones, byte-identical to main's, `cmp` = identical, mtimes = creation dates); tracked `.mcp.json` in 23/25; `.dopemux/` in 23/25.

**Runtime state** (`~/.dopemux/mcp/`): `runtime/instances.json` 11 rows (dNh_CRM ×3, dopemux-mvp ×3 incl. one stopped worktree, adOps ×2, dopeClaw ×2); `runtime/port-leases.json` 243 leases (40 active, 203 released, none for any of the 25 linked worktrees); 74 runtime dirs, including two per-worktree task-orchestrator identity files written as *separate projects* (`foundations-wave-1-d18abe9a584acf2e`, Oct 30; `runner-memory-2a-648a1a9dc91bf1fe`, Nov 4 04:13) — field evidence of finding §3.2.

**`mcp status`** (main): PASS_WITH_WARNINGS, project `dopemux-mvp-2e346e2084bca021`, conport PASS, dope-memory PASS, task-orchestrator WARN. **`mcp doctor --repo .`**: FAIL — `DOCKER_CONTAINER_WRONG_PROJECT` (task-orchestrator owned by dNh_CRM) plus the two pre-existing legacy-compose findings (`COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK`, `COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK`); doctor itself warns `DUAL_ALLOCATION_BRAINS` ("mcp init `_allocate_ports` and `InstanceOverlayManager` … not unified") and `INSTANCE_OVERLAY_NOT_WIRED_TO_INIT`. **`mcp control-plane identity`**: `resolution_status=UNKNOWN` for main and worktrees (identity registry absent; dormant by design, no production path imports it — LA Q-A7).

**Processes:** 9 orphan `hooks/monitor_daemon.py` processes (no pid file, no singleton guard; PR #1460 fixes only the test leak).

## 3. Findings (new since October, supervisor-verified unless marked)

### 3.1 How identity is derived (the mechanism everything else depends on)

Per-worktree: `instance_id = sha1(resolved worktree path)[:4]` (`src/dopemux/mcp/port_allocator.py:47`); compose project `dopemux_<slug>_<hash>` (`docker_runtime.py:77-79`); containers `dopemux-<slug>-<hash>-<svc>` (`docker_runtime.py:70-74`), where `slug` is derived from `Path(project_root).name` (`lifecycle.py:584-586`). Per-project: `project_id = <slug>-<sha256(project_root)[:16]>`, and the task-orchestrator container is `task-orchestrator-<project_id>` (`lifecycle.py:848-860`). `project_root` comes from `git rev-parse --git-common-dir` (`src/dopemux/mcp/project_identity.py:85-96`) **unless** `TASK_ORCHESTRATOR_PROJECT_ROOT` or `DOPEMUX_PROJECT_ROOT` is set, in which case the env wins and `git_common_dir` is recorded as `None` (`project_identity.py:122-129`). Ports: `base + int(sha1[:4],16) % 100`, with rebind on collision and a lease (`port_allocator.py:~558-640`); AGENTS.md:282 ("raises an error") is stale (LA Q-A2).

### 3.2 Identity resolution is environment-dependent — DEFECT (HIGH, no PR)

Empirical, `mcp start --dry-run --json --repo .worktrees/foundations-wave-1`:

| Shell | project_id | project_root | instance_id | workspace_id | conport container | TO container |
|---|---|---|---|---|---|---|
| clean (`env -i …`) | `dopemux-mvp-2e346e2084bca021` (= main) | `/Users/hue/code/dopemux-mvp` | `3303` | worktree path | `dopemux-dopemux-mvp-3303-conport` | `task-orchestrator-dopemux-mvp-2e346e2084bca021` (shared with main) |
| main's envrc loaded | **`foundations-wave-1-d18abe9a584acf2e`** | **the worktree** | **`dcd6`** (main's) | **main's path** | `dopemux-foundations-wave-1-3303-conport` | `task-orchestrator-foundations-wave-1-d18abe9a584acf2e` |

Second row ports = main's (3007/3019/4005/3054) → `LEASE_BELONGS_TO_OTHER_PROJECT` ×4, `PORT_OWNED_BY_OTHER_PROJECT` ×5, `DOCKER_CONTAINER_WRONG_PROJECT` ×3; status BLOCKED.

Mechanism: `lifecycle.py:445-448` builds the identity env as process env + the target's envrc (override), so with no envrc in the worktree the ambient variables leak through. `runtime_state.py:116-137`: when the ambient `DOPEMUX_WORKSPACE_ROOT` differs from the target it *forces* `DOPEMUX_PROJECT_ROOT` (and `TASK_ORCHESTRATOR_PROJECT_ROOT`) to the target path — reasonable for a foreign repo, wrong for a worktree of the same repo — and `project_identity.py:122-129` then treats that as an explicit override and never consults the git common dir. Meanwhile `runtime_state.py:158` (`instance_id = env_map.get("DOPEMUX_INSTANCE_ID") or …`) and `:171` (`workspace_id = env_map.get("DOPEMUX_WORKSPACE_ID") or …`) still take the ambient values. Three identity fields from three sources. Two caveats from the independent verification: the ambient values leak in only because the worktree has no `.envrc.dopemux-mcp` of its own (a target envrc overrides the process env, `lifecycle.py:444-448`), and both plans are BLOCKED today (`ENVRC_MISSING` and the ownership conflicts), so the mixed identity is reported rather than acted on — until the worktree gets an envrc generated under that same mixed identity. Why it is the default, not an edge case: `.envrc` is gitignored (`.gitignore:272`), so direnv in any nested worktree finds main's `.envrc` (`direnv status` from the worktree: `Found RC path /Users/hue/code/dopemux-mvp/.envrc`, LA Q-A1b); the Claude Code Bash tool in this repo carries the same env. Consequence: `mcp start/doctor/repair-config --repo <worktree>` from such a shell is fail-closed (BLOCKED) rather than silently wrong, but the worktree is classified as a different project, the task-orchestrator identity fragments (two such identity files already exist, §2), and any envrc generated in that state records the wrong identity.

### 3.3 `get_repo_root` is env-first — DEFECT (HIGH, no PR; LB Q-B3/B5, LA Q-A1b, verified by probe)

`src/dopemux/worktree_commands.py:53-90` (`get_repo_root`) checks `DOPEMUX_WORKSPACE_ROOT`, then `DOPEMUX_PROJECT_ROOT`, then git. `mcp init` (`mcp_commands.py:1391`), `add`, `remove`, `generate`, `ensure` use it with no `--repo`. From a worktree or a scratch dir whose shell has project A's env loaded, `mcp init` resolves to **A**: it then stops with `.envrc.dopemux-mcp already exists. Use --force` (`:1449-1452`), and `--force` rewrites A's envrc whole (`_write_envrc`, `:1490`, `:839-859`, which emits only the eight identity exports plus port numbers), dropping the hand-added `CONPORT_DB_*` tenant lines (October Q5); it also rewrites A's `.mcp.json` (`:1486-1487`) and allocates fresh port leases (`:1475-1482`). `mcp init` for a genuinely new project B from such a shell also records A's path as B's `DOPEMUX_PROJECT_ROOT`. `repair-config`, `doctor`, `fleet`, `start` honour `--repo` (subject to §3.2). Not executed; code-traced plus a read-only `get_repo_root` probe.

### 3.4 MCP ports never reach a session unless the shell or settings carry them — CAUTION (HIGH impact)

`.mcp.json` (tracked) uses `${CONPORT_MCP_PORT:-3005}`-style URLs. The only non-shell delivery is `.claude/settings.local.json` `env`, and **nothing under `src/` writes it** (repo-wide grep; LB Q-B3). Only the user-level scripts `~/.local/bin/dopemux-mcp-bootstrap` and `dopemux-mcp-sync-settings` do (they also add the direnv shim, run lease GC under a lock, and edit `.gitignore`); the bootstrap header states it exists because `dopemux init` does no MCP wiring. Result on this host: 0/25 linked worktrees have an envrc; a session opened in `.worktrees/*` gets ECONNREFUSED for conport/dope-memory and reaches dNh_CRM's orchestrator on 7890. The four Claude-created worktrees have byte-identical copies of main's `settings.local.json` (instance `dcd6`, ports 3007/3054, workspace id = main's path); if Claude Code applies that `env` block to `.mcp.json` interpolation, sessions there attach to main's sidecars under main's workspace id. Whether it does is not stated in the docs (guide lane: UNKNOWN), and this session cannot distinguish it from the launch shell's own exports, since the Bash tool shell already carries main's envrc. Whether the copy is harness behaviour: UNKNOWN (docs describe copying only via `.worktreeinclude`, which this repo lacks, or a `WorktreeCreate` hook, which no settings file defines; `https://code.claude.com/docs/en/worktrees.md`).

### 3.5 Lifecycle hooks crash in linked worktrees — DEFECT (HIGH, no PR; LC C1, supervisor-reproduced)

`.claude/hooks/run_native_hooks.sh:7-17` sets `ROOT=$(git rev-parse --show-toplevel)` (the worktree), prefers `$ROOT/.venv/bin/python`, else `command -v python3`; the site-packages injection loop (`:22-31`) also looks under `$ROOT/.venv`. Linked worktrees have no `.venv`. PATH `python3` here is mise 3.12.13 without pydantic. Probe (SessionStart payload piped into the dispatcher from `.worktrees/foundations-wave-1`, reproduced independently by the verifier): dispatcher exit 1, empty stdout, traceback `native_hooks.py:81 → workflow/__init__.py:3 → workflow/models.py:13 → pm/__init__.py:11 → pm/models.py:20 … ModuleNotFoundError: No module named 'pydantic'`. Every hook event fails the same way before any handler runs; exit 1 is a non-blocking error for Claude Code, so the DCP surface guard (H1 hard-deny), denylist nudge, health probe, proof-tracking guard, orchestrator nudges and workflow gating all **fail open** in worktrees. The outcome depends on which `python3` is first on PATH. Fix hint: resolve `.venv` from `git rev-parse --git-common-dir`'s parent.

### 3.6 A second worktree does not share the project's ConPort or chronicle — GATED P-18/P-19 (LA Q-A1)

From a clean shell the worktree gets its own `conport` container; its DB URL falls to `dopemux_knowledge_graph` (compose default, October Q3) while main runs on tenant `conport_dopemux_mvp`; no writer emits `CONPORT_DB_*` (zero hits under `src/dopemux/mcp` and `commands`). Its dope-memory bind-mounts `<worktree>/.dopemux` (`lifecycle.py:1208`; observed for main: `/Users/hue/code/dopemux-mvp/.dopemux -> /data`, `DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite`), a separate chronicle. The catalog says `scope: per-worktree` for conport, dope-memory and task-orchestrator (`mcp_catalog.yaml:536,578,604`); the ruled end-state (design §10.3, P-19) is project-scoped ConPort shared by a repo's worktrees. Until then "worktrees share records" is only achievable by attaching a worktree to main's sidecars (what §3.4's copied pins would do, if applied), which is undesigned and bypasses the per-worktree instance id.

### 3.7 Task-orchestrator: one project per host, and two identity schemes — GATED P-24 + DEFECT

Fixed reserved port 7890 (`mcp_catalog.yaml:604`, `port_policy: reserved_singleton`, `state_scope: single_active_project`). dNh_CRM holds it; every dopemux-mvp `mcp start` whose service set includes task-orchestrator (the default set is conport, dope-memory, task-orchestrator — LA Q-A6) is BLOCKED with `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER (match=CONFLICT port=7890)`. Additionally the wrapper labels the container `dopemux.project_id=dNh_CRM` (repo name) and writes `project_id: dNh_CRM, workspace_id: dnh_crm-9a4e…` to `~/.dopemux/mcp/runtime/dnh_crm-9a4e9aa8a329cdd5/task-orchestrator.identity.json`, while the lifecycle expects `<slug>-<sha256[:16]>`; every start plan therefore also reports `TASK_ORCHESTRATOR_RUNTIME_METADATA_CONFLICT: docker_labels vs wrapper_metadata` (design §2.1 "kill the four schemes", not done). `switch-project`, `adopt`, `migrate`, `reconcile` do not exist (AGENTS.md §12.6 is accurate).

### 3.8 Registries: atomic but unlocked — DEFECT (MED; October finding confirmed, LA Q-A4, L0 T6)

`instances.json` (`runtime_registry.py:193-208`), `port-leases.json` (`port_leases.py:434-444`), `service-leases.json` (`service_leases.py:222-232`), `identity.json` (`identity_registry.py:164-175`) all write temp + rename, but every path is load-modify-save with no lock; the runtime-registry window spans an entire `start`. `repair-config` writes config before persisting leases. Two concurrent `mcp init`/`start` lose updates. #1456 adds `mcp registry reconcile`, not a lock (UNKNOWN whether any PR does).

### 3.9 First start of any new project or worktree fails from a clean shell — DEFECT (PRs #1456 + #1459, unmerged)

`compose.yml:423` `${HOST_CODE_PARENT_DIR:?…}` is interpolated for every `up`/`config`, and the lifecycle passes only the process env (`lifecycle.py:~1371`); `conport`/`dope-memory` have `build:` without `image:`, so a new compose project name triggers a ~1.5 GB build that `docker_runtime.run_cmd`'s 180 s timeout kills (exit 124). Static evidence + October execution record; not re-run.

### 3.10 No garbage collection for anything per-worktree — CAUTION (LA Q-A5, LB Q-B2)

`mark_stale` has no callers; `leases reconcile` releases only reserved-singleton-port leases (dry-run today: 0 invalid); `control-plane reconcile` returns UNKNOWN/blocked (registry absent); runtime dirs, stopped `dopemux_*` compose projects, images (~3.3 GB per project) and volumes are never removed. `dopemux worktrees …` is defined (`commands/worktrees_commands.py`) but **not registered** (`dopemux worktrees` → "No such command"; only `instances` is added at `cli.py:4252`). `instances cleanup --all` uses a legacy `<root>/worktrees/<id>` layout and A–E port slots, cannot remove `.worktrees/` or `.claude/worktrees/` entries, and touches no containers or leases. The only lease GC is step 3 of the user bootstrap script.

### 3.11 Legacy cwd compose commands have a host-wide blast radius — CAUTION (LA Q-A3, LB Q-B4)

`mcp up`, `down`, `logs`, `start-all` without `--repo` run compose against the cwd `compose.yml` under project `dopemux` (compose `name:`) and so stop/remove the shared pal, dope-context, gptr, serena and litellm services (`down` uses `rm -v`); they do not touch postgres/redis/qdrant. `stop`/`down --repo` are scoped to exact container names. `restart` still passes the pre-stop docker snapshot into start (`lifecycle.py:573`, `:1062`) and can report `already_running` (October Q7). `dopemux update run` does `git pull`, `pip install` and a compose rebuild in whatever repo is the cwd.

### 3.12 Which `dopemux` runs — CAUTION (LB Q-B7)

PATH `dopemux` = non-editable `~/.dopemux/venv` from 640f0a2b (35 commits behind), whose `mcp start` needs `DOPEMUX_MVP_ROOT`. `docker/mcp-servers/dopemux` (the wrapper pinned by the bootstrap script) `cd`s to dopemux-mvp at line 25, so cwd-relative commands act on dopemux-mvp (`mcp list` shows Local = dopemux-mvp from anywhere). Use `/Users/hue/code/dopemux-mvp/.venv/bin/dopemux … --repo <path>`.

### 3.13 `dopemux init` and the ConPort git hook — CAUTION (LB Q-B1)

`dopemux init` (`cli.py:712-826`) is not worktree-aware: in a linked worktree `.git` is a file, `<workspace>/.git/hooks` does not exist, and the hook install is skipped silently (`:796-809`); a worktree-aware installer exists but is called only by tests. Main currently has **no** `post-checkout` hook. When installed, the hook runs `wire-conport`, which writes `.claude/claude_config.json` with `docker exec mcp-conport_<branch>` (`src/dopemux/conport/wire_project.py:71-117`) — names that never match live `dopemux-<slug>-<hash>-conport` containers. That file is **git-tracked**, and HEAD carries another worktree's branch identity in it (`mcp-conport_claude/migrate-cheaperinference-provider-5fa703`). No MCP consumer reads it (Claude Code reads `.mcp.json`; no doctor reads it), but it is not reader-free inside dopemux: the legacy `dopemux start` cockpit path reads it to print "would mount MCP servers" (`cli.py:1844-1853`) and then reads and rewrites it (`cli.py:2167-2168`), so it is a second writer. Inert for MCP wiring; a hygiene defect that dirties every checkout the hook touches. `init --force` overwrites `.claude/claude.md`, `session.md`, `context.md`, `llms.md`, `.dopemux/config.yaml` (October).

### 3.14 Host-global state and daemons under concurrent sessions — MED (LC C2–C4)

Fixed-path, unkeyed writers: `~/.dopemux/hook_status.json` (`hooks/claude_code_hooks.py:98-126`, last-writer-wins), `~/.dopemux/default_workspace` (`workspace_detection.py:76-77`, a global last-writer slot used when git detection fails), `~/.dopemux/config.json`/`routing.yaml`/`global_index.sqlite`. `~/.claude/settings.json` is read-modify-written without a lock by `routing_cli._set_claude_base_url` and `native-hooks register` (`cli.py:4199-4246`); `~/.claude.json` is rewritten whole by `mcp sync-globals --apply` and `dopemux start`. The monitor daemon has no pid file or singleton guard (9 live orphans) and attributes host-wide `pgrep claude` heartbeats to its own cwd project. Dormant: the workflow store sits at the git family root and `resolve()` binds any state with score > 0, so a Stop hook in one worktree could be gated by another worktree's active workflow (`.dopemux/workflows` empty today). Redis activity events go to one host stream with no project key (October Q1, P-21).

### 3.15 Plugins, statusline, tracked identity pin — LOW (LC C5–C6, L0 T5)

`plugins/dopemux-{pulse,route-ledger,memory-bridge}` are opt-in per launch (`--plugin-dir`; none in `enabledPlugins`). Pulse writes nothing and polls one shared ADHD engine on :3025; route-ledger writes one JSONL per session under `.control-tower/state`; memory-bridge writes one outbox per session under `.dopemux/memory-bridge/` and shells out to PATH `dopemux` (§3.12), failing closed in repos without `services/working-memory-assistant/` (adOps). `.claude/statusline.sh` reads only stdin and git. `.dopemux/mcp.instances.toml` is the only tracked file under `.dopemux/` and pins fixed legacy URLs (conport `127.0.0.1:3004/mcp`, dope-memory `:3020`, serena `:3006`, dope-context `:3010`) into every worktree; its only reader is `src/dopemux/mcp/resolver.py`, which only tests import — dormant.

### 3.16 Lifecycle hooks cannot be wired by the CLI in other repos — DEFECT (PR #1439, unmerged)

`native-hooks register` (`cli.py:4140-4251`) still writes `{"hooks": {"command": [{"events": [10 events], "command": …}]}}` (`:4174-4194`), not Claude Code's event-keyed schema used by `.claude/settings.json:8-14`; it also omits `SubagentStart` and, in project mode, writes `Path.cwd()/.claude/settings.json` (`:4199`) rather than the repo root. October H1 unchanged.

## 4. Readiness matrix

Classes: **OK** · **MANUAL** (works, but the developer must do steps the CLI does not) · **ONE-AT-A-TIME** · **GATED** (design gate) · **DEFECT** (code bug; PR if one exists) · **BROKEN-HOST** (not multi-project related; down for everyone right now).

| Surface | Separate projects, concurrently | Worktrees of one project | Concurrent sessions in one checkout |
|---|---|---|---|
| ConPort sidecar + tools (`/conport:*`, `/decision`, `/dx` notes, context save) | MANUAL (tenant via `scripts/migration/provision_conport_project_db.sh`, creds hand-added to envrc, creds only in shell at start — Oct Q3/Q7); shared `redis-primary` cache keyed by caller workspace id (Oct Q6) | GATED P-18/P-19: own container on legacy DB, not main's tenant (§3.6); or attach to main (undesigned) | OK (server-side; same workspace id) |
| dope-memory (`/mem:*`, chronicle) | MANUAL per repo; cross-project `decision.logged` delivery via shared consumer group (Oct Q1, P-21) | own chronicle per worktree (§3.6) or attach to main | OK (WAL, idempotent) |
| task-orchestrator (`/dx:*`) | ONE-AT-A-TIME (P-24); dNh_CRM owns 7890 now | GATED + DEFECT: shared identity only from a clean shell (§3.2); blocked while another repo holds 7890 (§3.7) | OK |
| Serena | BROKEN-HOST (no container) + GATED P-20 | same | same |
| dope-context (`/ctx:*`) | BROKEN-HOST (port unpublished); when up, pass `workspace_path=/workspaces/<repo>` (Oct Q4) | same | same |
| pal-stdio, gpt-researcher, MCP_DOCKER | OK (global stdio) | OK | OK |
| `mcp init` / `repair-config` / `doctor` / `status` / `fleet` | MANUAL + DEFECT §3.3 (use `--repo`, clean shell) | DEFECT §3.2/§3.3 | serialize (§3.8) |
| `mcp start` / `stop` | DEFECT §3.9 (HOST_* vars, pre-build), MANUAL env | same + §3.2 | serialize |
| `mcp up` / `down` / `start-all` (no `--repo`) | CAUTION §3.11 — avoid | avoid | avoid |
| Env delivery to Claude Code sessions | MANUAL (bootstrap/sync-settings scripts or direnv) | MANUAL; manual worktrees get nothing (§3.4) | OK |
| Lifecycle hooks (DCP guards, probes, ADHD save/energy) | DEFECT §3.16 (not wireable by CLI; hand-write settings) | DEFECT §3.5 (crash) | LOW: duplicate advisories; per-session nudge files leak (152) |
| `dopemux init` | CAUTION §3.13 | CAUTION §3.13 (hook skipped; `--force` clobbers `.claude/*`) | n/a |
| `worktrees *` | DEFECT: unregistered | unregistered | n/a |
| `instances *` | CAUTION: legacy model, wrong layout, `cleanup` deletes ConPort state at :3004 | same | n/a |
| Monitor daemon / hook_status | MED §3.14 | MED | MED (orphans, last-writer) |
| Plugins (pulse, route-ledger, memory-bridge) | OK / memory-bridge fails closed outside dopemux-mvp | OK | OK (per-session files) |
| Repo-local ADHD CLI (`save`, `session`, `status`, `workflow`) | OK (needs `<repo>/.dopemux/`) | OK per checkout | last-writer on `context.db`/`emergency_context.json` (LOW) |
| `capture`, `memory capture/rollup`, `kernel`, `rte` | NOT PORTABLE (Oct) | n/a | n/a |

## 5. Developer setup, as the code requires it today

> **Superseded for setup (2026-11-06):** the current recipe is [`docs/02-how-to/mcp-setup-other-repos.md`](../02-how-to/mcp-setup-other-repos.md) (launcher entries, `dopemux mcp init --repo`); this section is kept as the historical record of the 2026-11-04 state.

`D=/Users/hue/code/dopemux-mvp/.venv/bin/dopemux` (never bare `dopemux`, never the wrapper, §3.12). `T=<absolute path of the target repo or worktree>`. **Run every command below from a clean shell** — `env -u DOPEMUX_WORKSPACE_ROOT -u DOPEMUX_PROJECT_ROOT -u TASK_ORCHESTRATOR_PROJECT_ROOT -u DOPEMUX_INSTANCE_ID -u DOPEMUX_WORKSPACE_ID …` or `env -i HOME PATH USER LANG TMPDIR bash -c '…'` — because of §3.2 and §3.3. Run lifecycle commands one at a time (§3.8). Steps marked **MANUAL** are not performed by any dopemux command. All steps MUTATING.

### 5.1 New project (separate git repo)

1. **MANUAL** Ensure `$T` is a git repo. Export once per shell: `HOST_CODE_PARENT_DIR=<parent of your checkouts>`, `HOST_PROJECT_RELATIVE_PATH=<repo dir name>` (compose.yml:406,423; §3.9). `DOPEMUX_MVP_ROOT` is only needed by the PATH install, not by `$D`.
2. `$D mcp init` **with cwd = `$T`** (it has no `--repo`): writes `.mcp.json` if absent, `.envrc.dopemux-mcp` (13 vars, hash ports, rebinds on collision), takes leases in `~/.dopemux/mcp/runtime/port-leases.json`. Not idempotent: aborts if the envrc exists; `--force` rewrites it whole.
3. `$D mcp repair-config --repo $T --dry-run --json`, then `--apply` (adds `.claude/WORKTREE_MCP_SETUP.md`, untracked in a new repo). It is BLOCKED once the envrc contains secret-like keys (step 4), so run it before step 4.
4. **MANUAL** ConPort isolation: provision a tenant — `scripts/migration/provision_conport_project_db.sh` (reads `docker/mcp-servers-source/conport/…`; see memory note on the migration-gate deadlock) — and append `CONPORT_DB_NAME/USER/PASSWORD` to `$T/.envrc.dopemux-mcp`. Without this the sidecar uses the shared legacy DB. Keep the file gitignored.
5. **MANUAL** Env delivery: `echo 'source_env_if_exists .envrc.dopemux-mcp' >> $T/.envrc && direnv allow $T`; add `.envrc.dopemux-mcp` and `.claude/settings.local.json` to `$T/.gitignore`. For sessions not launched from a direnv shell (desktop app, IDE): `~/.local/bin/dopemux-mcp-sync-settings $T` writes the managed `env` block into `.claude/settings.local.json`. (`~/.local/bin/dopemux-mcp-bootstrap $T` does steps 2, 3, 5 and a lease GC under a lock, via the wrapper with `--repo`; it does not do step 4.)
6. **MANUAL** First-time images (§3.9): `cd /Users/hue/code/dopemux-mvp && HOST_CODE_PARENT_DIR=… HOST_PROJECT_RELATIVE_PATH=… DOPECON_BRIDGE_TOKEN=dopemux-compose-interpolation-only docker compose -f compose.yml -p dopemux_<slug>_<hash> build conport dope-memory` (hash = `sha1(resolved $T)[:4]`; ~3.3 GB per project; seconds from cache after the first). Outside the `dopemux mcp` surface — get the operator ruling first, as in October.
7. `source $T/.envrc.dopemux-mcp && HOST_CODE_PARENT_DIR=… HOST_PROJECT_RELATIVE_PATH=… $D mcp start --repo $T --services conport,dope-memory`. Omit task-orchestrator unless this project is the one that owns 7890 (`$D mcp stop --repo <owner> --services task-orchestrator` first; §3.7).
8. Verify: `$D mcp doctor --repo $T --json`, `$D mcp status --repo $T`, `curl -H 'Accept: text/event-stream' http://127.0.0.1:$CONPORT_MCP_PORT/sse` (200 then timeout is correct). Doctor's SSE probe reads UNKNOWN even when it works.
9. **MANUAL** Hooks: `native-hooks register` writes the wrong schema (§3.16); hand-write the event-keyed `hooks` block, and note the dispatcher expects `src/dopemux/claude/native_hooks.py` under the repo (absent outside dopemux-mvp).
10. Launch Claude Code from a shell with `$T`'s env loaded, or after step 5's settings sync.

### 5.2 New worktree of an existing project

1. `git -C <main> worktree add $T <branch>` (`dopemux worktrees` is unregistered; no hook fires).
2. Decide the model, because the code supports neither cleanly:
   - **Own sidecars (per-worktree, what the catalog says):** `$D mcp repair-config --repo $T --dry-run --json` then `--apply` (plans: create envrc, update the *tracked* `.claude/WORKTREE_MCP_SETUP.md` — discard that diff; `.mcp.json` unchanged). Do **not** run `mcp init` here (§3.3). Then **MANUAL** copy `CONPORT_DB_*` from main's envrc if the worktree should be on main's tenant (it will still be a separate container, instance id, and chronicle — §3.6). Pre-build (5.1 step 6) and `mcp start --repo $T --services conport,dope-memory` from a **clean** shell with `HOST_*` set. Cost: 2–3 containers per worktree.
   - **Attach to main's sidecars (what the Claude-created worktrees' copied pins would do, if Claude Code applies them):** copy main's `.claude/settings.local.json` (and/or `.envrc.dopemux-mcp`) into `$T`; ConPort records land under main's workspace id, chronicle is main's `.dopemux/chronicle.sqlite`, no new containers. Undesigned: the worktree's instance id is main's, and any `mcp` lifecycle command from that shell hits §3.2. To make Claude Code do it deliberately, add a `.worktreeinclude` listing `.envrc.dopemux-mcp` and `.claude/settings.local.json` (documented mechanism; untested here).
3. **MANUAL** Env delivery as in 5.1 step 5 (worktree-local `.envrc` so direnv stops walking up to main's).
4. task-orchestrator: shared with main only from a clean shell (§3.2), and only if dopemux-mvp owns 7890 (it does not today).
5. Hooks will crash in the worktree (§3.5) until the dispatcher resolves the venv via the git common dir; interim: `ln -s /Users/hue/code/dopemux-mvp/.venv $T/.venv` (untested; `.venv` is gitignored).
6. Never `git add` `.claude/WORKTREE_MCP_SETUP.md` or `.claude/claude_config.json` changes from a worktree.

### 5.3 Removing a worktree (maintenance)

1. `$D mcp stop --repo $T` **before** removal (containers are labelled per worktree; nothing else stops them).
2. `git -C <main> worktree remove $T && git worktree prune`. Do not use `dopemux instances cleanup` (§3.10).
3. **MANUAL** Leases: no CLI releases them; `~/.local/bin/dopemux-mcp-bootstrap <any repo>` step 3 marks leases of vanished worktree roots released. Images/volumes/compose projects: `docker compose -p dopemux_<slug>_<hash> down -v` and `docker image rm dopemux_<slug>_<hash>-conport …` by hand; runtime dirs under `~/.dopemux/mcp/runtime/<slug>-<hash>/` and rows in `instances.json` are never pruned (dry-run only, `runtime_registry.py:182`).
4. Orphan daemons: `pkill -f hooks/monitor_daemon.py` (9 live now); PR #1460 stops the test suite from adding more.

### 5.4 Running several at once

Per project: ConPort + dope-memory concurrently is fine *after* 5.1 step 4 for every project, accepting that `decision.logged` events can be consumed by another project's dope-memory (Oct Q1, P-21). task-orchestrator: one project; stop it before starting it elsewhere. Serena and dope-context: down host-wide; when up, Serena is dopemux-mvp-only (P-20) and dope-context needs the explicit container workspace path. Per worktree: see 5.2; sessions in different worktrees of one project do not share ConPort records unless attached to the same sidecar.

## 6. Limitations table

| # | Limitation | Class | Fix / gate | Evidence |
|---|---|---|---|---|
| 1 | Identity resolution takes ambient env over git common dir for worktrees | DEFECT (no PR) | scrub `DOPEMUX_INSTANCE_ID`/`WORKSPACE_ID` with the roots, or derive all three from git | §3.2; `runtime_state.py:116-171`, `project_identity.py:122-129` |
| 2 | `get_repo_root` env-first; `mcp init` has no `--repo`; `--force` clobbers tenant creds, `.mcp.json` and leases | DEFECT (no PR) | git-first; add `--repo`; preserve unknown keys | §3.3; `src/dopemux/worktree_commands.py:53-90`, `mcp_commands.py:1391,1449-1452,1475-1490` |
| 3 | No CLI path delivers ports to Claude Code sessions; `.mcp.json` falls back to 3005/3020/7890 | CAUTION (design gap) | make `mcp init`/`repair-config` write `settings.local.json` `env` or a worktree-local `.envrc`; `.worktreeinclude` | §3.4 |
| 4 | Hook dispatcher resolves `.venv` relative to the worktree | DEFECT (no PR) | resolve from git common dir | §3.5; `run_native_hooks.sh:7-31` |
| 5 | ConPort tenant per project is manual; worktrees do not share the tenant | GATED P-18 / P-19 | project-scoped ConPort | §3.6; Oct Q3 |
| 6 | task-orchestrator fixed 7890, one project; wrapper vs lifecycle identity schemes | GATED P-24 + DEFECT | project-scoped leased-port TO; unify identity | §3.7 |
| 7 | redis-events shared stream + consumer group | GATED P-21 (P0) | prefix streams/groups | Oct Q1 |
| 8 | Serena single mount / absent; dope-context port unpublished | GATED P-20 + BROKEN-HOST | deploy wrapper; publish port | §2 |
| 9 | Registries unlocked (load-modify-save) | DEFECT (no PR; #1456 adjacent) | file lock | §3.8 |
| 10 | `HOST_CODE_PARENT_DIR` guard; 180 s first-build timeout | DEFECT | PR #1456, PR #1459 (unmerged) | §3.9 |
| 11 | No GC of leases, runtime dirs, images, compose projects; `worktrees` unregistered; `instances` legacy | CAUTION | implement `reconcile`/GC (design §7, PLANNED); register or delete `worktrees` | §3.10 |
| 12 | Legacy cwd compose commands act on shared singletons; `restart` snapshot bug | CAUTION / DEFECT | P-22 removals; fix restart | §3.11 |
| 13 | PATH `dopemux` stale; wrapper `cd`s to dopemux-mvp | CAUTION | reinstall editable; drop the `cd` | §3.12 |
| 14 | `dopemux init` not worktree-aware; tracked `claude_config.json` with foreign identity (read and rewritten by legacy `dopemux start`); `--force` overwrites `.claude/*` | CAUTION | untrack/stop writing `claude_config.json`; worktree-aware hook install | §3.13 |
| 15 | `native-hooks register` wrong schema | DEFECT | PR #1439 (unmerged) | §3.16 |
| 16 | Monitor daemon orphans; `hook_status.json` last-writer; `~/.claude*.json` whole-file rewrites | DEFECT (MED) | pidfile + flock; PR #1460 (tests only) | §3.14 |
| 17 | Workflow store at family root can gate Stop across worktrees (dormant) | CAUTION (MED) | key by worktree | §3.14 |
| 18 | Docs stale: AGENTS.md §12.2 "raises", §12.3 omits `repair-config`/`start`/env prefixes; no doc names `HOST_CODE_PARENT_DIR`, `DOPEMUX_MVP_ROOT`, `CONPORT_DB_*`, direnv, settings env | DOCS | PR #1440 partially (unmerged) | LB Q-B6 |

## 7. What the lanes could not establish (UNKNOWN)

Who copies `settings.local.json` into Claude-created worktrees; whether `settings.local.json` `env` feeds `.mcp.json` interpolation per the docs (works on this host for main); what wrote the two per-worktree task-orchestrator identity files; whether the Kotlin orchestrator rejects foreign-project calls on 7890 (Oct Q2); whether any open PR adds a registry lock; Claude Code's hook PATH/cwd in worktree sessions; origin of the 203 released leases; writer of `~/.dopemux/operator_id`. Lane line numbers marked `~` in the scratchpad reports are approximate.

## 8. Governance block

- **Change Summary**: one new untracked file, this report. No code, config, container, registry, lease, or global file changed.
- **Authority Used**: user instruction ("check the code … figure out how a developer should set up dopemux for separate projects and what limitations there are"; "use opus, sonnet, and haiku where it makes sense"); AGENTS.md §12, §5; CLAUDE.md MCP rules. Authority NONE for any fix; nothing dispatched.
- **Analysis Performed**: §1. Five delegated read-only lanes (Haiku ×2 including the docs lookup, Sonnet ×3), supervisor dry-runs and docker/git/lsof measurement, three lane claims re-verified by the supervisor (unregistered `worktrees`, tracked `claude_config.json`, hook crash in worktree), and one independent Opus verification pass over the ten HIGH claims (outcome under Validation Performed; verdict table in the session scratchpad `lane-LV-verify.md`).
- **Validation Performed**: PASS — `mcp start --dry-run` write-free (code + mtimes); hook crash reproduced (twice, independently); identity divergence reproduced in two shells (twice, independently); `scripts/docs_validator.py` and `scripts/docs_frontmatter_guard.py` exit 0 on this file. Independent Opus verification of the ten HIGH claims (§3.2–§3.8, §3.12, §3.13, §3.16): 8 CONFIRMED, 1 CONFIRMED with caveats (§3.2, caveats folded in), 1 PARTIAL (§3.13, "no reader" corrected). NOT_RUN — `mcp init`, `mcp start`, `repair-config --apply`, `dopemux init`, `dopemux doctor`, build/first-start timeout (static + October record), `--force` clobber (code-traced), direnv walk-up in a worktree (observed via `direnv status` only). No test suite was run (no code changed).
- **Remaining Uncertainty**: §7. Confidence: `high` for §3.2–§3.7, §3.10–§3.13; `medium` for §3.14 (daemon attribution, dormant workflow gating); observed model identity of delegated lanes UNKNOWN.
- **Files Touched**: `docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md` (new, untracked). Scratchpad lane reports under the session scratchpad directory.
- **Git State**: main @ 75dacb43f, already dirty before this session (147 modified, 24 untracked, unrelated). This file is untracked; not staged, not committed.
- **Rollback Plan**: `rm docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md`.
- **Requested Next Step**: operator decision on which of limitations 1–4 (all DEFECT, no PR) to packet first; recommended order: 4 (hook venv, smallest), 1+2 together (identity + `get_repo_root`), 3 (env delivery), then merge #1456/#1459/#1439 which are already audited.
