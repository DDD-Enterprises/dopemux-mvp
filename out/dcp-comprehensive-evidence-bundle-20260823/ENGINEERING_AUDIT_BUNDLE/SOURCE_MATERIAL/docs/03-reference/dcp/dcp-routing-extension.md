---
id: DCP-ROUTING-EXTENSION
title: DCP Routing Extension Contract
type: reference
status: PROPOSED
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: DCP Routing Extension Contract (reference) for dopemux documentation and
  developer workflows.
---
# DCP Routing Extension Contract

This page defines the Packet 6 routing contract surface for DCP. It is a contracts-only artifact set:

- `schemas/dcp_extension/routing/route_decision.schema.json`
- `schemas/dcp_extension/routing/lane_engine.schema.json`
- `schemas/dcp_extension/routing/openclaw_route.schema.json`
- `tests/dcp_extension/routing/test_routing_contracts.py`

These schemas are the canonical Packet 6 contract artifacts. Existing OpenClaw routing files under `docs/03-reference/dcp/openclaw-routing/` remain advisory reference inputs unless a later accepted packet explicitly imports them.

## Non-Authority Boundaries

The routing extension does not implement production routing, call OpenClaw, call OpenRouter, select providers, or certify benchmark readiness. It records the shape of future route decisions and route metadata only.

Provider, model, router, bridge, adapter, and cache outputs are not authority surfaces. Runtime/source truth, current PR state, proof freshness, and accepted PCP/DCP governance remain higher authority.

## Fail-Closed Contract

Consumers of this contract must treat unknown, invalid, or incomplete routing decisions as fail-closed. The schemas encode this by requiring:

- `UNKNOWN` privacy or risk classes to produce a blocked, escalated, or supervisor-needed decision.
- blocked decisions to carry at least one machine-readable `blocked_reasons` value.
- live-write runner selection to remain `false`.
- undeclared runtime fields to be rejected.

Packet 6 does not execute those decisions. Runtime enforcement belongs to later packets.

## Protected Lanes

Protected lanes include security-sensitive, release-authority, secret-bearing, client-data, and unknown classification paths. They must not use OpenRouter-free routes. Security and release paths require independent or stronger audit posture and human-gate visibility.

The contract supports public low-risk OpenRouter-free route metadata, but only outside protected lanes. OpenRouter remains a routing/control layer, not a trust oracle.

## Downstream Consumers

Later PR Steward, Task Orchestrator visibility, live-write-gate, and bridge packets may consume these schemas. They must not infer runtime readiness or benchmark certification from this packet alone.

Breaking changes include removing or renaming enum values, changing required route-decision fields, or weakening fail-closed constraints. Additive fields require schema and consumer review before use.

## Remaining Unknowns

- Actual OpenClaw runtime behavior is not exercised.
- Actual OpenRouter provider/model behavior is not exercised.
- Benchmark certification is not run.
- External acceptance status of older OpenClaw reference documents remains unknown.
