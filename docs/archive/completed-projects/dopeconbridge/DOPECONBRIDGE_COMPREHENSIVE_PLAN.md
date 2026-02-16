---
id: DOPECONBRIDGE_COMPREHENSIVE_PLAN
title: Dopeconbridge_Comprehensive_Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopeconbridge_Comprehensive_Plan (explanation) for dopemux documentation
  and developer workflows.
---
# DopeconBridge - Comprehensive Migration & Expansion Plan

## 🎯 Mission

Transform "DopeconBridge" into **DopeconBridge** - a comprehensive coordination layer for ALL Dopemux services including:
- ✅ Already migrated: ADHD Engine, Voice Commands, Task Orchestrator, Serena v2, GPT-Researcher
- 🆕 **Dope Decision Graph (DDDPG)** - Decision knowledge graph
- 🆕 **Dope Context** - Context management
- 🆕 **Dope Brainz** - Intelligence layer
- 🆕 **Leantime Integration** - PM plane coordination
- 🆕 **TaskMaster** - Task management
- 🆕 **All remaining services**

Plus: **Full rename** from "DopeconBridge" to "DopeconBridge"

---

## 📋 Phase 1: Global Renaming (2 hours)

### 1.1 Automated Renaming Script ✅

**File:** `scripts/rename_to_dopecon_bridge.py` (CREATED)

**Renames:**
- `DopeconBridge` → `DopeconBridge`
- `dopecon_bridge` → `dopecon_bridge`
- `DopeconBridgeClient` → `DopeconBridgeClient`
- `DOPECON_BRIDGE_URL` → `DOPECON_BRIDGE_URL`

**Execution:**
```bash
cd /Users/dopemux/code/dopemux-mvp
python3 scripts/rename_to_dopecon_bridge.py
```

### 1.2 Manual Renames Required

**Service directory:**
```bash
mv services/mcp-dopecon-bridge services/dopecon-bridge
```

**Shared client:**
```bash
mv services/shared/dopecon_bridge_client services/shared/dopecon_bridge_client
```

**Documentation:**
```bash
mv DOPECON_BRIDGE_*.md DOPECONBRIDGE_*.md
mv .env.dopecon_bridge.example .env.dopecon_bridge.example
```

### 1.3 Test file rename
```bash
mv tests/shared/test_dopecon_bridge_client.py tests/shared/test_dopecon_bridge_client.py
```

---

## 📋 Phase 2: Add Dope Decision Graph (DDDPG) Integration (3 hours)

### 2.1 Create DDDPG Bridge Adapter

**File:** `services/dddpg/bridge_adapter.py`

```python
"""
DDDPG (Dope Decision Graph) DopeconBridge Adapter

Replaces direct storage access with DopeconBridge client usage.
All decision graph operations flow through DopeconBridge.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add shared modules
SHARED_DIR = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

class DDDPGBridgeAdapter:
    """
    DopeconBridge adapter for Dope Decision Graph.

    Provides decision graph operations via DopeconBridge:
- Decision creation and querying
- Graph traversal and navigation
- Context-aware decision retrieval
- Semantic search
    """

    def __init__(
        self,
        workspace_id: str,
        base_url: str = None,
        token: str = None,
    ):
        self.workspace_id = workspace_id

        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="cognitive_plane",
            )

        self.client = AsyncDopeconBridgeClient(config=config)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def create_decision(
        self,
        summary: str,
        rationale: str,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create decision via DopeconBridge"""
        return await self.client.create_decision(
            summary=summary,
            rationale=rationale,
            implementation_details=implementation_details,
            tags=tags or [],
            workspace_id=self.workspace_id,
        )

    async def get_recent_decisions(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent decisions via DopeconBridge"""
        results = await self.client.recent_decisions(
            workspace_id=self.workspace_id,
            limit=limit,
        )
        return results.items

    async def search_decisions(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search decisions via DopeconBridge"""
        results = await self.client.search_decisions(
            query=query,
            workspace_id=self.workspace_id,
            limit=limit,
        )
        return results.items

    async def get_related_decisions(
        self,
        decision_id: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get related decisions via graph traversal"""
        results = await self.client.related_decisions(
            decision_id=decision_id,
            k=k,
        )
        return results.items

    async def semantic_search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Semantic search via DopeconBridge"""
        results = await self.client.related_text(
            query=query,
            workspace_id=self.workspace_id,
            k=k,
        )
        return results.items

    async def save_graph_state(
        self,
        state_data: Dict[str, Any],
    ) -> bool:
        """Save graph navigation state"""
        return await self.client.save_custom_data(
            workspace_id=self.workspace_id,
            category="dddpg_graph_state",
            key="latest_navigation",
            value=state_data,
        )

    async def get_graph_state(self) -> Optional[Dict[str, Any]]:
        """Get graph navigation state"""
        results = await self.client.get_custom_data(
            workspace_id=self.workspace_id,
            category="dddpg_graph_state",
            key="latest_navigation",
            limit=1,
        )
        if results:
            return results[0].get("value", {})
        return None
```

### 2.2 Update DDDPG Service

**File:** `services/dddpg/kg_integration.py`

Replace storage backends with bridge adapter:

```python
# OLD:
from storage.sqlite_backend import SQLiteBackend
storage = SQLiteBackend(db_path)

# NEW:
from bridge_adapter import DDDPGBridgeAdapter
storage = DDDPGBridgeAdapter(workspace_id=workspace_id)
```

---

## 📋 Phase 3: Add Dope Context Integration (2 hours)

### 3.1 Create Dope Context Bridge Adapter

**File:** `services/dope-context/bridge_adapter.py`

```python
"""
Dope Context DopeconBridge Adapter

Manages context via DopeconBridge for:
- Active context tracking
- Context switching
- Multi-workspace context
- Context history
"""

class DopeContextBridgeAdapter:
    """DopeconBridge adapter for Dope Context service"""

    async def set_active_context(
        self,
        context_id: str,
        context_data: Dict[str, Any],
    ) -> bool:
        """Set active context via DopeconBridge custom data"""
        return await self.client.save_custom_data(
            workspace_id=self.workspace_id,
            category="active_context",
            key=context_id,
            value=context_data,
        )

    async def get_active_context(
        self,
        context_id: str = "default",
    ) -> Optional[Dict[str, Any]]:
        """Get active context"""
        results = await self.client.get_custom_data(
            workspace_id=self.workspace_id,
            category="active_context",
            key=context_id,
            limit=1,
        )
        if results:
            return results[0].get("value", {})
        return None

    async def log_context_switch(
        self,
        from_context: str,
        to_context: str,
        reason: str,
    ) -> bool:
        """Log context switch event"""
        await self.client.publish_event(
            event_type="context.switched",
            data={
                "from": from_context,
                "to": to_context,
                "reason": reason,
                "workspace_id": self.workspace_id,
            },
            source="dope-context",
        )
        return True
```

---

## 📋 Phase 4: Add Dope Brainz Integration (3 hours)

### 4.1 Identify Dope Brainz Components

Based on codebase scan, "Brainz" likely refers to:
- Intelligence services (`services/intelligence/`)
- ML predictions (`services/ml-predictions/`)
- ML risk assessment (`services/ml-risk-assessment/`)
- Session intelligence (`services/session_intelligence/`)
- Working memory assistant (`services/working-memory-assistant/`)

### 4.2 Create Unified Brainz Bridge Adapter

**File:** `services/shared/dopecon_bridge_client/brainz_adapter.py`

```python
"""
Dope Brainz DopeconBridge Adapter

Unified adapter for all intelligence/ML services to interact via DopeconBridge.
"""

class DopeBrainzBridgeAdapter:
    """
    Unified bridge adapter for Dope Brainz intelligence services.

    Handles:
- ML predictions
- Risk assessments
- Session intelligence
- Working memory
- Pattern learning
    """

    async def log_prediction(
        self,
        prediction_type: str,
        prediction_data: Dict[str, Any],
        confidence: float,
    ) -> bool:
        """Log ML prediction via DopeconBridge"""
        return await self.client.save_custom_data(
            workspace_id=self.workspace_id,
            category="ml_predictions",
            key=f"{prediction_type}_{datetime.utcnow().isoformat()}",
            value={
                "type": prediction_type,
                "data": prediction_data,
                "confidence": confidence,
            },
        )

    async def log_risk_assessment(
        self,
        task_id: str,
        risk_score: float,
        risk_factors: List[str],
    ) -> bool:
        """Log risk assessment"""
        await self.client.publish_event(
            event_type="brainz.risk_assessed",
            data={
                "task_id": task_id,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
            },
            source="dope-brainz",
        )
        return True

    async def save_learned_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
    ) -> bool:
        """Save learned pattern"""
        return await self.client.save_custom_data(
            workspace_id=self.workspace_id,
            category="learned_patterns",
            key=pattern_type,
            value=pattern_data,
        )
```

---

## 📋 Phase 5: Add Leantime Integration (2 hours)

### 5.1 Create Leantime Bridge Adapter

**File:** `services/shared/dopecon_bridge_client/leantime_adapter.py`

```python
"""
Leantime DopeconBridge Adapter

PM Plane integration for Leantime via DopeconBridge.
"""

class LeantimeBridgeAdapter:
    """
    DopeconBridge adapter for Leantime PM plane integration.

    Features:
- Task synchronization (PM ↔ Cognitive)
- Project updates
- Sprint planning
- Resource allocation
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id

        # Use PM plane for Leantime
        config = DopeconBridgeConfig.from_env()
        config.source_plane = "pm_plane"

        self.client = AsyncDopeconBridgeClient(config=config)

    async def sync_task_to_leantime(
        self,
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Sync cognitive task to PM plane (Leantime)"""
        response = await self.client.route_pm(
            operation="leantime.create_task",
            data=task_data,
            requester="cognitive-task-sync",
        )
        return response.data if response.success else {}

    async def get_leantime_tasks(
        self,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """Get tasks from Leantime via DopeconBridge"""
        response = await self.client.route_pm(
            operation="leantime.get_tasks",
            data={"project_id": project_id},
            requester="cognitive-query",
        )
        return response.data.get("tasks", []) if response.success else []

    async def update_sprint_status(
        self,
        sprint_id: str,
        status: str,
        completion: float,
    ) -> bool:
        """Update sprint status in Leantime"""
        response = await self.client.route_pm(
            operation="leantime.update_sprint",
            data={
                "sprint_id": sprint_id,
                "status": status,
                "completion": completion,
            },
            requester="sprint-tracker",
        )
        return response.success
```

---

## 📋 Phase 6: Add TaskMaster Integration (2 hours)

### 6.1 Create TaskMaster Bridge Adapter

**File:** `services/taskmaster/bridge_adapter.py`

```python
"""
TaskMaster DopeconBridge Adapter

Task management via DopeconBridge for:
- Task creation and tracking
- Task orchestration
- Cross-plane task sync
"""

class TaskMasterBridgeAdapter:
    """DopeconBridge adapter for TaskMaster service"""

    async def create_task(
        self,
        title: str,
        description: str,
        priority: int = 3,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create task via DopeconBridge"""
        return await self.client.create_progress_entry(
            description=f"{title}: {description}",
            status="TODO",
            metadata={
                "taskmaster_task": True,
                "priority": priority,
                "tags": tags or [],
                "title": title,
            },
            workspace_id=self.workspace_id,
        )

    async def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get tasks via DopeconBridge"""
        return await self.client.get_progress_entries(
            workspace_id=self.workspace_id,
            limit=limit,
            status=status,
        )

    async def sync_to_pm_plane(
        self,
        task_id: str,
    ) -> bool:
        """Sync task to PM plane (Leantime/etc)"""
        # Get task details
        tasks = await self.get_tasks()
        task = next((t for t in tasks if t.get("id") == task_id), None)

        if not task:
            return False

        # Route to PM plane
        response = await self.client.route_pm(
            operation="taskmaster.sync_task",
            data=task,
            requester="taskmaster",
        )

        return response.success
```

---

## 📋 Phase 7: Add Remaining Services (4 hours)

### 7.1 Services to Migrate

| Service | Priority | Adapter File | Estimated Time |
|---------|----------|--------------|----------------|
| **monitoring-dashboard** | HIGH | `monitoring/bridge_adapter.py` | 30 min |
| **activity-capture** | HIGH | `activity_capture/bridge_adapter.py` | 30 min |
| **workspace-watcher** | MEDIUM | `workspace_watcher/bridge_adapter.py` | 30 min |
| **break-suggester** | MEDIUM | `break_suggester/bridge_adapter.py` | 20 min |
| **energy-trends** | MEDIUM | `energy_trends/bridge_adapter.py` | 20 min |
| **interruption-shield** | MEDIUM | `interruption_shield/bridge_adapter.py` | 30 min |
| **slack-integration** | LOW | `slack_integration/bridge_adapter.py` | 30 min |
| **agents/** | VARIES | Individual adapters | 2 hours |

### 7.2 Generic Service Adapter Template

```python
"""
{Service Name} DopeconBridge Adapter

Replace direct ConPort/storage access with DopeconBridge.
"""

from services.shared.dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

class {ServiceName}BridgeAdapter:
    """DopeconBridge adapter for {Service Name}"""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        config = DopeconBridgeConfig.from_env()
        self.client = AsyncDopeconBridgeClient(config=config)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    # Add service-specific methods here
```

---

## 📋 Phase 8: Update DopeconBridge Server (2 hours)

### 8.1 Add Missing Endpoints

**File:** `services/dopecon-bridge/main.py`

Add these endpoints for comprehensive coverage:

```python
@app.post("/route/dddpg")
async def route_to_dddpg(operation: str, data: Dict[str, Any]):
    """Route operation to Dope Decision Graph"""
    # Implementation
    pass

@app.post("/route/brainz")
async def route_to_brainz(operation: str, data: Dict[str, Any]):
    """Route operation to Dope Brainz intelligence"""
    # Implementation
    pass

@app.post("/route/leantime")
async def route_to_leantime(operation: str, data: Dict[str, Any]):
    """Route operation to Leantime (PM plane)"""
    # Implementation
    pass

@app.post("/route/taskmaster")
async def route_to_taskmaster(operation: str, data: Dict[str, Any]):
    """Route operation to TaskMaster"""
    # Implementation
    pass
```

### 8.2 Update Service Registry

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

    # Infrastructure
    "conport": "http://conport:3010",
}
```

---

## 📋 Phase 9: Update All Documentation (2 hours)

### 9.1 Global Find/Replace in Docs

```bash
# In all .md files:
sed -i 's/DopeconBridge/DopeconBridge/g' *.md
sed -i 's/dopecon_bridge/dopecon_bridge/g' *.md
sed -i 's/DOPECON_BRIDGE/DOPECON_BRIDGE/g' *.md
```

### 9.2 Update README.md

Add DopeconBridge architecture diagram and service list.

### 9.3 Create Service Catalog

**File:** `DOPECONBRIDGE_SERVICE_CATALOG.md`

List all services with their bridge adapter status.

---

## 📋 Phase 10: Testing & Validation (3 hours)

### 10.1 Update All Tests

```bash
# Rename test files
mv tests/shared/test_dopecon_bridge_client.py tests/shared/test_dopecon_bridge_client.py

# Update test imports
sed -i 's/dopecon_bridge/dopecon_bridge/g' tests/**/*.py
```

### 10.2 Integration Tests

Create comprehensive integration tests for:
- Voice Commands → DopeconBridge → ConPort
- DDDPG → DopeconBridge → Decisions
- TaskMaster → DopeconBridge → PM Plane
- Leantime → DopeconBridge → Cognitive Plane

### 10.3 Validation Script

Update validation script to check all services:

```python
# Check all adapters can be imported
adapters = [
    "voice_commands.bridge_adapter",
    "task_orchestrator.adapters.bridge_adapter",
    "serena.v2.bridge_adapter",
    "dddpg.bridge_adapter",
    "dope_context.bridge_adapter",
    "taskmaster.bridge_adapter",
    # ... etc
]
```

---

## 📊 Timeline & Effort

| Phase | Task | Time | Total |
|-------|------|------|-------|
| 1 | Global Renaming | 2h | 2h |
| 2 | DDDPG Integration | 3h | 5h |
| 3 | Dope Context | 2h | 7h |
| 4 | Dope Brainz | 3h | 10h |
| 5 | Leantime | 2h | 12h |
| 6 | TaskMaster | 2h | 14h |
| 7 | Remaining Services | 4h | 18h |
| 8 | DopeconBridge Server | 2h | 20h |
| 9 | Documentation | 2h | 22h |
| 10 | Testing & Validation | 3h | 25h |

**Total Estimated Time: 25 hours (3-4 working days)**

---

## 🚀 Execution Plan

### Day 1: Foundation (8 hours)
- Execute global renaming script
- Update DopeconBridge server
- Update documentation
- Verify existing adapters still work

### Day 2: Core Services (8 hours)
- DDDPG integration
- Dope Context integration
- Dope Brainz foundation
- Leantime adapter

### Day 3: Expansion (8 hours)
- TaskMaster adapter
- Remaining services migration
- Comprehensive testing
- Final validation

### Day 4: Polish & Deploy (1 hour)
- Final documentation review
- Deploy to staging
- Performance validation
- Create completion report

---

## 🎯 Success Criteria

- ✅ ALL references renamed to "DopeconBridge"
- ✅ ALL critical services have bridge adapters
- ✅ DDDPG, Dope Context, Dope Brainz integrated
- ✅ Leantime and TaskMaster integrated
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Deployment successful

---

## 🔧 Quick Start

To begin the migration:

```bash
# 1. Run renaming script
python3 scripts/rename_to_dopecon_bridge.py

# 2. Verify renaming
grep -r "DopeconBridge" services/ --include="*.py" || echo "✓ Renamed"

# 3. Run tests
python3 -m pytest tests/shared/test_dopecon_bridge_client.py -v

# 4. Start creating adapters (use templates from Phase 2-7)

# 5. Update DopeconBridge server endpoints

# 6. Integration testing
```

---

**This is a comprehensive 25-hour plan to fully rename and expand DopeconBridge to cover ALL Dopemux services.**

Ready to execute when you are!
