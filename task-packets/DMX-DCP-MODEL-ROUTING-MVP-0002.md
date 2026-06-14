---
id: DMX-DCP-MODEL-ROUTING-MVP-0002
title: Add pure-function routing classification engine
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-13'
last_review: '2026-06-13'
next_review: '2026-09-11'
prelude: Pure-function routing classification engine mapping task attributes into
  conservative RouteDecision data using the DCP routing domain model.
---

# DMX-DCP-MODEL-ROUTING-MVP-0002 — Routing Classification Engine

## Objective

Pure-function routing classification engine that maps task/request attributes
into a conservative `RouteDecision` skeleton using types from
`src/dopemux/dcp/routing_model.py`.

## Scope

**IN**
- `src/dopemux/dcp/routing_classifier.py` — pure classifier module
- `src/dopemux/dcp/__init__.py` — exports added
- `tests/unit/dcp/test_routing_classifier.py` — 57 focused unit tests
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0002.md` — this file

**OUT** — No runner execution, live backend, connector, GitHub, MCP, CI workflow,
or external package dependencies.

## Implementation Notes

- `RoutingClassificationInput` dataclass with conservative defaults
  (`has_unknown_authority=True`).
- `classify_route()` pure function: no I/O, no mutation of input, no external
  imports beyond stdlib + `routing_model`.
- Fail-closed rules enforced for all red-lane trigger flags.
- Proof/audit/escalation requirements increase monotonically with risk.
- Backend and connector fields remain inert enum data.

## Validation Summary

| Gate | Result |
|------|--------|
| compileall src/dopemux/dcp | PASS |
| pytest routing_model + routing_classifier (103 tests) | PASS |
| git diff --check | PASS |
| static no-go scan | PASS (all matches are docstrings/string constants) |
| diff scope | PASS (only allowed files changed) |

## Remaining Risks

- `classify_route` confidence capped at `"MEDIUM"` even for safe low-risk tasks;
  callers must raise confidence through their own evidence gates.
- `is_runnable()` is not a method on `RouteDecision` (model 0001R); callers
  derive runnability from `is_red_lane()` + `is_blocked()` + `status`.

## Explicit Non-Claims

The pure routing classifier maps structured local task attributes into
conservative `RouteDecision` data using the merged routing model types, with
fail-closed behavior and targeted unit coverage.

DCP routing plane is NOT production-ready. Backends are NOT integrated.
Connectors are NOT callable. MCP is NOT wired. PR cannot merge without
PR Steward / check harvest.

## Next Packet

`DMX-DCP-MODEL-ROUTING-MVP-0003` — Routing Backend Policy Map
