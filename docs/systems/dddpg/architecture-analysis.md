---
id: architecture-analysis
title: Architecture Analysis
type: system-doc
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# 🧠 DDDPG Deep Architecture Analysis

**Date**: 2025-10-29
**Status**: Pre-Storage Planning
**Goal**: Ensure we don't miss critical data models or storage requirements

---

## 1. Missing Data Models Analysis

### ✅ What We Have
- `Decision` - Core decision tracking
- `DecisionStatus` - Lifecycle management
- `DecisionType` - Categorization
- Basic workspace/user fields

### 🤔 What We're Missing

#### A. Session & Context Models

**Problem**: ADHD users have multiple concurrent work sessions
- Feature work in worktree A
- Hotfix in worktree B
- Experimentation in worktree C

**Missing Models**:
```python
class WorkSession(BaseModel):
    """Active work session tracking"""
    id: str
    workspace_id: str  # Which worktree/instance
    instance_id: str  # DOPEMUX_INSTANCE_ID
    started_at: datetime
    last_activity: datetime

    # ADHD metadata
    focus_level: int  # 1-5
    break_needed: bool
    context_preserved: bool

    # Active state
    current_file: Optional[str]
    current_decisions: List[int]  # Decision IDs
```

#### B. Multi-Instance Isolation Models

**Problem**: From WORKSPACE_MULTI_INSTANCE_FIX.md:
- Multiple Dopemux instances run simultaneously
- Each needs isolated decision tracking
- Worktrees need separate contexts
- But some decisions should be shared (COMPLETED tasks)

**Missing Models**:
```python
class WorkspaceInstance(BaseModel):
    """Dopemux instance (main repo or worktree)"""
    instance_id: str  # "A", "feature-auth", etc
    workspace_root: str  # Absolute path
    is_main_repo: bool
    git_branch: Optional[str]

    # Linked to main
    main_repo_path: Optional[str]  # If worktree

    # Instance state
    active: bool
    created_at: datetime
    last_seen: datetime

class DecisionVisibility(str, Enum):
    """Who can see this decision?"""
    PRIVATE = "private"      # Only this instance
    SHARED = "shared"        # All instances in workspace
    GLOBAL = "global"        # All workspaces
```

#### C. Agent Coordination Models

**Problem**: 6 agents need to coordinate via EventBus
- Serena (LSP hover)
- Task-Orchestrator (task management)
- Zen (consensus)
- ADHD Engine (break detection)
- Desktop Commander (file ops)
- Dope-Context (workspace awareness)

**Missing Models**:
```python
class AgentActivity(BaseModel):
    """Track agent actions on decisions"""
    agent_id: str  # "serena", "task-orchestrator", etc
    decision_id: int
    action: str  # "viewed", "suggested", "enriched"
    timestamp: datetime
    metadata: Dict[str, Any]

class AgentSuggestion(BaseModel):
    """Agents suggest decisions (Zen consensus, Task-Orchestrator)"""
    agent_id: str
    suggested_decision: Decision  # Not yet created
    rationale: str
    confidence: float  # 0.0-1.0
    requires_approval: bool
```

#### D. Graph Relationship Models

**Problem**: Decisions relate to each other
- "Decision B supersedes Decision A"
- "Decision C implements Decision B"
- "Decisions D, E, F are all related"

**Current**: We have `related_decisions: List[int]` but no metadata

**Better Model**:
```python
class DecisionRelationship(BaseModel):
    """Typed relationships between decisions"""
    from_decision_id: int
    to_decision_id: int
    relationship_type: RelationshipType
    weight: float = 1.0  # Strength
    created_at: datetime
    created_by: str  # User or agent

class RelationshipType(str, Enum):
    SUPERSEDES = "supersedes"      # New replaces old
    IMPLEMENTS = "implements"      # Carries out
    RELATES_TO = "relates_to"      # Generic connection
    CONTRADICTS = "contradicts"    # Conflict
    REQUIRES = "requires"          # Dependency
    SUGGESTS = "suggests"          # Soft dependency
```

#### E. File & Code Relationships

**Problem**: Decisions mention files, but we don't track it properly

**Missing Models**:
```python
class CodeReference(BaseModel):
    """Link decision to code"""
    decision_id: int
    file_path: str  # Relative to workspace
    line_start: Optional[int]
    line_end: Optional[int]
    context: Optional[str]  # Code snippet
    created_at: datetime

class DecisionCodeImpact(BaseModel):
    """Track which files were changed for a decision"""
    decision_id: int
    files_changed: List[str]
    lines_added: int
    lines_removed: int
    commit_sha: Optional[str]
    committed_at: Optional[datetime]
```

---

## 2. Storage Considerations

### A. Multi-Instance Database Strategy

**Options**:

#### Option 1: Single PostgreSQL, Partitioned by Instance ✅ RECOMMENDED
```sql
-- All instances share one Postgres
-- Partitioned by workspace_id + instance_id

CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR NOT NULL,  -- Main workspace
    instance_id VARCHAR NOT NULL,   -- Worktree/instance
    summary TEXT NOT NULL,
    ...
    CONSTRAINT unique_decision_per_instance UNIQUE (workspace_id, instance_id, id)
);

-- Index for fast instance queries
CREATE INDEX idx_decisions_instance ON decisions(workspace_id, instance_id);
```

**Pros**:
- Simple query: `WHERE instance_id = 'feature-auth'`
- Easy sharing: `WHERE instance_id IN ('A', 'feature-auth')`
- Single source of truth
- Graph queries work across instances

**Cons**:
- Need careful indexing
- All instances need Postgres access

#### Option 2: SQLite Per Instance ❌ NOT RECOMMENDED
```
/dopemux-mvp/.dddpg/decisions.db         # Instance A
/dopemux-feature-auth/.dddpg/decisions.db  # Instance B
```

**Pros**:
- True isolation
- No network needed

**Cons**:
- Can't share decisions easily
- Graph queries impossible across instances
- Synchronization nightmare
- ConPort MCP already uses this pattern (limiting!)

#### Option 3: Hybrid (Postgres + Local Cache) ✅ BEST OF BOTH
```
PostgreSQL: Source of truth, all decisions
SQLite: Per-instance cache for fast reads

Instance writes → PostgreSQL (via EventBus)
Instance reads → SQLite cache (synced via EventBus)
```

**Pros**:
- Fast local reads (SQLite)
- Shared source of truth (Postgres)
- EventBus keeps caches in sync
- Works offline (cache-only mode)

**Cons**:
- More complex
- Cache invalidation needed
- EventBus dependency

---

### B. Graph Storage (PostgreSQL AGE)

**Schema Design**:

```sql
-- Vertex: Decision
CREATE VLABEL decision;

-- Properties stored as JSON in AGE
{
  "id": 1,
  "summary": "Use DDDPG",
  "workspace_id": "/dopemux-mvp",
  "instance_id": "A",
  "tags": ["architecture"],
  ...
}

-- Edge: Relationships
CREATE ELABEL supersedes;
CREATE ELABEL implements;
CREATE ELABEL relates_to;

-- Query: Find all decisions that implement decision #5
MATCH (d1)-[:implements]->(d2)
WHERE d2.id = 5
RETURN d1;

-- Query: Find decision graph (depth-2)
MATCH path = (d1)-[*1..2]-(d2)
WHERE d1.id = 10
RETURN path;
```

**Indexing Strategy**:
```sql
-- Fast lookups by workspace/instance
CREATE INDEX ON decision(workspace_id);
CREATE INDEX ON decision(instance_id);
CREATE INDEX ON decision(workspace_id, instance_id);

-- Full-text search (if AGE supports)
CREATE INDEX ON decision USING GIN(to_tsvector('english', summary || ' ' || rationale));
```

---

### C. SQLite Cache Schema

**Per-Instance Cache**:
```sql
-- Minimal schema for fast reads
CREATE TABLE decisions_cache (
    id INTEGER PRIMARY KEY,
    summary TEXT NOT NULL,
    rationale TEXT,
    tags TEXT,  -- JSON array
    visibility TEXT,  -- "private", "shared", "global"
    created_at TEXT,

    -- Cache metadata
    cached_at TEXT,
    source TEXT  -- "postgres", "local"
);

-- FTS for local search
CREATE VIRTUAL TABLE decisions_fts USING fts5(
    summary, rationale, tags
);
```

---

## 3. Multi-Agent Support Requirements

### A. Concurrent Access Patterns

**Scenario**: All 6 agents running simultaneously

```
Serena:     Read decisions for hover (10/sec)
Task-Orch:  Read/write task decisions (1/sec)
Zen:        Read for consensus (0.1/sec)
ADHD:       Write break suggestions (0.05/sec)
Desktop:    Write file operation decisions (0.5/sec)
Dope-Ctx:   Read workspace state (5/sec)
```

**Storage Requirements**:
- ✅ Read-heavy (90% reads, 10% writes)
- ✅ Postgres handles concurrent reads well
- ✅ SQLite cache perfect for Serena (local, fast)
- ✅ EventBus for write propagation

### B. Agent-Specific Extensions

**Storage Strategy**: Use JSON fields for agent metadata

```python
class Decision(BaseModel):
    ...
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)
    # {
    #   "serena": {"hover_count": 42, "last_viewed": "..."},
    #   "zen": {"consensus_score": 0.85, "voters": ["alice", "bob"]},
    #   "adhd": {"break_suggested": true, "cognitive_load": 4}
    # }
```

**Pros**:
- Flexible (agents can add fields)
- No schema changes needed
- Queryable in Postgres (JSONB)

**Cons**:
- Less type-safe
- Need validation

---

## 4. Orchestrator Requirements

### Task-Orchestrator Needs

**Current**: Task-Orchestrator tracks tasks
**Future**: Tasks ARE decisions with `decision_type = TASK`

**Extended Task Model**:
```python
class TaskDecision(Decision):
    """Decision that represents a task"""
    decision_type: DecisionType = DecisionType.IMPLEMENTATION

    # Task-specific fields (in agent_metadata or separate?)
    task_status: TaskStatus  # TODO, IN_PROGRESS, DONE
    task_priority: int  # 1-5
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    estimated_cognitive_load: int  # 1-5
    actual_cognitive_load: Optional[int]
```

**Storage Consideration**:
- Option A: Store in `agent_metadata["task_orchestrator"]`
- Option B: Separate `tasks` table that references `decisions`
- **Recommendation**: Option A (simpler, uses existing Decision model)

---

## 5. EventBus Integration Requirements

### A. Event Types Needed

**From Storage Layer**:
```python
# Decision events
decision.created    # New decision logged
decision.updated    # Decision modified
decision.deleted    # Decision archived/deleted
decision.related    # Relationship added

# Instance events
instance.started    # Worktree instance activated
instance.stopped    # Instance shut down
instance.synced     # Cache synchronized

# Agent events
agent.suggested     # Agent proposes decision
agent.enriched      # Agent added metadata
agent.conflict      # Agent detected issue
```

### B. Event Payload Schema

**Consistent Structure** (already defined in Path C):
```python
{
  "event_type": "decision.created",
  "timestamp": "2025-10-29T01:23:00Z",
  "source": "dddpg",
  "data": {
    "decision_id": 123,
    "workspace_id": "/dopemux-mvp",
    "instance_id": "A",
    "decision": {...}  # Full Decision object
  }
}
```

---

## 6. Recommended Data Model Additions

### Priority 1: MUST HAVE (for storage layer)

```python
# In core/models.py

class Decision(BaseModel):
    # ADD:
    workspace_id: str = Field(..., description="Workspace root path")
    instance_id: str = Field(default="A", description="Dopemux instance")
    visibility: str = Field(default="shared", description="private|shared|global")

    # ADD:
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)
    code_references: List[str] = Field(default_factory=list)  # File paths

class DecisionRelationship(BaseModel):
    """NEW: Typed graph relationships"""
    from_id: int
    to_id: int
    rel_type: str  # "supersedes", "implements", etc
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Priority 2: NICE TO HAVE (can add later)

```python
class WorkSession(BaseModel):
    """Track active work sessions"""
    id: str
    workspace_id: str
    instance_id: str
    started_at: datetime
    last_activity: datetime
    focus_level: Optional[int]

class AgentActivity(BaseModel):
    """Track agent interactions"""
    agent_id: str
    decision_id: int
    action: str
    timestamp: datetime
```

### Priority 3: FUTURE (post-MVP)

```python
class CodeReference(BaseModel):
    """Link decisions to code"""
    decision_id: int
    file_path: str
    line_range: Optional[Tuple[int, int]]

class DecisionTemplate(BaseModel):
    """Reusable decision patterns"""
    name: str
    template: str
    suggested_tags: List[str]
```

---

## 7. Storage Layer Architecture (FINAL)

### Recommended Hybrid Approach

```
┌────────────────────────────────────────────────────────┐
│              DDDPG Storage Architecture                │
├────────────────────────────────────────────────────────┤
│                                                        │
│  PostgreSQL AGE (Source of Truth)                     │
│  ├─ All decisions (graph + properties)                │
│  ├─ Relationships (typed edges)                       │
│  ├─ Full-text search (pg_trgm)                        │
│  └─ Multi-instance partitioning                       │
│                                                        │
│  ↕ EventBus (Redis Streams)                           │
│                                                        │
│  SQLite Cache (Per-Instance, Read-Only)               │
│  ├─ Local fast reads                                  │
│  ├─ FTS5 for offline search                           │
│  ├─ Synced via EventBus                               │
│  └─ Expires after TTL                                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Write Path
```
Decision created → Postgres → EventBus → All SQLite caches updated
```

### Read Path (ADHD-optimized)
```
Query → SQLite cache (< 1ms) → If miss → Postgres → Cache result
```

---

## 8. Migration from Existing Systems

### From ConPort MCP (SQLite)
```sql
-- Map old schema to new
INSERT INTO decisions (
    workspace_id,  -- ← Get from DOPEMUX_WORKSPACE_ID
    instance_id,   -- ← "A" (main instance)
    visibility,    -- ← "shared"
    summary,       -- ← Direct copy
    rationale,     -- ← Direct copy
    tags,          -- ← Parse JSON array
    created_at     -- ← timestamp field
)
SELECT
    '/dopemux-mvp',
    'A',
    'shared',
    summary,
    rationale,
    tags,
    timestamp
FROM old_decisions;
```

---

## 9. Final Recommendations

### Data Models to Add NOW

1. ✅ **Add to Decision model**:
   ```python
   workspace_id: str = Field(...)
   instance_id: str = Field(default="A")
   visibility: str = Field(default="shared")
   agent_metadata: Dict[str, Any] = {}
   ```

2. ✅ **Add DecisionRelationship model**:
   ```python
   from_id, to_id, rel_type, weight
   ```

3. ✅ **Add WorkSession model** (for ADHD tracking):
   ```python
   session_id, workspace_id, instance_id, focus_level
   ```

### Storage Architecture

✅ **Use Hybrid Approach**:
- PostgreSQL AGE for source of truth + graph
- SQLite for per-instance cache
- EventBus (Redis Streams) for synchronization
- Minimize ConPort MCP compatibility layer

### Implementation Order

1. **Week 1 Day 2** (NOW):
   - Update Decision model with workspace_id, instance_id
   - Create DecisionRelationship model
   - Create WorkSession model (basic)

2. **Week 1 Day 3-4**:
   - Build Postgres AGE storage adapter
   - Build SQLite cache adapter
   - Build storage interface (abstract)

3. **Week 1 Day 5**:
   - EventBus integration (write-through cache)
   - Multi-instance isolation testing

---

## 10. Questions to Answer

### Q1: Should decisions be globally unique or per-instance?

**Answer**: Globally unique ID, but filtered by workspace_id + instance_id

```sql
id SERIAL PRIMARY KEY,  -- Global sequence
workspace_id VARCHAR,   -- Instance identifier
instance_id VARCHAR,    -- A, B, feature-auth, etc
```

### Q2: How do we handle decision visibility across instances?

**Answer**: Three-tier visibility

```python
visibility = "private"   # Only this instance
visibility = "shared"    # All instances in workspace
visibility = "global"    # All workspaces (rare)
```

### Q3: Do we need separate tables for Task decisions?

**Answer**: No, use `decision_type` + `agent_metadata`

```python
decision_type = DecisionType.IMPLEMENTATION
agent_metadata["task_orchestrator"] = {
    "status": "IN_PROGRESS",
    "priority": 4
}
```

---

## Conclusion

✅ **We're ready to build storage**, but need to:

1. Update `Decision` model with instance/workspace fields
2. Add `DecisionRelationship` model
3. Add `WorkSession` model
4. Use hybrid Postgres + SQLite architecture
5. Design for multi-instance from day 1

**Estimated Time**: Add 30 minutes to update models, then proceed with storage layer

**Risk**: LOW - We've thought through the complexity

**Next**: Update models, then build storage! 🚀
