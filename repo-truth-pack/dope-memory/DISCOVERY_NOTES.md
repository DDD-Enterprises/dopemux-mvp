# DISCOVERY_NOTES — dope-memory Phase 1 Discovery

## 1. Repo Identity Snapshot

- **Repo URL:** <REPO_ROOT> (local)
- **Remote:** github.com (exact origin not inspected in this pass)
- **Repo name:** dopemux-mvp
- **Target service:** dope-memory
- **Analysis date:** 2026-07-16

## 2. Analyzed Ref

- **Commit:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
- **Timestamp:** 2026-03-06 12:22:43 -0800
- **Branch:** `codex/main-drain-20260306`

## 3. Default Branch

- **Current branch at HEAD:** `codex/main-drain-20260306`
- Note: This is the branch at HEAD; the canonical default branch name was not separately verified.

## 4. High-Confidence Active Module(s)

### 4.1 Dope-Memory MCP HTTP Server — `services/working-memory-assistant/dope_memory_main.py`
- **Status:** ACTIVE — canonical runtime entrypoint for the dope-memory service
- **Evidence:**
  - `Dockerfile.dope-memory` CMD is `python dope_memory_main.py` (line in Dockerfile)
  - `compose.yml` defines `dope-memory` service with `build.dockerfile: Dockerfile.dope-memory`
  - `docker-compose.smoke.yml` uses identical Dockerfile
  - `services/registry.yaml` registers port 3020, health `/health`, category `mcp`
  - Contains `DopeMemoryMCPServer` class (inline, lines 82–730)
  - Exposes 10 MCP tool methods and 10 corresponding HTTP POST routes under `/tools/`
  - FastAPI app on port 3020 via uvicorn

### 4.2 Dope-Memory MCP Library Module — `services/working-memory-assistant/mcp/server.py`
- **Status:** ACTIVE but SHADOWED — this is a separate module file containing `DopeMemoryMCPServer` with 7 tool methods
- **Evidence:**
  - `mcp/__init__.py` exports `DopeMemoryMCPServer` from this file
  - `dope_memory_main.py` does NOT import from `mcp/server.py`; it defines its own inline `DopeMemoryMCPServer` class
  - `mcp/server.py` has 7 methods (memory_search, memory_store, memory_recap, memory_mark_issue, memory_link_resolution, memory_replay_session, memory_correct)
  - `dope_memory_main.py` has 10 methods (adds memory_generate_reflection, memory_reflections, memory_trajectory)
  - **DISCREPANCY:** Two divergent `DopeMemoryMCPServer` classes exist. The `dope_memory_main.py` version is authoritative at runtime.

### 4.3 Chronicle Store — `services/working-memory-assistant/chronicle/store.py`
- **Status:** ACTIVE — canonical SQLite persistence layer
- **Evidence:** Used by both `DopeMemoryMCPServer` and `EventBusConsumer`
- **Schema:** `chronicle/schema.sql` defines 5 tables: `raw_activity_events`, `work_log_entries`, `issue_links`, `reflection_cards`, `trajectory_state`, `schema_migrations`
- **Migrations:** 4 versioned SQL migration files in `chronicle/migrations/`

### 4.4 Promotion Engine — `services/working-memory-assistant/promotion/`
- **Status:** ACTIVE — deterministic event promotion pipeline
- **Modules:** `promotion.py` (PromotionEngine, PromotedEntry, normalize_event_type), `redactor.py` (Redactor)
- **Evidence:** Imported and used in `dope_memory_main.py`, `mcp/server.py`, `eventbus_consumer.py`

### 4.5 EventBus Consumer — `services/working-memory-assistant/eventbus_consumer.py`
- **Status:** ACTIVE — real-time Redis stream ingestion
- **Evidence:** Enabled via `ENABLE_EVENTBUS=true` in compose files; started in `dope_memory_main.py` lifespan
- **Streams:** Input `activity.events.v1`, Output `memory.derived.v1`, Consumer group `dope-memory-ingestor`

### 4.6 Canonical Ledger Resolver — `services/working-memory-assistant/canonical_ledger.py`
- **Status:** ACTIVE — single-file resolution per ADR-213
- **Path:** `repo_root/.dopemux/chronicle.sqlite`
- **Override:** `DOPEMUX_CAPTURE_LEDGER_PATH` env var

### 4.7 Reflection Generator — `services/working-memory-assistant/reflection/reflection.py`
- **Status:** ACTIVE — Phase 2 deterministic reflection card generation
- **Evidence:** Class `ReflectionGenerator` used in `dope_memory_main.py` and `eventbus_consumer.py`

### 4.8 Trajectory Manager — `services/working-memory-assistant/trajectory/manager.py`
- **Status:** ACTIVE — Phase 2 trajectory state and boost factor
- **Evidence:** Class `TrajectoryManager` used in `eventbus_consumer.py`, tool exposed via `memory_trajectory` endpoint

### 4.9 Postgres Mirror Sync — `services/working-memory-assistant/postgres_mirror_sync.py`
- **Status:** ACTIVE (opt-in) — SQLite → PostgreSQL mirror
- **Evidence:** Gated by `ENABLE_MIRROR_SYNC` env var, started in lifespan if enabled

### 4.10 Capture Client — `src/dopemux/memory/capture_client.py`
- **Status:** ACTIVE — core library capture client used by CLI/plugins
- **Evidence:** Separate from service, provides `CaptureResult`, `resolve_repo_root_strict`, multiple capture modes

### 4.11 Stdio Adapter — `services/dope-memory/mcp_stdio_adapter.py`
- **Status:** ACTIVE (thin proxy) — converts MCP JSON-RPC over stdio to REST calls to port 8096
- **Evidence:** Referenced in `scripts/mcp_smoke.sh`; proxies to `http://localhost:8096/tools` (WMA port, NOT 3020)
- **DISCREPANCY:** Adapter targets port 8096 (WMA), but dope-memory HTTP server runs on 3020. This adapter talks to the legacy WMA service, not the dope_memory_main server.

## 5. Deprecated/Legacy Module(s)

### 5.1 WMA Service — `services/working-memory-assistant/main.py` + `wma_core.py`
- **Status:** LEGACY — original Working Memory Assistant HTTP service (port 8096)
- **Evidence:**
  - `Dockerfile` (not `Dockerfile.dope-memory`) uses `CMD ["python", "main.py"]` on port 8096
  - `README.md` describes WMA as a different service (snapshot/recover endpoints, PostgreSQL-based)
  - `main.py` has separate FastAPI app with snapshot/recover/preferences endpoints
  - `wma_core.py` contains `DevelopmentSnapshot` dataclass, compression, Redis+Postgres patterns
  - No compose service definition found pointing to this Dockerfile for the `dope-memory` service name
  - The `docs/api_contracts.md` documents WMA-specific classes (`DevelopmentSnapshot`, `SnapshotEngine`)
- **Relationship to dope-memory:** The WMA directory contains BOTH the legacy WMA service AND the dope-memory service. They share the same directory but have separate Dockerfiles and entrypoints.

### 5.2 Supporting Legacy Files
- `bridge_adapter.py` — `WorkingMemoryBridgeAdapter`, appears WMA-era, no imports from dope-memory entrypoint
- `cache_manager.py` — `CacheManager` (Redis-based), WMA-era, not imported by dope_memory_main.py
- `trigger_manager.py` — `TriggerManager`, WMA-era, not imported by dope_memory_main.py
- `predictive_context_restoration.py` — `PredictiveContextRestoration`, WMA-era, not imported by dope_memory_main.py
- `conport_client.py`, `conport_integration.py` — ConPort integration, not imported by dope_memory_main.py
- `serena_client.py`, `serena_integration.py` — Serena integration, not imported by dope_memory_main.py
- `adhd_engine_client.py`, `adhd_integration.py` — ADHD engine integration, imported by WMA `main.py` only

### 5.3 Verification/Demo Scripts
- `phase2_demo.py` — Minimal demo script (not production)
- `verify_phase2.py` — Verification script (not production)
- `verify_refactoring.sh` — Refactoring verification shell script (not production)
- `runtime_smoke.py` — Runtime smoke test (test utility)
- `test_wma_service.py`, `test_wma_performance.py` — WMA-specific tests

## 6. Runtime Entrypoints Discovered

| # | File | Entrypoint | Port | Transport | Wired In |
|---|------|-----------|------|-----------|----------|
| 1 | `services/working-memory-assistant/dope_memory_main.py` | `uvicorn dope_memory_main:app` | 3020 | HTTP (FastAPI) | `compose.yml`, `docker-compose.smoke.yml`, `Dockerfile.dope-memory` |
| 2 | `services/working-memory-assistant/main.py` | `uvicorn main:app` | 8096 | HTTP (FastAPI) | `Dockerfile` (legacy WMA) |
| 3 | `services/dope-memory/mcp_stdio_adapter.py` | `python mcp_stdio_adapter.py` | stdin/stdout | stdio JSON-RPC | `scripts/mcp_smoke.sh` |
| 4 | `services/working-memory-assistant/eventbus_consumer.py` | `run_consumer()` (async) | N/A (Redis consumer) | Redis Streams | Started in-process by dope_memory_main.py lifespan |
| 5 | `services/working-memory-assistant/postgres_mirror_sync.py` | `run_mirror_sync()` (async) | N/A | PostgreSQL client | Started in-process by dope_memory_main.py lifespan |

## 7. Callable/Tool/API Registration Locations Discovered

### HTTP Endpoints (dope_memory_main.py — AUTHORITATIVE)

| Route | Method | Pydantic Request Model | MCP Server Method |
|-------|--------|----------------------|-------------------|
| `GET /health` | `health_check` | — | — |
| `GET /` | `root` | — | — |
| `POST /tools/memory_search` | `memory_search` | `MemorySearchRequest` (line 740) | `mcp_server.memory_search()` |
| `POST /tools/memory_store` | `memory_store` | `MemoryStoreRequest` (line 757) | `mcp_server.memory_store()` |
| `POST /tools/memory_recap` | `memory_recap` | `MemoryRecapRequest` (line 774) | `mcp_server.memory_recap()` |
| `POST /tools/memory_mark_issue` | `memory_mark_issue` | `MemoryMarkIssueRequest` (line 784) | `mcp_server.memory_mark_issue()` |
| `POST /tools/memory_link_resolution` | `memory_link_resolution` | `MemoryLinkResolutionRequest` (line 796) | `mcp_server.memory_link_resolution()` |
| `POST /tools/memory_replay_session` | `memory_replay_session` | `MemoryReplaySessionRequest` (line 807) | `mcp_server.memory_replay_session()` |
| `POST /tools/memory_correct` | `memory_correct` | `MemoryCorrectRequest` (line 818) | `mcp_server.memory_correct()` |
| `POST /tools/memory_generate_reflection` | `memory_generate_reflection` | `MemoryGenerateReflectionRequest` (line 833) | `mcp_server.memory_generate_reflection()` |
| `POST /tools/memory_reflections` | `memory_reflections` | `MemoryReflectionsRequest` (line 842) | `mcp_server.memory_reflections()` |
| `POST /tools/memory_trajectory` | `memory_trajectory` | `MemoryTrajectoryRequest` (line 851) | `mcp_server.memory_trajectory()` |

### Root endpoint `GET /` tool listing (lines 1072–1087)
Lists only 7 tools: `memory_search`, `memory_store`, `memory_recap`, `memory_mark_issue`, `memory_link_resolution`, `memory_replay_session`, `memory_correct`.
**DISCREPANCY:** The root listing omits `memory_generate_reflection`, `memory_reflections`, `memory_trajectory` even though they have registered routes.

### Stdio Adapter tools (services/dope-memory/mcp_stdio_adapter.py)
Only 3 tools: `memory_recap`, `memory_search`, `memory_store`
Targets port 8096 (WMA), not 3020.

### MCP Client Configuration
- `.claude.json`: SSE transport at `http://localhost:3020/mcp`
  - **Note:** No `/mcp` SSE endpoint was found in `dope_memory_main.py`. The server only exposes REST `/tools/*` routes. The `.claude.json` SSE URL may be aspirational or require a proxy.
- `.dopemux/mcp.instances.toml`: HTTP transport at `http://127.0.0.1:3020`, required_tool_globs `["memory_*"]`

## 8. DTO/Parser/Validator Locations Discovered

### Pydantic Request Models (dope_memory_main.py)
| Model | Line | Key Fields |
|-------|------|------------|
| `MemorySearchRequest` | 740 | query, workspace_id, instance_id, session_id, filters, top_k, cursor |
| `MemoryStoreRequest` | 757 | workspace_id, instance_id, session_id, category, entry_type, workflow_phase, summary, details, reasoning, outcome, importance_score, tags, links |
| `MemoryRecapRequest` | 774 | workspace_id, instance_id, session_id, scope |
| `MemoryMarkIssueRequest` | 784 | workspace_id, instance_id, entry_id, severity, notes |
| `MemoryLinkResolutionRequest` | 796 | workspace_id, instance_id, issue_entry_id, resolution_entry_id, confidence |
| `MemoryReplaySessionRequest` | 807 | workspace_id, instance_id, session_id, mode, top_k, cursor |
| `MemoryCorrectRequest` | 818 | workspace_id, instance_id, entry_id, correction_type, new_summary, new_details, new_outcome, reason |
| `MemoryGenerateReflectionRequest` | 833 | workspace_id, instance_id, session_id, window_start, window_end |
| `MemoryReflectionsRequest` | 842 | workspace_id, instance_id, session_id, top_k |
| `MemoryTrajectoryRequest` | 851 | workspace_id, instance_id |

### Internal Dataclasses
| Class | File | Purpose |
|-------|------|---------|
| `ToolResponse` | dope_memory_main.py:74, mcp/server.py:44 | Standard tool response wrapper (success, data, error) |
| `SearchFilters` | mcp/server.py:33 | Search filter parameters |
| `PromotedEntry` | promotion/promotion.py:59 | Promoted work log entry ready for storage |

### Validators/Redactors
| Class | File | Purpose |
|-------|------|---------|
| `Redactor` | promotion/redactor.py:102 | Secret/PII scrubbing (regex patterns, denylist paths, sensitive keys, size caps) |

### Schema Enums (CHECK constraints in chronicle/schema.sql)
- `category`: `planning`, `implementation`, `review`, `debugging`, `research`, `deployment`, `architecture`, `documentation`
- `entry_type`: `decision`, `blocker`, `resolution`, `milestone`, `error`, `workflow_transition`, `manual_note`, `task_event`
- `workflow_phase`: `planning`, `implementation`, `review`, `audit`, `deployment`, `maintenance` (or NULL)
- `outcome`: `success`, `partial`, `blocked`, `abandoned`, `in_progress`, `failed`
- `importance_score`: INTEGER 1–10

## 9. Workflow/State/Gating Locations Discovered

### Promotion Gating
- **File:** `promotion/promotion.py`
- **Allowlist:** `PROMOTABLE_EVENT_TYPES` = frozenset of 7 event types: `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `workflow.phase_changed`, `manual.memory_store`
- **Method:** `PromotionEngine.is_promotable()` checks against allowlist
- **Flow:** Raw event → redaction → promotability check → promote → curated work_log_entry

### Event Normalization
- **File:** `promotion/promotion.py`, function `normalize_event_type()`
- **Handles:** underscore→dot conversion, whitespace trim, lowercase

### Supersession / Correction Gating
- **File:** `chronicle/store.py`
- **Chain depth limit:** `MAX_CHAIN_DEPTH = 10` (enforced at code level)
- **Fork prevention:** UNIQUE index on `supersedes_entry_id` scoped to `(workspace_id, instance_id)`
- **Methods:** `_get_chain_depth()`, `_resolve_chain_head()`, `_is_entry_superseded()`, `correct_entry()`, `retract_entry()`

### Session Tracking
- **File:** `eventbus_consumer.py`, class `SessionTracker`
- **Idle detection:** `DOPE_MEMORY_IDLE_MINUTES` (default 20)
- **Pulse emission:** `DOPE_MEMORY_PULSE_INTERVAL_SECONDS` (default 2700 = 45min)
- **Reflection triggers:** Session end, idle end, pulse boundaries
- **High-signal events:** `decision.logged`, `task.completed` (and more) reset idle timer

### Top-3 Boundary
- All search/recap tools default `top_k=3` per ADHD spec
- Cursor-based pagination for additional results

### Retention Job
- **File:** `dope_memory_main.py`, function `run_retention_job()`
- **Behavior:** Periodically calls `store.cleanup_expired_raw_events()` (7-day TTL on raw events)
- **Gated by:** `ENABLE_RETENTION_JOB` env var

## 10. Persistence/Storage Locations Discovered

### Primary: SQLite Canonical Ledger
- **Resolution:** `canonical_ledger.py` → `resolve_canonical_ledger()`
- **Default path:** `{repo_root}/.dopemux/chronicle.sqlite`
- **Override:** `DOPEMUX_CAPTURE_LEDGER_PATH` env var
- **Journal mode:** Configurable via `DOPEMUX_SQLITE_JOURNAL_MODE` (default `WAL`)
- **Schema:** `chronicle/schema.sql` — 5 data tables + migrations table

### Tables
1. `raw_activity_events` — short-lived (7-day TTL), indexed by workspace+ts
2. `work_log_entries` — durable curated entries with provenance fields, supersession support
3. `issue_links` — links between issue and resolution entries with confidence scores
4. `reflection_cards` — Phase 2, generated reflection summaries
5. `trajectory_state` — Phase 2, per-workspace+instance trajectory tracking
6. `schema_migrations` — version tracking

### Secondary: PostgreSQL Mirror (opt-in)
- **File:** `postgres_mirror_sync.py`
- **Schema:** `chronicle/postgres_mirror.sql`, `chronicle/postgres_mirror_reset.sql`
- **Gated by:** `ENABLE_MIRROR_SYNC=true`, `POSTGRES_URL` env var
- **Direction:** SQLite → PostgreSQL (one-way sync, SQLite is source of truth)
- **Bookmark tracking:** Sync positions persisted per workspace

### Tertiary: Redis (runtime state only)
- **Used by:** `EventBusConsumer` for stream consumption (`activity.events.v1`)
- **No durable memory storage in Redis** — Redis is transport, not persistence

## 11. Transport Locations Discovered

### HTTP (ACTIVE — primary)
- **File:** `dope_memory_main.py`
- **Framework:** FastAPI + uvicorn
- **Port:** 3020 (configured via `PORT` or `DOPE_MEMORY_PORT`)
- **Endpoints:** 10 tool routes under `/tools/` + health + root
- **CORS:** Configured via `ALLOWED_ORIGINS`

### Stdio JSON-RPC (ACTIVE — thin proxy)
- **File:** `services/dope-memory/mcp_stdio_adapter.py`
- **Protocol:** Line-delimited JSON-RPC over stdin/stdout
- **Tools:** 3 (memory_recap, memory_search, memory_store)
- **Backend:** Proxies to `http://localhost:8096/tools/` (WMA port, **NOT** dope-memory port 3020)
- **NOTE:** This adapter talks to the legacy WMA service endpoint, not the canonical dope-memory server

### SSE
- **Configuration:** `.claude.json` specifies SSE transport at `http://localhost:3020/mcp`
- **Code evidence:** No SSE/`/mcp` endpoint found in `dope_memory_main.py` source code
- **Status:** ASPIRATIONAL or requires external MCP proxy — not implemented in server code

### Redis Streams (internal transport — not externally callable)
- **File:** `eventbus_consumer.py`
- **Input:** `activity.events.v1` stream
- **Output:** `memory.derived.v1` stream
- **Consumer group:** `dope-memory-ingestor`

## 12. Export/Report Locations Discovered

### Reflection Cards
- Generated by `ReflectionGenerator` → stored in `reflection_cards` table
- Retrieved via `POST /tools/memory_reflections`
- Contains: trajectory, top_decisions, top_blockers, progress summary, suggested next steps

### Trajectory State
- Managed by `TrajectoryManager` → stored in `trajectory_state` table
- Retrieved via `POST /tools/memory_trajectory`

### UI Dashboard
- **File:** `services/working-memory-assistant/ui/index.html`
- Single-file HTML dashboard (22KB)
- No evidence of integration with dope-memory endpoints (appears WMA-era)

### No file-generation/export surfaces found beyond the API responses themselves.

## 13. Architecture/Module Boundary Notes

### Two Services, One Directory
The `services/working-memory-assistant/` directory contains TWO distinct services:
1. **dope-memory** (port 3020) — Temporal chronicle MCP server. Entrypoint: `dope_memory_main.py`, Dockerfile: `Dockerfile.dope-memory`
2. **WMA** (port 8096) — Legacy Working Memory Assistant. Entrypoint: `main.py`, Dockerfile: `Dockerfile`

These share the `chronicle/`, `promotion/`, `reflection/`, `trajectory/` modules but have entirely separate FastAPI apps, request models, and API surfaces.

### Two DopeMemoryMCPServer Classes
1. `dope_memory_main.py` (inline, 10 tools) — **AUTHORITATIVE at runtime**
2. `mcp/server.py` (module, 7 tools) — **SHADOWED, not imported by runtime entrypoint**

The `mcp/server.py` version lacks `memory_generate_reflection`, `memory_reflections`, `memory_trajectory` methods.

### Memory Trinity Boundaries
Per spec, dope-memory is one of three memory systems:
- **DopeContext** — Semantic archival (vector search in Qdrant)
- **DopeQuery** (ConPort) — Structured truth and decisions (PostgreSQL + AGE)
- **Dope-Memory** — Temporal chronicle and working-context (SQLite + Postgres mirror)

dope-memory WRITES to: SQLite canonical ledger, PostgreSQL mirror (opt-in), Redis derived events
dope-memory READS from: SQLite canonical ledger, Redis activity events stream

### Canonical Writer Logic
- `capture_client.py` (in `src/dopemux/memory/`) — CLI/plugin capture path
- `EventBusConsumer` — real-time stream capture path
- `DopeMemoryMCPServer.memory_store()` — manual MCP tool capture path
- All three resolve to the same canonical ledger via `resolve_canonical_ledger()`

### Provenance Chain
Every `work_log_entry` has mandatory provenance fields:
- `source_event_id`, `source_event_type`, `source_adapter`, `source_event_ts_utc`
- `promotion_rule`, `promotion_ts_utc`
- Pre-migration entries have sentinel values (`pre_migration`, `unknown`)

## 14. Intended-Use Notes

### Docs Say
- "Temporal chronicle and working-context manager" (spec, registry, compose)
- Part of "Memory Trinity" — handles "What am I doing right now?" temporal queries
- ADHD Top-3 boundary on all search responses
- Deterministic promotion (no LLM in Phase 1)
- Redaction-first: all events pass through `Redactor` before persistence
- Supersession chains for corrections (linear, max depth 10)
- Reflection cards generated at session boundaries
- Trajectory tracking for recency-boost in search ranking
- Per docs/spec/dope-memory/v1/07-mcp-contracts.md: 7 core tools defined

### Code Does
- Implements 10 HTTP tool endpoints (7 core + 3 Phase 2: reflection, reflections, trajectory)
- Inline `DopeMemoryMCPServer` class with full tool logic in `dope_memory_main.py`
- SQLite canonical ledger with WAL mode, automatic schema initialization and migrations
- EventBus consumer for real-time event ingestion from Redis streams
- Optional Postgres mirror sync
- Retention job for raw event cleanup (7-day TTL)
- Cursor-based pagination with scope-hash validation
- Entry ID generation using ULID (with fallback)
- Supersession chain tracking with depth limit and fork prevention via UNIQUE index
- Session tracking with idle detection, pulse emission, reflection triggers

### Tests Verify
- **Redactor:** AWS key, JWT, bearer token, private key, GitHub token, OpenAI key redaction; denylist path hashing; payload size cap; fail-closed behavior
- **PromotionEngine:** Decision logged promotes; task failed promotes; file modified NOT promoted; manual store promotes; tag extraction order; tag cap at 12
- **ChronicleStore:** Insert and search; deterministic ordering; cursor pagination no overlap; workspace isolation
- **Event type normalization:** dotted stays dotted; underscore converts; whitespace trim; case normalize; empty→unknown
- **EventBus consumer:** Init, custom streams, parse event, canonical ledger creation, store reuse; integration tests for promotion flow
- **Supersession:** Creates new entry; fork prevention; chain depth limit 10; cycle detection; search excludes superseded by default; search include superseded; replay current/full mode; count excludes superseded; correct entry summary; retraction; must target head; manual correction provenance; staleness detection; workspace scoping
- **Provenance:** Promotion extracts provenance; rejects missing provenance; rejects sentinels
- **Reflection:** No activity case; with decisions; with blockers; progress summary; next steps; persisted in DB
- **Trajectory:** Empty state; boost factor calculation; trajectory boost in ranking
- **Migrations:** SQLite migration application, table existence checks
- **Deterministic entry ID:** ID determinism; idempotent insertion
- **Retraction:** Tombstone creation
- **Canonical ledger convergence:** Integration test verifying legacy path failure

## 15. Missing Evidence

1. **SSE/MCP transport endpoint:** `.claude.json` configures SSE at `http://localhost:3020/mcp` but NO `/mcp` endpoint exists in `dope_memory_main.py`. Either an external MCP proxy is required or the configuration is aspirational. **STATUS: UNKNOWN how MCP SSE transport is actually served.**

2. **Stdio adapter targeting wrong port:** `mcp_stdio_adapter.py` targets port 8096 (WMA), not 3020 (dope-memory). May be intentionally talking to WMA or may be outdated.

3. **mcp/server.py vs dope_memory_main.py divergence:** Two `DopeMemoryMCPServer` classes with different tool sets. No mechanism observed to reconcile them. It is unknown whether `mcp/server.py` is actively maintained or legacy.

4. **Root endpoint tool listing incomplete:** `GET /` lists 7 tools but 10 are registered as routes.

5. **No formal MCP protocol implementation:** The server exposes REST HTTP endpoints, not MCP JSON-RPC protocol. MCP compliance is achieved either through external proxying or the thin stdio adapter.

6. **DopeContext index integration:** `ENABLE_DOPECONTEXT_INDEX` flag exists in `eventbus_consumer.py` for cross-indexing to DopeContext, but method `_index_in_dopecontext` behavior not fully inspected.

7. **`wma_migration.sql` and `wma_migration_standalone.sql`:** Present in root of working-memory-assistant dir. Not inspected — appear to be WMA-era PostgreSQL migrations, not dope-memory chronicle migrations.

## 16. Explicit Readiness Judgment

### **READY_FOR_PHASE_2**

**Justification:**
- All runtime entrypoints identified and verified against Docker/compose wiring
- All 10 tool endpoints located with request models, handler methods, and response builders
- Persistence layer (SQLite canonical ledger) fully mapped: schema, migrations, store methods
- Promotion engine, redactor, and event normalization located and understood
- EventBus consumer, session tracking, reflection, trajectory all located
- Transport layers documented (HTTP primary, stdio proxy, SSE aspirational)
- Active vs deprecated/legacy modules clearly separated with evidence
- Test coverage extensively mapped (25+ test files, 60+ test functions)
- Two `DopeMemoryMCPServer` divergence documented as known discrepancy
- Spec documents located and cross-referenced

**Known risks for Phase 2:**
- The mcp/server.py shadowed class needs explicit resolution
- SSE transport gap needs determination (proxy vs unimplemented)
- Stdio adapter port mismatch needs determination
