---
id: CONPORT_IMPLEMENTATION_PATHS
title: Conport_Implementation_Paths
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# ConPort Consolidation: Implementation Plans

**Based on**: CONPORT_DEEP_ANALYSIS.md
**Status**: Three detailed implementation paths
**Confidence**: VERY HIGH (0.89)

---

## Path Selection Matrix

| Path | Time | Risk | Value | Complexity | Recommendation |
|------|------|------|-------|------------|----------------|
| **A: Unified v3** | 4-6 weeks | Medium | Very High | High | ⭐ Best long-term |
| **B: Extend Enhanced** | 2 weeks | Low | High | Low | ⭐ Fastest win |
| **C: MCP + Bridge** | 3 days | Very Low | Medium | Very Low | ⭐ Simplest |

---

## PATH A: Unified ConPort v3 (RECOMMENDED FOR LONG-TERM)

### Vision

One codebase, multiple deployment modes, all features.

```
ConPort v3 Unified
├── Core Engine (unified)
│   ├── Storage: PostgreSQL AGE
│   ├── Cache: SQLite (optional)
│   ├── Auth: JWT (optional)
│   ├── Queries: 3-tier + graph
│   └── Events: Redis Streams
├── Deployment Modes
│   ├── STDIO (for MCP clients)
│   ├── HTTP/SSE (for web)
│   ├── REST API (for dashboard)
│   └── EventBus (for agents)
└── Configuration
    ├── Minimal (STDIO-only, like current MCP)
    ├── Standard (HTTP + EventBus)
    └── Full (all features, multi-tenant)
```

### Week-by-Week Plan

**Week 1: Core Architecture**
```
Day 1: Project setup
  - Create services/conport_v3/
  - Copy best code from all three systems
  - Define unified data model
  - Output: 500 lines, project skeleton

Day 2: Storage layer
  - PostgreSQL AGE client (from KG)
  - SQLite cache layer (from MCP)
  - Abstract storage interface
  - Output: 800 lines, dual storage working

Day 3: Query layer
  - 3-tier queries (from KG)
  - Graph queries (from Enhanced)
  - FTS search (from MCP)
  - Output: 1,200 lines, all query types

Day 4: Auth layer (optional)
  - JWT utils (from KG)
  - RBAC middleware (from KG)
  - Auth can be disabled for STDIO
  - Output: 600 lines, optional auth

Day 5: Event system
  - Redis Streams client
  - Event schemas
  - Pub/sub infrastructure
  - Output: 400 lines, EventBus ready

Deliverable: Core engine complete (~3,500 lines)
```

**Week 2: Deployment Modes**
```
Day 6: STDIO mode
  - MCP protocol handler (from MCP)
  - JSON-RPC over stdin/stdout
  - Works with Claude Code
  - Output: 300 lines, STDIO working

Day 7: HTTP mode
  - FastAPI server (from Enhanced)
  - SSE streaming (from Enhanced)
  - HTTP/SSE endpoints
  - Output: 400 lines, HTTP working

Day 8: REST API
  - Auth routes (from KG)
  - Query routes (from KG)
  - OpenAPI docs
  - Output: 600 lines, REST API complete

Day 9: EventBus API
  - Event publishers
  - Event consumers
  - Schema validation
  - Output: 300 lines, Events working

Day 10: Configuration system
  - Deployment profiles (minimal/standard/full)
  - Feature flags
  - Environment detection
  - Output: 200 lines, config complete

Deliverable: All deployment modes working (~1,800 lines)
Total: ~5,300 lines
```

**Week 3: Migration & Testing**
```
Day 11: Data migration
  - Export from MCP (SQLite → JSON)
  - Export from Enhanced (PostgreSQL → JSON)
  - Export from KG (PostgreSQL → JSON)
  - Output: 400 lines, migration scripts

Day 12: Import to v3
  - Import JSON → unified schema
  - Handle duplicates
  - Preserve relationships
  - Output: 300 lines, import complete

Day 13: Testing infrastructure
  - Unit tests (copy from KG)
  - Integration tests
  - Deployment mode tests
  - Output: 1,000 lines tests

Day 14: Performance testing
  - Benchmark all deployment modes
  - Validate latency targets
  - Stress test EventBus
  - Output: Test results, tuning

Day 15: Documentation
  - API documentation
  - Deployment guide
  - Migration guide
  - Output: Comprehensive docs

Deliverable: Migration complete, tested, documented
```

**Week 4: Agent Integration**
```
Day 16-17: Serena integration
  - EventBus subscription
  - Decision context in hovers
  - Testing and validation
  - Output: 300 lines, proof of concept

Day 18-19: Task-Orchestrator integration
  - Event-based task creation
  - Decision-task linking
  - Output: 200 lines

Day 20: Validation and polish
  - Test all integrations
  - Bug fixes
  - Performance tuning
  - Output: Production-ready system

Deliverable: 2 agents integrated, pattern proven
```

**Weeks 5-6: Scale & Dashboard**
```
Week 5: Remaining agents (Zen, Dope-Context, ADHD, Desktop)
  - 4 more integrations (50 lines each)
  - Total: 200 lines
  - Deliverable: 6/6 agents integrated

Week 6: ADHD Dashboard
  - React + TypeScript
  - Decision timeline
  - Top-3 pattern
  - Output: 2,000 lines
  - Deliverable: Dashboard live
```

### Total Effort

**Code**: ~7,500 lines (unified codebase)
**Tests**: ~1,500 lines
**Docs**: ~1,000 lines
**Time**: 6 weeks
**Risk**: Medium
**Value**: Very High

### Success Metrics

- ✅ One codebase (vs 3)
- ✅ All features preserved
- ✅ 6 agents integrated
- ✅ Dashboard live
- ✅ <100ms latency (all modes)
- ✅ 90%+ test coverage

---

## PATH B: Extend Enhanced Server (RECOMMENDED FOR SPEED)

### Vision

Enhanced Server becomes the primary system, absorbing features from MCP and KG.

```
Enhanced Server v2
├── Add from KG:
│   ├── JWT authentication
│   ├── RBAC middleware
│   ├── 3-tier ADHD queries
│   └── Audit logging
├── Add from MCP:
│   ├── STDIO mode (optional)
│   ├── Better docs
│   └── Semantic search
├── Keep existing:
│   ├── PostgreSQL AGE
│   ├── EventBus integration
│   ├── Multi-workspace
│   └── Graph queries
└── Deprecate:
    ├── ConPort MCP (migrate users)
    └── ConPort-KG (merge code)
```

### Week-by-Week Plan

**Week 1: Add Auth & ADHD**
```
Day 1: Copy JWT auth from KG
  - auth/jwt_utils.py → enhanced_server/auth/
  - auth/password_utils.py → enhanced_server/auth/
  - Output: 700 lines, auth working

Day 2: Copy RBAC from KG
  - middleware/rbac_middleware.py
  - auth/permissions.py
  - Output: 300 lines, RBAC working

Day 3: Add 3-tier queries from KG
  - queries/overview.py
  - queries/exploration.py
  - queries/deep_context.py
  - Output: 1,500 lines, ADHD queries working

Day 4: Add REST API
  - FastAPI endpoints
  - Auth routes
  - Query routes
  - Output: 800 lines, REST API complete

Day 5: Testing & docs
  - Test auth flow
  - Test queries
  - Update documentation
  - Output: Tested, documented

Deliverable: Enhanced Server v2 with auth + ADHD
Total added: ~3,300 lines
```

**Week 2: Agent Integration & Migration**
```
Day 6-7: Serena integration
  - EventBus subscription
  - Decision hovers
  - Output: 300 lines

Day 8: Data migration
  - MCP → Enhanced (export/import)
  - KG → Enhanced (merge data)
  - Output: Migration scripts

Day 9: Deprecation notices
  - Add warnings to MCP
  - Document migration path
  - Output: Migration guide

Day 10: Dashboard MVP
  - Simple React app
  - Top-3 decisions
  - Timeline view
  - Output: 1,000 lines, basic dashboard

Deliverable: Enhanced Server v2 production-ready
```

### Total Effort

**Code**: ~4,600 lines added to Enhanced
**Time**: 2 weeks
**Risk**: Low (incremental)
**Value**: High

### Success Metrics

- ✅ Auth working (JWT + RBAC)
- ✅ ADHD queries integrated
- ✅ 1 agent integrated
- ✅ Data migrated
- ✅ Dashboard live (basic)

---

## PATH C: MCP + Event Bridge (RECOMMENDED FOR SIMPLICITY)

### Vision

Keep MCP exactly as-is, add tiny event bridge to enable agent integration.

```
ConPort MCP (unchanged)
     ↓
Event Bridge (new, 200 lines)
  - Watches SQLite file (inotify)
  - Publishes to Redis Streams
  - Event types: decision.*, progress.*
     ↓
Redis Streams (EventBus)
     ↓
Agents subscribe
  - Serena
  - Task-Orchestrator
  - Others
```

### 3-Day Plan

**Day 1: Event Bridge Core**
```
Hour 1-2: Project setup
  - Create docker/mcp-servers/conport-bridge/
  - Python + inotify + Redis dependencies
  - Output: Dockerfile, requirements.txt

Hour 3-4: SQLite watcher
  - Watch context_portal/context.db
  - Detect INSERT/UPDATE/DELETE
  - Parse SQLite journal
  - Output: 100 lines, file watching working

Hour 5-6: Event publisher
  - Redis Streams client
  - Event schemas (decision.logged, etc)
  - Publish on DB change
  - Output: 100 lines, events publishing

Hour 7-8: Testing
  - Create decision in MCP
  - Verify event published
  - Output: Working prototype

Deliverable: Event Bridge working (200 lines)
```

**Day 2: Serena Integration**
```
Hour 1-3: EventBus consumer in Serena
  - Subscribe to decision.* events
  - Cache decisions in memory
  - Output: 150 lines

Hour 4-6: LSP hover enhancement
  - Query local cache (from events)
  - Show decisions in hover
  - Output: 150 lines

Hour 7-8: Testing
  - Create decision
  - Hover in IDE
  - See decision context
  - Output: Working integration

Deliverable: Serena integrated (300 lines total)
```

**Day 3: Polish & Deploy**
```
Hour 1-2: Docker Compose
  - Add conport-bridge service
  - Wire to MCP + Redis
  - Output: docker-compose.yml

Hour 3-4: Error handling
  - Graceful degradation
  - Retry logic
  - Logging
  - Output: Production-ready

Hour 5-6: Documentation
  - How it works
  - How to add more agents
  - Troubleshooting
  - Output: Complete docs

Hour 7-8: Deployment & validation
  - Deploy to Docker
  - Test end-to-end
  - Monitor for issues
  - Output: Live in production

Deliverable: Complete system deployed
```

### Total Effort

**Code**: ~500 lines total
**Time**: 3 days
**Risk**: Very Low
**Value**: Medium (proves concept)

### Success Metrics

- ✅ MCP unchanged (no risk)
- ✅ Events publishing (<100ms latency)
- ✅ Serena showing decisions
- ✅ No new API to maintain
- ✅ Easy to extend (add more agents)

---

## Recommendation: Choose Your Adventure

### Choose Path A if:
- ✅ You want the best long-term architecture
- ✅ You're willing to invest 4-6 weeks
- ✅ You value unified codebase
- ✅ You plan to support teams eventually

### Choose Path B if:
- ✅ You want results in 2 weeks
- ✅ Enhanced Server already works for you
- ✅ You want low risk
- ✅ You don't mind some technical debt

### Choose Path C if:
- ✅ You want agent integration THIS WEEK
- ✅ You love MCP as-is
- ✅ You want zero risk
- ✅ You're validating if agents even need decisions

---

## My Recommendation

**Start with Path C** (3 days):
1. Proves agent integration works
2. Zero risk to existing systems
3. Cheap to build
4. If it works, great!
5. If it doesn't, you learned with minimal investment

**Then decide**:
- If agent integration is valuable → Path B (extend Enhanced)
- If you want best architecture → Path A (unified v3)
- If agents don't need it → Keep MCP, skip the rest

---

**Analysis Complete**: 2025-10-28
**Implementation Plans**: 3 paths (A, B, C)
**Recommended Start**: Path C (3 days, prove value)
**Recommended Long-term**: Path A or B (depends on timeline)

**Next Step**: Pick a path and I'll create detailed implementation plan!
