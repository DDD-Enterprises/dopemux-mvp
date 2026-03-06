# Task Orchestrator, Leantime & PM Plane Documentation Summary

## Document Locations

### PM Plane (Hub)
- **HUB**: `docs/planes/pm/HUB.md` — Entry point, phase structure, deliverables
- **SUPERVISOR**: `docs/planes/pm/SUPERVISOR.md` — Phase 0 audit instructions
- **PM_ARCHITECTURE**: `docs/planes/pm/PM_ARCHITECTURE.md` — Canonical task object, lifecycle, storage model
- **PM_ADHD_REQUIREMENTS**: `docs/planes/pm/PM_ADHD_REQUIREMENTS.md` — ADHD-safe requirements, signals contract

### Task Orchestrator Service
- **Service README**: `services/task-orchestrator/README.md` (not yet viewed)
- **PM Plane Architecture**: `services/task-orchestrator/docs/pm-plane-architecture.md` — Two-plane design, components, data flow
- **Tools Documentation**: `services/task-orchestrator/docs/tools-documentation.md` — 37 tools (orchestration, ADHD, coordination, decision, risk, performance)
- **UI MVP**: `services/task-orchestrator/docs/DOPESMUX_ULTRA_UI_MVP_COMPLETION.md`
- **Suppression Telemetry**: `services/task-orchestrator/SUPPRESSION_TELEMETRY.md`

### PM Plane Derived Docs
- **PM_PLANE_INVENTORY**: `docs/planes/pm/PM_PLANE_INVENTORY.md` — Services, CLIs, stores (Phase 0)
- **PM_PLANE_GAPS**: `docs/planes/pm/PM_PLANE_GAPS.md` — Missing components, risks (Phase 0)
- **PM_FRICTION_MAP**: `docs/planes/pm/PM_FRICTION_MAP.md` — Pain points (Phase 1)
- **SIGNAL_VS_NOISE_ANALYSIS**: `docs/planes/pm/SIGNAL_VS_NOISE_ANALYSIS.md` — Event filtering (Phase 1)
- **PM_OUTPUT_BOUNDARIES**: `docs/planes/pm/PM_OUTPUT_BOUNDARIES.md` — Minimal output policy
- **PM_WORKFLOWS_DERIVED**: `docs/planes/pm/PM_WORKFLOWS_DERIVED.md` — User workflows (Phase 5)

---

## Key Architectural Concepts

### 1. Two-Plane Architecture
```
PM Plane (Leantime) ↔ Task Orchestrator ↔ ConPort-KG (Knowledge Graph)
                             ↓
                         Taskmaster AI
                         (Intelligent Analysis)
```

**Components**:
- **Leantime**: Human-facing PM tool (JSON-RPC API, x-api-key auth)
- **Task Orchestrator**: Coordination hub (agent dispatch, ADHD optimization, sync)
- **ConPort**: Knowledge graph (decisions, progress, semantic search)
- **Taskmaster**: AI task decomposition and analysis

### 2. Canonical Task Object (PM Architecture)

**Core Fields**:
- `task_id`: Immutable stable ID
- `title`: Required user-visible title
- `status`: Canonical enum (TODO, IN_PROGRESS, BLOCKED, DONE, CANCELED)
- `phase`: Optional workflow phase label
- `created_at_utc`, `updated_at_utc`: RFC3339 UTC timestamps
- `version`: Monotonic optimistic version
- `provenance`: Actor/tool details
- `idempotency`: Transition key + optional content hash
- `links`: ConPort, Chronicle, external refs

**Status Mapping** (dialect normalization):
- `pending`, `planned` → TODO
- `in_progress` → IN_PROGRESS
- `blocked` → BLOCKED
- `completed`, `done` → DONE
- `cancelled`, `canceled` → CANCELED

**Canonical Lifecycle**:
```
TODO → IN_PROGRESS → BLOCKED → DONE
  ↓        ↓          ↓
  └─ CANCELED ◄──────┘
```

### 3. Task Orchestrator Data Models

**Key Classes** (from `/services/task-orchestrator/task_orchestrator/models.py`):

1. **Task**
   - id, title, description, status
   - complexity_score, energy_required, cognitive_load
   - break_frequency_minutes
   - source (task-orchestrator, taskmaster, leantime, cli)

2. **OrchestrationTask**
   - Extends Task with:
   - leantime_id, conport_id
   - ADHD metadata (complexity_score, energy_required, break_frequency)

3. **SyncEvent**
   - source_system, target_systems
   - event_type (task_updated, decision_logged, progress_changed)
   - task_id, data, timestamp
   - adhd_metadata (cognitive_load, energy_required)

### 4. Event Lifecycle & Suppression

**Event Coordinator Suppression Rules** (from `event_coordinator.py`):

- **Deep Focus**: Suppress non-critical events during focus window
- **Low Energy**: Suppress high cognitive-load events when energy=low
- **Overwhelm**: Rapid task switching + no-progress detection
- **Telemetry**: Track suppression_rate_pct, signal_noise_ratio, top_suppression_rule

**Telemetry Summary** (minimal PM signals):
- `next_action`: One actionable next step
- `events_received`, `events_passed`, `events_suppressed`, `suppression_rate_pct`
- `overwhelm_risk_level`: From ADHD engine
- Context recovery: task, mental model, recent decisions

### 5. Storage & Mirroring Strategy

| Classification | Owner | Content | Write Contract |
|---|---|---|---|
| **Canonical PM** | PM plane | Task object + lifecycle version | Single write per transition; idempotent by key |
| **Memory/ConPort** | Memory plane | Decisions, rationale, progress | PM links out; PM doesn't duplicate |
| **Chronicle** | Memory capture | PM events promoted | Mirror-only; never canonical truth |
| **Derived** | PM telemetry | Suppression rates, dashboards | Never canonical truth |
| **Mirrored** | Integrations | Leantime/taskmaster views | Async projection; idempotent retries |

### 6. PM Event Taxonomy

**Canonical PM Events**:
- `pm.task.created`
- `pm.task.updated`
- `pm.task.status_changed`
- `pm.task.blocked`
- `pm.task.completed`
- `pm.decision.linked`
- `pm.sync.leantime.requested` / `.succeeded` / `.failed`

**Event Fields**:
- `event_id` (content-address hash)
- `task_id`
- `event_type`
- `ts_utc`
- `source`
- `idempotency_key`
- `payload` (minimal delta)

### 7. ADHD Requirements Summary

**PM Responsibilities**:
1. Decide what action to show now
2. Apply suppression policy (deep focus, low energy, overwhelm)
3. Expose minimal next-step output

**Must Not Do**:
- Persist full memory substrate or duplicate search internals
- Own decision logging or progress persistence
- Define search/noise filtering (that's Search plane)

**Minimum Viable Signals** (no overload):
- One actionable next step + current status
- Context recovery anchor (task, mental model, decisions)
- Suppression snapshot (received/passed/suppressed/rate)
- Overwhelm risk level

**Derived Signals** (from telemetry, not local state):
- `signal_noise_ratio`, `suppression_rate_pct`
- `top_suppression_rule`
- Current ADHD state (focus_mode, energy_level, context_switches)
- Context restorable/not-restorable

---

## Task Orchestrator: 37 Tools

### Core Orchestration (11 tools)
1. `analyze_dependencies` - Identify blocked tasks
2. `detect_conflicts` - Find scheduling conflicts
3. `find_critical_path` - Longest path through graph
4. `batch_tasks` - Group tasks for parallel execution
5. `parallelize_tasks` - Identify concurrent tasks
6. `sequence_tasks` - Linearized execution order
7. `estimate_timeline` - Completion prediction
8. `identify_blockers` - Focus on critical path
9. `optimize_workflow` - ADHD-friendly execution
10. `validate_workflow` - Completeness check
11. `generate_workflow_template` - Standardized templates

### ADHD Integration (8 tools)
12. `assess_energy_level` - Current energy state
13. `assess_attention_state` - Focus/scattered/transitioning
14. `analyze_context_switches` - Mental model drift
15. `detect_overwhelm_signals` - Rapid switching, no-progress
16. `recommend_break` - Pomodoro enforcement
17. `adapt_to_energy_state` - Adjust task complexity
18. `optimize_cognitive_load` - Balance workload
19. `suggest_next_task` - Energy-appropriate choice

### Service Coordination (7 tools)
20. `sync_with_leantime` - Leantime bidirectional sync
21. `sync_with_conport` - ConPort progress/decision logging
22. `emit_task_event` - EventBus publishing
23. `check_dependency_status` - Cross-service queries
24. `coordinate_with_agents` - Agent routing
25. `broadcast_updates` - Multi-system notification
26. `handle_integration_failure` - Error recovery

### Decision Management (6 tools)
27. `log_decision` - Architecture decision logging
28. `link_decision_to_task` - Decision→task relationships
29. `retrieve_decision_context` - Decision rationale
30. `track_decision_outcome` - Success/failure tracking
31. `link_evidence` - Citation tracking
32. `generate_decision_summary` - ADR auto-generation

### Risk Assessment (5 tools)
33. `identify_schedule_risk` - Timeline threats
34. `assess_dependency_risk` - Blocker likelihood
35. `predict_overrun_probability` - Estimation risk
36. `flag_context_switch_cost` - Mental model risk
37. `recommend_risk_mitigation` - Preventive actions

---

## Integration Points

### Leantime → Task Orchestrator
- **API**: JSON-RPC
- **Auth**: x-api-key header
- **Trigger**: Task creation, updates, milestone changes
- **Response**: ConPort entries + event emission

### Task Orchestrator → ConPort
- **Transport**: MCP async method calls (asyncpg + pgvector)
- **Operations**: 
  - `log_progress()` - Progress entry creation
  - `log_decision()` - Decision tracking
  - `link_decision_to_task()` - Relationships
  - `semantic_search()` - Vector similarity

### Task Orchestrator → EventBus
- **Adapter**: InMemory (process-local) or Redis Streams (distributed)
- **Pattern Matching**: Exact, prefix, wildcard subscriptions
- **Publishing**: PM events with idempotency keys

### ADHD Engine ↔ Task Orchestrator
- **Signals**: Energy level, attention state, overwhelm detection
- **Suppression**: Deep focus, low energy, overwhelm rules
- **Context**: Session checkpoints, mental model preservation

---

## Phase Structure (PM Plane)

### Phase 0: Inventory (Evidence-first)
- **Deliverables**: PM_PLANE_INVENTORY.md, PM_PLANE_GAPS.md
- **Method**: Scan task-orchestrator, taskmaster, leantime, CLI; identify services, stores, transitions

### Phase 1: Friction & Signal
- **Deliverables**: PM_FRICTION_MAP.md, SIGNAL_VS_NOISE_ANALYSIS.md
- **Focus**: Pain points, event filtering, suppression logic

### Phase 2: ADHD Alignment
- **Deliverables**: PM_ADHD_REQUIREMENTS.md, PM_OUTPUT_BOUNDARIES.md
- **Focus**: Minimal signals, progressive disclosure, context recovery

### Phase 3: Architecture
- **Deliverables**: PM_ARCHITECTURE.md, ADR-PM-### (decisions)
- **Focus**: Canonical task object, lifecycle, storage boundaries

### Phase 4: Implementation
- **Deliverables**: Task Packets A/B/C (coded solutions)
- **Focus**: Code changes, migrations, integration

### Phase 5: Workflows & Derived
- **Deliverables**: PM_WORKFLOWS_DERIVED.md, PM_PRESETS.md
- **Focus**: User workflows, optimization patterns

---

## Current State Observations

### Evidence-Locked (PM_ARCHITECTURE)

✅ **Confirmed**:
- Task-orchestrator has explicit task model + status enum
- ConPort MCP wrapper for progress/decision/linking
- Event-driven coordination with task lifecycle processors
- Dopemux event bus (in-memory + Redis adapters)
- Taskmaster bridge adapter + process proxy
- CLI task capture/listing commands
- Leantime + taskmaster integration surfaces

⚠️ **Unknowns**:
- Exact canonical PM persistence location/module
- Chronicle promotion contract for PM-only events
- `paused`, `needs_break`, `context_switch` → canonical states?
- Event ID hash normalization spec
- dopecon-bridge tasks table: projection or competing source of truth?

### Failure Modes (PM_ADHD_REQUIREMENTS)

- **Context Loss**: Task IDs lost after interruption; ADHD modules add context snapshot/restoration
- **Task Pile-up**: High-volume repeated events; overwhelm detection models rapid switching
- **Phase Confusion**: Status dialects split across task-orchestrator, ConPort, CLI
- **False Urgency**: Deep-focus suppression intentionally blocks lower-priority events

---

## Key References for Implementation

**Canonical Source Files**:
- Task models: `services/task-orchestrator/task_orchestrator/models.py`
- Event coordination: `services/task-orchestrator/event_coordinator.py`
- ConPort client: `services/task-orchestrator/conport_mcp_client.py`
- EventBus: `src/dopemux/event_bus.py`, `src/dopemux/events/types.py`
- CLI surfaces: `src/dopemux/cli.py` (task commands)
- ADHD context: `services/adhd_engine/domains/attention/context_preserver.py`

**Evidence Bundles**:
- Phase 0: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/`
- Phase 1: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/`

