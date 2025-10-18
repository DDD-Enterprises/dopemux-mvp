---
id: adr-197
title: 'ADR-197: Four-Stage Task/Epic Workflow System with Leantime Integration'
type: adr
owner: dopemux-core
date: 2025-10-04
status: approved
adhd_cognitive_load: 0.7
adhd_attention_required: high
tags:
- workflow
- task-management
- epic-management
- leantime-integration
- two-plane-architecture
- adhd-optimization
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# ADR-197: Four-Stage Task/Epic Workflow System with Leantime Integration

## Status

**Approved** (Multi-model consensus validation complete: 8/10 + 8/10 confidence)

**Depends On**:
- ConPort Memory System (Decision #196)
- Leantime PM Plane (active component)
- Integration Bridge (coordination layer)

**Validated By**:
- Zen Ultrathink: 8 steps, VERY HIGH confidence
- Zen Consensus: 2 models (gpt-5-mini FOR/AGAINST), strong convergence

## Context

### Problem Statement

Dopemux currently lacks a comprehensive workflow system for tracking ideas from inception through execution. This creates several problems:

**Current Pain Points**:
1. **Idea Capture Gap**: No structured place to store unvalidated ideas or feature requests
2. **Epic Planning Gap**: No workflow for promoting approved ideas into planned epics
3. **Task Decomposition Gap**: No system for breaking epics into concrete, executable tasks
4. **Execution Tracking Gap**: No clear handoff from planning to active development
5. **ADHD Context Loss**: Ideas get lost between stages, work falls through cracks

**User Request** (2025-10-04):
> "I think we should have a place to put things that we want to build but haven't fleshed out, either as ideas or todo's or epics, then have a queue of approved and thought out features or work, then once those are fully planned and broken down under an epic they can go in a work queue or something."

**Architecture Context**:
- Two-Plane Architecture (PM Plane + Cognitive Plane)
- Leantime = PM Plane presentation layer (status authority)
- ConPort = Cognitive Plane knowledge graph (knowledge authority)
- Integration Bridge = Cross-plane coordination (PORT_BASE+16)

**Critical Correction** (Decision #195):
- Initial design incorrectly assumed Leantime deprecated
- Leantime is ACTIVE component, required for two-plane architecture
- Must integrate as status authority, not optional one-way sync

## Decision

Implement **4-Stage Workflow System** using ConPort primitives with Leantime integration for the PM Plane.

### Four Stages (Idea → Epic → Planning → Execution)

#### Stage 1: Idea (Unstructured Capture)

**Purpose**: Capture rough ideas, feature requests, brainstorms before validation

**ConPort Storage**: `custom_data` category `workflow_ideas`

**Schema**:
```python
WorkflowIdea = {
    "title": str,
    "description": str,
    "source": str,  # "user-request", "brainstorm", "bug-report"
    "creator": str,
    "tags": List[str],
    "created_at": datetime,
    "status": str,  # "new", "under-review", "approved", "rejected"
}
```

**Leantime Sync**: ❌ None (too early/unstructured for PM tool)

**ADHD Optimizations**:
- Quick capture (title + description minimum)
- No required fields beyond basics
- Gentle reminder: "3+ similar ideas → consider epic"
- Progressive disclosure: details on request

#### Stage 2: Epic (Approved Feature with Scope)

**Purpose**: Approved ideas promoted to epics with defined scope and acceptance criteria

**ConPort Storage**: `custom_data` category `workflow_epics`

**Schema**:
```python
WorkflowEpic = {
    "title": str,
    "description": str,
    "business_value": str,
    "acceptance_criteria": List[str],
    "priority": str,  # "critical", "high", "medium", "low"
    "status": str,    # "planned", "in-planning", "ready", "in-progress", "done"
    "leantime_project_id": Optional[int],
    "created_from_idea_id": Optional[str],
    "tags": List[str],
    "adhd_metadata": {
        "estimated_complexity": float,  # 0.0-1.0
        "required_energy_level": str,   # "low", "medium", "high"
        "can_work_parallel": bool
    }
}
```

**Leantime Sync**: ✅ Bidirectional (Epic ↔ Leantime Project)
- **Status Authority**: Leantime (planned→active→done)
- **Knowledge Authority**: ConPort (business value, acceptance criteria, relationships)
- **Sync Frequency**: 30 seconds (Integration Bridge webhook)
- **Conflict Resolution**: Leantime status wins, ConPort knowledge wins

**ADHD Optimizations**:
- Show max 5 epics at a time (prevent overwhelm)
- Visual progress indicators
- Complexity scoring upfront
- Energy level matching

#### Stage 3: Planning (Task Decomposition)

**Purpose**: Break epics into concrete, executable tasks with dependencies

**ConPort Storage**: `progress_entry` with `parent_id` hierarchy

**Schema**:
```python
WorkflowTask = {
    "description": str,
    "status": str,  # "TODO", "IN_PROGRESS", "BLOCKED", "DONE"
    "parent_id": Optional[int],  # Link to parent task or None for top-level
    "epic_id": str,              # Link to workflow_epic
    "leantime_task_id": Optional[int],
    "adhd_metadata": {
        "complexity": float,           # 0.0-1.0 (Serena LSP scoring)
        "cognitive_load": float,       # 0.0-1.0
        "energy_level": str,           # "low", "medium", "high"
        "estimated_focus_minutes": int # 25, 50, 75 (Pomodoro units)
    },
    "dependencies": List[int],  # Task IDs that must complete first
    "linked_files": List[str],  # Files this task touches
    "linked_decisions": List[int]  # Decision IDs related to this task
}
```

**Leantime Sync**: ✅ Bidirectional (Task ↔ Leantime Task)
- **Status Authority**: Leantime (TODO→In Progress→Done)
- **Knowledge Authority**: ConPort (complexity, dependencies, file links)
- **Sync Frequency**: 30 seconds
- **Dependency Visualization**: Integration Bridge provides dependency graph

**ADHD Optimizations**:
- Max 3 active tasks (focus preservation)
- Progressive disclosure: collapsed by default, expand on request
- Dependency warnings: "Task B blocked by Task A"
- Complexity badges: 🟢 Low, 🟡 Medium, 🔴 High

#### Stage 4: Execution (Active Work)

**Purpose**: Tasks in active development with progress tracking

**ConPort Storage**: Same `progress_entry` with status `IN_PROGRESS`

**Serena LSP Integration**:
- Track actual file changes
- Link commits to tasks automatically
- Update complexity scores based on actual changes
- Detect scope creep (files changed beyond `linked_files`)

**Leantime Sync**: ✅ Real-time (Status updates via webhooks)
- Integration Bridge listens for Leantime status changes
- Updates ConPort progress_entry immediately
- Triggers Serena LSP file tracking when status → IN_PROGRESS

**ADHD Optimizations**:
- Auto-save every 30 seconds (context preservation)
- Break reminders: 25-minute Pomodoro default
- Visual progress: "3/8 tasks complete ████░░░░"
- Hyperfocus protection: Warn at 60min, mandate break at 90min

### Two-Plane Authority Matrix

| Aspect | Authority | Rationale |
|--------|-----------|-----------|
| Task Status | Leantime (PM Plane) | Team visibility, collaboration, status updates |
| Epic Status | Leantime (PM Plane) | Project tracking, milestone management |
| Decisions | ConPort (Cognitive Plane) | Knowledge graph, architectural choices, rationale |
| Dependencies | ConPort (Cognitive Plane) | Technical dependencies, file relationships |
| Complexity Scoring | Serena LSP (Cognitive Plane) | Code-level analysis, cognitive load estimation |
| File Links | ConPort + Serena (Cognitive Plane) | Semantic code understanding |
| Business Value | ConPort (Cognitive Plane) | Strategic context, acceptance criteria |

### Integration Bridge Sync Mechanics

**Webhook Architecture**:
```
Leantime Status Change (Task updated)
    ↓
Webhook → Integration Bridge (PORT_BASE+16)
    ↓
ConPort Update (progress_entry.status)
    ↓ (if status → IN_PROGRESS)
Serena LSP Activation (start tracking files)
```

**Idempotent Design**:
- All webhook handlers check last_updated timestamp
- Ignore duplicate events within 5-second window
- Reconciliation dashboard shows sync status
- Manual retry for failed syncs

**Conflict Resolution**:
1. **Status Conflicts**: Leantime always wins (status authority)
2. **Knowledge Conflicts**: ConPort always wins (knowledge authority)
3. **Race Conditions**: Last-write-wins with audit trail
4. **Sync Failures**: Queue for retry, show warning in UI

### Promotion Flow (One-Way)

**Idea → Epic**:
```python
def promote_idea_to_epic(idea_id: str) -> str:
    """Promote approved idea to epic (one-way)."""
    idea = get_custom_data("workflow_ideas", idea_id)

    epic = {
        "title": idea["title"],
        "description": idea["description"],
        "created_from_idea_id": idea_id,
        "status": "planned",
        "tags": idea["tags"]
    }

    epic_id = log_custom_data("workflow_epics", epic)

    # Create Leantime project
    leantime_project_id = integration_bridge.create_project(epic)
    epic["leantime_project_id"] = leantime_project_id
    update_custom_data("workflow_epics", epic_id, epic)

    # Mark idea as promoted
    idea["status"] = "promoted"
    idea["promoted_to_epic_id"] = epic_id
    update_custom_data("workflow_ideas", idea_id, idea)

    return epic_id
```

**Epic → Tasks**:
```python
def decompose_epic_to_tasks(epic_id: str, tasks: List[TaskSchema]) -> List[int]:
    """Decompose epic into tasks (one-way)."""
    task_ids = []

    for task in tasks:
        # Create ConPort progress_entry
        progress_id = log_progress(
            status="TODO",
            description=task["description"],
            linked_item_type="workflow_epic",
            linked_item_id=epic_id
        )

        # Create Leantime task
        leantime_task_id = integration_bridge.create_task(
            epic["leantime_project_id"],
            task
        )

        # Link back
        update_progress(
            progress_id,
            custom_fields={"leantime_task_id": leantime_task_id}
        )

        task_ids.append(progress_id)

    return task_ids
```

**Tasks → Execution**:
- User updates status in Leantime: TODO → IN_PROGRESS
- Webhook triggers Integration Bridge
- ConPort updates progress_entry status
- Serena LSP starts file tracking
- Auto-save activates (every 30s)

## Consequences

### Positive

**1. Complete Workflow Coverage**
- Ideas captured before they're lost
- Clear promotion path (idea→epic→tasks→execution)
- Nothing falls through cracks
- Traceability from concept to code

**2. ADHD Optimization**
- Progressive disclosure (max 3-5 items per stage)
- Gentle warnings (not blocking)
- Visual progress indicators
- Context preservation across interruptions

**3. Two-Plane Integration**
- Leantime provides team visibility and collaboration
- ConPort preserves knowledge graph and technical context
- Clear authority boundaries prevent conflicts
- Integration Bridge handles sync complexity

**4. Leverages Existing Infrastructure**
- Zero new databases or services required
- ConPort custom_data for stages 1-2
- ConPort progress_entry for stages 3-4
- Leantime for PM Plane presentation
- Serena LSP for code tracking

**5. Industry Best Practices**
- One-way promotion flow (prevents sync complexity)
- Single source of truth per field
- Idempotent webhook handlers
- Reconciliation dashboard for monitoring

### Negative

**1. Sync Complexity**
- Integration Bridge must maintain consistency
- Webhook delivery failures require retry logic
- Conflict resolution rules must be clear
- Monitoring overhead (sync status, failures)

**2. ConPort + Leantime Dependency**
- CLI depends on both systems being accessible
- If either down, degraded experience
- Need fallback workflows for outages

**3. Learning Curve**
- Users must understand two-plane model
- Clear documentation required for workflow stages
- Training needed for team adoption

**4. Maintenance Debt**
- Integration code becomes permanent product
- Schema migrations for both systems
- Webhook changes require coordination
- Long-term support commitment

### Mitigations

**Sync Failures**:
```python
# Queue failed syncs for retry
if not sync_successful:
    retry_queue.add(sync_event, max_retries=3, backoff_seconds=30)
    show_warning_in_ui("Sync delayed, will retry automatically")
```

**ConPort Unavailable**:
```python
try:
    epics = get_custom_data("workflow_epics")
except ConPortUnavailable:
    console.print("[yellow]⚠️  ConPort unavailable, showing Leantime data only[/yellow]")
    epics = integration_bridge.get_leantime_projects()
```

**Leantime Unavailable**:
```python
try:
    sync_to_leantime(epic)
except LeantimeUnavailable:
    console.print("[yellow]⚠️  Leantime unavailable, ConPort tracking continues[/yellow]")
    console.print("[dim]Status updates will sync when Leantime reconnects[/dim]")
```

**User Confusion**:
- Visual indicators: "Status from Leantime" vs "Knowledge from ConPort"
- Hover tooltips explaining authority boundaries
- Onboarding wizard for new users
- Clear error messages when sync conflicts occur

## Alternatives Considered

### Alternative 1: Leantime-Only (No ConPort)

**Approach**: Store everything in Leantime, skip ConPort

**Rejected**:
- Leantime lacks knowledge graph capabilities
- No semantic code relationships (Serena LSP integration lost)
- No decision genealogy tracking
- No ADHD-specific metadata (complexity, cognitive load)
- Violates two-plane architecture principle

### Alternative 2: ConPort-Only (No Leantime)

**Approach**: Store everything in ConPort, build custom UI

**Rejected**:
- Reinventing PM tool functionality
- No team collaboration features
- No visual project boards
- Significant development effort (6+ months)
- Violates DRY principle (Leantime already exists)

### Alternative 3: Full Two-Way Real-Time Sync

**Approach**: Bidirectional sync for ALL fields, not just status

**Rejected by Consensus**:
- Both FOR and AGAINST models warned against this
- High sync complexity, conflict-heavy
- GitHub/Jira synchronizers fail with this approach
- Industry best practice: one-way promotion + selective sync
- Should defer until Phase 1 proven stable

### Alternative 4: Manual Links Only (Deep Links + SSO)

**Approach**: Store link to Leantime in ConPort, no sync

**Rejected**:
- Manual status updates required (user burden)
- No automatic progress tracking
- ADHD users forget to update both systems
- Defeats purpose of integration

**Note**: This may be fallback for ConPort/Leantime outages

## Implementation Timeline

### Phase 1: Foundation (One-Way Promotion) - 8 hours

**Sprint 1: ConPort Workflow Schema (3 hours)**
- Define Pydantic models for WorkflowIdea, WorkflowEpic
- Create ConPort custom_data helper functions
- Write unit tests for schema validation

**Sprint 2: Integration Bridge Setup (3 hours)**
- Idempotent webhook handlers (status sync only)
- Leantime API client (create project, create task, update status)
- Retry queue with exponential backoff

**Sprint 3: Promotion Functions (2 hours)**
- `promote_idea_to_epic(idea_id)`
- `decompose_epic_to_tasks(epic_id, tasks)`
- CLI commands: `dopemux workflow promote idea <id>`

### Phase 2: Monitoring & Stability - 4 hours

**Sprint 4: Reconciliation Dashboard (2 hours)**
- Show sync status for all epics/tasks
- Display failed syncs with retry button
- Audit trail (last synced, sync errors)

**Sprint 5: Metrics & Alerting (2 hours)**
- Webhook delivery success rate
- Average sync latency
- Conflict frequency
- Manual reconciliation rate

**Success Criteria for Phase 2**:
- >95% webhook delivery success
- <30s average sync latency
- <5% manual reconciliation rate
- Zero data loss incidents

### Phase 3: Selective Bidirectional Sync (Optional) - 6 hours

**Only proceed if Phase 2 stable for 2+ months and clear user demand**

**Sprint 6: Field-Level Sync (3 hours)**
- Define ownership matrix (which system writes which fields)
- Implement conflict resolution UI
- Version tracking with audit trail

**Sprint 7: Advanced Features (3 hours)**
- Dependency visualization in Leantime
- Complexity badges in Leantime tasks
- Serena LSP file links in Leantime

**Total Timeline**: 12 hours minimum (Phase 1+2), 18 hours full (all phases)

## Testing Strategy

### Unit Tests

```python
# test_workflow_schema.py
def test_workflow_idea_validation():
    """Test Pydantic schema validation for ideas."""

def test_workflow_epic_creation():
    """Test epic creation with required fields."""

def test_promote_idea_to_epic():
    """Test idea→epic promotion flow."""

# test_integration_bridge.py
def test_idempotent_webhook_handler():
    """Test duplicate events ignored within 5-second window."""

def test_webhook_retry_logic():
    """Test failed syncs queued for retry."""

def test_conflict_resolution():
    """Test Leantime status wins, ConPort knowledge wins."""
```

### Integration Tests

```python
# test_workflow_integration.py
def test_full_workflow_idea_to_execution():
    """
    End-to-end test:
    1. Create idea in ConPort
    2. Promote to epic (Leantime project created)
    3. Decompose to tasks (Leantime tasks created)
    4. Update status in Leantime
    5. Verify ConPort synced
    """

def test_leantime_unavailable_fallback():
    """Test ConPort-only mode when Leantime down."""

def test_conport_unavailable_fallback():
    """Test Leantime-only mode when ConPort down."""
```

### Manual Validation

- Create idea → promote to epic → verify Leantime project
- Update task status in Leantime → verify ConPort synced
- Kill Leantime → verify graceful degradation
- Kill ConPort → verify graceful degradation
- Simulate webhook failure → verify retry queue

## Documentation Updates

### ADR
- ✅ This document (ADR-197)

### How-To Guides
- `docs/02-how-to/workflow-idea-to-epic.md` - Promote ideas to epics
- `docs/02-how-to/workflow-epic-decomposition.md` - Break epics into tasks
- `docs/02-how-to/workflow-troubleshooting.md` - Sync issues, conflicts

### Reference
- `docs/03-reference/workflow-schema.md` - Complete schema documentation
- `docs/03-reference/integration-bridge-api.md` - Webhook spec, retry logic

### Architecture
- Update `docs/01-architecture/two-plane-model.md` - Add workflow system
- Update `docs/01-architecture/integration-bridge.md` - Add sync mechanics

## Success Metrics

### User Experience
**Idea Capture**:
- Current: Ideas lost or scattered in notes/Slack
- Target: 100% ideas captured in structured workflow

**Context Switching**:
- Current: 2-5 minutes to remember "what was I doing?"
- Target: <10 seconds (auto-restore from ConPort active_context)

**Task Completion**:
- Current: ~60% tasks completed (ADHD baseline)
- Target: >85% tasks completed (ADHD-optimized workflow)

### Technical Performance
**Sync Latency**:
- Target: <30s average (95th percentile <60s)

**Webhook Delivery**:
- Target: >95% success rate

**Conflict Rate**:
- Target: <5% manual reconciliation

**Uptime**:
- Target: Graceful degradation when either system unavailable

### Business Value
**Feature Traceability**:
- Target: 100% features traceable from idea → epic → tasks → code

**Team Visibility**:
- Target: PM team can see all work in Leantime
- Target: Dev team can see all decisions in ConPort

**Knowledge Preservation**:
- Target: Zero knowledge loss during context switches
- Target: All architectural decisions logged with rationale

## Decision

✅ **APPROVED** for immediate implementation (Phase 1+2)

**Rationale**:
1. **Multi-Model Consensus**: Both FOR and AGAINST perspectives (8/10 + 8/10) recommended one-way promotion architecture
2. **Zero New Infrastructure**: Uses existing ConPort + Leantime + Integration Bridge
3. **Industry Alignment**: Matches proven patterns (Salesforce→Jira)
4. **ADHD Value**: Prevents idea loss, reduces context switching, preserves focus
5. **Low Risk**: Phase 1+2 = 12 hours, well-defined scope, clear success criteria

**Implementation Priority**: P0 (Immediate)

**Consensus Validation**:
- Zen Ultrathink: 8 steps, VERY HIGH confidence
- Zen Consensus (FOR): "Clear SSOT design with conservative sync patterns"
- Zen Consensus (AGAINST): "Start small with one-way promotion, avoid over-engineering"

**Key Takeaways from Consensus**:
- ✅ One-way promotion flow (idea→epic→tasks→execution)
- ✅ Idempotent webhook handlers with reconciliation dashboard
- ✅ Event-driven architecture (webhooks → queue → worker)
- ⚠️ Delay Phase 3 (bidirectional sync) until Phase 1+2 proven stable
- ⚠️ Monitor for sync storms, conflict UX confusion, maintenance debt

---

**Author**: Claude Code with SuperClaude framework + Zen multi-model validation
**Reviewers**: dopemux-core
**Related Decisions**:
- Decision #193 (Untracked Work Organization)
- Decision #195 (Leantime Status Correction)
- Decision #196 (Complete Workflow Design)
**Status**: Approved (Consensus validated 2025-10-04)
