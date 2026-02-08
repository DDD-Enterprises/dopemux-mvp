---
id: WORKFLOW_IDEA_EPIC_LIFECYCLE
title: Workflow Idea To Epic Lifecycle
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-08'
last_review: '2026-02-08'
next_review: '2026-05-08'
prelude: Run the ADR-197 Stage-1 and Stage-2 workflow lifecycle with task-orchestrator
  HTTP APIs and dopemux CLI commands.
---
# Workflow Idea to Epic Lifecycle

Use this guide to move work from idea capture to epic planning using the active
task-orchestrator workflow runtime.

## Prerequisites

1. `task-orchestrator` is reachable (`GET /health` returns 200).
2. DopeconBridge is available for workflow persistence.
3. Optional: Leantime bridge is configured if you want promote-time sync.

Set service URL:

```bash
export TASK_ORCH_URL="${TASK_ORCH_URL:-http://localhost:3014}"
```

## Step 1: Create an Idea

HTTP:

```bash
curl -sS -X POST "$TASK_ORCH_URL/api/workflow/ideas" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Reduce workflow friction",
    "description": "Add predictable status transitions and better docs",
    "source": "brainstorm",
    "creator": "hue",
    "tags": ["workflow", "docs"]
  }'
```

CLI:

```bash
dopemux workflow ideas add \
  --title "Reduce workflow friction" \
  --description "Add predictable status transitions and better docs" \
  --source brainstorm \
  --creator hue \
  --tag workflow \
  --tag docs
```

## Step 2: Review Ideas

```bash
curl -sS "$TASK_ORCH_URL/api/workflow/ideas?status=new&tag=workflow&limit=20"
```

## Step 3: Promote Idea to Epic

Promotion is idempotent. Re-promoting returns the same epic.

HTTP:

```bash
curl -sS -X POST "$TASK_ORCH_URL/api/workflow/ideas/idea_123/promote" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "high",
    "business_value": "Faster delivery with less planning debt",
    "acceptance_criteria": ["api tested", "docs updated"],
    "sync_to_leantime": false,
    "tags": ["workflow", "roadmap"]
  }'
```

CLI:

```bash
dopemux workflow ideas promote idea_123 \
  --priority high \
  --business-value "Faster delivery with less planning debt" \
  --criterion "api tested" \
  --criterion "docs updated" \
  --no-sync-leantime \
  --tag workflow \
  --tag roadmap
```

## Step 4: List and Refine Epics

List:

```bash
curl -sS "$TASK_ORCH_URL/api/workflow/epics?status=planned&priority=high&limit=20"
```

CLI list:

```bash
dopemux workflow epics list \
  --status planned \
  --priority high \
  --tag workflow \
  --limit 20
```

Patch epic:

```bash
curl -sS -X PATCH "$TASK_ORCH_URL/api/workflow/epics/epic_456" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in-planning",
    "acceptance_criteria": ["api tested", "docs updated", "release note added"]
  }'
```

## Response and Error Contracts

Workflow endpoints map errors as:
- `404`: missing idea or epic
- `409`: invalid state transition
- `503`: persistence/bridge unavailable
- `400`: invalid request payload

## Operational Notes

1. If Leantime sync fails during promote, epic creation still succeeds and
   response includes a non-empty `warning`.
2. Persistence categories are `workflow_ideas` and `workflow_epics`.
3. Runtime defaults can be tuned with `DOPMUX_WORKFLOW_*` env variables.
