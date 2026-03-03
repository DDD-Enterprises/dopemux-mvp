# RAG & Search Architecture Guide

## Executive Summary

This document outlines Dopemux's comprehensive Retrieval-Augmented Generation (RAG) and search architecture, designed for optimal code and documentation retrieval across development workflows.

### Key Recommendations

1. **Use VoyageAI's specialized models** for best accuracy: `voyage-code-3` for code and `voyage-context-3` for docs (they beat OpenAI-v3 by >12–14%). **Now**: swap Claude-Context to Voyage models (or Nomic open-models) via env vars. **3–6mo**: unify code/docs in one hybrid Milvus index with shared schemas.

2. **Deploy hybrid retrieval architecture**: **Now**: deploy DocRAG MCP on Milvus with hybrid (dense+BM25) and a reranker for high-precision QA; use Claude-Context (Voyage embedder) for code search. **3–6mo**: merge indices and frontends into a unified retrieval service for multi-domain queries.

3. **Implement hybrid retrieval (dense+BM25)** for docs to maximize recall (BM25 good for exact matches, dense for semantics). Prefer RRF rank fusion for combining scores (robust to mismatched scales). **Now**: Milvus-sparse or OpenSearch for BM25 sidecar and RRF weighting (e.g. 60; dense 0.6, bm25 0.4).

4. **Use Voyage rerank-2.5** for best QA accuracy, with rerank-2.5-lite when latency is critical (2.5 improves on 2 by ~1.85% at same cost). Rerank top50→return10 by default. Skip rerank on low-latency or high-throughput paths.

5. **Scale ConPort strategically**: ConPort (project knowledge) currently persists to SQLite (one DB/workspace). Scale by migrating to Postgres+pgvector or a graph DB if relationships/queries need growth. Expose ConPort content to RAG by indexing decision entries into doc index or adding a semantic_search_conport tool.

6. **Implement semantic caching**: Cache semantic results (e.g. with Redis) on stable queries (cosine ≥0.82) with TTL (e.g. 24h) to save API calls. Plan for cache invalidation when docs or code change.

7. **Monitor performance**: Monitor latencies: aim p95 <200ms for code search (dense/Milvus), <800–1200ms for doc search with rerank. Estimate costs: embedding ~$0.18 per 1M tokens (Voyage), rerank ~$0.05 per 1M tokens. Use RAG-only for critical tasks to limit calls.

8. **Follow migration plan**: 1) Confirm Claude-Context embedder and switch to Voyage; 2) Launch DocRAG MCP, backfill doc embeddings, enable rerank; 3) Add BM25 (Milvus-sparse or OpenSearch), tune fusion; 4) Unify code/docs on Milvus, migrate ConPort to scalable store. 5) Rollback by reverting embedder/env and dual-read.

## When to Use Each Component

### Code Search (Claude-Context/Code-index)
Use for developer-centric tasks: find functions, methods, class usages, or code snippets from natural queries (e.g. 'authentication function', stack traces). This pipeline is optimized for code semantics.

### Documentation Search (DocRAG)
Use for natural-language queries answered by docs: design docs, ADRs/RFCs, READMEs, issue trackers. Use semantic + BM25 to handle terminology and paraphrases.

### Unified Retrieval (3–6mo)
Use when queries span both code and docs (e.g. "How do we handle auth in our system?"). In a multi-project view, unify indices so an assistant can search all content in one call.

### Reranking Strategy
Enable rerank (Voyage-2.5) when top-10 precision is critical (e.g. final answers in an IDE prompt or CI assistant); skip rerank in preliminary searches (e.g. autocomplete or broad discovery) to save latency.

### Semantic Caching
Use semantic cache for repeated queries (common tasks/FAQs) across sessions to improve throughput; fallback to fresh embedding if result outdated (detect via TTL or manual reset).

## Production Configurations

### Code Search (Current Implementation)

```yaml
environment:
  EMBEDDING_PROVIDER: "VoyageAI"
  EMBEDDING_MODEL: "voyage-code-3"
  MILVUS_ADDRESS: "<host:port or Zilliz endpoint>"
  MILVUS_TOKEN: ""

chunking:
  unit: "function"
  prelude_tokens: 40
  max_tokens_per_chunk: 600

retrieval:
  mode: "hybrid"
  K_initial: 80
  filters:
    repo: "<repo_name>"
    lang: ["py", "ts"]

rerank:
  enabled: true
  model: "voyage-rerank-2.5"
  candidate_k: 50
  return_k: 10
  timeout_ms: 1200

observability:
  metrics: ["latency_p50", "latency_p95", "nDCG@10", "MRR"]
  logging: "info"
```

### Documentation Search (Current Implementation)

```yaml
embeddings:
  model: "voyage-context-3"
  chunk_tokens: 1200
  overlap_tokens: 150
  metadata: ["title", "h1_h2", "filepath", "repo", "doctype"]

store:
  type: "Milvus"
  collection: "docs_v1"
  index:
    metric: "cosine"
    type: "HNSW"
    params:
      M: 32
      efConstruction: 200

hybrid:
  bm25: "OpenSearch"
  fusion: "RRF"
  K_initial: 100
  fusion_params:
    rrf_k: 60
    weights:
      dense: 0.6
      bm25: 0.4

rerank:
  model: "voyage-rerank-2.5"
  candidate_k: 50
  return_k: 10

observability:
  dashboards: ["index-health", "query-latency"]
  alerts: ["p95>1200ms", "ingest-failures>0.5%"]
```

### Unified Search (3–6 Month Target)

```yaml
collections:
  code: "code_v2"
  docs: "docs_v2"
  schema_notes: "shared metadata fields; per-type embeddings"

hybrid:
  dense:
    index: "HNSW"
    metric: "cosine"
  sparse: "BM25 via OpenSearch or Milvus-sparse"
  fusion: "RRF"
  K_initial: 120

rerank:
  enabled: true
  model: "voyage-rerank-2.5"
  candidate_k: 60
  return_k: 12

cache:
  semantic:
    enabled: true
    similarity_threshold: 0.82
    ttl_seconds: 86400
    invalidation: "on-doc-update|manual"

security:
  auth: "OIDC+API keys"
  tenant_isolation: "collection or partition per tenant"
```

## Evaluation Plan

### Datasets
- **Code**: Function/class lookup queries, Stack trace→source search, Class/method searches
- **Docs**: ADR/RFC paragraph retrieval, Spec or QA from design docs, README/issue-based questions

### Metrics
- **nDCG@10**: Normalized Discounted Cumulative Gain at 10 results
- **MRR**: Mean Reciprocal Rank
- **Recall@50**: Recall at 50 results
- **Latency**: p50 and p95 response times

### Evaluation Procedure
Index documents as chunks. For each query, retrieve top-K (dense and BM25), fuse results, rerank top candidates (if enabled), then measure nDCG@10, MRR. Inspect failure cases, adjust chunk size/K/fusion weights/rerank threshold as needed.

## Migration Strategy

### Phase 1: Embedder Migration
Verify and switch Claude-Context to target embedder (VoyageAI code-3); confirm hybrid search config. Fall back to OpenAI if issues.

### Phase 2: DocRAG Deployment
Deploy DocRAG MCP: ingest docs, embed with context-3, build Milvus collection. Enable hybrid search and Voyage reranker on this pipeline.

### Phase 3: Hybrid & Unification
Add BM25 sidecar (OpenSearch or Milvus-sparse) and tune fusion. Consolidate code/docs indices (Milvus collections); retire duplicate retrieval paths. Migrate ConPort to scalable DB if needed.

### Rollback Strategy
Fallback to previous embedder/store by toggling env; maintain dual-read setup for one release while issues are resolved.

## Risk Assessment

### Technical Risks
- **Embedding model drift**: Model updates or domain shift may degrade quality (monitor via eval)
- **Index growth**: Large code/docbase can slow search or lower recall (plan periodic reindexing, sharding)
- **Cache staleness**: Outdated cached results if code/docs change (invalidate on updates or use short TTL)
- **Hybrid mismatch**: Semantic vs lexical may disagree; ensure fusion method is robust (RRF recommended)

### Operational Risks
- **Reranking cost**: LLM-based reranker adds latency and expense; use lightweight rerank when needed
- **Vendor/API issues**: Reliance on external embeddings/rerank APIs risks outages or cost spikes (have OpenAI fallback and budget limits)

## Supporting Research & Citations

1. **VoyageAI code-3 performance**: voyage-code-3 embedding yields ~13.8% higher code retrieval accuracy than OpenAI's text-embedding-3-large ([Voyage Blog, 2024-12-04](https://blog.voyageai.com/2024/12/04/voyage-code-3.html))

2. **Salesforce CodeXEmbed**: CodeXEmbed (7B) achieves new SOTA in code retrieval, outperforming Voyage Code by >20% on CoIR benchmark ([arXiv, 2024-11-15](https://arxiv.org/abs/2411.12644))

3. **Nomic Embed Code**: Nomic Embed Code (7B) outperforms Voyage Code 3 and OpenAI Embed-3-Large on CodeSearchNet benchmarks ([Hugging Face, 2024-12-01](https://huggingface.co/nomic-ai/nomic-embed-code))

4. **VoyageAI context-3 performance**: voyage-context-3 embedding yields ~14.2% higher retrieval accuracy on document chunks than OpenAI-v3-large ([Voyage Blog, 2025-07-23](https://blog.voyageai.com/2025/07/23/voyage-context-3.html))

5. **Voyage rerank-2.5**: rerank-2.5 outperforms rerank-2 by ~1.85% (and rerank-2.5-lite outperforms 2-lite by ~3.4%) at same cost ([Voyage Blog, 2025-08-11](https://blog.voyageai.com/2025/08/11/rerank-2-5.html))

6. **RRF implementation**: RRF combines scores via ∑1/(rank+k), with k≈60 giving best performance ([Azure AI Docs, 2025-08-27](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking))

7. **ConPort architecture**: Context Portal uses SQLite (one DB per workspace) for structured context storage with vector embeddings and semantic search capabilities ([GitHub, 2024](https://github.com/GreatScottyMac/context-portal))

## Validation Requirements

The following assumptions need validation during implementation:

1. **Claude-Context embedder flexibility**: Confirm Claude-Context supports swapping embedder via environment variables (VoyageAI, OpenAI, etc.)
2. **ConPort persistence patterns**: Validate how ConPort currently persists to SQLite per workspace and read/write operation frequency
3. **Milvus sparse search capabilities**: Determine if Milvus/Zilliz supports built-in sparse (BM25) search or if OpenSearch is needed as sidecar for lexical queries

---

*Last updated: 2025-09-24*
*Related: [MCP Architecture](./mcp-architecture.md), [Search Performance](../performance/search-metrics.md)*