---
id: PM_INV_01_TASK_SCHEMA_ANALYSIS
title: Task Schema Analysis (PM-INV-01)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-02-18'
prelude: Evidence-based analysis of task schemas across 3 PM systems
---
# PM-INV-01: Task Schema Deep-Dive

**Investigation**: GAP-1.1 (taskmaster) + GAP-1.2 (CLI TaskRecord)
**Status**: ✅ COMPLETE
**Analysis Date**: 2026-02-11

---

## Executive Summary

**Finding**: Three completely incompatible task models with ZERO overlap in field names or storage mechanisms.

| System            | Task Object                        | Storage                | ConPort Sync | Fields    | States   |
| ----------------- | ---------------------------------- | ---------------------- | ------------ | --------- | -------- |
| task-orchestrator | `OrchestrationTask`                | ConPort progress_entry | ✅ Yes        | 21 fields | 7 states |
| taskmaster        | **Implicit** (DopeconBridge proxy) | ConPort progress_entry | ✅ Yes        | ~8 fields | Unknown  |
| dopemux CLI       | `TaskRecord`                       | Filesystem JSON        | ❌ No         | 9 fields  | 3 states |

**Critical Gap**: No shared schema, no synchronization mechanism between systems.

---

## System 1: task-orchestrator - OrchestrationTask

**Location**: `services/task-orchestrator/task_orchestrator/models.py:34-62`

### Schema Definition

```python
@dataclass
class OrchestrationTask:
    """Enhanced task representation for orchestration."""
    # Core identifiers
    id: str
    leantime_id: Optional[int] = None
    conport_id: Optional[int] = None

    # Task metadata
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    complexity_score: float = 0.5
    estimated_minutes: int = 25
    assigned_agent: Optional[AgentType] = None

    # ADHD-specific fields
    energy_required: str = "medium"  # low, medium, high
    cognitive_load: float = 0.5  # 0.0-1.0
    context_switches_allowed: int = 2
    break_frequency_minutes: int = 25

    # Orchestration metadata
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    agent_assignments: Dict[str, str] = field(default_factory=dict)
    progress_checkpoints: List[Dict] = field(default_factory=list)

    # Sync tracking
    last_synced: Optional[datetime] = None
    sync_conflicts: List[str] = field(default_factory=list)
```

### Status Enum (7 states)

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    NEEDS_BREAK = "needs_break"      # ADHD accommodation
    CONTEXT_SWITCH = "context_switch" # ADHD accommodation
    PAUSED = "paused"
```

### Storage Mechanism

- **Primary**: ConPort `progress_entry` via MCP
- **Secondary**: Leantime (opt-in sync via `leantime-synced` tag)
- **Adapter**: `app/adapters/conport_adapter.py:145`

### ConPort Integration

✅ **Full bidirectional sync**
- Creates `progress_entry` on task create
- Updates on status changes
- Links to decisions via `linked_item_id`
- Maps via `schema_mapping.py:325-330`

**Evidence**: `enhanced_orchestrator.py:2106-2112`, `conport_adapter.py:145`

---

## System 2: taskmaster - Implicit Schema

**Location**: `services/taskmaster/bridge_adapter.py`

### Schema Definition (Implicit)

**No explicit dataclass** - schema constructed in `create_task()`:

```python
async def create_task(
    title: str,
    description: str,
    priority: int = 3,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result = await self.client.create_progress_entry(
        description=f"{title}: {description}",
        status="TODO",
        metadata={
            "taskmaster_task": True,  # Filter flag
            "priority": priority,
            "tags": tags or [],
            "title": title,
            **(metadata or {}),
        },
        workspace_id=self.workspace_id,
    )
```

### Inferred Schema

| Field          | Type      | Source                    | Notes                     |
| -------------- | --------- | ------------------------- | ------------------------- |
| `id`           | str       | ConPort auto-generated    | Progress entry ID         |
| `title`        | str       | User-provided             | Stored in metadata        |
| `description`  | str       | User-provided             | ConPort description field |
| `status`       | str       | Hardcoded "TODO"          | Updated via events        |
| `priority`     | int       | User-provided (default 3) | 1-5 scale                 |
| `tags`         | List[str] | User-provided             | For categorization        |
| `metadata`     | Dict      | User-provided             | Extensible                |
| `workspace_id` | str       | Environment               | Multi-tenant key          |

### Status Handling

**No explicit enum** - Status managed via:
- Create: hardcoded `"TODO"`
- Update: via `update_task_status(task_id, new_status)` → emits event only
- **Critical**: Status update does NOT call ConPort API, only emits EventBus event

```python
async def update_task_status(task_id: str, new_status: str) -> bool:
    # NOTE: Does not update ConPort, only emits event
    await self.client.publish_event(
        event_type="taskmaster.task.status_updated",
        data={"task_id": task_id, "new_status": new_status},
        source="taskmaster",
    )
```

### Storage Mechanism

- **Primary**: ConPort `progress_entry` via DopeconBridge
- **Filtered by**: `metadata.taskmaster_task = True`
- **Adapter**: `bridge_adapter.py:28`

### ConPort Integration

⚠️ **Partial integration**
- ✅ Creates `progress_entry` on task create
- ❌ Status updates via EventBus only (no ConPort API call)
- ❌ No decision linkage
- ⚠️ Relies on EventBus → working-memory-assistant → Chronicle path

**Evidence**: `bridge_adapter.py:67-96`, `bridge_adapter.py:122-146`

**Critical Gap**: `update_task_status()` does not update ConPort directly, relies on event propagation.

---

## System 3: dopemux CLI - TaskRecord

**Location**: `src/dopemux/adhd/task_decomposer.py:40-78`

### Schema Definition

```python
@dataclass
class TaskRecord:
    """Persisted representation of a task."""
    id: str
    description: str
    estimated_duration: int
    priority: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    created_at: str = field(default_factory=_now)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
```

### Status Enum (3 states)

```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    # Missing: FAILED (referenced in comment but not in enum)
```

### Storage Mechanism

- **Primary**: Filesystem JSON (`<workspace>/.dopemux/tasks/tasks.json`)
- **Format**: Dict[str, TaskRecord] serialized to JSON
- **No database integration**

### ConPort Integration

❌ **No integration**
- No ConPort imports
- No MCP client usage
- No progress_entry creation
- Tasks completely isolated from canonical PM system

**Evidence**: `task_decomposer.py:81-118`

**Critical Gap**: CLI tasks are orphaned - not visible to task-orchestrator or ConPort.

---

## Schema Comparison Matrix

| Feature                | task-orchestrator  | taskmaster    | dopemux CLI          |
| ---------------------- | ------------------ | ------------- | -------------------- |
| **Explicit dataclass** | ✅ Yes              | ❌ No          | ✅ Yes                |
| **ConPort sync**       | ✅ Bidirectional    | ⚠️ Create only | ❌ None               |
| **Storage**            | ConPort + Leantime | ConPort       | Filesystem           |
| **Status states**      | 7                  | Unknown       | 3                    |
| **ADHD fields**        | ✅ Yes (4 fields)   | ❌ No          | ⚠️ Partial (duration) |
| **Dependencies**       | ✅ Yes              | ❌ No          | ❌ No                 |
| **Decision links**     | ✅ Yes              | ❌ No          | ❌ No                 |
| **Agent assignment**   | ✅ Yes              | ❌ No          | ❌ No                 |
| **Complexity scoring** | ✅ Yes              | ❌ No          | ❌ No                 |
| **Leantime sync**      | ✅ Opt-in           | ❌ No          | ❌ No                 |
| **Multi-tenant**       | ✅ Yes              | ✅ Yes         | ❌ No                 |

---

## Field Name Conflicts

### Status Field

| System            | Field Name | Type            | Values                    |
| ----------------- | ---------- | --------------- | ------------------------- |
| task-orchestrator | `status`   | TaskStatus enum | 7 states                  |
| taskmaster        | `status`   | str             | Free-form (no validation) |
| CLI               | `status`   | TaskStatus enum | 3 states                  |

**Incompatibility**: Different enums, different value sets.

### Priority Field

| System            | Field Name | Type | Scale                   |
| ----------------- | ---------- | ---- | ----------------------- |
| task-orchestrator | `priority` | int  | 1-?                     |
| taskmaster        | `priority` | int  | 1-5 (default 3)         |
| CLI               | `priority` | str  | "low", "medium", "high" |

**Incompatibility**: int vs str, different scales.

### Identifier Fields

| System            | Primary Key         | ConPort Link       | External Link       |
| ----------------- | ------------------- | ------------------ | ------------------- |
| task-orchestrator | `id` (str)          \| `conport_id` (int) \| `leantime_id` (int) |
| taskmaster        | `id` (from ConPort) | implicit           | none                |
| CLI               | `id` (str, UUID)    | none               | none                |

**Incompatibility**: No shared ID space.

---

## State Transition Comparison

### task-orchestrator (7 states)

```
PENDING → IN_PROGRESS → COMPLETED
           ↓
        NEEDS_BREAK → IN_PROGRESS
           ↓
     CONTEXT_SWITCH → IN_PROGRESS
           ↓
         PAUSED → IN_PROGRESS
           ↓
        BLOCKED → IN_PROGRESS
```

### taskmaster (unknown)

- No explicit state machine
- Status updated via events only
- No validation of transitions

### CLI (3 states)

```
PENDING → IN_PROGRESS → COMPLETED
```

**Incompatibility**: Cannot map 7-state to 3-state without loss of information.

---

## Storage Format Comparison

### task-orchestrator

```json
{
  "id": "task_123",
  "conport_id": 456,
  "title": "Implement feature X",
  "status": "in_progress",
  "priority": 2,
  "complexity_score": 0.7,
  "energy_required": "high",
  "cognitive_load": 0.8,
  "dependencies": ["task_100", "task_101"]
}
```

### taskmaster

```json
{
  "id": 789,
  "description": "Implement feature X: detailed description",
  "status": "TODO",
  "metadata": {
    "taskmaster_task": true,
    "title": "Implement feature X",
    "priority": 3,
    "tags": ["feature", "backend"]
  }
}
```

### CLI

```json
{
  "task_abc": {
    "id": "task_abc",
    "description": "Implement feature X",
    "estimated_duration": 25,
    "priority": "medium",
    "status": "pending",
    "progress": 0.0,
    "created_at": "2026-02-11T10:00:00Z"
  }
}
```

**Incompatibility**: No shared fields except `description` (with different semantics).

---

## ConPort Sync Mechanisms

### task-orchestrator → ConPort

**Adapter**: `app/adapters/conport_adapter.py`

```python
async def create_task_in_conport(self, task: OrchestrationTask) -> int:
    result = await self.conport_client.log_progress(
        workspace_id=self.workspace_id,
        status=map_task_status_to_conport(task.status),
        description=f"{task.title}: {task.description}",
        linked_item_type="decision" if task.decision_link else None,
        linked_item_id=task.decision_link,
    )
    return result["id"]
```

**Sync Events**: `enhanced_orchestrator.py:2127-2201`

### taskmaster → ConPort

**Adapter**: `bridge_adapter.py`

```python
async def create_task(title, description, priority, tags, metadata):
    result = await self.client.create_progress_entry(
        description=f"{title}: {description}",
        status="TODO",
        metadata={"taskmaster_task": True, ...},
        workspace_id=self.workspace_id,
    )
```

**No sync mechanism for updates** - relies on EventBus propagation.

### CLI → ConPort

**Adapter**: ❌ None

---

## Unification Challenges

### Challenge 1: Incompatible Status Models

**Problem**: 7 states ≠ 3 states ≠ free-form strings

**Solutions**:
1. **Option A**: Canonical 7-state model (task-orchestrator wins)
- Pros: Most complete, ADHD-aware
- Cons: CLI needs major refactor
1. **Option B**: Minimal 3-state + metadata flags
- Pros: Simple, backwards-compatible
- Cons: Loses ADHD states
1. **Option C**: Extensible state + substates
- Pros: Flexible, supports all systems
- Cons: Complex mapping logic

### Challenge 2: Priority Type Mismatch

**Problem**: int (1-5) vs str ("low"/"medium"/"high")

**Solution**: Canonical int scale with string mapping:
```python
PRIORITY_MAP = {
    "low": 1,
    "medium": 3,
    "high": 5
}
```

### Challenge 3: Storage Divergence

**Problem**: ConPort vs Filesystem vs hybrid

**Solution**: ConPort as single source of truth:
- task-orchestrator: ✅ Already using ConPort
- taskmaster: ✅ Using ConPort, needs update sync fix
- CLI: ❌ Needs full refactor to use ConPort MCP client

### Challenge 4: ADHD Field Support

**Problem**: task-orchestrator has ADHD fields, others don't

**Solution**: Optional ADHD metadata in unified schema:
```python
adhd_metadata: Optional[ADHDMetadata] = None  # Backwards-compatible
```

---

## Migration Path Analysis

### Path 1: Extend taskmaster + CLI to match task-orchestrator

**Effort**: 40-60 hours
- taskmaster: Add ADHD fields, fix update sync (8-12 hours)
- CLI: Full refactor to use ConPort (20-30 hours)
- Integration tests: (12-18 hours)

**Pros**: Preserves rich task-orchestrator schema
**Cons**: Large breaking change for CLI users

### Path 2: Minimal unified schema

**Effort**: 20-30 hours
- Define minimal schema (4-6 hours)
- Adapter layer for each system (10-15 hours)
- Integration tests (6-9 hours)

**Pros**: Backwards-compatible, minimal changes
**Cons**: Lowest common denominator, loses features

### Path 3: ConPort-first with system-specific extensions

**Effort**: 30-40 hours
- Core ConPort schema (6-8 hours)
- System-specific metadata fields (12-16 hours)
- Bidirectional sync adapters (12-16 hours)

**Pros**: Single source of truth, extensible
**Cons**: Moderate complexity

---

## Recommendations

### Immediate (Week 2)

1. **Fix taskmaster update sync** (HIGH priority)
- `update_task_status()` must call ConPort API, not just emit event
- Effort: 2-3 hours
- Blocker: Current implementation creates orphaned state

1. **Add CLI ConPort client** (HIGH priority)
- Wire ConPort MCP client to TaskDecomposer
- Dual-write: filesystem + ConPort for migration period
- Effort: 4-6 hours

1. **Design unified schema** (BLOCKING)
- Propose canonical schema (PM-INV-03)
- Get stakeholder approval
- Effort: 6-8 hours

### Phase 1 (Week 3-4)

1. **Implement unified schema**
- Create shared schema module
- Adapter pattern for system-specific extensions
- Effort: 12-16 hours

1. **Migration utilities**
- CLI tasks → ConPort import script
- Validation tools
- Effort: 6-8 hours

1. **Integration tests**
- Cross-system task operations
- State transition validation
- Effort: 12-18 hours

---

## Success Criteria

**Phase 0 Complete When**:
- ✅ All 3 schemas documented (DONE)
- ✅ Incompatibilities identified (DONE)
- ✅ Migration paths analyzed (DONE)

**Phase 1 Complete When**:
- ✅ Unified schema designed and approved
- ✅ taskmaster update sync fixed
- ✅ CLI ConPort integration working
- ✅ All tasks visible in ConPort
- ✅ Cross-system tests passing

---

## Appendix: Code Evidence

### task-orchestrator Schema

**File**: `services/task-orchestrator/task_orchestrator/models.py`
**Lines**: 34-62
**Commit**: c4ae4a356

### taskmaster Implicit Schema

**File**: `services/taskmaster/bridge_adapter.py`
**Lines**: 57-96 (create), 122-146 (update)
**Commit**: c4ae4a356

### CLI TaskRecord Schema

**File**: `src/dopemux/adhd/task_decomposer.py`
**Lines**: 40-78
**Commit**: c4ae4a356

### ConPort Integration

**task-orchestrator adapter**: `services/task-orchestrator/app/adapters/conport_adapter.py:145`
**taskmaster adapter**: `services/taskmaster/bridge_adapter.py:67-96`
**CLI adapter**: ❌ None (missing)

---

**Analysis Complete**: 2026-02-11
**Next**: PM-INV-03 (Unified schema design)
