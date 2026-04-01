---
id: leantime_runtime_truth_integration_notes
title: Leantime Runtime Truth Integration Notes
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Current repository-proven integration notes for Leantime as the PM operational backend.
---
# Leantime - Integration Notes

## JSON-RPC client

- `LeantimeJSONRPCClient` targets `base_url + /api/jsonrpc`
- authentication uses `x-api-key`
- client methods include project and ticket operations

## Bridge translation layer

- dopecon-bridge maps normalized operations to Leantime tool calls:
  - `get_tasks` -> `list_tickets`
  - `create_task` -> `create_ticket`
  - `update_task` / `update_task_status` -> `update_ticket`

## PM-plane relationship

- PM metadata updates resolve to Leantime
- workflow-significant writes must not be treated as Leantime-owned decisions
- route-level policy blocks workflow-significant mutations unless they are adjudicated by Task Orchestrator
