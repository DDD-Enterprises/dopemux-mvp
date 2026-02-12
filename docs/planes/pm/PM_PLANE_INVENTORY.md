---
id: PM_PLANE_INVENTORY
title: Pm Plane Inventory
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Pm Plane Inventory (explanation) for dopemux documentation and developer workflows.
---
# PM Plane Inventory (Phase 0)

**Status**: ✅ EVIDENCE ANALYSIS COMPLETE
**Evidence Base**: PM-INV-00 outputs (git rev: `c408189`)
**Analysis Date**: 2026-02-11

## Scope
Phase 0 only. Inventory and reality check. No design.

## Evidence bundle pointers
- Evidence outputs folder: `docs/planes/pm/_evidence/PM-INV-00.outputs/`
- Command list: `docs/planes/pm/_evidence/PM-INV-00.commands.txt`

---

## Observed components (Verified)

| Component | Location | Purpose (Observed) | Entry points | Storage | Task model | States | Integrations | Tests | Evidence |
|-----------|----------|-------------------|--------------|---------|------------|--------|--------------|-------|----------|
| **task-orchestrator** | `services/task-orchestrator/` | ADHD-aware task management with ConPort/Leantime sync | FastAPI MCP server (port 8000) | ConPort (via MCP), Leantime (via JSON-RPC) | `OrchestrationTask` | PENDING, IN_PROGRESS, COMPLETED, NEEDS_BREAK, FAILED | ConPort, Leantime, EventBus, ADHD Engine | ❌ None | `enhanced_orchestrator.py:1705-1715`, `models.py:34-41` |
| **taskmaster** | `services/taskmaster/` | Legacy task manager with EventBus integration | MCP server | Local filesystem (.taskmaster/) | Not explicitly defined | Unknown | EventBus, ConPort (mentioned, not wired) | ❌ None | `server.py:28-81`, `bridge_adapter.py:81-303` |
| **dopemux CLI** | `src/dopemux/cli.py` | CLI orchestration layer | CLI commands | Filesystem | `TaskRecord` (ADHD) | PENDING, IN_PROGRESS, COMPLETED, FAILED | TaskMaster bridge, EventBus | ⚠️ Exists (`tests/`) | `adhd/task_decomposer.py:31-81` |
| **EventBus** | `src/dopemux/event_bus.py` | Redis Streams event coordination | Abstract API with adapters | Redis Streams (TTL-based) | N/A | N/A | All services (pub/sub) | ❌ None | `event_bus.py:68-166` |
| **Leantime** | External (Docker) | PM platform (Kanban, projects, tickets) | JSON-RPC API (port 80) | MySQL + Redis | Leantime native | Leantime states | task-orchestrator (sync) | External | `compose.yml:148-187`, `leantime_jsonrpc_client.py:40-360` |
| **working-memory-assistant** | `services/working-memory-assistant/` | EventBus consumer for memory ingestion | FastAPI + EventBus consumer | Chronicle (SQLite), Redis Streams | N/A | N/A | EventBus (activity.events.v1 → memory.derived.v1) | ✅ Yes | `eventbus_consumer.py:210-519` |

**Key Finding**: **THREE SEPARATE TASK MODELS** exist with no unified lifecycle management.

---

## Task lifecycle inventory (Verified)

| System | Canonical task object name | Status/state representation | Transition function(s) | Idempotency strategy | Evidence |
|--------|----------------------------|----------------------------|----------------------|---------------------|----------|
| **task-orchestrator** | `OrchestrationTask` (dataclass) | `TaskStatus` enum: PENDING, IN_PROGRESS, COMPLETED, NEEDS_BREAK, FAILED, BLOCKED | `_map_leantime_status()`, `_sync_to_conport()`, status mapping functions | ConPort progress_entry is source of truth; Leantime sync via `leantime-synced` tag | `enhanced_orchestrator.py:1682-1715`, `schema_mapping.py:325-330` |
| **taskmaster** | Implicit (not defined as class) | Unknown (bridge emits events with status field) | EventBus publish on status changes | Unknown - no ConPort integration found | `bridge_adapter.py:81-303`, `server.py:52` |
| **dopemux CLI (ADHD)** | `TaskRecord` (dataclass) | `TaskStatus` enum: PENDING, IN_PROGRESS, COMPLETED, FAILED | `start_task()`, `complete_task()`, `update_progress()` | Filesystem-based (.taskmaster/ directory) | `task_decomposer.py:31-81`, `task_decomposer.py:188-228` |

**Critical Gap**: Three independent task systems with different state models and no synchronization mechanism.

---

## Event producers/consumers (Verified)

| Producer | Consumer | Stream/topic | Event types | Payload shape | Determinism risks | Evidence |
|----------|----------|-------------|-------------|---------------|------------------|----------|
| **taskmaster** | EventBus subscribers | Redis Streams (unspecified) | task_created, task_updated, task_completed | `DopemuxEvent` with Priority, CognitiveLoad, ADHDMetadata | ⚠️ Events not persisted beyond Redis TTL | `server.py:74-154`, `bridge_adapter.py:81-303` |
| **working-memory-assistant** | EventBus subscribers | `memory.derived.v1` | decision.logged, task.completed, task.failed, workflow.phase_changed | Chronicle schema fields | ✅ Persisted to SQLite | `eventbus_consumer.py:36-519` |
| **task-orchestrator** | ConPort, EventBus | `dopemux:events` (via event_coordinator) | task_updated, decision_logged, progress_changed | `CoordinationEvent`, `SyncEvent` | ✅ ConPort provides persistence | `event_coordinator.py:21-627`, `enhanced_orchestrator.py:2127-2201` |
| **ADHD orchestrator** | EventBus subscribers | Redis Streams | attention_state_changed | Attention metrics (AttentionState enum) | ⚠️ Ephemeral (Redis only) | `adhd_orchestrator.py:95-116` |

**Key Finding**: EventBus is **coordination layer only**, NOT canonical PM state source. ConPort provides durable storage.

---

## Cross-plane wiring (Verified)

| PM component | Memory/Chronicle | DopeQuery/ConPort | ADHD Engine | Notes | Evidence |
|--------------|-----------------|------------------|-------------|-------|----------|
| **task-orchestrator** | ❌ No direct wire | ✅ Via `ConPortEventAdapter` | ✅ Via `adhd_prioritization` | ConPort is **mandatory** (`profile_models.py` validator); syncs progress_entry on task create/update | `enhanced_orchestrator.py:1927-1940`, `conport_adapter.py:145`, `profile_models.py:193-198` |
| **taskmaster** | ❌ No direct wire | ⚠️ Mentioned in docs but not wired in code | ❌ No integration | Bridge publishes to EventBus; **no ConPort API calls found** | `server.py:52` (comment only), `bridge_adapter.py` (no ConPort imports) |
| **working-memory-assistant** | ✅ Chronicle (SQLite) | ❌ No integration | ❌ No integration | Consumes EventBus → writes to Chronicle; **no feedback loop to PM systems** | `eventbus_consumer.py:210-262`, `chronicle/schema.sql` |
| **dopemux CLI** | ❌ No direct wire | ⚠️ Via TaskMaster bridge (weak) | ✅ Via `attention_monitor` | CLI delegates to taskmaster; **no ConPort API calls in CLI code** | `task_decomposer.py`, `adhd_orchestrator.py:95-116` |

**Critical Finding**: Only `task-orchestrator` has **bidirectional ConPort sync**. Other PM components operate in isolation.

---

## Resolved Questions (Phase 0)

### Q1: What is the PM canonical status source (Leantime vs internal)?

**Answer**: ✅ **ConPort** is the canonical source, NOT Leantime.

**Evidence**:
- `profile_models.py:193-198`: ConPort is **required** in all profiles (validator enforces "conport required in all profiles (memory authority)")
- `enhanced_orchestrator.py:2106-2112`: task-orchestrator creates ConPort `progress_entry` as source of truth on task creation
- `schema_mapping.py:105-221`: Leantime sync is **opt-in** via `leantime-synced` tag
- `app/core/sync.py:833-845`: Bidirectional status mapping (ConPort ↔ Leantime)

**Leantime Role**: External PM view layer for human operators; **not** authoritative for Dopemux internal state.

---

### Q2: Are decisions linked to tasks in a canonical store?

**Answer**: ✅ **YES**, via ConPort `link_conport_items()` and `progress_entry.linked_item_id`.

**Evidence**:
- `enhanced_orchestrator.py:2384-2561`: task-orchestrator logs decisions via ConPort and links them to tasks
- `conport_adapter.py:145`: ConPort adapter creates progress_entry with `linked_item_type="decision"` and `linked_item_id`
- `event_coordinator.py:536-627`: ConPort tracking setup on coordination events with target_systems=["conport"]

**Gap**: Taskmaster and CLI **do not** link decisions to tasks (no ConPort integration).

---

### Q3: Does event bus persist PM events?

**Answer**: ⚠️ **PARTIAL** - Raw events ephemeral, derived events persisted via Chronicle.

**Evidence**:
- `event_bus.py:127-166`: Redis Streams adapter (TTL-based, not durable beyond Redis persistence)
- `eventbus_consumer.py:262-519`: working-memory-assistant **persists** high-signal events to Chronicle SQLite
- Promotable event types: `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `manual.memory_store`, `workflow.phase_changed`

**Determinism Strategy**:
- Use Chronicle for durable memory of high-signal events
- Use EventBus for real-time coordination only
- ConPort is authoritative for task/decision state

---

## Unknown or Missing (Phase 0)

| Question | Why it matters | How to resolve (exact file/command) | Priority |
|----------|---------------|-------------------------------------|----------|
| ❓ How do taskmaster and CLI tasks sync to ConPort? | Prevents orphaned tasks not visible to task-orchestrator | Audit `src/dopemux/integrations/taskmaster_bridge.py` and `src/dopemux/adhd/task_decomposer.py` for ConPort API calls (likely **missing**) | 🔴 HIGH |
| ❓ What is the Leantime ↔ ConPort sync frequency? | Determines state drift window | Check `services/task-orchestrator/app/core/sync.py` for polling interval/webhook config | 🟡 MEDIUM |
| ❓ Are EventBus events replayed on restart? | Determines recovery strategy after crashes | Check Redis Streams consumer group persistence in `eventbus_consumer.py:267` and Redis persistence config | 🟡 MEDIUM |
| ❓ What happens if ConPort is unavailable? | Service resilience and degraded-mode behavior | Search for fallback/circuit-breaker logic in `conport_adapter.py` and `enhanced_orchestrator.py` | 🔴 HIGH |
| ❓ How are conflicting status updates resolved (ConPort vs Leantime)? | Prevents state corruption from race conditions | Inspect `_map_status_*` functions in `sync.py:833-845` for conflict resolution (last-write-wins vs merge logic) | 🟡 MEDIUM |
| ❓ What is the task model for taskmaster? | Needed to unify with OrchestrationTask and TaskRecord | Deep-dive `services/taskmaster/server.py` and `bridge_adapter.py` for implicit task schema | 🔴 HIGH |

---

## Critical Gaps Summary

### 🔴 High Priority
1. **No unified task model** - 3 separate systems (task-orchestrator, taskmaster, CLI) with incompatible schemas
2. **Taskmaster has no ConPort integration** - mentioned in comments but not wired; tasks orphaned from canonical store
3. **CLI tasks do not sync to ConPort** - CLI-created tasks invisible to task-orchestrator
4. **No PM-specific tests** - Zero coverage for task lifecycle, ConPort sync, Leantime sync
5. **ConPort unavailability handling unknown** - Resilience strategy not documented

### 🟡 Medium Priority

1. **Leantime sync logic not fully audited** - Conflict resolution strategy unclear
2. **EventBus replay strategy unknown** - Recovery after service restarts not documented
3. **working-memory-assistant has no feedback to PM** - One-way EventBus → Chronicle with no task updates

### 🟢 Low Priority

1. **Attention state changes ephemeral** - ADHD engine state not persisted beyond Redis

---

## Tests Inventory (PM-Related)

**Status**: ❌ **CRITICAL GAP - NO PM-SPECIFIC TESTS**

**Test directories that exist**:
- `services/working-memory-assistant/tests/` - EventBus consumer tests only
- `tests/` (root) - Unknown coverage for PM components

**Missing (critical)**:
- ❌ `services/task-orchestrator/tests/` - **Directory does not exist**
- ❌ `services/taskmaster/tests/` - **Directory does not exist**
- ❌ No integration tests for ConPort ↔ Leantime sync
- ❌ No lifecycle transition tests for `TaskStatus` enums
- ❌ No ConPort adapter tests
- ❌ No EventBus producer/consumer integration tests for PM events

**Evidence**: `PM-INV-00.outputs/06_tests_dirs.txt` - no task-orchestrator or taskmaster test directories found

---

## Next Phase Recommendation

**Phase 1 Focus**: Task Model Unification & ConPort Integration Gaps

**Rationale**:
- Cannot proceed with PM plane design until task model conflicts resolved
- ConPort integration gaps create orphaned tasks and broken traceability
- Test coverage required before any refactoring work

**Proposed Phase 1 Investigations**:
1. **PM-INV-01**: Deep-dive taskmaster task model (identify implicit schema)
2. **PM-INV-02**: Audit ConPort integration patterns across all PM components
3. **PM-INV-03**: Design unified task model (compatible with all 3 systems)
4. **PM-FRIC-01**: Map friction points in current multi-system architecture

---

## Appendix: Service Registry

From `services/registry.yaml` and `compose.yml`:

| Service | Port | Purpose | PM Role |
|---------|------|---------|---------|
| task-orchestrator | 8000 | ADHD-aware task management | Primary PM service |
| leantime | 80 | External PM platform | Human UI/view layer |
| mysql_leantime | 3306 | Leantime database | Leantime persistence |
| redis_leantime | 6379 | Leantime cache | Leantime cache |
| leantime-bridge | 3015 | MCP bridge for Leantime API | JSON-RPC → MCP adapter |

**Note**: taskmaster not in Docker Compose (local MCP server only).
