# APPENDIX_A_SOURCE_INDEX.md — dope-context Phase 1 Discovery

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

Every file inspected during Phase 1, grouped by category.

---

## Root Docs

| File | Lines | Purpose |
|------|-------|---------|
| `services/dope-context/README.md` | 595 | Service overview, tool documentation, configuration guide |

## docs/ (repo-level references, not inside service)

| File | Purpose |
|------|---------|
| `docs/03-reference/dope-context/dope-context-architecture-and-boundaries-v1-2.md` | Architecture reference (listed, not read in this pass) |
| `docs/03-reference/dope-context/dope-context-docs-contextual-embedding-v1-2.md` | Embedding reference (listed, not read) |
| `docs/02-how-to/dope-context/dope-context-user-guide.md` | User guide (listed, not read) |
| `docs/04-explanation/technical-deep-dives/dope-context-technical-deep-dive.md` | Technical deep dive (listed, not read) |
| `docs/systems/dope-context/architecture.md` | System architecture docs (listed, not read) |
| `docs/systems/dope-context/api-reference.md` | API reference docs (listed, not read) |
| `docs/systems/dope-context/autonomous-indexing.md` | Autonomous indexing docs (listed, not read) |
| `docs/systems/dope-context/deployment.md` | Deployment guide (listed, not read) |

## Source — MCP Layer

| File | Lines | Key Symbols |
|------|-------|-------------|
| `src/mcp/server.py` | 3043 | `mcp` (FastMCP instance), 18 `@mcp.tool()` functions, 4 `@mcp.custom_route` endpoints, `_resolve_transport_runtime()`, `_initialize_components()`, `__main__` |
| `src/mcp/simple_server.py` | 103 | `mcp` (FastMCP "Dope-Context"), 3 mock tools: `search_code`, `docs_search`, `get_index_status` |
| `src/mcp/fastmcp_stub.py` | 41 | `FastMCP` (stub class), `tool()`, `custom_route()`, `run()` |
| `src/mcp/setup.py` | 14 | `setup(name="dope-context-mcp", version="1.0.0")` |

## Source — Search

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/search/dense_search.py` | 80+ | `MultiVectorSearch`, `SearchProfile`, `SearchResult` |
| `src/search/hybrid_search.py` | 80+ | `HybridSearch`, `BM25Index`, `code_aware_tokenizer`, `reciprocal_rank_fusion` |
| `src/search/docs_search.py` | 75 | `DocumentSearch` (extends `MultiVectorSearch`) |

## Source — Embeddings

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/embeddings/voyage_embedder.py` | 60+ | `VoyageEmbedder`, `EmbeddingRequest`, `EmbeddingResponse`, `CostTracker` |
| `src/embeddings/contextualized_embedder.py` | 60+ | `ContextualizedEmbedder`, `ContextualizedEmbeddingResponse`, `CostTracker` |

## Source — Preprocessing

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/preprocessing/code_chunker.py` | 60+ | `CodeChunker`, `CodeChunk`, `ChunkingConfig` |
| `src/preprocessing/document_processor.py` | 60+ | `DocumentProcessor` |
| `src/preprocessing/models.py` | 47 | `DocumentType`, `ChunkMetadata`, `DocumentChunk` |

## Source — Context Generators

| File | Lines (viewed) | Key Symbols | Status |
|------|---------------|-------------|--------|
| `src/context/openai_generator.py` | 40+ | `OpenAIContextGenerator`, `ContextRequest`, `ContextResponse` | ACTIVE (imported by server.py) |
| `src/context/claude_generator.py` | 30+ | `ClaudeContextGenerator` | UNUSED by server.py |
| `src/context/grok_generator.py` | 30+ | `GrokContextGenerator`, `ContextResponse` | UNUSED by server.py |

## Source — Reranking

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/rerank/voyage_reranker.py` | 60+ | `VoyageReranker`, `RerankResult`, `RerankResponse`, `CostTracker` |

## Source — Pipeline

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/pipeline/indexing_pipeline.py` | 80+ | `IndexingPipeline`, `IndexingConfig`, `IndexingProgress` |
| `src/pipeline/docs_pipeline.py` | 80+ | `DocIndexingPipeline`, `DocsIndexingProgress` |

## Source — Autonomous Indexing

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/autonomous/autonomous_controller.py` | 80+ | `AutonomousController`, `AutonomousConfig` |
| `src/autonomous/watchdog_monitor.py` | 40+ | `DebouncedFileHandler`, `WatchdogMonitor` |
| `src/autonomous/indexing_worker.py` | 40+ | `IndexingWorker` |
| `src/autonomous/periodic_sync.py` | 40+ | `PeriodicSync` |

## Source — Sync

| File | Lines (viewed) | Key Symbols |
|------|---------------|-------------|
| `src/sync/file_synchronizer.py` | 60+ | `FileSynchronizer`, `FileSnapshot`, `WorkspaceSnapshot`, `ChangeSet` |
| `src/sync/incremental_indexer.py` | 60+ | `IncrementalIndexer`, `ChunkMetadata`, `FileChunkMap`, `ChunkSnapshot` |

## Source — Utils

| File | Lines | Key Symbols |
|------|-------|-------------|
| `src/utils/workspace.py` | 222 | `get_workspace_root()`, `workspace_to_hash()`, `get_collection_names()`, `get_snapshot_dir()` |
| `src/utils/token_budget.py` | 60+ | `truncate_code_results()`, `truncate_docs_results()`, `TruncationResult`, `estimate_tokens()` |
| `src/utils/metrics_tracker.py` | 60+ | `MetricsTracker`, `SearchMetric`, `get_tracker()` |

## Source — Enrichment

| File | Lines (viewed) | Key Symbols | Status |
|------|---------------|-------------|--------|
| `src/enrichment/code_graph_enricher.py` | 60+ | `CodeGraphEnricher` | Lazy-loaded in server.py |
| `src/enrichment/claude_code_enricher.py` | 60+ | `enrich_with_code_graph()` | External orchestration only |

## Source — Integration

| File | Lines (viewed) | Key Symbols | Status |
|------|---------------|-------------|--------|
| `src/integration_bridge_connector.py` | 40+ | `initialize_integration()`, `emit_search_completed` | Conditional import |
| `src/attention_aware_search.py` | 40+ | `AttentionAwareSearch` | UNUSED by server.py |
| `bridge_adapter.py` | 60+ | `DopeContextBridgeAdapter` | UNUSED by server.py |

## Source — Package Init

| File | Lines | Content |
|------|-------|---------|
| `src/__init__.py` | 1 | `"""Namespace package for dope-context modules."""` |

## Tests

| File | Lines (viewed) | What It Tests |
|------|---------------|---------------|
| `tests/test_mcp_server.py` | 80+ | MCP tool functions with mocked Qdrant/Voyage |
| `tests/test_hybrid_determinism.py` | 60+ | RRF fusion determinism |
| `tests/test_autonomous_controller.py` | 60+ | Controller start/stop lifecycle |
| `tests/test_docs_pipeline_invariants.py` | 60+ | Docs pipeline with stub components |
| `tests/contract/test_dope_context_contracts.py` | 80+ | JSON Schema contract validation |
| `tests/test_mcp_server.py.bak` | — | Backup file (inactive) |

## Build / Runtime

| File | Lines | Purpose |
|------|-------|---------|
| `Dockerfile` | 47 | Production image (python:3.11-slim, CMD python -m src.mcp.server) |
| `Dockerfile.fixed` | 56 | Multi-stage build variant |
| `requirements.txt` | 49 | Python dependencies |
| `.dockerignore` | — | Docker build exclusions |
| `config/multi_index_config.yaml` | 235 | Four-index architecture config (code, docs, api, chat) |

## Compose / Wrappers

| File | Lines (viewed) | Purpose |
|------|---------------|---------|
| `compose.yml` (lines 316-349) | 34 | dope-context service definition |
| `scripts/mcp-wrappers/dope-context-wrapper.sh` | 78 | Docker exec wrapper for stdio MCP |

## Contract Schemas

| File | Purpose |
|------|---------|
| `contracts/dope-context/docs_grouped_embed.request.schema.json` | JSON Schema for docs embedding requests |
| `contracts/dope-context/search.response.schema.json` | JSON Schema for search responses |

## Release / Tag Sources

No release-specific metadata was inspected in this pass. The analyzed ref is a branch commit, not a tagged release.
