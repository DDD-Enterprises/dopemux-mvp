---
id: dopecon_bridge_runtime_truth_data_model
title: Dopecon Bridge Runtime Truth Data Model
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: PM-visible request and payload shapes exposed or proxied by the current dopecon-bridge runtime.
---
# dopecon-bridge - Data Model

## PM-visible request models

Source: `services/dopecon-bridge/dopecon_bridge/routes.py`

- `PMRouteRequest`
- `CustomDataRequest`
- `DecisionRequest`
- `ProgressRequest`
- `PublishEventRequest`

## Important data boundary

- PM-route operations are normalized request envelopes, not authoritative PM objects.
- KG `custom_data`, `decisions`, and `progress` payloads are proxied toward ConPort-facing surfaces.
- Bridge-local PM routing does not define a canonical task or workflow schema of its own.

## Current leak

- Task Orchestrator currently uses bridge-exposed custom-data flows as workflow persistence substrate.
- That is a consumer leak into the bridge surface, not evidence that the bridge has become the rightful authority.
