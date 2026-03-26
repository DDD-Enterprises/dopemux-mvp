# Task Authority Removal

## Verdict

`dopecon-bridge` no longer acts as canonical task authority.

## Evidence

- `POST /tasks/parse-prd` returns `409` fail-closed.
- `GET /tasks/next/{project_id}` returns `409` fail-closed.
- `PATCH /tasks/{task_id}/status` returns `409` fail-closed.
- `/route/pm` rejects workflow-significant mutations instead of serving as a workflow or task-law bypass.
- Active route handling no longer uses bridge-local SQL task state as PM-plane truth.

## Remaining local state

- `TaskRecord`
- `ProjectRecord`

These model classes remain present only as transitional, explicitly non-canonical local state.
