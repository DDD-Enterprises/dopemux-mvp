---
id: DASHBOARD_QUICKSTART
title: Dashboard_Quickstart
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Quickstart (explanation) for dopemux documentation and developer
  workflows.
---
# Dashboard Implementation Quickstart 🚀

**TL;DR:** Start ADHD Engine, connect dashboard, ship in 3 days.

---

## ⚡ Day 1: ADHD Engine (30 min)

### Start the HTTP Server
```bash
cd services/adhd_engine
source venv/bin/activate  # or create if needed
pip install -r requirements.txt

# Start FastAPI server
python main.py
# ✅ Should see: "Starting on http://0.0.0.0:8095"
```

### Test the APIs
```bash
# Health check
curl http://localhost:8095/health

# Get energy level
curl http://localhost:8095/api/v1/energy-level/default_user

# Get attention state
curl http://localhost:8095/api/v1/attention-state/default_user
```

### Connect Dashboard
```python
# In dopemux_dashboard.py, update:
ENDPOINTS = {
    "adhd_state": "http://localhost:8095/api/v1/state",  # ✅ Real API
    # "tasks": "http://localhost:8001/api/v1/tasks",     # ⏳ TODO
    # "decisions": "http://localhost:8005/api/adhd/decisions/recent",  # ⏳ TODO
}
```

### Run Dashboard
```bash
python dopemux_dashboard.py
# ✅ Should see real ADHD state!
```

---

## ⚡ Day 2: ConPort HTTP Wrapper (2 hrs)

### Create HTTP Server
```bash
cd services/conport
touch http_server.py
```

```python
# http_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="ConPort HTTP API")

@app.get("/api/adhd/decisions/recent")
async def get_recent_decisions(limit: int = 10):
    # TODO: Call MCP tool or query database directly
    return {
        "count": 0,
        "decisions": []
    }

@app.get("/api/adhd/graph/stats")
async def get_graph_stats():
    return {
        "nodes": 0,
        "edges": 0,
        "active_workspaces": 1
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "conport"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
```

### Start Server
```bash
python http_server.py &
# ✅ Running on :8005
```

### Update Dashboard
```python
ENDPOINTS = {
    "adhd_state": "http://localhost:8095/api/v1/state",
    "decisions": "http://localhost:8005/api/adhd/decisions/recent",  # ✅ Now real
}
```

---

## ⚡ Day 3: Serena HTTP Wrapper (2 hrs)

### Same pattern as ConPort
```bash
cd services/serena/v2
touch http_server.py
```

```python
# services/serena/v2/http_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Serena HTTP API")

@app.get("/api/metrics")
async def get_metrics():
    return {
        "detections": 0,
        "patterns": [],
        "confidence": 0.0
    }

@app.get("/api/detections/summary")
async def get_detections_summary():
    return {
        "total": 0,
        "passed": 0,
        "top_patterns": []
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "serena"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

### Start Server
```bash
python http_server.py &
# ✅ Running on :8003
```

---

## 🎯 After 3 Days: You Have

- ✅ ADHD Engine serving real energy/attention data
- ✅ ConPort serving decisions & graph stats
- ✅ Serena serving pattern detections
- ✅ Dashboard displaying all real data
- ✅ All services running in dual-mode (MCP + HTTP)

**Ship it!** 🚀

---

## 🔧 Troubleshooting

### Service won't start
```bash
# Check if port is in use
lsof -i :8095  # ADHD Engine
lsof -i :8005  # ConPort
lsof -i :8003  # Serena

# Kill if needed
kill -9 <PID>
```

### Dashboard shows mock data
```bash
# Check services are running
curl http://localhost:8095/health
curl http://localhost:8005/health
curl http://localhost:8003/health

# Check dashboard config
grep ENDPOINTS dopemux_dashboard.py
```

### Dashboard crashes
```bash
# Check dependencies
pip install textual rich httpx

# Run with debug
python -m pdb dopemux_dashboard.py
```

---

## 📊 Testing Checklist

- [ ] `curl http://localhost:8095/health` returns 200
- [ ] `curl http://localhost:8005/health` returns 200
- [ ] `curl http://localhost:8003/health` returns 200
- [ ] Dashboard starts without errors
- [ ] ADHD panel shows real energy level
- [ ] Productivity panel shows real task count
- [ ] Services panel shows all services healthy
- [ ] CPU usage < 10%
- [ ] No crashes after 10 minutes

---

## 🚀 Next Steps (Week 2)

Once basic dashboard works:

1. **Add Redis caching** (fallback when services down)
2. **Add sparklines** (historical trends)
3. **Add keyboard nav** (1-4 to focus panels)
4. **Optimize performance** (profile & cache)
5. **Write tests** (pytest + integration)
6. **Document** (update README)

---

## 📚 Reference

- **Full Planning:** `docs/implementation-plans/DASHBOARD_DEEP_PLANNING.md`
- **Design Research:** `TMUX_DASHBOARD_DESIGN.md`
- **Metrics Inventory:** `TMUX_METRICS_INVENTORY.md`
- **Sprint Plan:** `docs/implementation-plans/tmux-dashboard-sprint-plan.md`

---

**Time to MVP:** 3 days
**Confidence:** HIGH
**Dependencies:** Python 3.11+, FastAPI, Textual, Rich

**Let's ship! 🎉**
