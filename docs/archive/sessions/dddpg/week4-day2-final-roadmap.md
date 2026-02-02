---
id: week4-day2-final-roadmap
title: Week4 Day2 Final Roadmap
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Week 4 Day 2: Final Implementation Roadmap
## Task Relationship Mapping - Validated & Ready

**Date**: 2025-10-29 10:07 UTC
**Validation**: Complete ✅
**Architecture**: Reviewed and refined
**Status**: Ready to build

---

## 🎯 What We're Building

**Goal**: Enhance DDDPG with intelligent task relationship mapping and context-aware suggestions.

**Key Insight**: DDDPGKG (Day 1) provides primitives. Day 2 builds **composite intelligence** on top.

---

## 📐 Final Architecture

### Component Stack

```
                    User/API
                        ↓
            ┌───────────────────────┐
            │   QueryService        │  ← Entry point
            │  (queries/service.py) │
            └───────────┬───────────┘
                        ↓
            ┌───────────────────────┐
            │  SuggestionEngine     │  ← Intelligence layer
            │ (suggestion_engine.py)│
            └───────┬───────────────┘
                    ↓
        ┌───────────────────────┐
        │  RelationshipMapper   │  ← Aggregation layer
        │(relationship_mapper.py)│
        └───────┬───────────────┘
                ↓
    ┌───────────────────────┐
    │      DDDPGKG          │  ← Primitive layer (Day 1 ✅)
    │ (kg_integration.py)   │
    └───────┬───────────────┘
            ↓
    ┌───────────────┐
    │   AGE (KG)    │  ← Data layer
    └───────────────┘
```

### Layer Responsibilities

**DDDPGKG** (Primitives):
- Single-purpose queries
- Direct KG access
- Basic relationship traversal

**RelationshipMapper** (Aggregation):
- Multi-query coordination
- Composite views
- Data synthesis

**SuggestionEngine** (Intelligence):
- Context-aware scoring
- Pattern matching
- Caching/optimization

**QueryService** (API):
- Public interface
- Optional KG integration
- Backward compatibility

---

## 📋 Implementation Phases

### Phase 1: Decision-Task Linking (15 min)

**Goal**: Link DDDPG Decisions to KG Tasks

**File**: `kg_integration.py` (extend DDDPGKG)

**New Methods**:
```python
async def link_decision_to_task(
    self,
    decision_id: str,
    task_id: str,
    relationship_type: str = "DECIDES"
) -> bool:
    """Create Decision→Task edge in KG."""

async def get_task_decisions(
    self,
    task_id: str
) -> List[str]:
    """Get all decision IDs for a task."""

async def unlink_decision_from_task(
    self,
    decision_id: str,
    task_id: str
) -> bool:
    """Remove Decision→Task edge (cleanup)."""
```

**Cypher**:
```cypher
# Link
MATCH (t:Task {id: $task_id})
CREATE (d:Decision {id: $decision_id})
CREATE (d)-[:DECIDES]->(t)

# Get decisions
MATCH (d:Decision)-[:DECIDES]->(t:Task {id: $task_id})
RETURN d.id

# Unlink
MATCH (d:Decision {id: $decision_id})-[r:DECIDES]->(t:Task {id: $task_id})
DELETE r
```

**Tests**:
- Link decision to task
- Get task decisions
- Unlink decision
- Handle missing task/decision
- Graceful degradation

**Success Criteria**:
- [ ] Can link decisions to tasks
- [ ] Can retrieve decision list
- [ ] Can remove links
- [ ] 100% test coverage
- [ ] Parameterized queries

### Phase 2: Relationship Mapper (25 min)

**Goal**: Composite relationship views

**File**: `relationship_mapper.py` (NEW)

**Class Structure**:
```python
class RelationshipMapper:
    """
    Aggregates multiple DDDPGKG queries into composite views.

    Responsibilities:
    - Coordinate parallel queries
    - Synthesize results
    - Identify patterns/clusters
    """

    def __init__(self, kg: DDDPGKG):
        self.kg = kg

    async def build_task_context(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get complete task context in one call.

        Aggregates:
        - Dependencies (upstream/downstream)
        - Related tasks (semantic)
        - Decisions (rationale)
        - Clusters (themes)

        Returns:
            {
                'task_id': str,
                'dependencies': {
                    'upstream': [task_ids],
                    'downstream': [task_ids],
                    'parallel': [task_ids]
                },
                'related': [task_details],
                'decisions': [decision_ids],
                'clusters': [cluster_info]
            }
        """

    async def build_work_cluster(
        self,
        theme: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Build cluster of related work by theme.

        Uses:
        - Semantic search (DDDPGKG)
        - Relationship traversal
        - Decision linking

        Returns:
            {
                'theme': str,
                'tasks': [task_details],
                'decisions': [decision_ids],
                'patterns': [pattern_info]
            }
        """

    def _identify_clusters(
        self,
        tasks: List[Dict]
    ) -> List[Dict]:
        """Identify thematic clusters in task list."""
        # Simple clustering by tags/keywords
```

**Tests**:
- Build task context (full view)
- Build work cluster (theme-based)
- Handle parallel queries
- Identify clusters
- Graceful degradation

**Success Criteria**:
- [ ] Aggregates all relationships
- [ ] Performs parallel queries
- [ ] Identifies clusters correctly
- [ ] < 200ms for task context
- [ ] 100% test coverage

### Phase 3: Suggestion Engine (35 min)

**Goal**: Context-aware task suggestions with caching

**File**: `suggestion_engine.py` (NEW)

**Class Structure**:
```python
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class SuggestionEngine:
    """
    ADHD-optimized task suggestions using KG relationships.

    Features:
    - Context-aware scoring (energy, time, focus)
    - Dependency satisfaction checking
    - Pattern-based ranking
    - In-memory caching (5 min TTL)

    Architecture:
    - Uses RelationshipMapper for data
    - Caches by workspace+context
    - Graceful degradation
    """

    def __init__(
        self,
        kg: DDDPGKG,
        mapper: RelationshipMapper,
        cache_ttl_minutes: int = 5
    ):
        self.kg = kg
        self.mapper = mapper
        self._cache: Dict[str, tuple[datetime, Dict]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)

    async def get_enhanced_suggestions(
        self,
        workspace_id: str,
        current_task: Optional[str] = None,
        energy_level: str = "medium",
        available_time_mins: int = 30,
        focus_state: str = "normal",
        limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Get context-aware task suggestions.

        Context Parameters:
        - energy_level: "low" | "medium" | "high"
        - available_time_mins: integer (minutes)
        - focus_state: "scattered" | "normal" | "deep"

        Returns:
            {
                'next_best': [tasks],       # Top recommendations
                'quick_wins': [tasks],      # < 15 min tasks
                'related_decisions': [ids], # Relevant context
                'patterns': [info]          # Success patterns
            }
        """
        # Check cache
        cache_key = f"{workspace_id}:{energy_level}:{available_time_mins}:{focus_state}"
        if cache_key in self._cache:
            cached_at, result = self._cache[cache_key]
            if datetime.now() - cached_at < self._cache_ttl:
                return result

        # Compute suggestions
        result = await self._compute_suggestions(
            workspace_id,
            current_task,
            energy_level,
            available_time_mins,
            focus_state,
            limit
        )

        # Update cache
        self._cache[cache_key] = (datetime.now(), result)

        return result

    async def _compute_suggestions(
        self,
        workspace_id: str,
        current_task: Optional[str],
        energy_level: str,
        available_time_mins: int,
        focus_state: str,
        limit: int
    ) -> Dict[str, List[Dict]]:
        """Core suggestion computation logic."""
        # 1. Get candidate tasks
        candidates = await self._get_candidate_tasks(workspace_id)

        # 2. Filter by dependency satisfaction
        viable = [t for t in candidates if await self._dependencies_satisfied(t)]

        # 3. Score by context
        context = {
            'energy_level': energy_level,
            'available_time_mins': available_time_mins,
            'focus_state': focus_state
        }
        scored = [(self._score_task(t, context), t) for t in viable]
        scored.sort(reverse=True, key=lambda x: x[0])

        # 4. Separate quick wins
        quick_wins = [t for score, t in scored if t.get('estimated_minutes', 30) < 15]

        # 5. Get related decisions
        top_task_ids = [t['id'] for _, t in scored[:limit]]
        decisions = await self._get_related_decisions(top_task_ids)

        return {
            'next_best': [t for _, t in scored[:limit]],
            'quick_wins': quick_wins[:3],
            'related_decisions': decisions,
            'patterns': []  # TODO: Pattern mining
        }

    def _score_task(
        self,
        task: Dict,
        context: Dict
    ) -> float:
        """
        Score task by context match (0.0-1.0).

        Scoring:
        - Energy match: 0-0.4
        - Time match: 0-0.3
        - Focus match: 0-0.2
        - Pattern match: 0-0.1
        """
        score = 0.0

        # Energy match
        score += self._energy_score(task, context)

        # Time match
        score += self._time_score(task, context)

        # Focus match
        score += self._focus_score(task, context)

        # Pattern match (TODO)
        # score += self._pattern_score(task, context)

        return min(score, 1.0)

    def _energy_score(self, task: Dict, context: Dict) -> float:
        """Energy level match (0-0.4)."""
        levels = {'low': 0, 'medium': 1, 'high': 2}
        task_energy = task.get('energy_required', 'medium')
        context_energy = context['energy_level']

        diff = abs(levels[task_energy] - levels[context_energy])
        return 0.4 * (1 - diff / 2)

    def _time_score(self, task: Dict, context: Dict) -> float:
        """Time availability match (0-0.3)."""
        task_time = task.get('estimated_minutes', 30)
        available = context['available_time_mins']

        if task_time > available:
            return 0.0
        return 0.3 * (1 - task_time / available)

    def _focus_score(self, task: Dict, context: Dict) -> float:
        """Focus state match (0-0.2)."""
        # Simple mapping for now
        focus_match = {
            ('scattered', 'shallow'): 0.2,
            ('scattered', 'creative'): 0.15,
            ('scattered', 'deep'): 0.0,
            ('normal', 'shallow'): 0.15,
            ('normal', 'creative'): 0.2,
            ('normal', 'deep'): 0.15,
            ('deep', 'shallow'): 0.1,
            ('deep', 'creative'): 0.15,
            ('deep', 'deep'): 0.2
        }

        task_focus = task.get('focus_type', 'creative')
        context_focus = context['focus_state']

        return focus_match.get((context_focus, task_focus), 0.1)

    async def _get_candidate_tasks(self, workspace_id: str) -> List[Dict]:
        """Get all candidate tasks for suggestions."""
        # Use KG search (semantic + keyword)
        return await self.kg.search_tasks("status:todo OR status:in_progress", limit=50)

    async def _dependencies_satisfied(self, task: Dict) -> bool:
        """Check if task dependencies are satisfied."""
        task_id = task.get('id')
        if not task_id:
            return True

        rels = await self.kg.get_task_relationships(task_id)
        deps = rels.get('dependencies', [])

        # TODO: Check if dependencies are complete
        # For now, assume satisfied if no dependencies
        return len(deps) == 0

    async def _get_related_decisions(self, task_ids: List[str]) -> List[str]:
        """Get decisions related to tasks."""
        decisions = []
        for task_id in task_ids:
            task_decisions = await self.kg.get_task_decisions(task_id)
            decisions.extend(task_decisions)
        return list(set(decisions))  # Deduplicate

    def clear_cache(self):
        """Clear suggestion cache."""
        self._cache.clear()
```

**Tests**:
- Get enhanced suggestions
- Context scoring (energy, time, focus)
- Cache hit/miss
- Dependency filtering
- Graceful degradation

**Success Criteria**:
- [ ] Returns ranked suggestions
- [ ] Cache works (5 min TTL)
- [ ] Scoring is reasonable
- [ ] < 500ms with cache miss
- [ ] < 50ms with cache hit
- [ ] 100% test coverage

### Phase 4: QueryService Integration (20 min)

**Goal**: Wire everything together via public API

**File**: `queries/service.py` (extend)

**Changes**:
```python
from typing import Optional
from ..kg_integration import DDDPGKG
from ..relationship_mapper import RelationshipMapper
from ..suggestion_engine import SuggestionEngine

class QueryService:
    def __init__(
        self,
        storage: StorageBackend,
        kg: Optional[DDDPGKG] = None  # NEW: Optional KG
    ):
        self.storage = storage
        self.kg = kg

        # Initialize KG-dependent services
        if kg:
            self.mapper = RelationshipMapper(kg)
            self.suggestions = SuggestionEngine(kg, self.mapper)
        else:
            self.mapper = None
            self.suggestions = None

    @classmethod
    def with_kg(
        cls,
        storage: StorageBackend,
        workspace_id: str,
        age_client: Optional[AGEClient] = None
    ) -> 'QueryService':
        """Factory: Create QueryService with KG integration."""
        kg = DDDPGKG(workspace_id, age_client=age_client)
        return cls(storage, kg=kg)

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
        if not self.mapper:
            # Fallback: basic task data
            return await self.storage.get_task(task_id)

        # KG-enhanced context
        return await self.mapper.build_task_context(task_id)

    async def suggest_next_tasks(
        self,
        workspace_id: str,
        context: Dict
    ) -> Dict[str, List[Dict]]:
        """
        Get ADHD-optimized task suggestions.

        Falls back to recency if KG unavailable.

        Args:
            context: {
                'energy_level': 'low|medium|high',
                'available_time_mins': int,
                'focus_state': 'scattered|normal|deep',
                'current_task': str (optional)
            }
        """
        if not self.suggestions:
            # Fallback: most recent tasks
            recent = await self.storage.list_recent_tasks(limit=5)
            return {
                'next_best': recent,
                'quick_wins': [],
                'related_decisions': [],
                'patterns': []
            }

        return await self.suggestions.get_enhanced_suggestions(
            workspace_id=workspace_id,
            **context
        )
```

**Tests**:
- Factory method creates KG-enabled service
- get_task_with_context() with KG
- get_task_with_context() without KG (fallback)
- suggest_next_tasks() with KG
- suggest_next_tasks() without KG (fallback)
- Integration test (end-to-end)

**Success Criteria**:
- [ ] Factory method works
- [ ] KG integration is optional
- [ ] Fallbacks work correctly
- [ ] No breaking changes
- [ ] 100% test coverage

---

## ✅ Definition of Done

**Functionality**:
- [ ] Can link decisions to tasks in KG
- [ ] Can build composite relationship views
- [ ] Can generate context-aware suggestions
- [ ] QueryService integrates seamlessly
- [ ] All fallbacks work

**Quality**:
- [ ] All methods have docstrings
- [ ] Parameterized queries (security)
- [ ] Graceful degradation everywhere
- [ ] 100% test coverage
- [ ] No breaking changes

**Performance**:
- [ ] Decision linking: < 100ms
- [ ] Task context: < 200ms
- [ ] Work cluster: < 300ms
- [ ] Suggestions (cached): < 50ms
- [ ] Suggestions (uncached): < 500ms

**Documentation**:
- [ ] README updated
- [ ] API examples provided
- [ ] Architecture documented

---

## 📊 Estimates

**Time Breakdown**:
- Phase 1: 15 min
- Phase 2: 25 min
- Phase 3: 35 min
- Phase 4: 20 min
- **Total**: 95 minutes (~1h 35m)

**Lines of Code (estimated)**:
- Phase 1: +80 lines (kg_integration.py)
- Phase 2: +150 lines (relationship_mapper.py)
- Phase 3: +220 lines (suggestion_engine.py)
- Phase 4: +60 lines (queries/service.py)
- Tests: +400 lines
- **Total**: ~910 lines

---

## 🚀 Ready to Build!

**Validation**: Complete ✅
**Architecture**: Refined and optimal
**Plan**: Detailed and actionable
**Confidence**: Very High

**Next Step**: Implement Phase 1 (Decision-Task Linking)

Let's build! 🎯
