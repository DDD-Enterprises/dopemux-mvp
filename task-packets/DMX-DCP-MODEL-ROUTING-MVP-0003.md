---
id: DMX-DCP-MODEL-ROUTING-MVP-0003
title: Add pure backend policy recommendation map
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Pure backend policy recommendation map for safe DCP RouteDecision data,
  preserving fail-closed behavior and adding no backend invocation path.
---

# DMX-DCP-MODEL-ROUTING-MVP-0003 - Routing Backend Policy Map

## Objective

Add a pure, deterministic backend policy map that recommends inert backend
preference data for already-classified `RouteDecision` values.

## Scope

**IN**
- `src/dopemux/dcp/routing_backend_policy.py` - pure backend policy data module
- `src/dopemux/dcp/__init__.py` - exports added
- `tests/unit/dcp/test_routing_backend_policy.py` - focused unit tests
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md` - this note

**OUT**
- No backend invocation
- No runner, connector, tool, GitHub, queue, scheduling, or service integration
- No model or classifier contract edits
- No dependency, workflow, or CI edits

## Implementation Notes

- `BackendPolicyRecommendation` is frozen dataclass data.
- `BackendPolicyRule` is frozen dataclass data.
- `select_backend_policy()` treats `RouteDecision.is_runnable()` as a hard gate.
- `BackendKind.NONE` is returned for blocked, unknown, red-lane,
  escalation-required, proof-stopped, and forbidden-action decisions.
- Safe code, docs/design, and audit routes receive backend preference data only.
- High-risk or supervisor routes return no executable backend recommendation.

## Validation Summary

| Gate | Result |
|------|--------|
| compileall src/dopemux/dcp | PASS |
| pytest routing_model + routing_classifier + routing_backend_policy | PASS - 153 tests |
| pytest tests/unit/dcp | PASS - 153 tests |
| git diff --check | PASS |
| static no-go scan | PASS - no matches |
| diff scope | PASS - packet allowlist only |
| embedded audit | PASS_WITH_RISKS |

## Remaining Risks

- Backend preference data is not authorization. Any future caller must keep
  approval, proof, and runtime gates outside this module.
- There is no supervisor-specific `BackendKind`; supervisor-required decisions
  intentionally fall back to `BackendKind.NONE`.

## Explicit Non-Claims

The backend policy map recommends inert backend preference data for safe
`RouteDecision` shapes and fails closed for blocked, unknown, red-lane,
escalation-required, stale-proof, missing-proof, and stop-condition decisions.

DCP routing plane is not production-ready. Backends are not integrated.
Connectors are not callable. MCP is not wired. This policy does not authorize
execution.

## Next Packet

`DMX-DCP-MODEL-ROUTING-MVP-0004` - Routing Policy Fixture Corpus
