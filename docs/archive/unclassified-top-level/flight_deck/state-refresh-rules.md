---
id: STATE_REFRESH_RULES
title: State Refresh Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: State Refresh Rules (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## State Refresh Rules

## When Mission State Is Considered Stale

Mission state is stale when any of the following is true:

1. `refreshed_at` timestamp is older than the artifact TTL (default: 300 seconds)
2. A meaningful event has occurred since last refresh (check update, comment, push)
3. A patch has been applied and `recomputed_at` has not been updated
4. Posture has changed since last refresh

## What Reloads Trigger

| Trigger Event | Reload Scope |
|---------------|-------------|
| Cycle start (REFRESH_STATE) | Full: posture, blockers, allowed_actions, artifact TTLs |
| `checks_passed` event | Posture recompute, blocker resolution |
| `checks_failed` event | Posture recompute, blocker injection |
| `patch_applied` event | Blocker resolution, allowed_actions recompute |
| `cycle_complete` event | Summary recompute, next_tactic selection |

## Debounce Rules

- Refresh calls within the same cycle are deduplicated (one refresh per cycle).
- Periodic background refresh: not triggered more than once per 60 seconds.
- Event-driven refresh: fires immediately on meaningful event, no debounce.

## Artifact TTL Concept

| Artifact | TTL | Expiry Behavior |
|----------|-----|-----------------|
| CI check status | 300s | Force refresh on next cycle |
| Blocker list | 60s | Re-derive from current state |
| Allowed actions | 30s | Recompute from posture + blockers |
| Posture | Persistent until event changes it | Never auto-expires |

## Invariants

1. A refresh never mutates PR state. It is always read-only.
2. `state_before` in `ClosedLoopTrace` captures pre-refresh snapshot.
3. `state_after` captures post-refresh + post-recompute snapshot.
4. If refresh fails, the cycle fails closed: `next_tactic = DEFER`.
