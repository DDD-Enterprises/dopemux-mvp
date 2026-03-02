# RFC-0042: Hybrid MCP Semantic Search for Dopemux (Claude-Context + Milvus DocRAG + Voyage Reranker)

**Status:** Accepted — Phase 1 rollout
**Date:** 2025-09-21
**Owner:** Dopemux Architecture Group

## Summary

Adopt a two-lane retrieval strategy: (1) Claude-Context MCP dedicated to code search (repositories only), and (2) a DocRAG pipeline to index documents into Milvus as a separate collection with optional hybrid search (dense + sparse/BM25) and Voyage rerank-2.5 before prompt assembly. Keep PluggedIn MCP proxy optional for quick multi-SaaS trials on non-sensitive corpora.

## Motivation & Goals

- **High-precision code retrieval** to improve Claude Code loops.
- **High-recall, policy-aware document retrieval** for PDFs, MD/HTML/Docs, tickets.
- **Local-first control** (privacy, cost, tunability) with clear escape hatches to managed services.
- **MCP-native tools** that integrate cleanly with Dopemux routing.

## Non-Goals

- Building a custom vector store from scratch.
- Full ECM/DMS features; scope is semantic search + light RAG.

## Requirements

- **Collections:** code_index (Claude-Context) and docs_index (DocRAG) in the same Milvus cluster.
- **Embeddings:** voyage-code-3 (code), general-purpose model for docs (pluggable).
- **Rerank:** Voyage rerank-2.5; top-32 ANN → rerank → top-8.
- **Hybrid:** Optional Milvus hybrid search via dense + BM25 or dense + custom sparse.
- **ACL & metadata:** enforceable at query time.
- **Ingestion:** incremental, de-dupe by content hash, observable.

## Options Considered

- PluggedIn MCP as primary
- Claude-Context only
- Vector-DB MCP only (Milvus/Qdrant/Weaviate)
- **Hybrid (recommended)**

## Decision

Ship the Hybrid: Claude-Context for code; Milvus DocRAG for docs; Voyage reranker. Optional PluggedIn for non-sensitive SaaS.

## Impact

- Best-of-breed code search without diluting index with docs.
- Tunable document pipeline with hybrid retrieval and reranking.
- Clear privacy posture and cost predictability.

## Rollout Plan

1. Exclude /docs from Claude-Context and rebuild code_index.
2. Create docs_index in Milvus; deploy DocRAG ingestion and search API.
3. Wire docs.search and code.search tools; add Dopemux routing.
4. Add evaluation harness (success@k, latency SLOs, freshness).

## SLIs/SLOs

- p50 ≤ 150ms, p95 ≤ 350ms for warm queries.
- Top-5 precision ≥ 0.75 on eval set; error budget 10%/month.
- Ingest-to-search freshness < 5 minutes for changed files.

## Security & Privacy

- Self-host Milvus for sensitive corpora; controlled connectors; audit logs.
- PluggedIn gated behind env flag; not used for sensitive data.