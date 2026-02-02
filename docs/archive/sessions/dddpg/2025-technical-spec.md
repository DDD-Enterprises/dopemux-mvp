---
id: 2025-technical-spec
title: 2025 Technical Spec
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# DDDPG Technical Specification 2025
**Version**: 2.0
**Date**: 2025-10-29
**Status**: Production Ready Foundation + Day 2 Spec

---

## 🎯 Service Overview

### Identity
- **Name**: DDDPG (Decision-Driven Development Planning Graph)
- **Purpose**: ADHD-optimized decision tracking with knowledge graph intelligence
- **Architecture**: Multi-instance, graph-native, agent-friendly
- **Deployment**: Hybrid storage (PostgreSQL AGE + SQLite cache)

### Core Capabilities
1. **Decision Tracking**: Track every development decision with full context
2. **Knowledge Graph**: Intelligent relationship mapping via PostgreSQL AGE
3. **ADHD Optimization**: Top-3 pattern, progressive disclosure, cognitive load awareness
4. **Multi-Instance**: Git worktree-aware workspace isolation
5. **Agent Coordination**: Flexible metadata for multi-agent systems

---

## 📐 Architecture Specification

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User/Agent Layer                          │
│  (CLI, LSP, API, EventBus subscribers)                          │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      QueryService (Public API)                   │
│  - overview() - Top-3 pattern                                   │
│  - exploration() - Progressive depth                            │
│  - search() - FTS5 + semantic                                   │
│  - suggest_next_tasks() - ADHD-optimized                       │
│  - get_task_with_context() - Composite views                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Intelligence Layer                           │
│  ┌───────────────────┐  ┌──────────────────┐                   │
│  │ SuggestionEngine  │  │ RelationshipMapper│                   │
│  │ - Context scoring │  │ - Composite views │                   │
│  │ - Caching         │  │ - Parallel queries│                   │
│  └─────────┬─────────┘  └────────┬──────────┘                   │
└────────────┴──────────────────────┴────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      KG Integration Layer                        │
│                          DDDPGKG                                 │
│  - Task relationships    - Semantic search                      │
│  - Decision linking      - Dependency tracking                  │
│  - Graceful degradation  - Parameterized queries                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Storage Layer                             │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │ PostgreSQL AGE   │◄─EventBus─►│  SQLite Cache    │           │
│  │ - Source of truth│           │ - Fast local reads│           │
│  │ - Graph queries  │           │ - Offline support │           │
│  └──────────────────┘           └──────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### QueryService
- **Role**: Public API surface
- **Responsibilities**:
  - Input validation
  - Optional KG integration
  - Graceful fallbacks
  - ADHD query patterns
- **Dependencies**: StorageBackend, DDDPGKG (optional)

#### SuggestionEngine
- **Role**: Context-aware task recommendations
- **Responsibilities**:
  - Energy/time/focus matching
  - Dependency satisfaction
  - Result caching (5 min TTL)
  - Pattern mining (future)
- **Dependencies**: DDDPGKG, RelationshipMapper

#### RelationshipMapper
- **Role**: Aggregate KG queries into composite views
- **Responsibilities**:
  - Parallel query coordination
  - Data synthesis
  - Cluster identification
  - Context building
- **Dependencies**: DDDPGKG

#### DDDPGKG
- **Role**: Knowledge graph primitive operations
- **Responsibilities**:
  - Single-purpose queries
  - Direct AGE access
  - Graceful degradation
  - Security (parameterized queries)
- **Dependencies**: AGEClient (optional)

---

## 💾 Data Model Specification

### Core Entities

#### Decision
```python
class Decision(BaseModel):
    # Identity
    id: Optional[int] = None

    # Content
    summary: str = Field(..., max_length=200)
    rationale: Optional[str] = Field(None, max_length=1000)
    implementation_details: Optional[str] = None
    code_references: List[str] = Field(default_factory=list)

    # Classification
    status: DecisionStatus  # DRAFT/ACTIVE/SUPERSEDED/ARCHIVED
    decision_type: Optional[DecisionType]
    tags: List[str] = Field(default_factory=list)

    # Multi-instance (CRITICAL!)
    workspace_id: str
    instance_id: str = "A"
    visibility: DecisionVisibility  # PRIVATE/SHARED/GLOBAL

    # ADHD
    cognitive_load: int = Field(3, ge=1, le=5)
    estimated_effort_minutes: Optional[int] = None
    session_context: Optional[str] = None

    # Graph
    related_decisions: List[int] = Field(default_factory=list)

    # Agent integration
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime
```

#### DecisionRelationship
```python
class DecisionRelationship(BaseModel):
    from_decision_id: int
    to_decision_id: int
    relationship_type: RelationshipType
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
```

**RelationshipType** values:
- `SUPERSEDES`: New decision replaces old
- `IMPLEMENTS`: Decision implements another
- `RELATES_TO`: General relationship
- `CONTRADICTS`: Conflicting decisions
- `REQUIRES`: Dependency relationship
- `SUGGESTS`: Weak recommendation

#### WorkSession
```python
class WorkSession(BaseModel):
    id: Optional[int] = None
    workspace_id: str
    instance_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    # ADHD tracking
    initial_energy_level: str  # low/medium/high
    initial_focus_state: str   # scattered/normal/deep
    interruptions_count: int = 0
    decisions_made: List[int] = Field(default_factory=list)

    # Context preservation
    context_snapshot: Optional[str] = None
    active_task_id: Optional[str] = None
```

---

## 🔌 API Specification

### QueryService Public Methods

#### overview()
```python
async def overview(
    workspace_id: str,
    instance_id: str = "A",
    limit: int = 3  # Top-3 pattern!
) -> DecisionGraph:
    """
    Get overview of most important decisions.

    ADHD Pattern: Top-3 - never overwhelm

    Returns: Most recent ACTIVE decisions
    """
```

#### exploration()
```python
async def exploration(
    workspace_id: str,
    instance_id: str = "A",
    depth: int = 1,  # 1, 2, or 3
    decision_id: Optional[int] = None
) -> DecisionGraph:
    """
    Progressive disclosure - explore decision graph.

    Depth levels:
    - 1: Direct relationships only
    - 2: + Second-degree relationships
    - 3: Full context dump
    """
```

#### search()
```python
async def search(
    query: str,
    workspace_id: str,
    instance_id: Optional[str] = None,
    search_type: str = "fts",  # fts | semantic
    limit: int = 10
) -> List[Decision]:
    """
    Search decisions.

    search_type:
    - fts: SQLite FTS5 full-text search
    - semantic: Vector similarity (requires embeddings)
    """
```

#### get_task_with_context() [NEW - Day 2]
```python
async def get_task_with_context(
    task_id: str,
    workspace_id: str
) -> Dict[str, Any]:
    """
    Get task with full relationship context.

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

    Fallback: Basic task data if KG unavailable
    """
```

#### suggest_next_tasks() [NEW - Day 2]
```python
async def suggest_next_tasks(
    workspace_id: str,
    context: Dict[str, Any]
) -> Dict[str, List[Dict]]:
    """
    Get ADHD-optimized task suggestions.

    Args:
        context: {
            'energy_level': 'low' | 'medium' | 'high',
            'available_time_mins': int,
            'focus_state': 'scattered' | 'normal' | 'deep',
            'current_task': Optional[str]
        }

    Returns:
        {
            'next_best': [tasks],       # Top recommendations
            'quick_wins': [tasks],      # < 15 min tasks
            'related_decisions': [ids], # Relevant context
            'patterns': [info]          # Success patterns
        }

    Fallback: Recent tasks if KG unavailable
    """
```

---

## 🧠 ADHD Optimization Patterns

### 1. Top-3 Pattern

**Principle**: Never show more than 3 items by default

**Implementation**:
```python
async def overview(limit: int = 3):
    """Default limit is always 3"""

async def suggest_next_tasks(limit: int = 5):
    """Even suggestions limited to 5 max"""
```

**Rationale**: Matches ADHD working memory limits (3-4 items)

### 2. Progressive Disclosure

**Principle**: User controls information density

**Levels**:
- **Overview**: Top-3 most important
- **Exploration**: Depth-controlled (1, 2, or 3 levels)
- **Deep**: Full context dump (when needed)

**Implementation**:
```python
# Start simple
overview = await service.overview()  # 3 items

# Need more?
exploration = await service.exploration(depth=1)  # +related

# Full context?
deep = await service.exploration(depth=3)  # Everything
```

### 3. Cognitive Load Tracking

**Principle**: Track and respect mental capacity

**Fields**:
- `cognitive_load`: 1-5 scale (simple → complex)
- `estimated_effort_minutes`: Time estimate
- `session_context`: Preserve focus state

**Usage**:
```python
# Filter by cognitive load
low_load_decisions = await service.search(
    query="status:active",
    filters={'cognitive_load__lte': 2}
)

# Suggest based on energy
suggestions = await service.suggest_next_tasks(
    workspace_id="...",
    context={'energy_level': 'low'}  # Gets low-load tasks
)
```

### 4. Context Preservation

**Principle**: Save state across interruptions

**Implementation**:
```python
# Start session
session = WorkSession(
    workspace_id=workspace_id,
    instance_id=instance_id,
    initial_energy_level="high",
    initial_focus_state="deep",
    context_snapshot="Working on auth feature..."
)

# Track interruptions
session.interruptions_count += 1

# Resume later
last_session = await service.get_last_session()
print(f"You were: {last_session.context_snapshot}")
```

---

## 🔒 Security Specification

### Parameterized Queries

**Requirement**: 100% parameterized queries (no string interpolation)

**Implementation**:
```python
# ✅ GOOD
query = """
MATCH (t:Task {id: $task_id})
RETURN t
"""
result = await client.execute(query, {'task_id': task_id})

# ❌ BAD
query = f"MATCH (t:Task {{id: '{task_id}'}}) RETURN t"  # SQL injection risk!
```

**Validation**: All Cypher queries use `$param` syntax

### Input Validation

**Requirement**: All inputs validated via Pydantic

**Implementation**:
```python
class Decision(BaseModel):
    summary: str = Field(..., max_length=200)  # Length limit
    cognitive_load: int = Field(3, ge=1, le=5)  # Range validation
    tags: List[str] = Field(default_factory=list)  # Type safety
```

### Multi-Instance Isolation

**Requirement**: Respect visibility boundaries

**Implementation**:
```python
# PRIVATE: Only this instance
visibility = DecisionVisibility.PRIVATE
query_filter = f"instance_id = '{instance_id}'"

# SHARED: All instances in workspace
visibility = DecisionVisibility.SHARED
query_filter = f"workspace_id = '{workspace_id}'"

# GLOBAL: All workspaces
visibility = DecisionVisibility.GLOBAL
query_filter = "1=1"  # No filter
```

---

## ⚡ Performance Specification

### Latency Targets

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Decision linking | < 100ms | TBD | ⏳ |
| Task context (composite) | < 200ms | TBD | ⏳ |
| Work cluster | < 300ms | TBD | ⏳ |
| Suggestions (cached) | < 50ms | TBD | ⏳ |
| Suggestions (uncached) | < 500ms | TBD | ⏳ |
| FTS5 search | < 100ms | ~50ms | ✅ |
| Overview query | < 50ms | ~20ms | ✅ |
| Event publishing | < 10ms | TBD | ⏳ |

### Caching Strategy

**SuggestionEngine Cache**:
- TTL: 5 minutes
- Key: `{workspace_id}:{energy}:{time}:{focus}`
- Invalidation: On decision created/updated

**SQLite Cache** (future):
- Scope: Per-instance
- Sync: Via EventBus
- Fallback: PostgreSQL

### Indexing

**SQLite**:
```sql
CREATE INDEX idx_workspace_instance ON decisions(workspace_id, instance_id);
CREATE INDEX idx_status ON decisions(status);
CREATE INDEX idx_created_at ON decisions(created_at DESC);
CREATE VIRTUAL TABLE decisions_fts USING fts5(summary, rationale);
```

**PostgreSQL AGE**:
```cypher
CREATE INDEX ON :Task(id);
CREATE INDEX ON :Decision(id);
CREATE INDEX ON :Task(status);
```

---

## 🔄 Event Specification

### Published Events

#### decision.created
```json
{
  "event": "decision.created",
  "decision_id": 123,
  "workspace_id": "/dopemux-mvp",
  "instance_id": "A",
  "summary": "Use FastAPI for API server",
  "decision_type": "architecture",
  "timestamp": "2025-10-29T13:26:23Z"
}
```

#### decision.updated
```json
{
  "event": "decision.updated",
  "decision_id": 123,
  "workspace_id": "/dopemux-mvp",
  "instance_id": "A",
  "changes": {
    "status": {"old": "active", "new": "superseded"},
    "updated_by": "user_123"
  },
  "timestamp": "2025-10-29T14:30:00Z"
}
```

#### decision.related
```json
{
  "event": "decision.related",
  "from_decision_id": 123,
  "to_decision_id": 456,
  "relationship_type": "implements",
  "workspace_id": "/dopemux-mvp",
  "timestamp": "2025-10-29T15:00:00Z"
}
```

### Subscribed Events

#### task.completed
```python
async def on_task_completed(event: Dict):
    """Auto-link decisions to completed tasks"""
    task_id = event['task_id']

    # Find related decisions
    decisions = await dddpg.search_decisions(
        tags__contains='task',
        summary__contains=task_id
    )

    # Link to KG
    for decision in decisions:
        await dddpg.link_decision_to_task(decision.id, task_id)
```

---

## 🧪 Testing Specification

### Test Coverage Requirements

- **Unit tests**: > 90% line coverage
- **Integration tests**: All public methods
- **Security tests**: All Cypher queries parameterized
- **Performance tests**: All latency targets validated

### Test Structure

```python
# Unit tests
class TestDDDPGKG:
    def test_link_decision_to_task(self):
        """Test decision-task linking"""

    def test_graceful_degradation(self):
        """Test fallback without KG"""

# Integration tests
class TestQueryServiceIntegration:
    def test_suggest_next_tasks_with_kg(self):
        """End-to-end suggestion flow"""

    def test_suggest_next_tasks_without_kg(self):
        """Fallback to recent tasks"""

# Performance tests
class TestPerformance:
    def test_suggestion_cache_hit(self):
        """Cache hit < 50ms"""

    def test_suggestion_cache_miss(self):
        """Cache miss < 500ms"""
```

### Current Test Status

**Week 4 Day 1** (kg_integration.py):
- Tests: 19/19 passing ✅
- Coverage: 100% ✅
- Runtime: 0.14s ✅

---

## 📦 Dependencies

### Core Dependencies
```
fastapi==0.104.1
pydantic==2.5.0
psycopg2-binary==2.9.9
redis==5.0.1
age-py==0.2.0
sqlalchemy==2.0.23
```

### Optional Dependencies
```
sentence-transformers==2.2.2  # Semantic search
numpy==1.24.0                 # Vector operations
```

### Development Dependencies
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
```

---

## 🚀 Deployment Specification

### Environment Variables

```bash
# Database
POSTGRES_DSN=postgresql://user:pass@localhost:5432/dopemux
SQLITE_PATH=/path/to/dddpg.db

# Redis (EventBus)
REDIS_URL=redis://localhost:6379/0

# DDDPG Config
DDDPG_WORKSPACE_ID=/dopemux-mvp
DDDPG_INSTANCE_ID=A
DDDPG_CACHE_TTL_MINUTES=5

# AGE (Knowledge Graph)
AGE_GRAPH_NAME=dopemux_kg
```

### Docker Compose

```yaml
services:
  dddpg:
    image: dopemux/dddpg:latest
    environment:
      - POSTGRES_DSN=${POSTGRES_DSN}
      - REDIS_URL=${REDIS_URL}
      - DDDPG_WORKSPACE_ID=${DDDPG_WORKSPACE_ID}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/data
    ports:
      - "8000:8000"
```

---

## 📚 Migration Path

### From ConPort to DDDPG

**Migration Script**:
```python
async def migrate_conport_to_dddpg():
    """Migrate ConPort decisions to DDDPG format"""

    # 1. Export from ConPort SQLite
    conport_decisions = await conport_db.export_all()

    # 2. Transform to DDDPG format
    dddpg_decisions = []
    for old_decision in conport_decisions:
        new_decision = Decision(
            summary=old_decision['summary'],
            rationale=old_decision.get('rationale'),
            workspace_id=old_decision['workspace_path'],
            instance_id='A',  # Default instance
            visibility=DecisionVisibility.SHARED,
            created_at=old_decision['timestamp']
        )
        dddpg_decisions.append(new_decision)

    # 3. Import to DDDPG
    for decision in dddpg_decisions:
        await dddpg_storage.create(decision)

    print(f"Migrated {len(dddpg_decisions)} decisions")
```

---

**Last Updated**: 2025-10-29
**Version**: 2.0
**Status**: Production Foundation + Day 2 Spec Ready
