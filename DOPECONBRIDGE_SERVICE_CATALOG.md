# DopeconBridge Service Catalog

**Complete registry of all Dopemux services and their DopeconBridge integration status**

Last Updated: 2025-01-15

---

## 📊 Overview

| Category | Total Services | Integrated | Remaining |
|----------|---------------|------------|-----------|
| **Core Services** | 10 | 10 | 0 |
| **Supporting Services** | 4 | 4 | 0 |
| **Experimental** | 6+ | 0 | 6+ |
| **TOTAL** | 20+ | 14 | 6+ |

**Integration Progress:** 70% complete

---

## ✅ Fully Integrated Services

### Core Cognitive Services

#### 1. ADHD Engine
- **Path:** `services/adhd_engine/`
- **Adapter:** `services/adhd_engine/bridge_integration.py`
- **Status:** ✅ COMPLETE
- **Features:**
  - Activity tracking
  - Progress logging
  - State persistence
  - Custom data storage
- **DopeconBridge Operations:**
  - `log_progress_entry()`
  - `get_progress_entries()`
  - `save_custom_data()`
  - `get_custom_data()`

#### 2. Voice Commands
- **Path:** `services/voice-commands/`
- **Adapter:** `services/voice-commands/bridge_adapter.py`
- **Status:** ✅ COMPLETE
- **Features:**
  - Task decomposition from voice
  - Natural language processing
  - Command execution
- **DopeconBridge Operations:**
  - `create_decision()`
  - `log_voice_command()`
  - `publish_event("voice.command.executed")`

#### 3. Task Orchestrator
- **Path:** `services/task-orchestrator/`
- **Adapter:** `services/task-orchestrator/adapters/bridge_adapter.py`
- **Status:** ✅ COMPLETE
- **Features:**
  - Task workflow coordination
  - Dependency management
  - Cross-service orchestration
- **DopeconBridge Operations:**
  - `route_pm()`
  - `route_cognitive()`
  - `publish_event()`

#### 4. Serena v2
- **Path:** `services/serena/v2/`
- **Adapter:** `services/serena/v2/bridge_adapter.py`
- **Status:** ✅ COMPLETE
- **Features:**
  - Decision search
  - Code navigation
  - Intelligence queries
- **DopeconBridge Operations:**
  - `recent_decisions()`
  - `search_decisions()`
  - `related_decisions()`

#### 5. GPT-Researcher
- **Path:** `services/dopemux-gpt-researcher/`
- **Adapter:** `services/dopemux-gpt-researcher/research_api/adapters/bridge_adapter.py`
- **Status:** ✅ COMPLETE
- **Features:**
  - Research state management
  - Findings storage
  - Research coordination
- **DopeconBridge Operations:**
  - `save_research_state()`
  - `get_research_state()`
  - `log_research_finding()`

#### 6. DDDPG (Dope Decision Graph)
- **Path:** `services/dddpg/`
- **Adapter:** `services/dddpg/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Decision graph operations
  - Graph traversal
  - Semantic search
  - State management
- **DopeconBridge Operations:**
  - `create_decision()`
  - `get_recent_decisions()`
  - `search_decisions()`
  - `get_related_decisions()`
  - `semantic_search()`
  - `save_graph_state()`
- **New Routing:** `/route/dddpg`

#### 7. Dope Context
- **Path:** `services/dope-context/`
- **Adapter:** `services/dope-context/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Context tracking
  - Context switching
  - Snapshot management
  - Context history
- **DopeconBridge Operations:**
  - `set_active_context()`
  - `get_active_context()`
  - `log_context_switch()`
  - `save_context_snapshot()`
  - `restore_context_snapshot()`

#### 8. Dope Brainz (Intelligence/ML)
- **Path:** `services/shared/dopecon_bridge_client/`
- **Adapter:** `services/shared/dopecon_bridge_client/brainz_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - ML predictions
  - Risk assessment
  - Pattern learning
  - Session intelligence
  - Working memory
- **DopeconBridge Operations:**
  - `log_prediction()`
  - `log_risk_assessment()`
  - `save_learned_pattern()`
  - `log_session_intelligence()`
  - `save_working_memory_state()`
- **New Routing:** `/route/brainz`

---

### PM Plane Services

#### 9. Leantime Integration
- **Path:** `services/shared/dopecon_bridge_client/`
- **Adapter:** `services/shared/dopecon_bridge_client/leantime_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Task synchronization (Cognitive ↔ PM)
  - Project management
  - Sprint tracking
  - Resource allocation
  - Task mapping
- **DopeconBridge Operations:**
  - `sync_task_to_leantime()`
  - `get_leantime_tasks()`
  - `update_sprint_status()`
  - `create_project()`
  - `allocate_resource()`
  - `sync_from_cognitive()`
- **New Routing:** `/route/leantime`

#### 10. TaskMaster
- **Path:** `services/taskmaster/`
- **Adapter:** `services/taskmaster/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Task creation and management
  - Status tracking
  - PM plane synchronization
  - Task assignment
  - Collaboration (comments)
- **DopeconBridge Operations:**
  - `create_task()`
  - `get_tasks()`
  - `update_task_status()`
  - `sync_to_pm_plane()`
  - `assign_task()`
  - `complete_task()`
- **New Routing:** `/route/taskmaster`

---

### Supporting Services

#### 11. Monitoring Dashboard
- **Path:** `services/monitoring-dashboard/`
- **Adapter:** `services/monitoring-dashboard/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Service health monitoring
  - Performance metrics
  - Alert management
  - Dashboard state
- **DopeconBridge Operations:**
  - `log_service_health()`
  - `log_performance_metric()`
  - `create_alert()`
  - `save_dashboard_state()`

#### 12. Activity Capture
- **Path:** `services/activity-capture/`
- **Adapter:** `services/activity-capture/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Window activity tracking
  - Application usage
  - Time tracking
  - Activity analytics
- **DopeconBridge Operations:**
  - `log_window_activity()`
  - `log_application_usage()`
  - `get_daily_activity()`
  - `start_activity_session()`

#### 13. Workspace Watcher
- **Path:** `services/workspace-watcher/`
- **Adapter:** `services/workspace-watcher/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - File change detection
  - Project activity tracking
  - Workspace state monitoring
- **DopeconBridge Operations:**
  - `log_file_change()`
  - `save_workspace_snapshot()`
  - `get_file_history()`

#### 14. Interruption Shield
- **Path:** `services/interruption-shield/`
- **Adapter:** `services/interruption-shield/bridge_adapter.py`
- **Status:** ✅ COMPLETE (NEW)
- **Features:**
  - Interruption detection
  - Focus session management
  - Distraction tracking
- **DopeconBridge Operations:**
  - `log_interruption()`
  - `start_focus_session()`
  - `end_focus_session()`

---

## ⏳ Remaining Services

### Low Priority / Experimental

#### 15. Break Suggester
- **Path:** `services/break-suggester/`
- **Status:** ⏳ PLANNED
- **Priority:** MEDIUM
- **Estimated Effort:** 30 minutes

#### 16. Energy Trends
- **Path:** `services/energy-trends/`
- **Status:** ⏳ PLANNED
- **Priority:** MEDIUM
- **Estimated Effort:** 30 minutes

#### 17. Slack Integration
- **Path:** `services/slack-integration/`
- **Status:** ⏳ PLANNED
- **Priority:** LOW
- **Estimated Effort:** 45 minutes

#### 18. Various Agents
- **Path:** `services/agents/`
- **Status:** ⏳ PLANNED
- **Priority:** VARIES
- **Estimated Effort:** 2-3 hours
- **Note:** Multiple agents may need individual adapters

#### 19. Working Memory Assistant
- **Path:** `services/working-memory-assistant/`
- **Status:** ⏳ PLANNED
- **Priority:** MEDIUM
- **Estimated Effort:** 45 minutes

#### 20. Session Intelligence
- **Path:** `services/session_intelligence/`
- **Status:** ⏳ PLANNED
- **Priority:** MEDIUM
- **Estimated Effort:** 45 minutes

---

## 🔧 DopeconBridge Server Endpoints

### Core Routing Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/route/pm` | PM plane coordination | ✅ COMPLETE |
| `/route/cognitive` | Cognitive plane coordination | ✅ COMPLETE |
| `/route/dddpg` | Decision graph operations | ✅ NEW |
| `/route/brainz` | Intelligence/ML operations | ✅ NEW |
| `/route/leantime` | Leantime PM operations | ✅ NEW |
| `/route/taskmaster` | TaskMaster operations | ✅ NEW |

### Event & Data Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/events` | Publish events | ✅ COMPLETE |
| `/events/{stream}` | Get stream info | ✅ COMPLETE |
| `/events/history` | Get event history | ✅ COMPLETE |
| `/ddg/decisions/recent` | Recent decisions | ✅ COMPLETE |
| `/ddg/decisions/search` | Search decisions | ✅ COMPLETE |
| `/ddg/decisions/related/{id}` | Related decisions | ✅ COMPLETE |
| `/ddg/related_text` | Semantic search | ✅ COMPLETE |
| `/kg/custom_data` | Custom data storage | ✅ COMPLETE |

---

## 📋 Service Registry

**File:** `services/dopecon-bridge/main.py`

```python
SERVICE_REGISTRY = {
    # Cognitive Plane
    "adhd_engine": "http://adhd-engine:3001",
    "serena": "http://serena:3002",
    "dope_context": "http://dope-context:3003",
    "dddpg": "http://dddpg:3004",
    "dope_brainz": "http://dope-brainz:3005",
    "voice_commands": "http://voice-commands:3007",
    "task_orchestrator": "http://task-orchestrator:3014",
    
    # PM Plane
    "leantime": "http://leantime:80",
    "taskmaster": "http://taskmaster:3008",
    
    # Supporting
    "monitoring": "http://monitoring-dashboard:3009",
    "activity_capture": "http://activity-capture:3011",
    "workspace_watcher": "http://workspace-watcher:3012",
    "interruption_shield": "http://interruption-shield:3013",
    
    # Infrastructure
    "conport": "http://conport:3010",
    "dopecon_bridge": "http://dopecon-bridge:3016",
}
```

---

## 🎯 Integration Patterns

### Pattern 1: Basic Event Publishing

```python
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

client = AsyncDopeconBridgeClient.from_env()

await client.publish_event(
    event_type="service.action.completed",
    data={"key": "value"},
    source="my-service"
)
```

### Pattern 2: Custom Data Storage

```python
# Save
await client.save_custom_data(
    workspace_id=workspace_id,
    category="my_category",
    key="my_key",
    value={"data": "here"}
)

# Retrieve
results = await client.get_custom_data(
    workspace_id=workspace_id,
    category="my_category",
    key="my_key",
    limit=10
)
```

### Pattern 3: Cross-Plane Routing

```python
# Cognitive → PM
response = await client.route_pm(
    operation="leantime.create_task",
    data={"title": "Task", "priority": 3},
    requester="cognitive-service"
)

# PM → Cognitive
response = await client.route_cognitive(
    operation="adhd_engine.get_state",
    data={},
    requester="pm-service"
)
```

### Pattern 4: Service-Specific Adapters

```python
from services.dddpg.bridge_adapter import DDDPGBridgeAdapter

async with DDDPGBridgeAdapter(workspace_id="default") as adapter:
    decision = await adapter.create_decision(
        summary="Architecture decision",
        rationale="Improves scalability"
    )
```

---

## 📊 Statistics

### Code Metrics
- **Total Services:** 20+
- **Integrated Services:** 14
- **Adapter Files:** 14
- **Total Adapter LOC:** ~3,000 lines
- **New Routing Endpoints:** 4
- **Test Coverage:** 100% for shared client

### Integration Timeline
- **Phase 1 (Original):** 5 services (4 hours)
- **Phase 2-6 (Path B):** 9 services (12 hours)
- **Remaining:** 6+ services (~4 hours)

---

## 🚀 Quick Reference

### For Service Developers

**To integrate your service:**

1. Install shared client:
```bash
pip install httpx pydantic
```

2. Import and configure:
```python
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient, DopeconBridgeConfig

config = DopeconBridgeConfig.from_env()
client = AsyncDopeconBridgeClient(config=config)
```

3. Use operations:
```python
# Events
await client.publish_event(event_type, data, source)

# Custom data
await client.save_custom_data(workspace_id, category, key, value)

# Cross-plane routing
response = await client.route_pm(operation, data, requester)
```

### For Operations

**Environment Variables:**
```bash
DOPECON_BRIDGE_URL=http://localhost:3016
DOPECON_BRIDGE_TOKEN=<optional>
DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane  # or pm_plane
```

**Docker Compose:**
```yaml
services:
  my-service:
    environment:
      - DOPECON_BRIDGE_URL=http://dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
```

---

## 📝 Notes

### Service Discovery
Services can discover DopeconBridge via:
- Environment variable `DOPECON_BRIDGE_URL`
- Default: `http://localhost:3016`
- Docker: `http://dopecon-bridge:3016`

### Authentication
- Optional token-based auth via `DOPECON_BRIDGE_TOKEN`
- Header: `Authorization: Bearer <token>`

### Source Plane
- `cognitive_plane` - For cognitive services
- `pm_plane` - For PM services
- Used for routing and authorization

---

**Last Updated:** 2025-01-15  
**Version:** 2.0  
**Integration Progress:** 70% (14/20 services)
