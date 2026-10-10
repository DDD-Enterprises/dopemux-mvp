---
id: storage-design
title: Storage Design
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Storage Design (reference) for dopemux documentation and developer workflows.
---
# 🏗️ DDDPG Storage Layer - Design Document

**Date**: 2025-10-29
**Status**: Design Phase
**Goal**: Production-ready hybrid storage (Postgres AGE + SQLite cache)

---

## 1. Architecture Overview

### The Hybrid Approach

```
┌─────────────────────────────────────────────────────────────┐
│                   DDDPG Storage Layer                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         PostgreSQL AGE (Source of Truth)            │   │
│  │  • All decisions (vertices)                         │   │
│  │  • All relationships (edges)                        │   │
│  │  • Graph queries (Cypher-like)                      │   │
│  │  • Full-text search                                 │   │
│  │  • ACID transactions                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↕                                  │
│                    EventBus (Redis)                         │
│              (decision.created, .updated, etc)              │
│                          ↕                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      SQLite Cache (Per-Instance, Fast Reads)        │   │
│  │  • Subset of decisions (instance-specific)          │   │
│  │  • FTS5 for local search                            │   │
│  │  • Read-only (synced via EventBus)                  │   │
│  │  • TTL-based expiration                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Write Path
```
Client → Storage Interface
       → Postgres AGE (persist)
       → EventBus (publish decision.created)
       → All SQLite caches (update)
       → Return success
```

### Read Path (Optimized)
```
Client → Storage Interface
       → SQLite Cache (check)
       → If HIT: Return (< 1ms)
       → If MISS: Postgres AGE → Cache result → Return
```

---

## 2. PostgreSQL AGE Schema

### Vertices (Nodes)

```sql
-- Create AGE graph
SELECT create_graph('dddpg');

-- Create vertex label for decisions
SELECT create_vlabel('dddpg', 'decision');

-- Decision properties (stored as JSONB in AGE)
{
  "id": 1,
  "summary": "Use DDDPG for context",
  "rationale": "Unified system better",
  "workspace_id": "/dopemux-mvp",
  "instance_id": "A",
  "visibility": "shared",
  "status": "active",
  "decision_type": "architecture",
  "tags": ["dddpg", "architecture"],
  "cognitive_load": 4,
  "agent_metadata": {
    "serena": {"hover_count": 0}
  },
  "created_at": "2025-10-29T03:00:00Z",
  "updated_at": null
}
```

### Edges (Relationships)

```sql
-- Create edge labels for each relationship type
SELECT create_elabel('dddpg', 'supersedes');
SELECT create_elabel('dddpg', 'implements');
SELECT create_elabel('dddpg', 'relates_to');
SELECT create_elabel('dddpg', 'contradicts');
SELECT create_elabel('dddpg', 'requires');
SELECT create_elabel('dddpg', 'suggests');

-- Edge properties
{
  "weight": 0.9,
  "created_at": "2025-10-29T03:00:00Z",
  "created_by": "task-orchestrator",
  "metadata": {}
}
```

### Indexes for Performance

```sql
-- Property indexes for fast lookups
CREATE INDEX decision_workspace_idx ON ag_catalog.decision
  USING btree ((properties->>'workspace_id'));

CREATE INDEX decision_instance_idx ON ag_catalog.decision
  USING btree ((properties->>'instance_id'));

CREATE INDEX decision_visibility_idx ON ag_catalog.decision
  USING btree ((properties->>'visibility'));

CREATE INDEX decision_status_idx ON ag_catalog.decision
  USING btree ((properties->>'status'));

-- Composite index for multi-instance queries
CREATE INDEX decision_workspace_instance_idx ON ag_catalog.decision
  USING btree ((properties->>'workspace_id'), (properties->>'instance_id'));

-- Full-text search on summary + rationale
CREATE INDEX decision_fts_idx ON ag_catalog.decision
  USING gin (to_tsvector('english',
    properties->>'summary' || ' ' || COALESCE(properties->>'rationale', '')));
```

### Common Queries

```sql
-- Find all decisions for an instance
SELECT * FROM cypher('dddpg', $$
  MATCH (d:decision)
  WHERE d.workspace_id = '/dopemux-mvp'
    AND d.instance_id = 'A'
    AND d.visibility IN ['shared', 'global']
  RETURN d
  ORDER BY d.created_at DESC
  LIMIT 100
$$) AS (decision agtype);

-- Find decisions that implement decision #5
SELECT * FROM cypher('dddpg', $$
  MATCH (d1:decision)-[:implements]->(d2:decision)
  WHERE d2.id = 5
  RETURN d1
$$) AS (decision agtype);

-- Graph traversal (depth-2)
SELECT * FROM cypher('dddpg', $$
  MATCH path = (d1:decision)-[*1..2]-(d2:decision)
  WHERE d1.id = 10
  RETURN path
$$) AS (path agtype);

-- Full-text search
SELECT * FROM cypher('dddpg', $$
  MATCH (d:decision)
  WHERE d.summary ~* 'event.*bridge'
  RETURN d
$$) AS (decision agtype);
```

---

## 3. SQLite Cache Schema

### Per-Instance Database

**Location**: `~/.dddpg/cache/{workspace_id}/{instance_id}/decisions.db`

**Example**:
- Main: `~/.dddpg/cache/dopemux-mvp/A/decisions.db`
- Worktree: `~/.dddpg/cache/dopemux-mvp/feature-auth/decisions.db`

### Schema

```sql
-- Minimal schema for fast reads
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    summary TEXT NOT NULL,
    rationale TEXT,
    implementation_details TEXT,

    -- Multi-instance
    workspace_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    visibility TEXT NOT NULL,  -- private, shared, global

    -- Classification
    status TEXT NOT NULL DEFAULT 'active',
    decision_type TEXT,
    tags TEXT,  -- JSON array

    -- Metadata
    cognitive_load INTEGER,
    agent_metadata TEXT,  -- JSON
    code_references TEXT,  -- JSON array

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT,

    -- Cache metadata
    cached_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cache_ttl INTEGER DEFAULT 3600  -- 1 hour TTL
);

-- FTS5 for fast local search
CREATE VIRTUAL TABLE decisions_fts USING fts5(
    summary,
    rationale,
    implementation_details,
    tags,
    content=decisions,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER decisions_ai AFTER INSERT ON decisions BEGIN
    INSERT INTO decisions_fts(rowid, summary, rationale, implementation_details, tags)
    VALUES (new.id, new.summary, new.rationale, new.implementation_details, new.tags);
END;

CREATE TRIGGER decisions_ad AFTER DELETE ON decisions BEGIN
    DELETE FROM decisions_fts WHERE rowid = old.id;
END;

CREATE TRIGGER decisions_au AFTER UPDATE ON decisions BEGIN
    DELETE FROM decisions_fts WHERE rowid = old.id;
    INSERT INTO decisions_fts(rowid, summary, rationale, implementation_details, tags)
    VALUES (new.id, new.summary, new.rationale, new.implementation_details, new.tags);
END;

-- Indexes
CREATE INDEX idx_workspace_instance ON decisions(workspace_id, instance_id);
CREATE INDEX idx_visibility ON decisions(visibility);
CREATE INDEX idx_status ON decisions(status);
CREATE INDEX idx_created ON decisions(created_at DESC);
```

### Cache Invalidation

```sql
-- Delete expired entries
DELETE FROM decisions
WHERE (unixepoch('now') - unixepoch(cached_at)) > cache_ttl;

-- Update cache entry
INSERT OR REPLACE INTO decisions (...) VALUES (...);
```

---

## 4. Storage Interface (Abstract)

### Base Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import Decision, DecisionRelationship, DecisionGraph

class StorageBackend(ABC):
    """Abstract storage interface"""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to storage backend"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from storage"""
        pass

    # Decisions
    @abstractmethod
    async def create_decision(self, decision: Decision) -> Decision:
        """Create a new decision, returns with ID"""
        pass

    @abstractmethod
    async def get_decision(self, decision_id: int) -> Optional[Decision]:
        """Get decision by ID"""
        pass

    @abstractmethod
    async def list_decisions(
        self,
        workspace_id: str,
        instance_id: str,
        include_shared: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Decision]:
        """List decisions for instance"""
        pass

    @abstractmethod
    async def update_decision(self, decision: Decision) -> Decision:
        """Update existing decision"""
        pass

    @abstractmethod
    async def delete_decision(self, decision_id: int) -> bool:
        """Delete decision (soft delete - set status=archived)"""
        pass

    # Relationships
    @abstractmethod
    async def create_relationship(self, rel: DecisionRelationship) -> DecisionRelationship:
        """Create relationship between decisions"""
        pass

    @abstractmethod
    async def get_relationships(self, decision_id: int) -> List[DecisionRelationship]:
        """Get all relationships for a decision"""
        pass

    # Graph queries
    @abstractmethod
    async def query_graph(
        self,
        start_decision_id: int,
        depth: int = 1,
        relationship_types: Optional[List[str]] = None
    ) -> DecisionGraph:
        """Traverse graph from starting decision"""
        pass

    # Search
    @abstractmethod
    async def search_decisions(
        self,
        query: str,
        workspace_id: str,
        instance_id: str,
        limit: int = 10
    ) -> List[Decision]:
        """Full-text search"""
        pass
```

---

## 5. Implementation Strategy

### Phase 1: PostgreSQL AGE Backend

**File**: `storage/postgres_age.py`

```python
class PostgresAGEBackend(StorageBackend):
    """PostgreSQL AGE graph storage"""

    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        self.pool = None

    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.conn_string)
        # Initialize AGE extension
        await self._init_graph()

    async def create_decision(self, decision: Decision) -> Decision:
        """
1. Generate properties dict from Decision model
1. Execute Cypher CREATE query
1. Return decision with ID
        """
        query = """
        SELECT * FROM cypher('dddpg', $$
          CREATE (d:decision {
            summary: $summary,
            rationale: $rationale,
            workspace_id: $workspace_id,
            instance_id: $instance_id,
            visibility: $visibility,
            ...
          })
          RETURN d
        $$) AS (decision agtype);
        """
        # Execute and parse result
        ...
```

### Phase 2: SQLite Cache Backend

**File**: `storage/sqlite_cache.py`

```python
class SQLiteCacheBackend(StorageBackend):
    """SQLite local cache - read-optimized"""

    def __init__(self, cache_dir: str, workspace_id: str, instance_id: str):
        self.cache_path = Path(cache_dir) / workspace_id / instance_id / "decisions.db"
        self.conn = None

    async def connect(self):
        """Create/open cache database"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.cache_path)
        await self._init_schema()

    async def list_decisions(self, workspace_id, instance_id, ...) -> List[Decision]:
        """
        Fast read from local cache
1. Query SQLite
1. Parse rows to Decision models
1. Return list
        """
        query = """
        SELECT * FROM decisions
        WHERE workspace_id = ? AND instance_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """
        # Execute and parse
        ...
```

### Phase 3: Hybrid Storage Manager

**File**: `storage/hybrid.py`

```python
class HybridStorage(StorageBackend):
    """
    Hybrid storage: Postgres (source of truth) + SQLite (cache)
    Coordinates writes, optimizes reads
    """

    def __init__(
        self,
        postgres: PostgresAGEBackend,
        sqlite: SQLiteCacheBackend,
        eventbus: Optional[EventBusPublisher] = None
    ):
        self.postgres = postgres
        self.sqlite = sqlite
        self.eventbus = eventbus

    async def create_decision(self, decision: Decision) -> Decision:
        """
        Write path:
1. Persist to Postgres (source of truth)
1. Update local SQLite cache
1. Publish to EventBus (other instances will update their caches)
        """
        # 1. Postgres
        decision = await self.postgres.create_decision(decision)

        # 2. Local cache
        await self.sqlite.create_decision(decision)

        # 3. EventBus
        if self.eventbus:
            await self.eventbus.publish("decision.created", decision.dict())

        return decision

    async def get_decision(self, decision_id: int) -> Optional[Decision]:
        """
        Read path (optimized):
1. Check SQLite cache (< 1ms)
1. If miss, query Postgres
1. Cache result
        """
        # Cache first
        decision = await self.sqlite.get_decision(decision_id)
        if decision:
            return decision

        # Cache miss - query Postgres
        decision = await self.postgres.get_decision(decision_id)
        if decision:
            # Cache for next time
            await self.sqlite.create_decision(decision)

        return decision
```

---

## 6. EventBus Integration

### Event Publisher

**File**: `storage/events.py`

```python
class EventBusPublisher:
    """Publish storage events to Redis Streams"""

    def __init__(self, redis_url: str, stream: str = "dddpg:events"):
        self.redis_url = redis_url
        self.stream = stream
        self.redis = None

    async def connect(self):
        self.redis = await redis.from_url(self.redis_url)

    async def publish(self, event_type: str, data: dict):
        """
        Publish event to Redis Stream
        Format compatible with Path C Event Bridge
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "dddpg",
            "data": json.dumps(data)
        }

        await self.redis.xadd(self.stream, event)
```

### Event Consumer (Cache Sync)

```python
class CacheSyncConsumer:
    """
    Listens to EventBus and updates local SQLite cache
    Used by other instances to stay in sync
    """

    async def start(self):
        """
        Subscribe to dddpg:events stream
        Handle decision.created, decision.updated, decision.deleted
        Update local cache accordingly
        """
        while self.running:
            messages = await self.redis.xreadgroup(
                "dddpg-cache-sync",
                self.instance_id,
                {self.stream: '>'},
                count=10,
                block=1000
            )

            for stream, events in messages:
                for event_id, event_data in events:
                    await self._handle_event(event_data)

    async def _handle_event(self, event_data):
        """Update cache based on event type"""
        event_type = event_data['event_type']

        if event_type == "decision.created":
            # Add to cache
            decision = Decision(**json.loads(event_data['data']))
            await self.cache.create_decision(decision)

        elif event_type == "decision.updated":
            # Update cache
            decision = Decision(**json.loads(event_data['data']))
            await self.cache.update_decision(decision)

        elif event_type == "decision.deleted":
            # Remove from cache
            decision_id = json.loads(event_data['data'])['id']
            await self.cache.delete_decision(decision_id)
```

---

## 7. File Structure

```
services/dddpg/storage/
├── __init__.py              # Export interfaces
├── interface.py             # StorageBackend abstract class
├── postgres_age.py          # PostgreSQL AGE implementation
├── sqlite_cache.py          # SQLite cache implementation
├── hybrid.py                # HybridStorage coordinator
├── events.py                # EventBus publisher/consumer
└── migrations/              # Database migrations
    ├── postgres/
    │   ├── 001_init_graph.sql
    │   └── 002_add_indexes.sql
    └── sqlite/
        └── 001_init_cache.sql
```

---

## 8. Testing Strategy

### Unit Tests

```python
# test_storage.py

async def test_create_decision_postgres():
    """Test creating decision in Postgres"""
    backend = PostgresAGEBackend(TEST_DB_URL)
    await backend.connect()

    decision = Decision(
        summary="Test decision",
        workspace_id="/test",
        instance_id="A"
    )

    result = await backend.create_decision(decision)
    assert result.id is not None
    assert result.summary == "Test decision"

async def test_cache_hit():
    """Test SQLite cache hit"""
    hybrid = HybridStorage(postgres, sqlite)

    # First read (cache miss)
    d1 = await hybrid.get_decision(1)  # Queries Postgres

    # Second read (cache hit)
    d2 = await hybrid.get_decision(1)  # Queries SQLite (< 1ms)

    assert d1 == d2

async def test_multi_instance_isolation():
    """Test instance isolation with visibility"""
    # Instance A creates private decision
    d_private = Decision(
        summary="Private to A",
        workspace_id="/test",
        instance_id="A",
        visibility=DecisionVisibility.PRIVATE
    )
    await storage_A.create_decision(d_private)

    # Instance B should NOT see it
    decisions_B = await storage_B.list_decisions("/test", "B")
    assert d_private.id not in [d.id for d in decisions_B]
```

---

## 9. Performance Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| Create decision | < 50ms | Postgres insert + cache |
| Get decision (cached) | < 1ms | SQLite local read |
| Get decision (miss) | < 20ms | Postgres query |
| List decisions (100) | < 10ms | SQLite cache |
| Graph query (depth-2) | < 100ms | Postgres AGE indexes |
| Full-text search | < 50ms | Postgres GIN index |
| EventBus publish | < 10ms | Redis XADD |

---

## 10. Migration Plan

### From ConPort MCP (SQLite)

```python
async def migrate_from_conport_mcp(old_db_path: str):
    """
    Migrate decisions from ConPort MCP SQLite to DDDPG
    """
    # Connect to old database
    old_conn = await aiosqlite.connect(old_db_path)

    # Read all decisions
    cursor = await old_conn.execute(
        "SELECT id, summary, rationale, implementation_details, tags, timestamp FROM decisions"
    )

    # Convert to DDDPG format
    for row in await cursor.fetchall():
        decision = Decision(
            summary=row[1],
            rationale=row[2],
            implementation_details=row[3],
            tags=json.loads(row[4]) if row[4] else [],
            workspace_id="/dopemux-mvp",  # From env
            instance_id="A",
            visibility=DecisionVisibility.SHARED,
            created_at=datetime.fromisoformat(row[5])
        )

        # Write to DDDPG
        await storage.create_decision(decision)
```

---

## 11. Implementation Checklist

### Phase 1: Core Storage (Tonight?)
- [ ] Create `storage/interface.py` (abstract base)
- [ ] Create `storage/postgres_age.py` (basic CRUD)
- [ ] Create `storage/sqlite_cache.py` (basic CRUD)
- [ ] Test Postgres create/read
- [ ] Test SQLite create/read

### Phase 2: Hybrid + EventBus (Tomorrow AM)
- [ ] Create `storage/hybrid.py` (coordinator)
- [ ] Create `storage/events.py` (publisher/consumer)
- [ ] Test hybrid write path
- [ ] Test cache sync via EventBus

### Phase 3: Graph Queries (Tomorrow PM)
- [ ] Implement graph traversal (Postgres AGE)
- [ ] Implement relationship creation
- [ ] Test depth-1, depth-2, depth-3 queries

### Phase 4: Polish (Evening)
- [ ] Add full-text search
- [ ] Add migration scripts
- [ ] Performance testing
- [ ] Documentation

---

## 12. Decision Points

### Q1: Start with Postgres or SQLite?

**Answer**: Start with SQLite (simpler), add Postgres after

**Reasoning**:
- SQLite works standalone (no Postgres setup needed)
- Can validate models and queries quickly
- Postgres adds graph queries (can be later)
- Hybrid can use SQLite-only mode initially

### Q2: Build full hybrid tonight or iterate?

**Answer**: Iterate - SQLite first, then Postgres, then hybrid

**Reasoning**:
- SQLite = 1 hour (storage working tonight!)
- Postgres AGE = 2 hours (tomorrow AM)
- Hybrid = 1 hour (tomorrow PM)
- EventBus = already proven (Path C)

### Q3: Graph queries now or later?

**Answer**: Later - basic CRUD first

**Reasoning**:
- Graph queries need Postgres AGE
- Basic CRUD works with SQLite
- Can add graph incrementally
- YAGNI until we prove value

---

## Recommendation

### Tonight (1-2 hours):
1. Build SQLite storage backend (CRUD)
1. Test with actual Decision models
1. Validate multi-instance isolation
1. Get DDDPG storing decisions! 🎉

### Tomorrow:
1. Add Postgres AGE backend
1. Build hybrid coordinator
1. Add graph queries
1. EventBus integration

**Start with SQLite = Ship something tonight! 🚀**
