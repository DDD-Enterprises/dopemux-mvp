# Synergy C: Code Graph + Semantic Search Enrichment

**Status**: Design Complete, Ready for Implementation
**Effort**: 2-3 days
**Impact**: MEDIUM (better code understanding for LLM)

---

## Problem

**dope-context** finds code semantically but lacks relationship context:
- Finds functions by semantic similarity
- Doesn't show who calls this function
- Doesn't show what this function calls
- Misses impact analysis clues

**Serena v2** has rich code graph but no semantic search:
- Tracks function calls, imports, hierarchies
- Can query "find all callers" efficiently
- PostgreSQL graph storage
- But requires knowing exact symbol names

**Gap**: Semantic search results lack relationship intelligence

---

## Solution: Graph-Enriched Search Results

### Architecture

```
User Query: "authentication middleware"
         ↓
┌────────────────────────────────────┐
│ dope-context Semantic Search       │
│  (finds relevant code chunks)      │
└────────────┬───────────────────────┘
             ↓
     Top 10 Results
             ↓
┌────────────────────────────────────┐
│ Graph Enrichment Layer (NEW)       │
│  For each result:                  │
│    - Query Serena code graph       │
│    - Get relationship metadata     │
│    - Enrich result object          │
└────────────┬───────────────────────┘
             ↓
Enhanced Results with Relationships
```

### Enhanced Result Format

**Before** (current):
```json
{
  "file_path": "src/auth/middleware.py",
  "function_name": "authenticate_request",
  "code": "async def authenticate_request...",
  "complexity": 0.42,
  "relevance_score": 0.87
}
```

**After** (enriched):
```json
{
  "file_path": "src/auth/middleware.py",
  "function_name": "authenticate_request",
  "code": "async def authenticate_request...",
  "complexity": 0.42,
  "relevance_score": 0.87,
  "relationships": {
    "called_by": 12,
    "calls": 5,
    "imported_by": 8,
    "imports": 3,
    "top_callers": [
      "src/api/routes.py:login_endpoint",
      "src/api/routes.py:refresh_endpoint",
      "src/middleware/auth_chain.py:auth_middleware"
    ]
  },
  "impact_analysis": {
    "change_risk": "medium",
    "affected_files": 8,
    "test_coverage": "87%"
  }
}
```

### Implementation

**File**: `services/dope-context/src/enrichment/graph_enrichment.py` (NEW)

```python
class GraphEnrichment:
    """Enrich semantic search results with code graph data."""

    def __init__(self, serena_client):
        self.serena = serena_client
        self.cache = {}  # Cache graph data

    async def enrich_results(
        self,
        search_results: List[Dict],
        max_results: int = 10
    ) -> List[Dict]:
        """
        Enrich search results with relationship data.

        Args:
            search_results: Results from semantic search
            max_results: Only enrich top N (avoid excessive calls)

        Returns:
            Enhanced results with relationship metadata
        """
        enriched = []

        for result in search_results[:max_results]:
            # Get code graph from Serena
            graph_data = await self._get_graph_data(
                result["file_path"],
                result.get("function_name", "")
            )

            # Enrich result
            result["relationships"] = {
                "called_by": len(graph_data.get("callers", [])),
                "calls": len(graph_data.get("callees", [])),
                "imported_by": len(graph_data.get("importers", [])),
                "imports": len(graph_data.get("imports", [])),
                "top_callers": graph_data.get("callers", [])[:3],
            }

            # Add impact analysis
            total_affected = (
                len(graph_data.get("callers", [])) +
                len(graph_data.get("importers", []))
            )

            result["impact_analysis"] = {
                "change_risk": "high" if total_affected > 20 else
                               "medium" if total_affected > 5 else "low",
                "affected_files": total_affected,
            }

            enriched.append(result)

        return enriched

    async def _get_graph_data(self, file_path: str, symbol: str) -> Dict:
        """Get graph data from Serena (with caching)."""
        cache_key = f"{file_path}:{symbol}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query Serena MCP
        graph_data = await self.serena.get_code_graph(file_path, symbol)

        # Cache for 5 minutes
        self.cache[cache_key] = graph_data

        return graph_data
```

**MCP Tool Enhancement** (`src/mcp/server.py`):
```python
@mcp.tool()
async def search_code_with_graph(
    query: str,
    top_k: int = 10,
    include_relationships: bool = True,
    ...
) -> List[Dict]:
    """
    Search code with optional graph enrichment.

    New parameter: include_relationships (default True)
    """
    # Standard semantic search
    results = await search_code(query, top_k, ...)

    # Enrich with graph data if requested
    if include_relationships:
        enricher = GraphEnrichment(serena_client)
        results = await enricher.enrich_results(results, max_results=top_k)

    return results
```

---

## Benefits for LLM (Me!)

When I search your codebase, enriched results help me:

1. **Understand Impact**: "This function is called by 12 places - changes will ripple"
2. **Find Related Code**: "Top callers are in routes.py - check those too"
3. **Assess Risk**: "High change risk - suggest comprehensive testing"
4. **Navigate Better**: "This imports 3 modules - might need to check those"
5. **Give Better Advice**: More context = better recommendations

---

## Implementation Checklist

### Phase 1: Core Enrichment (1 day)
- [ ] Create `services/dope-context/src/enrichment/` module
- [ ] Implement `GraphEnrichment` class
- [ ] Add Serena client integration
- [ ] Implement caching (5-minute TTL)
- [ ] Write unit tests

### Phase 2: MCP Integration (0.5 day)
- [ ] Add `search_code_with_graph()` tool
- [ ] Add `include_relationships` parameter to existing `search_code()`
- [ ] Update search_all() to support enrichment
- [ ] Test with real queries

### Phase 3: Serena MCP Client (0.5 day)
- [ ] Add `get_code_graph()` method to Serena MCP
- [ ] Query PostgreSQL code graph efficiently
- [ ] Return relationship metadata
- [ ] Add performance indexes if needed

### Phase 4: Optimization (1 day)
- [ ] Batch graph queries (multiple results at once)
- [ ] Parallel enrichment (async gather)
- [ ] Smart caching strategy
- [ ] Performance benchmarking

**Total**: 3 days

---

## Performance Considerations

**Latency Addition**:
- Graph query: ~10-20ms per result
- For 10 results: ~100-200ms total (parallel queries)
- **Total search time**: 2s (current) + 0.2s (enrichment) = 2.2s

**Mitigation**:
- Parallel graph queries (asyncio.gather)
- LRU cache (avoid redundant queries)
- Only enrich top N results (default: 10)
- Optional feature (can disable)

**Memory**:
- Cache size: ~10MB (1000 entries)
- Graph data per result: ~1KB
- Total overhead: Minimal

---

## Testing Strategy

1. **Accuracy**: Verify relationship counts match reality
2. **Performance**: Measure added latency (<250ms target)
3. **Cache**: Validate cache hits >70%
4. **Integration**: Test across different code patterns

---

## Success Metrics

- [ ] Enrichment adds <250ms latency
- [ ] Cache hit rate >70%
- [ ] Relationship data accuracy >95%
- [ ] LLM finds related code 50% faster (subjective)
