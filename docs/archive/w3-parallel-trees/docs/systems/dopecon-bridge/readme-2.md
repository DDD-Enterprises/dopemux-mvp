---
id: dopecon-bridge-active-runtime
title: Dopecon Bridge Active Runtime
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Active runtime boundary and sanctioned surface for the narrowed dopecon-bridge adapter layer.
---
# DopeconBridge Active Runtime

## Summary

DopeconBridge is the active adapter layer between PM-plane consumers and canonical backend authorities. It is not a PM authority hub.

## Canonical authority split

- **Leantime**: PM operational record authority
- **Task Orchestrator**: workflow authority
- **ConPort**: decision, progress, and durable context authority
- **dope-memory**: chronicle memory authority
- **dopecon-bridge**: adapter/router/translator only

## Active runtime

Treat only these paths as the active bridge runtime:

- `services/dopecon-bridge/main.py`
- `services/dopecon-bridge/dopecon_bridge/`

Observed runtime defaults:

- service port default is `PORT_BASE + 16`, which resolves to `3016` when `PORT_BASE=3000`
- the bridge config still defaults `TASK_ORCHESTRATOR_URL` to `http://<container-prefix>-task-orchestrator:8000`

Root-level legacy files such as `kg_endpoints.py`, `orchestrator_endpoints.py`, and other historical helper modules are excluded from the active runtime unless explicitly reintroduced by a later decision.

## Sanctioned active surfaces

- health and auth routes
- authenticated event write routes
- read-only event stream/history routes
- `POST /route/pm` for adapter-safe Leantime-backed PM operations only
- ConPort-backed compatibility routes:
  - `/kg/custom_data`
  - `/kg/decisions`
  - `/kg/progress`
  - `/ddg/decisions`
  - `/ddg/search`

## Fail-closed routes

These routes are intentionally blocked because they previously depended on bridge-local authority or on missing canonical workflow surfaces:

- `POST /tasks/parse-prd`
- `GET /tasks/next/{project_id}`
- `PATCH /tasks/{task_id}/status`

## Unsupported legacy surfaces

These are not sanctioned as active runtime contract paths:

- `/route/cognitive`
- `/ddg/decisions/related`
- `/ddg/decisions/related-text`
- `/kg/links`

## Local state rule

Any surviving bridge-local SQL state is transitional and non-canonical. Local tables may support migration or cache behavior, but they are not PM-plane truth.

## Current drift to keep explicit

- Task Orchestrator workflow persistence still depends on bridge-mediated `custom_data` categories for ideas, epics, and audit records.
- The bridge config still assumes a Task Orchestrator URL on port `8000`, while the Task Orchestrator runtime config defaults to `3014`.
- Workflow-significant PM mutations remain fail-closed on `/route/pm`; bridge routing is not an alternative authority path.

## Evidence companions

- `docs/planes/pm/_evidence/dopecon-bridge-runtime-truth/executive-summary.md`
- `docs/planes/pm/_evidence/dopecon-bridge-runtime-truth/transport-and-runbook.md`
- `docs/planes/pm/_evidence/dopecon-bridge-runtime-truth/drift-report.md`
- `docs/05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md`
- `docs/05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md`
