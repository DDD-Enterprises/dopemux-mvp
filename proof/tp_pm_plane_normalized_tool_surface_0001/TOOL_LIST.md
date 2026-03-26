# Normalized PM-Plane Tool List

Core tools defined: `12`

1. `pm_get_project_context`
2. `pm_get_priority_queue`
3. `pm_get_blockers`
4. `pm_get_workflow_state`
5. `pm_update_work_item`
6. `pm_transition_work_item`
7. `pm_get_sprint_snapshot`
8. `pm_get_decision_context`
9. `pm_log_progress`
10. `pm_get_work_chronicle`
11. `pm_search_project_knowledge`
12. `pm_get_technical_context`

Backend reality blockers:

- `pm_get_priority_queue`
- `pm_get_blockers`
- `pm_get_workflow_state`
- `pm_transition_work_item`

These remain canonically mapped to Task Orchestrator, but the active runtime lacks project-scoped next-action, blocker, workflow-state, and transition surfaces. Implementations must fail closed rather than invent local truth.
