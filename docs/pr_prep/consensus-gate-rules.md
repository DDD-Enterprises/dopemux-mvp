---
id: CONSENSUS_GATE_RULES
title: Consensus Gate Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Consensus Gate Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Consensus Gate Rules

## Trigger Conditions
The consensus gate is NOT a default validator. It is only invoked when:
1. `risk_hint` is `HIGH` or `CRITICAL`.
2. `ambiguity_level` is `MEDIUM` or `HIGH`.
3. `change_profile` is `DIRTY_OR_AMBIGUOUS`.

## Consensus Operation
When triggered, the gate evaluates the overlapping code (e.g., between the current branch and a stash) or the high-risk migration logic to determine if PR creation is safe.

## Outcomes
- **PASS**: The high-risk elements are deemed safe or intentional. Posture upgrades from `BLOCKED` to `DRAFT_RECOMMENDED`.
- **FAIL**: The risk is confirmed. Posture remains `BLOCKED` or downgrades to `HIGH_RISK_HANDOFF_REQUIRED`.
