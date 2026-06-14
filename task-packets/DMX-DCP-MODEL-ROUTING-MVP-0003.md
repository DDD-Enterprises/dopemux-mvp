---
id: DMX-DCP-MODEL-ROUTING-MVP-0003
title: Add routing backend policy map as inert data policy
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-06-14'
last_review: '2026-06-14'
next_review: '2026-09-12'
prelude: Pure backend preference policy for classified DCP RouteDecision data.
---
# DMX-DCP-MODEL-ROUTING-MVP-0003 - Routing Backend Policy Map

## Objective

Add a pure Python backend policy layer that maps an already-classified
`RouteDecision` to inert backend preference metadata.

This packet adds policy preference, not backend authority. The policy does not
invoke backends, runners, connectors, MCP, GitHub, provider APIs, Dopetask, or
Task Orchestrator.

## Authority

- Active packet: DMX-DCP-MODEL-ROUTING-MVP-0003 pasted task packet.
- Runtime dependencies: `src/dopemux/dcp/routing_model.py` and
  `src/dopemux/dcp/routing_classifier.py`.
- Advisory context: `config/ai/model-routing.policy.yaml` is proposed
  governance only, not runtime routing authority.

## Allowlist

- `src/dopemux/dcp/routing_backend_policy.py`
- `src/dopemux/dcp/__init__.py`
- `tests/unit/dcp/test_routing_backend_policy.py`
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md`

## Required PAL Chain

`analyze -> thinkdeep -> challenge -> planner -> challenge -> implement -> codereview -> precommit -> challenge`

## Validation

- `python -m compileall -q src/dopemux/dcp`
- `python -m pytest -q tests/unit/dcp/test_routing_model.py tests/unit/dcp/test_routing_classifier.py tests/unit/dcp/test_routing_backend_policy.py`
- `git diff --check`
- Static no-go scan for network, shell, filesystem-write, backend-runner, MCP,
  GitHub, merge, queue-drain, and provider invocation terms.
- Diff scope review with `git diff --name-only` and `git diff --stat`.

## Stop Conditions

- A required enum member is missing and cannot be mapped to actual runtime enum
  values.
- Any change is needed in `routing_model.py` or `routing_classifier.py`.
- Policy code requires runner, connector, filesystem write, subprocess, network,
  provider, GitHub, MCP, Dopetask, or Task Orchestrator imports.

## Non-Claims

- Backend availability is not proven.
- Backend health is not proven.
- Backend execution is not wired.
- Supervisor review capacity is not proven.
- This packet does not make any backend authoritative.
