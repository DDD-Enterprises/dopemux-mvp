# Consolidated Evidence: dopemux MCP fleet multi-instance research (2026-07-28)

Seven read-only agents examined the repo (worktree of ~/code/dopemux-mvp) and live Docker state.
This file is the evidence base for the design. All claims below carry file:line citations in the
underlying reports; treat them as verified unless marked UNKNOWN.

## 1. Live Docker state (ground truth, 2026-07-28)

- Compose project `dopemux` (working_dir /Users/hue/code/dopemux-mvp, compose.yml): ~22 services incl.
  postgres-age(:5432), redis-events(:6379), redis-primary(:6380), mcp-qdrant(:6333), mcp-conport
  (3004/3005/4004 — currently NOT holding its host ports), mcp-pal(:3003), mcp-pal-stdio, mcp-litellm(:4000),
  mcp-dope-context(:3010), dope-decision-graph-bridge(:3016), task-orchestrator PYTHON service(:8000),
  dopemux-mcp-serena(3006/4006), gptr-mcp(:3009), desktop-commander(:3012), leantime-bridge(:3015),
  dopemux-dope-memory-1 (0.0.0.0:3060->3020), leantime stack.
- Per-worktree override stacks (from ~/.dopemux/mcp/runtime/<slug-hash>/compose.override.yml + mcp.env):
  - `dopemux_dopemux-mvp_6a4f`: conport (127.0.0.1:3004-3005, 4019->4004 — SQUATTING the canonical conport ports),
    dope-memory (3035->3020). Labels: dopemux.managed=true, dopemux.project_id=dopemux-mvp-2e346e2084bca021,
    dopemux.worktree_hash=6a4f, dopemux.scope=worktree, workspace_id=.worktrees/free-lane-20260722_070957.
  - `dopemux_dopemux_mvp_dcd6` (UNDERSCORE variant — naming drift): dope-memory 3054->3020; override lives in
    /private/tmp/dopemux-mcp-dcd6/ (evaporates on reboot).
  - `dopemux_dnh-crm_8d6d`: dope-memory 3020->3020 (squats the DEFAULT dope-memory port).
  - `dnh_crm_tgmirror0117-dope-memory-1` (35104->3020, foreign convention).
- task-orchestrator KOTLIN jar: `task-orchestrator-dnh_crm-9a4e9aa8a329cdd5` on 127.0.0.1:7890, raw docker run,
  no compose labels, dopemux.* labels set by wrapper script. NOTE: currently owned by dNh_CRM project, i.e. the
  reserved singleton port is held by another project right now.
- pal-mcp project: pal-mcp-server (healthy, stdio) + pal-mcp-server-stale-20260721 (UNHEALTHY, stale) from
  /private/tmp/pal-model-refresh.
- Volumes: canonical dopemux_pg_age_data + qdrant volume, PLUS per-instance clones:
  {6a4f, dcd6, dnh-crm_8d6d AND dnh_crm_8d6d (hyphen/underscore DUPLICATE PAIR)} × {pg_age_data, qdrant-data}.
  mcp-task-data volume has NO labels.

## 2. Identity machinery (code)

- project identity (src/dopemux/mcp/project_identity.py:75-114): project_root = git common-dir parent =>
  same project_id for all worktrees of a repo. project_hash=sha256(project_root)[:16];
  project_id=f"{slug}-{hash}".
- worktree_hash = sha1(abspath(worktree))[:4] — DUPLICATED verbatim in port_diagnostics.py:59 and
  port_allocator.py:47 (no shared import).
- FOUR inconsistent naming schemes coexist:
  1) docker_runtime.compose_project_name(): `dopemux_{hyphen-slug}_{worktree_hash}` (lifecycle path).
  2) port_leases._slug(): underscores — same project renders `dopemux_mvp` in lease IDs.
  3) instance_overlay.get_compose_project_name(): `dopemux_{raw dir name}_{instance_id}` (cli wizard path) —
     a DIFFERENT compose project name for the same worktree than #1. Doctor flags this only as WARN
     (DUAL_ALLOCATION_BRAINS / INSTANCE_OVERLAY_NOT_WIRED_TO_INIT).
  4) instance_manager.py lettered A–E scheme, hardcodes task-orchestrator port 8000 (contradicts catalog 7890).
- Ownership classification (docker_inspect.classify_container_ownership:183-273): trust order = dopemux.* labels >
  compose-project heuristic (never full trust) > name/port (never proof). Mismatch => WRONG_PROJECT.
  Unlabeled => DOCKER_CONTAINER_UNLABELED_UNKNOWN => refuse to adopt (lifecycle.py:290-303).
- Blocking: BLOCKING_FINDING_CODES (lifecycle.py:38-57) blocks on CODE MEMBERSHIP regardless of severity;
  DOCKER_UNAVAILABLE (emitted severity UNKNOWN on docker ps timeout) hard-blocks start identically to a real
  foreign-container conflict.
- Discovery: subprocess `docker ps --format {{json .}}` with 25s timeout (docker_inspect.py:148), invoked
  TWICE per start (doctor.py:740 + lifecycle.py:578) => up to ~50s stall per command; fleet doctor loops
  per-worktree with no caching. Timeout => DOCKER_UNAVAILABLE => hard block. (This is the "discovery timeout"
  the operator hit; docker itself was fine.)
- `dopemux mcp init` does NOT run the ownership gate at all (mcp_commands.py:1264-1360); its fail-closed comes
  from the port allocator RuntimeError. `dopemux mcp start` runs run_lifecycle() preflight which IS the gate.
- gate.py "Phase 0 DiscoveryGate" is misnamed: runs AFTER compose up in cli.py:3856, checks tool reachability
  from a THIRD config surface (.dopemux/mcp.instances.toml via resolver.py), never checks ownership.
- config_repair.py: plan/apply for .mcp.json + .envrc.dopemux-mcp; states PLANNED/APPLIED/NOOP/BLOCKED/UNKNOWN;
  secret-like or parse errors => BLOCKED, no writes. Non-atomic across the two files (partial-write possible).

## 3. Port allocation & leases

- Registry ~/.dopemux/mcp/runtime/port-leases.json is runtime authority; hash formula
  base + sha1(path)[:4]%100 is only the preferred candidate (100 buckets, collision-prone).
- Allocation order: reserved-singleton path (never leased; identity proved via MCP initialize probe,
  allowlist RESERVED_SINGLETON_IDENTITY_PREFIX currently ONLY task-orchestrator) → reuse active lease →
  fixed-port services → first-free scan span 100.
- NO GC: mark_released only called on reserved-singleton reconciliation; mark_stale has ZERO callers;
  worktree deletion never touches leases. Live registry: 50 entries, 46 active; ORPHANS confirmed
  (dcd6 conport leases with no container; entire adOps a22d instance); 24 pytest-fixture leases polluting
  the real registry (incl. /Users/alice/... paths).
- Leases NEVER cross-validated against docker ps (two independent checks in run_lifecycle).
- init catch-22 (healthy TO on 7890 looked like unknown occupant) FIXED 2026-07-16 (#1052) via MCP identity
  probe — but docs (mcp-integration-guide.md, last touched AFTER the fix) still describe the old workaround.
- lease_migration.py: adopts legacy envrc hash-ports into leases (one-way).

## 4. Per-server nature & verdicts

| Server | Storage | Identity scoping today | Verdict today |
|---|---|---|---|
| ConPort (3004 REST/3005 SSE/4004 info) | Postgres+AGE (dopemux_knowledge_graph), Redis cache | workspace_id per-request (sound, every table+tool); instance_id from container env DOPEMUX_INSTANCE_ID (BROKEN for shared use — collapses worktrees); fork_instance/promote exist | CAN-SHARE across projects at row level; UNSAFE to share across concurrent worktrees until per-request instance identity lands. Live store already contains foreign-project data + missing provenance (ADR conport-canonical-record-service-v2, accepted, UNIMPLEMENTED) |
| dope-memory (:3020 http) | SQLite chronicle (journal=DELETE via compose override; single conn; sync in async handlers), optional PG mirror off | schema scoped by (workspace_id, instance_id) BUT: DOPEMUX_CAPTURE_LEDGER_PATH env override collapses all workspaces to ONE file; tool params DEFAULT to container-env identity instead of failing closed (3 layers); .mcp.json env blocks cannot reach a running HTTP server | UNSAFE shared. Proven contamination N2 (primary container carried DOPE_MEMORY_WORKSPACE_ID=dNh_CRM). Fix = DMX-MEMSPINE-IDENTITY-005 (fail-closed per-request identity) — NOT implemented |
| task-orchestrator KOTLIN jar (:7890) | SQLite per workspace_id under ~/.local/share/dopemux-mission-control/task-orchestrator/<ws>/current-tasks.db | wrapper script computes workspace_id=repo-basename+sha256(project_root)[:16]; kill-and-replace singleton per workspace; identity via serverInfo.name probe; dopemux.* labels set by script | MUST-BE-PER-PROJECT (workspace-rooted SQLite). Fixed default port 7890 means only ONE project reachable at a time; multi_project_singleton attempt landed 2026-07-21/26 and was REVERTED same day; ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001 (PROPOSED, code merged) keeps single_active_project |
| task-orchestrator PYTHON compose svc (:8000) | no direct SQLite; persists via DopeconBridge custom_data; redis keys workspace_id-scoped | shadow-twin of the jar; .vibe/config.toml points at :8000 (WRONG system) | Shadow-twin. Decide: retire or rename. Not the MCP tool surface. |
| PAL (mcp-pal :3003 http, mcp-pal-stdio compose, pal-mcp-server off-compose) | none (in-process 3h TTL continuation cache) | continuation_id unscoped, process-local | STATELESS. 3 deployments; only off-compose pal-mcp-server is consumed (Codex docker-exec's it, required=true); feature-register says RETIRE pal-http; compose pal-stdio has zero consumers |
| Serena (3006/4006) | ~/.serena shared cache | ONE workspace bind-mounted at container start (${DOPEMUX_WORKSPACE_ROOT}:/workspace:ro); wrapper = mcp-proxy stdio→SSE, workspace detected from cwd | MUST-BE-PER-INSTANCE in deployed form; real LSP CPU/mem per instance. In-repo multi-workspace wrapper exists but NOT deployed |
| dope-context (:3010) | Qdrant collections code_<md5(path)>/docs_<md5(path)> + __manifest__ compatibility gate (fail-closed, #1139) | per-call workspace_path; HOST_CODE_PARENT_DIR mounts parent of ALL checkouts | CAN-SHARE (true multi-tenant). Sole owner of HOST_* mounts |
| qdrant | per-workspace collections | — | CAN-SHARE |
| redis-primary | workspace_id-prefixed keys (TO python svc verified; others UNKNOWN) | — | CAN-SHARE (verify other consumers) |
| redis-events | no workspace scoping found in event streams | — | UNKNOWN — treat as single-project until proven |
| postgres-age | DB-level tenancy (dopemux_knowledge_graph, litellm); intra-graph workspace partitioning UNKNOWN | — | CAN-SHARE at DB level |
| litellm(:4000), gptr(:3009), exa(:3011), desktop-commander(:3012), leantime-bridge(:3015), dopecon-bridge(:3016) | mostly stateless/proxy | — | singletons per catalog |

## 5. Documented decisions & constraints (do not contradict without saying so)

- mcp_catalog.yaml is single source of truth (ADR-MCPINT-001); scope: singleton servers live in ~/.claude.json;
  per_worktree = [conport, dope-memory, task-orchestrator] in per-worktree .mcp.json.
- NO prior ADR makes ConPort/dope-memory shared-canonical. The user's pasted narrative assumed the architecture
  "evolved toward canonical shared services" — the doc record does NOT support that; what exists is
  ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001 (peer instances visible + non-blocking, NOT shareable) and the
  same-day revert of shared-TO.
  **CORRECTION (supervisor, 2026-07-28)**: the shared-TO revert rationale is NOT unknown. PR #1086 was closed
  because it bundled an unapproved Task Orchestrator authority change (`multi_project_singleton`) with the
  peer-project preflight repair — a governance rejection of that direction, not proof that multi-project TO
  operation is technically unsafe. Ruled end-state (design §10.1): project-scoped leased-port TO instances via
  a new ADR; `multi_project_singleton` stays not authorized.
- Env-var identity over shared HTTP declared "unimplementable" by the 2026-07-03 fleet audit; per-request
  identity (HRD-IDENTITY-009 / MEMSPINE-IDENTITY-005 / ConPort CRS v2 RLS) is the agreed direction, all queued.
- ChatGPT facade (ADR-DCP-MCP-RO-0009): opaque target_id, must never leak worktree hashes/ports.
- Transport truths (AGENTS.md §12): conport SSE GET /sse; dope-memory/TO/pal/serena/dope-context Streamable
  HTTP POST /mcp; 406 on GET /mcp is CORRECT.
- instance-state-persistence.md documents the dead lettered A–E model; instance_manager.py still implements it.
- Catalog drift: catalog says version:1 (ADR mandated 2); legacy registry.yaml still present though ordered killed.
- .envrc.dopemux-mcp at main checkout (dcd6): CONPORT_MCP_PORT=3007 etc. — main checkout itself is a leased
  "instance", not pointed at canonical 3005.
- Multi-instance base-port doc scheme A=3000/B=3030/C=3060/D=3090/E=3120 explains dopemux-dope-memory-1 on 3060.

## 6. Operator symptoms to explain/fix (from user's context)

- init generated .envrc/.mcp.json then rolled back to fail-closed because running conport/dope-memory containers
  (6a4f) could not be proven canonical for THIS worktree; TO passed via MCP handshake probe.
- Docker JSON discovery "timeout" while plain docker worked => the 25s×2 subprocess stalls + hard-block coupling.
- Wants: seamless multi-project/multi-worktree operation, no perf cripple, correct read/write scoping.
