---
id: DOPE_CONTEXT_MASTER_HISTORY
title: Dope Context Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Dope Context Master History (explanation) for dopemux documentation and developer
  workflows.
---
# Dope Context: Master History & Feature Catalog

**Service ID**: `dope-context` (Retrieval Layer)
**Role**: Semantic Search & Indexing Engine
**Primary Owner**: @hu3mann
**Latest Version**: 2.1 (Multi-Workspace Support)
**Port**: MCP (Stdio/SSE) + Qdrant (6333)

---

## 1. Executive Summary & Evolution

Dope Context is the **Retrieval Layer** of Dopemux, sitting alongside ConPort (Memory) and Serena (Navigation). It provides "Google-like" semantic search across the codebase and documentation, specifically tuned for ADHD brains that need "fuzzy" retrieval (finding "that auth thing" rather than exact regex matches).

**Evolutionary Phases:**
* **Phase 1 (Single Index)**: Basic RAG implementation using local embeddings.
* **Phase 2 (Hybrid Search)**: Adopted `Voyage AI` for embeddings (dense) combined with BM25 (sparse) and RRF fusion for higher accuracy.
* **Phase 3 (Multi-Workspace)**: Added ability to index multiple independent Git worktrees and aggregate results, solving the "Monorepo vs Polyrepo" problem.

---

## 2. Feature Catalog (Exhaustive)

### Core Capabilities
* **Hybrid Search**: Combines Dense vectors (embeddings) + Sparse (BM25) + Reranking (Voyage) for ~67% better retrieval than pure vector search.
* **4 Specialized Indices**:
    1. **Code**: Source files (AST-aware chunking via Tree-sitter).
    2. **Docs**: Markdown/PDF files (semantic chunking).
    3. **API**: OpenAPI specs and library signatures.
    4. **Chat**: Historical conversations.
* **Multi-Workspace**: Supports indexing distinct directories (e.g., `main`, `feature-branch`) and searching across them in one query.
* **Autonomous Indexing Daemon**: Background process that watches file changes and updates the index incrementally (using SHA256 hashes).

### Performance Stats
* **Latency**: <500ms (p95) for code search.
* **Recall**: High accuracy even with vague ADHD-style queries.
* **Isolation**: Perfect isolation between workspaces (collection-per-workspace).

---

## 3. Architecture Deep Dive

### The "Hybrid Pipeline"
```
Query -> [Dense Embedding] + [Sparse Keywords]
      -> [Qdrant Retrieval]
      -> [RRF Fusion] (Merge results)
      -> [Voyage Reranking] (Top 50 -> Top 10)
      -> [Progressive Disclosure] (Show 10)
```

### Integration Points
* **Serena**: Uses Serena's Tree-sitter AST parser for smart code chunking.
* **ConPort**: Indexes ConPort "Decisions" for unified search.
* **MCP**: Exposes tools like `search_code`, `docs_search`, `index_workspace`.

---

## 4. Validated Status (Audit Results)

**✅ Production Ready:**
* **Multi-Workspace**: Fully verified with 10 passing tests.
* **Fallbacks**: Gracefully handles missing heavy dependencies (`tiktoken`, `torch`) in constrained environments.
* **Test Coverage**: ~99% (93/94 tests passing).

**Known Limits**:
* **Cost**: Uses paid Voyage APIs (approx $0.20/workspace indexing).
* **Dependency**: Requires Qdrant container running.

---

*Sources: `DOPEMUX-CONTEXT-DEEP-DIVE.md`, `DOPE_CONTEXT_MULTI_WORKSPACE_COMPLETE.md`, `DOPE_CONTEXT_QUICK_START.md`.*
