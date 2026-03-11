# DISCOVERY_NOTES.md — dope-context Phase 1 Discovery

## 1. Repo Identity Snapshot

| Field | Value |
|-------|-------|
| Repo path | `<REPO_ROOT>` |
| Service path | `services/dope-context/` |
| Package name (setup.py) | `dope-context-mcp` |
| FastMCP server name | `"dope-context"` (server.py:90) |
| Python requirement | `>=3.11` (setup.py:9) |
| Service port | `3010` (Dockerfile:30, compose.yml:337, server.py:119) |

## 2. Analyzed Ref

```
Commit: fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2
Date:   2026-03-06 12:22:43 -0800
Branch: codex/main-drain-20260306
```

## 3. Default Branch

The analyzed ref is on `codex/main-drain-20260306`. The repository default branch was not separately queried; this analysis uses the checked-out HEAD which matches the analyzed ref exactly.

## 4. High-Confidence Active Module(s)

All evidence converges on **`src/mcp/server.py`** (3043 lines) as the single authoritative MCP surface. The following modules are actively imported and wired into `server.py`:

| Module | Path | Evidence |
|--------|------|----------|
| **MCP server** | `src/mcp/server.py` | FastMCP instance, 18 `@mcp.tool()` decorators, 4 `@mcp.custom_route` decorators, `__main__` block |
| **Dense search** | `src/search/dense_search.py` | Imported as `MultiVectorSearch`, `SearchProfile`, `SearchResult` by server.py:52 |
| **Hybrid search** | `src/search/hybrid_search.py` | Imported as `HybridSearch`, `BM25Index` by server.py:53 |
| **Docs search** | `src/search/docs_search.py` | Imported as `DocumentSearch` by server.py:61 |
| **Voyage embedder** | `src/embeddings/voyage_embedder.py` | Imported as `VoyageEmbedder` by server.py:51 |
| **Contextualized embedder** | `src/embeddings/contextualized_embedder.py` | Imported as `ContextualizedEmbedder` by server.py:52 |
| **Voyage reranker** | `src/rerank/voyage_reranker.py` | Imported as `VoyageReranker` by server.py:54 |
| **Code chunker** | `src/preprocessing/code_chunker.py` | Imported as `CodeChunker`, `ChunkingConfig` by server.py:48 |
| **Document processor** | `src/preprocessing/document_processor.py` | Imported via `DocIndexingPipeline` |
| **Data models** | `src/preprocessing/models.py` | `DocumentType`, `ChunkMetadata`, `DocumentChunk` |
| **Indexing pipeline** | `src/pipeline/indexing_pipeline.py` | Imported as `IndexingPipeline`, `IndexingConfig`, `IndexingProgress` by server.py:55-59 |
| **Docs pipeline** | `src/pipeline/docs_pipeline.py` | Imported as `DocIndexingPipeline` by server.py:60 |
| **OpenAI generator** | `src/context/openai_generator.py` | Imported as `OpenAIContextGenerator` by server.py:49 |
| **Workspace utils** | `src/utils/workspace.py` | Imported as `get_workspace_root`, `get_collection_names`, `get_snapshot_dir`, `workspace_to_hash` by server.py:62 |
| **Token budget** | `src/utils/token_budget.py` | Imported as `truncate_code_results`, `truncate_docs_results` by server.py:65 |
| **Metrics tracker** | `src/utils/metrics_tracker.py` | Imported as `get_tracker` by server.py:64 |
| **File synchronizer** | `src/sync/file_synchronizer.py` | Imported as `FileSynchronizer`, `ChangeSet` by server.py:63 |
| **Incremental indexer** | `src/sync/incremental_indexer.py` | Imported by indexing_pipeline.py:26 |
| **Autonomous controller** | `src/autonomous/autonomous_controller.py` | Imported as `AutonomousController`, `AutonomousConfig` by server.py:66 |
| **Watchdog monitor** | `src/autonomous/watchdog_monitor.py` | Imported by autonomous_controller.py:14 |
| **Indexing worker** | `src/autonomous/indexing_worker.py` | Imported by autonomous_controller.py:15 |
| **Periodic sync** | `src/autonomous/periodic_sync.py` | Imported by autonomous_controller.py:16 |

## 5. Deprecated / Legacy Module(s)

| Module | Path | Evidence |
|--------|------|----------|
| **simple_server.py** | `src/mcp/simple_server.py` | Contains only 3 mock tools (`search_code`, `docs_search`, `get_index_status`) returning hardcoded data. Not imported by anything. Not referenced by Dockerfile CMD. MOCK SURFACE ONLY. |
| **fastmcp_stub.py** | `src/mcp/fastmcp_stub.py` | Fallback-only stub for test environments. `server.py:28-31` imports it only when `fastmcp` package is missing. Not a tool surface. |
| **claude_generator.py** | `src/context/claude_generator.py` | Not imported by `server.py`. Server uses `openai_generator.py` instead. |
| **grok_generator.py** | `src/context/grok_generator.py` | Not imported by `server.py`. Experimental free context generation via OpenRouter. |
| **attention_aware_search.py** | `src/attention_aware_search.py` | Not imported by `server.py`. ADHD integration is done inline via `get_dynamic_top_k()` in server.py:313-339. |
| **integration_bridge_connector.py** | `src/integration_bridge_connector.py` | Imported conditionally (server.py:69-73) as `emit_search_completed` but behind `CONPORT_INTEGRATION_AVAILABLE` flag. |
| **bridge_adapter.py** | `bridge_adapter.py` (service root) | DopeconBridge adapter. Not imported by `server.py`. Imports `shared/dopecon_bridge_client`. |
| **claude_code_enricher.py** | `src/enrichment/claude_code_enricher.py` | Designed for external orchestration-level use (Claude Code), not imported by server.py. |
| **code_graph_enricher.py** | `src/enrichment/code_graph_enricher.py` | Imported lazily inside `_search_code_impl()` (server.py:1290) only when `enrich_with_graph=True`. Active but conditional. |
| **test_mcp_server.py.bak** | `tests/test_mcp_server.py.bak` | Backup file. Not active. |

### Nested duplicate
`services/dope-context/services/dope-context/Dockerfile` and `.dockerignore` exist as accidental nested duplicates. Not referenced by any build target.

## 6. Runtime Entrypoints Discovered

### Primary entrypoint (code + Docker)
- **File:** `src/mcp/server.py:3029-3043`
- **Invocation:** `python -m src.mcp.server`
- **Docker CMD:** `CMD ["python", "-m", "src.mcp.server"]` (Dockerfile:47, Dockerfile.fixed:56)
- **PYTHONPATH:** `/app/src` (Dockerfile:33, Dockerfile.fixed:34)
- **Transport:** Resolved by `_resolve_transport_runtime()` (server.py:93-126)

### Wrapper entrypoint
- **File:** `scripts/mcp-wrappers/dope-context-wrapper.sh`
- **Invocation:** `exec docker exec -i ... python /app/server.py "$@"`
- **Note:** This wrapper targets `/app/server.py` but Docker CMD targets `python -m src.mcp.server`. Potential discrepancy — the wrapper path `/app/server.py` does not match any file in the Docker image. The correct module path would be `python -m src.mcp.server`.

### Compose entrypoint
- **File:** `compose.yml:316-349`
- **Container:** `mcp-dope-context`
- **Port mapping:** `3010:3010`
- **Depends on:** `mcp-qdrant`

## 7. Callable / Tool / API Registration Locations Discovered

### MCP Tools (18 tools via `@mcp.tool()` in server.py)

| # | Tool Name | Line | Parameters |
|---|-----------|------|------------|
| 1 | `index_workspace` | 971-1023 | `workspace_path`, `workspace_paths`, `include_patterns`, `exclude_patterns`, `max_files` |
| 2 | `search_code` | 1313-1400 | `query`, `top_k=10`, `profile="implementation"`, `use_reranking=True`, `filter_language`, `workspace_path`, `workspace_paths`, `enrich_with_graph=False` |
| 3 | `get_index_status` | 1453-1468 | `workspace_path`, `workspace_paths` |
| 4 | `clear_index` | 1531-1546 | `workspace_path`, `target="code"` |
| 5 | `index_docs` | 1588-1621 | `workspace_path`, `workspace_paths`, `include_patterns` |
| 6 | `docs_search` | 1776-1848 | `query`, `top_k=10`, `filter_doc_type`, `workspace_path`, `max_content_length=2000`, `workspace_paths` |
| 7 | `configure_decision_auto_indexing` | 1962-2005 | `workspace_path`, `enabled=True`, `bridge_url`, `decision_limit=3`, `auto_include_in_search_all=True` |
| 8 | `search_all` | 2121-2178 | `query`, `top_k=10`, `workspace_path`, `workspace_paths`, `include_decisions=True` |
| 9 | `sync_workspace` | 2350-2389 | `workspace_path`, `workspace_paths`, `include_patterns`, `auto_reindex=False` |
| 10 | `sync_docs` | 2426-2462 | `workspace_path`, `workspace_paths`, `include_patterns` |
| 11 | `get_search_metrics` | 2465-2488 | `since_timestamp` |
| 12 | `clear_search_metrics` | 2491-2502 | (none) |
| 13 | `start_autonomous_indexing` | 2566-2615 | `workspace_path`, `workspace_paths`, `debounce_seconds=5.0`, `periodic_interval=600` |
| 14 | `stop_autonomous_indexing` | 2618-2675 | `workspace_path`, `workspace_paths` |
| 15 | `get_autonomous_status` | 2678-2728 | (none) |
| 16 | `start_autonomous_docs_indexing` | 2808-2857 | `workspace_path`, `workspace_paths`, `debounce_seconds=5.0`, `periodic_interval=600` |
| 17 | `stop_autonomous_docs_indexing` | 2860-2920 | `workspace_path`, `workspace_paths` |
| 18 | `get_chunk_complexity` | 2923-3026 | `file_path`, `symbol` |

### Custom HTTP Routes (4 routes via `@mcp.custom_route`)

| Route | Method | Line | Purpose |
|-------|--------|------|---------|
| `/health` | GET | 145-148 | Container health probe |
| `/info` | GET | 151-195 | Service discovery (ADR-208) |
| `/autoindex/bootstrap` | POST | 198-250 | Startup bootstrap indexing |
| `/autoindex/status` | GET | 253-279 | Autoindex progress query |

### simple_server.py Tools (MOCK — NOT AUTHORITATIVE)

| Tool Name | Line | Notes |
|-----------|------|-------|
| `search_code` | 24-51 | Returns hardcoded mock data |
| `docs_search` | 53-78 | Returns hardcoded mock data |
| `get_index_status` | 80-89 | Returns hardcoded mock data |

## 8. DTO / Parser / Validator Locations Discovered

| Type | Location | Symbol(s) |
|------|----------|-----------|
| **Search result DTO** | `src/search/dense_search.py:76` | `SearchResult` dataclass |
| **Search profile DTO** | `src/search/dense_search.py:28` | `SearchProfile` dataclass |
| **Code chunk DTO** | `src/preprocessing/code_chunker.py:27` | `CodeChunk` dataclass |
| **Chunking config** | `src/preprocessing/code_chunker.py:49` | `ChunkingConfig` dataclass |
| **Document chunk DTO** | `src/preprocessing/models.py:42` | `DocumentChunk` dataclass |
| **Document type enum** | `src/preprocessing/models.py:8` | `DocumentType(str, Enum)` |
| **Chunk metadata** | `src/preprocessing/models.py:19` | `ChunkMetadata` dataclass |
| **Indexing config** | `src/pipeline/indexing_pipeline.py:32` | `IndexingConfig` dataclass |
| **Indexing progress** | `src/pipeline/indexing_pipeline.py:61` | `IndexingProgress` dataclass |
| **Docs indexing progress** | `src/pipeline/docs_pipeline.py:20` | `DocsIndexingProgress` dataclass |
| **Embedding request** | `src/embeddings/voyage_embedder.py:22` | `EmbeddingRequest` dataclass |
| **Embedding response** | `src/embeddings/voyage_embedder.py:37` | `EmbeddingResponse` dataclass |
| **Contextualized embed response** | `src/embeddings/contextualized_embedder.py:21` | `ContextualizedEmbeddingResponse` dataclass |
| **Rerank result** | `src/rerank/voyage_reranker.py:20` | `RerankResult` dataclass |
| **Rerank response** | `src/rerank/voyage_reranker.py:29` | `RerankResponse` dataclass |
| **Truncation result** | `src/utils/token_budget.py:29` | `TruncationResult` dataclass |
| **Search metric** | `src/utils/metrics_tracker.py:19` | `SearchMetric` dataclass |
| **File snapshot** | `src/sync/file_synchronizer.py:22` | `FileSnapshot` dataclass |
| **Workspace snapshot** | `src/sync/file_synchronizer.py:33` | `WorkspaceSnapshot` dataclass |
| **Chunk metadata (indexer)** | `src/sync/incremental_indexer.py:20` | `ChunkMetadata` dataclass |
| **File chunk map** | `src/sync/incremental_indexer.py:33` | `FileChunkMap` dataclass |
| **Chunk snapshot** | `src/sync/incremental_indexer.py:42` | `ChunkSnapshot` dataclass |
| **Autonomous config** | `src/autonomous/autonomous_controller.py:23` | `AutonomousConfig` dataclass |
| **Contract schemas** | `contracts/dope-context/*.json` | JSON Schema (docs_grouped_embed.request, search.response) |
| **Decision limit normalizer** | `src/mcp/server.py:136` | `_normalize_decision_limit()` — clamp 1..10 |

## 9. Workflow / State / Gating Locations Discovered

| Workflow | Location | Description |
|----------|----------|-------------|
| **Indexing pipeline** | `src/pipeline/indexing_pipeline.py` | File Discovery → Code Chunking → Context Generation → Multi-Vector Embedding → Qdrant Storage |
| **Docs pipeline** | `src/pipeline/docs_pipeline.py` | Document discovery → chunk → embed (voyage-context-3) → upsert to Qdrant |
| **Search pipeline** | `server.py:_search_code_impl()` (1026-1310) | Embed query → Hybrid search (dense+BM25) → Rerank → Token budget truncation → Optional graph enrichment |
| **Docs search pipeline** | `server.py:_docs_search_impl()` (1624-1773) | Embed query → Dense search → Token budget truncation → Enrich with provenance metadata |
| **Unified search** | `server.py:_search_all_impl()` (2008-2118) | Parallel code+docs+decisions → Budget-split top_k → Trinity boundary metadata |
| **Autoindex bootstrap** | `server.py:_run_workspace_autoindex_bootstrap()` (667-746) | Marker-based idempotence → index_workspace + index_docs → start autonomous watchers |
| **Autonomous indexing** | `src/autonomous/autonomous_controller.py` | Watchdog (file events) → Debounce → IndexingWorker (async queue) → PeriodicSync (10min fallback) |
| **Sync / incremental** | `src/sync/file_synchronizer.py` | SHA256 snapshot comparison → ChangeSet (added/modified/removed) |
| **Trinity boundary gating** | `server.py:2019-2026` | `decision_enabled` requires: `include_decisions=True AND config.enabled AND auto_include_in_search_all AND top_k >= 3` |
| **ADHD dynamic top_k** | `server.py:313-339` | `get_dynamic_top_k()` — feature-flagged via `FEATURE_ADHD_ENGINE_DOPE_CONTEXT` |
| **Token budget gating** | `src/utils/token_budget.py` | 9000 token safe budget (10K MCP limit with 10% headroom) |

## 10. Persistence / Storage Locations Discovered

### Qdrant (vector store — primary)
- **Code collections:** `code_{workspace_hash}` (workspace.py:176)
- **Docs collections:** `docs_{workspace_hash}` (workspace.py:177)
- **Connection:** `QDRANT_URL` (default `localhost`), `QDRANT_PORT` (default `6333`)
- **Vector config:** 3 named vectors per collection: `content_vec`, `title_vec`, `breadcrumb_vec` (multi_index_config.yaml:11-17, dense_search.py)
- **Embedding dimensions:** 1024 (multi_index_config.yaml:9)
- **Distance metric:** DOT (dense_search.py imports `Distance`)

### File-based persistence
| Artifact | Path | Format | Durability |
|----------|------|--------|------------|
| BM25 index cache | `~/.dope-context/snapshots/{hash}/bm25_index.pkl` | pickle | Durable (rebuilt on index) |
| File snapshot | `~/.dope-context/snapshots/{hash}/snapshot.json` | JSON | Durable |
| Chunk snapshot | `~/.dope-context/snapshots/{hash}/chunk_snapshot.json` | JSON | Durable |
| Autoindex marker | `~/.dope-context/snapshots/{hash}/autoindex_bootstrap.json` | JSON | Durable (idempotence) |
| Decision sync config | `~/.dope-context/snapshots/{hash}/decision_sync_config.json` | JSON | Durable (per-workspace) |
| Search metrics | `~/.dope-context/search_metrics.json` | JSON | Durable |

### Docker volumes
- `./services/dope-context/data:/app/data` (compose.yml:339)
- `./services/dope-context/logs:/app/logs` (compose.yml:340)
- `${HOST_CODE_PARENT_DIR:-/tmp}:/workspaces` (compose.yml:341) — host code mount

### Observations
- **No SQLite.** All local persistence is JSON files or pickle.
- **No Redis for persistence.** Redis is listed in requirements.txt but not used by server.py for caching (code comments reference "Phase 3" caching). The ADHD engine integration uses Redis if available.
- **Qdrant is the sole vector store and source of truth for indexed content.**

## 11. Transport Locations Discovered

### Transport resolution (server.py:93-126)
`_resolve_transport_runtime()` resolves transport from environment variables:

| Priority | Env Var | Effect |
|----------|---------|--------|
| 1 | `MCP_TRANSPORT` or `FASTMCP_TRANSPORT` | Explicit transport selection |
| 2 | `MCP_SERVER_PORT` set (no transport env) | Defaults to `"http"` |
| 3 | Neither set | Defaults to `"stdio"` |

### Valid transports (server.py:103)
```python
valid_transports = {"stdio", "http", "sse", "streamable-http"}
```

### Transport execution (server.py:3029-3043)
```python
if transport != "stdio":
    run_kwargs.update(host=host, port=port)
mcp.run(transport=transport, **run_kwargs)
```

### Transport summary

| Transport | Supported | Default Port | Evidence |
|-----------|-----------|-------------|---------|
| **stdio** | Yes | N/A | server.py:124, simple_server.py:99 |
| **http** | Yes | 3010 | server.py:99, Dockerfile:30 |
| **sse** | Yes | 3010 | simple_server.py:102, server.py:103 |
| **streamable-http** | Yes | 3010 | server.py:103 (valid_transports set) |

### Docker transport
- Dockerfile sets `ENV MCP_SERVER_PORT=3010` → transport resolves to `"http"` by default
- compose.yml sets `MCP_SERVER_PORT=3010`
- Docker wrapper script (`dope-context-wrapper.sh`) does `docker exec` with stdio piping

## 12. Export / Report / File-Generation Surfaces Discovered

| Surface | Location | Description |
|---------|----------|-------------|
| Search metrics export | `server.py:get_search_metrics()` L2465-2488 | Returns JSON metrics summary |
| Index status report | `server.py:get_index_status()` L1453-1468 | Returns collection info per workspace |
| Autonomous status report | `server.py:get_autonomous_status()` L2678-2728 | Returns controller health per workspace |
| `/info` endpoint | `server.py:151-195` | Service discovery JSON (ADR-208) |
| Snapshot persistence | `server.py:_load_snapshot_metadata()` L531-564 | Reads and returns snapshot data |

No CSV, Markdown, or standalone file-generation export tools were found in the MCP surface. README.md documents JSON, Markdown, and CSV export formats (lines 556-558) but **code does not implement them** — this is a docs-code discrepancy.

## 13. Architecture / Module Boundary Notes

### Three-Plane Trinity Architecture

dope-context enforces explicit authority boundaries between search and memory planes:

- **Search plane authority:** code/docs retrieval, fusion, rerank, search provenance (server.py:84-86)
- **Memory plane authority:** decision lifecycle, decision truth records (owned by ConPort/dopecon-bridge)
- **`search_all` cross-plane integration:** read-only enrichment via dopecon-bridge, clamped to max 10 decisions, defaults to 3

Constants (server.py:84-86):
```python
TRINITY_DECISION_DEFAULT_LIMIT = 3
TRINITY_DECISION_MAX_LIMIT = 10
TRINITY_BOUNDARY_MARKER = "search-memory-authority-boundary-v1"
```

### Module Architecture

```
src/
├── mcp/
│   └── server.py          ← Orchestrator: all tools, lazy component init
├── search/
│   ├── dense_search.py    ← Qdrant multi-vector search engine
│   ├── hybrid_search.py   ← Dense+BM25 RRF fusion
│   └── docs_search.py     ← Document-specific search (extends dense)
├── embeddings/
│   ├── voyage_embedder.py ← voyage-code-3 embeddings
│   └── contextualized_embedder.py ← voyage-context-3 embeddings
├── preprocessing/
│   ├── code_chunker.py    ← Tree-sitter AST chunking
│   ├── document_processor.py ← Multi-format doc processing
│   └── models.py          ← Shared DTOs
├── context/
│   ├── openai_generator.py ← ACTIVE context generation
│   ├── claude_generator.py ← UNUSED by server
│   └── grok_generator.py   ← UNUSED by server
├── rerank/
│   └── voyage_reranker.py  ← voyage-rerank-2.5
├── pipeline/
│   ├── indexing_pipeline.py ← Code indexing orchestration
│   └── docs_pipeline.py     ← Docs indexing orchestration
├── autonomous/
│   ├── autonomous_controller.py ← Zero-touch coordinator
│   ├── watchdog_monitor.py  ← File event watcher
│   ├── indexing_worker.py   ← Async queue worker
│   └── periodic_sync.py     ← 10-min fallback
├── sync/
│   ├── file_synchronizer.py ← SHA256 change detection
│   └── incremental_indexer.py ← Chunk-level tracking
├── utils/
│   ├── workspace.py         ← Workspace detection, hashing, collection naming
│   ├── token_budget.py      ← MCP response size control
│   └── metrics_tracker.py   ← Search usage analytics
├── enrichment/
│   ├── code_graph_enricher.py ← Serena integration (lazy)
│   └── claude_code_enricher.py ← External orchestration helper
├── attention_aware_search.py ← UNUSED standalone ADHD integration
└── integration_bridge_connector.py ← ConPort-KG event bridge (conditional)
```

### Component Initialization
- **Lazy init:** Components initialize on first tool call, not at startup (server.py:3042 comment)
- **Global singletons:** `_pipeline`, `_hybrid_search`, `_reranker`, `_embedder`, `_bm25_index`, `_docs_pipeline`, `_docs_search`, `_docs_embedder` (server.py:452-461)
- **LRU caching:** `_get_cached_embedder`, `_get_cached_reranker`, `_get_cached_vector_search`, `_get_cached_contextualized_embedder`, `_get_cached_document_search` (server.py:346-448)

## 14. Intended-Use Notes

### Docs say:
- README.md describes dope-context as "Semantic Code & Documentation Search" with "ADHD Optimization"
- MCP tool names follow `mcp__dope-context__<tool_name>` convention (README.md passim)
- Supports four index types: code, docs, api, chat (multi_index_config.yaml:4-150)
- Export formats: JSON, Markdown, CSV (README.md:556-558)
- Serena, ConPort, Zen integration (README.md:462-479)

### Code does:
- Only **code** and **docs** indexes are implemented. **api** and **chat** indexes from multi_index_config.yaml have no implementation in server.py or any pipeline module.
- Export formats are NOT implemented — no CSV or Markdown export tools exist.
- Serena integration is lazy/optional (enrich_with_graph parameter, server.py:1288-1300)
- ConPort integration is conditional on `CONPORT_INTEGRATION_AVAILABLE` (server.py:69-73)
- Zen integration is not referenced in any source code
- ADHD Engine integration is feature-flagged and degrades gracefully (server.py:291-339)
- The `multi_index_config.yaml` describes a 4-index architecture but only 2 (code, docs) are wired

### Tests verify:
- `test_mcp_server.py` — Tests MCP tool functions with mocked Qdrant/Voyage clients. Verifies tool import and stub behavior.
- `test_hybrid_determinism.py` — Verifies RRF fusion determinism with fixed inputs
- `test_autonomous_controller.py` — Tests start/stop lifecycle with dummy components
- `test_docs_pipeline_invariants.py` — Tests docs pipeline with stub embedder/search
- `test_dope_context_contracts.py` — Validates JSON Schema contracts for request/response formats
- Tests do NOT verify: actual Qdrant connectivity, real embedding calls, end-to-end search, multi-workspace isolation, Trinity boundary enforcement

## 15. Missing Evidence

| Gap | Severity | Notes |
|-----|----------|-------|
| **api index** implementation | Medium | multi_index_config.yaml defines it; no code implements it |
| **chat index** implementation | Medium | multi_index_config.yaml defines it; no code implements it |
| **CSV/Markdown export** | Low | README claims support; no code implements it |
| **Zen integration** | Low | README describes it; no code references Zen |
| **Redis caching** | Low | requirements.txt includes redis; code marks caching as "Phase 3" |
| **Wrapper script path mismatch** | Medium | `dope-context-wrapper.sh` calls `/app/server.py` which doesn't exist in Docker image; CMD is `python -m src.mcp.server` |
| **End-to-end test coverage** | Medium | No integration tests with real Qdrant or real embeddings |
| **Release/tag metadata** | Low | No version tags or changelog specific to dope-context were inspected |
| **ConPort integration test** | Medium | `CONPORT_INTEGRATION_AVAILABLE` path has no test coverage |

## 16. Explicit Readiness Judgment

### **READY_FOR_PHASE_2**

**Rationale:**
1. ✅ The authoritative MCP surface is fully identified: `src/mcp/server.py` with 18 tools + 4 custom routes
2. ✅ All tool names, parameter schemas, and handler implementations are located and documented
3. ✅ Transport layer is fully characterized (stdio, http, sse, streamable-http)
4. ✅ Persistence model is fully mapped (Qdrant vectors + file-based JSON/pickle snapshots)
5. ✅ Architecture boundaries (Trinity) are explicit in code with named constants
6. ✅ Active vs deprecated/experimental modules are clearly distinguished with import evidence
7. ✅ DTOs, validators, and response builders are catalogued
8. ✅ Pipeline workflows (indexing, search, autonomous) are traced end-to-end
9. ✅ Discrepancies between docs and code are identified and documented
10. ✅ All source files under `services/dope-context/` have been inspected

**Caveats for Phase 2:**
- The `simple_server.py` is a separate, mock-only surface — it must NOT be merged with `server.py` tools
- The `multi_index_config.yaml` aspirational config (api, chat indexes) must be distinguished from implemented reality
- The wrapper script path `/app/server.py` needs reconciliation with actual Docker entrypoint
