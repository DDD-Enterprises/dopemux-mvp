---
id: week4-day2-validation
title: Week4 Day2 Validation
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week4 Day2 Validation (explanation) for dopemux documentation and developer
  workflows.
---
# Week 4 Day 2: Deep Validation & Architecture Review
## Critical Analysis Before Implementation

**Date**: 2025-10-29 10:07 UTC
**Status**: Validation in progress
**Goal**: Ensure Day 2 design is optimal before coding

---

## 🔍 Current State Analysis

### What We Have (Day 1 Complete)

**DDDPGKG** (`kg_integration.py` - 379 lines):
```python
class DDDPGKG:
    """KG query layer - DONE ✅"""

    # Task relationships
    - get_task_relationships()      # Dependencies + blockers
    - get_related_tasks()            # Semantic similarity
    - get_dependency_chain()         # Full traversal

    # Search
    - search_tasks()                 # Keyword search

    # Helpers
    - _execute_query()               # Safe parameterized queries
    - _format_task_result()          # Consistent output
```

**QueryService** (`queries/service.py` - 417 lines):
```python
class QueryService:
    """ADHD-optimized queries - EXISTS"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage  # No KG yet!

    # Tier 1: Overview (Top-3)
    - overview()
    - overview_by_type()
    - overview_by_tags()

    # Tier 2: Exploration
    - explore_related()
    - explore_timeline()

    # Tier 3: Deep
    - deep_context()
    - full_graph()
```

**Decision** (`core/models.py` - 221 lines):
```python
class Decision(BaseModel):
    """Core decision model - EXISTS ✅"""
    id: str
    workspace_id: str
    instance_id: str
    title: str
    description: str
    decision_type: DecisionType  # Enum
    status: DecisionStatus       # Enum
    visibility: DecisionVisibility
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    metadata: Dict[str, Any]
    relationships: List[DecisionRelationship]
```

---

## ❓ Critical Questions

### Q1: Do we need RelationshipMapper as separate class?

**Current Plan**:
```python
# relationship_mapper.py (NEW FILE)
class RelationshipMapper:
    def __init__(self, kg: DDDPGKG):
        self.kg = kg

    async def build_dependency_chain(...)
    async def build_work_cluster(...)
```

**Analysis**:
- DDDPGKG already has `get_dependency_chain()`! (line 289-333)
- DDDPGKG already has `get_related_tasks()`! (line 235-288)

**Question**: Are we duplicating functionality?

**Options**:
1. **Keep RelationshipMapper** - Higher-level orchestration
2. **Extend DDDPGKG** - Add cluster methods directly
3. **Skip it** - Use existing DDDPGKG methods

**Recommendation**: **Option 1 - Keep it**, BUT:
- Focus on **aggregation** not duplication
- Use DDDPGKG as primitive layer
- RelationshipMapper builds **composite views**

**Example**:
```python
class RelationshipMapper:
    """Composite relationship views"""

    async def build_task_context(self, task_id: str) -> Dict:
        """Aggregate all relationships in one call"""
        # Uses DDDPGKG primitives:
        deps = await self.kg.get_dependency_chain(task_id)
        related = await self.kg.get_related_tasks(task_id, limit=10)
        decisions = await self.kg.get_task_decisions(task_id)  # NEW

        return {
            'dependencies': deps,
            'related': related,
            'decisions': decisions,
            'clusters': self._identify_clusters(related)
        }
```

### Q2: Decision-Task Linking - Where does it belong?

**Current Plan**: Add to `kg_integration.py`

**Options**:
1. **DDDPGKG** - Fits with other KG queries
2. **Decision model** - Domain logic
3. **Separate service** - Decision management

**Analysis**:
- Decisions are stored in DDDPG storage (SQLite/Postgres)
- Tasks are stored in KG (AGE)
- Link exists in KG only (graph edge)

**Decision**: **DDDPGKG is correct**! It's a KG operation.

**Implementation**:
```python
# In DDDPGKG (kg_integration.py)
async def link_decision_to_task(
    self,
    decision_id: str,
    task_id: str,
    relationship_type: str = "DECIDES"
) -> bool:
    """Create Decision->Task edge in KG."""
    query = """
    MATCH (t:Task {id: $task_id})
    CREATE (d:Decision {id: $decision_id})
    CREATE (d)-[:DECIDES]->(t)
    RETURN d, t
    """
    # Note: Decision node in KG is minimal (just ID)
    # Full Decision data in DDDPG storage
```

### Q3: SuggestionEngine - Is this the right abstraction?

**Current Plan**:
```python
class SuggestionEngine:
    def __init__(self, kg: DDDPGKG, mapper: RelationshipMapper):
        ...

    async def get_enhanced_suggestions(
        energy_level: str,
        available_time_mins: int,
        focus_state: str,
        ...
    ) -> Dict[str, List[Dict]]
```

**Analysis**: This is **excellent** but needs refinement!

**Issues**:
1. Where does task metadata (energy_required, estimated_minutes) live?
   - Not in KG currently
   - Should it be?

2. How do we get current state (energy_level, focus_state)?
   - From user input?
   - From attention monitor?
   - From session history?

**Architectural Decision Required**:

**Option A**: Tasks store ADHD metadata in KG
```cypher
CREATE (t:Task {
    id: $id,
    description: $desc,
    energy_required: "medium",  # NEW
    estimated_minutes: 30,      # NEW
    focus_type: "deep"          # NEW
})
```

**Option B**: Tasks reference Decision metadata
```python
# Decision has adhd_context field
decision.metadata['adhd_context'] = {
    'energy_required': 'medium',
    'estimated_minutes': 30,
    'focus_type': 'deep'
}
```

**Option C**: Separate ADHD metadata store
```python
# New table/collection
ADHDTaskMetadata:
    task_id: str
    energy_required: str
    estimated_minutes: int
    focus_type: str
```

**Recommendation**: **Option A** - Store in KG!

**Why**:
- Tasks are already in KG
- Enables graph queries ("find low-energy tasks")
- Consistent with existing architecture
- No extra joins needed

**Updated Task Schema**:
```cypher
CREATE (t:Task {
    id: $id,
    workspace_id: $workspace_id,
    description: $description,
    status: $status,
    created_at: $created_at,

    // ADHD metadata (NEW)
    energy_required: $energy,      # low/medium/high
    estimated_minutes: $minutes,   # integer
    focus_type: $focus,            # deep/shallow/creative
    complexity: $complexity        # simple/medium/complex
})
```

### Q4: QueryService Integration - Breaking changes?

**Current Plan**: Add `kg` parameter to `__init__()`

**Analysis**:
```python
# Current
class QueryService:
    def __init__(self, storage: StorageBackend):
        ...

# Proposed
class QueryService:
    def __init__(
        self,
        storage: StorageBackend,
        kg: Optional[DDDPGKG] = None  # NEW
    ):
        ...
```

**Impact**: **Backward compatible** ✅
- Existing code still works (kg=None)
- New features optional
- Graceful degradation built-in

**Enhancement**: Add factory method!
```python
class QueryService:
    @classmethod
    def with_kg(
        cls,
        storage: StorageBackend,
        workspace_id: str,
        age_client: Optional[AGEClient] = None
    ) -> 'QueryService':
        """Create QueryService with KG integration."""
        kg = DDDPGKG(workspace_id, age_client=age_client)
        return cls(storage, kg=kg)
```

### Q5: Performance - Are we over-fetching?

**Concern**: Each suggestion query might be expensive!

**Current Design**:
```python
# get_enhanced_suggestions() might do:
1. get_dependency_chain() → graph traversal
2. get_related_tasks() → semantic search
3. get_task_decisions() → multiple lookups
4. Score all results → computation
```

**Analysis**: We need **caching**!

**Solution**: Add simple in-memory cache
```python
from functools import lru_cache
from datetime import datetime, timedelta

class SuggestionEngine:
    def __init__(self, kg, mapper):
        self.kg = kg
        self.mapper = mapper
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)

    async def get_enhanced_suggestions(
        self,
        workspace_id: str,
        context: Dict
    ) -> Dict:
        # Check cache
        cache_key = f"{workspace_id}:{context['energy_level']}"
        if cache_key in self._cache:
            cached_at, result = self._cache[cache_key]
            if datetime.now() - cached_at < self._cache_ttl:
                return result

        # Compute
        result = await self._compute_suggestions(workspace_id, context)

        # Cache
        self._cache[cache_key] = (datetime.now(), result)
        return result
```

---

## 🎯 Refined Architecture

### Updated Component Design

```
services/dddpg/
├── kg_integration.py (379 lines)
│   └── DDDPGKG
│       ├── [existing methods] ✅
│       ├── link_decision_to_task() [NEW]
│       └── get_task_decisions() [NEW]
│
├── relationship_mapper.py [NEW - 150 lines]
│   └── RelationshipMapper
│       ├── build_task_context()      # Aggregates all relationships
│       └── build_work_cluster()      # Theme-based clustering
│
├── suggestion_engine.py [NEW - 200 lines]
│   └── SuggestionEngine
│       ├── get_enhanced_suggestions()  # Main API
│       ├── _compute_suggestions()      # Core logic
│       ├── _score_task()               # Context scoring
│       └── _cache [in-memory]          # Performance
│
└── queries/service.py (417 lines)
    └── QueryService
        ├── [existing methods] ✅
        ├── with_kg() [class method]    # Factory
        ├── get_task_with_context()     # New query
        └── suggest_next_tasks()        # New query
```

### Updated Task Schema (KG)

```cypher
// Enhanced Task node
CREATE (t:Task {
    // Core
    id: $id,
    workspace_id: $workspace_id,
    description: $description,
    status: $status,
    created_at: $created_at,
    updated_at: $updated_at,

    // ADHD metadata
    energy_required: $energy,      // "low" | "medium" | "high"
    estimated_minutes: $minutes,   // integer
    focus_type: $focus,            // "deep" | "shallow" | "creative"
    complexity: $complexity,       // "simple" | "medium" | "complex"

    // Patterns
    success_pattern: $pattern,     // Optional past success indicator
    break_friendly: $break_ok      // boolean - can pause mid-task?
})
```

### Data Flow (Refined)

```
User: "Suggest next task"
    ↓
QueryService.suggest_next_tasks(context={
    energy_level: "medium",
    available_time_mins: 30,
    focus_state: "scattered"
})
    ↓
SuggestionEngine.get_enhanced_suggestions()
    ↓
    ├─→ Check cache (5 min TTL)
    │   └─→ Return if fresh
    │
    └─→ Compute:
        ├─→ RelationshipMapper.build_task_context()
        │   └─→ DDDPGKG queries (parallel!)
        │
        ├─→ Filter by dependencies satisfied
        │
        ├─→ Score by context match
        │
        └─→ Rank & return top 5
```

---

## ✅ Validation Results

### What's GOOD:
1. ✅ DDDPGKG foundation is solid
2. ✅ QueryService integration is backward compatible
3. ✅ Decision model already exists
4. ✅ Graceful degradation strategy works

### What Needs REFINEMENT:
1. 🔄 Task schema needs ADHD metadata
2. 🔄 Add caching to SuggestionEngine
3. 🔄 RelationshipMapper should aggregate, not duplicate
4. 🔄 Add factory method to QueryService

### What's MISSING:
1. ❌ Task creation workflow (how do ADHD fields get set?)
2. ❌ Context source (where does energy_level come from?)
3. ❌ Pattern learning (how do we track success patterns?)

---

## 📋 Updated Implementation Plan

### Phase 1: Task Schema Enhancement (20 min)

**Task**: Extend Task nodes with ADHD metadata

**Files**:
- `kg_integration.py` - Update task creation queries

**Work**:
1. Update `create_task()` method (if exists)
2. Add ADHD metadata to schema
3. Update tests

### Phase 2: Decision-Task Linking (15 min)

**Task**: Link decisions to tasks in KG

**Files**:
- `kg_integration.py` - Add methods to DDDPGKG

**Work**:
1. `link_decision_to_task()`
2. `get_task_decisions()`
3. Tests

### Phase 3: Relationship Mapper (20 min)

**Task**: Composite relationship views

**Files**:
- `relationship_mapper.py` (NEW)

**Work**:
1. `RelationshipMapper` class
2. `build_task_context()` - Aggregates all relationships
3. `build_work_cluster()` - Theme-based grouping
4. Tests

### Phase 4: Suggestion Engine (30 min)

**Task**: Context-aware suggestions with caching

**Files**:
- `suggestion_engine.py` (NEW)

**Work**:
1. `SuggestionEngine` class with cache
2. `get_enhanced_suggestions()` - Main API
3. `_compute_suggestions()` - Core logic
4. `_score_task()` - Context matching
5. Tests

### Phase 5: QueryService Integration (15 min)

**Task**: Wire everything together

**Files**:
- `queries/service.py`

**Work**:
1. Add `kg` parameter (optional)
2. Add `with_kg()` factory method
3. Add `get_task_with_context()`
4. Add `suggest_next_tasks()`
5. Integration test

**Total**: ~100 minutes (1h 40m)

---

## 🚀 Ready to Proceed?

**Validation Complete**: Architecture is sound with refinements!

**Key Changes from Original Plan**:
1. Added Task schema enhancement (Phase 1)
2. Added caching to SuggestionEngine
3. Refined RelationshipMapper to aggregate
4. Added factory method pattern

**Confidence**: Very High ✅

**Next**: Implement Phase 1 (Task Schema Enhancement)

---

**Status**: Validated and ready to build! 🎯
