---
id: RUNTIME_STABILITY_HOTFIXES_2026_02_08
title: Runtime Stability Hotfixes 2026 02 08
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-08'
last_review: '2026-02-08'
next_review: '2026-02-22'
status: draft
prelude: Runtime hotfix evidence for ADHD engine and genetic agent startup stability and container health.
---
# Runtime Stability Hotfixes (2026-02-08)

## Scope

This report captures runtime blockers resolved during the current audit push and
the verification evidence that those blockers are no longer active.

## Resolved Blockers

1. ADHD engine startup crash:
   `AttributeError: 'Settings' object has no attribute 'task_orchestrator_url'`
2. ADHD engine event bus wiring issue:
   event emitter was initialized with a bridge adapter instead of a Redis URL.
3. ADHD engine monitoring oversight:
   break monitor was started twice.
4. Genetic agent startup crash:
   package import drift (`from core...`, `from shared...`) and missing runtime
   dependencies caused restart loops.
5. Genetic agent MCP compatibility drift:
   missing Zen client shim and GPT-Researcher base-client mismatch.

## Commits

1. `a9bce589` `fix(adhd-engine): restore missing settings contract for startup`
2. `3e140f2a` `fix(adhd-engine): wire event emitter redis bus and dedupe monitors`
3. `132d8503` `fix(genetic-agent): restore package wiring and runtime dependencies`

## Verification Evidence

Container snapshot after deployment:

- `dopemux-mvp-adhd-engine-1` => `Up (healthy)`
- `dopemux-genetic-agent` => `Up (healthy)`
- `dope-decision-graph-bridge` => `Up (healthy)`
- `mcp-conport` => `Up (healthy)`
- `mcp-pal` => `Up (healthy)`

ADHD engine log signals:

- `ADHD Accommodation Engine ready`
- `ADHD Event Emitter connected to Redis`
- One `Started break timing monitor` line (duplicate removed)

Genetic agent log signals:

- `Application startup complete`
- `Uvicorn running on http://0.0.0.0:8000`
- Repeated `/health` 200 responses

Evidence artifact:

- `/Users/hue/code/dopemux-mvp/reports/strict_closure/runtime_stability_hotfixes_2026-02-08.json`

## Remaining Follow-up

1. Genetic agent still emits FastAPI `@app.on_event` deprecation warning.
   Functional status is healthy, but this should be modernized to lifespan
   handlers in a non-breaking cleanup pass.
