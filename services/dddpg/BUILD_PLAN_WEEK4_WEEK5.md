# DDDPG: Week 4 Day 2 → Week 5 Build Plan
**Service**: DDDPG (Decision-Driven Development Planning Graph)  
**Created**: 2025-10-29  
**Status**: Ready to Execute  
**Session Type**: Implementation Roadmap

---

## 🎯 Overview

This document provides the **actionable build plan** for completing DDDPG modernization from Week 4 Day 2 through Week 5.

**Timeline**: 1.5-2 weeks (at 3.5x velocity) or 3-4 weeks (at normal velocity)

**Current Status**: Week 4 Day 1 complete ✅, Day 2 ready to build 🚀

---

## 📅 Week 4 Day 2: Relationship Intelligence (TODAY)

### Time Estimate
- **Normal Velocity**: 95 minutes (~1.5 hours)
- **At 3.5x Velocity**: ~25 minutes
- **Realistic**: 30-45 minutes (accounting for context switching)

### Phase 1: Decision-Task Linking (15 min → ~4 min)

**File to Edit**: `kg_integration.py`

**What to Add**: Extend the `DDDPGKG` class with 3 new methods

**Method 1**: `link_decision_to_task()`
```python
async def link_decision_to_task(
    self,
    decision_id: str,
    task_id: str,
    relationship_type: str = "DECIDES"
) -> bool:
    """
    Link a DDDPG Decision to a KG Task.
    
    Args:
        decision_id: Decision identifier (e.g., "decision_123")
        task_id: Task identifier in KG (e.g., "task_456")
        relationship_type: Edge label (default: "DECIDES")
    
    Returns:
        True if linked successfully, False otherwise
    
    Example:
        >>> await kg.link_decision_to_task("decision_42", "task_auth_impl")
        True
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
```

**Method 2**: `get_task_decisions()`
```python
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
    
    Example:
        >>> await kg.get_task_decisions("task_auth_impl")
        ["decision_42", "decision_43"]
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
        
        # Parse results (AGE returns JSON-like strings)
        decision_ids = [self._parse_id(row[0]) for row in results]
        return decision_ids
    except Exception as e:
        logger.error(f"Failed to get task decisions: {e}")
        return []
```

**Method 3**: `unlink_decision_from_task()`
```python
async def unlink_decision_from_task(
    self,
    decision_id: str,
    task_id: str
) -> bool:
    """
    Remove Decision→Task edge (cleanup/undo).
    
    Args:
        decision_id: Decision identifier
        task_id: Task identifier
    
    Returns:
        True if unlinked successfully
    
    Example:
        >>> await kg.unlink_decision_from_task("decision_42", "task_auth_impl")
        True
    """
    if not self.enable_kg:
        logger.warning("KG disabled, cannot unlink decision from task")
        return False
    
    try:
        query = """
        SELECT * FROM cypher('workspace', $$
            MATCH (d:Decision {id: $decision_id})-[r:DECIDES]->(t:Task {id: $task_id})
            DELETE r
            RETURN COUNT(r) as deleted
        $$, $params) AS (deleted agtype);
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

**Tests to Add**: In `test_kg_integration.py`
```python
@pytest.mark.asyncio
async def test_link_decision_to_task():
    kg = DDDPGKG(workspace_id="/test", enable_kg=False)
    result = await kg.link_decision_to_task("d1", "t1")
    assert result == False  # KG disabled

@pytest.mark.asyncio
async def test_get_task_decisions_empty():
    kg = DDDPGKG(workspace_id="/test", enable_kg=False)
    result = await kg.get_task_decisions("t1")
    assert result == []  # KG disabled

@pytest.mark.asyncio
async def test_unlink_decision_from_task():
    kg = DDDPGKG(workspace_id="/test", enable_kg=False)
    result = await kg.unlink_decision_from_task("d1", "t1")
    assert result == False  # KG disabled

# With mocked AGE client:
@pytest.mark.asyncio
async def test_link_decision_to_task_with_mock():
    mock_client = MockAGEClient()
    kg = DDDPGKG(workspace_id="/test", age_client=mock_client, enable_kg=True)
    result = await kg.link_decision_to_task("d1", "t1")
    assert result == True
    assert mock_client.last_query.startswith("SELECT * FROM cypher")
```

**Completion Criteria**:
- ✅ 3 methods added to `DDDPGKG`
- ✅ 4-5 tests passing
- ✅ All queries parameterized (security check)

---

### Phase 2: RelationshipMapper (25 min → ~7 min)

**File to Create**: `relationship_mapper.py`

**Purpose**: Aggregate multiple KG queries into composite context views

**Full Implementation**:
```python
#!/usr/bin/env python3
"""
DDDPG Relationship Mapper - Composite KG Views
Week 4 Day 2: Aggregation layer on top of DDDPGKG primitives

Provides:
- Task context (dependencies, related, decisions, clusters)
- Work clusters (theme-based task grouping)
- Parallel query execution for performance
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from .kg_integration import DDDPGKG

logger = logging.getLogger(__name__)


class RelationshipMapper:
    """
    Aggregate multiple KG queries into composite views.
    
    Architecture:
    - Parallel query execution (asyncio.gather)
    - Data synthesis (merge results from multiple queries)
    - Graceful degradation (partial results OK)
    """
    
    def __init__(self, kg: DDDPGKG):
        """
        Initialize with KG integration layer.
        
        Args:
            kg: DDDPGKG instance (already initialized)
        """
        self.kg = kg
    
    async def build_task_context(
        self,
        task_id: str,
        include_decisions: bool = True,
        include_dependencies: bool = True,
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Build comprehensive task context from multiple KG queries.
        
        Args:
            task_id: Task identifier
            include_decisions: Include linked decisions
            include_dependencies: Include blocking tasks
            include_related: Include similar/related tasks
        
        Returns:
            {
                "task_id": str,
                "dependencies": List[str],     # Blocking task IDs
                "related": List[Dict],         # Related tasks
                "decisions": List[str],        # Decision IDs
                "clusters": List[str],         # Theme clusters
                "context_complete": bool       # All queries succeeded
            }
        
        Example:
            >>> mapper = RelationshipMapper(kg)
            >>> context = await mapper.build_task_context("task_auth_impl")
            >>> print(context["dependencies"])
            ["task_db_setup", "task_user_model"]
        """
        logger.info(f"Building context for task {task_id}")
        
        # Parallel query execution
        queries = []
        
        if include_dependencies:
            queries.append(self.kg.get_task_relationships(task_id))
        
        if include_related:
            # Search for semantically related tasks
            # (Assume task has a summary field we can search with)
            queries.append(self.kg.search_tasks_semantic(f"related to {task_id}", limit=5))
        
        if include_decisions:
            queries.append(self.kg.get_task_decisions(task_id))
        
        # Execute all queries in parallel
        try:
            results = await asyncio.gather(*queries, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in parallel queries: {e}")
            results = [None] * len(queries)
        
        # Unpack results
        idx = 0
        dependencies = []
        related = []
        decisions = []
        
        if include_dependencies:
            dep_result = results[idx]
            if not isinstance(dep_result, Exception) and dep_result:
                dependencies = dep_result.get("dependencies", [])
            idx += 1
        
        if include_related:
            rel_result = results[idx]
            if not isinstance(rel_result, Exception) and rel_result:
                related = rel_result
            idx += 1
        
        if include_decisions:
            dec_result = results[idx]
            if not isinstance(dec_result, Exception) and dec_result:
                decisions = dec_result
            idx += 1
        
        # Identify theme clusters (simple approach: extract from task IDs)
        clusters = self._identify_clusters([task_id] + dependencies)
        
        context_complete = all(not isinstance(r, Exception) for r in results)
        
        return {
            "task_id": task_id,
            "dependencies": dependencies,
            "related": related,
            "decisions": decisions,
            "clusters": clusters,
            "context_complete": context_complete
        }
    
    async def build_work_cluster(
        self,
        theme: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Build cluster of related work around a theme.
        
        Args:
            theme: Theme keyword (e.g., "authentication", "database")
            limit: Max tasks to return
        
        Returns:
            {
                "theme": str,
                "tasks": List[Dict],        # Related tasks
                "decisions": List[str],     # Theme-related decisions
                "patterns": List[str]       # Common patterns (future)
            }
        
        Example:
            >>> cluster = await mapper.build_work_cluster("authentication", limit=10)
            >>> print(len(cluster["tasks"]))
            10
        """
        logger.info(f"Building work cluster for theme: {theme}")
        
        # Parallel queries
        tasks_future = self.kg.search_tasks_semantic(theme, limit=limit)
        
        # Execute
        try:
            tasks = await tasks_future
        except Exception as e:
            logger.error(f"Error building work cluster: {e}")
            tasks = []
        
        # Extract decision IDs from tasks (if they have them)
        decisions = []
        for task in tasks:
            task_decisions = await self.kg.get_task_decisions(task.get("id", ""))
            decisions.extend(task_decisions)
        
        # Remove duplicates
        decisions = list(set(decisions))
        
        # Patterns (placeholder for future ML)
        patterns = []
        
        return {
            "theme": theme,
            "tasks": tasks,
            "decisions": decisions,
            "patterns": patterns
        }
    
    def _identify_clusters(self, task_ids: List[str]) -> List[str]:
        """
        Identify theme clusters from task IDs.
        
        Simple approach: Extract common prefixes (e.g., "task_auth_*")
        Future: Use ML clustering on embeddings
        
        Args:
            task_ids: List of task identifiers
        
        Returns:
            List of cluster themes
        """
        if not task_ids:
            return []
        
        # Extract prefixes (simple heuristic)
        prefixes = set()
        for task_id in task_ids:
            parts = task_id.split("_")
            if len(parts) >= 2:
                # Take first 2 parts as cluster (e.g., "task_auth")
                prefix = "_".join(parts[:2])
                prefixes.add(prefix)
        
        return list(prefixes)
```

**Tests to Add**: `test_relationship_mapper.py`
```python
import pytest
from relationship_mapper import RelationshipMapper
from kg_integration import DDDPGKG

@pytest.mark.asyncio
async def test_build_task_context_basic():
    kg = DDDPGKG(workspace_id="/test", enable_kg=False)
    mapper = RelationshipMapper(kg)
    
    context = await mapper.build_task_context("task_1")
    
    assert context["task_id"] == "task_1"
    assert "dependencies" in context
    assert "related" in context
    assert "decisions" in context
    assert "clusters" in context

@pytest.mark.asyncio
async def test_build_work_cluster():
    kg = DDDPGKG(workspace_id="/test", enable_kg=False)
    mapper = RelationshipMapper(kg)
    
    cluster = await mapper.build_work_cluster("auth")
    
    assert cluster["theme"] == "auth"
    assert "tasks" in cluster
    assert "decisions" in cluster

@pytest.mark.asyncio
async def test_identify_clusters():
    kg = DDDPGKG(workspace_id="/test", enable_kg=False)
    mapper = RelationshipMapper(kg)
    
    task_ids = ["task_auth_login", "task_auth_signup", "task_db_setup"]
    clusters = mapper._identify_clusters(task_ids)
    
    assert "task_auth" in clusters
    assert "task_db" in clusters
```

**Completion Criteria**:
- ✅ `relationship_mapper.py` created
- ✅ `RelationshipMapper` class implemented
- ✅ 5-6 tests passing
- ✅ Parallel query execution working

---

### Phase 3: SuggestionEngine (35 min → ~10 min)

**File to Create**: `suggestion_engine.py`

**Purpose**: ADHD-optimized task suggestions matching cognitive state

**Full Implementation**: (See comprehensive analysis document for complete code - ~200 lines)

**Key Features**:
- Context-aware scoring (energy, time, focus)
- Dependency satisfaction checking
- In-memory caching (5 min TTL)
- Pattern matching (future)

**Completion Criteria**:
- ✅ `suggestion_engine.py` created
- ✅ `SuggestionEngine` class implemented
- ✅ Scoring algorithm working
- ✅ 8-10 tests passing
- ✅ Cache invalidation working

---

### Phase 4: QueryService Integration (20 min → ~6 min)

**File to Edit**: `queries/service.py`

**Changes**: Add optional KG integration, new methods

**Completion Criteria**:
- ✅ `__init__` accepts optional `kg` parameter
- ✅ `get_task_with_context()` method added
- ✅ `suggest_next_tasks()` method added
- ✅ Graceful fallbacks implemented
- ✅ 4-5 integration tests passing

---

## 📅 Week 4 Days 3-4: Semantic Search (~3 hours)

### Phase 1: Embedding Generation (1 hour)

**Library**: `sentence-transformers`

**Model**: `all-MiniLM-L6-v2` (small, fast, good quality)

**Implementation**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> List[float]:
    """Generate 384-dim embedding vector."""
    return model.encode(text).tolist()

async def embed_decisions_batch(decisions: List[Decision]):
    """Batch process decisions for embeddings."""
    texts = [f"{d.summary} {d.rationale}" for d in decisions]
    embeddings = model.encode(texts, batch_size=32)
    
    for decision, embedding in zip(decisions, embeddings):
        await storage.store_embedding(decision.id, embedding.tolist())
```

**Storage**: Add `embedding` column to decisions table (ARRAY or JSONB)

### Phase 2: Vector Similarity Search (1.5 hours)

**Query**:
```python
async def semantic_search(
    query: str,
    limit: int = 10
) -> List[Decision]:
    """Search by semantic similarity."""
    query_embedding = generate_embedding(query)
    
    # Cosine similarity query
    # (Postgres: use pgvector extension, or compute in Python)
    results = await storage.search_by_embedding(query_embedding, limit)
    return results
```

**Options**:
1. PostgreSQL `pgvector` extension (best for production)
2. Python cosine similarity (simpler, slower)

### Phase 3: Hybrid Search (30 min)

**Combine**: FTS5 (keyword) + embeddings (semantic)

```python
async def hybrid_search(
    query: str,
    limit: int = 10
) -> List[Decision]:
    """Weighted hybrid search."""
    # Parallel execution
    keyword_results = await fts5_search(query, limit=limit*2)
    semantic_results = await semantic_search(query, limit=limit*2)
    
    # Weighted scoring
    scores = {}
    for result in keyword_results:
        scores[result.id] = scores.get(result.id, 0) + 0.3 * result.score
    for result in semantic_results:
        scores[result.id] = scores.get(result.id, 0) + 0.7 * result.score
    
    # Sort and return top K
    top_ids = sorted(scores, key=scores.get, reverse=True)[:limit]
    return await storage.get_decisions_by_ids(top_ids)
```

---

## 📅 Week 4 Day 5: EventBus Integration (~2 hours)

### Events to Publish

**File to Edit**: `storage/sqlite_backend.py` (or create `events.py`)

```python
from dopemux.eventbus import EventBus

class DDDPGEventPublisher:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
    
    async def publish_decision_created(self, decision: Decision):
        await self.bus.publish("dddpg.decision.created", {
            "decision_id": decision.id,
            "workspace_id": decision.workspace_id,
            "instance_id": decision.instance_id,
            "decision_type": decision.decision_type.value,
            "summary": decision.summary,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_decision_updated(self, decision: Decision):
        await self.bus.publish("dddpg.decision.updated", {...})
    
    async def publish_decision_superseded(self, old_id: int, new_id: int):
        await self.bus.publish("dddpg.decision.superseded", {
            "old_decision_id": old_id,
            "new_decision_id": new_id,
            "timestamp": datetime.utcnow().isoformat()
        })
```

### Events to Subscribe

```python
class DDDPGEventSubscriber:
    def __init__(self, dddpg_service):
        self.service = dddpg_service
    
    async def on_task_completed(self, event):
        """Link decision to completed task."""
        if "decision_id" in event and "task_id" in event:
            await self.service.link_decision_to_task(
                event["decision_id"],
                event["task_id"]
            )
    
    async def on_session_ended(self, event):
        """Archive session decisions."""
        session_id = event.get("session_id")
        await self.service.archive_session_decisions(session_id)
```

---

## 📅 Week 5 Days 1-2: Hybrid Storage (~4 hours)

### Architecture

```
PostgresAGEBackend (source of truth)
         ↓
    EventBus (sync notifications)
         ↓
SQLiteBackend (per-instance cache)
```

### Implementation

**File to Create**: `storage/postgres_age_backend.py`

**File to Create**: `storage/hybrid_backend.py`

**Cache Sync Logic**:
```python
class HybridBackend:
    def __init__(self, postgres: PostgresAGEBackend, sqlite: SQLiteBackend, event_bus: EventBus):
        self.postgres = postgres
        self.sqlite = sqlite
        self.bus = event_bus
        
        # Subscribe to cache invalidation events
        self.bus.subscribe("dddpg.decision.updated", self.invalidate_cache)
    
    async def create_decision(self, decision: Decision) -> int:
        # Write to Postgres (source of truth)
        decision_id = await self.postgres.create_decision(decision)
        
        # Update local cache
        await self.sqlite.create_decision(decision)
        
        # Publish event (other instances will update their caches)
        await self.bus.publish("dddpg.decision.created", {"decision_id": decision_id})
        
        return decision_id
    
    async def get_decision(self, decision_id: int) -> Optional[Decision]:
        # Try cache first
        decision = await self.sqlite.get_decision(decision_id)
        if decision:
            return decision
        
        # Fallback to Postgres
        decision = await self.postgres.get_decision(decision_id)
        if decision:
            # Update cache
            await self.sqlite.create_decision(decision)
        
        return decision
    
    async def invalidate_cache(self, event):
        # Remove from local cache (will be refetched from Postgres next time)
        await self.sqlite.delete_decision(event["decision_id"])
```

---

## 📅 Week 5 Days 3-5: Agents & Dashboard (~6 hours)

### Serena (LSP) Integration (1 hour)

**File**: `integration/serena_integration.py`

```python
async def on_hover(task_id: str) -> str:
    """Generate hover text for task."""
    context = await dddpg.get_task_with_context(task_id)
    
    return f"""
Task: {context['task']['summary']}

Decisions: {len(context['decisions'])} related
Dependencies: {len(context['dependencies'])} blocking
Cognitive Load: {context['task'].get('cognitive_load', 'N/A')}/5

Related Tasks:
{format_tasks(context['related'][:3])}
"""
```

### Task-Orchestrator Integration (1 hour)

**File**: `integration/task_orchestrator_integration.py`

```python
async def on_task_created(task: Task):
    """Create decision for new task."""
    decision = Decision(
        summary=f"Implement: {task.name}",
        decision_type=DecisionType.IMPLEMENTATION,
        workspace_id=task.workspace_id,
        instance_id=task.instance_id,
        agent_metadata={
            "task_orchestrator": {
                "task_id": task.id,
                "priority": task.priority,
                "estimated_time_mins": task.estimated_time
            }
        }
    )
    decision_id = await dddpg.create_decision(decision)
    await dddpg.link_decision_to_task(decision_id, task.id)
```

### Dashboard Components (3 hours)

**File**: `dashboard/components/DecisionTimeline.tsx`

```typescript
import React from 'react';
import { useQuery } from 'react-query';
import { api } from '../api';

export const DecisionTimeline: React.FC = () => {
  const { data, isLoading } = useQuery('decisions', () =>
    api.dddpg.overview({ limit: 3 })
  );
  
  if (isLoading) return <Spinner />;
  
  return (
    <div className="decision-timeline">
      <h2>Recent Decisions</h2>
      {data.map(decision => (
        <DecisionCard key={decision.id} decision={decision} />
      ))}
    </div>
  );
};
```

**File**: `dashboard/components/TaskSuggestions.tsx`

```typescript
export const TaskSuggestions: React.FC<{
  energyLevel: string;
  availableTime: number;
}> = ({ energyLevel, availableTime }) => {
  const { data } = useQuery(
    ['suggestions', energyLevel, availableTime],
    () => api.dddpg.suggestNextTasks({ energyLevel, availableTime })
  );
  
  return (
    <div className="task-suggestions">
      <h2>Suggested Tasks</h2>
      {data?.suggestions.map(suggestion => (
        <SuggestionCard
          key={suggestion.task.id}
          task={suggestion.task}
          score={suggestion.score}
          reasons={suggestion.reasons}
        />
      ))}
    </div>
  );
};
```

---

## ✅ Completion Checklist

### Week 4 Day 2
- [ ] Phase 1: Decision-Task Linking (3 methods added, 4-5 tests)
- [ ] Phase 2: RelationshipMapper (class created, 5-6 tests)
- [ ] Phase 3: SuggestionEngine (class created, 8-10 tests)
- [ ] Phase 4: QueryService Integration (methods added, 4-5 tests)
- [ ] All tests passing (target: 40+ total tests)
- [ ] Documentation updated (Week 4 Day 2 marked complete)

### Week 4 Days 3-4
- [ ] Embedding generation working
- [ ] Vector similarity search working
- [ ] Hybrid search working
- [ ] Tests passing (10+ semantic search tests)

### Week 4 Day 5
- [ ] EventBus integration complete
- [ ] Events publishing correctly
- [ ] Event subscribers working
- [ ] Tests passing (5+ event tests)

### Week 5 Days 1-2
- [ ] PostgresAGEBackend implemented
- [ ] HybridBackend implemented
- [ ] Cache sync working
- [ ] Tests passing (15+ hybrid storage tests)

### Week 5 Days 3-5
- [ ] Serena integration working
- [ ] Task-Orchestrator integration working
- [ ] Zen integration working
- [ ] Dashboard components rendering
- [ ] API routes working
- [ ] End-to-end tests passing

---

## 🎯 Success Metrics

### Technical Metrics
- ✅ Test coverage: > 90%
- ✅ All queries parameterized: 100%
- ✅ Performance SLAs met: < 500ms P95
- ✅ Zero security vulnerabilities

### Development Metrics
- ✅ Velocity: Maintain 2-3x speed
- ✅ Code quality: No complexity warnings
- ✅ Documentation: Updated concurrently

### User Metrics (Post-Launch)
- ✅ Time to decision: < 2 min
- ✅ Context recovery: < 1 min
- ✅ Feature adoption: > 60% within 1 week

---

## 📞 Support & Resources

### Technical Questions
- See: `2025_COMPREHENSIVE_ANALYSIS_AND_PLAN.md`
- See: `2025_TECHNICAL_SPEC.md`

### Architecture Questions
- See: `2025_MODERNIZATION_ROADMAP.md`
- See: `ARCHITECTURE_ANALYSIS.md`

### Implementation Help
- See: `WEEK4_DAY2_IMPLEMENTATION_PLAN.md`
- Run: `pytest -v` to see test examples

---

**Status**: READY TO BUILD 🚀  
**Next Step**: Start Week 4 Day 2 Phase 1  
**Let's ship it!** 🎯
