---
id: DOPECONBRIDGE_QUICK_REFERENCE_CARD
title: Dopeconbridge_Quick_Reference_Card
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopeconbridge_Quick_Reference_Card (explanation) for dopemux documentation
  and developer workflows.
---
# DopeconBridge Quick Reference Card

**Version:** 2.0 | **Status:** ✅ Production Ready | **Port:** 3016

---

## 🚀 Quick Start (30 seconds)

```bash
# 1. Install client
pip install -e services/shared/dopecon_bridge_client

# 2. Set environment
export DOPECONBRIDGE_URL="http://localhost:3016"
export DOPECONBRIDGE_SOURCE_PLANE="cognitive_plane"

# 3. Start bridge
cd services/dopecon-bridge && python3 main.py

# 4. Verify
curl http://localhost:3016/health
```

---

## 📝 Basic Usage

```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient

# Initialize
bridge = DopeconBridgeClient.from_env()

# Publish event
bridge.publish_event("my.event", {"key": "value"}, source="my-service")

# Route to PM plane
bridge.route_pm("leantime.create_task", {"title": "Task"}, "my-service")

# Save to KG
bridge.save_custom_data("workspace-id", "category", "key", {"data": "value"})

# Query decisions
decisions = bridge.recent_decisions(workspace_id="workspace-id", limit=10)
```

---

## 🔗 Essential Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/events` | POST | Publish event |
| `/events/{stream}` | GET | Stream info |
| `/events/history` | GET | Event history |
| `/route/pm` | POST | Route to PM plane |
| `/route/cognitive` | POST | Route to cognitive plane |
| `/kg/custom_data` | GET/POST | KG custom data |
| `/ddg/decisions/recent` | GET | Recent decisions |
| `/ddg/decisions/search` | POST | Search decisions |

---

## 🌍 Environment Variables

### Bridge Server
```bash
DOPECONBRIDGE_HOST=0.0.0.0
DOPECONBRIDGE_PORT=3016
DOPECONBRIDGE_TOKEN=secret                    # Optional
REDIS_URL=redis://localhost:6379/0
CONPORT_URL=http://localhost:3010
LEANTIME_URL=http://localhost:8080
LEANTIME_API_KEY=your-key
DOPEBRAINZ_URL=http://localhost:3020
```

### Client Services
```bash
DOPECONBRIDGE_URL=http://localhost:3016
DOPECONBRIDGE_TOKEN=secret                    # Optional
DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane    # or pm_plane
```

---

## 🧪 Testing Commands

```bash
# Unit tests
python3 -m pytest tests/shared/test_dopecon_bridge_client.py -v

# Integration tests
cd services/dopecon-bridge && python3 -m pytest tests/integration/ -v

# Full validation
./verify_dopecon_bridge.sh

# Smoke test
cd services/dopecon-bridge && ./test_api.sh
```

---

## 🐛 Troubleshooting One-Liners

```bash
# Check bridge health
curl http://localhost:3016/health?detailed=true

# Check bridge is running
ps aux | grep "python.*dopecon-bridge"

# Check Redis connection
redis-cli PING

# Check ConPort connection
curl http://localhost:3010/health

# View bridge logs
docker-compose logs -f dopecon-bridge

# Check metrics
curl http://localhost:3016/metrics | grep dopeconbridge_
```

---

## 📊 Client API Cheat Sheet

### Event Bus
```python
# Publish
bridge.publish_event(event_type, data, stream="dopemux:events", source="svc")

# Stream info
info = bridge.get_stream_info("dopemux:events")

# History
history = bridge.get_event_history("dopemux:events", count=50)
```

### Cross-Plane Routing
```python
# To PM plane
resp = bridge.route_pm(operation, data, requester, source="cognitive")

# To Cognitive plane
resp = bridge.route_cognitive(operation, data, requester, source="pm")
```

### Knowledge Graph
```python
# Save
bridge.save_custom_data(workspace_id, category, key, value)

# Get
data = bridge.get_custom_data(workspace_id, category, key=None, limit=50)

# Search
results = bridge.search_workspace(workspace_id, query, limit=20)
```

### Decision Graph
```python
# Recent
decisions = bridge.recent_decisions(workspace_id=None, limit=20)

# Search
results = bridge.search_decisions(query, workspace_id=None, limit=20)

# Related
related = bridge.related_decisions(decision_id, k=10)
```

### Leantime
```python
# Create project
project = bridge.create_leantime_project(name, description, client_id)

# Create task
task = bridge.create_leantime_task(project_id, title, description, milestone_id)

# Get projects
projects = bridge.get_leantime_projects()

# Get tasks
tasks = bridge.get_leantime_tasks(project_id)
```

### DopeBrainz
```python
# Log learning
bridge.log_brainz_learning(workspace_id, pattern_type, data)

# Get patterns
patterns = bridge.get_brainz_patterns(workspace_id, pattern_type, limit=50)
```

### Async
```python
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

async with AsyncDopeconBridgeClient.from_env() as bridge:
    await bridge.publish_event(...)
    decisions = await bridge.recent_decisions(...)
```

---

## 🎯 Common Patterns

### Service Integration Pattern
```python
# In your service's bridge_adapter.py
from services.shared.dopecon_bridge_client import DopeconBridgeClient, DopeconBridgeConfig

class MyServiceBridgeAdapter:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.bridge = DopeconBridgeClient.from_env()

    def log_activity(self, activity_type: str, data: dict):
        self.bridge.publish_event(
            event_type=f"myservice.{activity_type}",
            data=data,
            source="myservice"
        )
        self.bridge.save_custom_data(
            workspace_id=self.workspace_id,
            category="myservice_activities",
            key=activity_type,
            value=data
        )
```

### Event Publishing Pattern
```python
# Always publish events for state changes
def update_state(self, new_state: str):
    self.state = new_state
    self.bridge.publish_event(
        event_type="service.state_changed",
        data={"old": self.old_state, "new": new_state, "timestamp": time.time()},
        source="service"
    )
```

### Error Handling Pattern
```python
from services.shared.dopecon_bridge_client import DopeconBridgeError

try:
    result = bridge.save_custom_data(...)
except DopeconBridgeError as e:
    logger.error(f"Bridge operation failed: {e}")
    # Fallback logic
except Exception as e:
    logger.exception("Unexpected error")
```

---

## 📦 Docker Compose Snippet

```yaml
services:
  dopecon-bridge:
    build: ./services/dopecon-bridge
    ports:
      - "3016:3016"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CONPORT_URL=http://conport:3010
    depends_on:
      - redis
      - conport
    networks:
      - dopemux

  my-service:
    environment:
      - DOPECONBRIDGE_URL=http://dopecon-bridge:3016
      - DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane
    depends_on:
      - dopecon-bridge
    networks:
      - dopemux
```

---

## 📚 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| **DOPECONBRIDGE_COMPLETE_FINAL_V2.md** | Complete status & deployment |
| **DOPECONBRIDGE_MASTER_GUIDE.md** | Comprehensive usage guide |
| **DOPECONBRIDGE_CONPORT_UPDATE.md** | ConPort integration details |
| **DOPECONBRIDGE_SERVICE_CATALOG.md** | All services documented |
| **START_HERE_DOPECONBRIDGE.md** | Quick start guide |
| **DOPECONBRIDGE_DEPLOYMENT_SUMMARY.md** | Deployment checklist |

---

## ⚡ Performance Tips

1. **Use async client for high throughput:**
   ```python
   async with AsyncDopeconBridgeClient.from_env() as bridge:
       await asyncio.gather(*[bridge.publish_event(...) for _ in range(100)])
   ```

2. **Batch operations when possible:**
   ```python
   for item in items:
       # Process and collect
       events.append(item)
   # Publish all at once
   for event in events:
       bridge.publish_event(...)
   ```

3. **Cache frequently accessed data:**
   ```python
   @lru_cache(maxsize=100)
   def get_workspace_config(workspace_id):
       return bridge.get_custom_data(workspace_id, "config", "settings")
   ```

---

## 🔐 Security Best Practices

1. **Always use tokens in production:**
   ```bash
   DOPECONBRIDGE_TOKEN=$(openssl rand -hex 32)
   ```

2. **Scope operations to workspace:**
   ```python
   # ✅ Good
   bridge.save_custom_data(current_workspace_id, ...)

   # ❌ Bad
   bridge.save_custom_data("global", ...)
   ```

3. **Validate source plane:**
   ```python
   config = DopeconBridgeConfig(
       source_plane="cognitive_plane"  # Explicit
   )
   ```

---

## 🚨 Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` | Bridge not running | `docker-compose up dopecon-bridge` |
| `401 Unauthorized` | Missing/invalid token | Check `DOPECONBRIDGE_TOKEN` |
| `ConPort unavailable` | ConPort down | `docker-compose up conport` |
| `Event not publishing` | Redis down | `docker-compose up redis` |
| `Timeout` | Bridge overloaded | Check metrics, scale if needed |

---

## 📞 Support & Resources

- **Validation:** `./verify_dopecon_bridge.sh`
- **Health:** `curl http://localhost:3016/health`
- **Metrics:** `curl http://localhost:3016/metrics`
- **Logs:** `docker-compose logs -f dopecon-bridge`
- **Docs:** See `DOPECONBRIDGE_MASTER_GUIDE.md`

---

**Quick Reference Card v2.0** | **Port:** 3016 | **Status:** ✅ Production Ready
**Last Updated:** 2025-11-13 | **Team:** Dopemux Core
