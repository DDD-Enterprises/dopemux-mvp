---
id: dope-context-deep-dive
title: Dope Context Technical Deep Dive
type: explanation
owner: '@hu3mann'
status: draft
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Dope Context Technical Deep Dive (explanation) for dopemux documentation
  and developer workflows.
---
# Dope Context: Technical Deep Dive & Audit

## 1. System Identity
- **Component**: `dope-context`
- **Role**: Semantic Search & Code Indexing
- **Current Status**: **Potemkin Village / Mock**
- **Audit Date**: 2026-02-09

## 2. Architecture: Claims vs. Reality

### The Claim (`docs/systems/dope-context/architecture.md`)
The documentation describes a "Multi-Project Semantic Search Architecture" featuring:
- **Vector Database**: Qdrant
- **Embeddings**: Voyage AI (`voyage-code-3`, `voyage-context-3`)
- **Indexing**: 4 distinct indices (Code, Docs, API, Chat)
- **Retrieval**: Hybrid (Dense + Sparse/BM25) with RRF Fusion and Reranking.
- **Components**: `file_synchronizer.py`, `incremental_indexer.py`.

### The Reality (`services/dope-context/src/mcp/simple_server.py`)
The active service is a **Mock Server** running a simple FastAPI shell:
- **No Vector DB**: Qdrant connection is not initialized or used.
- **No Embeddings**: No Voyage AI integration.
- **Hardcoded Responses**:
- `search_code` returns: `[{"code": "# Mock code result for 'query'..."}]`
- `docs_search` returns: `[{"text": "Mock documentation for 'query'..."}]`
- **Dependencies**: Explicitly avoids `fastmcp` and vector libraries.

### Evidence Trail
- **Dockerfile**: Runs `CMD ["python", "src/mcp/simple_server.py"]`.
- **Source Code**: `services/dope-context/src/` contains complex code (`search/`, `sync/`, `embeddings/`) but it is **dead code** in the current deployment.
- **Runtime**: `docker ps` shows the container is healthy, but it is purely a placeholder.

## 3. Runtime Analysis
- **Status**: **Healthy** (Technically)
- **Port**: 3010
- **Behavior**: Responds to MCP calls, but returns fake data.
- **Purpose**: Likely a placeholder to allow other services (like Orchestrator) to boot without failing on missing dependencies.

## 4. Recommendations
1. **Acknowledge Technical Debt**: The current implementation is a placeholder. It provides zero functional value for actual context retrieval.
1. **Activation Path**: The "real" code exists in `src/`. It requires bringing up Qdrant (verified in `docker-compose`?) and configuring Voyage AI keys, then switching the `Dockerfile` entrypoint to the real MCP server.
1. **Risk**: Any agent relying on this for context is hallucinating capability.

## 5. Audit Log
- **2026-02-09**: Initial audit confirmed "Potemkin" status. Service is running but fake.
