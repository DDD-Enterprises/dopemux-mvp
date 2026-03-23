# Taskmaster Service

The Taskmaster service acts as an MCP wrapper for AI-driven task decomposition and PRD parsing with ADHD accommodations.

## Architecture

Taskmaster relies on the Dopemux PM plane to canonicalize tasks, enforce state boundaries, and maintain decision traceability. As a PM producer:
- Task creations are normalized with stable `content_hash_task_id`.
- Task statuses map exclusively to `PMTaskStatus` via `TASKMASTER_TO_CANONICAL`.
- Canonical status updates are routed through `pm_transition_work_item`.
- Linked IDs from synchronization are preserved canonically.
- Comments and creation progress utilize `pm_log_progress` to push context explicitly to ConPort.

## Wrapper Failure and Sync Behavior

The wrapper (`TaskMasterWrapper`) wraps execution of the `task-master-ai` package and acts as a transparent stdio proxy. Event emission acts as a secondary mechanism to log completion and metrics.
The `TaskMasterBridgeAdapter` routes sync and task modifications explicitly through PMPlane configurations (`PMWriteConfig`).

If bridge actions fail, operations explicitly raise or return false per PM-plane "fail-closed" guarantees.

## Run Tests

```bash
python3 -m pytest -q services/taskmaster tests
```
