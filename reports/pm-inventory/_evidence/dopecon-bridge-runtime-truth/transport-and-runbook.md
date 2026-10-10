---
id: dopecon_bridge_runtime_truth_transport_runbook
title: Dopecon Bridge Runtime Truth Transport and Runbook
type: runbook
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
status: active
prelude: Active transport surfaces and default runtime settings for the current dopecon-bridge service.
---
# dopecon-bridge - Transport and Runbook

## Active HTTP runtime

- Framework: FastAPI
- Entrypoint: `services/dopecon-bridge/main.py`
- Default port: `PORT_BASE + 16`, which resolves to `3016` when `PORT_BASE=3000`
- Default health path: `/health`

## High-value route groups

- `/route/pm`
- `/events`
- `/ddg/*`
- `/kg/*`
- `/tasks/*` legacy paths that now fail closed on non-canonical operations

## Dependency defaults

- `CONPORT_URL` default: `http://conport:3004`
- `LEANTIME_BRIDGE_URL` default: `http://<container-prefix>-leantime-bridge:3015`
- `TASK_ORCHESTRATOR_URL` default: `http://<container-prefix>-task-orchestrator:8000`
