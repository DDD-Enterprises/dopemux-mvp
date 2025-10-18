---
id: 04-CONPORT-SEARCH-DELEGATION
title: 04 Conport Search Delegation
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Implementation Plan: ConPort Search Delegation

**Task ID**: IP-004
**Priority**: 🟡 HIGH VALUE (Quick Win!)
**Duration**: 1 day (2 focus blocks @ 25min each)
**Complexity**: 0.35 (LOW-MEDIUM)
**Dependencies**: None
**Risk Level**: LOW (simple removal)

---

## Executive Summary

**Problem**: ConPort implements inferior semantic search (384-dim embeddings) while dope-context has superior search (1024-dim Voyage embeddings + BM25 hybrid + neural reranking).

**Solution**: Remove ConPort's semantic search entirely, delegate ALL semantic queries to dope-context MCP.

**Impact**:
- ✅ +35-67% search quality improvement (Anthropic benchmark)
- ✅ Eliminates code duplication (~500 lines removed)
- ✅ Removes ConPort's dependency on sentence-transformers
- ✅ Reduces ConPort container size by ~200MB
- ✅ Single source of truth for semantic search

**Success Criteria**:
- [ ] ConPort semantic_search_conport() removed or delegated
- [ ] ConPort keeps PostgreSQL FTS for keyword search
- [ ] All semantic queries route to dope-context
- [ ] Search quality improves measurably
- [ ] Zero functional regressions

---

## Current State Analysis

### ConPort's Inferior Search (services/conport/)

**Embedding Service** (`src/context_portal_mcp/core/embedding_service.py`):
```python
# INFERIOR 384-dimensional embeddings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim, baseline quality
embedding = model.encode(text)  # Returns 384-dim vector
```

**Vector Store** (`src/context_portal_mcp/v2/vector_store.py`):
```python
# Simple cosine similarity search - no hybrid, no reranking
from qdrant_client import AsyncQdrantClient

client = AsyncQdrantClient(url="http://localhost:6333")

# Simple search (no BM25, no multi-vector, no reranking)
results = await client.search(
    collection_name="conport_knowledge",
    query_vector=query_embedding,  # 384-dim
    limit=top_k
)
```

**Search Quality**: Baseline (documented as 35-67% worse than Voyage)

### Dope-Context's Superior Search (services/dope-context/)

**Embedding Service** (`src/embeddings/voyage_embedder.py`):
```python
# SUPERIOR 1024-dimensional embeddings
import voyageai

voyage_client = voyageai.Client()
embedding = voyage_client.embed(
    texts=[text],
    model="voyage-code-3"  # 1024-dim, best-in-class for code
)
```

**Hybrid Search** (`src/search/hybrid_search.py`):
```python
# Advanced hybrid search pipeline:
# 1. Multi-vector dense search (content + title + breadcrumb)
# 2. BM25 sparse search (keyword matching)
# 3. RRF fusion (combines dense + sparse)
# 4. Voyage reranking (top 50 → top 10 with rerank-2.5)
# 5. Context generation (gpt-5-mini descriptions)

results = await hybrid_search(
    query=query,
    top_k=50,
    dense_weight=0.7,
    sparse_weight=0.3
)

reranked = await voyage_reranker.rerank(results, query)
return reranked[:10]
```

**Search Quality**: Best-in-class (35-67% better than baseline)

---

## Implementation Plan

### Step 1: Audit ConPort Semantic Search Usage (15 min)

**Find all calls to semantic_search_conport**:
```bash
# Search codebase
grep -r "semantic_search_conport" services/ --include="*.py"

# Expected locations:
# - MCP handler: mcp_handlers.py
# - Tests: test_semantic_search.py
# - Maybe: CLI commands
```

**Document current behavior**:
```bash
# Test current ConPort search
python -c "
from context_portal_mcp import ConPortMCP
mcp = ConPortMCP()
results = mcp.semantic_search_conport('ADHD energy matching')
print(f'Found {len(results)} results')
print(f'Top score: {results[0].score if results else 0}')
"
```

---

### Step 2: Implement Delegation Pattern (20 min)

**Location**: `services/conport/src/context_portal_mcp/handlers/mcp_handlers.py`

**Before** (Current Implementation):
```python
async def handle_semantic_search_conport(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search ConPort data using semantic search.

    PROBLEM: Uses inferior 384-dim embeddings with simple cosine search.
    """
    query_text = params['query_text']
    top_k = params.get('top_k', 5)

    # Generate query embedding (384-dim, low quality)
    query_embedding = await embedding_service.get_embedding(query_text)

    # Simple vector search (no hybrid, no reranking)
    results = await vector_store_service.search(
        workspace_id=params['workspace_id'],
        query_vector=query_embedding,
        top_k=top_k
    )

    return {"results": results}
```

**After** (Delegated Implementation):
```python
async def handle_semantic_search_conport(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search ConPort data using dope-context's superior semantic search.

    SOLUTION: Delegate to dope-context for 1024-dim Voyage embeddings
    + BM25 hybrid + neural reranking.
    """
    query_text = params['query_text']
    top_k = params.get('top_k', 5)
    workspace_id = params['workspace_id']

    # Option A: HTTP call to dope-context MCP (if exposed via HTTP)
    # Option B: Import dope-context search function (shared library)
    # Option C: CLI call to dope-context MCP

    # RECOMMENDED: Option B (shared library - fastest, no network overhead)
    from dope_context.search import unified_search

    # Search ConPort's indexed data through dope-context
    results = await unified_search(
        query=query_text,
        top_k=top_k,
        workspace_path=workspace_id,
        collections=["conport_decisions", "conport_patterns"],  # ConPort-specific collections
        use_reranking=True
    )

    # Filter to ConPort data only
    conport_results = [
        r for r in results
        if r.get('collection') in ['conport_decisions', 'conport_patterns']
    ]

    return {"results": conport_results}
```

**Alternative: Keep Wrapper, Change Implementation**:
```python
async def handle_semantic_search_conport(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search ConPort data - now delegating to dope-context.

    Preserves API compatibility while using superior search.
    """
    # Check feature flag for gradual rollout
    use_dope_context = await feature_flags.is_enabled(
        "conport_delegate_search",
        "conport"
    )

    if use_dope_context:
        # NEW: Delegate to dope-context
        results = await _search_via_dope_context(params)
    else:
        # OLD: Use ConPort's inferior search (backward compatibility)
        results = await _search_via_conport(params)

    return {"results": results}

async def _search_via_dope_context(params: Dict[str, Any]) -> List[Dict]:
    """Use dope-context's superior search."""
    from dope_context.search import unified_search

    results = await unified_search(
        query=params['query_text'],
        top_k=params.get('top_k', 5),
        workspace_path=params['workspace_id'],
        collections=["conport_decisions", "conport_patterns"]
    )

    return results

async def _search_via_conport(params: Dict[str, Any]) -> List[Dict]:
    """Legacy ConPort search (inferior, for rollback)."""
    # Existing 384-dim embedding search code
    # Keep for backward compatibility during migration
    pass
```

---

### Step 3: Remove ConPort Vector Dependencies (15 min)

**Tasks**:
1. Remove sentence-transformers dependency
2. Remove ConPort's Qdrant client (dope-context owns it now)
3. Update requirements.txt
4. Rebuild container

**Update Requirements** (`services/conport/requirements.txt`):
```diff
# BEFORE:
fastmcp>=0.2.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
qdrant-client>=1.7.0
-sentence-transformers>=2.2.0  # REMOVE (384-dim embeddings)
pydantic>=2.0.0

# AFTER:
fastmcp>=0.2.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
+dope-context-client>=0.1.0     # ADD (shared library for search delegation)
pydantic>=2.0.0
```

**Remove Embedding Service** (`services/conport/src/context_portal_mcp/core/embedding_service.py`):
```bash
# Option A: Delete file entirely
rm services/conport/src/context_portal_mcp/core/embedding_service.py

# Option B: Keep file, replace with delegation stub
# (Safer for gradual migration)
```

**Update Container** (`services/conport/Dockerfile`):
```dockerfile
# BEFORE: Heavy container with ML models
FROM python:3.11-slim
RUN pip install sentence-transformers  # Downloads 200MB+ model
COPY . .
# Final size: ~1.2GB

# AFTER: Lighter container
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt  # No ML dependencies
COPY . .
# Final size: ~500MB (-58% reduction!)
```

**Deliverables**:
- [ ] sentence-transformers removed from requirements
- [ ] Qdrant client removed from ConPort
- [ ] Container size reduced by ~200-500MB
- [ ] Build time faster (no ML model downloads)

---

### Step 4: Testing & Validation (10 min)

**Test Search Quality Improvement**:
```python
# tests/test_search_delegation.py
import pytest

@pytest.mark.asyncio
async def test_search_quality_improvement():
    """
    Verify dope-context delegation improves search quality.
    """
    query = "ADHD energy matching task routing algorithms"

    # Search via new delegation
    from context_portal_mcp import ConPortMCP
    conport = ConPortMCP()
    results_new = await conport.semantic_search_conport(query, top_k=5)

    # Compare to old method (if feature flag allows)
    # results_old = await conport._search_via_conport(query, top_k=5)

    # Quality assertions
    assert len(results_new) > 0, "Returns results"
    assert all(r['score'] > 0.5 for r in results_new), "High relevance scores"

    # Verify using dope-context (check for Voyage metadata)
    assert any('voyage' in str(r).lower() for r in results_new), "Using Voyage embeddings"

    print(f"✅ Search quality validated!")
    print(f"   Top result score: {results_new[0]['score']:.3f}")
```

**Benchmark Search Performance**:
```python
# tests/benchmark_search.py
import time

async def benchmark_search_delegation():
    """Compare search latency: old vs new."""

    query = "PostgreSQL connection pooling patterns"

    # Time new delegation approach
    start = time.time()
    results_new = await conport.semantic_search_conport(query)
    latency_new = time.time() - start

    print(f"New (dope-context delegation): {latency_new*1000:.1f}ms")
    print(f"✅ Search latency acceptable!")

    # Quality check
    print(f"Results: {len(results_new)}")
    print(f"Top score: {results_new[0]['score']:.3f}")
```

**Functional Tests**:
```bash
# Verify all ConPort MCP tools still work
pytest tests/conport/test_mcp_handlers.py -v

# Specifically test semantic search
pytest tests/conport/test_semantic_search.py::test_semantic_search_decisions -v
pytest tests/conport/test_semantic_search.py::test_semantic_search_patterns -v

# Should pass with HIGHER quality results
```

**Deliverables**:
- [ ] Search quality tests passing
- [ ] Performance benchmarks acceptable (<100ms)
- [ ] All ConPort MCP tools operational
- [ ] Improvement documented (before/after comparison)

---

## Migration Strategy

### Approach: Feature Flag Rollout

**Phase 1: Preparation (Hours 1-2)**
- Add dope-context client library to ConPort
- Implement delegation code with feature flag
- Test with flag OFF (verify no regressions)

**Phase 2: Beta Test (Hours 3-4)**
- Enable flag for one user
- Monitor search quality and latency
- Collect feedback

**Phase 3: Full Rollout (Hours 5-6)**
- Enable flag globally
- Monitor for 1 hour
- If successful, remove old embedding code

**Phase 4: Cleanup (Hours 7-8)**
- Remove sentence-transformers dependency
- Delete embedding_service.py
- Remove Qdrant client from ConPort
- Rebuild container
- Update documentation

---

## Code Changes

### File: `services/conport/src/context_portal_mcp/handlers/mcp_handlers.py`

**Lines to Modify**: ~112-140 (semantic_search_conport handler)

**Before** (Current - ~150 lines):
```python
async def handle_semantic_search_conport(params: Dict[str, Any]) -> Dict[str, Any]:
    workspace_id = params['workspace_id']
    query_text = params['query_text']
    top_k = params.get('top_k', 5)

    # Get embedding (384-dim, inferior)
    query_embedding = await embedding_service.get_embedding(query_text)

    # Search ConPort's Qdrant collection
    vector_results = await vector_store_service.search(
        workspace_id=workspace_id,
        query_vector=query_embedding,
        top_k=top_k
    )

    # Hydrate results from SQLite
    results = []
    for hit in vector_results:
        item_type = hit.payload['item_type']
        item_id = hit.payload['item_id']

        if item_type == 'decision':
            decision = db.get_decision_by_id(item_id)
            results.append({
                "type": "decision",
                "id": decision.id,
                "summary": decision.summary,
                "score": hit.score
            })
        elif item_type == 'system_pattern':
            pattern = db.get_system_pattern_by_id(item_id)
            results.append({
                "type": "system_pattern",
                "id": pattern.id,
                "name": pattern.name,
                "score": hit.score
            })

    return {"results": results}
```

**After** (Delegated - ~50 lines, 67% reduction):
```python
async def handle_semantic_search_conport(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search ConPort data using dope-context's superior semantic search.

    Delegates to dope-context for 1024-dim Voyage embeddings + BM25 hybrid
    + neural reranking (35-67% better quality than old 384-dim search).
    """
    workspace_id = params['workspace_id']
    query_text = params['query_text']
    top_k = params.get('top_k', 5)

    # Import dope-context search (shared library)
    from dope_context.search import search_custom_collection

    # Search ConPort-specific collections via dope-context
    results = await search_custom_collection(
        query=query_text,
        collection_name="conport_knowledge",  # ConPort's Qdrant collection
        top_k=top_k,
        workspace_path=workspace_id,
        use_hybrid=True,      # Enable BM25 hybrid search
        use_reranking=True    # Enable Voyage reranking
    )

    # Transform dope-context results to ConPort format
    conport_results = []
    for hit in results:
        item_type = hit['metadata']['item_type']
        item_id = hit['metadata']['item_id']

        # Hydrate from SQLite (same as before)
        if item_type == 'decision':
            decision = db.get_decision_by_id(item_id)
            conport_results.append({
                "type": "decision",
                "id": decision.id,
                "summary": decision.summary,
                "score": hit['score'],  # Higher quality score!
                "context": hit.get('context', '')  # NEW: gpt-5-mini context
            })
        elif item_type == 'system_pattern':
            pattern = db.get_system_pattern_by_id(item_id)
            conport_results.append({
                "type": "system_pattern",
                "id": pattern.id,
                "name": pattern.name,
                "score": hit['score'],
                "context": hit.get('context', '')
            })

    return {"results": conport_results}
```

**Code Reduction**: 150 lines → 50 lines (67% reduction)

---

### Step 5: Remove Embedding Infrastructure (20 min)

**Files to Delete**:
```bash
# Delete embedding service
rm services/conport/src/context_portal_mcp/core/embedding_service.py

# Delete vector store service (now owned by dope-context)
rm services/conport/src/context_portal_mcp/v2/vector_store.py

# Update imports
# Remove from __init__.py, mcp_handlers.py, etc.
```

**Keep PostgreSQL FTS** (keyword search):
```python
# Keep this for keyword-only search (complement to semantic)
async def handle_search_decisions_fts(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full-text search using PostgreSQL (keyword-based).

    This is DIFFERENT from semantic search - uses keyword matching.
    Keep this for exact phrase searches.
    """
    query_term = params['query_term']

    # Use PostgreSQL full-text search (fast, good for keywords)
    results = db.search_decisions_fts(query_term)

    return {"results": results}
```

**Why Keep FTS?**
- Semantic search: "find similar decisions" (meaning-based)
- FTS search: "find exact phrase 'Redis pub/sub'" (keyword-based)
- Both useful for different use cases
- FTS has zero external dependencies

---

## Dope-Context Collection Setup

### Index ConPort Data in Dope-Context

**Current Problem**: ConPort data in separate Qdrant collection, not indexed by dope-context

**Solution**: Add ConPort data indexing to dope-context

**Create Indexing Script** (`scripts/index_conport_in_dope_context.py`):
```python
"""
Index ConPort decisions and patterns in dope-context for unified search.
"""
from dope_context.indexing import index_custom_data
from context_portal_mcp import ConPortMCP

async def index_conport_data():
    """Index all ConPort decisions and patterns."""
    conport = ConPortMCP()

    # Get all decisions
    decisions = conport.get_decisions(limit=None)  # Get all

    # Index each decision
    for decision in decisions:
        text = f"{decision.summary}\n\n{decision.rationale}\n\n{decision.implementation_details}"

        await index_custom_data(
            collection_name="conport_decisions",
            doc_id=str(decision.id),
            text=text,
            metadata={
                "item_type": "decision",
                "item_id": decision.id,
                "tags": decision.tags,
                "created_at": decision.created_at
            }
        )

    print(f"✅ Indexed {len(decisions)} decisions")

    # Get all patterns
    patterns = conport.get_system_patterns(limit=None)

    # Index each pattern
    for pattern in patterns:
        text = f"{pattern.name}\n\n{pattern.description}"

        await index_custom_data(
            collection_name="conport_patterns",
            doc_id=str(pattern.id),
            text=text,
            metadata={
                "item_type": "system_pattern",
                "item_id": pattern.id,
                "tags": pattern.tags,
                "created_at": pattern.created_at
            }
        )

    print(f"✅ Indexed {len(patterns)} patterns")

# Run on ConPort data changes (hook into log_decision, log_system_pattern)
```

**Add Auto-Indexing Hook** (services/conport/src/context_portal_mcp/handlers/mcp_handlers.py):
```python
async def handle_log_decision(params: Dict[str, Any]) -> Dict[str, Any]:
    # Existing decision logging code...
    decision_id = db.create_decision(...)

    # NEW: Auto-index in dope-context for semantic search
    from dope_context.indexing import index_custom_data

    await index_custom_data(
        collection_name="conport_decisions",
        doc_id=str(decision_id),
        text=f"{params['summary']}\n\n{params['rationale']}",
        metadata={
            "item_type": "decision",
            "item_id": decision_id,
            "tags": params.get('tags', [])
        }
    )

    return {"id": decision_id}
```

---

## Testing Strategy

### Unit Tests
```python
# tests/conport/test_search_delegation.py

@pytest.mark.asyncio
async def test_semantic_search_delegates_to_dope_context():
    """Verify semantic search uses dope-context."""
    results = await conport.semantic_search_conport(
        query="ADHD energy matching",
        top_k=5
    )

    # Verify using Voyage embeddings (check metadata)
    assert results[0].get('context'), "Has gpt-5-mini context"
    assert results[0]['score'] > 0.6, "High quality scores"

@pytest.mark.asyncio
async def test_fts_search_still_works():
    """Verify PostgreSQL FTS still functional."""
    results = await conport.search_decisions_fts(
        query_term="Redis pub/sub"
    )

    assert len(results) > 0, "FTS returns results"
    # FTS is keyword-based, different from semantic
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_search_quality_improvement():
    """
    Compare search quality before/after delegation.

    This test requires feature flag to switch between implementations.
    """
    query = "systematic task decomposition with dependency tracking"

    # Test with flag OFF (old 384-dim search)
    await feature_flags.disable("conport_delegate_search")
    results_old = await conport.semantic_search_conport(query, top_k=10)

    # Test with flag ON (new 1024-dim delegated search)
    await feature_flags.enable("conport_delegate_search")
    results_new = await conport.semantic_search_conport(query, top_k=10)

    # Compare top result scores
    score_old = results_old[0]['score'] if results_old else 0
    score_new = results_new[0]['score'] if results_new else 0

    # NEW should be better (35-67% improvement expected)
    improvement = (score_new - score_old) / score_old
    print(f"📈 Search quality improvement: {improvement:.1%}")

    assert improvement > 0.20, "At least 20% improvement"
```

### Performance Tests
```python
@pytest.mark.asyncio
async def test_search_latency_acceptable():
    """Verify delegation doesn't add excessive latency."""
    import time

    query = "ConPort knowledge graph relationships"

    start = time.time()
    results = await conport.semantic_search_conport(query, top_k=5)
    latency = time.time() - start

    assert latency < 0.5, "Search completes in <500ms"
    print(f"⚡ Search latency: {latency*1000:.1f}ms")
```

---

## Rollout Plan

### Hour 1-2: Preparation
- [ ] Add dope-context client library to ConPort
- [ ] Implement delegation code
- [ ] Add feature flag checks
- [ ] Test with flag OFF (verify no changes)

### Hour 3-4: Beta Test
- [ ] Enable flag for one workspace
- [ ] Run 20 test queries
- [ ] Compare quality scores
- [ ] Check latency benchmarks
- [ ] Collect any errors

### Hour 5-6: Full Rollout
- [ ] Enable flag globally
- [ ] Monitor ConPort MCP logs
- [ ] Run integration tests
- [ ] Verify all semantic searches working

### Hour 7-8: Cleanup
- [ ] Remove sentence-transformers dependency
- [ ] Delete embedding_service.py
- [ ] Delete vector_store.py
- [ ] Rebuild ConPort container
- [ ] Update documentation
- [ ] Remove feature flag code (optional)

---

## Rollback Procedure

**Immediate Rollback**:
```bash
# Disable feature flag
redis-cli SET "feature_flags:conport_delegate_search:global" "false"

# ConPort immediately reverts to old 384-dim search
# No code changes needed!
```

**Full Rollback** (if delegation code has bugs):
```bash
# Revert commits
git revert <commit-hash>

# Redeploy ConPort
docker-compose up -d --build conport

# Old embedding service still in git history, easily restored
```

---

## Success Metrics

**Quality Improvements**:
- [ ] Search relevance scores +35-67% (Anthropic benchmark)
- [ ] More accurate results for same queries
- [ ] Better handling of semantic similarity
- [ ] Contextual summaries for each result (gpt-5-mini)

**Operational Improvements**:
- [ ] ConPort container -200-500MB smaller
- [ ] Faster container builds (no ML model downloads)
- [ ] Code duplication -~500 lines
- [ ] Single source of truth for semantic search

**Performance**:
- [ ] Search latency <500ms (acceptable with network call)
- [ ] No regressions in ConPort MCP response times
- [ ] Caching reduces repeated query overhead

---

## Risk Assessment

**Risk 1: Latency Increase**
**Probability**: LOW
**Impact**: MEDIUM
**Mitigation**: Caching, async calls, monitor latency
**Acceptable**: <500ms for semantic search (quality worth it)

**Risk 2: Dope-Context Unavailable**
**Probability**: LOW
**Impact**: HIGH
**Mitigation**: Keep PostgreSQL FTS as fallback, feature flags allow instant revert

**Risk 3: Quality Regression**
**Probability**: VERY LOW
**Impact**: MEDIUM
**Mitigation**: Extensive testing, benchmark comparisons, gradual rollout

---

## Benefits Analysis

**Code Reduction**:
- Remove ~500 lines of embedding/vector code
- Remove sentence-transformers dependency (~200MB)
- Simpler ConPort codebase (focus on core competency)

**Quality Improvement**:
- 384-dim → 1024-dim embeddings (+35-67% quality)
- Simple cosine → Hybrid search with reranking
- No context → gpt-5-mini generated summaries

**Architectural Cleanliness**:
- Single Responsibility: ConPort does knowledge graph, dope-context does search
- DRY: Eliminate duplicate semantic search implementation
- Integration: Services coordinate through shared infrastructure

**ROI**: 🔥 EXTREME
- 1 day effort for 35-67% quality boost
- Simplifies codebase significantly
- Easy win with minimal risk

---

## Next Steps After Completion

1. **Monitor for 1 week**: Track search quality metrics
2. **Optimize**: Tune caching if needed
3. **Document**: Update ConPort docs to reference dope-context
4. **Celebrate**: Easy win with huge quality boost! 🎉

---

**Total Effort**: 1 day (2 focus blocks @ 25min each)
**Risk Level**: LOW (feature flags + fallbacks)
**Impact**: HIGH (quality improvement + code reduction)
**ROI**: 🔥 EXTREME (best effort/value ratio of all tasks!)
