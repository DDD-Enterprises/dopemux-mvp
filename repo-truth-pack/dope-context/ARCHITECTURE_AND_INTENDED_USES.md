# ARCHITECTURE_AND_INTENDED_USES.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

---

## 1. System Purpose

dope-context is a **semantic code and documentation search** MCP server designed for ADHD-optimized developer workflows. It provides hybrid retrieval (dense + sparse + rerank), autonomous zero-touch indexing, and cross-plane decision enrichment via the Trinity architecture.

## 2. Module Architecture

```
services/dope-context/
├── src/
│   ├── mcp/
│   │   ├── server.py              ← ORCHESTRATOR (3043 lines)
│   │   │                            18 @mcp.tool(), 4 @mcp.custom_route()
│   │   │                            Lazy component init, all business logic
│   │   ├── simple_server.py        ← MOCK (3 hardcoded tools, not imported)
│   │   ├── fastmcp_stub.py         ← FALLBACK (test-env stub for FastMCP)
│   │   └── setup.py                ← PACKAGING (setuptools stub)
│   │
│   ├── search/
│   │   ├── dense_search.py         ← Multi-vector Qdrant search engine
│   │   │                            Classes: MultiVectorSearch, SearchProfile, SearchResult
│   │   ├── hybrid_search.py        ← Dense+BM25 RRF fusion
│   │   │                            Classes: HybridSearch, BM25Index
│   │   │                            Functions: code_aware_tokenizer, reciprocal_rank_fusion
│   │   └── docs_search.py          ← Document-specific search (extends dense)
│   │                                Class: DocumentSearch (extends MultiVectorSearch)
│   │
│   ├── embeddings/
│   │   ├── voyage_embedder.py      ← Standard embeddings (voyage-code-3)
│   │   │                            Classes: VoyageEmbedder, EmbeddingRequest, EmbeddingResponse
│   │   └── contextualized_embedder.py ← Contextualized embeddings (voyage-context-3)
│   │                                   Classes: ContextualizedEmbedder, ContextualizedEmbeddingResponse
│   │
│   ├── preprocessing/
│   │   ├── code_chunker.py         ← Tree-sitter AST chunking
│   │   │                            Classes: CodeChunker, CodeChunk, ChunkingConfig
│   │   ├── document_processor.py   ← Multi-format doc processing (PDF, DOCX, HTML, MD)
│   │   │                            Class: DocumentProcessor
│   │   └── models.py               ← Shared DTOs
│   │                                Enum: DocumentType (markdown, pdf, html, text, code, docx)
│   │                                Classes: ChunkMetadata, DocumentChunk
│   │
│   ├── context/
│   │   ├── openai_generator.py     ← ACTIVE — Context generation for embeddings
│   │   │                            Classes: OpenAIContextGenerator, ContextRequest, ContextResponse
│   │   ├── claude_generator.py     ← UNUSED by server.py
│   │   └── grok_generator.py       ← UNUSED by server.py
│   │
│   ├── rerank/
│   │   └── voyage_reranker.py      ← Voyage reranking (voyage-rerank-2.5)
│   │                                Classes: VoyageReranker, RerankResult, RerankResponse
│   │
│   ├── pipeline/
│   │   ├── indexing_pipeline.py    ← Code indexing orchestration
│   │   │                            Classes: IndexingPipeline, IndexingConfig, IndexingProgress
│   │   └── docs_pipeline.py        ← Docs indexing orchestration
│   │                                Classes: DocIndexingPipeline, DocsIndexingProgress
│   │
│   ├── autonomous/
│   │   ├── autonomous_controller.py ← Zero-touch coordinator
│   │   │                             Classes: AutonomousController, AutonomousConfig
│   │   ├── watchdog_monitor.py     ← File event watcher (watchdog library)
│   │   │                            Classes: DebouncedFileHandler, WatchdogMonitor
│   │   ├── indexing_worker.py      ← Async queue consumer
│   │   │                            Class: IndexingWorker
│   │   └── periodic_sync.py        ← 10-min fallback sync
│   │                                Class: PeriodicSync
│   │
│   ├── sync/
│   │   ├── file_synchronizer.py    ← SHA256 change detection
│   │   │                            Classes: FileSynchronizer, FileSnapshot, WorkspaceSnapshot, ChangeSet
│   │   └── incremental_indexer.py  ← Chunk-level tracking
│   │                                Classes: IncrementalIndexer, ChunkMetadata, FileChunkMap, ChunkSnapshot
│   │
│   ├── utils/
│   │   ├── workspace.py            ← Workspace detection, hashing, collection naming
│   │   │                            Functions: get_workspace_root, workspace_to_hash,
│   │   │                                      get_collection_names, get_snapshot_dir
│   │   ├── token_budget.py         ← MCP response size control
│   │   │                            Functions: truncate_code_results, truncate_docs_results,
│   │   │                                      estimate_tokens
│   │   │                            Class: TruncationResult
│   │   └── metrics_tracker.py      ← Search usage analytics
│   │                                Classes: MetricsTracker, SearchMetric
│   │                                Function: get_tracker
│   │
│   ├── enrichment/
│   │   ├── code_graph_enricher.py  ← Serena integration (lazy-loaded, conditional)
│   │   │                            Class: CodeGraphEnricher
│   │   └── claude_code_enricher.py ← External orchestration helper (not imported by server)
│   │
│   ├── integration_bridge_connector.py ← ConPort-KG event bridge (conditional import)
│   │                                     Functions: initialize_integration, emit_search_completed
│   ├── attention_aware_search.py   ← UNUSED standalone ADHD integration
│   │                                Class: AttentionAwareSearch
│   └── __init__.py                 ← Namespace package
│
├── bridge_adapter.py              ← DopeconBridge adapter (NOT imported by server)
│                                    Class: DopeContextBridgeAdapter
├── config/
│   └── multi_index_config.yaml    ← Four-index architecture config (aspirational)
├── tests/                         ← Test suite
├── Dockerfile                     ← Single-stage production build
├── Dockerfile.fixed               ← Multi-stage optimized build
└── requirements.txt               ← 49 Python dependencies
```

## 3. Responsibilities by Module

| Module | Responsibility | Authority |
|--------|---------------|-----------|
| **mcp/server.py** | Tool registration, request routing, lazy init, business orchestration | Orchestrator / API surface |
| **search/** | Vector search, hybrid fusion, BM25 indexing | Search execution |
| **embeddings/** | Text-to-vector conversion via Voyage AI APIs | Embedding generation |
| **preprocessing/** | Source code parsing (tree-sitter), document format handling | Content preparation |
| **context/** | LLM-based context snippet generation for embeddings | Embedding enrichment |
| **rerank/** | Result reranking via Voyage rerank API | Relevance refinement |
| **pipeline/** | End-to-end indexing orchestration (chunking → embedding → storage) | Indexing workflow |
| **autonomous/** | Zero-touch file monitoring and incremental indexing | Background operations |
| **sync/** | File change detection via SHA256 snapshots | Change tracking |
| **utils/** | Workspace detection, token budgeting, metrics | Cross-cutting utilities |
| **enrichment/** | Code graph relationship enrichment (optional) | Result decoration |

## 4. Dependency Graph

```
server.py (orchestrator)
  ├── search/dense_search.py (MultiVectorSearch, SearchProfile)
  ├── search/hybrid_search.py (HybridSearch, BM25Index)
  ├── search/docs_search.py (DocumentSearch)
  ├── embeddings/voyage_embedder.py (VoyageEmbedder)
  ├── embeddings/contextualized_embedder.py (ContextualizedEmbedder)
  ├── rerank/voyage_reranker.py (VoyageReranker)
  ├── preprocessing/code_chunker.py (CodeChunker, ChunkingConfig)
  ├── context/openai_generator.py (OpenAIContextGenerator)
  ├── pipeline/indexing_pipeline.py (IndexingPipeline, IndexingConfig)
  ├── pipeline/docs_pipeline.py (DocIndexingPipeline)
  ├── sync/file_synchronizer.py (FileSynchronizer, ChangeSet)
  ├── autonomous/autonomous_controller.py (AutonomousController, AutonomousConfig)
  ├── utils/workspace.py (workspace functions)
  ├── utils/token_budget.py (truncation functions)
  ├── utils/metrics_tracker.py (get_tracker)
  └── [conditional] dopecon_bridge_connector (emit_search_completed)
```

## 5. Transport Architecture

| Transport | Default | Port | Evidence |
|-----------|---------|------|----------|
| **stdio** | Yes (no PORT env) | N/A | `server.py:101,124` |
| **http** | Yes (PORT env set) | 3010 | `server.py:99`, Dockerfile |
| **sse** | Supported | 3010 | `server.py:103` |
| **streamable-http** | Supported | 3010 | `server.py:103` |

Transport resolution: `_resolve_transport_runtime()` (server.py:93-126)

### Environment Variable Priority
1. `MCP_TRANSPORT` or `FASTMCP_TRANSPORT` → explicit transport name
2. `MCP_SERVER_PORT` set (no transport env) → defaults to `"http"`
3. Neither set → defaults to `"stdio"`

### Host Resolution
1. `MCP_SERVER_HOST` or `FASTMCP_HOST` → explicit host
2. Default: `"0.0.0.0"`

### Port Resolution
1. `MCP_SERVER_PORT` or `FASTMCP_PORT` or `PORT`
2. Default: `3010`

## 6. Persistence Boundaries

### Durable (survives restart)
| Store | Location | Format | Content |
|-------|----------|--------|---------|
| Qdrant vectors | Qdrant service (6333) | Vector DB | Code/docs embeddings |
| File snapshots | `~/.dope-context/snapshots/{hash}/snapshot.json` | JSON | File SHA256 hashes |
| Chunk snapshots | `~/.dope-context/snapshots/{hash}/chunk_snapshot.json` | JSON | Chunk-level metadata |
| BM25 cache | `~/.dope-context/snapshots/{hash}/bm25_index.pkl` | pickle | BM25 index data |
| Bootstrap markers | `~/.dope-context/snapshots/{hash}/autoindex_bootstrap.json` | JSON | Idempotence markers |
| Decision config | `~/.dope-context/snapshots/{hash}/decision_sync_config.json` | JSON | Per-workspace config |
| Search metrics | `~/.dope-context/search_metrics.json` | JSON | Usage analytics |

### Ephemeral (in-memory only)
| State | Location | Lifetime |
|-------|----------|----------|
| LRU-cached embedders | `_get_cached_embedder` etc. | Process lifetime |
| Global singletons | `_pipeline`, `_hybrid_search`, etc. | Process lifetime |
| Autonomous controllers | `AutonomousController._active_controllers` | Process lifetime |
| Bootstrap tasks | `_autoindex_bootstrap_tasks` | Process lifetime |
| Bootstrap status | `_autoindex_bootstrap_status` | Process lifetime |
| ADHD config | `_adhd_config`, `_adhd_feature_flags` | Process lifetime |

## 7. Authority Boundaries (Trinity Architecture)

### Constants (server.py:84-86)
```python
TRINITY_DECISION_DEFAULT_LIMIT = 3
TRINITY_DECISION_MAX_LIMIT = 10
TRINITY_BOUNDARY_MARKER = "search-memory-authority-boundary-v1"
```

### Boundary Rules
| Plane | Authority | Owned By | Access Pattern |
|-------|-----------|----------|----------------|
| **Search Plane** | Code/docs retrieval, fusion, rerank | dope-context | Read/Write to Qdrant |
| **Memory Plane** | Decision lifecycle, truth records | ConPort/dopecon-bridge | Read-only from dope-context |
| **Cognitive Plane** | Attention state, result tuning | ADHD Engine | Read-only from dope-context |

dope-context **never writes** to ConPort or ADHD Engine. It only reads decisions from dopecon-bridge via HTTP and attention state from ADHD Engine via Redis.

## 8. Intended Uses

### Primary (code does)
1. **Code search** — Hybrid dense+sparse retrieval with Voyage reranking
2. **Document search** — Semantic search over PDF/MD/HTML/TXT with contextualized embeddings
3. **Unified search** — Combined code+docs+decisions with Trinity boundary enforcement
4. **Autonomous indexing** — Zero-touch file monitoring with watchdog + debounce + periodic sync
5. **Incremental sync** — SHA256-based change detection with optional auto-reindex
6. **Complexity analysis** — AST-based code complexity scoring (0.0-1.0)
7. **Bootstrap indexing** — Idempotent startup indexing with marker-based skip logic
8. **Search metrics** — Usage analytics for benchmarking

### Secondary (code supports but conditionally)
1. **Code graph enrichment** — Serena integration via `enrich_with_graph=True` (lazy-loaded)
2. **ConPort event emission** — Search event tracking via `emit_search_completed` (conditional import)
3. **ADHD dynamic top_k** — Attention-aware result limits (feature-flagged)
4. **Decision enrichment** — ConPort decision retrieval in unified search (config-gated)

### Aspirational (docs say, code doesn't do)
1. **API index** — `multi_index_config.yaml` defines it; no implementation
2. **Chat index** — `multi_index_config.yaml` defines it; no implementation
3. **CSV/Markdown export** — README claims support; no implementation
4. **Zen integration** — README describes it; no code reference
5. **Redis caching** — requirements.txt includes redis; marked "Phase 3"

## 9. Component Initialization

### Lazy Initialization Pattern
Components are NOT initialized at server startup. They initialize on first tool call via:
- Global singletons set in `_initialize_components()` (server.py:795-878)
- LRU-cached factory functions: `_get_cached_embedder`, `_get_cached_reranker`, `_get_cached_vector_search`, `_get_cached_contextualized_embedder`, `_get_cached_document_search`
- Per-tool workspace-scoped components created inline

### LRU Cache Configuration
| Factory | maxsize | Key | Evidence |
|---------|---------|-----|----------|
| `_get_cached_embedder` | 10 | `(api_key, model)` | server.py:346 |
| `_get_cached_reranker` | 10 | `(api_key,)` | server.py:365 |
| `_get_cached_vector_search` | 20 | `(collection_name, url, port)` | server.py:383 |
| `_get_cached_contextualized_embedder` | 10 | `(api_key,)` | server.py:408 |
| `_get_cached_document_search` | 20 | `(collection_name, url, port)` | server.py:426 |

## 10. Workspace Resolution

Two resolution strategies exist:

### `_resolve_target_workspaces` (server.py:603-633)
Used by: `get_index_status`
- Accepts explicit paths
- Falls back to **snapshot discovery** (reads existing snapshot metadata)
- Final fallback: `get_workspace_root()`

### `_resolve_explicit_workspaces` (server.py:636-664)
Used by: `index_workspace`, `search_code`, `docs_search`, `search_all`, `sync_workspace`, `sync_docs`, `start_autonomous_indexing`, `stop_autonomous_indexing`, `start_autonomous_docs_indexing`, `stop_autonomous_docs_indexing`
- Accepts explicit paths only
- Falls back to `get_workspace_root()` (if `fallback_to_current=True`)
- Does NOT discover from snapshots

### Multi-Workspace Pattern
All tools support single or batch workspace operation:
- Single workspace: return direct result
- Multiple workspaces: return `{workspace_count, results: [{workspace, ...}]}`
