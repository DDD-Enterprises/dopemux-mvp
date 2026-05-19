---
id: data-and-control-flow
title: Data And Control Flow
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Evidence-backed data and control flow summary for Dopemux systems.
---
# Data And Control Flow

This document summarizes observed control and data flows. It does not prove
live runtime health; packet 003 did not start services.

## Operator Startup Flow

```text
operator -> dopemux CLI -> routing/MCP/workspace coordination -> downstream systems
```

Observed evidence:

- `pyproject.toml` registers `dopemux = "dopemux.cli:main"`.
- `src/dopemux/cli.py` contains `dopemux start` and command registration.
- `compose.yml` and `services/registry.yaml` describe the default service stack.

Control authority stays with `dopemux` only for the operator-control slice.

## Execution Handoff Flow

```text
dopemux kernel path -> scripts/taskx -> scripts/dopetask -> external dopetask
```

`scripts/taskx` is a compatibility shim. `scripts/dopetask` creates or reuses a
local `.dopetask_venv`, installs the version from `.dopetask-pin`, and executes
the external `dopetask` binary. The external runtime is not implemented as repo
source here.

## PM Write Flow

```text
metadata -> Leantime
workflow transition -> task-orchestrator
decision/progress/context -> ConPort
historical receipt mirror -> dope-memory
```

Observed evidence:

- `src/dopemux/pm/writes.py` classifies PM actions and returns canonical
  receipts naming `leantime`, `task-orchestrator`, or `conport`.
- dope-memory appears as a mirror receipt sink for PM progress/decision activity.

This flow is intentionally split. A bridge route or mirror receipt does not
change the canonical writer.

## Workflow Persistence Flow

```text
task-orchestrator workflow service -> DopeconBridge custom-data client -> bridge-backed storage path
```

Observed evidence:

- task-orchestrator workflow APIs live under `services/task-orchestrator/app/*`.
- workflow store code writes categories such as `workflow_ideas`,
  `workflow_epics`, and `workflow_audit` through a bridge client.

This means Task Orchestrator serves workflow authority while its persistence path
is bridge-mediated. The bridge still does not become workflow authority.

## Chronicle Flow

```text
PM or operator event -> dope-memory /tools routes -> chronicle ledger
```

Observed evidence:

- `services/working-memory-assistant/dope_memory_main.py` identifies itself as
  the canonical dope-memory HTTP entrypoint on `3020`.
- chronicle store and schema files define the durable ledger behavior.

dope-memory is historical receipt authority. It is not the current PM state
writer.

## Retrieval Flow

```text
caller -> dope-context or ConPort retrieval -> ranked derived output -> operator evidence
```

Observed evidence:

- `services/dope-context/src/mcp/server.py` exposes indexing and search tools.
- ConPort exposes structured context, decision, progress, custom-data, and
  relationship query surfaces.

Retrieval output is derived. Use it to find source evidence; do not let it
override runtime files, schemas, tests, compose wiring, or active entrypoints.

## Bridge Proxy Flow

```text
caller -> dopecon-bridge route -> upstream service or event bus
```

Observed evidence:

- `services/dopecon-bridge/dopecon_bridge/routes.py` explicitly states the
  bridge is adapter/proxy only.
- The same file policy-checks workflow-significant PM mutations and routes safe
  PM and KG-like calls to upstream systems.

Bridge outputs must be labeled proxy, compatibility, or derived unless the
upstream system is named.

## Repo Truth Extractor Flow

```text
dopemux rte -> extractor command wrapper -> run_extraction_v5.py -> extraction artifacts
```

Observed evidence:

- `src/dopemux/cli.py` registers `dopemux rte` as the canonical operator command
  family.
- `services/repo-truth-extractor/run_extraction_v5.py` is the strongest v5
  runner authority.

Extractor artifacts are evidence artifacts. Runtime truth still wins.

## UNKNOWN And Drift

- `UNKNOWN`: one canonical repo-wide agent runtime.
- `UNKNOWN`: exact deployed authority for some Serena and support surfaces.
- `NEEDS_REPO_VERIFICATION`: live startup and health for the full compose stack
  in the current environment.
