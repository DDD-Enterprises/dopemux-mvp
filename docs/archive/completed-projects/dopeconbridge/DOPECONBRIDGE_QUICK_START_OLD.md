---
id: DOPECONBRIDGE_QUICK_START_OLD
title: Dopeconbridge_Quick_Start_Old
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# DopeconBridge Migration - Quick Start Checklist

**For the next developer picking up this work.**

## ✅ What's Already Done

- [x] Shared DopeconBridge client (sync + async) with full API
- [x] 5 service-specific bridge adapters created
- [x] 4 new DopeconBridge endpoints added to `kg_endpoints.py`
- [x] All shared client tests passing (4/4)
- [x] Comprehensive documentation (25KB+)
- [x] Environment configuration templates
- [x] Voice Commands API updated to use bridge

## 🔧 Immediate Tasks (Start Here)

### 1. Verify DopeconBridge Endpoints (30 min)

The new endpoints are added to code but need ConPort MCP integration:

```bash
# File: services/mcp-dopecon-bridge/kg_endpoints.py
# Lines: 428-643 (new endpoints)

# Check these endpoints work:
# POST /kg/decisions - create_decision()
# POST /kg/progress - create_progress_entry()
# GET /kg/progress - get_progress_entries()
# POST /kg/links - create_link()
```

**Action Items:**
```bash
cd services/mcp-dopecon-bridge

# 1. Check ConPortMCPClient has required methods:
grep -n "log_decision\|log_progress\|get_progress\|link_conport_items" mcp_client.py

# 2. If missing, implement them in mcp_client.py
# 3. Start DopeconBridge and test endpoints:
python3 main.py

# 4. Test with curl:
curl -X POST http://localhost:3016/kg/decisions \
  -H "Content-Type: application/json" \
  -H "X-Source-Plane: cognitive_plane" \
  -d '{"summary": "Test", "rationale": "Testing", "workspace_id": "/workspace"}'
```

### 2. Update Docker Compose Files (1 hour)

Add DopeconBridge env vars to all service definitions:

```yaml
# File: docker-compose.master.yml
# Add to each service:

services:
  adhd-engine:
    environment:
      - DOPECON_BRIDGE_URL=http://mcp-dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - WORKSPACE_ID=/workspace

  voice-commands:
    environment:
      - DOPECON_BRIDGE_URL=http://mcp-dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - WORKSPACE_ID=/workspace

  task-orchestrator:
    environment:
      - DOPECON_BRIDGE_URL=http://mcp-dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - WORKSPACE_ID=/workspace

  serena:
    environment:
      - DOPECON_BRIDGE_URL=http://mcp-dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - WORKSPACE_ROOT=/workspace

  dopemux-gpt-researcher:
    environment:
      - DOPECON_BRIDGE_URL=http://mcp-dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - WORKSPACE_ID=/workspace
```

**Files to update:**
- [ ] `docker-compose.master.yml`
- [ ] `docker-compose.unified.yml`
- [ ] `docker-compose.staging.yml`
- [ ] `docker/mcp-servers/docker-compose.yml`

### 3. Actually Use Bridge Adapters in Services (1-2 hours)

The adapters exist but services need to import and use them:

#### Task Orchestrator
```python
# File: services/task-orchestrator/enhanced_orchestrator.py
# Line: ~358 (search for CONPORT_URL)

# OLD:
conport_url = os.getenv("CONPORT_URL", "http://localhost:8005")
self.conport_adapter = ConPortEventAdapter(conport_url)

# NEW:
from adapters.bridge_adapter import TaskOrchestratorBridgeAdapter
workspace_id = os.getenv("WORKSPACE_ID", os.getcwd())
self.conport_adapter = TaskOrchestratorBridgeAdapter(workspace_id)
```

#### Serena v2
```python
# File: services/serena/v2/mcp_server.py
# Line: ~495 (search for ConPortDBClient)

# OLD:
from conport_client_unified import ConPortDBClient
self.conport_client = ConPortDBClient(...)

# NEW:
from bridge_adapter import SerenaBridgeAdapter
self.conport_client = SerenaBridgeAdapter(workspace_id=workspace_id)
```

#### GPT-Researcher
```python
# File: services/dopemux-gpt-researcher/research_api/main.py
# Search for ConPortAdapter usage

# OLD:
from adapters.conport_adapter import ConPortAdapter
self.conport = ConPortAdapter(workspace_id)

# NEW:
from adapters.bridge_adapter import ResearchBridgeAdapter
self.conport = ResearchBridgeAdapter(workspace_id)
```

**Files to update:**
- [ ] `services/task-orchestrator/enhanced_orchestrator.py`
- [ ] `services/serena/v2/mcp_server.py`
- [ ] `services/serena/v2/metrics_dashboard.py`
- [ ] `services/dopemux-gpt-researcher/research_api/main.py`

### 4. Create Integration Tests (2 hours)

```bash
# Create: tests/integration/test_bridge_migration.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_voice_commands_end_to_end():
    """Test voice command → bridge → ConPort flow"""
    async with AsyncClient(base_url="http://localhost:3007") as client:
        response = await client.post("/api/v1/decompose-task", json={
            "voice_input": "Test task",
            "user_id": "test_user",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "decision_id" in data["conport_result"]

@pytest.mark.asyncio
async def test_task_orchestrator_bridge_sync():
    """Test task orchestrator → bridge → ConPort sync"""
    # Test task creation and sync
    ...

@pytest.mark.asyncio
async def test_serena_decision_search():
    """Test Serena → bridge → decision search"""
    # Test decision search via bridge
    ...
```

**Action Items:**
- [ ] Create `tests/integration/test_bridge_migration.py`
- [ ] Run tests with services up: `python3 -m pytest tests/integration/ -v`
- [ ] Verify all cross-service flows work

## 📋 Verification Checklist

After completing immediate tasks, verify:

### DopeconBridge
- [ ] Service starts without errors
- [ ] All 4 new endpoints respond
- [ ] ConPort MCP client methods work
- [ ] Authority enforcement working (cognitive plane only for writes)

### Service Adapters
- [ ] Voice Commands uses `VoiceCommandsBridgeAdapter`
- [ ] Task Orchestrator uses `TaskOrchestratorBridgeAdapter`
- [ ] Serena uses `SerenaBridgeAdapter`
- [ ] GPT-Researcher uses `ResearchBridgeAdapter`
- [ ] ADHD Engine still uses `ConPortBridgeAdapter`

### Docker Compose
- [ ] All services have `DOPECON_BRIDGE_URL` env var
- [ ] All services have `DOPECON_BRIDGE_SOURCE_PLANE` env var
- [ ] All services have `WORKSPACE_ID` or `WORKSPACE_ROOT` env var
- [ ] Services can connect to DopeconBridge container

### End-to-End Testing
- [ ] Voice command creates decision via bridge
- [ ] Task orchestrator syncs tasks via bridge
- [ ] Serena searches decisions via bridge
- [ ] GPT-Researcher saves state via bridge
- [ ] ADHD Engine logs progress via bridge

## 🔍 Common Issues & Solutions

### Issue: "Module 'dopecon_bridge_client' not found"
**Solution:**
```bash
# Ensure shared module is in PYTHONPATH:
export PYTHONPATH=/path/to/dopemux-mvp/services:$PYTHONPATH

# Or add to service code:
import sys
sys.path.insert(0, '/path/to/dopemux-mvp/services')
```

### Issue: "DopeconBridge error (403): cognitive_plane authority required"
**Solution:**
```bash
# Set source plane in environment:
export DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane

# Or in docker-compose.yml:
environment:
  - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
```

### Issue: "ConPort MCP client method not found"
**Solution:**
```python
# Check if method exists in services/mcp-dopecon-bridge/mcp_client.py
# If missing, implement it using existing patterns

# Example:
async def log_decision(self, summary, rationale, **kwargs):
    # Call ConPort MCP stdio interface
    result = await self.call_tool("conport", "log_decision", {
        "summary": summary,
        "rationale": rationale,
        **kwargs
    })
    return result
```

### Issue: "httpx.ConnectError: Connection refused"
**Solution:**
```bash
# Check DopeconBridge is running:
curl http://localhost:3016/health

# If not running:
cd services/mcp-dopecon-bridge
python3 main.py

# In Docker:
docker-compose up mcp-dopecon-bridge
```

## 📚 Key Documentation References

1. **Client Usage:** `services/shared/dopecon_bridge_client/README.md`
2. **Migration Guide:** `DOPECON_BRIDGE_MIGRATION_COMPLETE.md`
3. **Executive Summary:** `DOPECON_BRIDGE_EXECUTIVE_SUMMARY.md`
4. **Environment Setup:** `.env.dopecon_bridge.example`

## 🎯 Definition of Done

You'll know you're done when:

1. ✅ All new DopeconBridge endpoints work with real ConPort
2. ✅ All 5 services use their bridge adapters (not direct ConPort)
3. ✅ Docker Compose files have bridge configuration
4. ✅ Integration tests pass for all critical flows
5. ✅ No direct `CONPORT_URL` usage in migrated services
6. ✅ All services can publish events to bridge
7. ✅ Cross-plane routing works (PM ↔ Cognitive)

## ⏭️ After Completion

Once immediate tasks are done:

1. **Deploy to staging:** Test in staging environment
2. **Monitor metrics:** Check DopeconBridge logs/metrics
3. **Migrate remaining services:** Use same adapter pattern for agents, orchestrator
4. **Update architecture docs:** Add DopeconBridge to diagrams
5. **Performance testing:** Ensure no regressions from bridge layer

## 🆘 Need Help?

- **Code questions:** Check adapter implementations for examples
- **DopeconBridge questions:** See `services/mcp-dopecon-bridge/main.py`
- **Client questions:** See `services/shared/dopecon_bridge_client/client.py`
- **Testing questions:** See `tests/shared/test_dopecon_bridge_client.py`

## 📝 Time Estimates

Based on complexity:

- **Task 1** (Verify endpoints): 30 min
- **Task 2** (Docker Compose): 1 hour
- **Task 3** (Update services): 1-2 hours
- **Task 4** (Integration tests): 2 hours

**Total: 4.5-5.5 hours** to complete immediate migration

---

**Last Updated:** After shared client implementation
**Status:** Ready for next developer
**Next Step:** Task 1 - Verify DopeconBridge endpoints
