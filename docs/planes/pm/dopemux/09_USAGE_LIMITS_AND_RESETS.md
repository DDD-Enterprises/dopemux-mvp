---
title: "Usage Limits and Resets"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# Usage Limits Tracking and Reset Strategy

## Purpose

Operational truth: quotas reset and we want auto-switch-back behaviors.

## Scope

TODO: Define the scope of usage tracking and limit management.

## Non-negotiable invariants

TODO: List limit invariants (e.g., "never exceed the quota provided by the manual store").

## FACT ANCHORS (Repo-derived)

TODO: Link to limits.json and the logic that handles model switching on exhaustion.

## Open questions

TODO: List limits/reset unknowns and how to resolve them.

## Tracking model

Fields:
- runner_id
- model_id
- limit scopes (5hr / weekly / monthly)
- reset_at
- remaining_percent

TODO: Define the v1 JSON schema for limits.json.

## Policy behavior
- prefer included until exhausted
- fall back to codex credits
- then API cheapest
- when reset happens: suggest switch back automatically

TODO: Define the exact trigger thresholds (example: remaining_percent <= 10).

## Minimum implementation
- local limits.json store updated manually
- optional automation hook later

TODO: Define where stored per worktree and how it is loaded safely.

## Failure modes

TODO: wrong reset times, stale limits, incorrect fallback.

## Acceptance criteria

TODO: Simulate 5 scenarios and expected routing outcomes.
