# Implementation Plan: Infrastructure Consolidation

**Task ID**: IP-003
**Priority**: 🟡 HIGH VALUE
**Duration**: 6-9 days (12-18 focus blocks @ 25min each)
**Complexity**: 0.60 (MEDIUM-HIGH)
**Dependencies**: None (can run parallel with IP-001, IP-002)
**Risk Level**: MEDIUM (phased approach mitigates risk)

---

## Executive Summary

**Problem**: Infrastructure fragmentation with 8 orphaned Docker containers, 3 PostgreSQL instances (1 unused), duplicate Redis instances, and competing vector DBs (Milvus vs Qdrant).

**Solution**: 3-phase consolidation eliminating orphaned containers, consolidating databases, and standardizing on Qdrant vector DB.

**Impact**:
- ✅ Eliminates 8 containers (19 → 11 containers)
- ✅ Saves 2-3GB memory
- ✅ Resolves port conflicts (5455 collision)
- ✅ Reduces operational complexity
- ✅ Standardizes infrastructure stack

**Success Criteria**:
- [ ] Only 1 PostgreSQL instance running
- [ ] 2 Redis instances (shared + events)
- [ ] Only Qdrant for vector storage (Milvus removed)
- [ ] Zero data loss during migrations
- [ ] All services operational after consolidation

---

## Current Infrastructure State

### Discovered Containers

**PostgreSQL Instances** (3 instances → should be 1):
```
1. dopemux-postgres           ORPHANED - No connections, can delete
2. dopemux-postgres-age       ACTIVE - Used by ConPort, port 5432
3. conport-kg-postgres-age    DEFERRED - Port 5455 (CONFLICTS!), part of old stack
```

**Redis Instances** (4+ instances → should be 2):
```
1. dopemux-redis-primary      UNNAMED - Used by services, port 6379
2. dopemux-redis-events       ACTIVE - Event bus, port 6380
3. conport-kg-redis           DEFERRED - Part of old stack, port 6381
4. redis_leantime             ISOLATED - Leantime only, keep separate
```

**Vector DBs** (2 different technologies → should be 1):
```
Qdrant Stack (1 container):
  - qdrant                    ACTIVE - Simple, modern, port 6333

Milvus Stack (3 containers):
  - milvus-standalone         Complex multi-component system
  - milvus-etcd               Coordination service
  - milvus-minio              Object storage
  Total: 3 containers for same functionality as Qdrant's 1
```

**Total Bloat**: 8 extra containers, ~2-3GB wasted memory

---

## Phase 1: Decommission Orphaned PostgreSQL (1 hour, ZERO risk)

### Tasks
1. Verify no connections to `dopemux-postgres`
2. Backup (safety measure)
3. Stop and remove container
4. Remove volume
5. Update docker-compose

**Verification Script** (`scripts/verify_orphaned_postgres.sh`):
```bash
#!/bin/bash
# Verify dopemux-postgres is truly orphaned

echo "🔍 Checking connections to dopemux-postgres..."

# Check active connections
docker exec dopemux-postgres psql -U dopemux -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE datname != 'postgres';"

# If count = 0, it's safe to remove

# Check which services reference it in config
grep -r "dopemux-postgres" services/ --include="*.py" --include="*.yaml" --include="*.env"

# Should show NO references (or only old commented code)

echo "✅ Verification complete"
```

**Backup Script** (`scripts/backup_postgres_before_deletion.sh`):
```bash
#!/bin/bash
# Safety backup before deletion (even though orphaned)

BACKUP_DIR="./backups/postgres-orphaned-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "💾 Backing up dopemux-postgres (safety measure)..."

docker exec dopemux-postgres pg_dumpall -U dopemux > "$BACKUP_DIR/full_backup.sql"

echo "✅ Backup saved to $BACKUP_DIR"
echo "ℹ️  If container truly orphaned, backup can be deleted in 30 days"
```

**Deletion Script** (`scripts/decommission_orphaned_postgres.sh`):
```bash
#!/bin/bash
# Safely decommission orphaned PostgreSQL container

echo "🗑️  Decommissioning dopemux-postgres..."

# 1. Stop container
docker stop dopemux-postgres

# 2. Wait 5 minutes and check for service errors
echo "⏰ Waiting 5 minutes to verify no errors..."
sleep 300

# 3. Check logs for database connection errors
echo "🔍 Checking service logs for database errors..."
docker-compose logs --tail=100 conport 2>&1 | grep -i "connection\|database\|error" || echo "No errors found"
docker-compose logs --tail=100 serena 2>&1 | grep -i "connection\|database\|error" || echo "No errors found"

# 4. If no errors, remove container and volume
read -p "No errors found. Proceed with deletion? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rm dopemux-postgres
    docker volume rm dopemux-postgres-data
    echo "✅ Orphaned PostgreSQL removed!"
else
    echo "⏸️  Deletion cancelled. Restarting container..."
    docker start dopemux-postgres
fi
```

**Update Docker Compose** (`docker-compose.yml`):
```yaml
# REMOVE this entire block:
  # dopemux-postgres:
  #   image: postgres:16
  #   container_name: dopemux-postgres
  #   environment:
  #     POSTGRES_USER: dopemux
  #     POSTGRES_PASSWORD: dopemux_dev_password
  #     POSTGRES_DB: dopemux
  #   ports:
  #     - "5433:5432"  # Avoid conflict with primary
  #   volumes:
  #     - dopemux-postgres-data:/var/lib/postgresql/data

# volumes:
#   dopemux-postgres-data:  # REMOVE
```

**Deliverables**:
- [ ] Verified orphaned (no connections)
- [ ] Backup created
- [ ] Container and volume deleted
- [ ] Docker compose updated
- [ ] Services still operational
- [ ] ~500MB disk space reclaimed

**Risk**: ZERO (verified orphaned)
**Time**: 1 hour
**Impact**: Instant cleanup win! 🎉

---

## Phase 2: Consolidate Redis Instances (3-4 days, MEDIUM risk)

### Current Redis State

**4 Redis Instances**:
```yaml
1. dopemux-redis-primary (port 6379):
   - Used by: ADHD Engine (db=5), Serena (db=0), dope-context (caching)
   - Purpose: General shared Redis
   - Status: KEEP

2. dopemux-redis-events (port 6380):
   - Used by: Integration Bridge (db=6)
   - Purpose: Event bus pub/sub
   - Status: KEEP (dedicated for events)

3. conport-kg-redis (port 6381):
   - Used by: NOTHING (part of old conport-kg stack)
   - Purpose: Obsolete
   - Status: DELETE

4. redis_leantime (port 6382):
   - Used by: Leantime PM system
   - Purpose: Leantime session storage
   - Status: KEEP (Leantime isolation)
```

**Consolidation Target**: 4 instances → 2 instances
- Keep: dopemux-redis-primary, dopemux-redis-events
- Delete: conport-kg-redis (orphaned)
- Keep: redis_leantime (appropriate isolation)

**Savings**: 1 container, ~100MB memory

### Tasks

**Day 1: Verify conport-kg-redis Orphaned**

```bash
# Check connections
docker exec conport-kg-redis redis-cli CLIENT LIST

# Check which services reference it
grep -r "6381\|conport-kg-redis" services/ --include="*.py" --include="*.yaml"

# Should find NO active references
```

**Day 2: Migrate Any Remaining Data** (if found)

```bash
# Check if any data exists
docker exec conport-kg-redis redis-cli DBSIZE

# If DBSIZE > 0, migrate to dopemux-redis-primary
docker exec conport-kg-redis redis-cli --rdb /data/dump.rdb SAVE
docker cp conport-kg-redis:/data/dump.rdb ./dump.rdb
docker cp ./dump.rdb dopemux-redis-primary:/data/import.rdb
docker exec dopemux-redis-primary redis-cli --rdb /data/import.rdb RESTORE
```

**Day 3-4: Remove Container**

```bash
# Stop and remove
docker stop conport-kg-redis
docker rm conport-kg-redis
docker volume rm conport-kg-redis-data

# Update docker-compose.yml
# Remove conport-kg-redis section

# Verify services still operational
docker-compose ps
docker-compose logs --tail=20 conport
```

**Deliverables**:
- [ ] conport-kg-redis verified orphaned
- [ ] Data migrated (if any existed)
- [ ] Container removed
- [ ] Docker compose updated
- [ ] ~100MB memory saved

---

## Phase 3: Migrate Milvus → Qdrant (3-5 days, MEDIUM-HIGH risk)

### Why Migrate?

**Milvus Issues**:
- Complex: 3-container stack (milvus + etcd + minio)
- Memory: ~1-1.5GB for 3 containers
- Maintenance: 3 health checks, 3 failure points
- Complexity: Requires etcd coordination and minio object storage

**Qdrant Advantages**:
- Simple: 1 container
- Memory: ~300-500MB total
- Modern: Built for cloud-native workflows
- Compatible: Already used by ConPort and dope-context successfully
- Performance: Comparable to Milvus for our scale

**Migration Impact**:
- Eliminates 3 containers
- Saves ~1-1.5GB memory
- Reduces operational complexity
- Standardizes on single vector DB technology

### Current Milvus Usage

**Who Uses Milvus?**
```bash
# Search codebase for Milvus clients
grep -r "MilvusClient\|pymilvus\|milvus" services/ --include="*.py"

# Expected: claude-context service (services/claude-context/)
```

**What's Stored in Milvus?**
- Code embeddings for claude-context MCP
- Document embeddings
- Collection schemas

### Migration Strategy

**Day 1: Audit Milvus Data**

```python
# Script: scripts/audit_milvus_collections.py
from pymilvus import connections, Collection, utility

# Connect to Milvus
connections.connect(host="localhost", port="19530")

# List collections
collections = utility.list_collections()
print(f"📊 Found {len(collections)} collections:")

for coll_name in collections:
    coll = Collection(coll_name)
    coll.load()
    count = coll.num_entities
    print(f"  - {coll_name}: {count} entities")

    # Get schema
    schema = coll.schema
    print(f"    Fields: {[f.name for f in schema.fields]}")
    print(f"    Dimension: {[f.params for f in schema.fields if 'dim' in f.params]}")

connections.disconnect()
```

**Day 2: Export Milvus Data**

```python
# Script: scripts/export_milvus_to_qdrant.py
"""
Export all Milvus collections to Qdrant-compatible format.
"""
from pymilvus import connections, Collection
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

# Connect to both
connections.connect(host="localhost", port="19530")
qdrant = QdrantClient(url="http://localhost:6333")

def migrate_collection(milvus_collection_name: str, qdrant_collection_name: str):
    """Migrate single collection from Milvus to Qdrant."""
    print(f"🔄 Migrating {milvus_collection_name} → {qdrant_collection_name}...")

    # Load Milvus collection
    milvus_coll = Collection(milvus_collection_name)
    milvus_coll.load()

    # Get schema info
    schema = milvus_coll.schema
    vector_field = [f for f in schema.fields if f.dtype == DataType.FLOAT_VECTOR][0]
    vector_dim = vector_field.params['dim']

    # Create Qdrant collection
    qdrant.create_collection(
        collection_name=qdrant_collection_name,
        vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE)
    )

    # Query all vectors from Milvus
    results = milvus_coll.query(
        expr="id >= 0",
        output_fields=["*"]
    )

    # Batch upsert to Qdrant
    batch_size = 100
    for i in range(0, len(results), batch_size):
        batch = results[i:i+batch_size]

        points = [
            PointStruct(
                id=item['id'],
                vector=item[vector_field.name],
                payload={k: v for k, v in item.items() if k != vector_field.name}
            )
            for item in batch
        ]

        qdrant.upsert(
            collection_name=qdrant_collection_name,
            points=points
        )

        print(f"  Migrated {len(points)} vectors...")

    print(f"✅ Migrated {len(results)} total vectors")

# Migrate all collections
# (Adjust collection names based on audit results)
migrate_collection("claude_context_code", "claude_context_code")
migrate_collection("claude_context_docs", "claude_context_docs")
```

**Day 3-4: Test Qdrant Migration**

```python
# Script: scripts/test_qdrant_migration.py
"""
Verify Qdrant migration matches Milvus functionality.
"""
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Test search functionality
test_vector = [0.1] * 1024  # Example query vector

results = client.search(
    collection_name="claude_context_code",
    query_vector=test_vector,
    limit=10
)

assert len(results) > 0, "Search returned results"
assert all(r.score >= 0 for r in results), "Scores valid"

print(f"✅ Found {len(results)} results")
print(f"✅ Top score: {results[0].score:.3f}")
print("✅ Qdrant migration successful!")
```

**Day 5: Update Service Clients**

Update all services using Milvus to use Qdrant:

```python
# services/claude-context/vector_store.py

# BEFORE (Milvus):
from pymilvus import connections, Collection

connections.connect(host="localhost", port="19530")
collection = Collection("claude_context_code")

# AFTER (Qdrant):
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
# Use existing Qdrant API (same as ConPort, dope-context)
```

**Day 6: Decommission Milvus Stack**

```bash
# Stop Milvus containers
docker stop milvus-standalone milvus-etcd milvus-minio

# Test services for 24 hours

# If successful, remove:
docker rm milvus-standalone milvus-etcd milvus-minio
docker volume rm milvus-data etcd-data minio-data

# Update docker-compose.yml (remove milvus section)
```

**Deliverables**:
- [ ] Milvus data migrated to Qdrant
- [ ] Services using Qdrant successfully
- [ ] 3 containers eliminated
- [ ] ~1-1.5GB memory saved
- [ ] Single vector DB technology

---

## Phase 4: PostgreSQL Consolidation (2-3 days, MEDIUM risk)

### Challenge: Port 5455 Conflict

**Current State**:
```
dopemux-postgres-age:     5432 (ACTIVE - ConPort uses this)
conport-kg-postgres-age:  5455 (DEFERRED - Old stack, CONFLICTS!)
```

**Conflict**: Port 5455 may be needed by other services. Two PostgreSQL AGE instances is redundant.

### Tasks

**Day 1: Audit conport-kg-postgres-age Usage**

```bash
# Check for connections
docker exec conport-kg-postgres-age psql -U conport -c "SELECT count(*) FROM pg_stat_activity WHERE datname != 'postgres';"

# Check code references
grep -r "5455\|conport-kg-postgres-age" services/ --include="*.py" --include="*.env"

# Likely result: ZERO active usage (part of old memory stack)
```

**Day 2: Data Migration (if needed)**

```bash
# Check if data exists
docker exec conport-kg-postgres-age psql -U conport -d conport_kg -c "\dt"

# If tables exist, migrate to dopemux-postgres-age
docker exec conport-kg-postgres-age pg_dump -U conport conport_kg > /tmp/conport_kg_backup.sql

# Import to main PostgreSQL
docker exec -i dopemux-postgres-age psql -U dopemux -d conport < /tmp/conport_kg_backup.sql

# Update ConPort config to use new database
```

**Day 3: Remove conport-kg-postgres-age**

```bash
docker stop conport-kg-postgres-age
docker rm conport-kg-postgres-age
docker volume rm conport-kg-postgres-data

# Update docker-compose.yml
# Remove conport-kg-postgres-age section

# Port 5455 now FREE for future use!
```

**Deliverables**:
- [ ] Only 1 PostgreSQL instance running
- [ ] Port 5455 freed
- [ ] All ConPort data preserved
- [ ] ~500MB memory saved
- [ ] Simplified PostgreSQL management

---

## Consolidated Infrastructure Architecture

### Before Consolidation (19 containers)
```
PostgreSQL:
  - dopemux-postgres          ❌ ORPHANED
  - dopemux-postgres-age      ✅ KEEP
  - conport-kg-postgres-age   ❌ REMOVE

Redis:
  - dopemux-redis-primary     ✅ KEEP
  - dopemux-redis-events      ✅ KEEP
  - conport-kg-redis          ❌ REMOVE
  - redis_leantime            ✅ KEEP (isolated)

Vector DBs:
  - qdrant                    ✅ KEEP
  - milvus-standalone         ❌ REMOVE
  - milvus-etcd               ❌ REMOVE
  - milvus-minio              ❌ REMOVE

Other:
  - (Various MCP services)    ✅ KEEP

Total: 19 containers
```

### After Consolidation (11 containers)
```
PostgreSQL:
  - dopemux-postgres-age      ✅ ONLY ONE

Redis:
  - dopemux-redis-primary     ✅ SHARED
  - dopemux-redis-events      ✅ EVENTS
  - redis_leantime            ✅ LEANTIME (isolated)

Vector DBs:
  - qdrant                    ✅ ONLY ONE

Other:
  - (MCP services)            ✅ UNCHANGED

Total: 11 containers (-8 containers, -42% reduction)
```

**Memory Savings**: ~2-3GB
**Complexity Reduction**: 3 DB technologies → cleaner operations
**Port Conflicts**: Resolved (5455 freed)

---

## Final Consolidated docker-compose.yml

```yaml
version: '3.8'

services:
  # === CONSOLIDATED DATABASES ===

  # Single PostgreSQL with AGE extension
  dopemux-postgres-age:
    image: apache/age:PG16_latest
    container_name: dopemux-postgres-age
    environment:
      POSTGRES_USER: dopemux
      POSTGRES_PASSWORD: dopemux_dev_password
      POSTGRES_DB: dopemux
    ports:
      - "5432:5432"
    volumes:
      - postgres-age-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dopemux"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Shared Redis (general purpose)
  dopemux-redis-primary:
    image: redis:7-alpine
    container_name: dopemux-redis-primary
    ports:
      - "6379:6379"
    volumes:
      - redis-primary-data:/data
    command: redis-server --appendonly yes

  # Events Redis (Integration Bridge)
  dopemux-redis-events:
    image: redis:7-alpine
    container_name: dopemux-redis-events
    ports:
      - "6380:6379"
    volumes:
      - redis-events-data:/data
    command: redis-server --appendonly yes

  # Leantime Redis (isolated, PM plane)
  redis_leantime:
    image: redis:7-alpine
    container_name: redis_leantime
    ports:
      - "6382:6379"
    volumes:
      - redis-leantime-data:/data

  # Single Vector DB (Qdrant)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage

  # === MCP SERVICES ===
  # (Unchanged - ConPort, Serena, etc.)

volumes:
  postgres-age-data:
  redis-primary-data:
  redis-events-data:
  redis-leantime-data:
  qdrant-data:

  # REMOVED volumes:
  # dopemux-postgres-data      ❌ DELETED
  # conport-kg-postgres-data   ❌ DELETED
  # conport-kg-redis-data      ❌ DELETED
  # milvus-data                ❌ DELETED
  # etcd-data                  ❌ DELETED
  # minio-data                 ❌ DELETED
```

---

## Testing Strategy

### Phase 1 Testing (PostgreSQL)
```bash
# After removing dopemux-postgres:
pytest tests/ -v  # All tests should pass
docker-compose logs --tail=100  # No connection errors
```

### Phase 2 Testing (Redis)
```bash
# After removing conport-kg-redis:
redis-cli -h localhost -p 6379 PING  # PRIMARY still works
redis-cli -h localhost -p 6380 PING  # EVENTS still works
docker-compose logs conport --tail=50  # No Redis errors
```

### Phase 3 Testing (Vector DB)
```bash
# After Milvus → Qdrant migration:
curl http://localhost:6333/collections  # Qdrant collections listed
pytest tests/claude-context/ -v  # All vector search tests pass
```

### Integration Testing
```bash
# End-to-end: All services operational
docker-compose ps  # All services "Up" status
docker-compose logs --tail=20  # No connection errors anywhere

# Verify database connections
docker exec dopemux-postgres-age psql -U dopemux -c "SELECT count(*) FROM pg_stat_activity;"
docker exec dopemux-redis-primary redis-cli INFO clients
docker exec qdrant curl http://localhost:6333/health
```

---

## Monitoring After Consolidation

**Metrics to Track**:
```yaml
container_metrics:
  total_containers: 11 (target, down from 19)
  total_memory: Monitor for 2-3GB reduction
  cpu_usage: Should decrease slightly

database_metrics:
  postgres_connections: Monitor active connections
  redis_ops_per_sec: Track for performance regression
  qdrant_search_latency: Compare to Milvus baseline

service_health:
  conport_health: Should remain "healthy"
  serena_health: Should remain "healthy"
  claude_context_health: Watch closely during Milvus migration
```

**Alerts**:
- Alert if any service shows "unhealthy"
- Alert if memory usage increases (regression)
- Alert if database connections fail

---

## Rollback Plans

### Phase 1 Rollback (PostgreSQL)
```bash
# If orphaned postgres was needed (unlikely):
docker volume create dopemux-postgres-data
docker run -d --name dopemux-postgres \
  -e POSTGRES_USER=dopemux \
  -e POSTGRES_PASSWORD=dopemux_dev_password \
  -p 5433:5432 \
  -v dopemux-postgres-data:/var/lib/postgresql/data \
  postgres:16

# Restore from backup
docker exec -i dopemux-postgres psql -U dopemux < ./backups/postgres-orphaned-YYYYMMDD/full_backup.sql
```

### Phase 2 Rollback (Redis)
```bash
# If conport-kg-redis needed:
docker volume create conport-kg-redis-data
docker run -d --name conport-kg-redis \
  -p 6381:6379 \
  -v conport-kg-redis-data:/data \
  redis:7-alpine

# Data already migrated to dopemux-redis-primary, so:
# Export from primary, import to conport-kg-redis if needed
```

### Phase 3 Rollback (Milvus)
```bash
# If Qdrant migration fails:
# Restart Milvus stack
docker-compose -f docker-compose.milvus.yml up -d

# Data preserved in milvus-data volume
# Services automatically reconnect
```

---

## Success Metrics

**Infrastructure**:
- [ ] 11 containers running (down from 19)
- [ ] 2-3GB memory saved
- [ ] Zero port conflicts
- [ ] All databases consolidated

**Services**:
- [ ] ConPort operational on single PostgreSQL
- [ ] All Redis clients connected to consolidated instances
- [ ] All vector searches working via Qdrant
- [ ] Zero connection errors in logs

**Operations**:
- [ ] Simplified docker-compose.yml
- [ ] Faster startup time (fewer containers)
- [ ] Easier debugging (fewer components)
- [ ] Lower infrastructure costs

---

## Risk Assessment

**Risk 1: Data Loss During Migration**
**Probability**: LOW
**Impact**: CRITICAL
**Mitigation**: Backups before each phase, gradual migration, extensive testing

**Risk 2: Service Downtime**
**Probability**: MEDIUM
**Impact**: MEDIUM
**Mitigation**: Phased approach, rollback procedures, health monitoring

**Risk 3: Performance Regression**
**Probability**: LOW
**Impact**: MEDIUM
**Mitigation**: Qdrant performance comparable to Milvus, monitoring in place

---

**Total Effort**: 6-9 days (varies by data migration needs)
**Risk Level**: MEDIUM (phased approach mitigates)
**Impact**: HIGH (reduced complexity, saved resources)
**ROI**: 🔥 Medium-High (operational improvements, cost savings)
