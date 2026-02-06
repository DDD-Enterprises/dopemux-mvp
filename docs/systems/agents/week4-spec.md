---
id: week4-spec
title: Week4 Spec
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week4 Spec (reference) for dopemux documentation and developer workflows.
---
# Week 4: Technical Specification

**Date**: 2025-10-29
**Status**: 📐 Specification Phase
**Focus**: ADHD-Optimized ConPort-KG Integration
**Complexity**: 0.6 (Medium)

---

## Overview

Week 4 integrates **CognitiveGuardian** with **ConPort-KG** (Knowledge Graph) to provide:
1. Task relationship mapping (dependencies, blockers)
2. Semantic task search (natural language, fuzzy matching)
3. Decision context graphs (track "why")
4. ADHD pattern mining (successful work patterns)
5. Agent knowledge sharing (cross-session learning)

**Foundation**: ConPort-KG infrastructure already exists (discovered during research)

---

## Architecture

### Current Stack (Discovered)

**ConPort-KG** (`services/conport_kg/`):
```
├── age_client.py              # PostgreSQL AGE client (connection pooling)
├── adhd_query_adapter.py      # Attention-aware query selection
├── orchestrator.py            # Event-driven KG automation
├── queries/
│   ├── overview.py            # Decision overview queries
│   ├── exploration.py         # Pattern exploration
│   ├── deep_context.py        # Context retrieval
│   └── models.py              # Data models
├── api/                       # REST API layer
├── auth/                      # Authentication
└── middleware/                # RBAC middleware
```

**Key Features Already Built**:
- ✅ Apache AGE graph database (PostgreSQL extension)
- ✅ Connection pooling (1-5 concurrent connections)
- ✅ ADHD query adapter (attention state-aware)
- ✅ Event-driven orchestration
- ✅ Query classes (overview, exploration, deep context)

---

### Week 4 Integration Points

```
CognitiveGuardian (services/agents/)
    │
    ├─→ ConPort MCP [✅ Week 3]
    │   └─ State persistence (user state, metrics)
    │
    ├─→ ConPort-KG [NEW: Week 4]
    │   ├─ Task relationship queries
    │   ├─ Semantic task search
    │   ├─ Decision context retrieval
    │   └─ Pattern mining queries
    │
    └─→ Task-Orchestrator
            │
            ├─→ ConPort-KG [NEW: Week 4]
            │   ├─ Pre-routing dependency checks
            │   ├─ Semantic task matching
            │   └─ Context-aware dispatch
            │
            └─→ Agent dispatch (ConPort, Serena, etc.)
```

---

## New Components

### Component 1: CognitiveGuardianKG

**File**: `services/agents/cognitive_guardian_kg.py`
**Lines**: ~250
**Purpose**: Wrapper around ConPort-KG for ADHD-optimized graph queries

**Class Structure**:
```python
class CognitiveGuardianKG:
    """
    ADHD-optimized Knowledge Graph integration for CognitiveGuardian.

    Provides:
    - Task relationship mapping
    - Semantic search
    - Decision context retrieval
    - Pattern mining
    """

    def __init__(
        self,
        workspace_id: str,
        age_client: Optional[AGEClient] = None,
        adhd_adapter: Optional[ADHDQueryAdapter] = None
    ):
        """Initialize KG integration with optional AGE client."""

    async def get_task_relationships(
        self,
        task_id: str
    ) -> Dict[str, List[str]]:
        """
        Get task relationships (dependencies, blockers, related).

        Returns:
            {
                "dependencies": ["task-123", "task-456"],
                "blockers": ["task-789"],
                "related": ["task-321", "task-654"]
            }
        """

    async def search_tasks_semantic(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for tasks (natural language).

        Args:
            query: Natural language query ("tasks about API")
            limit: Max results (default 5 for ADHD)

        Returns:
            List of matching tasks with relevance scores
        """

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

    async def mine_adhd_patterns(
        self,
        user_id: str,
        days_lookback: int = 30
    ) -> Dict[str, Any]:
        """
        Mine successful ADHD work patterns.

        Returns:
            {
                "successful_energy_task_combos": [...],
                "optimal_break_timing": {...},
                "preferred_task_types": [...]
            }
        """
```

**Methods** (7):
1. `__init__()` - Initialize with AGE client
2. `get_task_relationships()` - Map dependencies/blockers
3. `search_tasks_semantic()` - Natural language search
4. `get_decision_context()` - Retrieve "why" decisions
5. `mine_adhd_patterns()` - Pattern mining
6. `_build_task_graph()` - Internal: Graph construction
7. `_calculate_relevance()` - Internal: Semantic scoring

**Dependencies**:
- `age_client.AGEClient` (existing)
- `adhd_query_adapter.ADHDQueryAdapter` (existing)
- `queries.exploration.ExplorationQueries` (existing)

---

### Component 2: Enhanced CognitiveGuardian

**File**: `services/agents/cognitive_guardian.py` (updates)
**Lines Added**: ~120
**Purpose**: Integrate KG queries into task suggestions and state tracking

**New Methods**:
```python
async def suggest_tasks_with_context(
    self,
    energy: Optional[str] = None,
    max_suggestions: int = 3
) -> List[Dict[str, Any]]:
    """
    Enhanced task suggestions with KG context.

    Adds:
    - Dependency checking (prerequisite tasks first)
    - Related task grouping
    - Decision context (why this task exists)
    """

async def check_task_dependencies(
    self,
    task_id: str
) -> Dict[str, bool]:
    """
    Check if task dependencies are met.

    Returns:
        {
            "ready": True/False,
            "blocked_by": ["task-123"],
            "suggestion": "Complete prerequisite X first"
        }
    """

async def save_task_outcome(
    self,
    task_id: str,
    success: bool,
    energy_level: str,
    complexity: float
) -> None:
    """
    Save task outcome to KG for pattern mining.

    Stores:
    - Task completion status
    - Energy level at completion
    - Complexity rating
    - Duration (from session tracking)
    """
```

**Integration Points**:
1. `suggest_tasks()` → calls `suggest_tasks_with_context()`
2. `check_task_readiness()` → calls `check_task_dependencies()`
3. `stop_monitoring()` → calls `save_task_outcome()` (if task completed)

---

### Component 3: Enhanced Task-Orchestrator

**File**: `services/task-orchestrator/enhanced_orchestrator.py` (updates)
**Lines Added**: ~100
**Purpose**: Use KG for smarter task routing

**New Methods**:
```python
async def _check_dependencies_before_routing(
    self,
    task: OrchestrationTask
) -> bool:
    """
    Check KG for task dependencies before routing.

    Returns:
        True if ready, False if blocked
    """

async def _find_related_tasks(
    self,
    task: OrchestrationTask
) -> List[str]:
    """
    Find related tasks in KG for context.

    Returns:
        List of related task IDs
    """

async def _semantic_task_match(
    self,
    task: OrchestrationTask,
    agent: AgentType
) -> float:
    """
    Calculate semantic match score using KG.

    Returns:
        Confidence score 0.0-1.0
    """
```

**Integration Points**:
1. `_assign_optimal_agent()` → call `_check_dependencies_before_routing()` first
2. `_dispatch_to_agent()` → call `_find_related_tasks()` for context
3. Agent selection → use `_semantic_task_match()` for better routing

---

### Component 4: ADHD Pattern Analyzer

**File**: `services/agents/adhd_pattern_analyzer.py`
**Lines**: ~230
**Purpose**: Mine KG for successful ADHD work patterns

**Class Structure**:
```python
class ADHDPatternAnalyzer:
    """
    Analyze historical data to identify successful ADHD patterns.

    Mines:
    - Energy-task type correlations
    - Optimal break timing (personalized)
    - Task complexity preferences
    - Time-of-day effectiveness
    """

    def __init__(self, kg_client: CognitiveGuardianKG):
        """Initialize with KG client."""

    async def analyze_energy_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Identify which energy levels work best for which tasks.

        Returns:
            {
                "high_energy": ["complex_coding", "architecture"],
                "medium_energy": ["testing", "documentation"],
                "low_energy": ["code_review", "meeting_notes"]
            }
        """

    async def analyze_break_patterns(
        self,
        user_id: str
    ) -> Dict[str, int]:
        """
        Learn optimal break timing for this user.

        Returns:
            {
                "gentle_reminder": 28,  # minutes (not 25!)
                "mandatory": 95,        # minutes (not 90!)
                "hyperfocus_warning": 65
            }
        """

    async def get_personalized_recommendations(
        self,
        user_state: UserState
    ) -> List[str]:
        """
        Get AI-generated recommendations based on patterns.

        Returns:
            [
                "You're most productive at 9am-11am for complex tasks",
                "Take breaks every 28 min (your optimal rhythm)",
                "Evening is best for code review (90% success rate)"
            ]
        """
```

**Methods** (6):
1. `analyze_energy_patterns()` - Energy-task correlations
2. `analyze_break_patterns()` - Personalized break timing
3. `analyze_complexity_preferences()` - Task complexity patterns
4. `analyze_time_of_day_patterns()` - When user is most effective
5. `get_personalized_recommendations()` - AI suggestions
6. `_query_historical_data()` - Internal: KG queries

---

## Data Models

### TaskRelationship

```python
@dataclass
class TaskRelationship:
    """Task relationship in knowledge graph"""
    source_task_id: str
    target_task_id: str
    relationship_type: str  # dependency, blocker, related
    strength: float  # 0.0-1.0
    created_at: str
    metadata: Dict[str, Any]
```

### DecisionContext

```python
@dataclass
class DecisionContext:
    """Decision context for a task"""
    decision_id: str
    task_id: str
    rationale: str
    outcomes: List[str]
    related_decisions: List[str]
    timestamp: str
```

### ADHDPattern

```python
@dataclass
class ADHDPattern:
    """Discovered ADHD work pattern"""
    pattern_type: str  # energy_task, break_timing, complexity
    confidence: float  # 0.0-1.0
    data: Dict[str, Any]
    discovered_at: str
    sample_size: int
```

---

## Graph Schema (Extensions)

### New Node Types

**Task Node**:
```cypher
CREATE (t:Task {
    id: "task-123",
    title: "Implement API endpoint",
    complexity: 0.7,
    energy_required: "high",
    status: "TODO",
    created_at: "2025-10-29T...",
    completed_at: null
})
```

**TaskOutcome Node**:
```cypher
CREATE (o:TaskOutcome {
    task_id: "task-123",
    success: true,
    energy_level: "high",
    attention_state: "focused",
    duration_minutes: 45,
    timestamp: "2025-10-29T..."
})
```

**ADHDPattern Node**:
```cypher
CREATE (p:ADHDPattern {
    user_id: "user-456",
    pattern_type: "energy_task",
    confidence: 0.85,
    data: '{"high_energy": ["coding", "design"]}',
    discovered_at: "2025-10-29T..."
})
```

### New Relationship Types

**DEPENDS_ON**:
```cypher
(task1:Task)-[:DEPENDS_ON {strength: 0.9}]->(task2:Task)
```

**BLOCKS**:
```cypher
(task1:Task)-[:BLOCKS {reason: "API not ready"}]->(task2:Task)
```

**RELATED_TO**:
```cypher
(task1:Task)-[:RELATED_TO {similarity: 0.75}]->(task2:Task)
```

**HAS_CONTEXT**:
```cypher
(task:Task)-[:HAS_CONTEXT]->(decision:Decision)
```

**PRODUCED**:
```cypher
(task:Task)-[:PRODUCED]->(outcome:TaskOutcome)
```

---

## API Specifications

### Endpoint 1: Task Relationships

**URL**: `GET /api/v1/kg/tasks/{task_id}/relationships`

**Response**:
```json
{
  "task_id": "task-123",
  "dependencies": [
    {"task_id": "task-456", "title": "Setup API", "strength": 0.9}
  ],
  "blockers": [
    {"task_id": "task-789", "title": "Fix DB", "reason": "Schema needed"}
  ],
  "related": [
    {"task_id": "task-321", "title": "Add tests", "similarity": 0.75}
  ]
}
```

### Endpoint 2: Semantic Search

**URL**: `POST /api/v1/kg/tasks/search`

**Request**:
```json
{
  "query": "tasks about API integration",
  "limit": 5,
  "energy_filter": "high"
}
```

**Response**:
```json
{
  "results": [
    {
      "task_id": "task-123",
      "title": "Implement REST API",
      "relevance": 0.92,
      "energy_required": "high",
      "complexity": 0.7
    }
  ],
  "total": 12
}
```

### Endpoint 3: Decision Context

**URL**: `GET /api/v1/kg/tasks/{task_id}/context`

**Response**:
```json
{
  "task_id": "task-123",
  "decisions": [
    {
      "decision_id": "dec-456",
      "summary": "Use FastAPI for REST API",
      "rationale": "Best async support for Python",
      "timestamp": "2025-10-25T..."
    }
  ],
  "outcomes": [
    {"status": "success", "duration": 45, "energy": "high"}
  ]
}
```

### Endpoint 4: Pattern Mining

**URL**: `GET /api/v1/kg/users/{user_id}/patterns?days=30`

**Response**:
```json
{
  "user_id": "user-456",
  "energy_patterns": {
    "high_energy": ["coding", "architecture"],
    "medium_energy": ["testing", "docs"],
    "low_energy": ["review", "meetings"]
  },
  "break_patterns": {
    "gentle_reminder": 28,
    "mandatory": 95,
    "optimal_rhythm": "28/95"
  },
  "recommendations": [
    "You're 90% successful with complex tasks at 9-11am",
    "Take breaks every 28 min (your natural rhythm)",
    "Evening is best for code review (85% success)"
  ]
}
```

---

## Performance Targets

### Query Performance

**Tier 1** (Frequent queries):
- Task relationships: <50ms
- Dependency checks: <50ms
- Simple searches: <50ms

**Tier 2** (Moderate queries):
- Semantic search: <150ms
- Decision context: <150ms
- Related tasks: <150ms

**Tier 3** (Heavy queries):
- Pattern mining: <500ms
- Deep analysis: <500ms
- Cross-session patterns: <500ms

**Background** (Non-blocking):
- Full pattern analysis: <2s (async)
- Graph construction: <3s (async)
- Recommendation generation: <5s (async)

### Caching Strategy

**Cache Keys**:
- `task:relationships:{task_id}` (TTL: 5 min)
- `task:context:{task_id}` (TTL: 10 min)
- `user:patterns:{user_id}` (TTL: 1 hour)
- `search:{hash(query)}` (TTL: 15 min)

**Invalidation**:
- On task update: Clear task-specific caches
- On task completion: Clear pattern caches
- On new decision: Clear context caches

---

## Testing Strategy

### Unit Tests

**cognitive_guardian_kg_test.py** (6 tests):
1. `test_get_task_relationships()` - Basic relationship query
2. `test_search_tasks_semantic()` - Semantic search
3. `test_get_decision_context()` - Context retrieval
4. `test_mine_adhd_patterns()` - Pattern mining
5. `test_graceful_degradation()` - KG unavailable fallback
6. `test_caching()` - Cache hit/miss behavior

**adhd_pattern_analyzer_test.py** (6 tests):
1. `test_analyze_energy_patterns()` - Energy correlations
2. `test_analyze_break_patterns()` - Personalized timing
3. `test_analyze_complexity_preferences()` - Complexity patterns
4. `test_analyze_time_of_day_patterns()` - Time effectiveness
5. `test_get_personalized_recommendations()` - AI suggestions
6. `test_insufficient_data_handling()` - Graceful degradation

### Integration Tests

**test_kg_integration.py** (6 tests):
1. `test_cognitive_guardian_with_kg()` - Full integration
2. `test_orchestrator_dependency_checks()` - Routing integration
3. `test_task_completion_pattern_learning()` - Learning loop
4. `test_semantic_search_accuracy()` - Search quality
5. `test_cross_session_continuity()` - Persistence
6. `test_performance_targets()` - Speed requirements

**Total**: 18 tests (unit + integration)

---

## Error Handling

### Graceful Degradation

**KG Unavailable**:
```python
try:
    relationships = await kg.get_task_relationships(task_id)
except ConnectionError:
    logger.warning("KG unavailable, falling back to basic mode")
    relationships = {"dependencies": [], "blockers": [], "related": []}
    # Continue without KG features
```

**Query Timeout**:
```python
try:
    async with asyncio.timeout(2.0):
        results = await kg.search_tasks_semantic(query)
except asyncio.TimeoutError:
    logger.error("KG query timeout, returning partial results")
    results = []  # or cached results
```

**Pattern Mining Failure**:
```python
try:
    patterns = await analyzer.mine_adhd_patterns(user_id)
except Exception as e:
    logger.error(f"Pattern mining failed: {e}")
    patterns = self._get_default_patterns()  # Use defaults
```

---

## Security Considerations

### Access Control

**Row-Level Security**:
- Tasks: User can only see own workspace tasks
- Patterns: User can only see own patterns
- Decisions: Respect existing RBAC middleware

**Query Sanitization**:
```python
def sanitize_query(query: str) -> str:
    """Sanitize user input for graph queries"""
    # Remove Cypher injection attempts
    # Escape special characters
    # Limit query length
```

### Data Privacy

**ADHD Patterns**:
- Stored per-user (not shared)
- Encrypted at rest
- Deletable on user request
- No cross-user aggregation

**Task Relationships**:
- Workspace-scoped (not global)
- Respect task visibility rules
- No inference across workspaces

---

## Migration Path

### Phase 1: KG Layer (Day 1)
1. Create `cognitive_guardian_kg.py`
2. Implement basic query methods
3. Add unit tests
4. Verify AGE connection

### Phase 2: Task Relationships (Day 2)
1. Define graph schema extensions
2. Implement relationship mapping
3. Add dependency checking
4. Integration tests

### Phase 3: Semantic Search (Day 3)
1. Add embedding generation
2. Implement semantic matching
3. Integrate with orchestrator
4. Performance testing

### Phase 4: Decision Context (Day 4)
1. Link tasks to decisions
2. Implement context retrieval
3. Add to task suggestions
4. Integration testing

### Phase 5: Pattern Mining (Day 5)
1. Create pattern analyzer
2. Implement mining algorithms
3. Add personalized recommendations
4. Full integration test

---

## Success Criteria

### Technical

- [ ] All 18 tests passing (100%)
- [ ] Query performance meets targets (Tier 1: <50ms, Tier 2: <150ms, Tier 3: <500ms)
- [ ] Graceful degradation works (KG unavailable → basic mode)
- [ ] Zero data loss (all outcomes persisted)
- [ ] Security verified (RBAC respected)

### Functional

- [ ] Task dependencies detected (100% accuracy)
- [ ] Semantic search returns relevant results (>70% accuracy)
- [ ] Decision context retrieved (100% when exists)
- [ ] Patterns discovered (after 10+ task completions)
- [ ] Personalized recommendations generated

### ADHD Impact

- [ ] 50% reduction in "forgot prerequisite" issues
- [ ] 70% semantic search success rate
- [ ] 100% decision context availability
- [ ] Personalized break timing learned
- [ ] Cross-session knowledge preserved

---

## Dependencies

### External

- PostgreSQL 14+ with AGE extension
- Redis (for caching)
- ConPort-KG service (existing)
- CognitiveGuardian (Week 3)
- Task-Orchestrator (existing)

### Python Packages

```
psycopg2-binary==2.9.9
redis==5.0.1
sentence-transformers==2.2.2  # For semantic embeddings
numpy==1.24.3
```

---

## Rollout Plan

### Week 4 Development

**Days 1-5**: Build all components (as per roadmap)

**Testing**: Continuous (per day)

**Documentation**: Final (Day 5)

### Week 5 Soft Launch

**Limited users**: Internal testing only

**Monitoring**: Heavy logging, performance tracking

**Feedback**: Collect ADHD impact data

### Week 6 Full Rollout

**All users**: Production release

**Optimization**: Based on Week 5 data

**Documentation**: User guides, troubleshooting

---

## Monitoring & Observability

### Metrics to Track

**Performance**:
- Query latency (p50, p95, p99)
- Cache hit rate
- Connection pool utilization
- Pattern mining duration

**Usage**:
- Queries per user per day
- Semantic search adoption
- Pattern mining requests
- Dependency check frequency

**ADHD Impact**:
- Tasks completed with dependency checks
- Semantic search success rate
- Personalized patterns discovered
- Recommendation acceptance rate

### Logging

**INFO**: User actions, successful queries
**WARNING**: Query timeouts, degradation mode
**ERROR**: KG failures, connection issues
**DEBUG**: Query details, performance data

---

## Next Steps

1. ✅ Technical spec complete (this document)
2. ⏭️ Create implementation roadmap (Day-by-day)
3. ⏭️ Set up development environment
4. ⏭️ Begin Day 1 implementation

**Status**: Ready for detailed roadmap creation

---

**Created**: 2025-10-29
**Specification Time**: 60 minutes
**Components**: 4 new, 2 enhanced
**Total Code**: ~700 lines
**Tests**: 18
**Confidence**: 95%

🎯 **Week 4: Technical Specification Complete** 🎯
