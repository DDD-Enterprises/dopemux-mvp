# APPENDIX A — Source Index

Grouped listing of every file inspected during Phase 1 discovery for dope-memory.

## Root Docs

| File | Purpose |
|------|---------|
| `DOPE_MEMORY_INTEGRATION.md` | Root-level integration doc (not inspected deeply; duplicate exists in `docs/`) |

## docs/

| File | Purpose |
|------|---------|
| `docs/spec/dope-memory/v1/readme-2.md` | Spec index: 11-document specification suite |
| `docs/spec/dope-memory/v1/00-overview.md` | Purpose, principles, cognitive tiers |
| `docs/spec/dope-memory/v1/01-architecture.md` | Service responsibilities and component diagram |
| `docs/spec/dope-memory/v1/02-data-model-sqlite.md` | SQLite canonical schema |
| `docs/spec/dope-memory/v1/02-derived-memory-pipeline.md` | Derived memory pipeline spec |
| `docs/spec/dope-memory/v1/03-data-model-postgres.md` | Postgres mirror schema |
| `docs/spec/dope-memory/v1/04-event-taxonomy.md` | Event types and envelope format |
| `docs/spec/dope-memory/v1/05-promotion-redaction.md` | Redaction rules and promotion logic |
| `docs/spec/dope-memory/v1/06-retrieval-ranking.md` | Search and deterministic ranking |
| `docs/spec/dope-memory/v1/07-mcp-contracts.md` | MCP tool request/response schemas (inspected: first 100 lines) |
| `docs/spec/dope-memory/v1/08-phased-roadmap.md` | Phase 0-4 delivery plan |
| `docs/spec/dope-memory/v1/09-test-plan.md` | Test plan |
| `docs/spec/dope-memory/v1/10-risk-register.md` | Risk register |
| `docs/DOPE_MEMORY_INTEGRATION.md` | Integration guide |
| `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-3.md` | Deep dive doc (listed, not inspected) |
| `docs/90-adr/adr-213-dual-capture-canonical-ledger-3.md` | ADR for canonical ledger (referenced, not inspected) |
| `docs/03-reference/memory-capture-cli.md` | CLI capture reference (listed, not inspected) |
| `docs/docs_index.yaml` | Machine-readable doc index (listed, references dope-memory) |

## source/ (services/working-memory-assistant/)

### Core Entrypoints
| File | Lines | Purpose |
|------|-------|---------|
| `dope_memory_main.py` | 1312 | **Canonical entrypoint**: FastAPI HTTP server, inline DopeMemoryMCPServer, 10 tool endpoints, Pydantic models, lifespan, retention job |
| `main.py` | ~800+ | **Legacy WMA entrypoint**: FastAPI HTTP server on port 8096, snapshot/recover/preferences API |

### MCP Module
| File | Lines | Purpose |
|------|-------|---------|
| `mcp/__init__.py` | 11 | Package init, exports DopeMemoryMCPServer |
| `mcp/server.py` | 650 | Shadowed DopeMemoryMCPServer with 7 tools (subset of dope_memory_main.py's 10) |

### Chronicle (Persistence)
| File | Lines | Purpose |
|------|-------|---------|
| `canonical_ledger.py` | ~95 | Canonical ledger path resolution per ADR-213 |
| `chronicle/__init__.py` | — | Package init |
| `chronicle/store.py` | ~1256+ | ChronicleStore: SQLite CRUD, search, replay, correction, supersession, reflection, trajectory |
| `chronicle/schema.sql` | ~170 | DDL for 5 data tables + migrations table |
| `chronicle/sqlite_migrations.py` | ~60+ | Migration applicator: semantic version ordering, idempotent apply |
| `chronicle/migrations/v1_1_0_add_provenance_fields.sql` | — | Add provenance columns to work_log_entries |
| `chronicle/migrations/v1_1_1_add_supersession_unique_index.sql` | — | Global supersession unique index |
| `chronicle/migrations/v1_2_0_enforce_linear_supersession.sql` | — | Duplicate of v1.1.1 (versioned separately) |
| `chronicle/migrations/v1_2_1_scope_supersession_unique_index.sql` | — | Scope supersession uniqueness to workspace+instance |
| `chronicle/postgres_mirror.sql` | — | PostgreSQL mirror schema DDL |
| `chronicle/postgres_mirror_reset.sql` | — | PostgreSQL mirror reset script |

### Promotion
| File | Lines | Purpose |
|------|-------|---------|
| `promotion/__init__.py` | 15 | Exports Redactor, PromotionEngine |
| `promotion/promotion.py` | ~400 | PromotionEngine: allowlist, importance scores, event→entry promotion, tag extraction |
| `promotion/redactor.py` | ~210 | Redactor: regex secret scrubbing, denylist paths, sensitive keys, size caps |

### Reflection & Trajectory (Phase 2)
| File | Lines | Purpose |
|------|-------|---------|
| `reflection/__init__.py` | — | Package init |
| `reflection/reflection.py` | ~340 | ReflectionGenerator: deterministic reflection cards from work log entries |
| `trajectory/manager.py` | ~190 | TrajectoryManager: trajectory state, boost factor (0.0-0.5) |

### EventBus & Sync
| File | Lines | Purpose |
|------|-------|---------|
| `eventbus_consumer.py` | ~770 | EventBusConsumer + SessionTracker: Redis stream ingestion, promotion, session tracking, reflection triggers |
| `postgres_mirror_sync.py` | ~800 | PostgresMirrorSync: SQLite→PostgreSQL one-way sync with bookmarks |

### Legacy/WMA-Era Modules (not imported by dope-memory entrypoint)
| File | Lines | Purpose |
|------|-------|---------|
| `wma_core.py` | ~100+ | WMA core: DevelopmentSnapshot, compression, Redis+Postgres patterns |
| `bridge_adapter.py` | ~240 | WorkingMemoryBridgeAdapter: bridge communication |
| `cache_manager.py` | ~240 | CacheManager: Redis context caching (WMA-era) |
| `trigger_manager.py` | ~140 | TriggerManager: monitoring loop for WMA triggers |
| `predictive_context_restoration.py` | ~410 | PredictiveContextRestoration: TF-IDF, KNN pattern matching, ADHD optimization |
| `conport_client.py` | — | ConPort integration client |
| `conport_integration.py` | — | ConPort integration logic |
| `serena_client.py` | — | Serena integration client |
| `serena_integration.py` | — | Serena integration logic |
| `adhd_engine_client.py` | — | ADHD engine client |
| `adhd_integration.py` | — | ADHD integration logic |
| `migration_runner.py` | — | WMA PostgreSQL migration runner |
| `utils.py` | — | Utilities |

### Verification/Demo (not production)
| File | Purpose |
|------|---------|
| `phase2_demo.py` | Minimal Phase 2 demo script |
| `verify_phase2.py` | Phase 2 verification script |
| `verify_refactoring.sh` | Refactoring verification |
| `runtime_smoke.py` | Runtime smoke test |
| `test_wma_service.py` | WMA service test |
| `test_wma_performance.py` | WMA performance test |

### Thin Adapter (services/dope-memory/)
| File | Lines | Purpose |
|------|-------|---------|
| `services/dope-memory/mcp_stdio_adapter.py` | 242 | Stdio JSON-RPC adapter proxying 3 tools to port 8096 |

### Core Library (src/)
| File | Purpose |
|------|---------|
| `src/dopemux/memory/capture_client.py` | Deterministic capture client for CLI/plugin mode |

## tests/

### Service-Level Tests (services/working-memory-assistant/tests/)
| File | Purpose |
|------|---------|
| `conftest.py` | Shared fixtures |
| `test_dope_memory.py` | Core tests: Redactor, PromotionEngine, ChronicleStore |
| `test_event_type_normalization.py` | Event type normalization + promotable types |
| `test_eventbus_consumer.py` | EventBus consumer init, parsing, integration |
| `test_migration_runner_optimized.py` | WMA migration runner tests |
| `test_phase2_reflection_trajectory.py` | ReflectionGenerator + TrajectoryManager |
| `test_promotion_allowlist.py` | Promotion allowlist verification |
| `test_reflection.py` | Reflection tests |
| `test_session_tracker.py` | Session tracker tests |
| `test_trajectory.py` | Trajectory tests |
| `test_trajectory_boost_in_ranking.py` | Trajectory boost in ranking |
| `test_predictive_restoration.py` | Predictive context restoration (WMA-era) |
| `test_wma_core.py` | WMA core tests (WMA-era) |

### Unit Tests (services/working-memory-assistant/tests/unit/)
| File | Purpose |
|------|---------|
| `test_chronicle_sqlite_migrations.py` | SQLite migration application |
| `test_copilot_adapter_hardening.py` | Copilot adapter hardening |
| `test_deterministic_entry_id.py` | Entry ID determinism + idempotent insertion |
| `test_event_id_convergence.py` | Event ID convergence |
| `test_packet_h_supersession_hardening.py` | Packet H supersession hardening |
| `test_promotion_provenance.py` | Promotion provenance extraction, rejection |
| `test_reflection_provenance.py` | Reflection provenance |
| `test_replay_ordering.py` | Replay ordering |
| `test_retraction_tombstone.py` | Retraction tombstone |
| `test_search_excludes_superseded_by_default.py` | Search excludes superseded |
| `test_supersession_depth_limit.py` | Supersession depth limit |
| `test_supersession_linearity.py` | Supersession linearity |
| `test_supersession_semantics.py` | Full supersession semantics (17 tests) |
| `test_time_semantics.py` | Time semantics |

### Repo-Level Tests
| File | Purpose |
|------|---------|
| `tests/integration/test_canonical_ledger_convergence.py` | Canonical ledger convergence, legacy path rejection |
| `tests/arch/test_service_env_contract.py` | Service environment contract verification |
| `tests/test_instance_manager_ports.py` | Instance manager port mapping |

## build/runtime

| File | Purpose |
|------|---------|
| `services/working-memory-assistant/Dockerfile.dope-memory` | Docker build for dope-memory service (port 3020, CMD python dope_memory_main.py) |
| `services/working-memory-assistant/Dockerfile` | Docker build for legacy WMA service (port 8096, CMD python main.py) |
| `services/working-memory-assistant/requirements.txt` | Python dependencies |
| `services/working-memory-assistant/pytest.ini` | pytest configuration |
| `compose.yml` | Docker Compose: dope-memory service definition |
| `docker-compose.smoke.yml` | Smoke test compose: dope-memory service definition |
| `services/registry.yaml` | Service registry: port 3020, health /health, category mcp |
| `.claude.json` | MCP client config: SSE at localhost:3020/mcp |
| `.dopemux/mcp.instances.toml` | MCP instance config: HTTP at localhost:3020 |
| `.dopemux/instances/A/mcp.compose.override.yml` | Instance A compose override |
| `scripts/mcp_smoke.sh` | MCP smoke test script |

## release/tag sources
- No release tags inspected. Analysis performed on branch commit `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`.
