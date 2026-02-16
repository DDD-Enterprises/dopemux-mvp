---
id: DASHBOARD_DEEP_PLANNING
title: Dashboard_Deep_Planning
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Deep_Planning (explanation) for dopemux documentation and developer
  workflows.
---
# Dashboard Deep Architecture Planning 🧠

**Date:** 2025-10-28
**Status:** Pre-Implementation Planning Complete
**Next:** Review & Approve Architecture

---

## 🎯 EXECUTIVE SUMMARY

We have a **dashboard prototype with mock data** and **services that already support HTTP APIs** (ADHD Engine). The path forward is clear:

1. **Start ADHD Engine's FastAPI server** (already exists!)
1. **Add lightweight HTTP endpoints to ConPort & Serena** (minimal code)
1. **Wire up dashboard to real APIs** (replace mock data)
1. **Optimize with caching & WebSockets** (Phase 2)

**Key Insight:** We're 70% there. The hard work (research, design, API structure) is done. Now we just connect the dots.

---

## ✅ WHAT WE HAVE (Current State)

### 1. Dashboard Prototype (`dopemux_dashboard.py`)
- **Framework:** Textual (TUI) + Rich (rendering)
- **Panels:** ADHD State, Productivity, Services, Trends
- **Data:** Currently using mock placeholders
- **Status:** ✅ Working, ready for real data

### 2. ADHD Engine Service
- **Has:** Complete FastAPI server with `/api/v1/` endpoints
- **Port:** 8095 (configurable)
- **APIs:**
- `/api/v1/assess-task`
- `/api/v1/energy-level/{user_id}`
- `/api/v1/attention-state/{user_id}`
- `/api/v1/recommend-break`
- `/health` ✅
- **Status:** ✅ Ready to use, just needs to be started as HTTP server

### 3. ConPort & Serena Services
- **Current:** Running as MCP servers (stdio mode)
- **Need:** Add HTTP API wrapper (FastAPI)
- **Effort:** ~100 lines of code per service
- **Status:** ⏳ Need to implement

### 4. Documentation
- ✅ Design research (TMUX_DASHBOARD_DESIGN.md)
- ✅ Metrics inventory (TMUX_METRICS_INVENTORY.md)
- ✅ Enhancement roadmap (DASHBOARD_ENHANCEMENTS.md)
- ✅ Sprint plan (tmux-dashboard-sprint-plan.md)

---

## 🚧 THE GAP (What's Missing)

### Problem: Dashboard expects HTTP, services run MCP

```
Dashboard Code (Current):
  async with httpx.AsyncClient() as client:
      resp = await client.get("http://localhost:8001/api/v1/state")

Reality:
  Services run as: conport-mcp --mode stdio
  (No HTTP server listening!)
```

### Solution: Dual-Mode Services

```python
# Services run BOTH MCP and HTTP simultaneously

# MCP mode (for Claude/Copilot)
mcp_server.run(stdio=True)

# HTTP mode (for dashboard)
uvicorn.run(fastapi_app, port=8005)
```

**This is the architecture we'll implement.**

---

## 🎨 RECOMMENDED ARCHITECTURE

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                 Tmux Dashboard (Textual)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  ADHD    │ │  Tasks   │ │ Services │ │  Trends  │       │
│  │  Panel   │ │  Panel   │ │  Panel   │ │  Panel   │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
└───────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   MetricsFetcher       │
        │  - HTTP Client         │
        │  - Redis Cache         │
        │  - Error Handling      │
        └────────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐       ┌──────────────────┐
│  HTTP APIs    │       │   Redis Cache    │
│  (Port 800x)  │       │   (Fallback)     │
└───────┬───────┘       └──────────────────┘
        │
        ├─── ADHD Engine:8095 (FastAPI ✅)
        ├─── ConPort:8005 (Add FastAPI)
        └─── Serena:8003 (Add FastAPI)
```

### Data Flow

1. **Dashboard Widget** needs data (e.g., energy level)
1. **MetricsFetcher** tries HTTP API first
1. If HTTP fails, tries **Redis cache**
1. If cache fails, returns **mock data** (graceful degradation)
1. Widget renders with whatever data is available

**Result:** Dashboard always shows *something*, never crashes.

---

## 🔧 IMPLEMENTATION PLAN

### Phase 1: Get It Working (Days 1-3)

**Goal:** Dashboard showing real data from at least ADHD Engine

#### Day 1: ADHD Engine HTTP Server
- [x] ADHD Engine already has FastAPI
- [ ] Start it as HTTP server (port 8095)
- [ ] Test endpoints with curl
- [ ] Update dashboard to point to :8095

**Commands:**
```bash
cd services/adhd_engine
source venv/bin/activate
python main.py  # Starts on port 8095

# Test
curl http://localhost:8095/health
curl http://localhost:8095/api/v1/energy-level/default_user
```

#### Day 2: ConPort HTTP Wrapper
- [ ] Create `services/conport/http_server.py`
- [ ] Add FastAPI wrapper around MCP tools
- [ ] Expose `/api/adhd/decisions/recent`
- [ ] Expose `/api/adhd/graph/stats`
- [ ] Start on port 8005

**Code Template:**
```python
# services/conport/http_server.py
from fastapi import FastAPI
from mcp_server import ConPortMCP

app = FastAPI(title="ConPort HTTP API")
mcp = ConPortMCP()

@app.get("/api/adhd/decisions/recent")
async def get_recent_decisions():
    return await mcp.get_decisions(limit=10)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "conport"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
```

#### Day 3: Serena HTTP Wrapper
- [ ] Create `services/serena/v2/http_server.py`
- [ ] Expose `/api/metrics`
- [ ] Expose `/api/detections/summary`
- [ ] Start on port 8003

**Same pattern as ConPort wrapper**

---

### Phase 2: Polish & Optimize (Days 4-7)

#### Day 4: Error Handling & Caching
- [ ] Add Redis fallback to MetricsFetcher
- [ ] Implement graceful degradation
- [ ] Add service health checks
- [ ] Test with services up/down

#### Day 5: Sparklines with Real Data
- [ ] Query Prometheus for historical metrics
- [ ] Generate sparklines from time-series
- [ ] Cache sparkline renders (60s TTL)
- [ ] Test with cognitive load, velocity, switches

#### Day 6: Keyboard Navigation
- [ ] Panel focusing (1-4 keys)
- [ ] Tab cycling
- [ ] Arrow key scrolling
- [ ] Visual focus indicator

#### Day 7: Testing & Documentation
- [ ] Run stress test (1 hour uptime)
- [ ] Verify CPU < 5%, Memory < 100MB
- [ ] Update README with startup instructions
- [ ] Record demo video

---

## 🎯 SUCCESS CRITERIA

### Must Have (Phase 1)
- [ ] Dashboard shows real ADHD state from Engine
- [ ] Dashboard shows real decisions from ConPort
- [ ] Dashboard shows real patterns from Serena
- [ ] Services can run in dual-mode (MCP + HTTP)
- [ ] Graceful degradation when services offline

### Should Have (Phase 2)
- [ ] Sparklines with historical data
- [ ] Full keyboard navigation
- [ ] < 100ms update latency
- [ ] Redis caching working

### Nice to Have (Future)
- [ ] WebSocket streaming for real-time updates
- [ ] Mobile-friendly web dashboard
- [ ] Desktop notifications (macOS)
- [ ] Prometheus metrics exporter

---

## ⚡ PERFORMANCE TARGETS

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Startup time | < 2s | < 5s |
| Update latency | < 100ms | < 500ms |
| CPU usage | < 3% | < 10% |
| Memory | < 50MB | < 150MB |
| Render FPS | 30fps | 15fps |

### Optimization Strategies
- **Async everywhere:** No blocking I/O
- **Batch API calls:** Fetch all metrics in parallel
- **Cache aggressively:** Redis + in-memory (60s TTL)
- **Debounce renders:** Max 30fps even if data updates faster
- **Profile hotspots:** Use cProfile to find slow code

---

## 🛡️ ERROR HANDLING STRATEGY

### Graceful Degradation

```python
async def get_adhd_state(self) -> Dict:
    """Fetch ADHD state with fallbacks."""
    try:
        # Try HTTP API first (fastest, most accurate)
        return await http_client.get("http://localhost:8095/api/v1/state")
    except httpx.HTTPError:
        try:
            # Fall back to Redis cache (stale but better than nothing)
            cached = await redis.get("adhd:state:cache")
            if cached:
                return json.loads(cached)
        except redis.RedisError:
            pass

        # Last resort: return mock data
        logger.warning("All data sources failed, using mock data")
        return {
            "energy_level": "unknown",
            "attention_state": "unknown",
            "cognitive_load": 0.0,
            "message": "Service unavailable"
        }
```

### Service Health Indicator

```
Footer: ConPort ✓  ADHD ✓  Serena ⚠  Redis ✗
```

- **✓ Green:** Healthy (< 200ms response)
- **⚠ Yellow:** Degraded (> 200ms or using cache)
- **✗ Red:** Offline (using mock data)

---

## 🚨 RISKS & MITIGATIONS

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Services don't have HTTP | **HIGH** | LOW (ADHD Engine has it!) | Add FastAPI wrapper (~100 LOC) |
| Performance too slow | MEDIUM | MEDIUM | Profile, cache, optimize |
| Textual rendering bugs | MEDIUM | LOW | Fallback to Rich console |
| Redis unavailable | LOW | LOW | In-memory cache fallback |
| User overwhelmed by data | MEDIUM | MEDIUM | Start with compact layout |

---

## 📊 METRICS TO TRACK

### P1: Real-Time (Update every 1s)
- Energy level
- Attention state
- Cognitive load
- Flow state active

### P2: Fast (Update every 5s)
- Break timer countdown
- Session duration
- Token usage (Claude API)

### P3: Medium (Update every 30s)
- Task completion (count/%)
- Decision logging (count)
- Context switches (count)

### P4: Slow (Update every 60s)
- Pattern detections (top 5)
- Service health (all services)
- Sparkline trends (cognitive load, velocity, switches)

---

## 🧪 TESTING CHECKLIST

### Unit Tests
- [ ] MetricsFetcher with mocked HTTP
- [ ] Sparkline generation
- [ ] Error handling (all fallback paths)

### Integration Tests
- [ ] Dashboard with real services
- [ ] Dashboard with services offline
- [ ] Dashboard with mixed (some up, some down)

### Stress Tests
- [ ] Run for 1 hour continuously
- [ ] Monitor CPU/memory every 60s
- [ ] Verify no memory leaks
- [ ] Check render performance doesn't degrade

---

## 🎓 LESSONS FROM RESEARCH

### From btop (System Monitor)
- **High information density** works if organized clearly
- **Color coding** is critical for quick pattern recognition
- **Sparklines** communicate trends better than numbers

### From k9s (Kubernetes TUI)
- **Keyboard-first navigation** is essential
- **Contextual help** (press '?' for shortcuts)
- **Progressive disclosure** (summary → detail on demand)

### From ADHD Design Research
- **No blinking/flashing** (triggers distraction)
- **Color meaning must be consistent** (red always = urgent)
- **Reduce cognitive load** (max 7±2 items per section)
- **Make it actionable** (show next step, not just status)

---

## 🔍 ARCHITECTURAL DECISIONS

### ✅ Decision 1: Data Access
**Chosen:** Dual-mode services (MCP + HTTP)

**Why:**
- Dashboard needs HTTP (simple, fast, standard)
- MCP tools still work for Claude/Copilot
- Clean separation of concerns
- ADHD Engine already proves this works

### ✅ Decision 2: Update Strategy
**Chosen:** Polling (Phase 1), WebSocket (Phase 2)

**Why:**
- Polling is simple and works with any backend
- Ship working dashboard faster
- Optimize with WebSocket later (real-time P1 metrics)

### ✅ Decision 3: Caching
**Chosen:** Multi-layer (in-memory → Redis → HTTP)

**Why:**
- In-memory is instant (no network)
- Redis survives dashboard restart
- HTTP is source of truth
- Graceful degradation when services down

---

## 🚀 NEXT STEPS

### Immediate (Today)
1. **Review this plan** - Does the architecture make sense?
1. **Test ADHD Engine HTTP** - Start it, curl the endpoints
1. **Confirm service ports** - 8095 (ADHD), 8005 (ConPort), 8003 (Serena)

### Day 1 (Tomorrow)
1. **Start ADHD Engine HTTP server**
1. **Update dashboard to use real API**
1. **Test with real energy/attention data**

### Week 1
- Wire up all services (HTTP wrappers for ConPort/Serena)
- Connect dashboard to real APIs
- Add error handling & Redis cache
- Ship working dashboard! 🎉

---

## 📦 DELIVERABLES

### Week 1
- ✅ Working dashboard with real data
- ✅ All services expose HTTP APIs
- ✅ Error handling & graceful degradation
- ✅ Performance < 5% CPU, < 100MB RAM

### Week 2
- ✅ Sparklines with historical data
- ✅ Full keyboard navigation
- ✅ Layout presets (compact/standard/detailed)
- ✅ Documentation & demo video

---

## 💡 KEY INSIGHTS

1. **We're closer than we thought:** ADHD Engine already has HTTP!
1. **Dual-mode is the answer:** Services can do both MCP + HTTP
1. **Start simple, optimize later:** Polling → WebSocket progression
1. **Graceful degradation:** Dashboard should never crash
1. **The research was worth it:** We know exactly what to build

---

## 🎯 FINAL RECOMMENDATION

**Start with Day 1 immediately:**
1. Launch ADHD Engine HTTP server (it already exists!)
1. Point dashboard at `http://localhost:8095`
1. See real energy/attention data flowing
1. Build momentum from early win

**Then iterate:**
- Day 2: ConPort HTTP wrapper
- Day 3: Serena HTTP wrapper
- Days 4-7: Polish, optimize, ship

**We can have a working dashboard by end of Week 1.** 🚀

---

**Status:** ✅ Planning Complete
**Confidence:** HIGH (architecture proven, APIs exist, clear path)
**Estimated Time:** 1-2 weeks to production-ready
**Risk Level:** LOW (worst case: graceful degradation to mock data)

**Ready to proceed?** 🎉
