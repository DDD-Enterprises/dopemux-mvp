# Arc42 - Dopemux Semantic Search Architecture

## 1. Requirements & Goals

- **Primary:** fast, accurate retrieval across code and documents; MCP-first.
- **Quality:** low latency, high precision@k, fresh indexes; observability.
- **Security:** local-first; explicit handling for non-sensitive SaaS via proxy.

## 2. Constraints

- Existing Milvus cluster (Docker).
- Claude-Context already deployed; must not regress.
- Prefer OSS and pluggable components.

## 3. System Scope & Context (C4 L0)

- **Users:** Developers, Operators.
- **External Systems:** VoyageAI API (rerankers), optional PluggedIn proxy, SaaS sources (Drive/Notion/etc. when enabled).

## 4. Solution Strategy

- Two lanes: Code (Claude-Context) and Docs (DocRAG on Milvus).
- Hybrid search capability for Docs; rerank every answer path.
- MCP servers for standard tool interfaces; Dopemux routes by intent.

## 5. Building Block View (C4 L1/L2)

### Client (Claude/Dopemux)
- **Tools:** code.search, docs.search

### Claude-Context MCP
- **Embeddings:** voyage-code-3
- **Milvus collection:** code_index

### DocRAG Service
- **Loaders:** PDF/MD/HTML/DOCX; OCR optional
- **Chunker:** 900–1,200 tokens, 10–15% overlap
- **Embeddings:** general model (configurable)
- **Milvus collection:** docs_index
- **Search:** ANN (HNSW or AUTOINDEX) → optional Hybrid (dense+sparse/BM25)
- **Rerank:** Voyage rerank-2.5

### Milvus
- **Collections:** code_index, docs_index
- **Index:** HNSW (M=16, efConstruction=200), COSINE/IP
- **Optional:** SPARSE field + WeightedRanker

### Optional PluggedIn MCP
- Aggregates SaaS connectors (non-sensitive only)

## 6. Runtime View (Request Flow)

1. Dopemux receives query → Router classifies code vs docs (or both).
2. **Docs path:** embed query → Milvus search (limit 32) → hybrid if enabled → Voyage rerank top-8 → assemble context → answer.
3. **Code path:** Claude-Context executes code-aware retrieval from code_index → answer.

## 7. Deployment View

Docker compose stack:
- milvus services (etcd, minio, milvusd)
- claude-context-mcp
- docrag (Python/FastAPI) with VOYAGE_API_KEY
- (optional) pluggedin-mcp-proxy

## 8. Cross-cutting Concepts

- **Metadata/ACLs:** owner, team, sensitivity, tags, source, path, commit, page.
- **De-duplication:** content hash per chunk; delete+insert upsert strategy.
- **Observability:** latency histos; success@k; ingest lag; index sizes.
- **Eval:** labeled queries; regression harness in CI.

## 9. Architectural Decisions

See ADRs 0028–0033.

## 10. Quality Scenarios

- P95 ≤ 350ms on warm cache for typical queries.
- Precision@5 ≥ 0.75 on eval deck of 200 queries.
- Recovery: if reranker fails, degrade gracefully to vector score.

## 11. Risks & Mitigations

- **Vendor/API limits** → cache rerank inputs; use lite model or local reranker fallback.
- **Index drift** → periodic full re-embed; versioned collections.
- **Hybrid tuning** → run ablations to set weights; keep feature flag.

## 12. Open Points

- Finalize doc embedding model + dimension.
- Choose BM25 vs custom sparse for hybrid track A/B.
- Define retention policy for meta and PII redaction in loaders.