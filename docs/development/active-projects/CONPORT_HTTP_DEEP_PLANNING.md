# ConPort HTTP Wrapper - Deep Planning & Analysis

**Date:** 2025-10-29  
**Task:** Create HTTP API wrapper for ConPort (Day 2 Afternoon)  
**Status:** Planning Phase  

---

## 🎯 OBJECTIVE

Create a lightweight HTTP API layer for ConPort that exposes:
1. Recent decisions logged by users
2. Knowledge graph statistics (nodes, edges, workspaces)

**Why:** Dashboard needs HTTP endpoints to display ConPort data. ConPort currently runs only as MCP server (stdio mode).

---

## 🔍 CURRENT STATE ANALYSIS

### What ConPort Is
ConPort is a **PostgreSQL + Apache AGE knowledge graph** that stores:
- Decisions made during development
- Relationships between code, tasks, files
- Workspace contexts
- Session data

### How ConPort Runs Now
```bash
# MCP Server (stdio mode) - for Claude/Copilot
conport-mcp --workspace_id /Users/hue/code/dopemux-mvp --mode stdio

# Multiple instances running (one per tmux pane)
ps aux | grep conport-mcp
# Shows: Multiple Python processes running conport-mcp in stdio mode
```

### ConPort Directory Structure
```
services/conport/
├── mcp_server.py          # MCP server entry point
├── database/
│   └── postgres_client.py # PostgreSQL + AGE client
├── api/
│   └── auth_routes.py     # Existing API routes (if any)
├── tools/                 # MCP tools
└── venv/                  # Python environment
```

---

## 🏗️ ARCHITECTURE OPTIONS

### Option A: Standalone HTTP Server (RECOMMENDED)
```
┌─────────────────────────────────────────────────────┐
│  ConPort HTTP Server (Port 8005)                    │
│  ├─ FastAPI app                                     │
│  ├─ Direct PostgreSQL/AGE queries                   │
│  └─ Independent of MCP server                       │
└─────────────────────────────────────────────────────┘
         │
         ▼
   PostgreSQL + AGE
   (ConPort database)

Pros:
+ Simple, clean separation
+ No MCP dependency
+ Direct database access (fast)
+ Easy to test and debug

Cons:
- Duplicate database connection
- Need to recreate some query logic
```

### Option B: HTTP Wrapper Around MCP
```
┌─────────────────────────────────────────────────────┐
│  ConPort HTTP Server (Port 8005)                    │
│  ├─ FastAPI app                                     │
│  ├─ Calls MCP server via bridge                     │
│  └─ Translates HTTP → MCP → HTTP                    │
└─────────────────────────────────────────────────────┘
         │
         ▼
   MCP Server (stdio)
         │
         ▼
   PostgreSQL + AGE

Pros:
+ Reuses existing MCP logic
+ Single source of truth

Cons:
- More complex (double hop)
- Slower (extra layer)
- MCP server must be running
```

### Option C: Dual-Mode Server
```
┌─────────────────────────────────────────────────────┐
│  ConPort Unified Server                             │
│  ├─ FastAPI app (HTTP on :8005)                     │
│  ├─ MCP server (stdio)                              │
│  └─ Shared database client                          │
└─────────────────────────────────────────────────────┘
         │
         ▼
   PostgreSQL + AGE

Pros:
+ Single process
+ Shared resources
+ Both interfaces available

Cons:
- Complex startup
- Mixing concerns
- Harder to debug
```

**DECISION: Option A - Standalone HTTP Server**
- Simplest to implement (30 min)
- Independent testing
- Clear separation of concerns
- Can share database connection if needed later

---

## 📊 DATA REQUIREMENTS

### Endpoint 1: GET `/api/adhd/decisions/recent`

**Purpose:** Get recent decisions logged by user

**Query Needed:**
```sql
SELECT 
    id,
    title,
    context,
    type,
    confidence,
    created_at
FROM decisions
ORDER BY created_at DESC
LIMIT ?
```

**Response Format:**
```json
{
  "count": 5,
  "decisions": [
    {
      "id": "uuid",
      "title": "Use FastAPI for HTTP wrapper",
      "context": "Need HTTP API for dashboard",
      "type": "architecture",
      "confidence": 0.9,
      "created_at": "2025-10-29T07:00:00Z"
    }
  ]
}
```

### Endpoint 2: GET `/api/adhd/graph/stats`

**Purpose:** Get knowledge graph statistics

**Queries Needed:**
```sql
-- Count nodes by type
SELECT type, COUNT(*) as count
FROM nodes
GROUP BY type;

-- Count total edges
SELECT COUNT(*) as count FROM edges;

-- Count workspaces
SELECT COUNT(DISTINCT workspace_id) FROM workspaces;
```

**Response Format:**
```json
{
  "nodes": {
    "total": 1250,
    "tasks": 450,
    "decisions": 320,
    "files": 380,
    "concepts": 100
  },
  "edges": 2340,
  "workspaces": 1,
  "last_updated": "2025-10-29T07:00:00Z"
}
```

### Endpoint 3: GET `/health`

**Purpose:** Health check for dashboard monitoring

**Response Format:**
```json
{
  "status": "healthy",
  "service": "conport",
  "database": "connected",
  "latency_ms": 15
}
```

---

## 🛠️ IMPLEMENTATION PLAN

### Step 1: Investigate ConPort Database Setup

**Questions to Answer:**
1. Is PostgreSQL running?
2. What's the database connection string?
3. Does AGE extension exist?
4. Are there existing tables?
5. What's the schema for decisions/nodes/edges?

**Commands:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Find ConPort database config
grep -r "DATABASE_URL\|POSTGRES" services/conport/

# Check existing database client
cat services/conport/database/postgres_client.py
```

### Step 2: Create Minimal HTTP Server

**File:** `services/conport/http_server.py`

```python
#!/usr/bin/env python3
"""
ConPort HTTP API - Dashboard access layer
Standalone FastAPI server for ConPort data access
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import List, Dict, Any
import os

app = FastAPI(
    title="ConPort HTTP API",
    version="1.0.0",
    description="Dashboard access to ConPort knowledge graph"
)

# CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Database client (to be initialized)
db = None

@app.on_event("startup")
async def startup():
    """Initialize database connection"""
    global db
    # TODO: Initialize PostgreSQL client
    pass

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    if db:
        await db.close()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "conport",
        "database": "connected" if db else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/adhd/decisions/recent")
async def get_recent_decisions(limit: int = 10):
    """Get recent decisions"""
    # TODO: Query database
    return {
        "count": 0,
        "decisions": []
    }

@app.get("/api/adhd/graph/stats")
async def get_graph_stats():
    """Get knowledge graph statistics"""
    # TODO: Query database
    return {
        "nodes": {"total": 0},
        "edges": 0,
        "workspaces": 1
    }

if __name__ == "__main__":
    print("🚀 Starting ConPort HTTP API on port 8005...")
    uvicorn.run(app, host="0.0.0.0", port=8005)
```

### Step 3: Add Database Integration

**Options:**
1. Use existing `postgres_client.py` if compatible
2. Use `asyncpg` directly (lightweight)
3. Use `psycopg3` (more features)

**Recommended:** Check existing client first, fall back to asyncpg if needed.

### Step 4: Test & Verify

**Test Plan:**
```bash
# 1. Start server
cd services/conport
python3 http_server.py &

# 2. Test health
curl http://localhost:8005/health | jq '.'

# 3. Test decisions endpoint
curl http://localhost:8005/api/adhd/decisions/recent?limit=5 | jq '.'

# 4. Test graph stats
curl http://localhost:8005/api/adhd/graph/stats | jq '.'
```

---

## 🗺️ DATABASE SCHEMA INVESTIGATION

### Need to Find:
1. **Decisions table structure**
   ```sql
   DESCRIBE decisions;
   -- or
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'decisions';
   ```

2. **Nodes table structure**
   ```sql
   DESCRIBE nodes;
   ```

3. **Edges table structure**
   ```sql
   DESCRIBE edges;
   ```

4. **Sample data**
   ```sql
   SELECT * FROM decisions LIMIT 1;
   SELECT * FROM nodes LIMIT 1;
   SELECT * FROM edges LIMIT 1;
   ```

---

## ⚠️ POTENTIAL ISSUES & SOLUTIONS

### Issue 1: PostgreSQL Not Running
**Symptom:** Can't connect to database  
**Check:** `docker ps | grep postgres`  
**Solution:** Start PostgreSQL container or use existing one

### Issue 2: Database Empty
**Symptom:** No decisions/nodes found  
**Impact:** API returns empty arrays (OK for MVP)  
**Solution:** Return mock data or empty results (dashboard handles gracefully)

### Issue 3: Schema Unknown
**Symptom:** Don't know table structure  
**Solution:** 
- Inspect existing MCP server code
- Check migrations or schema files
- Query information_schema
- Start with mock data, refine later

### Issue 4: AGE Extension Not Loaded
**Symptom:** Can't query graph  
**Solution:** Use regular PostgreSQL tables for now, AGE for graph later

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Investigation (10 min)
- [ ] Check if PostgreSQL is running
- [ ] Find database connection config
- [ ] Review existing postgres_client.py
- [ ] Check for existing schema/migrations
- [ ] Determine if AGE is required for basic queries

### Phase 2: Skeleton Server (10 min)
- [ ] Create http_server.py with FastAPI
- [ ] Add health endpoint
- [ ] Add decisions endpoint (mock)
- [ ] Add graph stats endpoint (mock)
- [ ] Test server starts on port 8005

### Phase 3: Database Integration (15 min)
- [ ] Initialize database client
- [ ] Test connection
- [ ] Query decisions table
- [ ] Query nodes/edges for stats
- [ ] Handle errors gracefully

### Phase 4: Dashboard Integration (10 min)
- [ ] Update dashboard ENDPOINTS config
- [ ] Update get_decisions() method
- [ ] Test dashboard shows real data
- [ ] Verify no errors in fallback

**Total Estimated Time: 45 minutes**

---

## 🎯 SUCCESS CRITERIA

### Must Have:
- [ ] HTTP server running on port 8005
- [ ] /health endpoint responds
- [ ] /api/adhd/decisions/recent returns data (even if empty)
- [ ] /api/adhd/graph/stats returns data (even if zeros)
- [ ] Dashboard connects without errors

### Nice to Have:
- [ ] Real decisions from database
- [ ] Real graph stats
- [ ] Sub-100ms response times
- [ ] Proper error handling

### Can Defer:
- [ ] Authentication
- [ ] Rate limiting
- [ ] Caching
- [ ] Complex graph queries

---

## 🚀 EXECUTION STRATEGY

### Approach: Incremental with Fallbacks

1. **Start with skeleton** - Get HTTP server running first
2. **Add mock endpoints** - Dashboard can connect even if data empty
3. **Investigate database** - While server runs, check DB setup
4. **Add real queries** - Replace mocks once DB understood
5. **Test end-to-end** - Verify dashboard → HTTP → DB flow

**Philosophy:** Ship working (even if empty) fast, then add real data.

---

## 📊 DECISION MATRIX

| Aspect | Option A | Option B | Option C | Chosen |
|--------|----------|----------|----------|--------|
| Complexity | Low | Medium | High | A ✅ |
| Speed | Fast (direct) | Slow (2 hops) | Fast | A ✅ |
| Dependencies | DB only | MCP + DB | Both | A ✅ |
| Testing | Easy | Hard | Medium | A ✅ |
| Maintenance | Low | Medium | High | A ✅ |

**Rationale:** For MVP dashboard, simplest solution wins. Can refactor later if needed.

---

## 🔍 NEXT ACTIONS

1. **Investigate ConPort Database** (5 min)
   - Check PostgreSQL status
   - Find connection config
   - Review existing client code

2. **Create HTTP Server Skeleton** (10 min)
   - Copy template above
   - Test server starts
   - Verify endpoints respond

3. **Add Database Queries** (15 min)
   - Connect to PostgreSQL
   - Query decisions
   - Query graph stats

4. **Integrate with Dashboard** (10 min)
   - Update endpoints config
   - Test end-to-end
   - Verify graceful fallback

**Let's start with investigation!**

---

**Status:** ✅ Planning Complete  
**Confidence:** HIGH  
**Estimated Time:** 45 minutes  
**Risk:** LOW (fallback to mock data if DB issues)  
**Ready to Execute:** YES 🚀
