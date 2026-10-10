---
id: leantime_runtime_truth_architecture
title: Leantime Runtime Truth Architecture and Intended Uses
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Current Leantime integration truth as evidenced by repository adapters, tests, and ADRs in this checkout.
---
# Leantime - Architecture and Intended Uses

## Scope

This packet does not inspect a standalone Leantime codebase. It documents only what this repository proves through:

- `src/integrations/leantime_jsonrpc_client.py`
- `services/dopecon-bridge/dopecon_bridge/leantime_contract.py`
- `services/dopecon-bridge/tests/test_leantime_route_contract.py`
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md`

## Architecture

- The primary evidenced machine-to-machine seam is JSON-RPC over `/api/jsonrpc`.
- Authentication is by `x-api-key`.
- This repo also contains a translation layer that maps normalized or bridge PM operations onto Leantime tool names such as `list_tickets`, `create_ticket`, and `update_ticket`.

## Intended use

- Canonical PM operational system of record for:
  - projects
  - tasks / tickets
  - sprints
  - milestones
  - PM-facing assignment and status records
- Not the workflow authority.
- Not the chronicle authority.
- Not the durable decision/progress/context authority.
