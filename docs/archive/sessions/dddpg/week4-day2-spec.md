---
id: week4-day2-spec
title: Week4 Day2 Spec
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week4 Day2 Spec (explanation) for dopemux documentation and developer workflows.
---
# Week 4 Day 2: Technical Specification
## Task Relationship Mapping with DDDPG Integration

**Date**: 2025-10-29
**Status**: Ready to implement
**Based on**: WEEK4_DAY2_DEEP_RESEARCH.md

---

## 🎯 Integration Strategy

### Discovery: DDDPG Already Has Decision Models!

**Existing Infrastructure** (from core/models.py):
```python
class Decision(BaseModel):
    """Core decision model - ADHD-optimized"""
    # Already has:
- id, workspace_id, instance_id
- title, description, context
- decision_type, status, visibility
- created_at, updated_at
- tags, metadata
```

**Existing Services** (from queries/service.py):
```python
class QueryService:
    """ADHD-optimized query patterns"""
    # Already has:
- overview() - Top-3 pattern
- search() - Text search
- get_by_id() - Single decision
- list_decisions() - Filtered list
```

**Our Task**: Extend with KG-powered relationship queries!

---

## 📐 Architecture

### Component Structure

```
services/dddpg/
├── kg_integration.py           # Day 1 (DONE)
│   └── DDDPGKG                 # KG query layer
│
├── relationship_mapper.py      # Day 2 (NEW)
│   └── RelationshipMapper      # Graph construction
│
├── suggestion_engine.py        # Day 2 (NEW)
│   └── SuggestionEngine        # Enhanced suggestions
│
├── queries/service.py          # EXTEND
│   └── QueryService            # Add KG methods
│
└── core/models.py              # EXTEND (optional)
    └── DecisionContext         # Decision context model
```

### Data Flow

```
User Request
    ↓
QueryService (queries/service.py)
    ↓
├─→ RelationshipMapper (build graphs)
│   └─→ DDDPGKG (KG queries)
│       └─→ AGE (graph DB)
│
└─→ SuggestionEngine (rank tasks)
    └─→ DDDPGKG (semantic search)
        └─→ AGE (graph DB)
```

---

## 🏗️ Implementation Design

### Phase 1: Decision Context Extension (SIMPLIFIED)

**Realization**: DDDPG already tracks decisions! Just add KG relationships.

**Add to kg_integration.py**:
```python
async def link_decision_to_task(
    self,
    decision_id: str,
    task_id: str,
    relationship_type: str = "DECIDES"
) -> None:
    """Link existing Decision to Task in KG."""
    # Cypher:
    # MATCH (d:Decision {id: $decision_id})
    # MATCH (t:Task {id: $task_id})
    # CREATE (d)-[:DECIDES]->(t)

async def get_task_decisions(
    self,
    task_id: str
) -> List[str]:
    """Get all decisions for a task."""
    # Returns: list of decision_ids
```

**No new models needed** - reuse existing `Decision` from core/models.py!

### Phase 2: Relationship Mapper (NEW FILE)

**Create relationship_mapper.py**:
```python
class RelationshipMapper:
    """
    Builds relationship graphs from KG data.
    Works with DDDPGKG for raw queries.
    """

    def __init__(self, kg: DDDPGKG):
        self.kg = kg

    async def build_dependency_chain(
        self,
        task_id: str,
        max_depth: int = 3
    ) -> Dict[str, List[str]]:
        """
        Build full dependency chain.

        Returns:
            {
                'upstream': [...],    # Dependencies
                'downstream': [...],  # Dependents
                'parallel': [...]     # Siblings
            }
        """
        # Use KG to traverse DEPENDS_ON edges
        # Upstream: tasks this depends on
        # Downstream: tasks that depend on this
        # Parallel: tasks with same upstream

    async def build_work_cluster(
        self,
        theme: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Build cluster of related work.

        Returns:
            {
                'tasks': [...],
                'decisions': [...],
                'patterns': [...]
            }
        """
        # Use semantic search + relationship traversal
```

### Phase 3: Suggestion Engine (NEW FILE)

**Create suggestion_engine.py**:
```python
class SuggestionEngine:
    """
    ADHD-optimized task suggestions.
    Uses KG relationships + context scoring.
    """

    def __init__(self, kg: DDDPGKG, mapper: RelationshipMapper):
        self.kg = kg
        self.mapper = mapper

    async def get_enhanced_suggestions(
        self,
        current_task: Optional[str] = None,
        energy_level: str = "medium",
        available_time_mins: int = 30,
        focus_state: str = "normal",
        limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Context-aware task suggestions.

        Scoring:
- Dependency satisfaction (blockers resolved)
- Energy level match
- Time availability
- Focus state compatibility
- Pattern similarity

        Returns:
            {
                'next_best': [...],       # Top recommendations
                'quick_wins': [...],      # < 15 min tasks
                'related_decisions': [...], # Relevant context
                'patterns': [...]         # Success patterns
            }
        """
        # 1. Get dependency-satisfied tasks
        # 2. Score by context
        # 3. Rank and filter
        # 4. Return structured results

    def _score_task(
        self,
        task: Dict,
        context: Dict
    ) -> float:
        """Score task by context match (0-1)."""
        score = 0.0

        # Energy match (0-0.4)
        score += self._energy_score(task, context)

        # Time match (0-0.3)
        score += self._time_score(task, context)

        # Focus match (0-0.2)
        score += self._focus_score(task, context)

        # Pattern match (0-0.1)
        score += self._pattern_score(task, context)

        return min(score, 1.0)
```

### Phase 4: QueryService Integration

**Extend queries/service.py**:
```python
class QueryService:
    # ... existing methods ...

    def __init__(
        self,
        storage: StorageBackend,
        kg: Optional[DDDPGKG] = None  # NEW
    ):
        self.storage = storage
        self.kg = kg

        if kg:
            self.mapper = RelationshipMapper(kg)
            self.suggestions = SuggestionEngine(kg, self.mapper)

    # NEW: KG-powered queries

    async def get_task_with_context(
        self,
        task_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        Get task with full relationship context.
        Falls back to basic query if KG unavailable.
        """
        if not self.kg:
            return await self.storage.get_task(task_id)

        # Get task + relationships + decisions
        task = await self.storage.get_task(task_id)
        relationships = await self.kg.get_task_relationships(task_id)
        decisions = await self.kg.get_task_decisions(task_id)

        return {
            **task,
            'relationships': relationships,
            'decisions': decisions
        }

    async def suggest_next_tasks(
        self,
        workspace_id: str,
        context: Dict
    ) -> Dict[str, List[Dict]]:
        """
        ADHD-optimized task suggestions.
        Falls back to recency if KG unavailable.
        """
        if not self.suggestions:
            # Fallback: most recent tasks
            return {
                'next_best': await self.storage.list_recent_tasks(limit=5),
                'quick_wins': [],
                'related_decisions': [],
                'patterns': []
            }

        return await self.suggestions.get_enhanced_suggestions(**context)
```

---

## 📋 Implementation Tasks

### Phase 1: Decision Context (15 min)

**File**: `kg_integration.py` (extend DDDPGKG)

1. Add `link_decision_to_task()` (7 min)
1. Add `get_task_decisions()` (5 min)
1. Add tests (3 min)

**Cypher queries**:
```cypher
# Link decision
MATCH (d:Decision {id: $decision_id})
MATCH (t:Task {id: $task_id})
CREATE (d)-[:DECIDES]->(t)

# Get decisions
MATCH (d:Decision)-[:DECIDES]->(t:Task {id: $task_id})
RETURN d.id
```

### Phase 2: Relationship Mapper (25 min)

**File**: `relationship_mapper.py` (NEW)

1. Create `RelationshipMapper` class (5 min)
1. Implement `build_dependency_chain()` (10 min)
1. Implement `build_work_cluster()` (7 min)
1. Add tests (3 min)

**Cypher queries**:
```cypher
# Dependency chain (upstream)
MATCH (t:Task {id: $task_id})-[:DEPENDS_ON*1..3]->(upstream:Task)
RETURN upstream.id

# Dependency chain (downstream)
MATCH (downstream:Task)-[:DEPENDS_ON*1..3]->(t:Task {id: $task_id})
RETURN downstream.id

# Work cluster
MATCH (t:Task)
WHERE t.description CONTAINS $theme
  OR t.tags CONTAINS $theme
OPTIONAL MATCH (t)<-[:DECIDES]-(d:Decision)
RETURN t, d
LIMIT $limit
```

### Phase 3: Suggestion Engine (30 min)

**File**: `suggestion_engine.py` (NEW)

1. Create `SuggestionEngine` class (5 min)
1. Implement `get_enhanced_suggestions()` (12 min)
1. Implement `_score_task()` helper (8 min)
1. Add tests (5 min)

**Scoring logic**:
```python
def _energy_score(task, context):
    """Energy level match (0-0.4)"""
    levels = ['low', 'medium', 'high']
    task_level = task.get('energy_required', 'medium')
    context_level = context['energy_level']

    diff = abs(levels.index(task_level) - levels.index(context_level))
    return 0.4 * (1 - diff / 2)

def _time_score(task, context):
    """Time availability match (0-0.3)"""
    task_time = task.get('estimated_minutes', 30)
    available = context['available_time_mins']

    if task_time > available:
        return 0.0
    return 0.3 * (1 - task_time / available)
```

### Phase 4: QueryService Integration (20 min)

**File**: `queries/service.py` (extend)

1. Add `kg` parameter to `__init__()` (3 min)
1. Add `get_task_with_context()` (7 min)
1. Add `suggest_next_tasks()` (7 min)
1. Add integration test (3 min)

---

## ✅ Success Criteria

**Functionality**:
- [ ] Can link decisions to tasks in KG
- [ ] Can build dependency chains (3 levels deep)
- [ ] Can build work clusters by theme
- [ ] Can generate context-aware suggestions
- [ ] QueryService integrates seamlessly

**Quality**:
- [ ] All methods have docstrings
- [ ] Parameterized queries (security)
- [ ] Graceful degradation everywhere
- [ ] 100% test coverage

**Performance**:
- [ ] Dependency chain: < 200ms
- [ ] Work cluster: < 300ms
- [ ] Suggestions: < 500ms

**Integration**:
- [ ] Works with existing DDDPG models
- [ ] No breaking changes to QueryService
- [ ] Fallbacks work without KG

---

## 🚀 Ready to Build

**Total Estimate**: 1.5 hours
**Phases**: 4 (15 + 25 + 30 + 20 min)
**Confidence**: Very High

**Next**: Implement Phase 1 (Decision Context)

---

**Status**: Spec complete, ready to code! 🎯
