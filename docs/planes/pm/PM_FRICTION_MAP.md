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
# PM Friction Map (Phase 1, Critiqued)

Status: Tightened for citation integrity and Trinity boundaries.
Evidence root: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`

## Friction Table

| Friction | Symptom | ADHD cost | Severity | Evidence |
|---|---|---|---|---|
| Status vocabulary drift across services | Task-orchestrator model uses `pending/completed/blocked`, while ConPort/taskmaster paths use `TODO/DONE`, and coordinator handlers key on lowercase runtime values. | Context-switch tax: must remember multiple status dialects for the same lifecycle. | High | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt L13-L18; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt L85-L86; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L69-L70; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L400-L407` |
| Multiple task-creation entrypoints | Creation exists in taskmaster bridge adapter, taskmaster wrapper tool path, and CLI task decomposer path. | Decision overhead and uncertain provenance for newly created work items. | High | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L57-L70; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_server.py.txt L185-L191; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_cli.py.txt L2496-L2501` |
| ID-centric task operations | Update/sync interfaces require explicit `task_id`; missing record path is `Task ... not found`; CLI exposes generated ID. | Higher interruption recovery cost because IDs must be retained across tools and time gaps. | High | `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L122-L126; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L148-L160; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_cli.py.txt L2500-L2501` |
| Runtime validation and manual conflict handling | Missing-field failures are raised at runtime and sync conflicts are queued for manual resolution. | Retry loops and context breaks when the user/agent has to reconcile failures manually. | High | `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L8-L8; docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L12-L21` |
| Evidence search noise in PM triage | Evidence scans include binary cache hits and non-PM status matches. | Attention fragmentation during audit; weakens PM signal extraction. | Medium | `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11; docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96` |
| Root test discovery asymmetry | Root test list for task-orchestrator contains entries; taskmaster root list is empty. | Lower confidence for safe PM changes touching taskmaster flows. | Medium | `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/40_task_orchestrator_root_tests.txt L1-L6; docs/planes/pm/_evidence/PM-FRIC-01.outputs/41_taskmaster_root_tests.txt (empty file)` |

## Trinity Boundaries (PM vs Memory vs Search)

- Boundary violation: status mapping behavior spans PM-owned orchestration model and Memory-owned ConPort progress representation, but ownership is not declared. Evidence: `[Direct code] docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt L13-L18; docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt L85-L86`.
- Boundary violation: manual conflict evidence originates from Memory adapter/search artifacts and should not be framed as PM-only behavior. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L8-L8; docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L12-L21`.
- Boundary violation: binary-cache and broad regex noise are Search-pipeline concerns, not PM-domain friction by themselves. Evidence: `[Search hit] docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11`.

## Open Questions

### Which status vocabulary is canonical across PM boundaries?
UNKNOWN. Evidence needed: signed mapping contract between PM `TaskStatus` and Memory/ConPort status representation.

### Which creation entrypoint owns PM provenance for new tasks?
UNKNOWN. Evidence needed: routing policy that names one source of truth for creation across bridge adapter, wrapper, and CLI paths.

### Is taskmaster root-test emptiness an actual gap or a discovery-path artifact?
UNKNOWN. Evidence needed: CI and local discovery outputs showing exactly which test globs execute.

### What ratio of scan output is actionable PM signal after suppression?
UNKNOWN. Evidence needed: filtered/unfiltered counts on the same evidence set with explicit suppression rules.
