---
id: dopecon_bridge_runtime_truth_integration_notes
title: Dopecon Bridge Runtime Truth Integration Notes
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Current dopecon-bridge integration relationships with ConPort, Leantime, Task Orchestrator, and event transport.
---
# dopecon-bridge - Integration Notes

## ConPort

- `/kg/custom_data`, `/kg/decisions`, and `/kg/progress` proxy to ConPort-facing clients.
- Response normalization marks these results as `source: conport`.

## Leantime

- `/route/pm` uses shared Leantime contract translation logic.
- Safe PM operations are routed through Leantime bridge tools.
- Workflow-significant mutations are blocked before they become PM-route writes.

## Task Orchestrator

- The bridge recognizes Task Orchestrator as the required adjudicator for workflow-significant mutations.
- It also exposes orchestrator-facing routes elsewhere in the service.
- Current workflow persistence dependence on bridge custom-data calls is architectural debt.

## Event bus

- `/events` is the authenticated publish surface.
- `/events/stream` and `/events/history` expose event consumption views.
