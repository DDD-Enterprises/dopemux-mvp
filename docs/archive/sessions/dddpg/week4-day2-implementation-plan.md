---
id: week4-day2-implementation-plan
title: Week4 Day2 Implementation Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week4 Day2 Implementation Plan (explanation) for dopemux documentation and
  developer workflows.
---
# Week 4 Day 2: Implementation Plan
## Task Relationship Mapping - Ready to Build!

**Date**: 2025-10-29
**Status**: ✅ Validated, Analyzed, Ready
**Confidence**: Very High

---

## 🎯 What We're Building Today

**Goal**: Add intelligent task relationship mapping and ADHD-optimized suggestions to DDDPG

**Based on**:
- ✅ WEEK4_DAY2_FINAL_ROADMAP.md (validated architecture)
- ✅ DEEP_ANALYSIS_CURRENT_STATE.md (current state audit)
- ✅ WEEK4_DAY1_COMPLETE.md (foundation complete)

**Estimated Time**: 95 minutes (~1.5 hours)

---

## 📋 Implementation Checklist

### Phase 1: Decision-Task Linking (15 min) ⏱️

**File**: `kg_integration.py` (extend existing DDDPGKG class)

**Tasks**:
- [ ] Add `link_decision_to_task()` method (5 min)
- [ ] Add `get_task_decisions()` method (3 min)
- [ ] Add `unlink_decision_from_task()` method (2 min)
- [ ] Write tests (5 min)

**Code to add**:
```python
# In DDDPGKG class

async def link_decision_to_task(
    self,
    decision_id: str,
    task_id: str,
    relationship_type: str = "DECIDES"
) -> bool:
    """
    Link a DDDPG Decision to a KG Task.

    Args:
        decision_id: Decision identifier
        task_id: Task identifier in KG
        relationship_type: Edge label (default: DECIDES)

    Returns:
        True if linked successfully
    """
    if not self.enable_kg:
        logger.warning("KG disabled, cannot link decision to task")
        return False

    try:
        query = """
        SELECT * FROM cypher('workspace', $$
            MATCH (t:Task {id: $task_id})
            MERGE (d:Decision {id: $decision_id})
            MERGE (d)-[r:DECIDES]->(t)
            RETURN d, r, t
        $$, $params) AS (d agtype, r agtype, t agtype);
        """
        params = {
            'task_id': task_id,
            'decision_id': decision_id
        }
        await self.age_client.execute_query(query, params)
        logger.info(f"✅ Linked decision {decision_id} to task {task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to link decision to task: {e}")
        return False

async def get_task_decisions(
    self,
    task_id: str
) -> List[str]:
    """
    Get all decision IDs linked to a task.

    Args:
        task_id: Task identifier

    Returns:
        List of decision IDs (empty if none or KG disabled)
    """
    if not self.enable_kg:
        return []

    try:
        query = """
        SELECT * FROM cypher('workspace', $$
            MATCH (d:Decision)-[:DECIDES]->(t:Task {id: $task_id})
            RETURN d.id
        $$, $params) AS (decision_id agtype);
        """
        params = {'task_id': task_id}
        results = await self.age_client.execute_query(query, params)
        return [row['decision_id'] for row in results]
    except Exception as e:
        logger.error(f"Failed to get task decisions: {e}")
        return []

async def unlink_decision_from_task(
    self,
    decision_id: str,
    task_id: str
) -> bool:
    """
    Remove Decision→Task link (cleanup).

    Args:
        decision_id: Decision identifier
        task_id: Task identifier

    Returns:
        True if unlinked successfully
    """
    if not self.enable_kg:
        return False

    try:
        query = """
        SELECT * FROM cypher('workspace', $$
            MATCH (d:Decision {id: $decision_id})-[r:DECIDES]->(t:Task {id: $task_id})
            DELETE r
        $$, $params) AS (result agtype);
        """
        params = {
            'decision_id': decision_id,
            'task_id': task_id
        }
        await self.age_client.execute_query(query, params)
        logger.info(f"✅ Unlinked decision {decision_id} from task {task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to unlink decision from task: {e}")
        return False
```

**Tests to add** (in `test_kg_integration.py`):
```python
@pytest.mark.asyncio
async def test_link_decision_to_task():
    """Test linking decision to task"""
    kg = DDDPGKG("/test", age_client=mock_client)
    result = await kg.link_decision_to_task("decision_1", "task_1")
    assert result is True

@pytest.mark.asyncio
async def test_get_task_decisions():
    """Test retrieving task decisions"""
    kg = DDDPGKG("/test", age_client=mock_client)
    decisions = await kg.get_task_decisions("task_1")
    assert isinstance(decisions, list)

@pytest.mark.asyncio
async def test_unlink_decision_from_task():
    """Test unlinking decision from task"""
    kg = DDDPGKG("/test", age_client=mock_client)
    result = await kg.unlink_decision_from_task("decision_1", "task_1")
    assert result is True

@pytest.mark.asyncio
async def test_decision_linking_graceful_degradation():
    """Test graceful degradation when KG disabled"""
    kg = DDDPGKG("/test", enable_kg=False)
    result = await kg.link_decision_to_task("d1", "t1")
    assert result is False
    decisions = await kg.get_task_decisions("t1")
    assert decisions == []
```

---

### Phase 2: Relationship Mapper (25 min) ⏱️

**File**: `relationship_mapper.py` (NEW)

**Tasks**:
- [ ] Create RelationshipMapper class (5 min)
- [ ] Implement `build_task_context()` (10 min)
- [ ] Implement `build_work_cluster()` (7 min)
- [ ] Write tests (3 min)

**Full file content**:
```python
"""
DDDPG Relationship Mapper
Builds composite relationship views from KG queries
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
from .kg_integration import DDDPGKG

logger = logging.getLogger(__name__)

class RelationshipMapper:
    """
    Aggregates multiple DDDPGKG queries into composite views.

    Responsibilities:
- Coordinate parallel queries
- Synthesize relationship data
- Identify task clusters
- Build rich context views
    """

    def __init__(self, kg: DDDPGKG):
        """
        Initialize with KG integration.

        Args:
            kg: DDDPGKG instance for queries
        """
        self.kg = kg

    async def build_task_context(
        self,
        task_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Build complete task context in one call.

        Aggregates:
- Dependencies (upstream/downstream)
- Related tasks (semantic)
- Decisions (rationale)
- Clusters (themes)

        Args:
            task_id: Task identifier
            max_depth: Maximum relationship depth (default 2)

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
                'has_blockers': bool
            }
        """
        if not self.kg.enable_kg:
            return {
                'task_id': task_id,
                'dependencies': {'upstream': [], 'downstream': [], 'parallel': []},
                'related': [],
                'decisions': [],
                'has_blockers': False
            }

        try:
            # Parallel query execution
            deps_task = self.kg.get_task_relationships(task_id)
            related_task = self.kg.get_related_tasks(task_id, limit=5)
            decisions_task = self.kg.get_task_decisions(task_id)

            # Wait for all queries
            deps, related, decisions = await asyncio.gather(
                deps_task,
                related_task,
                decisions_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(deps, Exception):
                logger.error(f"Failed to get dependencies: {deps}")
                deps = {}
            if isinstance(related, Exception):
                logger.error(f"Failed to get related tasks: {related}")
                related = []
            if isinstance(decisions, Exception):
                logger.error(f"Failed to get decisions: {decisions}")
                decisions = []

            # Build context
            return {
                'task_id': task_id,
                'dependencies': {
                    'upstream': deps.get('dependencies', []),
                    'downstream': deps.get('dependents', []),
                    'parallel': []  # TODO: Find sibling tasks
                },
                'related': related,
                'decisions': decisions,
                'has_blockers': len(deps.get('blockers', [])) > 0
            }

        except Exception as e:
            logger.error(f"Failed to build task context: {e}")
            return {
                'task_id': task_id,
                'dependencies': {'upstream': [], 'downstream': [], 'parallel': []},
                'related': [],
                'decisions': [],
                'has_blockers': False
            }

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

        Args:
            theme: Search theme/keyword
            limit: Maximum tasks to return

        Returns:
            {
                'theme': str,
                'tasks': [task_details],
                'decisions': [decision_ids],
                'total_tasks': int
            }
        """
        if not self.kg.enable_kg:
            return {
                'theme': theme,
                'tasks': [],
                'decisions': [],
                'total_tasks': 0
            }

        try:
            # Search for tasks by theme
            tasks = await self.kg.search_tasks(theme, limit=limit)

            # Get decisions for each task (parallel)
            task_ids = [t.get('id') for t in tasks if t.get('id')]
            decision_tasks = [self.kg.get_task_decisions(tid) for tid in task_ids]
            decision_lists = await asyncio.gather(*decision_tasks, return_exceptions=True)

            # Flatten decision lists
            all_decisions = []
            for dlist in decision_lists:
                if not isinstance(dlist, Exception):
                    all_decisions.extend(dlist)

            # Deduplicate decisions
            unique_decisions = list(set(all_decisions))

            return {
                'theme': theme,
                'tasks': tasks,
                'decisions': unique_decisions,
                'total_tasks': len(tasks)
            }

        except Exception as e:
            logger.error(f"Failed to build work cluster: {e}")
            return {
                'theme': theme,
                'tasks': [],
                'decisions': [],
                'total_tasks': 0
            }
```

**Tests** (create `test_relationship_mapper.py`):
```python
"""Tests for RelationshipMapper"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from .relationship_mapper import RelationshipMapper
from .kg_integration import DDDPGKG

@pytest.mark.asyncio
async def test_build_task_context():
    """Test building complete task context"""
    mock_kg = Mock(spec=DDDPGKG)
    mock_kg.enable_kg = True
    mock_kg.get_task_relationships = AsyncMock(return_value={
        'dependencies': ['task_1', 'task_2'],
        'dependents': ['task_3'],
        'blockers': []
    })
    mock_kg.get_related_tasks = AsyncMock(return_value=[
        {'id': 'task_4', 'title': 'Related task'}
    ])
    mock_kg.get_task_decisions = AsyncMock(return_value=['decision_1', 'decision_2'])

    mapper = RelationshipMapper(mock_kg)
    context = await mapper.build_task_context('task_0')

    assert context['task_id'] == 'task_0'
    assert 'dependencies' in context
    assert 'related' in context
    assert 'decisions' in context
    assert context['decisions'] == ['decision_1', 'decision_2']

@pytest.mark.asyncio
async def test_build_work_cluster():
    """Test building work cluster by theme"""
    mock_kg = Mock(spec=DDDPGKG)
    mock_kg.enable_kg = True
    mock_kg.search_tasks = AsyncMock(return_value=[
        {'id': 'task_1', 'title': 'Auth task'},
        {'id': 'task_2', 'title': 'Auth API'}
    ])
    mock_kg.get_task_decisions = AsyncMock(return_value=['decision_1'])

    mapper = RelationshipMapper(mock_kg)
    cluster = await mapper.build_work_cluster('auth', limit=10)

    assert cluster['theme'] == 'auth'
    assert len(cluster['tasks']) == 2
    assert cluster['total_tasks'] == 2

@pytest.mark.asyncio
async def test_graceful_degradation_no_kg():
    """Test graceful degradation when KG disabled"""
    mock_kg = Mock(spec=DDDPGKG)
    mock_kg.enable_kg = False

    mapper = RelationshipMapper(mock_kg)
    context = await mapper.build_task_context('task_0')

    assert context['dependencies'] == {'upstream': [], 'downstream': [], 'parallel': []}
    assert context['related'] == []
    assert context['decisions'] == []
```

---

### Phase 3: Suggestion Engine (35 min) ⏱️

**File**: `suggestion_engine.py` (NEW)

**Tasks**:
- [ ] Create SuggestionEngine class (5 min)
- [ ] Implement `get_enhanced_suggestions()` (10 min)
- [ ] Implement scoring methods (15 min)
- [ ] Write tests (5 min)

**Implementation**: See WEEK4_DAY2_FINAL_ROADMAP.md lines 236-450 for full code

**Key methods**:
```python
class SuggestionEngine:
    async def get_enhanced_suggestions(...) -> Dict
    async def _compute_suggestions(...) -> Dict
    def _score_task(task, context) -> float
    def _energy_score(...) -> float
    def _time_score(...) -> float
    def _focus_score(...) -> float
```

---

### Phase 4: QueryService Integration (20 min) ⏱️

**File**: `queries/service.py` (extend)

**Tasks**:
- [ ] Add KG parameter to `__init__()` (2 min)
- [ ] Add factory method `with_kg()` (3 min)
- [ ] Add `get_task_with_context()` (7 min)
- [ ] Add `suggest_next_tasks()` (5 min)
- [ ] Write integration tests (3 min)

**Code to add**: See WEEK4_DAY2_FINAL_ROADMAP.md lines 468-558

---

## ✅ Definition of Done

**Before marking complete, verify**:

### Functionality
- [ ] Can link decisions to tasks in KG
- [ ] Can build composite relationship views
- [ ] Can generate context-aware suggestions
- [ ] QueryService integrates seamlessly
- [ ] All fallbacks work (graceful degradation)

### Quality
- [ ] All new methods have docstrings
- [ ] Parameterized queries (no string interpolation)
- [ ] Graceful degradation everywhere
- [ ] Test coverage > 90%
- [ ] No breaking changes to existing code

### Performance
- [ ] Decision linking: < 100ms
- [ ] Task context: < 200ms
- [ ] Work cluster: < 300ms
- [ ] Suggestions (cached): < 50ms
- [ ] Suggestions (uncached): < 500ms

### Documentation
- [ ] Update WEEK4_PROGRESS.md with Day 2 completion
- [ ] Add API examples to this file
- [ ] Update README (if needed)

---

## 🚦 Progress Tracking

**Start Time**: _**:**_ UTC
**Phase 1 Complete**: _**:**_ UTC (+15 min)
**Phase 2 Complete**: _**:**_ UTC (+25 min)
**Phase 3 Complete**: _**:**_ UTC (+35 min)
**Phase 4 Complete**: _**:**_ UTC (+20 min)
**Total Time**: ___ minutes

**Blockers**: (note any issues)

---

## 🧪 Testing Strategy

### Unit Tests
- Each phase has dedicated tests
- Mock AGE client for isolation
- Test graceful degradation

### Integration Tests
- QueryService end-to-end
- Full suggestion flow
- Multi-query coordination

### Performance Tests
- Benchmark each method
- Validate SLA targets
- Identify bottlenecks

---

## 📚 References

- **WEEK4_DAY2_FINAL_ROADMAP.md**: Full implementation details
- **DEEP_ANALYSIS_CURRENT_STATE.md**: Current state audit
- **WEEK4_DAY1_COMPLETE.md**: Foundation code
- **ARCHITECTURE_ANALYSIS.md**: Design decisions

---

## 🎯 Let's Build!

**Status**: Ready to implement
**Confidence**: Very High
**Est. Time**: 95 minutes

**Next step**: Start Phase 1 - Decision-Task Linking

---

**Last Updated**: 2025-10-29
**Author**: Implementation Planning Session
