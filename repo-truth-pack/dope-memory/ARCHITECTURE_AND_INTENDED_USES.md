# ARCHITECTURE AND INTENDED USES — dope-memory

## 1. Module Map

### Active Modules (imported by dope_memory_main.py)

```
services/working-memory-assistant/
├── dope_memory_main.py          # Canonical entrypoint: FastAPI app, inline DopeMemoryMCPServer (10 tools)
├── canonical_ledger.py          # Ledger path resolution per ADR-213
├── chronicle/
│   ├── store.py                 # ChronicleStore: SQLite CRUD, search, replay, correction, supersession
│   ├── schema.sql               # DDL for 5 data tables + migrations table
│   ├── sqlite_migrations.py     # Migration applicator: semver ordering, idempotent
│   ├── postgres_mirror.sql      # PostgreSQL mirror schema
│   └── migrations/              # 4 versioned SQL migrations (v1.1.0 → v1.2.1)
├── promotion/
│   ├── promotion.py             # PromotionEngine: allowlist, handler dispatch, provenance injection
│   └── redactor.py              # Redactor: regex secret scrubbing, denylist paths, size caps
├── reflection/
│   └── reflection.py            # ReflectionGenerator: deterministic reflection cards
├── trajectory/
│   └── manager.py               # TrajectoryManager: trajectory state, boost factor (0.0-0.5)
├── eventbus_consumer.py         # EventBusConsumer + SessionTracker: Redis stream ingestion
└── postgres_mirror_sync.py      # PostgresMirrorSync: SQLite → PostgreSQL one-way sync
```

### Shadowed Module (NOT imported by runtime entrypoint)

```
services/working-memory-assistant/
└── mcp/
    ├── __init__.py              # Exports DopeMemoryMCPServer
    └── server.py                # Alternate DopeMemoryMCPServer with 7 tools (SHADOWED)
```

### Legacy WMA Modules (NOT imported by dope-memory entrypoint)

```
services/working-memory-assistant/
├── main.py                      # Legacy WMA FastAPI app (port 8096)
├── wma_core.py                  # DevelopmentSnapshot, compression
├── bridge_adapter.py            # WorkingMemoryBridgeAdapter
├── cache_manager.py             # CacheManager (Redis-based)
├── trigger_manager.py           # TriggerManager
├── predictive_context_restoration.py  # PredictiveContextRestoration (TF-IDF, KNN)
├── conport_client.py            # ConPort integration
├── serena_client.py             # Serena integration
└── adhd_engine_client.py        # ADHD engine integration
```

### Thin Adapter (separate directory)

```
services/dope-memory/
└── mcp_stdio_adapter.py         # Stdio JSON-RPC proxy to port 8096 (targets WMA, NOT dope-memory)
```

### Core Library Client

```
src/dopemux/memory/
└── capture_client.py            # CLI/plugin capture client (writes to canonical ledger)
```

## 2. Responsibility Boundaries

| Module | Responsibility | Owns |
|--------|---------------|------|
| `dope_memory_main.py` | HTTP API, tool dispatch, lifespan management | FastAPI app, route definitions, Pydantic models |
| `DopeMemoryMCPServer` (inline) | Tool logic, pagination, cursor encoding | All 10 tool method implementations |
| `ChronicleStore` | All SQLite read/write operations | Schema init, migrations, CRUD, search, supersession |
| `PromotionEngine` | Event → work_log_entry conversion | Allowlist, handler dispatch, provenance injection |
| `Redactor` | Secret/PII removal | Regex patterns, denylist paths, sensitive keys, size caps |
| `ReflectionGenerator` | Reflection card generation | Top-3 decisions/blockers, progress summary, next steps |
| `TrajectoryManager` | Trajectory state management | Stream tracking, boost factor calculation |
| `EventBusConsumer` | Redis stream ingestion | Event parsing, promotion pipeline, session tracking |
| `SessionTracker` | Session idle/pulse detection | Per-session state, reflection trigger boundaries |
| `canonical_ledger.py` | Ledger path resolution | ADR-213 resolution chain, fail-closed semantics |
| `PostgresMirrorSync` | SQLite → Postgres sync | Bookmark tracking, schema management |

## 3. Dependency Direction

```
dope_memory_main.py
  ├── canonical_ledger.py
  ├── chronicle/store.py
  │     └── chronicle/sqlite_migrations.py
  ├── promotion/promotion.py
  │     └── promotion/redactor.py
  ├── reflection/reflection.py
  │     └── (uses ChronicleStore)
  ├── trajectory/manager.py
  │     └── (uses ChronicleStore)
  ├── eventbus_consumer.py (conditional, ENABLE_EVENTBUS)
  │     ├── canonical_ledger.py
  │     ├── chronicle/store.py
  │     ├── promotion/promotion.py
  │     ├── promotion/redactor.py
  │     ├── reflection/reflection.py
  │     └── trajectory/manager.py
  └── postgres_mirror_sync.py (conditional, ENABLE_MIRROR_SYNC)
```

No circular dependencies. All modules depend downward. `ChronicleStore` is the shared persistence layer used by all tool/consumer modules.

## 4. Entrypoints

| Entrypoint | File | Transport | Port | Wired In |
|-----------|------|-----------|------|----------|
| dope-memory HTTP server | `dope_memory_main.py` | HTTP (FastAPI/uvicorn) | 3020 | `compose.yml`, `docker-compose.smoke.yml`, `Dockerfile.dope-memory` |
| EventBus consumer | `eventbus_consumer.py` | Redis Streams (in-process) | N/A | Started in `dope_memory_main.py` lifespan if `ENABLE_EVENTBUS=true` |
| Postgres mirror sync | `postgres_mirror_sync.py` | PostgreSQL client (in-process) | N/A | Started in `dope_memory_main.py` lifespan if `ENABLE_MIRROR_SYNC=true` |
| Retention job | `run_retention_job()` | In-process async task | N/A | Started in lifespan if `ENABLE_RETENTION_JOB=true` |
| Legacy WMA server | `main.py` | HTTP (FastAPI/uvicorn) | 8096 | `Dockerfile` (not `Dockerfile.dope-memory`) |
| Stdio adapter | `services/dope-memory/mcp_stdio_adapter.py` | stdio JSON-RPC | N/A | `scripts/mcp_smoke.sh` |

## 5. Persistence Boundaries

| Store | Technology | Durability | Source of Truth | Scope |
|-------|-----------|------------|-----------------|-------|
| Canonical Ledger | SQLite (WAL) | Durable | **YES** — primary for all tool reads/writes | `{repo_root}/.dopemux/chronicle.sqlite` |
| PostgreSQL Mirror | PostgreSQL | Durable | No — one-way replica from SQLite | Opt-in via `ENABLE_MIRROR_SYNC` |
| Redis Streams | Redis | Ephemeral transport | No — event transport only | `activity.events.v1` (input), `memory.derived.v1` (output) |

## 6. External Integrations

| Integration | Protocol | Direction | Feature Flag | Evidence |
|------------|----------|-----------|--------------|----------|
| Redis (EventBus) | Redis Streams | Read (input) + Write (derived) | `ENABLE_EVENTBUS` | `eventbus_consumer.py` |
| PostgreSQL | psycopg2 / asyncpg | Write (mirror) | `ENABLE_MIRROR_SYNC` | `postgres_mirror_sync.py` |
| DopeContext | HTTP | Write (index) | `ENABLE_DOPECONTEXT_INDEX` | `eventbus_consumer.py` (aspirational) |
| MCP Clients | HTTP REST | Serve | Always on | `dope_memory_main.py` routes |

## 7. Intended Uses

### Implemented (code evidence)
- Temporal work log capture and retrieval with ADHD-optimized top-3 boundaries
- Manual memory storage via MCP tool (`memory_store`)
- Automated event promotion from Redis activity stream
- Session replay with chronological ordering and supersession awareness
- Issue tracking and issue-to-resolution linking
- Entry correction via immutable supersession chains
- Reflection card generation at session boundaries (deterministic, no LLM)
- Trajectory tracking with search relevance boosting
- Secret/PII redaction on all persisted data

### Documented but not implemented
- SSE transport at `/mcp` endpoint (configured in `.claude.json`, no code)
- Cross-indexing to DopeContext (flag exists, method stub only)
- Full MCP JSON-RPC protocol compliance (REST-only, no native MCP framing)

### Demo/Verification only (not production)
- `phase2_demo.py`, `verify_phase2.py`, `verify_refactoring.sh`
- `runtime_smoke.py`
