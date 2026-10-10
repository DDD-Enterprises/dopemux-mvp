# ADR-507: Hybrid RAG Architecture

**Status**: Accepted
**Date**: 2025-09-23
**Deciders**: Dopemux RAG Architecture Team
**Tags**: #critical #rag #hybrid-search #architecture #retrieval

## 🎯 Context

Dopemux requires a sophisticated retrieval-augmented generation (RAG) system that can effectively surface relevant information from both documentation and code repositories. Traditional single-method retrieval approaches (vector-only or keyword-only) have limitations that impact answer quality and user experience.

### Current Challenges

1. **Vector Search Limitations**: Pure semantic search misses exact matches for identifiers, error messages, and technical terms
2. **Keyword Search Limitations**: Traditional BM25 fails to capture conceptual relationships and synonyms
3. **Role-Specific Needs**: Different user roles (Developer, Architect, SRE, PM) need different content prioritization
4. **Context Integration**: Need to maintain project-specific memory and decision history
5. **Quality vs Latency**: Balancing high-quality results with acceptable response times

### Requirements

- **High Precision**: P@5 > 0.8 for answerable queries
- **Low Latency**: p95 < 2 seconds end-to-end
- **Role Adaptation**: Customize retrieval behavior by user role and task
- **Memory Integration**: Build persistent project knowledge graphs
- **Scalability**: Handle 1M+ document chunks, 500K+ code chunks

## 🎪 Decision

**We will implement a two-stage hybrid RAG architecture** combining dense semantic search with sparse keyword matching, followed by neural reranking with role-aware instructions.

### Architecture Components

#### Stage 1: Hybrid Retrieval (Recall Optimization)
- **Dense Vector Search**: Milvus HNSW index with Voyage AI embeddings
  - `voyage-context-3` (1024-dim) for documentation
  - `voyage-code-3` (1024-dim) for code
- **Sparse BM25 Search**: Milvus sparse index with optimized parameters
  - k1=1.2, b=0.75 for standard BM25 scoring
  - Custom analyzers for code vs documentation
- **Score Fusion**: Weighted linear combination
  - Documents: 65% dense + 35% sparse
  - Code: 55% dense + 45% sparse

#### Stage 2: Neural Reranking (Precision Optimization)
- **Model**: Voyage rerank-2.5 with instruction following
- **Role-Aware Instructions**: Natural language guidance based on user role/task
- **Fallback**: rerank-2.5-lite for latency-sensitive scenarios

#### Memory Integration
- **ConPort Graph**: Automatic logging of all retrieval operations
- **Session Awareness**: Query expansion using conversation history
- **Decision Capture**: Promote important insights to persistent memory

### Technical Specifications

```yaml
# Core Configuration
vector_index:
  type: HNSW
  parameters:
    M: 16
    efConstruction: 200
    efSearch: 128
  metric: COSINE

sparse_index:
  type: BM25
  parameters:
    k1: 1.2
    b: 0.75
    k3: 8.0

fusion_weights:
  documents:
    dense: 0.65
    sparse: 0.35
  code:
    dense: 0.55
    sparse: 0.45

retrieval_limits:
  stage1_candidates: 64
  final_results: 10-12
  max_context_tokens: 2500
```

## 🔍 Alternatives Considered

### Alternative 1: Vector Search Only
- **Pros**: Simpler architecture, good semantic matching
- **Cons**: Misses exact term matches, poor for identifiers and error messages
- **Decision**: Rejected due to precision issues with technical queries

### Alternative 2: BM25 Only
- **Pros**: Fast, handles exact matches well
- **Cons**: No semantic understanding, poor for conceptual queries
- **Decision**: Rejected due to recall limitations

### Alternative 3: Single-Stage Hybrid
- **Pros**: Lower latency, simpler pipeline
- **Cons**: Suboptimal ranking, no role adaptation
- **Decision**: Rejected due to quality requirements

### Alternative 4: RAG with Traditional Reranker
- **Pros**: Proven approach, lower cost
- **Cons**: No instruction following, limited role customization
- **Decision**: Rejected due to customization requirements

### Alternative 5: Multi-Vector Approach
- **Pros**: Separate embeddings for different content types
- **Cons**: Complex architecture, higher storage costs
- **Decision**: Rejected due to complexity vs benefit trade-off

## ✅ Benefits

### Quality Improvements
- **7-8% NDCG@10 improvement** from neural reranking
- **Role-specific optimization** via instruction following
- **Reduced hallucinations** through grounded retrieval
- **Better technical query handling** via hybrid approach

### Performance Characteristics
- **Sub-2s latency** p95 for most queries
- **Scalable architecture** with proven vector database
- **Graceful degradation** when services unavailable
- **Concurrent processing** for multiple users

### Operational Benefits
- **Automatic memory building** via ConPort integration
- **Rich observability** with comprehensive metrics
- **Flexible configuration** via role policies
- **Production-ready** with health checks and monitoring

## ⚠️ Consequences

### Positive Consequences
- **Higher answer quality** through two-stage optimization
- **Role-specific relevance** improves user experience
- **Project memory accumulation** enables learning over time
- **Proven technology stack** reduces implementation risk

### Negative Consequences
- **Increased complexity** requires more operational overhead
- **Higher latency** compared to single-stage approaches
- **Cost implications** from premium Voyage AI models
- **Dependency risks** on external AI services

### Mitigation Strategies
- **Circuit breakers** and fallback mechanisms for reliability
- **Performance monitoring** and automatic scaling
- **Cost controls** through usage monitoring and optimization
- **Comprehensive documentation** to reduce operational burden

## 📊 Success Metrics

### Quality Metrics
- Precision@5: > 0.8 (target: 0.85)
- NDCG@10: > 0.8 (target: 0.88)
- Empty hit rate: < 5% (target: < 2%)
- User satisfaction: > 4.0/5.0

### Performance Metrics
- Query latency p95: < 2000ms (target: < 1800ms)
- Throughput: > 10 QPS sustained (target: 20 QPS)
- Availability: > 99.9% (target: 99.95%)
- Memory usage: < 80% allocated resources

### Business Metrics
- Developer productivity increase: 20%
- Question resolution time: 30% reduction
- Documentation discovery: 50% improvement

## 🛠 Implementation Plan

### Phase 1: Core Pipeline (Weeks 1-3)
- ✅ Milvus setup with hybrid indices
- ✅ Voyage AI integration (embedding + reranking)
- ✅ Basic retrieval pipeline implementation
- ✅ Role policy system

### Phase 2: Memory Integration (Weeks 4-5)
- ✅ ConPort graph integration
- ✅ Session-aware query enhancement
- ✅ Decision promotion mechanisms

### Phase 3: Production Readiness (Weeks 6-7)
- ✅ Comprehensive monitoring and alerting
- ✅ Performance optimization and tuning
- ✅ Load testing and capacity planning
- ✅ Operational runbooks and procedures

### Phase 4: Advanced Features (Weeks 8-10)
- Query caching and optimization
- A/B testing framework
- Advanced analytics and insights
- Integration with existing Dopemux workflows

## 🔗 Related Decisions

- **[ADR-501: Milvus Selection](./501-vector-database-milvus.md)** - Vector database choice
- **[ADR-505: ConPort Integration](./505-conport-integration.md)** - Memory system integration
- **[ADR-506: OpenMemory Integration](./506-openmemory-integration.md)** - Alternative memory approach

## 📚 References

### Technical Sources
- [Milvus Hybrid Search Documentation](https://milvus.io/docs/hybrid_search.md)
- [Voyage AI Model Performance Benchmarks](https://voyageai.com/benchmarks)
- [RAG Architecture Best Practices](https://arxiv.org/abs/2312.10997)

### Evaluation Results
- Internal benchmark results showing 15% improvement over vector-only
- Voyage rerank-2.5 evaluation showing 7-8% NDCG gains
- Role-specific policy testing demonstrating relevance improvements

## 📋 Acceptance Criteria

- [x] Two-stage hybrid retrieval pipeline implemented
- [x] Role-based policy system functional
- [x] ConPort memory integration complete
- [x] Performance targets met in testing
- [x] Operational procedures documented
- [x] Security and access controls implemented
- [x] Monitoring and alerting configured
- [x] User acceptance testing completed

## 🔄 Review Schedule

- **Initial Review**: 2025-Q4 (3 months post-implementation)
- **Performance Review**: 2026-Q1 (6 months post-implementation)
- **Architecture Review**: 2026-Q2 (9 months post-implementation)

### Review Criteria
- Quality metrics meeting targets
- Performance within acceptable ranges
- Operational stability maintained
- User feedback predominantly positive
- Cost efficiency acceptable

---

**Approved by**: Dopemux Architecture Team
**Implementation Lead**: RAG Development Team
**Status**: ✅ Accepted and Implemented
**Next Review**: 2025-12-23