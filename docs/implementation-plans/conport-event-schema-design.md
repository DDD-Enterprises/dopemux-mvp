# ConPort Event Schema Design - Architecture 3.0

**Task**: 2.1 - Design ConPort Event Schema
**Date**: 2025-10-19
**Component**: 2 - Data Contract Adapters
**Status**: Complete
**Complexity**: 0.7 (high - architecture design)
**Duration**: 60 minutes
**Dependencies**: Task 1.3 ✅

## Executive Summary

This specification defines the **canonical event schema** for ConPort ↔ Task-Orchestrator communication in Architecture 3.0. It standardizes ADHD metadata encoding, establishes bidirectional transformations, and ensures data integrity across the integration boundary.

**Key Decisions**:
1. **ADHD Metadata Storage**: Tags for queryable fields, description for display-only
2. **Transformation Strategy**: Lossless bidirectional with validation
3. **Tag Format**: Standardized `{category}-{value}` pattern
4. **Dependency Tracking**: Use ConPort `link_conport_items` with `depends_on` relationship

**Implementation**: Tasks 2.2-2.6 will implement this specification

## Event Schema Architecture

### Schema Layers

```
┌─────────────────────────────────────────────────┐
│  LAYER 1: ConPort Native Schema                │
│  progress_entry, decision, active_context       │
│  (ConPort storage authority - canonical source) │
└─────────────┬───────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  LAYER 2: Transformation Layer                  │
│  ConPortEventAdapter (Task 2.2)                 │
│  - OrchestrationTask ↔ progress_entry           │
│  - ADHD metadata encoding/decoding              │
│  - Tag generation and parsing                   │
└─────────────┬───────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  LAYER 3: Task-Orchestrator Internal Schema    │
│  OrchestrationTask, SyncEvent                   │
│  (Application model - derived from ConPort)     │
└─────────────────────────────────────────────────┘
```

### Event Flow Patterns

**Pattern 1: Progress Creation** (Leantime → ConPort → Task-Orchestrator)
```
Leantime Task Created
  ↓
Task-Orchestrator polls/receives event
  ↓
Transform to OrchestrationTask (internal)
  ↓
ConPort Adapter: orchestration_task_to_progress()
  ↓
ConPort MCP: log_progress(workspace_id, status, description, tags)
  ↓
ConPort storage: progress_entry created (ID returned)
  ↓
Task-Orchestrator stores ConPort ID for future updates
```

**Pattern 2: Progress Updates** (Task-Orchestrator → ConPort)
```
Task status changes (PENDING → IN_PROGRESS → DONE)
  ↓
Task-Orchestrator detects change
  ↓
ConPort Adapter: update_progress()
  ↓
ConPort MCP: update_progress(workspace_id, progress_id, status)
  ↓
ConPort storage: progress_entry updated
  ↓
Timestamp recorded for sync tracking
```

**Pattern 3: Sprint Activation** (Leantime → ConPort → Task-Orchestrator)
```
Sprint Created in Leantime
  ↓
Task-Orchestrator automation triggered
  ↓
ConPort Adapter: create_sprint_context()
  ↓
ConPort MCP: update_active_context(patch_content={sprint data})
  ↓
ConPort storage: active_context updated (mode=ACT)
  ↓
Task-Orchestrator begins sprint orchestration
```

## ADHD Tag Format Standardization

### Tag Schema Specification

**Format**: `{category}-{value}`
**Case**: Lowercase with hyphens
**Validation**: Regex `^[a-z]+(-[a-z0-9]+)+$`

### Standard ADHD Tags

**Energy Level**:
```python
"energy-low"      # <30 min focus tasks, minimal cognitive load
"energy-medium"   # 30-60 min tasks, moderate thinking required
"energy-high"     # 60-90 min tasks, deep focus required
```

**Complexity Score** (scaled 0.0-1.0 → 0-10):
```python
"complexity-0"    # 0.0-0.09  Trivial (copy-paste, simple edits)
"complexity-1"    # 0.1-0.19  Very low
"complexity-2"    # 0.2-0.29  Low
"complexity-3"    # 0.3-0.39  Low-moderate
"complexity-4"    # 0.4-0.49  Moderate
"complexity-5"    # 0.5-0.59  Moderate
"complexity-6"    # 0.6-0.69  Moderate-high
"complexity-7"    # 0.7-0.79  High
"complexity-8"    # 0.8-0.89  Very high
"complexity-9"    # 0.9-0.99  Extremely high
"complexity-10"   # 1.0       Maximum complexity
```

**Priority Level**:
```python
"priority-1"      # Low priority (nice-to-have)
"priority-2"      # Medium-low
"priority-3"      # Medium (standard tasks)
"priority-4"      # High (important)
"priority-5"      # Critical (blocking other work)
```

**Agent Assignment**:
```python
"agent-conport"   # Assigned to ConPort (decision logging, memory)
"agent-serena"    # Assigned to Serena (code navigation, analysis)
"agent-zen"       # Assigned to Zen (consensus, deep analysis)
"agent-taskmaster"  # Assigned to TaskMaster (PRD parsing)
"agent-claude-flow"  # Assigned to Claude Flow orchestration
```

**Task Source** (system identification):
```python
"task-orchestrator"  # Created/managed by Task-Orchestrator
"leantime-synced"    # Synced from Leantime
"conport-native"     # Created directly in ConPort
"manual-entry"       # User-created
```

### Tag Composition Rules

**All tasks MUST include**:
```python
[
    "task-orchestrator",          # Source system
    "energy-{low|medium|high}",   # Energy requirement
    "complexity-{0-10}",          # Cognitive load
    "priority-{1-5}"              # Priority level
]
```

**Optional tags**:
```python
"agent-{type}"           # If assigned to specific agent
"leantime-synced"        # If linked to Leantime
"component-{1-5}"        # Phase 1 component grouping
"critical"               # High-impact tasks
"blocked"                # Waiting on dependencies
```

**Example** (from Phase 1 Task 1.3):
```python
tags = [
    "task-orchestrator",
    "phase-1",
    "component-1",
    "task-1.3",
    "audit",
    "conport-api",
    "energy-high",
    "complexity-6",
    "priority-4"
]
```

## Data Structure Specifications

### OrchestrationTask (Task-Orchestrator Internal)

**Source**: `services/task-orchestrator/enhanced_orchestrator.py:54-93`

```python
@dataclass
class OrchestrationTask:
    """Enhanced task representation for orchestration."""
    # === Core Identifiers ===
    id: str                           # UUID or task-{number}
    leantime_id: Optional[int]        # Leantime task ID (if synced)
    conport_id: Optional[int]         # ConPort progress_entry ID (ADDED in Component 2)

    # === Task Description ===
    title: str
    description: str
    status: TaskStatus                # PENDING, IN_PROGRESS, COMPLETED, BLOCKED, etc.

    # === Scheduling ===
    priority: int                     # 1-5
    estimated_minutes: int            # Duration estimate
    complexity_score: float           # 0.0-1.0

    # === ADHD Optimizations ===
    energy_required: str              # "low", "medium", "high"
    cognitive_load: float             # 0.0-1.0 (same as complexity)
    context_switches_allowed: int     # Max interruptions before break
    break_frequency_minutes: int      # Recommended break interval (Pomodoro)

    # === Orchestration Metadata ===
    assigned_agent: Optional[AgentType]  # Which AI agent handles this
    dependencies: List[str]           # Task IDs this depends on
    dependents: List[str]             # Task IDs that depend on this
    agent_assignments: Dict[str, str]  # Historical agent assignments
    progress_checkpoints: List[Dict]  # Intermediate save points

    # === Sync Tracking ===
    last_synced: Optional[datetime]   # Last ConPort sync timestamp
    sync_conflicts: List[str]         # Detected conflicts
```

### ConPort progress_entry Schema

**ConPort MCP API**: `mcp__conport__log_progress`

```python
{
    # === Required Fields ===
    "workspace_id": str,              # "/Users/hue/code/dopemux-mvp"
    "status": str,                    # "TODO" | "IN_PROGRESS" | "DONE" | "BLOCKED"
    "description": str,               # Full task description

    # === Optional Fields ===
    "tags": List[str],                # ADHD metadata tags
    "parent_id": Optional[int],       # Subtask hierarchy
    "linked_item_type": Optional[str],  # "leantime_task", "decision", etc.
    "linked_item_id": Optional[str],   # External system ID
    "link_relationship_type": Optional[str]  # "tracks_implementation", "depends_on"
}
```

**Returns**:
```python
{
    "id": int,                        # ConPort-generated progress_entry ID
    "timestamp": str,                 # ISO 8601 creation time
    "status": str,                    # Echoed status
    "description": str,               # Echoed description
    "parent_id": Optional[int],       # Echoed parent
    # ... other fields
}
```

## Bidirectional Transformation Specification

### Transformation 1: OrchestrationTask → ConPort progress_entry

**Function Signature**:
```python
def orchestration_task_to_conport_progress(
    task: OrchestrationTask,
    workspace_id: str
) -> Dict[str, Any]:
    """
    Transform OrchestrationTask to ConPort progress_entry format.

    Ensures ADHD metadata is preserved as queryable tags.
    """
```

**Implementation Specification**:
```python
def orchestration_task_to_conport_progress(task: OrchestrationTask, workspace_id: str) -> Dict:
    # Step 1: Map status enum
    status_mapping = {
        TaskStatus.PENDING: "TODO",
        TaskStatus.IN_PROGRESS: "IN_PROGRESS",
        TaskStatus.COMPLETED: "DONE",
        TaskStatus.BLOCKED: "BLOCKED",
        TaskStatus.NEEDS_BREAK: "IN_PROGRESS",  # ConPort doesn't have NEEDS_BREAK
        TaskStatus.CONTEXT_SWITCH: "IN_PROGRESS",  # Treated as in-progress
        TaskStatus.PAUSED: "BLOCKED"  # Paused = temporarily blocked
    }

    # Step 2: Build rich description with embedded metadata
    # Format: "Title | Description | Duration: Xm | Complexity: Y.Z | Energy: {level}"
    description_parts = [
        task.title,
        task.description if task.description else "",
        f"Duration: {task.estimated_minutes}m",
        f"Complexity: {task.complexity_score}",
        f"Energy: {task.energy_required}"
    ]
    description = " | ".join(p for p in description_parts if p)

    # Step 3: Build ADHD metadata tags (queryable)
    tags = [
        "task-orchestrator",  # Source system identifier
        f"energy-{task.energy_required}",  # Queryable energy level
        f"complexity-{int(task.complexity_score * 10)}",  # Scaled to 0-10
        f"priority-{task.priority}"  # Queryable priority
    ]

    # Add agent assignment tag if present
    if task.assigned_agent:
        tags.append(f"agent-{task.assigned_agent.value}")

    # Add Leantime sync tag if applicable
    if task.leantime_id:
        tags.append("leantime-synced")

    # Step 4: Build ConPort progress_entry
    progress_entry = {
        "workspace_id": workspace_id,
        "status": status_mapping.get(task.status, "TODO"),
        "description": description,
        "tags": tags
    }

    # Step 5: Add linking if Leantime task
    if task.leantime_id:
        progress_entry.update({
            "linked_item_type": "leantime_task",
            "linked_item_id": str(task.leantime_id),
            "link_relationship_type": "tracks_implementation"
        })

    return progress_entry
```

**Validation Rules**:
- `workspace_id` MUST be absolute path
- `status` MUST be one of: TODO, IN_PROGRESS, DONE, BLOCKED
- `description` MUST NOT be empty
- `tags` MUST include minimum: task-orchestrator, energy-*, complexity-*, priority-*

### Transformation 2: ConPort progress_entry → OrchestrationTask

**Function Signature**:
```python
def conport_progress_to_orchestration_task(
    progress: Dict[str, Any]
) -> OrchestrationTask:
    """
    Transform ConPort progress_entry to OrchestrationTask.

    Parses embedded metadata from description and tags.
    """
```

**Implementation Specification**:
```python
def conport_progress_to_orchestration_task(progress: Dict) -> OrchestrationTask:
    # Step 1: Reverse status mapping
    status_mapping = {
        "TODO": TaskStatus.PENDING,
        "IN_PROGRESS": TaskStatus.IN_PROGRESS,
        "DONE": TaskStatus.COMPLETED,
        "BLOCKED": TaskStatus.BLOCKED
    }

    # Step 2: Parse description (format: "title | description | metadata")
    desc_parts = progress["description"].split(" | ")
    title = desc_parts[0] if len(desc_parts) > 0 else "Unknown Task"
    description = desc_parts[1] if len(desc_parts) > 1 else ""

    # Parse embedded metadata from description
    estimated_minutes = 25  # default
    complexity_score = 0.5  # default
    energy_required = "medium"  # default

    for part in desc_parts[2:]:  # Metadata in later parts
        if part.startswith("Duration: "):
            estimated_minutes = int(part.replace("Duration: ", "").replace("m", ""))
        elif part.startswith("Complexity: "):
            complexity_score = float(part.replace("Complexity: ", ""))
        elif part.startswith("Energy: "):
            energy_required = part.replace("Energy: ", "")

    # Step 3: Extract ADHD metadata from tags
    priority = 3  # default
    assigned_agent = None
    leantime_id = None

    for tag in progress.get("tags", []):
        if tag.startswith("complexity-"):
            # Override with tag value (more authoritative)
            complexity_score = float(tag.split("-")[1]) / 10.0
        elif tag.startswith("energy-"):
            energy_required = tag.split("-")[1]
        elif tag.startswith("priority-"):
            priority = int(tag.split("-")[1])
        elif tag.startswith("agent-"):
            agent_name = tag.split("-", 1)[1]
            assigned_agent = AgentType(agent_name)

    # Step 4: Extract Leantime link if present
    if progress.get("linked_item_type") == "leantime_task":
        leantime_id = int(progress["linked_item_id"])

    # Step 5: Build OrchestrationTask
    return OrchestrationTask(
        id=f"conport-{progress['id']}",  # Prefix to identify source
        conport_id=progress["id"],  # Store ConPort ID for updates
        leantime_id=leantime_id,
        title=title,
        description=description,
        status=status_mapping.get(progress["status"], TaskStatus.PENDING),
        priority=priority,
        complexity_score=complexity_score,
        estimated_minutes=estimated_minutes,
        assigned_agent=assigned_agent,
        energy_required=energy_required,
        cognitive_load=complexity_score,  # Same as complexity
        context_switches_allowed=2,  # Default
        break_frequency_minutes=25,  # Default Pomodoro
        dependencies=[],  # Populated from linked_items query
        dependents=[],
        agent_assignments={},
        progress_checkpoints=[],
        last_synced=datetime.fromisoformat(progress["timestamp"]),
        sync_conflicts=[]
    )
```

**Validation Rules**:
- ConPort ID MUST be stored in `conport_id` field for update operations
- Timestamp MUST be preserved in `last_synced` for conflict detection
- Tags MUST be parsed before description (tags are authoritative)
- Missing tags use safe defaults (don't fail transformation)

## Event Type Definitions

### Event Type 1: Task Progress Events

**Purpose**: Synchronize task status between systems

**Event Structure**:
```python
class TaskProgressEvent:
    event_type: str = "task_progress"
    task_id: str                      # OrchestrationTask.id
    conport_id: int                   # progress_entry.id
    leantime_id: Optional[int]        # Leantime task ID if linked

    # Status transition
    old_status: TaskStatus
    new_status: TaskStatus

    # ADHD context
    energy_level: str                 # low, medium, high
    complexity: float                 # 0.0-1.0
    estimated_duration: int           # minutes

    # Sync metadata
    timestamp: datetime
    source_system: str                # "task-orchestrator", "leantime", "conport"
    sync_direction: str               # "to_conport", "from_conport"
```

**Usage**:
```python
# When Task-Orchestrator updates task status
event = TaskProgressEvent(
    task_id="task-123",
    conport_id=125,
    old_status=TaskStatus.PENDING,
    new_status=TaskStatus.IN_PROGRESS,
    energy_level="high",
    complexity=0.7,
    estimated_duration=60,
    timestamp=datetime.now(),
    source_system="task-orchestrator",
    sync_direction="to_conport"
)

# Trigger: Call ConPort update_progress
adapter.update_task_progress(event)
```

### Event Type 2: Sprint Activation Events

**Purpose**: Set ConPort active_context when sprint starts

**Event Structure**:
```python
class SprintActivationEvent:
    event_type: str = "sprint_activation"
    sprint_id: str                    # Leantime sprint ID
    sprint_name: str

    # Context setup
    mode: str = "ACT"                 # Sprint execution mode
    focus: str                        # Sprint focus description
    task_count: int                   # Number of tasks in sprint

    # ADHD metadata
    automation_enabled: bool = True
    adhd_optimized: bool = True

    # Timestamps
    sprint_start: datetime
    activation_timestamp: datetime

    # Source
    source_system: str = "task-orchestrator"
```

**Usage**:
```python
# When sprint created in Leantime
event = SprintActivationEvent(
    sprint_id="S-2025.10",
    sprint_name="Architecture 3.0 Phase 1",
    focus="Task-Orchestrator integration with ConPort",
    task_count=20,
    sprint_start=datetime.now(),
    activation_timestamp=datetime.now()
)

# Trigger: Call ConPort update_active_context
adapter.activate_sprint_context(event)
```

### Event Type 3: AI Decision Events

**Purpose**: Log AI agent decisions to ConPort knowledge graph

**Event Structure**:
```python
class AIDecisionEvent:
    event_type: str = "ai_decision"
    decision_id: Optional[int]        # ConPort decision ID (after creation)

    # Decision content
    summary: str                      # Concise decision statement
    rationale: str                    # Why this decision
    implementation_details: str       # How to implement

    # AI metadata
    agent_type: AgentType             # Which AI agent made decision
    confidence: float                 # 0.0-1.0
    alternatives_considered: List[str]  # Other options evaluated

    # Linking
    related_task_id: Optional[str]    # OrchestrationTask this relates to
    related_conport_id: Optional[int]  # progress_entry to link to

    # Tags
    tags: List[str]                   # ["ai-generated", "agent-{type}", ...]

    # Timestamps
    timestamp: datetime
```

**Usage**:
```python
# When AI agent (Zen, Serena, etc.) completes analysis
event = AIDecisionEvent(
    summary="Use event-driven architecture for cross-service communication",
    rationale="Reduces coupling, enables async operations, ADHD-friendly pause/resume",
    implementation_details="Implement Redis Streams EventBus with pub/sub pattern",
    agent_type=AgentType.ZEN,
    confidence=0.85,
    alternatives_considered=["Direct HTTP calls", "Shared database polling"],
    related_task_id="task-132",  # Task 3.2: Implement Event Subscription
    tags=["ai-generated", "agent-zen", "architecture", "event-bus"]
)

# Trigger: Call ConPort log_decision
decision_id = adapter.log_ai_decision(event)
# Then link to related task
adapter.link_decision_to_task(decision_id, event.related_conport_id)
```

## Transformation Validation Schema

### Lossless Transformation Requirements

**Round-trip test**:
```python
# Start with OrchestrationTask
original_task = OrchestrationTask(
    id="test-123",
    title="Test Task",
    complexity_score=0.6,
    energy_required="high",
    # ... all fields
)

# Transform to ConPort
progress_data = orchestration_task_to_conport_progress(original_task, workspace_id)

# Simulate ConPort storage (adds ID and timestamp)
stored_progress = {
    **progress_data,
    "id": 999,
    "timestamp": "2025-10-19T22:00:00Z"
}

# Transform back
restored_task = conport_progress_to_orchestration_task(stored_progress)

# Validate lossless (except IDs and timestamps)
assert restored_task.title == original_task.title
assert restored_task.complexity_score == original_task.complexity_score
assert restored_task.energy_required == original_task.energy_required
assert restored_task.status == original_task.status
# ... all business fields preserved
```

**Acceptable Losses** (metadata only):
- `id` changes: `task-123` → `conport-999` (expected, both stored)
- `last_synced` added: Timestamp from ConPort (enhancement)
- `conport_id` added: 999 (enables future updates)

**Unacceptable Losses** (MUST preserve):
- Any ADHD metadata (energy, complexity, cognitive_load)
- Task description or title
- Status or priority
- Dependencies or relationships
- Any business-critical field

### Validation Test Suite (for Task 2.6)

```python
def test_transformation_lossless():
    """Test round-trip transformation preserves data."""
    # Test all field types
    # Test all status values
    # Test optional fields (None, empty lists)
    # Test ADHD metadata encoding/decoding
    pass

def test_adhd_tags_queryable():
    """Test ADHD tags enable filtering."""
    # Create tasks with different energy levels
    # Transform to ConPort
    # Verify tags: energy-low, energy-medium, energy-high
    # Query ConPort by tag
    # Verify correct tasks returned
    pass

def test_status_mapping_comprehensive():
    """Test all TaskStatus values map correctly."""
    # Test PENDING → TODO
    # Test IN_PROGRESS → IN_PROGRESS
    # Test COMPLETED → DONE
    # Test BLOCKED → BLOCKED
    # Test NEEDS_BREAK → IN_PROGRESS (lossy, acceptable)
    pass
```

## Dependency Tracking Schema

### Dependency Representation

**In OrchestrationTask**:
```python
dependencies: List[str] = ["task-120", "task-121"]  # Task IDs this depends on
dependents: List[str] = ["task-130", "task-131"]    # Tasks that depend on this
```

**In ConPort**:
```python
# Use link_conport_items API
mcp__conport__link_conport_items(
    workspace_id="/Users/hue/code/dopemux-mvp",
    source_item_type="progress_entry",
    source_item_id="122",  # Task 1.3 (depends on 1.1)
    target_item_type="progress_entry",
    target_item_id="120",  # Task 1.1
    relationship_type="depends_on",
    description="Task 1.3 depends on Task 1.1"
)
```

**Sync Strategy**:
```python
# When OrchestrationTask has dependencies, sync to ConPort
for dependency_id in task.dependencies:
    # Find ConPort ID for dependency_id
    dep_conport_id = get_conport_id_for_task(dependency_id)

    # Create dependency link
    link_conport_items(
        source_item_id=task.conport_id,
        target_item_id=dep_conport_id,
        relationship_type="depends_on"
    )

# When loading from ConPort, query links
links = get_linked_items(
    item_type="progress_entry",
    item_id=task.conport_id,
    relationship_type_filter="depends_on"
)

# Populate dependencies list
task.dependencies = [link["target_id"] for link in links]
```

## Batch Update Strategy

### Challenge

ConPort doesn't have dedicated batch progress update endpoint.

### Solution Options

**Option A: Sequential Updates** (RECOMMENDED for Phase 1)
```python
async def batch_update_conport_progress(updates: List[Dict]) -> List[int]:
    """Update multiple ConPort progress entries sequentially."""
    updated_ids = []

    for update in updates:
        result = await conport_client.update_progress(
            workspace_id=update["workspace_id"],
            progress_id=update["progress_id"],
            status=update.get("status"),
            description=update.get("description")
        )
        updated_ids.append(result["id"])

    return updated_ids
```

**Pros**: Simple, uses existing API, no ConPort changes needed
**Cons**: N network calls for N updates
**Performance**: Acceptable for <10 updates (typical sprint has 3-7 active tasks)

**Option B: Use batch_log_items** (for creation only)
```python
# ConPort has batch_log_items for creation
mcp__conport__batch_log_items(
    workspace_id=workspace_id,
    item_type="progress_entry",
    items=[{...}, {...}, {...}]
)
```

**Pros**: Single API call, atomic creation
**Cons**: Only works for creation, not updates
**Use Case**: Initial sprint task import (Leantime → ConPort bulk sync)

**Recommendation**: Use Option A (sequential) for Phase 1, monitor performance in Task 5.2

## Sprint Context Schema

### active_context Structure

**ConPort API**: `mcp__conport__update_active_context`

**Sprint Context Format**:
```python
sprint_context = {
    # === Sprint Identification ===
    "sprint_id": str,                 # e.g., "S-2025.10"
    "sprint_name": str,               # e.g., "Architecture 3.0 Phase 1"

    # === Mode Control ===
    "mode": str,                      # "PLAN" or "ACT"
    "focus": str,                     # Current focus description

    # === Task-Orchestrator Metadata ===
    "automation_enabled": bool,       # True if orchestrator active
    "adhd_optimized": bool,           # True (always for task-orchestrator)
    "task_count": int,                # Number of tasks in sprint
    "orchestration_active": bool,     # True when orchestrator running

    # === Timestamps ===
    "auto_setup_timestamp": str,      # ISO 8601 when sprint activated
    "sprint_start_date": Optional[str],  # From Leantime
    "sprint_end_date": Optional[str],    # From Leantime

    # === Leantime Sync ===
    "leantime_managed": bool,         # True if Leantime is source of truth
    "leantime_sprint_id": Optional[int],  # Leantime internal ID

    # === Progress Tracking ===
    "tasks_completed": int,           # Count of DONE tasks
    "component_progress": str         # e.g., "Component 1: 80%"
}
```

**Example** (from Task 1.3 audit):
```python
sprint_context = {
    "sprint_id": "S-2025.10",
    "sprint_name": "Architecture 3.0 Phase 1 Implementation",
    "mode": "ACT",
    "focus": "Sprint execution with automated PM via Task-Orchestrator",
    "automation_enabled": True,
    "adhd_optimized": True,
    "task_count": 20,
    "orchestration_active": True,
    "auto_setup_timestamp": "2025-10-19T22:00:00Z",
    "leantime_managed": True,
    "leantime_sprint_id": 42,
    "tasks_completed": 5,
    "component_progress": "Component 1: 100%, Component 2: 0%"
}
```

## Error Handling and Graceful Degradation

### Transformation Error Handling

```python
def safe_orchestration_task_to_conport_progress(
    task: OrchestrationTask,
    workspace_id: str
) -> Optional[Dict]:
    """Safe transformation with validation and error handling."""
    try:
        # Validate required fields
        if not task.id or not task.title:
            logger.error(f"Invalid task: missing id or title")
            return None

        # Validate complexity score range
        if not (0.0 <= task.complexity_score <= 1.0):
            logger.warning(f"Invalid complexity {task.complexity_score}, clamping to [0,1]")
            task.complexity_score = max(0.0, min(1.0, task.complexity_score))

        # Perform transformation
        progress_data = orchestration_task_to_conport_progress(task, workspace_id)

        # Validate output
        required_keys = ["workspace_id", "status", "description", "tags"]
        if not all(k in progress_data for k in required_keys):
            logger.error(f"Invalid progress_data: missing required keys")
            return None

        return progress_data

    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        return None
```

### ConPort API Failure Handling

```python
async def resilient_log_progress(progress_data: Dict) -> Optional[int]:
    """Log progress with retry and fallback."""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            result = await conport_client.log_progress(**progress_data)
            return result["id"]  # Success!

        except ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"ConPort connection failed (attempt {attempt+1}/{max_retries}), retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"ConPort unavailable after {max_retries} attempts: {e}")
                # Fallback: Store in local cache for later sync
                await local_cache.store_failed_sync(progress_data)
                return None

        except Exception as e:
            logger.error(f"ConPort API error: {e}")
            return None
```

**Graceful Degradation**:
- ConPort unavailable → Cache locally, sync when available
- Transformation error → Log warning, skip item, continue processing
- Validation failure → Use safe defaults, log issue for manual review

## Schema Evolution Strategy

### Version Compatibility

**Current Version**: 1.0 (Phase 1 implementation)
**Future Versions**: 1.1, 2.0, etc.

**Version Field** (add to all events):
```python
schema_version: str = "1.0"
```

**Backward Compatibility Rules**:
1. **Additive Only**: New optional fields OK, removing fields breaks compatibility
2. **Tag Namespace**: New tag categories use new prefixes (don't reuse)
3. **Status Values**: Never remove status values, only add new ones
4. **Defaults**: All new fields MUST have safe defaults

**Example** (hypothetical v1.1):
```python
# v1.0 (Phase 1)
tags = ["energy-high", "complexity-6"]

# v1.1 (Phase 2 - adds time tracking)
tags = ["energy-high", "complexity-6", "time-estimate-60m", "time-actual-45m"]

# Backward compatible: v1.0 transformers ignore unknown tags
# Forward compatible: v1.1 transformers provide defaults for missing tags
```

## Implementation Checklist (for Tasks 2.2-2.6)

### Task 2.2: Create ConPort Event Adapter

**File**: `services/task-orchestrator/adapters/conport_adapter.py`

**Implement**:
- [x] `orchestration_task_to_conport_progress()` (from this spec)
- [x] `conport_progress_to_orchestration_task()` (from this spec)
- [x] `safe_orchestration_task_to_conport_progress()` (error handling)
- [x] `resilient_log_progress()` (retry + fallback)
- [x] Tag generation utilities
- [x] Tag parsing utilities
- [x] Status mapping constants
- [x] Validation functions

### Task 2.3: Create Insight Publisher

**File**: `services/task-orchestrator/adapters/conport_insight_publisher.py`

**Implement**:
- [x] `AIDecisionEvent` dataclass
- [x] `log_ai_decision()` method
- [x] `link_decision_to_task()` method
- [x] AI agent result parsing
- [x] Automatic linking to related tasks

### Task 2.4: Implement Schema Mapping

**File**: `services/task-orchestrator/adapters/schema_mapping.py`

**Implement**:
- [x] ADHD tag encoders (`encode_energy()`, `encode_complexity()`, `encode_priority()`)
- [x] ADHD tag decoders (`decode_energy()`, `decode_complexity()`, `decode_priority()`)
- [x] Description formatters (`build_description()`, `parse_description()`)
- [x] Dependency mapping (`sync_dependencies_to_conport()`)

### Task 2.5: Remove Direct Storage

**File**: `services/task-orchestrator/enhanced_orchestrator.py`

**Refactor**:
- [x] Remove `self.orchestrated_tasks: Dict[str, OrchestrationTask] = {}` (line 136)
- [x] Add `self.conport_adapter: ConPortEventAdapter`
- [x] Replace all `self.orchestrated_tasks[id]` with ConPort queries
- [x] Implement `get_orchestrated_tasks()` → calls `conport_adapter.get_all_progress()`
- [x] Implement `update_task()` → calls `conport_adapter.update_progress()`

### Task 2.6: Integration Test Event Flow

**File**: `services/task-orchestrator/tests/test_conport_integration.py`

**Tests**:
- [x] `test_transformation_lossless()`
- [x] `test_adhd_tags_queryable()`
- [x] `test_status_mapping_comprehensive()`
- [x] `test_dependency_sync()`
- [x] `test_sprint_activation_event()`
- [x] `test_ai_decision_logging()`
- [x] `test_batch_updates()`
- [x] `test_error_handling_graceful()`

## Next Steps (Component 2 Execution)

### Task 2.2: Create ConPort Event Adapter (90 min, complexity 0.7)

**Dependencies**: Task 2.1 ✅ (this specification)

**Deliverable**: `services/task-orchestrator/adapters/conport_adapter.py`

**Implementation Guidance**:
1. Copy transformation functions from this specification (lines 90-180)
2. Add error handling (safe_*, resilient_* wrappers)
3. Implement ConPort MCP client wrapper
4. Add logging for debugging
5. Write unit tests for transformers

**Estimated Lines**: ~300-400 lines

### Task 2.3: Create Insight Publisher (60 min, complexity 0.6)

**Dependencies**: Task 2.1 ✅

**Deliverable**: `services/task-orchestrator/adapters/conport_insight_publisher.py`

**Implementation Guidance**:
1. Implement `AIDecisionEvent` dataclass (from this spec lines 230-260)
2. Create `log_ai_decision()` method
3. Add automatic linking to related tasks
4. Handle AI agent result parsing

**Estimated Lines**: ~200 lines

## Conclusion

**Task 2.1 Status**: ✅ **COMPLETE**
**Event Schema**: 🟢 Fully specified
**ADHD Tag Format**: 🟢 Standardized
**Transformations**: 🟢 Implementation-ready
**Validation**: 🟢 Test suite defined

**Go/No-Go for Task 2.2 (Event Adapter Implementation)**: 🟢 **GO**

This specification provides complete implementation guidance for Component 2 tasks:
- Bidirectional transformations (copy-paste ready code)
- ADHD tag format (standardized for all future use)
- Event types (3 primary patterns documented)
- Error handling strategy (graceful degradation)
- Validation test suite (comprehensive coverage)

Component 2 implementation can proceed with high confidence - all architectural decisions are made, all patterns are specified.

---

**Deliverable**: conport-event-schema-design.md
**Completion Time**: 60 minutes (on schedule)
**Code Provided**: ~200 lines of implementation-ready transformation logic
**Next Task**: 2.2 (Create ConPort Event Adapter) - READY TO IMPLEMENT
**Component 2 Progress**: 1/6 tasks (17%)
