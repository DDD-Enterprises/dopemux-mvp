# Tool Contract

## 1. Phase-1 Allowed Tools
- `list_projects`: Returns approved projects. No `project_id` required.
- `task_orchestrator_read`: Wraps read tools (`query_items`, etc). Requires `project_id`.
- `conport_read`: Reads structured context. Requires `project_id`.
- `memory_read`: Reads chronicle/memory. Requires `project_id`.

## 2. Denied Tools / Routes
- `dopecon-bridge`: Denied in Phase 1.
- `search_all`: Denied in Phase 1.
- All mutating actions (e.g., `advance_item`, `manage_items`) are denied.

## 3. Authority Labels
- All outputs must retain `OBSERVED`, `PROPOSED`, `UNKNOWN`, or `CONFLICTING` labels.
