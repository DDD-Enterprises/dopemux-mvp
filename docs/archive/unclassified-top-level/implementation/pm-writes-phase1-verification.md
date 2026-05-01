---
id: pm-writes-phase1-verification
title: Pm Writes Phase1 Verification
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Pm Writes Phase1 Verification (explanation) for dopemux documentation and
  developer workflows.
---
# PM Writes Phase 1 Verification Note

This note records focused verification for the published phase-1 PM writes slice in the dedicated worktree.

## Worktree proof

- Worktree path: `/Users/hue/code/dopemux-mvp-wt-pm-writes-phase1`
- Primary checkout used: no
- Branch: `codex/pm-writes-phase1`
- Repo marker verified: `.dopetaskroot`
- Repo identity: `https://github.com/DDD-Enterprises/dopemux-mvp.git`

## Files changed in the slice

- `src/dopemux/pm/writes.py`
- `src/dopemux/pm/api.py`
- `src/dopemux/pm/adapters/orchestrator.py`
- `src/dopemux/pm/__init__.py`
- `src/dopemux/ui/pm_writes.py`
- `services/dopecon-bridge/dopecon_bridge/services/task_integration.py`
- `tests/unit/dopemux/pm/test_writes.py`
- `tests/unit/dopemux/ui/test_pm_writes.py`
- `tests/unit/pm/test_pm_route_contracts.py`
- `tests/test_pm_api.py`
- `docs/implementation/pm-writes-phase1-authority-map.md`

## Authority split verified

- Metadata writes stay on the Leantime path through `pm_update_work_item` in `src/dopemux/pm/writes.py`.
- Workflow-significant transitions stay on task-orchestrator through `pm_transition_work_item` in `src/dopemux/pm/writes.py`.
- Progress and decision logging stay ConPort-primary through `pm_log_progress` and `pm_log_decision` in `src/dopemux/pm/writes.py`.
- Mirror receipts stay downstream-only and are emitted separately for `dope-memory`.
- Authority-visible confirmation and receipt text stays explicit in `src/dopemux/ui/pm_writes.py`.

## Routes and write surfaces verified

- Leantime metadata write surface used by this slice:
  - bridge tool `update_ticket`
  - normalized payload keys: `ticketId`, `headline`, `description`, `assignedTo`
- Task-orchestrator workflow route used by this slice:
  - `POST /api/projects/{project_id}/workflow/transition`
- Dormant route explicitly not used:
  - `/api/pm/work-items/{task_id}/transition`
- Bridge status-update caller no longer imports `dopemux.pm.write` on the active verified path.

## Focused proof checks

### 1. Metadata edit from PM mode

- Test: `tests/unit/dopemux/pm/test_writes.py::test_pm_update_work_item_success_uses_update_ticket_payload`
- Proof:
  - canonical system asserted as `leantime`
  - call asserted as `update_ticket`
  - payload asserted as `{"ticketId": "task-1", "headline": "new title", "description": "operator note"}`

### 2. Workflow transition from PM mode

- Test: `tests/unit/dopemux/pm/test_writes.py::test_pm_transition_work_item_uses_project_scoped_transition_only`
- Proof:
  - canonical system asserted as `task-orchestrator`
  - Leantime client asserted unused
  - orchestrator request asserted on `/api/projects/proj-7/workflow/transition`

### 3. Progress / decision write

- Test: `tests/test_pm_api.py::test_pm_log_progress_success_with_memory_mirror`
- Proof:
  - canonical backend asserted as `conport`
  - operation type asserted as `log_progress`
  - mirror/reflection state asserted as succeeded

### 4. dope-memory mirror receipt

- Test: `tests/test_pm_api.py::test_pm_log_progress_success_with_memory_mirror`
- Proof:
  - same progress write records a successful downstream mirror path
  - `src/dopemux/pm/writes.py` emits `mirror_receipts` with `system="dope-memory"`

### 5. Forbidden Leantime workflow mutation blocked

- Test: `tests/test_pm_api.py::test_pm_update_work_item_rejected_mixed`
- Proof:
  - payload mixing `title` and `status` is rejected
  - error asserted to contain `workflow-significant fields`
  - reconciliation asserted as rejected

### 6. Confirm modal names the real target

- Test: `tests/unit/dopemux/ui/test_pm_writes.py::test_render_workflow_confirmation_names_task_orchestrator`
- Proof:
  - rendered text asserted as `WRITE -> task-orchestrator: transition workflow state`

## Focused command run

Executed in the dedicated worktree with the dependency-capable environment:

```bash
PATH="/Users/hue/code/dopemux-mvp/.venv/bin:$PATH" /Users/hue/code/dopemux-mvp/.venv/bin/pytest -q \
  tests/unit/dopemux/pm/test_writes.py::test_pm_update_work_item_success_uses_update_ticket_payload \
  tests/unit/dopemux/pm/test_writes.py::test_pm_transition_work_item_uses_project_scoped_transition_only \
  tests/test_pm_api.py::test_pm_log_progress_success_with_memory_mirror \
  tests/test_pm_api.py::test_pm_update_work_item_rejected_mixed \
  tests/unit/dopemux/ui/test_pm_writes.py::test_render_workflow_confirmation_names_task_orchestrator
```

Result:

- `5 passed`

## Remaining drift and ambiguity

- The Leantime metadata subset remains intentionally narrow. Tags, dates, estimates, and reference-style fields remain rejected unless proven on the active bridge tool surface.
- `src/dopemux/pm/write.py` still exists as overlapping legacy drift even though the active verified bridge path no longer imports it.
- The bridge-adjacent transition path still carries inherited `expected_version=1` behavior and was not expanded in this slice.
- This note verifies the focused phase-1 authority boundaries. It does not convert unresolved runtime drift elsewhere in the repo into a claim of unified PM authority.
