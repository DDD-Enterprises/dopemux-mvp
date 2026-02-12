---
id: SIGNAL_VS_NOISE_ANALYSIS
title: Signal Vs Noise Analysis
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: ADHD-first event classification for PM plane distinguishing actionable signals from cognitive noise.
---
# Signal vs Noise Analysis (Phase 1)

Status: Drafted from PM-FRIC-01 evidence only.
Evidence root: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`

## Signal

| Signal | Why it is signal | Evidence |
|---|---|---|
| Task status transitions to `in_progress`, `completed`, `blocked` | These transitions trigger explicit orchestration handlers, including blocked-task intervention. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L400-L407`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L674-L683` |
| High/critical coordination priorities | Coordinator reserves dedicated workers by priority class and treats high/critical separately in deep-focus filtering. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L48-L55`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L182-L187`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L331-L338` |
| ADHD break/context-switch state changes | Event schema explicitly models break reminders and context switches as first-class ADHD state events. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_events_types.py.txt L73-L77` |
| Task creation calls from taskmaster wrapper | Wrapper emits creation events when `create_task`, `parse_prd`, or `decompose_task` are called. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_server.py.txt L185-L191` |

## Noise

| Noise | Why it is noise for PM friction triage | Evidence |
|---|---|---|
| Binary `__pycache__` grep hits | Not human-actionable for PM friction mapping and inflate scan volume. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11` |
| Non-PM status matches (health/monitoring/etc.) | Matches regex terms but are not task-lifecycle semantics for PM plane redesign. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96` |
| Generic CLI progress `add_task(...)` output work | Many hits are UI progress meters, not PM task model operations. | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L1098-L1114` |

## Suppressed-by-default Rules

1. Drop lines matching `^Binary file .*__pycache__/.* matches$` during PM evidence triage. Evidence: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11`.
2. For PM friction analysis, suppress status hits outside PM ownership boundaries unless explicitly requested for cross-plane audit. Evidence: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96`.
3. In deep focus mode, suppress non-high/non-critical coordination events and non-critical interrupting events. Evidence: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L331-L338`.
4. Batch events when `can_batch=True` and `time_sensitive=False`; avoid immediate interruptions for those events. Evidence: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_event_bus.py.txt L34-L38`.
5. Any classification without direct evidence is `UNKNOWN` and moved to open questions. Evidence: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L1-L1447`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L1-L281`.

## Open Questions

### What is the observed event-rate reduction after suppression rules?
UNKNOWN. Evidence needed: before/after event counts from live event bus traffic under identical workload.

### Which suppressed classes should remain visible for recovery workflows?
UNKNOWN. Evidence needed: user validation on missed-critical incidents after applying rules 1-4.

### Does current test discovery execute taskmaster PM-path tests elsewhere?
UNKNOWN. Evidence needed: CI/local test command outputs mapped to file-discovery behavior.
