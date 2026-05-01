---
id: pm-writes-phase1-authority-map
title: Pm Writes Phase1 Authority Map
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Pm Writes Phase1 Authority Map (explanation) for dopemux documentation and
  developer workflows.
---
# PM Writes Phase 1 Authority Map

This note freezes the phase-1 PM write surface against repo truth in this worktree.

## Verified authorities

- Metadata writes:
  - Canonical target: `leantime`
  - Proven transport: `docker/mcp-servers-source/leantime-bridge/leantime_bridge/http_server.py`
  - Proven HTTP surface: `POST /api/tools/{tool_name}`
  - Proven tool: `update_ticket`
  - Proven `update_ticket` fields in this checkout: `ticketId`, `headline`, `description`, `status`, `priority`, `assignedTo`
  - Phase-1 dopemux metadata writes are bounded to the passive intersection currently proven on that surface: headline/title, description/details/notes, assignee aliases

- Workflow transitions:
  - Canonical target: `task-orchestrator`
  - Proven active runtime: `services/task-orchestrator/app/main.py`
  - Proven active write route: `POST /api/projects/{project_id}/workflow/transition`
  - Included router: `services/task-orchestrator/app/main.py` includes `project_workflow_router`
  - Proven transition names on the runtime-backed path: `start`, `block`, `done`

- Decision and progress logging:
  - Canonical target: `conport`
  - Existing dopemux write path: `src/dopemux/pm/writes.py`
  - Mirror sink: `dope-memory` via `src/dopemux/pm/chronicle.py`

- History receipts:
  - Canonical target: `dope-memory`
  - Role in this slice: mirror and chronicle receipt sink, not PM state authority

## Verified non-authority and blocked routes

- `dopecon-bridge` is adapter-only in this slice:
  - `services/dopecon-bridge/dopecon_bridge/routes.py` states the bridge must not act as canonical task, workflow, decision, or progress authority
  - `/route/pm` blocks workflow-significant mutations

- Dormant task-orchestrator PM router:
  - `services/task-orchestrator/app/api/pm_tools.py` defines `/api/pm/work-items/*`
  - `services/task-orchestrator/app/main.py` does not include that router
  - These routes are defined in code but not proven active runtime in this checkout

## Phase-1 implementation constraints

- No unified PM write API.
- No workflow-significant mutation through Leantime.
- No binding to `/api/pm/work-items/*`.
- No bridge-mediated authority claims.
- No silent multi-authority write fan-out.

## Risks / known limits

- Phase 1 binds only to the proven Leantime `update_ticket` metadata subset; tags, dates, estimates, and reference-style metadata remain rejected unless their support is proven on the active bridge tool surface.
- Workflow writes intentionally use only the active project-scoped task-orchestrator transition route and do not bind to dormant `/api/pm/work-items/*` routes.
- Full behavior validation remains blocked in this worktree pending a Python environment with repo dependencies and `pytest` available.
- Overlapping legacy PM write surfaces remain drift risk until explicitly audited; this slice rebounded the observed bridge status-update caller away from `src/dopemux/pm/write.py`, but the overlapping module still exists in-repo.

## Worktree proof

- Worktree path: `/Users/hue/code/dopemux-mvp-wt-pm-writes-phase1`
- Expected dedicated worktree: yes
- Primary checkout used: no
- Repo marker verified: `.dopetaskroot`
- Branch verified: `codex/pm-writes-phase1`
- Repo identity matched expected dopemux-mvp binding: yes

## Observed drift

- `docs/03-reference/truth/truth-interfaces.md` still lists `/work-items/{task_id}/update`, `/transition`, and `/progress` under task-orchestrator observed routes even though `app/main.py` only proves `project_workflow_router` as active from the inspected PM write surface.
- The direct Leantime `update_ticket` tool surface currently proves fewer metadata fields than the broader phase-1 write plan originally proposed.
- Bridge status-update code previously imported `dopemux.pm.write.pm_transition_work_item`; this slice redirects that caller to the phase-1 write core but still leaves the overlapping module present as drift risk.
