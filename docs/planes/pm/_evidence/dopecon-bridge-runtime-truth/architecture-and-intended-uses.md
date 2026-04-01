---
id: dopecon_bridge_runtime_truth_architecture
title: Dopecon Bridge Runtime Truth Architecture and Intended Uses
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Runtime-truth architecture summary for dopecon-bridge as an adapter, router, and translation layer in the PM stack.
---
# dopecon-bridge - Architecture and Intended Uses

## Active role

- The active bridge declares itself as an adapter and proxy layer only.
- The main FastAPI entrypoint registers routers for:
  - auth
  - events
  - tasks
  - ddg
  - PM routing
  - KG / ConPort proxy
  - health

## Intended use

- translation and routing layer
- contract mediation for PM-plane calls
- event bus ingress / streaming surface
- ConPort proxy surface

## Explicit non-role

- not canonical task authority
- not canonical workflow authority
- not canonical decision or progress authority

This non-role is stated directly in the bridge routes module and reinforced by fail-closed route behavior.
