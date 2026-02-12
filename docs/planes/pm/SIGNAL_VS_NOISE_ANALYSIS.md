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
# Signal vs Noise Analysis (Phase 1, Critiqued)

Status: Tightened for citation integrity and Trinity boundaries.
Evidence root: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`

## Signal

| Signal | Why it is signal | Evidence |
|---|---|---|
| Task status transitions (`in_progress`, `completed`, `blocked`) | Coordinator routes these values to dedicated handlers, including blocked-task intervention. | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L400-L407; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L674-L683` |
| High and critical priorities under deep-focus gating | Deep-focus mode explicitly allows only critical/high classes and applies interruption gating. | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L48-L55; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L331-L338` |
| ADHD break/context-switch states | Event schema explicitly models break reminders and context switches. | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_events_types.py.txt L73-L77` |
| Task creation tool calls from wrapper | Wrapper emits creation event flow for `create_task`, `parse_prd`, `decompose_task`. | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_server.py.txt L185-L191` |

## Noise

| Noise | Why it is noise for PM friction triage | Evidence |
|---|---|---|
| Binary cache matches in grep outputs | Not actionable PM semantics and materially inflate triage stream. | `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11` |
| Non-PM status hits (health/monitoring and unrelated services) | Regex matches contain status tokens but do not describe PM-task lifecycle behavior. | `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96` |
| CLI progress meter `add_task(...)` lines | Mostly UI progress plumbing, not PM ownership boundaries or task-state contracts. | `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L1098-L1114` |

## Suppressed-by-default Rules

1. Suppress binary-cache grep rows during PM audits. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11`.
2. Suppress non-PM status hits unless running explicit cross-plane audits. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96`.
3. Under deep focus, suppress non-high/non-critical events and non-critical interrupts. Evidence: `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L331-L338`.
4. Batch events marked `can_batch=True` and keep immediate delivery for time-sensitive items. Evidence: `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_event_bus.py.txt L34-L38`.
5. Any non-cited classification is invalid and must be moved to `UNKNOWN`. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L1-L1447; docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L1-L281`.

## Trinity Boundaries (PM vs Memory vs Search)

- PM-owned: task lifecycle orchestration and deep-focus event gating logic. Evidence: `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L400-L407; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L331-L338`.
- Memory-derived: conflict and missing-field behavior surfaced via ConPort/adapter evidence. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L8-L21`.
- Search-owned: binary and broad regex artifact noise in evidence generation. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11; docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96`.

## Open Questions

### What is the measured event-rate reduction after these suppression rules?
UNKNOWN. Evidence needed: before/after event-rate telemetry on identical workloads.

### Which suppressed classes are still needed for incident recovery?
UNKNOWN. Evidence needed: user validation and incident replay after suppression.

### Which PM notifications must stay visible in deep-focus mode by policy?
UNKNOWN. Evidence needed: explicit PM policy document mapping event classes to focus-mode behavior.
