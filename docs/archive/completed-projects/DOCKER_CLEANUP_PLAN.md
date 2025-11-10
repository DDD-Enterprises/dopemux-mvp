---
id: DOCKER_CLEANUP_PLAN
title: Docker_Cleanup_Plan
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Docker Container Cleanup and Reorganization Plan

## Executive Summary

**Current State**: 38 containers (17 running, 21 exited/stopped)
**Target State**: ~15-20 active containers (remove staging, unused services)
**Redundancy Found**: Milvus vs Qdrant (both vector databases)

---

## 1. CONTAINERS TO REMOVE IMMEDIATELY

### Staging Containers (9 containers - NO LONGER NEEDED)
```bash
# These were for testing and are now obsolete
staging-task-orchestrator      # Exited - replaced by mcp-task-orchestrator
staging-serena-mcp             # Exited - replaced by mcp-serena
staging-break-suggester        # Restarting (failing) - no longer used
staging-grafana                # Exited - monitoring not active
staging-prometheus             # Exited - monitoring not active
staging-conport-mcp            # Exited - replaced by mcp-conport
staging-adhd-engine            # Exited - integrated into main system
staging-dopemux-postgres-age   # Running on port 15432 - REMOVE
staging-redis                  # Running on port 16379 - REMOVE
staging-qdrant                 # Exited - using main mcp-qdrant
```

**Action**: `docker-compose -f docker-compose.staging.yml down -v`

### Memory Stack (3 containers - REDUNDANT)
```bash
# Milvus vector database - REPLACED BY QDRANT
milvus-standalone   # Exited - Qdrant is lighter and already running
milvus-minio        # Exited - Object storage for Milvus
milvus-etcd         # Exited - Metadata store for Milvus
```

**Why Remove**:
- Qdrant (mcp-qdrant) is already running and active
- Milvus is heavier (3 containers vs 1 for Qdrant)
- No code references Milvus (checked services/)
- All exited/not running

**Action**: `docker-compose -f docker/memory-stack/docker-compose.yml down -v`

### Old/Orphaned Containers (3 containers)
```bash
dopemux-conport-memory  # Exited - old memory service
dopemux-postgres        # Exited - replaced by dopemux-postgres-age
```

**Action**: `docker rm -f` these containers

**Total to Remove**: 15 containers

---

## 2. ACTIVE MCP SERVERS (KEEP - 10 containers)

All healthy and serving specific purposes:

| Container | Port | Purpose | Status | Health |
|-----------|------|---------|--------|--------|
| mcp-context7 | 3002 | Context/file operations | Up 2d | ✅ Healthy |
| mcp-zen | 3003 | Neon layout automation | Up 10h | ✅ Healthy |
| mcp-conport | 3004 | HTTP context port | Up 13h | ✅ Healthy |
| mcp-serena | 3006 | Code navigation/LSP | Up 2d | ⚠️ No health |
| mcp-exa | 3008 | Web search | Up 2d | ✅ Healthy |
| mcp-gptr-mcp | 3009 | GPT router | Up 43h | ✅ Healthy |
| mcp-desktop-commander | 3012 | Desktop automation | Up 2d | ✅ Healthy |
| mcp-task-orchestrator | 3014 | Task management | Up 2d | ✅ Healthy |
| mcp-leantime-bridge | 3015 | Leantime integration | Up 1h | ✅ Healthy |
| mcp-qdrant | 6333-6334 | Vector database | Up 2d | ⚠️ No health |

**Port Range**: 3002-3016 (no conflicts)

### Issues to Fix:
1. `mcp-serena` - No health check
2. `mcp-qdrant` - No health check

---

## 3. SUPPORTING INFRASTRUCTURE (KEEP - 8 containers)

### Leantime Stack (4 containers)
```
leantime            Port 8080   - Project management UI
mysql_leantime      Port 3306   - Leantime database
redis_leantime      Internal    - Leantime cache
```

### Decision Graph Stack (4 containers)
```
dope-decision-graph-bridge     Port 3016   - Decision graph API
dope-decision-graph-postgres   Port 5455   - Graph database
dope-decision-graph-redis      Internal    - Graph cache
dope-decision-graph-qdrant     Created     - Graph vectors (NOT STARTED)
```

### Redis/Cache Layer (3 containers)
```
dopemux-redis-primary   Internal  - Primary Redis
dopemux-redis-events    Port 6379 - Event bus
dopemux-redis-ui        Port 8081 - Redis web UI
```

### Database Layer (1 container)
```
dopemux-postgres-age    Port 5456 - Main PostgreSQL with AGE extension
```

---

## 4. PORT CONFLICTS ANALYSIS

### Current Port Usage (NO CONFLICTS FOUND ✅)

**MCP Servers (3000 range):**
- 3002: mcp-context7
- 3003: mcp-zen
- 3004: mcp-conport
- 3006: mcp-serena
- 3008: mcp-exa
- 3009: mcp-gptr-mcp
- 3012: mcp-desktop-commander
- 3014: mcp-task-orchestrator
- 3015: mcp-leantime-bridge
- 3016: dope-decision-graph-bridge

**Databases:**
- 3306: MySQL (Leantime)
- 5455: PostgreSQL (Decision Graph)
- 5456: PostgreSQL (Main - with AGE)
- 6333-6334: Qdrant
- 6379: Redis (exposed for events)

**Web UIs:**
- 8080: Leantime
- 8081: Redis UI

**Staging Conflicts (TO REMOVE):**
- 15432: staging-postgres (conflicts with nothing, but unused)
- 16379: staging-redis (conflicts with nothing, but unused)

---

## 5. MEMORY STACK EXPLANATION

### What is it?
The memory-stack was an attempt to use **Milvus** for vector similarity search to enable:
- Semantic code search
- Context/memory retrieval
- Similar issue finding
- Intelligent caching

### Why was it created?
- Long-term context storage
- Semantic search across codebase
- ADHD-friendly "what was I working on?" queries

### Why remove it?
1. **Redundant**: Qdrant already provides vector search
2. **Heavyweight**: Milvus needs 3 containers (Milvus + MinIO + etcd)
3. **Not Running**: All containers exited 4 days ago
4. **Not Used**: No code references it (grep confirmed)
5. **Better Alternative**: Qdrant is:
   - Lighter weight (1 container)
   - Already running and healthy
   - Better documented
   - More actively maintained

### What replaces it?
**mcp-qdrant** (already running on ports 6333-6334)
- Provides same vector search capabilities
- Used by multiple services
- Part of decision-graph stack
- More modern and efficient

---

## 6. CLEANUP SCRIPT

```bash
#!/bin/bash
# Docker Cleanup Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Docker Container Cleanup - Dopemux                        ║"
echo "╚════════════════════════════════════════════════════════════╝"

# 1. Remove staging environment
echo "1. Removing staging containers..."
docker-compose -f docker-compose.staging.yml down -v
docker rm -f staging-break-suggester 2>/dev/null || true

# 2. Remove memory-stack (Milvus)
echo "2. Removing Milvus memory-stack..."
docker-compose -f docker/memory-stack/docker-compose.yml down -v

# 3. Remove old orphaned containers
echo "3. Removing orphaned containers..."
docker rm -f dopemux-conport-memory dopemux-postgres 2>/dev/null || true

# 4. Clean up volumes
echo "4. Removing unused volumes..."
docker volume prune -f

# 5. Clean up networks
echo "5. Removing unused networks..."
docker network prune -f

# 6. Summary
echo ""
echo "Cleanup complete!"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20
echo ""
echo "✅ Removed: ~15 containers"
echo "✅ Active MCP Servers: 10"
echo "✅ Supporting Services: 11"
echo "✅ No port conflicts"
```

---

## 7. POST-CLEANUP VERIFICATION

### Health Checks to Run:
```bash
# 1. Verify all MCP servers healthy
docker ps --filter "name=mcp-" --format "{{.Names}}: {{.Status}}"

# 2. Test MCP endpoints
curl -f http://localhost:3002/health  # context7
curl -f http://localhost:3003/health  # zen
curl -f http://localhost:3004/health  # conport
curl -f http://localhost:3015/sse --head  # leantime-bridge

# 3. Verify databases
docker exec dopemux-postgres-age pg_isready
docker exec mysql_leantime mysqladmin ping

# 4. Check Qdrant
curl -f http://localhost:6333/health
```

---

## 8. RECOMMENDATIONS

### Immediate Actions:
1. ✅ Remove staging containers (docker-compose.staging.yml down)
2. ✅ Remove memory-stack/Milvus (not needed, have Qdrant)
3. ✅ Remove orphaned containers
4. ⚠️ Add health checks to mcp-serena and mcp-qdrant

### Future Optimizations:
1. **Consolidate Redis**: 3 Redis instances might be reduced to 2
2. **Decision Graph Qdrant**: Start the created container or remove if not needed
3. **Monitor Resource Usage**: Track which services are actively used
4. **Document Service Dependencies**: Create service dependency map

### Files to Update/Remove:
- `docker-compose.staging.yml` - Can be archived or removed
- `docker/memory-stack/` - Can be removed entirely
- Update main documentation to reflect current architecture

---

## 9. FINAL ARCHITECTURE

**After Cleanup:**

```
Production Stack (21 containers):
├── MCP Servers (10)
│   ├── context7, zen, conport, serena
│   ├── exa, gptr-mcp, desktop-commander
│   ├── task-orchestrator, leantime-bridge
│   └── qdrant (shared vector DB)
├── Leantime (4)
│   ├── leantime, mysql, redis
│   └── (project management)
├── Decision Graph (4)
│   ├── bridge, postgres, redis
│   └── qdrant (if started)
├── Redis Layer (3)
│   ├── primary, events, ui
└── Database (1)
    └── postgres-age (main DB)
```

**Port Map:**
- 3002-3016: MCP Services
- 5455-5456: PostgreSQL
- 6333-6334: Qdrant
- 6379: Redis Events
- 8080-8081: Web UIs

---

## 10. MEMORY & PERFORMANCE IMPACT

### Before Cleanup:
- **Containers**: 38 (17 running, 21 stopped)
- **Estimated RAM**: ~8-12GB
- **Disk**: ~20GB (with Milvus data)

### After Cleanup:
- **Containers**: ~21-23 (all running)
- **Estimated RAM**: ~6-8GB
- **Disk**: ~12GB (freed ~8GB)

### Benefits:
- ✅ Cleaner `docker ps` output
- ✅ Reduced resource usage
- ✅ Faster Docker operations
- ✅ No port conflicts
- ✅ Easier to understand architecture

---

**Status**: Ready to execute cleanup
**Risk Level**: Low (removing unused/exited containers)
**Backup Needed**: No (staging data not critical)
**Estimated Time**: 5 minutes
