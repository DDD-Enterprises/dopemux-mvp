# Backend Mapping

## Canonical backend map

- `ConPort`
  - `pm_get_project_context`
  - `pm_get_decision_context`
  - `pm_log_progress`
- `Task Orchestrator`
  - `pm_get_priority_queue`
  - `pm_get_blockers`
  - `pm_get_workflow_state`
  - `pm_transition_work_item`
- `Leantime`
  - `pm_update_work_item`
  - `pm_get_sprint_snapshot`
- `dope-memory`
  - `pm_get_work_chronicle`
- `dope-context`
  - `pm_search_project_knowledge`
- `Serena`
  - `pm_get_technical_context`

## Supporting-source rules

- Supporting sources may enrich results but do not replace the canonical backend.
- Multi-plane reads must preserve provenance, source plane, and canonical IDs.
- Raw subsystem-native methods remain implementation details rather than the long-term agent contract.

## Backend reality gaps

The active Task Orchestrator runtime still lacks project-scoped surfaces for:

- next-action / priority queue
- blockers
- workflow-state reads
- workflow-significant transitions

Result: those four normalized tools remain canonically mapped to Task Orchestrator but must currently fail closed or return explicit unavailable results instead of inventing bridge-local or Leantime-local truth.
