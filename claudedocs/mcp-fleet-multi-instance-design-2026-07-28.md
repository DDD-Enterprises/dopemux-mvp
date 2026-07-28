# DESIGN: dopemux MCP fleet — multi-instance / multi-project / multi-worktree operation

**Status**: DRAFT for operator sign-off
**Date**: 2026-07-28
**Evidence base**: [`mcp-fleet-multi-instance-evidence-2026-07-28.md`](mcp-fleet-multi-instance-evidence-2026-07-28.md) (seven read-only research agents, file:line verified). Legacy launch-path file list for P-22/P-23: [`mcp-legacy-launch-path-worklist-2026-07-28.md`](mcp-legacy-launch-path-worklist-2026-07-28.md).
**Citation form**: `EV §n` = section of the evidence file; `file.py:NN` = line cited there. Spot-checks re-run in this
worktree are marked `[spot-checked]`.
**Authority**: `mcp_catalog.yaml` remains single source of truth (ADR-MCPINT-001). Where this design overrides an
existing ADR it says so explicitly in §10.

---

## 0. Problem statement (one paragraph)

The fleet was designed as a set of host singletons, then grew per-worktree instances bolted on through a second
(and third, and fourth) naming scheme. Today a single repo can have containers under four different identity
conventions, a lease registry with no garbage collector and 24 pytest-injected rows, canonical ports squatted by
a stale worktree stack, and a start path that hard-fails on a transient `docker ps` timeout as if it were a
security violation (EV §1, §2, §3). The operator's symptom — `init` rolls back to fail-closed while `docker ps`
works fine by hand — is the direct product of two design defects: **ownership can only be proven by labels that
the legacy launch paths never applied**, and **discovery unavailability is coded as an ownership conflict**.

This design fixes identity, ports, discovery, scoping, and lifecycle as one coherent system, and separates what
is *safe today* from what becomes safe once two already-queued packets (MEMSPINE-IDENTITY-005, ConPort CRS v2)
land.

---

## 1. Target topology

### 1.1 Sharing classes (definitions — normative)

| Class | Meaning | Count | Ports | Labels `dopemux.scope` |
|---|---|---|---|---|
| **host-singleton** | Exactly one container per host, shared by every project and worktree. Tenancy enforced *inside* the server (per-request identity or per-tenant storage keys). | 1 | fixed, from catalog `reserved_port` | `host` |
| **project-scoped** | One container per project (= git common-dir root, so all worktrees of a repo share it). | 1 per project | leased per project | `project` |
| **worktree-scoped** | One container per worktree checkout. | 1 per worktree | leased per worktree | `worktree` |
| **retired** | Must not be started by any path; removal is a migration step. | 0 | — | — |

A server may have an **interim** class and an **end-state** class separated by a named **gate**. The gate is a
merged, verified packet — never a date, never a judgement call.

### 1.2 The table

| Server | Interim class | End-state class | Gate to flip | Defense |
|---|---|---|---|---|
| **postgres-age** (:5432) | host-singleton | host-singleton | — | Tenancy is DB-level (`dopemux_knowledge_graph`, `litellm`) and already multi-tenant in production use (EV §4). Intra-graph workspace partitioning is UNKNOWN, but that is ConPort's problem, not Postgres's: the DB engine is not the isolation boundary being violated. Per-instance `pg_age_data` volume clones exist today (EV §1) and are pure waste — they duplicate the engine, not the tenancy. |
| **redis-primary** (:6380) | host-singleton | host-singleton | — | Keys are `workspace_id`-prefixed (verified for the TO python service; other consumers UNKNOWN — EV §4). Cost of a per-worktree redis is a whole process for a keyspace that is already namespaced. Residual risk is a consumer that writes unprefixed keys; §9 packet P-21 adds a key-prefix lint. |
| **redis-events** (:6379) | host-singleton **(single-project)** | host-singleton (multi-project) | P-21 event-stream project prefix + consumer audit | No workspace scoping was found in the event streams (EV §4). Streams are advisory telemetry, not an authority surface (Truth Order: runtime > docs, but events are neither), so cross-project bleed degrades dashboards, it does not corrupt state. That justifies sharing the process now while *forbidding* any new consumer from treating events as authoritative until prefixes land. **OPEN** — see §10.4. |
| **qdrant** (:6333) | host-singleton | host-singleton | — | Collections are per-workspace (`code_<md5(path)>` / `docs_<md5(path)>`) with a `__manifest__` compatibility gate that already fails closed (#1139, EV §4). Tenancy is in the collection name; the engine is genuinely multi-tenant. Per-instance `qdrant-data` volume clones (EV §1) destroy the shared index for no isolation benefit and force re-embedding per worktree — a direct cost, since embeddings are paid work. |
| **dope-context** (:3010) | host-singleton | host-singleton | — | The only server in the fleet that is *already* correct multi-tenant: `workspace_path` is a per-call parameter, and it is the sole owner of the `HOST_*` parent-directory mounts covering all checkouts (EV §4). Running one per worktree would multiply embedding cost and defeat the shared Qdrant index. |
| **litellm** (:4000) | host-singleton | host-singleton | — | Stateless proxy over provider credentials; per-project instances multiply credential surface with zero isolation gain (EV §4). |
| **gpt-researcher** (:3009) | host-singleton | host-singleton | — | Stateless / external-provider `identity_scope` in the catalog [spot-checked `default_catalog.yaml:140-152`]. |
| **exa** (:3011) | host-singleton | host-singleton | — | Stateless external-provider proxy (EV §4). |
| **desktop-commander** (:3012) | host-singleton | host-singleton | — | `identity_scope: host-session` [spot-checked `default_catalog.yaml:123-130`]; it *is* the host. Per-project copies are meaningless. |
| **leantime-bridge** (:3015) | host-singleton | host-singleton | — | Bridge to a single external Leantime instance (EV §4). |
| **dopecon-bridge / decision-graph-bridge** (:3016) | host-singleton | host-singleton | — | Stateless bridge; persists through ConPort custom_data, so its tenancy is inherited from ConPort's (EV §4). |
| **pal — `mcp-pal` HTTP (:3003)** | **retired** | retired | — | PAL is stateless (in-process 3h continuation cache, process-local `continuation_id`) and the feature-register already says RETIRE pal-http (EV §4). Three deployments of a stateless server is pure surface. |
| **pal — `mcp-pal-stdio` (compose)** | **retired** | retired | — | Zero consumers (EV §4). |
| **pal — `pal-mcp-server` (off-compose)** | host-singleton **(adopt into managed fleet)** | host-singleton | P-07 adoption | This is the only PAL actually consumed (Codex `docker exec`s it, `required=true` — EV §4). It currently runs from `/private/tmp/pal-model-refresh`, i.e. outside compose, unlabeled, and it has a stale UNHEALTHY twin `pal-mcp-server-stale-20260721`. Stateless ⇒ safe to share; the work is bringing it under labels and a compose file, not changing its class. |
| **serena** (3006/4006) | **worktree-scoped** | host-singleton | P-20: deploy the in-repo multi-workspace wrapper + per-call workspace routing | As deployed, exactly one workspace is bind-mounted read-only at container start (`${DOPEMUX_WORKSPACE_ROOT}:/workspace:ro`) and the wrapper detects the workspace from cwd (EV §4). That is a *container-construction-time* binding — no per-request escape exists, so sharing is not a policy choice, it is impossible. An in-repo multi-workspace wrapper exists but is NOT deployed (EV §4); deploying it is the gate. Until then serena is worktree-scoped **and rate-limited** (§6) because each instance is a real LSP with real CPU/RAM. |
| **conport** (3004 REST / 3005 SSE / 4004 info) | **worktree-scoped** | host-singleton | **ConPort CRS v2**: per-request `instance_id` + RLS (ADR `conport-canonical-record-service-v2`, accepted, UNIMPLEMENTED) | `workspace_id` is already a sound per-request parameter on every table and tool, so cross-*project* rows are safe at the row level. The break is `instance_id`, which comes from the container env `DOPEMUX_INSTANCE_ID` — one value per process, so every concurrent worktree hitting one container collapses into one instance (EV §4). Sharing today would silently merge worktree histories; the live store *already* contains foreign-project data with missing provenance (EV §4). Therefore: per-worktree until CRS v2, then host-singleton. |
| **dope-memory** (:3020) | **worktree-scoped** | host-singleton | **DMX-MEMSPINE-IDENTITY-005**: fail-closed per-request identity | Schema is scoped by `(workspace_id, instance_id)` — correct in principle. In practice three layers defeat it: `DOPEMUX_CAPTURE_LEDGER_PATH` collapses all workspaces to one ledger file; tool params *default* to container-env identity instead of failing closed; and `.mcp.json` env blocks cannot reach an already-running HTTP server (EV §4). Contamination is not theoretical — the primary container was observed carrying `DOPE_MEMORY_WORKSPACE_ID=dNh_CRM` (EV §4, finding N2). Also SQLite single-connection with sync calls in async handlers, so a shared instance is a serialization point (§6). |
| **task-orchestrator — KOTLIN jar** (:7890) | host-singleton, **single active project** | host-singleton, single active project *(re-open only via §10.1)* | none by default | Storage is workspace-rooted SQLite under `~/.local/share/dopemux-mission-control/task-orchestrator/<workspace_id>/current-tasks.db`, so *storage* is per-project-safe. The blocker is the fixed reserved port 7890, meaning one project is reachable at a time, and the wrapper implements kill-and-replace (EV §4). A `multi_project_singleton` attempt landed 2026-07-21/26 and **was reverted the same day**; ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001 (PROPOSED, code merged) deliberately keeps `single_active_project` (EV §5). This design **does not override that ADR**. It adds an explicit, fast `dopemux mcp switch-project` (§7) so the constraint is legible instead of manifesting as "TO is answering for the wrong repo" — which is exactly today's state, since 7890 is currently held by dNh_CRM (EV §1). |
| **task-orchestrator — PYTHON compose svc** (:8000) | **retired** (rename-only fallback) | retired | operator sign-off §10.2 | Shadow twin: it is not the MCP tool surface, holds no direct SQLite, and persists via DopeconBridge custom_data (EV §4). Its only real consequence is that `.vibe/config.toml` points at `:8000` — i.e. a live config aims at the wrong system. Keeping a service whose sole distinguishing behaviour is being confused for another service is a defect, not a feature. If it has a non-orchestrator function worth keeping, it must be renamed (`dopecon-taskbridge`) and stripped of the `task-orchestrator` name and port. **OPEN** — §10.2. |

### 1.3 Consequences of the interim state (state this plainly)

While ConPort, dope-memory and serena are worktree-scoped, **N worktrees cost 3N containers**. That is the price
of correctness under the current server implementations, and §6 bounds it with on-demand start + idle reaping.
The end-state collapses those 3N to 3 host singletons. Both identity gates are already queued work
(MEMSPINE-IDENTITY-005, CRS v2 — EV §5); this design's job is to make the flip a *config change*, not a rewrite.

---

## 2. Identity model

### 2.1 Kill the four schemes

Today four naming schemes coexist (EV §2):

| # | Scheme | Where | Fate |
|---|---|---|---|
| 1 | `dopemux_{hyphen-slug}_{worktree_hash}` | `docker_runtime.compose_project_name()` | **CANONICAL** — becomes the one true form (hyphen slug preserved; see §2.2 rule) |
| 2 | underscore slug (`dopemux_mvp`) | `port_leases._slug()` [spot-checked `port_leases.py:88`] | kept *internally* for lease IDs, but **derived** from the canonical slug, never computed independently |
| 3 | `dopemux_{raw dir name}_{instance_id}` | `instance_overlay.get_compose_project_name()` (CLI wizard path) | **DELETED** — produces a different compose project for the same worktree; doctor only WARNs (`DUAL_ALLOCATION_BRAINS`, `INSTANCE_OVERLAY_NOT_WIRED_TO_INIT`) |
| 4 | lettered A–E, hardcodes TO port 8000 | `instance_manager.py` (+ `instance-state-persistence.md`) | **DELETED** — contradicts catalog port 7890; the A/B/C/D/E base-port doc scheme is why `dopemux-dope-memory-1` sits on 3060 (EV §5) |

### 2.2 One module: `src/dopemux/mcp/identity.py`

All identity derivation moves into a single module. Every other module imports it; **no module may recompute a
hash, slug, or name.** `project_identity.py` is absorbed (its `resolve_project_identity` becomes the internal
resolver; `worktree_hash` currently duplicated verbatim in `port_diagnostics.py:59` and `port_allocator.py:47`
(EV §2) is deleted from both).

```
canonical_slug(name)          -> hyphen-lowercase, [a-z0-9-], collapse runs, strip edges
project_root(cwd)             -> parent of `git rev-parse --git-common-dir`  (all worktrees share it)
project_hash(root)            -> sha256(abspath(root))[:16]
project_id(root)              -> f"{canonical_slug(root.name)}-{project_hash(root)}"
worktree_root(cwd)            -> `git rev-parse --show-toplevel`
worktree_hash(wt)             -> sha1(abspath(wt))[:4]
compose_project_name(scope)   -> host:     "dopemux"
                                 project:  f"dopemux_{canonical_slug}_{project_hash[:4]}"
                                 worktree: f"dopemux_{canonical_slug}_{worktree_hash}"
lease_slug(...)               -> underscore(canonical_slug(...))   # derived, not independent; lease IDs only
lease_id(service, role, wt)   -> f"{lease_slug}_{worktree_hash}_{service}_{role}"
container_name(service,scope) -> f"{compose_project_name(scope)}-{service}-1"   # compose native
volume_name(vol, scope)       -> f"{compose_project_name(scope)}_{vol}"          # compose native
labels(service, scope)        -> dict (below)
```

**Rule**: the compose project name keeps the **hyphen slug** inside `dopemux_{slug}_{hash}` — i.e. today's
`docker_runtime.compose_project_name()` form (`dopemux_dopemux-mvp_6a4f`), which is what the live labeled
containers and the majority of existing volumes already use. Changing the separator would rename every compose
project and orphan every existing project-prefixed volume — recreating the exact duplicate-volume bug this
design closes. The underscore transform exists **only** inside `lease_slug` for lease IDs, and it is *derived*
from `canonical_slug`, never recomputed from raw input. The hyphen/underscore duplicate volume pairs observed
live (`dnh-crm_8d6d` **and** `dnh_crm_8d6d` — EV §1) came from two callers disagreeing about separator; the fix
is one derivation chain, not a new separator.

### 2.3 Mandatory label set

Every managed container MUST carry all of these. Missing any one ⇒ `UNLABELED_UNKNOWN` ⇒ not adoptable without
explicit `adopt` (§7).

| Label | Example | Purpose |
|---|---|---|
| `dopemux.managed` | `true` | fleet membership |
| `dopemux.label_schema` | `2` | migration discriminator (schema 1 = today's partial labels) |
| `dopemux.service` | `conport` | catalog key — the join to `mcp_catalog.yaml` |
| `dopemux.scope` | `host` \| `project` \| `worktree` | sharing class from §1 |
| `dopemux.project_id` | `dopemux-mvp-2e346e2084bca021` | project identity |
| `dopemux.project_slug` | `dopemux-mvp` | human-readable |
| `dopemux.project_root` | `/Users/hue/code/dopemux-mvp` | proof target for ownership |
| `dopemux.worktree_hash` | `6a4f` | `""` for host/project scope |
| `dopemux.worktree_path` | `/Users/.../worktrees/free-lane-...` | `""` for host/project scope |
| `dopemux.compose_project` | `dopemux_dopemux-mvp_6a4f` | cross-check against docker's own label |
| `dopemux.catalog_version` | `2` | detects containers built from a stale catalog |
| `dopemux.created_at` | RFC3339 | reaping / staleness |
| `dopemux.lease_ids` | comma-separated | cross-validation against the lease registry (§3) |

Host-singleton containers carry `dopemux.scope=host`, empty `worktree_hash`/`worktree_path`, and
`project_id=__host__`. **A host-scoped container is never a WRONG_PROJECT conflict** — that is the single most
important semantic change in this section, because today ownership classification treats any project mismatch as
a conflict (`classify_container_ownership:183-273`, EV §2).

### 2.4 Migration of existing containers & volumes

| Situation | Action |
|---|---|
| Container has `dopemux.*` schema-1 labels (e.g. the `6a4f` stack — EV §1) | `dopemux mcp migrate --relabel`: recreate under the canonical compose project with schema-2 labels. Docker cannot mutate labels on a live container, so relabel = stop + recreate; volumes are preserved by name. |
| Container correct-but-unlabeled (e.g. `pal-mcp-server`, TO jar's raw `docker run`) | `dopemux mcp adopt <service>` with proof (§7) — writes a **sidecar adoption record** in `~/.dopemux/mcp/runtime/adoptions.json` and schedules relabel-on-next-restart. Never silent. |
| Foreign convention (`dnh_crm_tgmirror0117-dope-memory-1` — EV §1) | Out of scope for this repo's fleet; `doctor` reports it as `FOREIGN_CONVENTION` (INFO, non-blocking) provided it is not on a port we need. |
| Duplicate hyphen/underscore volume pairs | `dopemux mcp migrate --volumes`: for each pair, pick the one with the later mtime **and** non-zero size, `docker run --rm -v old:/from -v new:/to alpine cp -a`, verify, then `docker volume rm` the loser only after an explicit `--prune-losers` second invocation. Reversible until prune. |
| Unlabeled volumes (`mcp-task-data` — EV §1) | Cannot be labeled in place; recreate-with-copy under `migrate --volumes`, or leave and record in `adoptions.json` as `legacy-unlabeled` (INFO). |
| Override dirs in `/private/tmp` (dcd6 — EV §1) | Relocated to `~/.dopemux/mcp/runtime/<compose_project>/` by `migrate`. `/private/tmp` evaporates on reboot, so any stack there is by construction unmanageable. |

---

## 3. Port model

### 3.1 Three port tiers

| Tier | Who | Source | Leased? |
|---|---|---|---|
| **Fixed singleton** | every host-singleton in §1 | catalog `reserved_port` | never leased; registered in the lease registry as `reserved` rows only so collisions are *detectable* |
| **Reserved singleton (identity-probed)** | task-orchestrator :7890 | catalog `port_policy: reserved_singleton` [spot-checked `default_catalog.yaml:390-402`] | never leased; ownership proven by MCP `initialize` probe |
| **Leased** | every project-scoped and worktree-scoped service | `port-leases.json` (runtime authority) | yes |

The hash formula `base + sha1(path)[:4] % 100` remains only a **preferred candidate**, not an allocation (EV §3).
100 buckets is collision-prone by design; the registry is the authority. No change needed here — the defect is
not the formula, it is the absence of GC.

### 3.2 Extend the identity-probe allowlist

`RESERVED_SINGLETON_IDENTITY_PREFIX` currently contains **only** task-orchestrator [spot-checked
`port_allocator.py:33`]. Every host-singleton that speaks MCP must be added, keyed by the `serverInfo.name`
prefix it returns on `initialize`:

| Service | Port | Probe | Notes |
|---|---|---|---|
| task-orchestrator | 7890 | `initialize` → `serverInfo.name` prefix | existing |
| conport | 3005 | SSE `GET /sse` handshake (AGENTS.md §12) | different transport — probe adapter needed |
| dope-memory | 3020 | `POST /mcp` streamable HTTP | 406 on `GET /mcp` is CORRECT, not evidence of SSE (EV §5) |
| dope-context | 3010 | `POST /mcp` | |
| serena | 3006/4006 | `POST /mcp` | |
| gpt-researcher / exa / desktop-commander / leantime-bridge / dopecon-bridge | per catalog | per catalog transport (`POST /mcp` for streamable HTTP, `GET /sse` handshake for SSE) | |

Non-MCP infra (postgres, redis×2, qdrant, litellm) gets a **protocol probe** instead: `PING`/`SELECT 1`/`GET
/readyz`. Same trust tier as the MCP probe: *proves the port serves the expected service*, does **not** prove
project ownership. Ownership still requires labels (§4.2).

### 3.3 Lease garbage collection

Current state: `mark_released` is called only during reserved-singleton reconciliation, `mark_stale` has **zero
callers**, and worktree deletion never touches leases; the live registry has 50 rows / 46 active with confirmed
orphans (dcd6 conport leases with no container; an entire adOps `a22d` instance) (EV §3).

Wire it:

| Trigger | Call | Effect |
|---|---|---|
| `dopemux mcp stop` (worktree scope) | `mark_released(lease_id)` | lease freed immediately |
| worktree deletion hook (`git worktree remove` wrapper + `dopemux worktree rm`) | `mark_released` for every lease whose `worktree_path` no longer exists | primary orphan source closed |
| `dopemux mcp reconcile` | `mark_stale` for any active lease with no matching container in the discovery snapshot | stale ≠ released: stale rows are retained for audit, excluded from allocation, purged after 7 days |
| `reconcile --purge` | delete `stale` rows older than the retention window | operator-driven |
| startup of any command | nothing (never GC implicitly — GC on read is how you lose a lease mid-allocation) | |

**Cross-validation** is the new invariant: `reconcile` performs the join that today does not exist — leases are
*never* checked against `docker ps` (EV §3). For each active lease, look up the container by
`dopemux.lease_ids`. Four outcomes:

| Lease | Container | Verdict |
|---|---|---|
| active | present, labels match | `OK` |
| active | absent | `LEASE_ORPHANED` → `mark_stale` |
| active | present, different project/worktree | `LEASE_STOLEN` → **FAIL**, operator decision required |
| absent | present, holds a port in a leased range | `PORT_SQUATTED` → offer `adopt` |

The live `6a4f` conport stack squatting canonical 3004/3005 is a `PORT_SQUATTED` on a *fixed-singleton* port —
the most severe variant, since it blocks the host singleton. `reconcile` must classify fixed-singleton squatting
as **FAIL with a named remedy** (`dopemux mcp migrate --evict 6a4f`), not as a generic conflict.

### 3.4 pytest isolation

24 pytest-fixture leases (including `/Users/alice/...` paths) are polluting the real registry (EV §3). Cause:
`default_lease_registry_path()` [spot-checked `port_leases.py:35`] resolves to `~/.dopemux/...` regardless of
test context.

Fix, in order of strength:
1. `PortLeaseRegistry.load()` honours `DOPEMUX_LEASE_REGISTRY_PATH`; an autouse session fixture in
   `tests/conftest.py` points it at `tmp_path`.
2. `default_lease_registry_path()` **raises** if `PYTEST_CURRENT_TEST` is set and the env override is absent —
   fail closed, so a new test cannot silently reacquire the habit.
3. `reconcile --purge-synthetic` one-shot: drop rows whose `worktree_path` does not exist **and** whose path is
   outside every configured project root. This removes the existing 24 without touching real leases.

---

## 4. Discovery & the ownership gate

### 4.1 Kill the 25s × 2 stall

Today: `docker ps --format {{json .}}` with a **25s** timeout (`docker_inspect.py:148`), invoked **twice** per
start (`doctor.py:740` + `lifecycle.py:578`) ⇒ up to ~50s; fleet doctor loops per worktree with no caching
(EV §2).

Target:

| Property | Value |
|---|---|
| Snapshot | one `DiscoverySnapshot` object per **command invocation**; a fleet run over N worktrees uses **one** snapshot for all N |
| Cache | in-process, plus an on-disk snapshot at `~/.dopemux/mcp/runtime/discovery-snapshot.json` with a **3s** TTL, so back-to-back commands (`init` then `start`) reuse it |
| Timeout | **5s** per attempt |
| Retry | 3 attempts, backoff 0.25s / 1s (total worst case ~16s, down from ~50s) |
| Content | one `docker ps --all --no-trunc --format {{json .}}` **plus** one batched `docker inspect` over the returned IDs for labels/mounts/ports — two calls total, not per-container |
| Invalidation | any command that mutates docker state (`start`, `stop`, `migrate`, `adopt`) invalidates the on-disk snapshot on completion |

### 4.2 Decouple unavailability from conflict

Today `BLOCKING_FINDING_CODES` (`lifecycle.py:38-57`) blocks on **code membership regardless of severity**, and
`DOCKER_UNAVAILABLE` (emitted at severity UNKNOWN on timeout) hard-blocks `start` identically to a genuine
foreign-container conflict (EV §2). This is the operator's reported failure.

New model — blocking is a function of **(class, severity)**, not code membership:

| Finding class | Example codes | Behaviour |
|---|---|---|
| `TRANSIENT` | `DOCKER_UNAVAILABLE`, `PROBE_TIMEOUT` | after retries exhausted: **WARN + degrade**. `start` proceeds in *degraded mode*: it will not claim any port it cannot prove free, so it starts only services whose ports bind successfully (bind failure is itself proof of occupancy). Exit code 0 with a `DEGRADED` banner. |
| `OWNERSHIP` | `WRONG_PROJECT`, `LEASE_STOLEN`, `PORT_SQUATTED` (fixed-singleton) | **hard FAIL**, named remedy in the message |
| `UNKNOWN_OWNER` | `DOCKER_CONTAINER_UNLABELED_UNKNOWN` | **hard FAIL** with the `adopt` remedy quoted verbatim (today: refuse with no path forward — `lifecycle.py:290-303`, EV §2) |
| `ADVISORY` | `FOREIGN_CONVENTION`, `CATALOG_VERSION_DRIFT` | INFO, never blocks |

`--strict` promotes TRANSIENT to blocking, for CI. Default is degrade, because *a human at a terminal being
unable to start their fleet because docker was slow* is a worse failure than an unproven port claim that will
fail loudly at bind time anyway.

### 4.3 Ownership proof hierarchy (normative)

Ordered; first conclusive answer wins. This formalizes what `classify_container_ownership:183-273` already
approximates (EV §2).

1. **`dopemux.*` labels, schema 2** → conclusive. Compare `project_id` + `worktree_hash` + `scope`.
   `scope=host` matches every caller.
2. **`dopemux.*` labels, schema 1** (partial — today's `6a4f`) → conclusive *for refusal*, inconclusive for
   adoption: enough to say "not mine", not enough to say "mine". Emits `LABEL_SCHEMA_STALE` + `migrate` remedy.
3. **MCP / protocol identity probe** → proves *what* is listening, never *whose* it is. Sufficient to satisfy the
   reserved-singleton path (that is exactly the #1052 fix, 2026-07-16 — EV §3); insufficient for leased ports.
4. **compose-project label heuristic** (`com.docker.compose.project`) → corroborating only, never trusted alone.
5. **name / port** → never proof (unchanged).
6. Otherwise → **refuse**, with `adopt` as the named path.

### 4.4 `init` must run the gate

`dopemux mcp init` does **not** run the ownership gate at all today; its fail-closed behaviour is an incidental
side effect of the port allocator's `RuntimeError` (`mcp_commands.py:1264-1360`, EV §2) — which is why the
operator saw config generated and then rolled back. `init` will call the **same** `run_preflight(snapshot)` that
`start` calls, in `--dry-run` posture: it reports and refuses to write config, but never mutates docker. There is
no defensible reason for two gates.

### 4.5 Rename the misnamed Phase 0 gate

`gate.py` "Phase 0 DiscoveryGate" runs **after** `compose up` (`cli.py:3856`), checks tool *reachability* from a
third config surface, and never checks ownership (EV §2). It is a post-start readiness check wearing a
preflight's name.

- Rename to **`ReadinessGate`**, move to `readiness.py`, and re-label its phase as **Phase 3 (post-start)**.
- The name `DiscoveryGate` is retired, not reused, so no doc or log line silently changes meaning.
- New **Phase 0 = `OwnershipPreflight`** in `lifecycle.py`, shared by `init` / `start` / `doctor` / `reconcile`.

### 4.6 Unify the three config surfaces

| Surface | Today | Target |
|---|---|---|
| `mcp_catalog.yaml` | single source of truth per ADR-MCPINT-001 (EV §5) | **unchanged — remains the only hand-edited source** |
| `.mcp.json` + `.envrc.dopemux-mcp` | generated by `config_repair.py`, non-atomic across the two files (EV §2) | **generated artifact**; generation becomes atomic: write both to `.tmp`, `fsync`, then rename both; on any failure remove both temps and leave originals untouched |
| `.dopemux/mcp.instances.toml` (read by `resolver.py`) | a **third** independent surface the readiness gate reads (EV §2) | **DELETED as an input.** Regenerated from the catalog + lease registry as a read-only artifact for tooling that already parses it, carrying a `# GENERATED — do not edit` header and a `source_digest` of the catalog. `resolver.py` reads generated artifacts only. |
| `registry.yaml` (legacy, ordered killed but still present — EV §5) | present | deleted (packet P-14) |

Catalog drift (`version: 1` where the ADR mandated 2 — EV §5) is fixed in P-01 and enforced: a catalog whose
`version` is not the code's expected version is a hard FAIL, not a warning.

---

## 5. Read/write scoping

### 5.1 Per-server scoping contract

| Server | Scoping key | Where it comes from | Fail-closed rule |
|---|---|---|---|
| ConPort | `workspace_id` (per request) + `instance_id` (per request, **after CRS v2**) | caller passes `workspace_id` explicitly; `instance_id` derived from `identity.py` by the client wrapper | **Interim**: worktree-scoped container, `DOPEMUX_INSTANCE_ID` set at container build from `identity.py`. **End-state**: reject any write whose request lacks `instance_id`; no env fallback. Implementing packet: **ConPort CRS v2** (accepted, unimplemented — EV §4) |
| dope-memory | `(workspace_id, instance_id)` per request | request params only | **End-state**: reject writes with missing/blank identity; delete the container-env default at all three layers; **remove `DOPEMUX_CAPTURE_LEDGER_PATH` entirely** — ledger path must be *derived*: `~/.dopemux/memory/<project_id>/<worktree_hash>/chronicle.db`, never configurable, so no env var can collapse workspaces again (EV §4). Implementing packet: **DMX-MEMSPINE-IDENTITY-005** |
| task-orchestrator (jar) | `workspace_id` = repo-basename + `sha256(project_root)[:16]` | wrapper script | Must be computed by `identity.py`, not re-derived in the wrapper. Mismatch between the running jar's workspace_id and the caller's ⇒ **FAIL with `switch-project` remedy** (today it silently answers for whichever project claimed 7890 — EV §1) |
| dope-context / qdrant | collection `code_<md5(workspace_path)>` / `docs_<...>` + `__manifest__` gate | per-call `workspace_path` | Already fail-closed on incompatible collections (#1139 — EV §4). Add: reject calls whose `workspace_path` is outside the mounted `HOST_CODE_PARENT_DIR` rather than creating an empty collection |
| serena | bind-mounted workspace | container construction | Interim: one workspace per container, enforced by labels. End-state (P-07): per-call workspace, rejected if not in the mount set |
| redis-primary | `workspace_id` key prefix | caller | P-08 lint asserts every key written matches `^dmx:{workspace_id}:` |
| redis-events | **none today** | — | P-08 adds `dmx:{project_id}:` stream prefix. Until then, events are non-authoritative by policy (§1.2) |
| postgres-age | database-level | connection string | unchanged |

### 5.2 The general rule

> **No stateful write may derive its tenancy from process environment.** Identity travels with the request or the
> write is rejected.

This is the single sentence that both queued packets implement, and the reason env-var identity over shared HTTP
was declared unimplementable by the 2026-07-03 fleet audit (EV §5). Any future server added to the catalog must
declare `identity_scope: per-call-*` to be eligible for `host-singleton`.

---

## 6. Performance budget

### 6.1 Known costs

| Cost | Evidence | Consequence |
|---|---|---|
| Serena = a real LSP per worktree (CPU + RAM, index warm-up) | EV §4 | hard cap on concurrent instances |
| dope-memory = SQLite, `journal=DELETE`, single connection, **sync calls in async handlers** | EV §4 | a shared instance serializes; a per-worktree instance is cheap but multiplies file handles |
| ConPort per worktree = a container + Postgres connections against the shared `postgres-age` | EV §1, §4 | connection-pool pressure on one Postgres |
| Qdrant re-embedding if per-instance volumes persist | EV §1 | direct $ cost; fixed by §2.4 volume consolidation |
| `docker ps` discovery | §4.1 | fixed |

### 6.2 Resource policy

| Class | Policy |
|---|---|
| host-singleton | **always-on**, started by `dopemux mcp start --host` (idempotent), never reaped |
| project-scoped | on-demand start, reaped after **60 min** idle |
| worktree-scoped | **on-demand start** on first tool call or explicit `start`; reaped after **20 min** idle |
| serena | additionally **capped at 3 concurrent instances** (`DOPEMUX_SERENA_MAX_INSTANCES`, default 3); exceeding the cap evicts the least-recently-used instance, never refuses the new one |
| conport (worktree) | **lazy** — not started by `init`, only on first ConPort call, until CRS v2 lands. After CRS v2 it becomes a host singleton and this rule is deleted |
| dope-memory (worktree) | lazy, same as conport |

"Idle" = no MCP request for the window, measured by the server's own last-request timestamp where available, else
by container CPU-time delta. Reaping is performed by `dopemux mcp reconcile --reap`, invoked from the existing
session-lifecycle hook path — **not** a daemon (no new always-running process).

### 6.3 Context-switch budget

CLAUDE.md targets **sub-2s context switching**. Decomposition for switching to an already-warm worktree:

| Step | Budget |
|---|---|
| identity resolution (2 git calls, cached per process) | 50 ms |
| discovery snapshot (cache hit, 3s TTL) | 10 ms |
| lease lookup (single JSON read) | 20 ms |
| config artifact read (`.mcp.json`) | 20 ms |
| **total warm switch** | **< 200 ms** |
| cold worktree (3 containers starting) | 8–20 s — **explicitly out of the 2s budget**, reported with a progress banner |

The 2s target applies to *warm* switching only. Claiming it for cold container starts would be dishonest; the
design instead makes warm switching the common case via idle windows longer than a typical task cycle.

---

## 7. Lifecycle UX — command surface

```
dopemux mcp init        # generate config for THIS worktree; runs OwnershipPreflight in dry-run; never mutates docker
dopemux mcp start       # ensure host singletons + this worktree's scoped services
dopemux mcp stop        # stop this worktree's scoped services; release leases. --host also stops singletons
dopemux mcp doctor      # read-only diagnosis; one discovery snapshot; exit 0 unless OWNERSHIP findings
dopemux mcp reconcile   # lease↔docker cross-validation; --reap, --purge, --purge-synthetic
dopemux mcp adopt       # apply labels to a proven-correct unlabeled container
dopemux mcp migrate     # relabel / relocate / consolidate volumes / evict squatters
dopemux mcp switch-project   # (task-orchestrator) kill-and-replace the 7890 jar for this project
```

### 7.1 Behaviour matrix

| State of a required service | `init` | `start` | `doctor` | `reconcile` |
|---|---|---|---|---|
| **missing** (no container, port free) | write config, note "will start on demand" | start it | INFO `NOT_RUNNING` | no-op |
| **healthy, labels match** | write config | no-op | OK | verify lease join |
| **foreign** (labels prove another project/worktree) | **FAIL**, no config written, remedy = `migrate --evict` or use its own worktree | **FAIL** | FAIL `WRONG_PROJECT` | `LEASE_STOLEN` FAIL |
| **unlabeled but correct** (probe identifies the service, port matches, e.g. `pal-mcp-server`) | FAIL with `adopt` remedy | FAIL with `adopt` remedy | FAIL `UNLABELED_UNKNOWN` + remedy | offer `adopt` |
| **ambiguous** (schema-1 labels, e.g. `6a4f`) | FAIL `LABEL_SCHEMA_STALE`, remedy `migrate --relabel` | same | FAIL | same |
| **stale** (lease active, container gone) | proceed (lease reused) | proceed | WARN `LEASE_ORPHANED` | `mark_stale` |
| **docker unavailable** | WARN, write config, mark `DEGRADED` | WARN, degraded start | WARN | abort with retry hint |

### 7.2 Adoption — the missing path

Today an unlabeled container is `DOCKER_CONTAINER_UNLABELED_UNKNOWN` and adoption is simply refused
(`lifecycle.py:290-303`, EV §2). That is why correct, healthy infrastructure (the TO jar, `pal-mcp-server`)
cannot be brought into the fleet without deleting and recreating it.

```
dopemux mcp adopt <service> [--container <id>] [--scope host|project|worktree]
```

Required proof, all four, else refuse:
1. **Protocol probe passes** — MCP `initialize` returns a `serverInfo.name` matching the catalog entry (or the
   infra probe for non-MCP services).
2. **Port matches** the catalog `reserved_port` (host/reserved) or an active lease owned by this identity.
3. **Mount/volume check** — for stateful services, the container's mounts reference this project's paths or the
   canonical shared volume; a container mounting another project's root is refused outright.
4. **Operator confirmation** — interactive `y/N`, or `--yes` which is recorded in the adoption record.

Effect: writes `~/.dopemux/mcp/runtime/adoptions.json` `{container_id, service, scope, identity, proof[], ts,
operator}`, and the container is treated as owned **for this host only**, with a `LABELS_PENDING` advisory until
its next recreate applies real labels. Adoption is never implicit, never a fallback in `start`.

---

## 8. Migration plan (ordered, reversible)

Every step: precondition → command → verification → rollback. Steps are ordered so that each one leaves the fleet
in a runnable state.

| # | Step | Pre | Command | Verify | Rollback |
|---|---|---|---|---|---|
| **M0** | Snapshot everything | — | `docker ps -a --format json > ~/.dopemux/backup/ps-$(date +%s).json`; `docker volume ls > ...`; `cp ~/.dopemux/mcp/runtime/port-leases.json ~/.dopemux/backup/` | files non-empty | — |
| **M1** | Purge synthetic pytest leases (24 rows, incl. `/Users/alice/...` — EV §3) | M0 | `dopemux mcp reconcile --purge-synthetic --dry-run` then without | registry row count drops by exactly the synthetic count; no row with an existing worktree_path removed | restore leases.json from M0 |
| **M2** | Mark orphaned leases stale (dcd6 conport, adOps `a22d` — EV §3) | M1 | `dopemux mcp reconcile --dry-run` → review → `dopemux mcp reconcile` | every `active` lease now joins to a live container | restore from M0 |
| **M3** | Remove the stale PAL twin `pal-mcp-server-stale-20260721` (UNHEALTHY — EV §1) | none | `docker rm -f pal-mcp-server-stale-20260721` | `pal-mcp-server` still healthy; Codex `docker exec` still works | recreate from `/private/tmp/pal-model-refresh` compose (record the file in M0) |
| **M4** | Adopt `pal-mcp-server` into the managed fleet | M3, P-07 merged | `dopemux mcp adopt pal --scope host` | adoptions.json entry; `doctor` no longer reports UNLABELED for pal | delete the adoptions.json entry |
| **M5** | Retire `mcp-pal` (:3003) and `mcp-pal-stdio` | M4 (the consumed PAL is safe) | `docker compose -p dopemux rm -sf pal pal-stdio` (compose service names); remove from compose.yml + catalog | PAL tools still answer via `pal-mcp-server`; nothing references :3003 | `git revert` the compose/catalog commit, `compose up` |
| **M6** | Evict the `6a4f` squatters off canonical conport ports 3004/3005/4004 (EV §1) | M2; operator confirms the `free-lane-20260722_070957` worktree is not in active use | `dopemux mcp migrate --evict 6a4f` (stop stack, release leases, keep volumes) | `lsof -i :3004,:3005` empty; canonical `mcp-conport` can bind | `dopemux mcp start` from that worktree re-creates it with schema-2 labels and **leased** (non-canonical) ports |
| **M7** | Relocate the `dcd6` override stack out of `/private/tmp/dopemux-mcp-dcd6/` (EV §1) | M2 | `dopemux mcp migrate --relocate dcd6` | override + mcp.env now under `~/.dopemux/mcp/runtime/<compose_project>/`; stack restarts from the new path | copy files back to `/private/tmp/...`; note this rollback is lost on reboot, which is the point |
| **M8** | Consolidate hyphen/underscore duplicate volumes (`dnh-crm_8d6d` vs `dnh_crm_8d6d` × {pg_age_data, qdrant-data} — EV §1) | M0; all containers using either volume stopped | `dopemux mcp migrate --volumes --dry-run` (prints winner/loser per pair with mtime+size) → `--volumes` | winner volume mounts; row counts / collection counts match pre-migration | losers still exist (not pruned) — remount the loser |
| **M9** | Prune losing volumes | M8 verified over ≥1 working session | `dopemux mcp migrate --volumes --prune-losers` | `docker volume ls` shows one per pair | **irreversible** — hence the deliberate delay |
| **M10** | Repoint `.vibe/config.toml` off the `:8000` shadow twin onto the jar `:7890` (EV §4) | none | edit `.vibe/config.toml` | vibe commands reach a server whose `serverInfo.name` is the Kotlin TO | `git checkout .vibe/config.toml` |
| **M11** | Retire the python task-orchestrator (:8000) | M10; §10.2 signed off | `docker compose -p dopemux rm -sf task-orchestrator`; remove from compose + catalog | nothing binds :8000; DopeconBridge custom_data unaffected | revert commit + `compose up` |
| **M12** | Resolve TO 7890 ownership (currently held by dNh_CRM — EV §1) | M11 | `dopemux mcp switch-project` from the target repo | `initialize` on 7890 reports this project's `workspace_id` | run `switch-project` from dNh_CRM |
| **M13** | Move `dnh-crm` dope-memory off default 3020 (EV §1) | M2 | from the dnh-crm checkout: `dopemux mcp stop && dopemux mcp start` (now leases a port) | 3020 free for the canonical/host dope-memory | restart the old stack |
| **M14** | Relabel all remaining schema-1 stacks to schema 2 | P-02, P-03 merged | `dopemux mcp migrate --relabel --all` | `doctor` reports zero `LABEL_SCHEMA_STALE` | containers recreate from the previous compose files; volumes untouched |
| **M15** | Point the main checkout at canonical ports (its `.envrc.dopemux-mcp` uses `CONPORT_MCP_PORT=3007` — EV §5) | M6, M14 | `dopemux mcp init --force` in the main checkout | `.envrc.dopemux-mcp` shows 3005 for the SSE port; MCP clients connect | `git checkout` the envrc |
| **M16** | Delete legacy launch paths + `registry.yaml` | P-22, P-14 | see P-22 / P-14 | `grep` finds no non-`dopemux mcp` fleet-start path | revert |

**Reboot note**: M7 must precede any host reboot, or the dcd6 stack's override files are gone and the stack
becomes unmanageable (recoverable only by `migrate --evict`).

---

## 9. Implementation work breakdown

Sonnet-implementable packets. Dependency order is the `Deps` column; packets with the same deps are parallel.

| ID | Title | Files touched | Acceptance criteria | Test strategy | Deps |
|---|---|---|---|---|---|
| **P-01** | Catalog schema v2 + version gate | `mcp/default_catalog.yaml`, `mcp/fleet_catalog.py` | `version: 2`; every entry declares `sharing_class` (host/project/worktree/retired), `identity_scope`, `probe` (mcp/http/redis/postgres/none), optional `reserved_port`. Loader **raises** on version mismatch. | unit: load v1 catalog ⇒ raises; load v2 ⇒ all entries validate against a schema | — |
| **P-02** | `identity.py` — canonical identity module | new `mcp/identity.py`; absorb `mcp/project_identity.py` | All functions in §2.2 exist with the stated signatures; `worktree_hash` deleted from `port_diagnostics.py:59` and `port_allocator.py:47` and imported instead; `lease_slug` derived from `canonical_slug` | unit: golden vectors for slug/hash/compose-name incl. names with `.`, `_`, uppercase, unicode; property test that `lease_slug(x) == underscore(canonical_slug(x))` | P-01 |
| **P-03** | Label schema 2 emission | `mcp/docker_runtime.py`, `mcp/instance_overlay.py` (as deleted caller), compose templates, TO wrapper script | Every container the fleet starts carries all 13 labels of §2.3; a golden test asserts the exact key set | integration: start conport in a tmp worktree, `docker inspect` label set equals golden | P-02 |
| **P-04** | Delete schemes 3 & 4 | delete `mcp/instance_manager.py`, `mcp/instance_overlay.py`; update `docs/.../instance-state-persistence.md` | No import of the deleted modules anywhere; `DUAL_ALLOCATION_BRAINS` / `INSTANCE_OVERLAY_NOT_WIRED_TO_INIT` finding codes removed as unreachable | `grep` guard test in CI; full test suite green | P-03 |
| **P-05** | Discovery snapshot + retry | `mcp/docker_inspect.py`, `mcp/doctor.py`, `mcp/lifecycle.py` | One snapshot per invocation; 5s timeout, 3 attempts; 3s on-disk TTL; batched `docker inspect`; `docker ps` invoked **at most twice per process** (assertable) | unit with a fake docker binary that sleeps: assert wall-clock < 20s worst case and exactly 1 snapshot build; regression test asserting call count | P-01 |
| **P-06** | Finding taxonomy: TRANSIENT vs OWNERSHIP | `mcp/lifecycle.py` (`BLOCKING_FINDING_CODES` → class map), `mcp/doctor.py` | `DOCKER_UNAVAILABLE` ⇒ WARN + degraded start, exit 0; `WRONG_PROJECT` ⇒ FAIL; `--strict` promotes TRANSIENT | unit over the full finding-code table: each code maps to exactly one class; integration: docker unreachable ⇒ start succeeds degraded | P-05 |
| **P-07** | `adopt` command + adoption records | `commands/mcp_commands.py`, new `mcp/adoption.py` | Four-proof gate of §7.2; refuses on any missing proof; writes adoptions.json; `--yes` recorded | unit per proof (each one failing ⇒ refuse); integration: adopt an unlabeled container started by hand | P-03, P-06 |
| **P-08** | `init` runs OwnershipPreflight | `commands/mcp_commands.py:1264-1360`, `mcp/lifecycle.py` | `init` and `start` call the same `run_preflight(snapshot)`; `init` never mutates docker; config write is atomic across `.mcp.json` + `.envrc.dopemux-mcp` (both-or-neither) | integration: foreign container present ⇒ `init` writes nothing and exits non-zero with the remedy string; crash-injection between the two writes leaves both originals | P-06 |
| **P-09** | Lease GC wiring | `mcp/port_leases.py`, `mcp/lifecycle.py`, worktree-removal hook | `mark_released` on stop + worktree removal; `mark_stale` reachable and called by `reconcile`; `mark_stale` has ≥1 caller (assertable) | unit: stop releases; delete worktree releases; test that fails if `mark_stale` call count is 0 | P-02 |
| **P-10** | `reconcile` command (lease↔docker join) | new `mcp/reconcile.py`, `commands/mcp_commands.py` | Implements the 4-outcome table of §3.3 plus `--reap`, `--purge`, `--purge-synthetic`, `--dry-run`; fixed-singleton squatting ⇒ FAIL with named remedy | unit over synthetic snapshot×registry fixtures covering all 4 outcomes; golden dry-run output | P-05, P-09 |
| **P-11** | pytest lease isolation | `mcp/port_leases.py`, `tests/conftest.py` | `DOPEMUX_LEASE_REGISTRY_PATH` honoured; `default_lease_registry_path()` raises under `PYTEST_CURRENT_TEST` without the override | meta-test: run the suite, assert `~/.dopemux/mcp/runtime/port-leases.json` mtime unchanged | P-09 |
| **P-12** | Probe allowlist expansion | `mcp/port_allocator.py:33`, new `mcp/probes.py` | §3.2 table implemented; SSE adapter for conport; redis/postgres/http infra probes; probe result is `service-identity`, never `ownership` | unit against recorded handshakes; a test asserting a probe pass alone never yields `owned` | P-01 |
| **P-13** | Rename DiscoveryGate → ReadinessGate (Phase 3) | `mcp/gate.py` → `mcp/readiness.py`, `cli.py:3856` | Old name absent from code, logs, and docs; phase relabelled 3 | grep guard; snapshot of log output | P-06 |
| **P-14** | Config-surface unification | `mcp/resolver.py`, `mcp/config_repair.py`, delete `mcp/registry.yaml` | `mcp.instances.toml` is generated with a `# GENERATED` header + catalog `source_digest`; `resolver.py` reads generated artifacts only; hand-edits detected via digest mismatch ⇒ WARN + regenerate | unit: hand-edited toml ⇒ digest mismatch detected; resolver has no read path to the catalog | P-01, P-08 |
| **P-15** | `migrate` command | new `mcp/migrate.py` | `--relabel`, `--relocate`, `--volumes` (+`--prune-losers`), `--evict`; every mode has `--dry-run`; volume copy verified by size+file-count before the loser is retained | integration on throwaway volumes: copy fidelity; dry-run mutates nothing | P-03, P-10 |
| **P-16** | Idle reaping + serena cap | `mcp/lifecycle.py`, session-lifecycle hook | 20 min worktree / 60 min project windows; serena LRU eviction at `DOPEMUX_SERENA_MAX_INSTANCES`; no daemon process introduced | unit with injected clock; integration: 4th serena evicts the LRU, never refuses | P-10 |
| **P-17** | dope-memory fail-closed identity (**= MEMSPINE-IDENTITY-005**) | dope-memory server: tool params, ledger path derivation | Writes without `(workspace_id, instance_id)` are **rejected**; `DOPEMUX_CAPTURE_LEDGER_PATH` removed; ledger path derived per §5.1 | unit: write without identity ⇒ error; two workspaces ⇒ two ledger files; env var set ⇒ ignored | P-02 |
| **P-18** | ConPort per-request instance_id (**= CRS v2**) | ConPort server + schema | `instance_id` accepted per request; env fallback removed; RLS per the accepted ADR | contract tests per tool; concurrency test: two worktrees writing simultaneously produce disjoint instance rows | P-02 |
| **P-19** | Flip conport + dope-memory to host-singleton | catalog, compose, `identity.py` scope map | Both become `sharing_class: host`; per-worktree containers stopped and leases released by `reconcile` | integration: two worktrees share one container with disjoint reads/writes | P-17, P-18 |
| **P-20** | Serena multi-workspace deployment | serena wrapper deployment, compose | The in-repo multi-workspace wrapper is deployed; workspace is per-call; calls outside the mount set rejected | integration: two workspaces answered by one container | P-16 |
| **P-21** | redis key/stream prefix audit + lint | consumers of redis-primary/redis-events | Every write key matches `^dmx:{workspace_id}:`; event streams gain `dmx:{project_id}:`; lint in CI | static lint over redis call sites + runtime assertion in tests | P-01 |
| **P-22** | **Legacy launch-path removal** | *(file list from a separate sweep)* | **AC: no path outside `dopemux mcp` can start fleet services.** Concretely: every `docker compose up` / `docker run` / shell wrapper / Makefile target / hook that starts a catalog service is either deleted or converted to shell out to `dopemux mcp start`. A CI guard greps for `docker compose up`/`docker run` outside `src/dopemux/mcp/` and fails on any hit not in an allowlist file with a written justification per entry. | CI grep guard + one integration test per removed path proving the canonical command covers it | P-08, P-15 |
| **P-23** | **Docs + agent-file update** | *(file list from a separate sweep)* | **AC: all docs reference only canonical commands.** No doc describes the pre-#1052 port catch-22 workaround (`mcp-integration-guide.md` was touched *after* the fix and still does — EV §3); no doc references the lettered A–E model, `registry.yaml`, `DiscoveryGate`, `:8000` as the orchestrator, or `instance_manager`. CLAUDE.md / AGENTS.md §12 updated with the sharing-class table. A CI doc-lint greps a deny-list of retired terms. | doc-lint in CI with the retired-term deny-list; manual read of the 5 canonical MCP docs | P-13, P-22 |

**Critical path**: P-01 → P-02 → P-03 → P-05 → P-06 → P-08 → P-10 → P-15 → migration M1–M16.
**Parallel tracks**: {P-17, P-18} (server-side identity, unblocks the end-state flip) and {P-22, P-23} (cleanup)
can run alongside the core path.

---

## 10. Risks & open decisions

### 10.1 OPEN — Does task-orchestrator ever become multi-project? *(operator sign-off)*

The jar's *storage* is already per-project-safe (workspace-rooted SQLite — EV §4). Only the fixed port 7890 and
the kill-and-replace wrapper enforce single-active-project. A per-project leased-port TO is therefore
*technically* small work. But `multi_project_singleton` landed and was reverted the same day (2026-07-21/26), and
ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001 deliberately keeps `single_active_project` (EV §5). **This design does not
override that ADR.** The interim and end-state both keep single-active-project plus an explicit
`switch-project`. Re-opening requires: (a) the revert's stated reason recovered from the PR record — currently
**UNKNOWN**, and this is the blocking unknown; (b) a new ADR. Do not let an implementation agent "fix" this
opportunistically.

### 10.2 OPEN — Retire or rename the python task-orchestrator (:8000)? *(operator sign-off)*

Retire is the recommendation (§1.2). Rename-to-`dopecon-taskbridge` is the fallback **if** it has a consumer
other than `.vibe/config.toml`. **UNKNOWN**: whether anything besides `.vibe` targets :8000. A consumer sweep is
a precondition to M11; M10 (repointing `.vibe`) is safe either way and should ship first.

### 10.3 OPEN — Is ConPort host-singleton the right long-term end-state, or per-worktree forever?

This design says host-singleton after CRS v2. The counter-argument is real: ConPort is the canonical decision
record, its live store *already* contains foreign-project data with missing provenance (EV §4), and a shared
instance makes the blast radius of an identity bug the entire knowledge graph rather than one worktree. A
defensible alternative is **project-scoped** (one per repo, all worktrees sharing) — it removes the worktree
collapse problem (which is the actual `instance_id` bug) while keeping a hard boundary between projects.
**Recommendation: decide this before P-18 starts**, because CRS v2's RLS design differs between the two.

### 10.4 OPEN — redis-events scoping

No workspace scoping was found in event streams (EV §4). This design shares the process and declares events
non-authoritative until P-21. If any consumer *does* treat events as authoritative (dashboards are fine; a
consumer that writes state from an event is not), redis-events must become project-scoped instead. **UNKNOWN**:
the full consumer list.

### 10.5 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `migrate --volumes` picks the wrong winner and loses data | low | high | winner chosen by mtime **and** non-zero size; loser retained until an explicit second command (M8→M9 gap) |
| Degraded start (P-06) masks a genuine conflict | medium | medium | degraded mode never claims an unproven port — bind failure is the backstop; `--strict` for CI |
| Adoption (P-07) used to bless a genuinely foreign container | low | high | four independent proofs, mount check refuses cross-project mounts, operator confirmation recorded |
| Relabel (M14) requires stop+recreate, so it interrupts running work | high | low | run per-worktree, on demand; volumes preserved |
| `identity.py` consolidation changes a hash and orphans every existing lease/volume | medium | high | P-02 golden vectors are captured from **current** behaviour first; any intentional change to a hash formula requires a migration step, not a silent recompute |
| Shipping P-19 before P-17/P-18 are *verified* (not merged) | medium | high | P-19's acceptance criteria require the concurrency test from P-18 to pass on a real two-worktree run |
| Two agents implement P-22 and P-23 against different file lists | medium | low | the sweep that produces the file lists is a precondition; the packets' ACs are grep-guards, so they are verifiable independent of the list |

### 10.6 Deliberate non-goals

- No new daemon. Reaping rides existing hooks (§6.2).
- No change to the ChatGPT facade's opaque `target_id` contract (ADR-DCP-MCP-RO-0009) — worktree hashes and
  ports must never leak, and nothing in this design exposes them there (EV §5).
- No change to transports. conport SSE `GET /sse`; dope-memory/TO/pal/serena/dope-context Streamable HTTP
  `POST /mcp`; a 406 on `GET /mcp` is correct behaviour and is not to be "fixed" (AGENTS.md §12, EV §5).

---

## 11. Confidence & unresolved

| Claim | Confidence |
|---|---|
| Identity/naming/lease/discovery defects and their file:line locations | **high** (EV, spot-checked) |
| Sharing classes for stateless + genuinely multi-tenant servers (pal, dope-context, qdrant, litellm, exa, gptr, desktop-commander, bridges) | **high** |
| conport / dope-memory interim=worktree, end-state=host behind the two named gates | **high** on interim, **medium** on end-state (depends on §10.3) |
| redis-events sharing being acceptable | **low** — §10.4, marked OPEN |
| TO staying single-active-project | **high** as an ADR-compliance statement; the revert's *reason* is UNKNOWN |
| Migration step ordering | **medium** — M6/M13 depend on the operator confirming those worktrees are idle |
| Performance budgets (§6.3) | **low-medium** — the warm-switch decomposition is estimated, not measured. Measure during P-05. |
