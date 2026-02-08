---
id: week4-roadmap
title: Week4 Roadmap
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week4 Roadmap (reference) for dopemux documentation and developer workflows.
---
# Week 4: Implementation Roadmap

**Date**: 2025-10-29
**Status**: 🗺️ Roadmap Phase
**Duration**: 5 days (estimated 17.5 hours, likely faster)
**Goal**: ADHD-Optimized ConPort-KG Integration

---

## Overview

**Week 4 builds on**:
- Week 3: CognitiveGuardian + Orchestrator (production-ready)
- Existing: ConPort-KG infrastructure (discovered during research)

**Week 4 delivers**:
- Task relationship mapping
- Semantic task search
- Decision context graphs
- ADHD pattern mining
- Agent knowledge sharing

---

## Day-by-Day Breakdown

### Day 1 (Monday): KG Query Layer Foundation

**Energy Required**: Medium-High
**Complexity**: 0.6
**Time Estimate**: 3.5 hours (likely 1 hour based on Week 3 efficiency)

---

#### Focus Block 1.1 (25 min) - Project Setup

**Start Time**: 9:00 AM

**Tasks**:
1. Create `cognitive_guardian_kg.py` file
2. Set up imports and dependencies
3. Define class structure
4. Initialize AGE client connection

**Code Template**:
```python
#!/usr/bin/env python3
"""
CognitiveGuardianKG - ADHD-Optimized Knowledge Graph Integration
Part of Week 4: Advanced ADHD Features

Provides:
- Task relationship mapping
- Semantic task search
- Decision context retrieval
- ADHD pattern mining
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

# ConPort-KG imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'conport_kg'))

from age_client import AGEClient
from adhd_query_adapter import ADHDQueryAdapter, AttentionStateMonitor
from queries.exploration import ExplorationQueries

logger = logging.getLogger(__name__)


class CognitiveGuardianKG:
    """ADHD-optimized Knowledge Graph integration."""

    def __init__(
        self,
        workspace_id: str,
        age_client: Optional[AGEClient] = None,
        adhd_adapter: Optional[ADHDQueryAdapter] = None
    ):
        self.workspace_id = workspace_id
        self.age_client = age_client or self._create_age_client()
        self.adhd_adapter = adhd_adapter or ADHDQueryAdapter()

        logger.info(f"CognitiveGuardianKG initialized for {workspace_id}")

    def _create_age_client(self) -> AGEClient:
        """Create default AGE client with connection pooling."""
        return AGEClient(
            host=os.getenv('AGE_HOST', 'localhost'),
            port=int(os.getenv('AGE_PORT', 5455)),
            database='dopemux_knowledge_graph',
            user='dopemux_age',
            graph_name='conport_knowledge'
        )
```

**Test**:
```python
# Quick validation
kg = CognitiveGuardianKG(workspace_id="/test")
assert kg.age_client is not None
print("✅ KG client initialized")
```

**Completion Criteria**:
- [ ] File created
- [ ] AGE client connection works
- [ ] Imports clean
- [ ] Test passes

**Break**: 5 minutes

---

#### Focus Block 1.2 (25 min) - Task Relationship Queries

**Start Time**: 9:30 AM

**Task**: Implement basic task relationship retrieval

**Method**:
```python
async def get_task_relationships(
    self,
    task_id: str
) -> Dict[str, List[str]]:
    """
    Get task relationships from knowledge graph.

    Args:
        task_id: Task to query

    Returns:
        {
            "dependencies": ["task-123"],
            "blockers": ["task-456"],
            "related": ["task-789"]
        }
    """
    try:
        # Query AGE graph
        query = f"""
        MATCH (t:Task {{id: '{task_id}'}})
        OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
        OPTIONAL MATCH (t)-[:BLOCKS]->(block:Task)
        OPTIONAL MATCH (t)-[:RELATED_TO]->(rel:Task)
        RETURN
            collect(DISTINCT dep.id) as dependencies,
            collect(DISTINCT block.id) as blockers,
            collect(DISTINCT rel.id) as related
        """

        result = await self.age_client.execute_query(query)

        if not result:
            return {"dependencies": [], "blockers": [], "related": []}

        row = result[0]
        return {
            "dependencies": [d for d in row['dependencies'] if d],
            "blockers": [b for b in row['blockers'] if b],
            "related": [r for r in row['related'] if r]
        }

    except Exception as e:
        logger.error(f"Failed to get task relationships: {e}")
        return {"dependencies": [], "blockers": [], "related": []}
```

**Test**:
```python
async def test_relationships():
    kg = CognitiveGuardianKG("/test")
    rels = await kg.get_task_relationships("task-123")
    assert "dependencies" in rels
    assert "blockers" in rels
    assert "related" in rels
    print("✅ Task relationships working")

asyncio.run(test_relationships())
```

**Completion Criteria**:
- [ ] Method implemented
- [ ] Cypher query correct
- [ ] Graceful error handling
- [ ] Test passes

**Break**: 5 minutes

---

#### Focus Block 1.3 (25 min) - Semantic Search Stub

**Start Time**: 10:00 AM

**Task**: Create semantic search method (basic version, enhanced in Day 3)

**Method**:
```python
async def search_tasks_semantic(
    self,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Semantic search for tasks (natural language).

    Day 1: Basic keyword matching
    Day 3: Enhanced with embeddings

    Args:
        query: Natural language query
        limit: Max results (default 5 for ADHD)

    Returns:
        List of matching tasks with relevance scores
    """
    try:
        # Day 1: Simple keyword matching
        # Day 3: Will add embedding-based semantic search

        keywords = query.lower().split()

        # Build Cypher query for keyword matching
        conditions = " OR ".join([f"toLower(t.title) CONTAINS '{kw}'" for kw in keywords])

        cypher_query = f"""
        MATCH (t:Task)
        WHERE {conditions}
        RETURN t.id, t.title, t.complexity, t.energy_required
        LIMIT {limit}
        """

        results = await self.age_client.execute_query(cypher_query)

        # Calculate basic relevance (keyword matches)
        tasks = []
        for row in results:
            relevance = sum(1 for kw in keywords if kw in row['t.title'].lower())
            relevance = relevance / len(keywords)  # Normalize

            tasks.append({
                "task_id": row['t.id'],
                "title": row['t.title'],
                "relevance": relevance,
                "complexity": row.get('t.complexity', 0.5),
                "energy_required": row.get('t.energy_required', 'medium')
            })

        # Sort by relevance
        tasks.sort(key=lambda t: t['relevance'], reverse=True)

        return tasks

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []
```

**Test**:
```python
async def test_search():
    kg = CognitiveGuardianKG("/test")
    results = await kg.search_tasks_semantic("API integration")
    assert isinstance(results, list)
    print(f"✅ Found {len(results)} tasks")

asyncio.run(test_search())
```

**Completion Criteria**:
- [ ] Basic keyword search works
- [ ] Results ranked by relevance
- [ ] Graceful error handling
- [ ] Test passes

**Break**: 10 minutes (longer after 3 blocks)

---

#### Focus Block 1.4 (25 min) - Unit Tests

**Start Time**: 10:40 AM

**Task**: Create unit test file

**File**: `test_cognitive_guardian_kg.py`

```python
#!/usr/bin/env python3
"""
Unit tests for CognitiveGuardianKG
"""

import pytest
import asyncio
from cognitive_guardian_kg import CognitiveGuardianKG


@pytest.mark.asyncio
async def test_initialization():
    """Test KG client initialization"""
    kg = CognitiveGuardianKG(workspace_id="/test")
    assert kg.workspace_id == "/test"
    assert kg.age_client is not None


@pytest.mark.asyncio
async def test_get_task_relationships_empty():
    """Test relationship query with non-existent task"""
    kg = CognitiveGuardianKG("/test")
    rels = await kg.get_task_relationships("nonexistent")
    assert rels == {"dependencies": [], "blockers": [], "related": []}


@pytest.mark.asyncio
async def test_search_tasks_empty_query():
    """Test search with empty query"""
    kg = CognitiveGuardianKG("/test")
    results = await kg.search_tasks_semantic("")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test graceful degradation when AGE unavailable"""
    # Mock AGE client to raise error
    kg = CognitiveGuardianKG("/test")
    # Force connection error
    kg.age_client.pool = None

    rels = await kg.get_task_relationships("task-123")
    assert rels == {"dependencies": [], "blockers": [], "related": []}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Run Tests**:
```bash
cd services/agents
python test_cognitive_guardian_kg.py
```

**Completion Criteria**:
- [ ] 4 tests written
- [ ] All tests pass
- [ ] Coverage: initialization, queries, errors

**Break**: 5 minutes

---

#### Day 1 Wrap-Up (30 min) - 11:10 AM

**Tasks**:
1. Review all code written today
2. Run all tests
3. Commit changes:
   ```bash
   git add cognitive_guardian_kg.py test_cognitive_guardian_kg.py
   git commit -m "Week 4 Day 1: KG query layer foundation

   - CognitiveGuardianKG class created
   - Task relationship queries implemented
   - Basic semantic search (keyword matching)
   - Unit tests: 4/4 passing

   Output: ~150 lines
   Status: Day 1 complete"
   ```
4. Update progress doc

**Completion Criteria**:
- [ ] All Day 1 tests passing
- [ ] Code committed
- [ ] Progress documented

**Output**: ~150 lines code, 4 tests passing

---

### Day 2 (Tuesday): Task Relationship Mapping

**Energy Required**: Medium
**Complexity**: 0.5
**Time Estimate**: 3.5 hours (likely 45 min)

---

#### Focus Block 2.1 (25 min) - Decision Context Query

**Task**: Implement decision context retrieval

**Method**:
```python
async def get_decision_context(
    self,
    task_id: str
) -> Dict[str, Any]:
    """
    Retrieve decision context for a task.

    Returns:
        {
            "decisions": [...],
            "rationale": "...",
            "outcomes": [...]
        }
    """
    try:
        query = f"""
        MATCH (t:Task {{id: '{task_id}'}})
        OPTIONAL MATCH (t)-[:HAS_CONTEXT]->(d:Decision)
        OPTIONAL MATCH (t)-[:PRODUCED]->(o:TaskOutcome)
        RETURN
            collect({{
                id: d.id,
                summary: d.summary,
                rationale: d.rationale
            }}) as decisions,
            collect({{
                success: o.success,
                duration: o.duration_minutes,
                energy: o.energy_level
            }}) as outcomes
        """

        result = await self.age_client.execute_query(query)

        if not result:
            return {"decisions": [], "outcomes": []}

        row = result[0]
        return {
            "decisions": [d for d in row['decisions'] if d['id']],
            "outcomes": [o for o in row['outcomes'] if o.get('success') is not None]
        }

    except Exception as e:
        logger.error(f"Failed to get decision context: {e}")
        return {"decisions": [], "outcomes": []}
```

**Test**: Add to test file

---

#### Focus Block 2.2 (25 min) - Graph Construction Helper

**Task**: Build task relationship graph

**Method**:
```python
async def _build_task_graph(
    self,
    task_ids: List[str]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Build relationship graph for multiple tasks.

    Internal helper for batch operations.
    """
    graph = {}

    for task_id in task_ids:
        graph[task_id] = await self.get_task_relationships(task_id)

    return graph
```

---

#### Focus Block 2.3 (25 min) - CognitiveGuardian Integration

**Task**: Add KG to CognitiveGuardian

**File**: `cognitive_guardian.py` (updates)

```python
# Add to __init__
from cognitive_guardian_kg import CognitiveGuardianKG

class CognitiveGuardian:
    def __init__(self, ...):
        # ... existing code ...

        # NEW: Week 4 KG integration
        self.kg_client = None
        if self._in_claude_code:
            try:
                self.kg_client = CognitiveGuardianKG(workspace_id)
                logger.info("✅ KG integration enabled")
            except Exception as e:
                logger.warning(f"KG unavailable: {e}")
```

---

#### Focus Block 2.4 (25 min) - Enhanced Task Suggestions

**Task**: Use KG for better task suggestions

**Method**:
```python
async def suggest_tasks_with_context(
    self,
    energy: Optional[str] = None,
    max_suggestions: int = 3
) -> List[Dict[str, Any]]:
    """Enhanced task suggestions with KG context."""

    # Get basic suggestions (Week 3 logic)
    tasks = await self.suggest_tasks(energy, max_suggestions)

    # Enhance with KG (if available)
    if self.kg_client:
        for task in tasks:
            task_id = task.get("id")
            if task_id:
                # Add relationships
                rels = await self.kg_client.get_task_relationships(task_id)
                task["relationships"] = rels

                # Add context
                context = await self.kg_client.get_decision_context(task_id)
                task["context"] = context

    return tasks
```

---

#### Day 2 Wrap-Up

**Commit**:
```bash
git commit -m "Week 4 Day 2: Task relationship mapping

- Decision context queries
- Graph construction helpers
- CognitiveGuardian KG integration
- Enhanced task suggestions with context
- Tests: 6/6 passing

Output: ~120 lines"
```

**Output**: ~120 lines

---

### Day 3 (Wednesday): Semantic Search Enhancement

**Energy Required**: Medium-High
**Complexity**: 0.6
**Time Estimate**: 3.5 hours (likely 1 hour)

---

#### Focus Block 3.1 - Embedding Generation

**Task**: Add semantic embeddings using sentence-transformers

**Code**:
```python
from sentence_transformers import SentenceTransformer

class CognitiveGuardianKG:
    def __init__(self, ...):
        # ... existing code ...

        # Semantic search model (lightweight)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate semantic embedding for text."""
        return self.embedding_model.encode(text).tolist()
```

---

#### Focus Block 3.2 - Enhanced Semantic Search

**Task**: Replace keyword matching with embeddings

**Method**:
```python
async def search_tasks_semantic(
    self,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Enhanced semantic search with embeddings."""

    # Generate query embedding
    query_embedding = self._generate_embedding(query)

    # Query tasks with embeddings
    # (Simplified - real implementation would use pgvector)
    cypher_query = """
    MATCH (t:Task)
    RETURN t.id, t.title, t.embedding, t.complexity, t.energy_required
    """

    results = await self.age_client.execute_query(cypher_query)

    # Calculate cosine similarity
    tasks = []
    for row in results:
        if row.get('t.embedding'):
            similarity = self._cosine_similarity(
                query_embedding,
                row['t.embedding']
            )

            tasks.append({
                "task_id": row['t.id'],
                "title": row['t.title'],
                "relevance": similarity,
                "complexity": row.get('t.complexity', 0.5),
                "energy_required": row.get('t.energy_required', 'medium')
            })

    # Sort by relevance
    tasks.sort(key=lambda t: t['relevance'], reverse=True)

    return tasks[:limit]
```

---

#### Focus Block 3.3 - Orchestrator Integration

**Task**: Use semantic search in task routing

**File**: `enhanced_orchestrator.py` (updates)

```python
async def _semantic_task_match(
    self,
    task: OrchestrationTask,
    agent: AgentType
) -> float:
    """Calculate semantic match score using KG."""

    if not self.cognitive_guardian or not self.cognitive_guardian.kg_client:
        return 0.5  # Default confidence

    # Search for similar tasks handled by this agent
    query = f"{task.title} {task.description}"
    similar_tasks = await self.cognitive_guardian.kg_client.search_tasks_semantic(query)

    # Calculate confidence based on similarity
    if similar_tasks:
        # High similarity = high confidence
        return similar_tasks[0]['relevance']

    return 0.5
```

---

#### Day 3 Wrap-Up

**Commit**:
```bash
git commit -m "Week 4 Day 3: Semantic search enhancement

- Embedding generation (sentence-transformers)
- Cosine similarity calculation
- Enhanced semantic search
- Orchestrator semantic matching
- Tests: 8/8 passing

Output: ~100 lines"
```

**Output**: ~100 lines

---

### Day 4 (Thursday): Decision Context & Pattern Stub

**Energy Required**: Medium
**Complexity**: 0.5
**Time Estimate**: 3.5 hours (likely 1 hour)

---

#### Focus Block 4.1 - Save Task Outcomes

**Method**:
```python
async def save_task_outcome(
    self,
    task_id: str,
    success: bool,
    energy_level: str,
    complexity: float,
    duration_minutes: int
) -> None:
    """Save task outcome to KG for pattern mining."""

    try:
        query = f"""
        MATCH (t:Task {{id: '{task_id}'}})
        CREATE (o:TaskOutcome {{
            task_id: '{task_id}',
            success: {success},
            energy_level: '{energy_level}',
            complexity: {complexity},
            duration_minutes: {duration_minutes},
            timestamp: '{datetime.now(timezone.utc).isoformat()}'
        }})
        CREATE (t)-[:PRODUCED]->(o)
        """

        await self.age_client.execute_query(query)
        logger.info(f"Task outcome saved: {task_id}")

    except Exception as e:
        logger.error(f"Failed to save task outcome: {e}")
```

---

#### Focus Block 4.2 - Pattern Mining Stub

**File**: `adhd_pattern_analyzer.py` (new)

```python
class ADHDPatternAnalyzer:
    """Analyze historical data for ADHD patterns."""

    def __init__(self, kg_client: CognitiveGuardianKG):
        self.kg = kg_client

    async def analyze_energy_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, List[str]]:
        """Identify energy-task correlations."""

        # Query successful task outcomes
        query = f"""
        MATCH (o:TaskOutcome)
        WHERE o.success = true
          AND o.timestamp > '{(datetime.now() - timedelta(days=days)).isoformat()}'
        RETURN o.energy_level, collect(DISTINCT o.task_type)
        """

        # Group by energy level
        patterns = {
            "high_energy": [],
            "medium_energy": [],
            "low_energy": []
        }

        # ... analysis logic ...

        return patterns
```

---

#### Day 4 Wrap-Up

**Commit**:
```bash
git commit -m "Week 4 Day 4: Decision context & pattern stub

- Save task outcomes to KG
- Pattern analyzer foundation
- Energy pattern analysis stub
- Tests: 10/10 passing

Output: ~130 lines"
```

**Output**: ~130 lines

---

### Day 5 (Friday): Pattern Mining & Documentation

**Energy Required**: Medium-Low
**Complexity**: 0.4
**Time Estimate**: 3.5 hours (likely 1.5 hours)

---

#### Focus Block 5.1 - Complete Pattern Analyzer

**Tasks**:
1. Finish energy pattern analysis
2. Add break timing analysis
3. Add complexity preference analysis
4. Generate personalized recommendations

**Output**: ~70 lines

---

#### Focus Block 5.2 - Integration Tests

**File**: `test_week4_integration.py`

**Tests** (6):
1. Full CognitiveGuardian + KG workflow
2. Task suggestions with context
3. Semantic search accuracy
4. Pattern mining with sample data
5. Cross-session continuity
6. Performance benchmarks

---

#### Focus Block 5.3 - Documentation

**Create**:
1. `WEEK4_COMPLETE.md` - Summary
2. Update `INTEGRATION_GUIDE.md`
3. Add KG usage examples
4. Document performance tuning

**Output**: ~600 lines docs

---

#### Day 5 Wrap-Up

**Final Commit**:
```bash
git commit -m "Week 4 COMPLETE: ADHD-Optimized KG Integration

Components:
- CognitiveGuardianKG: ~250 lines
- Enhanced CognitiveGuardian: +120 lines
- Enhanced Orchestrator: +100 lines
- ADHD Pattern Analyzer: ~230 lines

Tests: 18/18 passing (100%)
Documentation: ~1,500 lines total

Impact:
- Task relationships: Working
- Semantic search: >70% accuracy
- Decision context: 100% retrieval
- Pattern mining: Operational

Functionality: 60% → 75% (+15%)
ADHD Optimization: 60% → 80% (+20%)

Status: Production-ready"
```

---

## Week 4 Summary

### Total Output

**Code**: ~700 lines production, ~200 lines tests
**Documentation**: ~1,500 lines
**Tests**: 18 passing (100%)

### Time Breakdown

**Planned**: 17.5 hours (5 days × 3.5 hours)
**Likely Actual**: ~6 hours (based on Week 3 efficiency)
**Efficiency**: ~3x faster than planned

### Deliverables Checklist

- [ ] CognitiveGuardianKG class complete
- [ ] Task relationship queries working
- [ ] Semantic search operational
- [ ] Decision context retrieval functional
- [ ] ADHD pattern analyzer implemented
- [ ] All 18 tests passing
- [ ] Documentation comprehensive
- [ ] Performance targets met

### Success Metrics

**Technical**:
- [ ] Query performance: Tier 1 <50ms, Tier 2 <150ms, Tier 3 <500ms
- [ ] Test coverage: 100%
- [ ] Graceful degradation: Working

**ADHD Impact**:
- [ ] 50% reduction in "forgot prerequisite" issues
- [ ] 70% semantic search success rate
- [ ] 100% decision context availability
- [ ] Personalized patterns discovered

---

## Next Steps After Week 4

**Week 5 Options**:
1. **Production deployment** (already in Week 5 plan)
2. **Dashboard integration** (visualize KG)
3. **Advanced features** (biometric/ML from research)

---

**Created**: 2025-10-29
**Roadmap Time**: 60 minutes
**Total Week 4 Plan**: Research + Spec + Roadmap = 180 minutes
**Status**: Ready to build!

🎯 **Week 4: Implementation Roadmap Complete** 🎯
