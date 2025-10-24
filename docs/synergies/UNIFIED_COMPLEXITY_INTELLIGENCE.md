# Synergy A: Unified Complexity Intelligence

**Status**: Design Complete, Ready for Implementation
**Effort**: 2-3 days
**Impact**: HIGH (better accuracy + reduced computation)

---

## Problem

Three systems calculate code complexity independently:

1. **dope-context** (`src/preprocessing/code_chunker.py`):
   - Tree-sitter AST analysis
   - Nesting depth, cyclomatic complexity
   - Score: 0.0-1.0

2. **Serena v2** (`adhd_features.py`):
   - LSP symbol metadata
   - Line count, reference patterns
   - Score: 0.0-1.0

3. **ADHD Engine** (implicitly via cognitive load):
   - User-specific fatigue patterns
   - Historical completion rates
   - Adjustment multiplier

**Duplication**: Each system computes independently → wasted CPU + inconsistent scores

---

## Solution: Hybrid Complexity Scoring

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Complexity Coordinator (NEW)                            │
│                                                          │
│  get_unified_complexity(file_path, symbol, user_id)     │
│         ↓                ↓                ↓              │
│    ┌─────────┐    ┌──────────┐    ┌─────────────┐      │
│    │  AST    │    │   LSP    │    │    ADHD     │      │
│    │ (dope)  │    │ (Serena) │    │  (Engine)   │      │
│    └────┬────┘    └─────┬────┘    └──────┬──────┘      │
│         │               │                 │              │
│         └───────────────┼─────────────────┘              │
│                         ↓                                 │
│           Weighted Combination + Caching                 │
│                         ↓                                 │
│           Unified Score (0.0-1.0) + Metadata             │
└─────────────────────────────────────────────────────────┘
```

### Algorithm

```python
unified_score = (
    ast_complexity * 0.50 +      # Structural complexity (accurate)
    usage_complexity * 0.30 +     # How widely used (LSP)
    user_adjustment * 0.20        # Personal difficulty (ADHD)
)
```

**Components**:

1. **AST Complexity** (from dope-context):
   - Nesting depth
   - Cyclomatic complexity
   - Control flow
   - Weight: 50% (most objective)

2. **Usage Complexity** (from Serena LSP):
   - Reference count / 100
   - Caller count / 50
   - Import frequency
   - Weight: 30% (impact indicator)

3. **User Adjustment** (from ADHD Engine):
   - Historical completion rate for similar complexity
   - Fatigue multiplier
   - Energy-complexity match history
   - Weight: 20% (personalization)

### Implementation

**File**: `services/shared/complexity_coordinator.py` (NEW)

```python
class ComplexityCoordinator:
    def __init__(
        self,
        dope_context_client,
        serena_client,
        adhd_engine_client
    ):
        self.dope = dope_context_client
        self.serena = serena_client
        self.adhd = adhd_engine_client
        self.cache = {}  # LRU cache

    async def get_unified_complexity(
        self,
        file_path: str,
        symbol: str,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        # Check cache
        cache_key = f"{file_path}:{symbol}:{user_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 1. Get AST complexity from dope-context
        ast_data = await self.dope.get_chunk_complexity(file_path, symbol)
        ast_score = ast_data.get("complexity", 0.5)

        # 2. Get LSP usage data from Serena
        lsp_data = await self.serena.get_symbol_metadata(file_path, symbol)
        ref_count = lsp_data.get("references_count", 0)
        caller_count = lsp_data.get("callers_count", 0)
        usage_score = min(1.0, (ref_count / 100.0 + caller_count / 50.0) / 2)

        # 3. Get ADHD adjustment
        adhd_data = await self.adhd.get_complexity_adjustment(
            user_id, base_complexity=ast_score
        )
        user_multiplier = adhd_data.get("multiplier", 1.0)

        # 4. Calculate unified score
        unified = (
            ast_score * 0.50 +
            usage_score * 0.30
        ) * user_multiplier * 0.20

        result = {
            "unified_score": round(unified, 3),
            "components": {
                "ast_complexity": round(ast_score, 3),
                "usage_complexity": round(usage_score, 3),
                "user_multiplier": round(user_multiplier, 3),
            },
            "metadata": {
                "reference_count": ref_count,
                "caller_count": caller_count,
            }
        }

        # Cache result
        self.cache[cache_key] = result

        return result
```

### Integration Points

**dope-context Enhancement**:
```python
# search_code() returns results with unified complexity
results = await search_code("auth function")
# Each result now has:
# {
#   "file_path": "...",
#   "code": "...",
#   "complexity": 0.42,  # Unified score!
#   "complexity_breakdown": {...}
# }
```

**Serena v2 Enhancement**:
```python
# find_symbol() uses unified complexity for filtering
symbols = await find_symbol("authenticate")
# High complexity symbols flagged for ADHD users
```

**ADHD Engine Enhancement**:
```python
# Task assessment uses unified complexity
assessment = await assess_task(task_with_code_refs)
# More accurate cognitive load calculation
```

---

## Benefits

1. **Better Accuracy**: AST + LSP + user history = best score
2. **Reduced Computation**: Calculate once, use everywhere
3. **Consistent**: Same score across all systems
4. **Personalized**: Adapts to individual ADHD patterns
5. **Cached**: Avoid redundant calculations

---

## Implementation Plan

### Phase 1: Core Coordinator (1 day)
- [ ] Create `services/shared/complexity_coordinator.py`
- [ ] Implement hybrid scoring algorithm
- [ ] Add LRU cache (max 1000 entries)
- [ ] Write unit tests

### Phase 2: dope-context Integration (0.5 day)
- [ ] Add complexity_coordinator to search pipeline
- [ ] Enhance search results with unified scores
- [ ] Test with real codebase

### Phase 3: Serena Integration (0.5 day)
- [ ] Add complexity_coordinator to symbol tools
- [ ] Use unified scores in ADHD filtering
- [ ] Test find_symbol with complexity

### Phase 4: ADHD Engine Integration (1 day)
- [ ] Add complexity adjustment endpoint
- [ ] Track user-specific complexity patterns
- [ ] Test task assessment accuracy

**Total**: 3 days, HIGH impact

---

## Testing Strategy

1. **Accuracy Validation**: Compare unified scores vs individual scores
2. **Performance Benchmarking**: Measure cache hit rates and latency
3. **ADHD Effectiveness**: Test with real ADHD developers
4. **Consistency Check**: Verify same score across systems

---

## Success Metrics

- [ ] Cache hit rate >80%
- [ ] Unified score variance <10% from AST baseline
- [ ] ADHD task completion improvement >15%
- [ ] Reduced complexity calculation time by 60%
