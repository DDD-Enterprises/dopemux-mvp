---
id: ADR-207-LEANTIME-API-RESEARCH
title: Adr 207 Leantime Api Research
type: adr
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Adr 207 Leantime Api Research (adr) for dopemux documentation and developer
  workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-207 Appendix: Leantime API Integration Research

**Date**: 2025-10-19
**Related**: ADR-207 (Architecture 3.0)
**Status**: Research Complete
**Purpose**: Document existing Leantime integration implementation for Phase 2

---

## Executive Summary

✅ **Leantime integration already exists** in Task-Orchestrator's `EnhancedTaskOrchestrator` class
✅ **Production-ready implementation** with authentication, polling, sync, and error handling
✅ **No rebuild required** - just need to update for Architecture 3.0 patterns

---

## Existing Implementation Analysis

### Location
`services/task-orchestrator/enhanced_orchestrator.py` (lines 107-300+)

### Core Components

#### 1. Leantime Connection Management

**Initialization** (lines 179-196):
```python
async def _initialize_leantime_connection(self) -> None:
    """Initialize connection to Leantime JSON-RPC API."""
    self.leantime_session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={
            "Authorization": f"Bearer {self.leantime_token}",
            "Content-Type": "application/json"
        }
    )
    await self._test_leantime_connection()
```

**Authentication**: Bearer token-based
**Transport**: aiohttp ClientSession
**Timeout**: 30 seconds
**Format**: JSON-RPC 2.0

#### 2. Leantime API Endpoints

**Connection Test** (lines 198-217):
```python
async def _test_leantime_connection(self) -> bool:
    """Test Leantime API connectivity."""
    async with self.leantime_session.post(
        f"{self.leantime_url}/api/jsonrpc",
        json={
            "jsonrpc": "2.0",
            "method": "leantime.rpc.projects.getAllProjects",
            "params": {"limit": 1},
            "id": 1
        }
    ) as response:
        return response.status == 200 and "result" in await response.json()
```

**JSON-RPC Format**:
- **Endpoint**: `{leantime_url}/api/jsonrpc`
- **Method**: JSON-RPC 2.0 protocol
- **Example Method**: `leantime.rpc.projects.getAllProjects`
- **Params**: Dictionary of method-specific parameters
- **ID**: Request identifier for response matching

#### 3. Task Synchronization

**Polling Worker** (lines 281-298):
```python
async def _leantime_poller(self) -> None:
    """Background poller for Leantime task updates."""
    while self.running:
        try:
            updated_tasks = await self._fetch_updated_leantime_tasks()
            for leantime_task in updated_tasks:
                await self._process_leantime_task_update(leantime_task)
            await asyncio.sleep(30)  # Poll every 30 seconds
        except Exception as e:
            logger.error(f"Leantime polling error: {e}")
            await asyncio.sleep(60)  # Back off on error
```

**Polling Strategy**:
- **Frequency**: 30-second intervals
- **Error Handling**: 60-second backoff on failure
- **Processing**: Async task processing for each update

#### 4. Data Model

**OrchestrationTask** (lines 53-92):
```python
@dataclass
class OrchestrationTask:
    """Enhanced task representation for orchestration."""
    id: str
    leantime_id: Optional[int] = None  # ← Leantime task ID
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    complexity_score: float = 0.5
    estimated_minutes: int = 25

    # ADHD-specific fields
    energy_required: str = "medium"
    cognitive_load: float = 0.5
    context_switches_allowed: int = 2
    break_frequency_minutes: int = 25

    # Orchestration metadata
    dependencies: List[str] = None
    dependents: List[str] = None

    # Sync tracking
    last_synced: Optional[datetime] = None
    sync_conflicts: List[str] = None
```

**Key Fields**:
- `leantime_id`: Links orchestration task to Leantime
- `last_synced`: Timestamp for sync tracking
- `sync_conflicts`: List of detected conflicts

#### 5. Background Workers

**Worker Tasks** (lines 266-277):
```python
async def _start_background_workers(self) -> None:
    """Start background worker tasks."""
    workers = [
        self._leantime_poller(),          # Poll Leantime for updates
        self._sync_processor(),            # Process sync events
        self._adhd_monitor(),              # Monitor ADHD accommodations
        self._implicit_automation_engine(), # Auto-trigger workflows
        self._progress_correlator()        # Correlate progress across systems
    ]
    self.workers = [asyncio.create_task(worker) for worker in workers]
```

**5 Background Workers**:
1. **Leantime Poller**: Fetch Leantime updates every 30s
2. **Sync Processor**: Process bi-directional sync events
3. **ADHD Monitor**: Enforce breaks, energy matching
4. **Automation Engine**: Implicit workflow triggers
5. **Progress Correlator**: Cross-system progress tracking

---

## Leantime JSON-RPC API Methods

Based on the implementation, these methods are likely used:

### Projects
- `leantime.rpc.projects.getAllProjects` - List all projects
- `leantime.rpc.projects.getProject` - Get single project
- `leantime.rpc.projects.createProject` - Create project
- `leantime.rpc.projects.updateProject` - Update project

### Tasks
- `leantime.rpc.tasks.getAllTasks` - List all tasks (likely used in poller)
- `leantime.rpc.tasks.getTask` - Get single task
- `leantime.rpc.tasks.createTask` - Create task
- `leantime.rpc.tasks.updateTask` - Update task
- `leantime.rpc.tasks.deleteTask` - Delete task

### Sprints
- `leantime.rpc.sprints.getAllSprints` - List sprints
- `leantime.rpc.sprints.createSprint` - Create sprint

**Note**: These are inferred from common Leantime usage. Actual methods need verification against Leantime documentation.

---

## ADHD Optimization Features

### Configuration (lines 140-147):
```python
self.adhd_config = {
    "max_concurrent_tasks": 3,           # Limit parallel work
    "break_enforcement": True,            # Enforce break reminders
    "context_switch_penalty": 0.3,       # Penalty for task switching
    "energy_level_matching": True,       # Match tasks to energy
    "implicit_progress_tracking": True   # Auto-track progress
}
```

### ADHD Monitor Worker
- Monitors task complexity and cognitive load
- Enforces 25-minute break intervals
- Matches tasks to user energy levels
- Prevents hyperfocus burnout

---

## Architecture 3.0 Integration Requirements

### What's Already Built ✅
- Leantime API client (aiohttp-based)
- JSON-RPC 2.0 protocol handling
- Polling mechanism (30s intervals)
- Task synchronization logic
- ADHD optimization features
- Error handling and backoff

### What Needs Updating for Arch 3.0 🔄

#### 1. ConPort Integration
**Current**: Direct task storage in `orchestrated_tasks` dict
**Needed**: ConPort as authoritative storage

**Changes**:
```python
# OLD (current implementation):
self.orchestrated_tasks[task_id] = task

# NEW (Architecture 3.0):
await self._publish_to_conport(task)
```

#### 2. Event-Driven Architecture
**Current**: Direct method calls
**Needed**: DopeconBridge pub/sub

**Changes**:
```python
# OLD:
await self._process_leantime_task_update(leantime_task)

# NEW:
await self.dopecon_bridge.publish_event({
    "type": "leantime.task.updated",
    "source": "task-orchestrator",
    "data": leantime_task
})
```

#### 3. ConPort → Leantime Sync
**Current**: Leantime → Orchestrator only (one-way)
**Needed**: Bidirectional sync via ConPort

**New Flow**:
```
ConPort task created
  → DopeconBridge event
    → Task-Orchestrator receives
      → Sync to Leantime
        → Leantime task created
          → Poller detects (no action - already synced)
```

#### 4. Authority Boundaries
**Current**: Task-Orchestrator stores tasks
**Needed**: ConPort stores, Task-Orchestrator analyzes only

**Changes**:
- Remove `self.orchestrated_tasks` storage
- Query ConPort for task data
- Store analysis results in ConPort (via DopeconBridge)

---

## Phase 2 Implementation Plan

### Phase 2.1: ConPort Event Subscription (4h)

**Goal**: Task-Orchestrator listens to ConPort events

**Tasks**:
1. Create ConPort event subscriber
2. Map ConPort `progress_entry` events to OrchestrationTask
3. Validate event schema

**Code Changes**:
```python
async def _subscribe_to_conport_events(self):
    """Subscribe to ConPort task events via DopeconBridge."""
    await self.dopecon_bridge.subscribe(
        event_type="conport.progress.created",
        handler=self._handle_conport_task_created
    )
    await self.dopecon_bridge.subscribe(
        event_type="conport.progress.updated",
        handler=self._handle_conport_task_updated
    )
```

### Phase 2.2: Leantime Sync Adapter (8h)

**Goal**: Sync ConPort tasks to Leantime

**Tasks**:
1. Create `LeanTimeSync Adapter` class
2. Map ConPort schema → Leantime schema
3. Implement create/update/delete operations
4. Handle multi-project workspace mapping

**Code Changes**:
```python
class LeantimeSyncAdapter:
    """Sync ConPort tasks to Leantime."""

    async def sync_task_to_leantime(
        self,
        conport_task: Dict[str, Any],
        leantime_project_id: int
    ) -> int:
        """Sync single ConPort task to Leantime.

        Returns:
            Leantime task ID
        """
        # Map ConPort progress_entry to Leantime task schema
        leantime_task = self._map_conport_to_leantime(conport_task)

        # Create or update in Leantime
        if leantime_task.get("leantime_id"):
            return await self._update_leantime_task(leantime_task)
        else:
            return await self._create_leantime_task(leantime_task, leantime_project_id)
```

### Phase 2.3: Leantime → ConPort Updates (6h)

**Goal**: Flow Leantime updates through ConPort

**Tasks**:
1. Modify poller to publish to DopeconBridge (not direct storage)
2. Create ConPort update handler
3. Validate authority boundaries (Leantime → ConPort only, not direct)

**Code Changes**:
```python
async def _process_leantime_task_update(self, leantime_task: Dict) -> None:
    """Process Leantime task update and flow through ConPort."""

    # Map Leantime schema → ConPort schema
    conport_update = self._map_leantime_to_conport(leantime_task)

    # Publish to DopeconBridge (ConPort will handle storage)
    await self.dopecon_bridge.publish_event({
        "type": "leantime.task.updated",
        "source": "task-orchestrator",
        "target": "conport",
        "data": conport_update
    })

    # ConPort will:
    # 1. Validate authority (Leantime allowed to update status)
    # 2. Update progress_entry
    # 3. Publish "conport.progress.updated" event
    # 4. Task-Orchestrator receives and re-analyzes dependencies
```

### Phase 2.4: Multi-Project Configuration (4h)

**Goal**: Configure Leantime for multiple projects

**Tasks**:
1. Create workspace → Leantime project mapping
2. Configure project-level dashboards
3. Test cross-project workflows

**Configuration**:
```python
workspace_mapping = {
    "/Users/hue/code/dopemux-mvp": {
        "leantime_project_id": 1,
        "project_name": "Dopemux MVP"
    },
    "/Users/hue/code/project-2": {
        "leantime_project_id": 2,
        "project_name": "Project 2"
    }
}
```

### Phase 2.5: Integration Testing (2h)

**Test Scenarios**:
1. Create task in ConPort → appears in Leantime
2. Update status in Leantime → updates ConPort
3. Multi-project isolation (project 1 tasks don't leak to project 2)
4. Sync latency < 60 seconds
5. Error handling (Leantime down, network errors)

---

## Schema Mapping

### ConPort → Leantime

```python
def _map_conport_to_leantime(conport_task: Dict) -> Dict:
    """Map ConPort progress_entry to Leantime task schema."""
    return {
        "title": conport_task["description"].split("|")[0].strip(),
        "description": conport_task["description"],
        "status": _map_status_to_leantime(conport_task["status"]),
        "priority": _infer_priority(conport_task),
        "tags": conport_task.get("tags", []),
        "customFields": {
            "complexity": conport_task.get("complexity_score"),
            "cognitive_load": conport_task.get("cognitive_load"),
            "energy_required": conport_task.get("energy_required")
        }
    }

def _map_status_to_leantime(conport_status: str) -> int:
    """Map ConPort status to Leantime status ID."""
    status_map = {
        "TODO": 3,
        "IN_PROGRESS": 2,
        "DONE": 4,
        "BLOCKED": 1
    }
    return status_map.get(conport_status, 3)
```

### Leantime → ConPort

```python
def _map_leantime_to_conport(leantime_task: Dict) -> Dict:
    """Map Leantime task to ConPort progress_entry update."""
    return {
        "id": _get_conport_id_from_leantime(leantime_task["id"]),
        "status": _map_status_from_leantime(leantime_task["status"]),
        "description": leantime_task["description"],
        "leantime_metadata": {
            "leantime_id": leantime_task["id"],
            "last_synced": datetime.now().isoformat()
        }
    }

def _map_status_from_leantime(leantime_status: int) -> str:
    """Map Leantime status ID to ConPort status."""
    status_map = {
        1: "BLOCKED",
        2: "IN_PROGRESS",
        3: "TODO",
        4: "DONE"
    }
    return status_map.get(leantime_status, "TODO")
```

---

## Configuration Requirements

### Environment Variables

```bash
# Leantime Connection
LEANTIME_URL=https://leantime.example.com
LEANTIME_TOKEN=your_bearer_token_here

# Redis Coordination
REDIS_URL=redis://localhost:6379

# Workspace
WORKSPACE_ID=/Users/hue/code/dopemux-mvp

# Sync Configuration
LEANTIME_POLL_INTERVAL=30  # seconds
LEANTIME_SYNC_BATCH_SIZE=50
LEANTIME_TIMEOUT=30  # seconds
```

### Leantime Setup

**Required**:
1. Leantime instance (self-hosted or cloud)
2. API access enabled
3. Bearer token generated
4. Projects created for each workspace

**Recommended**:
- Enable webhooks (if available) to reduce polling
- Configure custom fields for ADHD metadata
- Set up project templates for new workspaces

---

## Risk Mitigation

### Risk: Leantime API Rate Limiting

**Mitigation**:
- 30-second polling (2 requests/minute max)
- Batch operations where possible
- Redis caching to reduce API calls
- Exponential backoff on errors

### Risk: Sync Conflicts (Concurrent Updates)

**Mitigation**:
- Last-write-wins strategy (Leantime → ConPort)
- Conflict detection via `last_synced` timestamp
- Log conflicts to ConPort for manual resolution
- ADHD-friendly conflict UI (defer to user, don't block)

### Risk: Network Failures

**Mitigation**:
- Queue sync events in Redis (persist across restarts)
- Retry failed syncs with exponential backoff
- Graceful degradation (ConPort continues if Leantime down)
- Health check endpoint for monitoring

### Risk: Schema Drift

**Mitigation**:
- Version event schemas
- Validate incoming data against schemas
- Migration scripts for schema changes
- Comprehensive integration tests

---

## Testing Strategy

### Unit Tests
- Schema mapping functions
- Status code conversions
- Event publishing/subscribing
- Error handling

### Integration Tests
- ConPort → Leantime sync flow
- Leantime → ConPort update flow
- Multi-project isolation
- Conflict resolution

### End-to-End Tests
1. Create task in ConPort
2. Verify appears in Leantime (< 60s)
3. Update status in Leantime
4. Verify updates ConPort (< 60s)
5. Verify Task-Orchestrator re-analyzes dependencies

### Load Tests
- 100 tasks created in ConPort simultaneously
- Measure sync latency
- Validate no data loss
- Check memory/CPU usage

---

## Monitoring & Observability

### Metrics to Track
- Sync latency (P50, P95, P99)
- Leantime API response time
- Sync failure rate
- Conflict rate
- Event queue depth

### Alerts
- Leantime API down (> 5 consecutive failures)
- Sync latency > 120 seconds
- Event queue depth > 1000
- Conflict rate > 5% of syncs

### Logging
- All sync events (INFO level)
- Sync failures (ERROR level)
- Conflicts detected (WARN level)
- Performance metrics (DEBUG level)

---

## Next Steps

1. ✅ **Research Complete** - Existing implementation documented
2. **Verify Leantime API** - Confirm JSON-RPC methods match implementation
3. **Update for Arch 3.0** - Implement 5 phases above (24 hours total)
4. **Test End-to-End** - Validate full sync flow
5. **Deploy Phase 2** - Leantime visualization live

---

## References

- **Implementation**: `services/task-orchestrator/enhanced_orchestrator.py`
- **ADR-207**: Architecture 3.0 main document
- **Leantime Docs**: https://docs.leantime.io/api (to verify JSON-RPC methods)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
**Status**: Research Complete - Ready for Phase 2 Implementation
