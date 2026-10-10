---
id: dopecon_bridge_runtime_truth_workflow_gates
title: Dopecon Bridge Runtime Truth Workflow and Gates
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Fail-closed workflow and PM-route gates enforced by the current dopecon-bridge runtime.
---
# dopecon-bridge - Workflow and Gates

## Confirmed fail-closed behavior

- legacy task creation and status routes are disabled because bridge-local task authority is non-canonical
- workflow-significant PM-route mutations are blocked with HTTP `409`
- the error path explicitly references `Task Orchestrator adjudication`

## Safe path

- safe Leantime-backed PM operations are proxied through `/route/pm`
- custom-data and decision/progress surfaces are explicitly normalized as ConPort-backed

## Gate meaning

- The bridge is attempting to prevent silent authority escalation.
- Where callers still rely on the bridge as a persistence substrate, that reliance is outside the intended boundary.
