---
id: PM_FRICTION_MAP
title: Pm Friction Map
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: PM plane friction analysis documenting cognitive load, state drift, and integration friction points.
---
# PM Friction Map (Phase 1)

**Status**: Phase 1 Complete (Evidence-Based)
**Analysis Date**: 2026-02-12
**Evidence Location**: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`

## Overview

This document maps friction points where the PM plane breaks developer cognition and flow. Focus areas: creation friction, state drift, duplicate representations, missing decision linkage.

**Evidence Summary**:
- 1,710 lines of task state management patterns analyzed
- 281 lines of memory burden indicators found
- 11 core source files examined
- Test coverage gap identified (taskmaster: 0 root tests)

## Friction Points Table

| Friction | Symptom | User Cost | Evidence |
|----------|---------|-----------|----------|
| **Multiple Task Creation APIs** | User must choose: task-orchestrator, taskmaster, dopemux-gpt-researcher, or task-router | Decision fatigue, API confusion, inconsistent task creation | `20_friction_search.txt:7-100` (6+ task creation patterns), `nl_services_taskmaster_bridge_adapter.py.txt:57-69`, `nl_services_task-orchestrator_conport_mcp_client.py:85-108` |
| **Status String Proliferation** | Hardcoded status strings ("TODO", "IN_PROGRESS", "DONE", "BLOCKED") scattered across services | Memory burden, typo risk, no validation, state drift | `20_friction_search.txt:4-27` (36 status= assignments), `30_memory_burden_search.txt:4-54` (status mapping sprawl) |
| **Manual Task ID Tracking** | Operations require explicit task_id parameter with no discovery mechanism | Must remember IDs, context switching overhead, lost work risk | `30_memory_burden_search.txt:72-81` (user_id required, provide task_id), `20_friction_search.txt:96-108` |
| **Missing Validation Guidance** | "missing required fields" errors without upfront field specification | Trial-and-error creation, wasted time, frustration | `30_memory_burden_search.txt:12-24` (missing id/title/status checks), `nl_services_task-orchestrator_app_adapters_conport_adapter.py.txt:103-187` |
| **Duplicate Task Management Logic** | Same functionality in multiple services: create_task, add_task, new_task, upsert | Code duplication, maintenance burden, behavior drift | `20_friction_search.txt:86-100` (create_task in 3+ services), `20_friction_search.txt:61-69` (status transitions duplicated) |
| **Manual Conflict Resolution** | Conflicts flagged for manual review with no automated resolution | Interruption, context loss, decision burden | `30_memory_burden_search.txt:8` ("manual resolution" comment), `30_memory_burden_search.txt:89-100` (manual merge/resolution flags) |
| **Cognitive State Not Integrated** | Task routing and orchestration ignore ADHD attention state | Poor task matching, cognitive overload, flow breaks | `20_friction_search.txt:30,63,74,79` (cognitive_state params unused in orchestrator), task-router isolated from orchestrator |
| **Test Coverage Gap** | Taskmaster has zero root-level tests, orchestrator tests only integration | Behavior uncertainty, regression risk, fear of changes | `40_task_orchestrator_root_tests.txt:1-6` (6 integration tests), `41_taskmaster_root_tests.txt` (empty file) |

## "Forces User to Remember" Map

### Critical Memory Burdens

1. **Task IDs Must Be Tracked Manually**
   - Symptom: No automatic task discovery or context-based task retrieval
   - Evidence: `30_memory_burden_search.txt:72-81` ("user_id required", "provide task_id")
   - Cost: Context switching overhead, lost task references during interruptions

2. **Status Values Are Strings**
   - Symptom: Must remember exact string spelling ("TODO" vs "todo" vs "pending")
   - Evidence: `20_friction_search.txt:4-54` (status string literals in 36+ locations)
   - Cost: Typo risk, no IDE autocomplete, validation failures at runtime

3. **Which Service Creates What Tasks?**
   - Symptom: No clear ownership model for task creation
   - Evidence: `20_friction_search.txt:86-100` (create_task in taskmaster, task-orchestrator, gpt-researcher)
   - Cost: Decision paralysis, duplicate tasks, lost coordination

4. **Conflict Resolution Rules Unknown**
   - Symptom: "Manual resolution" flags without resolution guidance
   - Evidence: `30_memory_burden_search.txt:8,89-100`
   - Cost: Interruption uncertainty, deferred decisions pile up

5. **Required Fields Not Discoverable**
   - Symptom: Trial-and-error task creation until all required fields provided
   - Evidence: `30_memory_burden_search.txt:12-24` ("missing id or title")
   - Cost: Frustration, wasted time, abandoned task creation attempts

### ADHD-Specific Burdens

**Interruption Recovery Cost**: Task IDs + status tracking + conflict queue = 3 things to remember across context switches

**Decision Fatigue**: 6+ task creation patterns + 4 status values + manual conflict resolution = paralyzing choice overload

**Lost Context**: No automatic task resumption after interruption (must manually search by ID)

## State Drift Patterns

### ConPort ↔ Orchestrator Sync Issues

- **Symptom**: Task status in ConPort may differ from task-orchestrator cache
- **Evidence**: `nl_services_task-orchestrator_app_core_sync.py.txt:402-848` (status mapping between systems)
- **Root Cause**: No single source of truth, eventual consistency without conflict resolution

### Status Transition Inconsistency

- **Symptom**: Different services transition states differently
- **Evidence**: `20_friction_search.txt:51-60` (dopemux-gpt-researcher transitions), vs `20_friction_search.txt:96-108` (task-orchestrator manual status updates)
- **Impact**: State machines diverge, validation rules conflict

### Event Bus Noise

- **Observation**: Many task state change events may be noise vs. signal
- **Evidence**: Needs classification (see SIGNAL_VS_NOISE_ANALYSIS.md)
- **Impact**: Cognitive load from irrelevant notifications

## Missing Decision Linkage

### Tasks ↔ ADRs Disconnected

- **Gap**: No automatic linking of tasks to architectural decision records
- **Evidence**: No linkage found in `20_friction_search.txt`, `30_memory_burden_search.txt`
- **Impact**: Lost rationale context, decisions forgotten, design drift

### Tasks ↔ Cognitive State Isolation

- **Gap**: Task creation doesn't capture ADHD attention state at creation time
- **Evidence**: `20_friction_search.txt:30,63,74` (cognitive_state params in task-router but not task-orchestrator)
- **Impact**: Tasks created during scatter state may be unrealistic during focus state

### Decomposition ↔ Parent Task State Drift

- **Gap**: Parent task status ("BLOCKED") not automatically updated when subtasks complete
- **Evidence**: `nl_services_task-orchestrator_task_orchestrator_app.py.txt:148` (manual DECOMPOSED_INTO links)
- **Impact**: Parent tasks stay "BLOCKED" forever, stale state accumulates

## Open Questions

- **Q1**: What percentage of task state transitions are user-initiated vs. automatic?
  - **Why Unknown**: No telemetry in evidence, would require event bus analysis

- **Q2**: How often do users abandon task creation due to "missing fields" errors?
  - **Why Unknown**: No error telemetry or user flow tracking in evidence

- **Q3**: What is the actual conflict rate between ConPort and orchestrator?
  - **Why Unknown**: Manual resolution queue not instrumented, no conflict metrics

- **Q4**: Which status transitions are signal vs. noise for ADHD developers?
  - **Why Unknown**: Needs user behavior analysis, see SIGNAL_VS_NOISE_ANALYSIS.md

## Next Steps (Phase 2)

1. **Telemetry**: Instrument task operations to answer open questions
2. **Unification**: Design single task creation API with guided fields
3. **Enum Migration**: Replace status strings with type-safe enums
4. **Auto-Linking**: Implement decision-to-task relationship tracking
5. **Test Coverage**: Add unit tests for taskmaster core logic

---

**Evidence Manifest**:
- `20_friction_search.txt`: 1,710 lines of task state patterns
- `30_memory_burden_search.txt`: 281 lines of memory burden markers
- `40_task_orchestrator_root_tests.txt`: 6 integration tests found
- `41_taskmaster_root_tests.txt`: 0 tests found
- 11 numbered line source files (nl_*.txt)
