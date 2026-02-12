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

Status: Drafted from PM-FRIC-01 evidence only.
Evidence root: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`

## Friction Table

| Friction | Symptom | ADHD cost | Severity | Evidence |
|---|---|---|---|---|
| Status vocabulary drift across services | Task-orchestrator model uses `pending/completed/blocked`, while ConPort and TaskMaster adapters use `TODO/DONE`, and coordinator logic keys on lowercase status strings. | Extra memory load to remember per-system status dialects; higher transition error risk after interruptions. | High | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt L13-L18`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt L85-L86`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L69-L70`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_task-orchestrator_event_coordinator.py.txt L400-L407` |
| Multiple task-creation entrypoints | Task creation is exposed through taskmaster bridge adapter, taskmaster wrapper tool calls, and CLI task decomposer. | Choice overload and inconsistent task provenance. | High | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L57-L70`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_server.py.txt L185-L191`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_cli.py.txt L2496-L2501` |
| ID-centric task operations | Update/sync methods require explicit `task_id`; failure path is `Task ... not found`; CLI surfaces IDs directly. | High interruption recovery cost because users/agents must carry IDs across contexts. | High | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L122-L126`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_services_taskmaster_bridge_adapter.py.txt L148-L160`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_cli.py.txt L2500-L2501` |
| Runtime validation and manual conflict handling | Missing required fields raise runtime errors; sync conflicts are queued for manual resolution. | Context breaks and retry loops under ambiguous error states. | High | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L8-L8`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L12-L21` |
| Evidence search noise in PM triage | Search output includes binary `__pycache__` matches and many non-PM status hits (health/monitoring, etc.). | Attention fragmentation while triaging PM findings. | Medium | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/30_memory_burden_search.txt L2-L11`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/20_friction_search.txt L81-L96` |
| Root-level test asymmetry | Task-orchestrator has root test files; taskmaster root-level discovery output is empty. | Lower confidence when changing taskmaster PM paths. | Medium | `docs/planes/pm/_evidence/PM-FRIC-01.outputs/40_task_orchestrator_root_tests.txt L1-L6`; `docs/planes/pm/_evidence/PM-FRIC-01.outputs/41_taskmaster_root_tests.txt` (empty file) |

## Open Questions

### Which status vocabulary is canonical across PM boundaries?
UNKNOWN. Evidence needed: explicit runtime mapping contract between `TaskStatus` and ConPort/taskmaster status values.

### Which creation entrypoint should own PM-plane task provenance?
UNKNOWN. Evidence needed: routing policy that defines ownership for `create_task` across taskmaster wrapper, bridge adapter, and CLI.

### Are empty taskmaster root tests a real coverage gap or a discovery-path issue?
UNKNOWN. Evidence needed: CI/local test discovery configuration and observed execution output.

### What fraction of PM triage output is actionable vs noise?
UNKNOWN. Evidence needed: filtered vs unfiltered counts for `20_friction_search.txt` and `30_memory_burden_search.txt` with scoped path rules.
