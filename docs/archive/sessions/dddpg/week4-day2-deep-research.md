---
id: week4-day2-deep-research
title: Week4 Day2 Deep Research
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week4 Day2 Deep Research (explanation) for dopemux documentation and developer
  workflows.
---
# Week 4 Day 2: Deep Research & Planning
## Task Relationship Mapping - Architecture Analysis

**Date**: 2025-10-29
**Focus**: Decision context, graph construction, enhanced suggestions
**Approach**: Research → Think → Plan → Build

---

## 🧠 Research Phase (30 min estimate)

### 1. Current State Analysis

**What we have (Day 1)**:
- `DDDPGKG.get_task_relationships()` - Query relationships from KG
- `DDDPGKG.search_tasks_semantic()` - Find related tasks
- Basic structure for task queries

**What we need (Day 2)**:
- Decision context tracking ("why did I do this?")
- Graph construction helpers (build relationship maps)
- Enhanced task suggestions (use relationships for better recommendations)
- Integration with DDDPG core

### 2. Key Questions to Research

#### Q1: What is a "decision context" in ADHD workflow?

**ADHD Challenge**: Forgetting "why" decisions were made
- Lost context after interruptions
- Difficulty resuming work after breaks
- Forgotten reasoning when returning to tasks

**What to track**:
```python
{
    "task_id": "task-123",
    "decision": "Chose FastAPI over Flask",
    "reasoning": [
        "Better async support",
        "OpenAPI auto-generation",
        "Team preference"
    ],
    "alternatives_considered": ["Flask", "Django"],
    "context": {
        "session_id": "sess-456",
        "timestamp": "2025-10-29T10:00:00Z",
        "energy_level": "high",
        "focus_state": "flow"
    }
}
```

**KG Representation**:
```cypher
# Decision node
(d:Decision {
    id: "dec-123",
    task_id: "task-123",
    decision: "Chose FastAPI over Flask",
    timestamp: datetime()
})

# Reasoning edges
(d)-[:REASONED_BY {text: "Better async support", weight: 0.9}]->(r1:Reason)
(d)-[:REASONED_BY {text: "OpenAPI auto-gen", weight: 0.7}]->(r2:Reason)

# Alternative edges
(d)-[:CONSIDERED {rejected: true}]->(alt1:Alternative {name: "Flask"})
(d)-[:CONSIDERED {rejected: true}]->(alt2:Alternative {name: "Django"})

# Context edges
(d)-[:MADE_IN]->(s:Session {id: "sess-456"})
(d)-[:AT_ENERGY_LEVEL]->(e:EnergyLevel {level: "high"})
```

#### Q2: What graph construction helpers are most valuable?

**Use Cases**:

1. **Dependency Chain**:
   - "What needs to happen before Task X?"
   - "What's blocked by Task Y?"

2. **Related Work Cluster**:
   - "What other tasks involve API design?"
   - "Show me all authentication-related work"

3. **Decision History**:
   - "Why did I choose this approach?"
   - "What alternatives did I consider?"

4. **Success Pattern**:
   - "What worked well last time I did X?"
   - "What mistakes should I avoid?"

**Graph Patterns**:
```python
# Pattern 1: Full dependency chain
def build_dependency_chain(task_id: str) -> Dict:
    """
    Returns: {
        'upstream': [task-1, task-2],      # Must complete first
        'downstream': [task-5, task-6],    # Blocked on this
        'parallel': [task-3, task-4]       # Can do concurrently
    }
    """

# Pattern 2: Related work cluster
def build_work_cluster(theme: str) -> Dict:
    """
    Returns: {
        'tasks': [...],
        'decisions': [...],
        'patterns': [...]
    }
    """

# Pattern 3: Decision tree
def build_decision_tree(task_id: str) -> Dict:
    """
    Returns: {
        'decisions': [...],
        'alternatives': [...],
        'outcomes': [...]
    }
    """
```

#### Q3: How do we enhance task suggestions?

**Current** (Day 1):
```python
# Basic keyword matching
results = await kg.search_tasks_semantic("API integration")
# Returns: tasks with "API" or "integration" in description
```

**Enhanced** (Day 2):
```python
# Context-aware suggestions
suggestions = await kg.get_enhanced_suggestions(
    current_task="task-123",
    energy_level="medium",
    available_time_mins=30,
    focus_state="scattered"
)

# Returns:
{
    'next_best_tasks': [
        {
            'task': 'task-125',
            'reason': 'Builds on current work',
            'dependency_satisfied': True,
            'estimated_time': 20,
            'energy_match': 0.95
        }
    ],
    'quick_wins': [...],      # < 15 min, low energy
    'related_decisions': [...], # "You chose X for similar work"
    'patterns_to_reuse': [...]  # "This worked before"
}
```

**Algorithm**:
1. Get current task context (energy, focus, time)
2. Query KG for:
   - Tasks with satisfied dependencies
   - Similar past tasks (success patterns)
   - Related decisions (avoid re-thinking)
3. Score by:
   - Energy level match
   - Time availability
   - Focus state compatibility
   - Success pattern similarity
4. Return ranked suggestions

### 3. Integration with DDDPG Core

**Check existing DDDPG structure**:
```bash
services/dddpg/
├── core/
│   ├── config.py       # Configuration
│   ├── models.py       # Data models
│   └── __init__.py
├── queries/
│   ├── service.py      # Query service
│   └── __init__.py
├── storage/
│   ├── interface.py    # Storage interface
│   ├── sqlite_backend.py
│   └── __init__.py
└── kg_integration.py   # Our Day 1 work
```

**Integration Points**:
1. `queries/service.py` - Add KG-powered queries
2. `core/models.py` - Add Decision/Context models
3. `storage/interface.py` - Add KG storage backend option

---

## 🎯 Key Decisions to Make

### Decision 1: Where to store decision context?

**Options**:
- **A**: PostgreSQL (existing DDDPG storage)
- **B**: Apache AGE (graph-native)
- **C**: Both (PG for data, AGE for relationships)

**Analysis**:
- **A**: Simple, existing infrastructure, no new dependencies
  - ❌ Relationship queries are slow
  - ❌ Graph traversals require multiple JOINs

- **B**: Optimal for graph queries, natural fit
  - ❌ Requires AGE setup
  - ❌ Separate from other DDDPG data

- **C**: Best of both worlds
  - ✅ Fast queries
  - ✅ Data consistency
  - ✅ Graph traversals
  - ⚠️  More complex

**Recommendation**: **C (Hybrid)** - Store in PostgreSQL, index in AGE

### Decision 2: Graph construction - incremental or batch?

**Options**:
- **A**: Incremental (build graph on-demand)
- **B**: Batch (pre-compute graphs periodically)
- **C**: Hybrid (cache + update)

**Analysis**:
- **A**: Always fresh, simple
  - ❌ Slow for large graphs
  - ❌ Repeated computation

- **B**: Fast queries, pre-computed
  - ❌ Stale data
  - ❌ Memory intensive

- **C**: Best of both
  - ✅ Fast common queries (cached)
  - ✅ Fresh data (incremental updates)
  - ⚠️  Cache invalidation complexity

**Recommendation**: **C (Hybrid)** - Cache common graphs, update incrementally

### Decision 3: Suggestion scoring - simple or ML?

**Options**:
- **A**: Rule-based (if/then logic)
- **B**: ML-based (learned patterns)
- **C**: Hybrid (rules + ML)

**Analysis**:
- **A**: Simple, predictable, debuggable
  - ✅ No training needed
  - ✅ Fast
  - ❌ Less adaptive

- **B**: Learns user preferences
  - ❌ Requires training data
  - ❌ Complex
  - ❌ Black box

- **C**: Rules for safety, ML for personalization
  - ✅ Best of both
  - ⚠️  More complex

**Recommendation**: **A (Rule-based)** for Week 4 - Keep it simple, proven patterns

### Decision 4: API surface - methods vs service class?

**Options**:
- **A**: Add methods to `DDDPGKG`
- **B**: Create `DDDPGRelationshipService`
- **C**: Create `DDDPGSuggestionEngine`

**Analysis**:
- **A**: Simple, cohesive
  - ⚠️  Class growing large
  - ⚠️  Mixed responsibilities

- **B**: Separate concerns
  - ✅ Single responsibility
  - ✅ Easier testing
  - ⚠️  More files

- **C**: Domain-specific
  - ✅ Clear purpose
  - ✅ Reusable
  - ⚠️  More classes

**Recommendation**: **A for now** - Add to `DDDPGKG`, refactor later if needed

### Decision 5: Graceful degradation strategy?

**Scenarios**:
1. AGE unavailable → Fall back to keyword search
2. No decision history → Return empty context
3. No relationships → Suggest by recency

**Strategy**:
```python
async def get_enhanced_suggestions(self, ...):
    if not self.enable_kg:
        # Fallback: use recency + keyword matching
        return self._fallback_suggestions(...)

    try:
        # Try KG-powered suggestions
        return await self._kg_suggestions(...)
    except Exception as e:
        logger.error(f"KG suggestions failed: {e}")
        return self._fallback_suggestions(...)
```

**Recommendation**: Same pattern as Day 1 - graceful everywhere

---

## 📋 Implementation Plan

### Phase 1: Decision Context (25 min)

**Tasks**:
1. Add `save_decision_context()` method (10 min)
2. Add `get_decision_context()` method (10 min)
3. Add tests (5 min)

**API Design**:
```python
async def save_decision_context(
    self,
    task_id: str,
    decision: str,
    reasoning: List[str],
    alternatives: Optional[List[str]] = None,
    context: Optional[Dict] = None
) -> str:
    """Save decision context to KG."""
    # Returns: decision_id

async def get_decision_context(
    self,
    task_id: str
) -> List[Dict]:
    """Get decision history for task."""
    # Returns: list of decisions with full context
```

### Phase 2: Graph Construction (25 min)

**Tasks**:
1. Add `build_dependency_chain()` (10 min)
2. Add `build_work_cluster()` (10 min)
3. Add tests (5 min)

**API Design**:
```python
async def build_dependency_chain(
    self,
    task_id: str,
    max_depth: int = 3
) -> Dict[str, List[str]]:
    """Build dependency chain for task."""
    # Returns: {upstream, downstream, parallel}

async def build_work_cluster(
    self,
    theme: str,
    limit: int = 20
) -> Dict[str, List[Dict]]:
    """Build cluster of related work."""
    # Returns: {tasks, decisions, patterns}
```

### Phase 3: Enhanced Suggestions (25 min)

**Tasks**:
1. Add `get_enhanced_suggestions()` (15 min)
2. Add scoring logic (5 min)
3. Add tests (5 min)

**API Design**:
```python
async def get_enhanced_suggestions(
    self,
    current_task: Optional[str] = None,
    energy_level: str = "medium",
    available_time_mins: int = 30,
    focus_state: str = "normal",
    limit: int = 5
) -> Dict[str, List[Dict]]:
    """Get context-aware task suggestions."""
    # Returns: {next_best, quick_wins, related_decisions, patterns}
```

### Phase 4: Integration (25 min)

**Tasks**:
1. Add to `queries/service.py` (10 min)
2. Update models if needed (10 min)
3. Integration test (5 min)

---

## 🎯 Success Criteria

**Code Quality**:
- [ ] All new methods have docstrings
- [ ] Parameterized queries (security)
- [ ] Graceful degradation everywhere
- [ ] 100% test coverage

**Functionality**:
- [ ] Can save/retrieve decision context
- [ ] Can build dependency chains
- [ ] Can generate enhanced suggestions
- [ ] Integrates with DDDPG core

**Performance**:
- [ ] Queries complete in < 500ms
- [ ] Graceful fallbacks work
- [ ] No memory leaks

**Documentation**:
- [ ] API examples provided
- [ ] Architecture decisions documented
- [ ] Integration guide updated

---

## 🚀 Ready to Build?

**Estimated Time**: 1.5 hours (25 min × 4 phases + 30 min buffer)
**Confidence**: High (Day 1 went 3.5x faster than planned)

**Next Steps**:
1. Review this research document
2. Make any adjustments to plan
3. Start Phase 1 (Decision Context)

---

**Status**: Research complete, awaiting approval to build 🎯
