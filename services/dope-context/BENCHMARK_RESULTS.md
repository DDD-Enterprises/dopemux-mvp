# dope-context Performance Benchmark Results

**Date**: 2025-10-03  
**Collection**: dopemux_source  
**Indexed**: 133 chunks from 30 dopemux Python files  
**Cost**: $0.0577 for full indexing  

## Search Performance

### By Profile

| Profile | Min | Avg | Max | Results | Status |
|---------|-----|-----|-----|---------|--------|
| **Implementation** | 30.4ms | 35.8ms | 47.8ms | 100 | ✅ PASS |
| **Debugging** | 17.9ms | 18.3ms | 18.8ms | 50 | ✅ PASS |
| **Exploration** | 36.1ms | 37.0ms | 39.0ms | 133 | ✅ PASS |

### Overall Metrics

```
Average Latency:  30.3ms  (16x faster than 500ms target)
P50 Latency:      33.3ms
P95 Latency:      47.8ms  (10x faster than 500ms target)
Target:           <500ms  → ✅ PASS
```

## Performance vs Targets

| Metric | Target | Actual | Ratio | Status |
|--------|--------|--------|-------|--------|
| Search P95 | 500ms | 47.8ms | **10.5x faster** | ✅ |
| Search Avg | 500ms | 30.3ms | **16.5x faster** | ✅ |
| Collection | green | green | ✅ | ✅ |

## Tuning Recommendations

### Current State: EXCELLENT ✅

**No immediate tuning needed** - performance exceeds targets significantly.

### Optional Optimizations (if needed later):

**1. HNSW Parameters** (config/defaults.yaml:34-37)
```yaml
Current:
  m: 16              # Edges per node
  ef_construct: 200  # Build quality
  ef: 150            # Search quality

If search gets slower with more data:
  ef: 100  # Reduce from 150 (faster, slightly lower recall)
```

**2. Search Profiles** (dense_search.py:39-73)
```python
Current top_k values:
  implementation: 100  # Could reduce to 50 for faster
  debugging: 50        # Optimal
  exploration: 200     # Could reduce to 100
```

**3. Reranking** (defaults.yaml:92-101)
```yaml
Currently enabled: true
If latency becomes critical:
  enabled: false  # Saves ~200-500ms, slight quality drop
```

## Resource Usage

```
Qdrant Memory: Minimal (133 vectors)
Disk Space: ~10MB for collection
API Costs: $0.0577 for 30 files
```

## Conclusion

**Status**: Production-ready, no tuning required  
**Performance**: Exceptional (10-16x faster than targets)  
**Recommendation**: Deploy as-is, monitor at scale
