# ADR-013: RAG & Search Architecture with VoyageAI and Hybrid Retrieval

## Status
**Accepted** - 2025-09-24

## Context

Dopemux requires sophisticated search capabilities across both code and documentation to support ADHD-optimized development workflows. The current implementation has several limitations:

1. **Suboptimal embedding models**: Using OpenAI text-embedding-3-large for both code and documentation
2. **Single retrieval method**: Dense vector search only, missing lexical matching capabilities
3. **Fragmented search experience**: Separate systems for code (Claude-Context) and docs with no unified interface
4. **Performance gaps**: No reranking, caching, or optimization for common queries
5. **Scalability concerns**: ConPort using SQLite per workspace may not scale

## Decision

We will implement a comprehensive RAG & Search Architecture with the following components:

### Immediate Changes (Phase 1)
1. **Switch to VoyageAI specialized embeddings**:
   - `voyage-code-3` for code search (13.8% better than OpenAI)
   - `voyage-context-3` for document search (14.2% better than OpenAI)

2. **Deploy hybrid retrieval**:
   - Dense vector search (semantic similarity)
   - BM25 sparse search (lexical matching)
   - RRF (Reciprocal Rank Fusion) with k=60, weights: dense=0.6, sparse=0.4

3. **Implement reranking**:
   - Voyage rerank-2.5 for high-precision results
   - Top-50 candidates → return top-10
   - Skip reranking for low-latency paths

### Medium-term Evolution (Phase 2-3)
4. **Unified search interface**: Single API for code + docs queries
5. **Semantic caching**: Redis cache for stable queries (cosine ≥0.82, 24h TTL)
6. **ConPort scaling**: Migrate from SQLite to Postgres+pgvector or graph DB

## Consequences

### Positive
- **Improved accuracy**: 12-14% better retrieval performance
- **Better recall**: Hybrid retrieval captures both semantic and exact matches
- **Reduced latency**: Semantic caching for common queries
- **Unified experience**: Single interface for all search needs
- **ADHD-optimized**: Faster, more accurate results reduce cognitive load

### Negative
- **Implementation complexity**: Multi-phase migration with potential rollback needs
- **Cost increase**: VoyageAI embeddings (~$0.18/1M tokens) + reranking (~$0.05/1M tokens)
- **External dependencies**: Reliance on VoyageAI API availability
- **Performance monitoring**: Need comprehensive observability for hybrid system

### Risks & Mitigations
- **Model drift**: Monitor via automated evaluation, maintain OpenAI fallback
- **Cost overruns**: Budget limits, selective reranking, caching optimization
- **Cache staleness**: TTL + invalidation on code/doc updates
- **Vendor lock-in**: Multi-provider support (VoyageAI, OpenAI, Nomic)

## Implementation Plan

### Phase 1: Foundation (Now)
- Switch Claude-Context to VoyageAI code-3 embeddings
- Verify hybrid search configuration works
- Implement basic reranking pipeline

### Phase 2: DocRAG Deployment (1-2 months)
- Deploy DocRAG MCP with VoyageAI context-3
- Build hybrid search with BM25 sidecar (OpenSearch/Milvus-sparse)
- Enable reranking with Voyage rerank-2.5

### Phase 3: Unification (3-6 months)
- Merge code/docs indices into unified Milvus collections
- Implement semantic caching layer
- Migrate ConPort to scalable storage
- Retire duplicate retrieval systems

### Rollback Strategy
- Environment variable toggles for embedder selection
- Dual-read capability during transition
- Automated fallback to OpenAI on VoyageAI failures

## Evaluation Criteria

### Performance Metrics
- **Accuracy**: nDCG@10, MRR improvements vs baseline
- **Latency**: p95 <200ms code search, <1200ms doc search with rerank
- **Cost**: Monthly embedding/rerank API spend within budget

### Success Indicators
- 12%+ improvement in search accuracy metrics
- <500ms average query response time
- >90% cache hit rate on repeated queries
- Positive developer feedback on search relevance

## Alternatives Considered

### Alternative 1: Continue with OpenAI embeddings
- **Pros**: No migration complexity, established reliability
- **Cons**: 12-14% lower accuracy, no domain specialization

### Alternative 2: Self-hosted embeddings (Nomic, CodeXEmbed)
- **Pros**: No vendor lock-in, potentially lower long-term costs
- **Cons**: Infrastructure complexity, model management overhead

### Alternative 3: Single retrieval method (dense only)
- **Pros**: Simpler implementation, lower complexity
- **Cons**: Poor recall for exact matches, terminology misses

## References

- [VoyageAI Code-3 Performance](https://blog.voyageai.com/2024/12/04/voyage-code-3.html)
- [VoyageAI Context-3 Results](https://blog.voyageai.com/2025/07/23/voyage-context-3.html)
- [Hybrid Search with RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)
- [RAG Search Architecture Docs](../04-explanation/architecture/rag-search-architecture.md)

---

**Decision made by**: Architecture Team
**Stakeholders consulted**: Development Team, DevEx Team
**Next review**: 2025-12-24 (3 months)