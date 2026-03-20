---
id: TACTIC_SELECTION_MODEL
title: Tactic Selection Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tactic Selection Model (explanation) for dopemux documentation and developer
  workflows.
---
# Tactic Selection Model

## Overview

Next-tactic selection applies a strict priority ordering to the `allowed_actions` set
derived from current posture and blockers. The system fails closed: if no safe tactic
is found, the output is always `DEFER`.

## Priority Ordering

Tactics are evaluated in this order (highest to lowest priority):

| Priority | Tactic | Safe to Auto-Stage | Notes |
|----------|--------|--------------------|-------|
| 1 | `MERGE` | No | Requires signoff |
| 2 | `REQUEST_CHANGES` | No | Operator communication |
| 3 | `APPROVE` | No | Requires operator confirmation |
| 4 | `APPLY_FIX` | Conditional | Class-dependent |
| 5 | `REQUEST_REVIEW` | Yes | Safe to surface |
| 6 | `DEFER` | N/A | Fallback, always safe |

## Selection Algorithm

```
for tactic in TACTIC_PRIORITY:
    if tactic in allowed_actions:
        return {tactic, safe_to_auto_stage}
# Fallback
return {DEFER, safe=False}
```

## Safe-to-Auto-Stage Logic

A tactic is `safe_to_auto_stage = True` only if:
- It is NOT in the set `{MERGE, APPLY_FIX, APPROVE}`
- AND posture is not HOLD

This means `REQUEST_REVIEW` can surface automatically.
`MERGE`, `APPLY_FIX`, and `APPROVE` always require explicit operator staging.

## Fallback to DEFER

`DEFER` is returned (with `safe_to_auto_stage = False`) when:
1. `allowed_actions` is empty
2. No tactic in the priority list appears in `allowed_actions`
3. An exception occurs during selection (fail-closed)

## Posture → Allowed Actions Relationship

| Posture | Allowed Action Set |
|---------|--------------------|
| HOLD | [] (empty — only DEFER available) |
| CAUTION | [REQUEST_REVIEW, DEFER] |
| GO_SUPERVISED_ONLY | [APPLY_FIX (safe classes), REQUEST_REVIEW, REQUEST_CHANGES, DEFER] |
| GO_FULL_AUTO | All actions except MERGE (always staged) |
