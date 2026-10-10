---
id: DOPE-CONTEXT-ARCHITECTURE-AND-BOUNDARIES-V1
title: Dope-Context Architecture and Trinity Boundaries v1
type: reference
owner: '@hu3mann'
date: '2026-02-26'
author: '@codex'
prelude: Decision-complete reference for dope-context retrieval architecture, startup indexing modes, contracts, and Trinity boundary enforcement.
last_review: '2026-02-26'
next_review: '2026-05-27'
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/dope-context/src/mcp/server.py
    - services/dope-context/src/pipeline/docs_pipeline.py
    - services/dope-context/src/embeddings/contextualized_embedder.py
    - services/dope-context/src/search/hybrid_search.py
    - src/dopemux/cli.py
---
# Dope-Context Architecture and Trinity Boundaries v1

## Scope

This document defines the currently enforced architecture and contracts for:

- docs contextual embedding (`voyage-context-3`, grouped by document)
- code + docs hybrid retrieval
- decision enrichment boundaries
- startup autoindex behavior (bootstrap + autonomous async)

Canonical implementation surfaces:

- MCP server: `services/dope-context/src/mcp/server.py`
- docs indexing pipeline: `services/dope-context/src/pipeline/docs_pipeline.py`
- contextual embedder: `services/dope-context/src/embeddings/contextualized_embedder.py`
- hybrid fusion: `services/dope-context/src/search/hybrid_search.py`
- CLI startup trigger: `src/dopemux/cli.py`

## Runtime Architecture

### 1) Indexing paths

- **Code index**
  - initiated by `index_workspace`
  - supports autonomous updates through `start_autonomous_indexing`
- **Docs index**
  - initiated by `index_docs`
  - chunk extraction through `DocumentProcessor`
  - contextual embedding through `ContextualizedEmbedder`
  - autonomous updates through `start_autonomous_docs_indexing`

### 2) Retrieval paths

- **docs_search**
  - query embedding model is pinned to `voyage-context-3`
  - returns provenance envelope:
    - `lane_used`
    - `fusion_strategy`
    - `rerank_used`
    - `embed_model_used`
    - `timings_ms`
    - `results`
- **search_all**
  - runs code + docs retrieval in parallel
  - optional decision enrichment from dopecon-bridge
  - returns deterministic provenance and Trinity boundary metadata

### 3) Transport and server truth

- canonical container entrypoint is `python -m src.mcp.server`
- `/info` exposes:
  - `fastmcp_available`
  - runtime transport (`stdio/http/sse/streamable-http`)
  - canonical entrypoint marker

## Docs Contextual Embedding Contract

Hard fail-closed invariants per document:

1. chunk ordinals are contiguous (`0..N-1`)
2. embedding count equals chunk count
3. each chunk has deterministic:
   - `doc_id`
   - `chunk_id`
   - `ordinal`
4. on any mismatch, skip document upsert

Required payload metadata persisted per chunk:

- `workspace_id`
- `instance_id`
- `source_type` (`doc`)
- `source_uri`
- `doc_id`
- `chunk_id`
- `ordinal`
- `content_hash`
- `embed_model` (`voyage-context-3`)
- `chunker_version`

## Hybrid Determinism Contract

`HybridSearch` determinism requirements:

- reciprocal rank fusion sorted by:
  1. score descending
  2. stable identifier ascending
- final hybrid result sorting uses the same stable tie-break rule

This guarantees repeatable output order for identical inputs.

## Trinity Boundary Enforcement

### Authority split

- **Search plane**
  - owns code/docs retrieval and fusion behavior
  - owns search provenance and timings
- **Memory plane**
  - owns decisions, summaries, and decision lifecycle

### Enforced rails in dope-context

- decision enrichment is read-only through bridge search
- `search_all` decision limit defaults to **Top-3**
- decision limit is hard-clamped to **10 max**
- boundary metadata is emitted in responses:
  - `trinity_boundaries.marker`
  - configured/effective decision limits
  - authority ownership fields

## Startup Indexing Mode Contract

On Dopemux startup (`start`, `launch`, `dope`):

1. trigger autoindex bootstrap for current workspace
2. bootstrap performs one full pass:
   - `index_workspace`
   - `index_docs`
3. start ongoing async controllers:
   - code autonomous indexing
   - docs autonomous indexing
4. idempotence guard skips bootstrap if workspace snapshot already indexed

Control env vars:

- `DOPEMUX_AUTO_INDEX_ON_STARTUP`
- `DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS`
- `DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS`

## Verification Matrix

Primary test surfaces for this contract:

- `services/dope-context/tests/contract/test_dope_context_contracts.py`
- `services/dope-context/tests/test_docs_pipeline_invariants.py`
- `services/dope-context/tests/test_hybrid_determinism.py`
- `services/dope-context/tests/test_mcp_server.py`
- `tests/test_cli_mcp_startup.py`

Root hygiene and docs format gates:

- `scripts/check_root_hygiene.py`
- `scripts/docs_validator.py`
