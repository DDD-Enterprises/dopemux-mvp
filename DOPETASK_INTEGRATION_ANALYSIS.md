# dopeTask Integration Analysis
## Comprehensive Architecture Review: Task Packets → Orchestrator Bridge → ADHD Task Enablement

**Analysis Date**: 2026-02-16
**Scope**: Task Packet System, Task Orchestrator Bridge, ADHD Task Enablement Integration
**Status**: ⚠️ **PARTIAL INTEGRATION** - Systems exist but lack end-to-end coordination

---

## 📊 Executive Summary

### Current State
Three interconnected systems with **incomplete integration**:

| System | Status | Maturity | Risk |
|--------|--------|----------|------|
| **Task Packet Collection** | ✅ Complete | Production-ready | LOW - Standalone artifact collection |
| **Orchestrator Bridge** | ⚠️ Partial | 50% implemented | MEDIUM - Event emitter only, consumer incomplete |
| **ADHD Task Enablement** | ⚠️ Partial | 70% implemented | MEDIUM - Decomposition logic solid, event routing incomplete |

### Key Finding: **Integration Gaps**
```
Task Packets          Task Orchestrator      ADHD Engine
    ↓                      ↓                       ↓
[Collect artifacts]   [Emit events]    [Decompose tasks]
    └─────────────────────────────────────────────┘
                  MISSING CONNECTIONS
```

---

## 🏗️ Architecture Overview

### System 1: Task Packet Collection (`collect_task_packet.py`)

**Purpose**: Multi-layer debugging artifact collection for investigation packets

**Components**:
- Docker Compose log collection (service logs with timestamps)
- Health endpoint snapshots (HTTP health checks)
- Metrics collection (Prometheus format)
- Local log aggregation (from `./logs/` directory)
- Git state snapshots (branch, commit, diff status)

**Data Flow**:
```
Docker Compose Logs → [Summarizer] → JSON/JSONL
                                   ↓
                          Service Summaries
                                   ↓
                    Health Checks + Metrics
                                   ↓
                    [Archive] → TAR.GZ + JSON Report
                                   ↓
                    Optional: Datadog Emission
```

**Strengths**:
- ✅ Comprehensive multi-source collection
- ✅ Well-structured output (normalized JSONL, Prometheus export)
- ✅ Graceful degradation (skips unavailable services)
- ✅ Clear investigation workflow documentation

**Issues**:
- ❌ **No connection to task context**: Packet `task_id` is just a label, not linked to Task Orchestrator
- ❌ **No event emission**: Creates artifacts but doesn't inform other systems
- ❌ **Static configuration**: Service registry hardcoded, no dynamic discovery
- ⚠️ **Docker dependency**: Requires docker compose to be running

**Code Quality**:
- Type hints: ✅ Present
- Error handling: ✅ Comprehensive
- Testability: ⚠️ Difficult (Docker dependency, file I/O)
- Logging: ✅ Good progress indicators

---

### System 2: Task Orchestrator Bridge (`task_orchestrator.py`)

**Purpose**: Event emitter for task progress tracking and state changes

**Components**:
```
TaskOrchestratorEventEmitter
├── emit_task_progress_updated()  → task.progress.updated
├── emit_task_completed()         → task.completed
└── emit_task_blocked()           → task.blocked

TaskOrchestratorIntegrationManager
├── handle_task_status_change()   → Orchestrates event emission
└── get_metrics()                 → Emission statistics
```

**Data Flow**:
```
Task Status Change
    ↓
[emit_task_progress_updated]
    ↓
Event {
  type: "task.progress.updated",
  data: {task_id, status_transition, complexity, energy_required, ...},
  source: "task-orchestrator"
}
    ↓
EventBus.publish("dopemux:events", event)
```

**Strengths**:
- ✅ ADHD metadata captured (complexity, energy_required)
- ✅ Clear event structure
- ✅ Error tracking with emission_errors counter
- ✅ Supports multiple event types (progress, completion, blocking)

**Critical Issues**:
- ❌ **INCOMPLETE IMPLEMENTATION**: Only 50% done
  - Emits events BUT doesn't consume them
  - No event subscription logic
  - No ConPort persistence callback
  - Task Packet system not notified of progress

- ❌ **Missing bidirectional communication**:
  - Comment says "Bidirectional: subscribe ✅ + publish ✅" (line 305)
  - But subscribe implementation is missing!
  - Status says "70% done" in comment but only emit methods exist

- ❌ **No ConPort integration**:
  - Events emitted but never persisted to ConPort knowledge graph
  - Task decomposition events not linked to decisions
  - Progress tracking disconnected from session context

- ❌ **No Task Packet triggering**:
  - When task.blocked event emitted, should trigger investigation packet collection
  - Currently: task blocked → event → nowhere

**Code Quality**:
- Type hints: ✅ Present
- Error handling: ✅ Try/except with logging
- Testability: ⚠️ Event bus dependency, no mocking
- Logging: ✅ Good emoji-based status

---

### System 3: ADHD Task Enablement

**Purpose**: Break down complex tasks into ADHD-friendly micro-tasks with cognitive load routing

#### Component 3a: Task Decomposition Assistant

**Features**:
```
Input: "Migrate database from SQLite to PostgreSQL" (180 min estimate)
                           ↓
         [Analyze Complexity] → VERY_COMPLEX
         [Analyze Energy]     → HIGH
         [Check if decompose] → YES (>2h)
                           ↓
    [Generate micro-tasks by pattern]
      1. Review current implementation (10 min, MEDIUM)
      2. Design PostgreSQL schema (15 min, HIGH)
      3. Write migration script (15 min, HIGH)
      4. Test on staging (10 min, MEDIUM)
      5. Execute migration (5 min, LOW)
                           ↓
    [Optimize order by energy level]
      → For HIGH energy: Start with HIGH-energy tasks
      → For LOW energy: Start with LOW-energy tasks (momentum)
                           ↓
    Output: TaskDecomposition {
      micro_tasks: [...],
      recommended_order: [...],
      adhd_friendly_score: 0.95
    }
```

**Strengths**:
- ✅ **Excellent pattern-based decomposition**:
  - Implementation: Read docs → Test → Code → Test → Edge cases
  - Refactoring: Review → Identify areas → Add tests → Refactor → Verify
  - Bug fix: Reproduce → Test → Root cause → Fix → Verify
  - Generic: Time-based chunking fallback

- ✅ **Energy-aware scheduling**:
  - Complexity scoring (0.0-1.0)
  - Energy requirements (HIGH/MEDIUM/LOW)
  - Task suitability scoring based on current state

- ✅ **Micro-commitment generation**:
  - "Just 5 minutes reading requirements"
  - Lowers activation energy for task initiation

- ✅ **Clear ADHD accommodations**:
  - 5-15 minute tasks (perfect for focus windows)
  - Simple descriptions (≤10 words)
  - Progressive complexity
  - Clear dependencies

**Issues**:
- ⚠️ **Pattern matching is keyword-based**:
  - May miss tasks that don't fit predefined patterns
  - Could add NLP or LLM-based analysis (Pal planner integration missing)
  - Generic fallback only uses time chunking

- ⚠️ **No Pal planner integration**:
  - Code mentions "Pal" in decomposition_coordinator.py
  - But actual Pal planner call is NOT implemented
  - Would provide smarter, AI-driven decomposition

- ⚠️ **Order optimization could be smarter**:
  - Currently respects dependencies and energy level
  - Could consider: task dependencies, prerequisites, learning curve

#### Component 3b: Decomposition Coordinator

**Purpose**: Orchestrates decomposition between ADHD Engine and Task Orchestrator

**Features**:
```
Auto-decomposition triggers:
1. Time-based: >120 minutes
2. Complexity-based: complexity_score > 0.6
3. Keyword-based: "refactor", "migrate", "integrate", etc.
4. Paralysis detection: TODO for >24 hours
5. Procrastination pattern: (Future - not implemented)

Consent flow:
   [Detect complex task]
         ↓
   [Check user state]
      - Hyperfocus? → Queue for later
      - Low energy? → Minimal message
      - Normal? → Detailed explanation
         ↓
   [Request consent] → Y/N/Preview
         ↓
   [If approved] → Call Task Orchestrator
         ↓
   [Task Orchestrator] → Pal planner / Pattern fallback
         ↓
   [ConPort persistence + Leantime sync]
```

**Strengths**:
- ✅ **Smart auto-detection**:
  - Multiple trigger conditions
  - Doesn't interrupt hyperfocus
  - Respects energy levels

- ✅ **Consent-first design**:
  - Never forces decomposition
  - Adaptive messaging based on energy
  - Preview option before committing

- ✅ **Clear architecture**:
  - DecompositionRequest dataclass
  - Well-defined separation of concerns
  - Coordinator bridges ADHD Engine ↔ Task Orchestrator

**Critical Issues**:
- ❌ **Task Orchestrator integration incomplete**:
  - Code calls `orch_client.request_decomposition()` (line 352)
  - But Task Orchestrator doesn't have this endpoint!
  - Will fail at runtime

- ❌ **Pal planner never called**:
  - Mentions "method='pal'" (line 335)
  - But no actual Pal planner HTTP call or SDK integration
  - Falls back to pattern matching silently

- ❌ **ConPort persistence missing**:
  - Decomposition creates subtasks
  - But never logs to ConPort decision graph
  - Event emission happens (line 363) but no ConPort link

- ⚠️ **Procrastination pattern not implemented**:
  - Code has TODO comment (line 153-157)
  - Feature partially designed but never finished

#### Component 3c: Task Decomposition Event Listener

**Purpose**: Listens to task events and triggers auto-decomposition

**Features**:
```
EventBus (dopemux:events)
    ↓
Listen for: ["task.created", "task.updated"]
    ↓
Filter events:
  - Drop non-task events
  - Drop events from adhd-engine (avoid loops)
  - Drop already-decomposed tasks
    ↓
Pass to Coordinator:
  - should_auto_decompose()
  - request_decomposition_consent()
  - decompose_task()
    ↓
Background process (asyncio.create_task)
```

**Strengths**:
- ✅ **Event-driven architecture**:
  - Non-blocking (async)
  - Background listening
  - Self-healing (restarts on error)

- ✅ **Loop prevention**:
  - Ignores events from adhd-engine
  - Checks "decomposed" metadata flag

- ✅ **Graceful error handling**:
  - Catches exceptions per event
  - Logs but continues listening
  - Auto-restart after errors

**Issues**:
- ⚠️ **Event source validation weak**:
  - Only checks `source == "adhd-engine"`
  - What if multiple ADHD engines exist?
  - Could add source UUID or hostname

- ❌ **Missing metadata propagation**:
  - Sets task `metadata.decomposed = True` check (line 172)
  - But who actually sets this metadata?
  - Task Orchestrator update missing

- ❌ **No progress tracking**:
  - Listener starts, but no way to monitor status
  - No event published when decomposition starts/completes
  - User never knows decomposition happened

---

## 🔗 Integration Analysis

### Current Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TASK LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────────┘

User creates task in Leantime/CLI
    ↓
Task Orchestrator stores task
    ↓
Task Orchestrator publishes "task.created" event
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    ⚠️  GAP 1: Event Loss                             │
│ - TaskOrchestratorEventEmitter is NOT subscribed to task.created    │
│ - Bridge only EMITS progress/completion, doesn't RECEIVE task.creat │
│ - Task Packet system has no hook into task creation                 │
└──────────────────────────────────────────────────────────────────────┘
    ↓
Event reaches EventBus
    ↓
TaskDecompositionEventListener subscribes
    ↓
DecompositionCoordinator.should_auto_decompose()
    ├─ Analyzes complexity ✅
    └─ Returns (true/false, reason) ✅
    ↓
If complex: request_decomposition_consent()
    ├─ Checks ADHD state ✅
    └─ Asks user permission ✅
    ↓
If approved: decompose_task()
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│            ❌ CRITICAL: Missing Task Orchestrator Call               │
│ decompose_task() calls:                                              │
│   await orch_client.request_decomposition(task_id=task_id, ...)      │
│                                                                       │
│ But Task Orchestrator has NO /decompose endpoint!                   │
│ - Endpoint not defined in task-orchestrator service                 │
│ - Will timeout or 404 at runtime                                    │
└──────────────────────────────────────────────────────────────────────┘
    ↓
(If endpoint existed)
    ↓
Task Orchestrator would:
  1. Call Pal planner → Get AI-driven decomposition ✅ (theory)
  2. Create subtasks ✅ (theory)
  3. Persist to ConPort ❌ (no event / callback)
  4. Sync to Leantime ❌ (no endpoint)
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│              ⚠️  GAP 2: ConPort Disconnection                        │
│ - Decomposition creates subtasks in memory                           │
│ - No log_decision() to ConPort                                       │
│ - No decision genealogy tracked                                      │
│ - Progress tracking disconnected from session context                │
└──────────────────────────────────────────────────────────────────────┘
    ↓
Task Orchestrator would emit "decomposition.completed" event
    ↓
┌──────────────────────────────────────────────────────────────────────┐
│          ⚠️  GAP 3: Task Packet Disconnection                        │
│ - Task completion event fired                                        │
│ - But collect_task_packet.py never notified                          │
│ - When complex task blocked, no investigation packet triggered       │
│ - Debug artifacts exist but never linked to task context             │
└──────────────────────────────────────────────────────────────────────┘
    ↓
(End of currently implemented flow)
    ↓
What SHOULD happen:
    ├─ Event reaches TaskOrchestratorEventEmitter
    │   ├─ Emits task.completed event ✅ (implemented)
    │   └─ Calls ConPort to log completion ❌ (missing)
    │
    ├─ Event triggers Task Packet collection
    │   ├─ Collects logs for debugging ✅ (functionality exists)
    │   └─ Links packet to task context ❌ (missing)
    │
    └─ Event updates ADHD Engine metrics
        └─ Feeds back into energy/attention prediction ❌ (missing)
```

### Integration Gap Summary

| Connection | Source | Target | Status | Impact |
|-----------|--------|--------|--------|--------|
| **Task creation** | Leantime | Task Orchestrator | ✅ | Core flow works |
| **Event emission (task→progress)** | Task Orchestrator | EventBus | ✅ | Progress tracking possible |
| **Event subscription (progress→bridge)** | EventBus | Orchestrator Bridge | ❌ MISSING | Events not persisted |
| **Auto-decomposition trigger** | EventBus | Decomposition Listener | ⚠️ INCOMPLETE | Only detects, doesn't execute |
| **Decomposition request** | Coordinator | Task Orchestrator | ❌ MISSING | No /decompose endpoint |
| **ConPort persistence** | Task Orchestrator | ConPort | ❌ MISSING | No decision logging |
| **Task Packet generation** | Task blocking | Task Packet Collector | ❌ MISSING | No investigation artifacts |
| **ADHD state feedback** | Task metrics | ADHD Engine | ❌ MISSING | No adaptive learning |

---

## 🎯 Quality Assessment

### Architecture Patterns

#### ✅ Good Patterns

1. **Event-Driven Architecture**
   - Systems communicate via EventBus
   - Loose coupling, high cohesion
   - Good for microservices

2. **Consent-First ADHD Design**
   - Never forces decomposition
   - Respects hyperfocus state
   - Adaptive messaging

3. **Pattern-Based Task Decomposition**
   - Handles common task types
   - Respects dependencies
   - Energy-aware scheduling

4. **Multi-Source Artifact Collection**
   - Comprehensive debugging
   - Graceful degradation
   - Well-organized output

#### ⚠️ Problematic Patterns

1. **Missing Service-to-Service Contracts**
   - Coordinator calls `request_decomposition()` endpoint that doesn't exist
   - No specification document
   - Will cause runtime failures

2. **Incomplete Integration Points**
   - Events emitted but never consumed
   - Persistence missing
   - No feedback loops

3. **Hard-Coded Assumptions**
   - Task Orchestrator URL hardcoded ("http://localhost:8000")
   - No service discovery
   - Port 8000 assumption fragile

4. **Type Safety Gaps**
   - Event Bus returns generic Dict[str, Any]
   - No type validation of event structure
   - Easy to miss required fields

### Code Quality Metrics

| Metric | Rating | Notes |
|--------|--------|-------|
| **Type Hints** | ✅ Good | Present throughout, proper use of Optional, Tuple |
| **Error Handling** | ✅ Good | Try/except blocks, logging, graceful degradation |
| **Testability** | ⚠️ Fair | Dependencies make unit testing hard; needs mocking |
| **Documentation** | ✅ Good | Docstrings present, README.md workflow documented |
| **ADHD Awareness** | ✅ Excellent | Complexity scoring, energy tracking, consent patterns |
| **Completeness** | ❌ POOR | Multiple 70-80% implementations with TODOs |
| **Integration** | ❌ POOR | Systems exist but don't talk to each other |

### Complexity Analysis

```python
# High-complexity areas (>0.6 ADHD score):

1. DecompositionCoordinator.should_auto_decompose()
   - 5 separate trigger conditions
   - Complex timestamp parsing
   - Multiple return paths
   Recommendation: Extract to separate condition checkers

2. TaskDecompositionAssistant._generate_micro_tasks()
   - 4 pattern branches (Implementation, Refactor, Bug, Generic)
   - Each with 5+ subtasks
   - Could extract to pattern factory

3. collect_service_logs()
   - Nested loops: services → commands → log parsing → JSON conversion
   - Multiple data structures
   Recommendation: Create LogParser class
```

---

## 🚀 Missing Implementations

### Critical (Blocking)

1. **Task Orchestrator `/decompose` Endpoint**
   ```python
   # In services/task-orchestrator/endpoints.py (MISSING)
   @app.post("/decompose/{task_id}")
   async def request_decomposition(
       task_id: str,
       method: str = "pal",  # pal, pattern, manual
       adhd_context: Dict = None
   ):
       """Request task decomposition via Pal planner or pattern fallback"""
       # 1. Get task from storage
       # 2. Call Pal planner API
       # 3. Create subtasks
       # 4. Call ConPort log_decision()
       # 5. Sync to Leantime
       # 6. Emit decomposition.completed event
   ```

2. **Task Orchestrator Event Subscription**
   ```python
   # In TaskOrchestratorEventEmitter (MISSING - only emit exists)
   async def subscribe_to_events(self) -> None:
       """Subscribe to task.created, task.updated for ConPort persistence"""
       async for event in event_bus.subscribe("task.*"):
           if event.type == "task.created":
               await self.persist_to_conport(event.data)
           elif event.type == "decomposition.completed":
               await self.emit_task_progress_updated(...)
   ```

3. **ConPort Integration Callback**
   ```python
   # In decompose_task() method (MISSING)
   # After creating subtasks:
   await conport_client.log_decision(
       summary=f"Decomposed task {task_id} into {len(subtask_ids)} subtasks",
       rationale="High complexity detected by ADHD Engine",
       implementation_details={
           "method": method,
           "subtask_ids": subtask_ids,
           "complexity_score": complexity_score,
           "adhd_context": adhd_context
       },
       tags=["task-decomposition", "adhd-enablement", f"complexity-{complexity_score:.1f}"]
   )
   ```

4. **Task Packet Triggering on Task.Blocked**
   ```python
   # In TaskOrchestratorEventEmitter (MISSING)
   async def emit_task_blocked(self, ...):
       # Existing code...

       # NEW: Trigger investigation packet
       try:
           await packet_collector.collect(
               task_id=task_id,
               reason=blocker_reason,
               services="all"  # Collect full system state
           )
       except Exception:
           logger.warning("Could not collect investigation packet")
   ```

### High Priority (Enabling)

5. **Pal Planner Integration**
   ```python
   # In Task Orchestrator decomposition endpoint
   async def call_pal_planner(task_description: str, constraints: Dict) -> List[MicroTask]:
       """Call Pal planner API for AI-driven decomposition"""
       async with aiohttp.ClientSession() as session:
           response = await session.post(
               f"{PAL_URL}/decompose",
               json={"description": task_description, "constraints": constraints}
           )
           return response.json()["subtasks"]
   ```

6. **Leantime Sync Completion**
   ```python
   # In Task Orchestrator (MISSING the "sync" part)
   async def sync_subtasks_to_leantime(task_id: str, subtask_ids: List[str]):
       """Create child tickets in Leantime"""
       leantime_client = LeanTimeClient()
       for subtask_id in subtask_ids:
           await leantime_client.create_child_ticket(
               parent_id=task_id,
               title=subtask.title,
               description=subtask.description,
               estimate_hours=subtask.estimated_minutes / 60
           )
   ```

### Medium Priority (Nice-to-Have)

7. **Procrastination Pattern Detection**
   ```python
   # In DecompositionCoordinator (TODO at line 153)
   if self.procrastination_detector:
       pattern = await self.procrastination_detector.check_procrastination(task_id)
       if pattern and pattern.pattern_type in ["decision_paralysis", "overwhelm_avoidance"]:
           return (True, f"Procrastination pattern detected: {pattern.pattern_type}")
   ```

8. **Task Metadata Propagation**
   ```python
   # After successful decomposition, mark original task
   await task_orchestrator.update_task(
       task_id=task_id,
       metadata={"decomposed": True, "subtask_ids": subtask_ids}
   )
   ```

---

## 🔧 Recommended Fixes (Priority Order)

### Phase 1: Unblock Execution (1 day)

1. **Create Task Orchestrator `/decompose` endpoint**
   - Allow decomposition requests to complete
   - Can use pattern fallback initially (Pal planner is optional)
   - Returns {parent_task_id, subtask_ids, total_time}

2. **Fix hardcoded URLs and ports**
   ```python
   # Use environment variables
   task_orchestrator_url = os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:8000")
   conport_url = os.getenv("CONPORT_URL", "http://localhost:3004")
   ```

3. **Add ConPort logging to decomposition**
   - Call `log_decision()` when decomposition completes
   - Enables decision tracking and ADHD state persistence

### Phase 2: Complete Integration (3 days)

4. **Implement bidirectional Task Orchestrator Bridge**
   - Subscribe to decomposition.completed events
   - Emit task.progress events on subtask updates
   - Link to ConPort decision graph

5. **Connect Task Packet collection to task blocking**
   - When task.blocked event fired, trigger packet collection
   - Store packet reference in ConPort decision
   - Create investigation workflow link

6. **Implement Leantime sync**
   - Create child tickets in Leantime when decomposing
   - Update parent ticket with link to breakdown
   - Keep estimates in sync

### Phase 3: ADHD Optimization (2 days)

7. **Add Pal planner integration**
   - Call Pal for AI-driven decomposition
   - Compare with pattern fallback
   - Use best result

8. **Implement feedback loop**
   - Track which decomposition methods work best
   - Feed into ADHD Engine learning
   - Adjust complexity scoring over time

9. **Add procrastination detection**
   - Monitor tasks in TODO for >24h
   - Track skip/postponement patterns
   - Auto-trigger decomposition

---

## 📋 Specific Code Recommendations

### Fix 1: Complete Decomposition Coordinator

```python
# FILE: services/adhd_engine/domains/task_enablement/decomposition_coordinator.py
# LINES: 352-358 (CURRENT)

# BEFORE:
breakdown = await orch_client.request_decomposition(
    task_id=task_id,
    adhd_context=adhd_context,
    method=orch_method,
    max_subtasks=max_subtasks,
    target_duration_minutes=target_duration
)

# AFTER:
try:
    breakdown = await orch_client.request_decomposition(
        task_id=task_id,
        adhd_context=adhd_context,
        method=orch_method,
        max_subtasks=max_subtasks,
        target_duration_minutes=target_duration
    )
except HTTPException as e:
    if e.status_code == 404:
        # Fallback: Use pattern-based decomposition
        logger.warning("Task Orchestrator /decompose not available, using pattern fallback")
        decomposition = self.decomposer.decompose_task(
            task_id=task_id,
            task_description=task.get("description", ""),
            time_estimate=task.get("estimated_minutes"),
            current_energy=adhd_context.get("energy_level", "medium")
        )
        breakdown = {
            "parent_task_id": task_id,
            "subtask_ids": [mt.task_id for mt in decomposition.micro_tasks],
            "subtasks": [asdict(mt) for mt in decomposition.micro_tasks],
            "total_estimated_minutes": decomposition.total_estimated_minutes,
            "method": "pattern_fallback",
            "leantime_synced": False,
            "conport_persisted": False
        }
    else:
        raise
```

### Fix 2: Add ConPort Decision Logging

```python
# FILE: services/adhd_engine/domains/task_enablement/decomposition_coordinator.py
# ADD: After breakdown is obtained (line 360)

# Log decision to ConPort
if hasattr(self, 'conport_client'):  # Optional
    try:
        complexity_score = self._complexity_level_to_score(complexity_level)
        await self.conport_client.log_decision(
            workspace_id=adhd_context.get("workspace_id", ""),
            summary=f"Decomposed high-complexity task '{task.get('description', '')[:60]}...'",
            rationale=(
                f"Task complexity score: {complexity_score:.2f} ({complexity_level.value}). "
                f"Trigger: {reason}"
            ),
            implementation_details={
                "method": method,
                "subtask_count": len(breakdown.get("subtask_ids", [])),
                "total_estimated_minutes": breakdown.get("total_estimated_minutes"),
                "complexity_score": complexity_score,
                "adhd_context": adhd_context,
                "subtask_ids": breakdown.get("subtask_ids", [])
            },
            tags=[
                "task-decomposition",
                "adhd-enablement",
                f"complexity-{complexity_score:.1f}",
                f"method-{method}"
            ]
        )
        logger.info(f"Logged decomposition decision to ConPort for task {task_id}")
    except Exception as e:
        logger.error(f"Could not log decision to ConPort: {e}")
```

### Fix 3: Environment-Based Configuration

```python
# FILE: services/adhd_engine/domains/task_enablement/decomposition_coordinator.py
# REPLACE: Hardcoded task_orchestrator_url parameter

import os

class DecompositionCoordinator:
    def __init__(
        self,
        decomposer: TaskDecompositionAssistant,
        task_orchestrator_url: Optional[str] = None,
        bridge_client = None,
        adhd_state_provider: Optional[Callable[...]] = None,
        consent_provider: Optional[Callable[...]] = None,
    ):
        # Use provided URL, fallback to env, fallback to localhost
        self.task_orchestrator_url = (
            task_orchestrator_url or
            os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:8000")
        )
        self.conport_url = os.getenv("CONPORT_URL", "http://localhost:3004")
        # ... rest of init
```

---

## 📚 Testing Recommendations

### Unit Tests Needed

```python
# test_decomposition_coordinator.py
class TestDecompositionCoordinator:
    @pytest.mark.asyncio
    async def test_should_auto_decompose_triggers(self):
        """Test all auto-decompose conditions"""
        coordinator = DecompositionCoordinator(...)

        # Test time-based trigger
        result = await coordinator.should_auto_decompose(
            {"estimated_minutes": 150},
            {}
        )
        assert result[0] == True

        # Test complexity-based trigger
        result = await coordinator.should_auto_decompose(
            {"description": "Refactor authentication system"},
            {}
        )
        assert result[0] == True
```

### Integration Tests Needed

```python
# test_taskx_integration.py
class TestTaskXIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_decomposition_flow(self):
        """Test: Create task → Detect complexity → Decompose → Persist"""
        # 1. Create task
        # 2. Task Orchestrator emits task.created
        # 3. Event Listener receives it
        # 4. Coordinator detects complexity
        # 5. User consents
        # 6. Decomposition happens
        # 7. ConPort logs decision
        # 8. Subtasks created in Leantime
```

---

## 🎓 Knowledge Gaps & Learning Needed

1. **Task Orchestrator API Specification** ❓
   - Does `/decompose` endpoint exist?
   - What does `request_decomposition()` expect?
   - Who should implement Pal planner call?

2. **ConPort Client Library** ❓
   - How to instantiate `conport_client`?
   - Is it already available in codebase?
   - Authentication/workspace_id handling?

3. **Leantime Integration** ❓
   - Where is Leantime sync implemented?
   - Does Task Orchestrator have Leantime client?
   - Parent-child ticket relationships?

4. **Pal Planner API** ❓
   - Where is it documented?
   - Endpoint for decomposition requests?
   - Response format and constraints?

---

## ✅ Summary: To Make This Work

### Immediate Actions (Next Session)

- [ ] **Check if Task Orchestrator has `/decompose` endpoint**
  - If not, create one or update decomposition_coordinator.py to use fallback

- [ ] **Verify ConPort client availability**
  - Search for existing `ConPortClient` in codebase
  - Add imports if needed

- [ ] **Document Task Packet triggering logic**
  - When should packets be collected?
  - Link to task context for debugging

### Implementation Checklist

- [ ] Fix hardcoded URLs (use environment variables)
- [ ] Add ConPort integration to decomposition
- [ ] Complete Task Orchestrator event subscription
- [ ] Implement Task Packet collection on task.blocked
- [ ] Add Pal planner integration (optional Phase 2)
- [ ] Write integration tests
- [ ] Update ADR with final architecture

### Documentation Needed

- [ ] Service-to-service API contracts (OpenAPI specs)
- [ ] Event schema definitions
- [ ] Configuration guide (environment variables)
- [ ] Troubleshooting guide for decomposition failures

---

## 🏁 Conclusion

**Current Status**: ⚠️ **PARTIALLY INTEGRATED, INCOMPLETE**

The three systems are well-designed individually but lack proper end-to-end integration:

1. ✅ **Task Packet System** - Works standalone, comprehensive artifact collection
2. ⚠️ **Orchestrator Bridge** - Events emitted, but subscription/persistence missing
3. ⚠️ **ADHD Task Enablement** - Decomposition logic solid, but Task Orchestrator integration incomplete

**Primary Issue**: Decomposition coordinator calls a Task Orchestrator endpoint (`/decompose`) that doesn't exist. This blocks the entire flow at runtime.

**Fix Complexity**: **2-3 days of development** to complete all integrations properly.

**Recommendation**: **Prioritize creating Task Orchestrator `/decompose` endpoint** and adding ConPort persistence. This unblocks the ADHD decomposition feature and enables proper task tracking.

---

**Next Steps**:
1. Read this analysis with architecture/backend team
2. Clarify missing service endpoints and APIs
3. Create detailed implementation plan for Phase 1 (blocking issues)
4. Schedule 2-day sprint to complete integration
