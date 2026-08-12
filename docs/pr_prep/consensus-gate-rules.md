---
id: CONSENSUS_GATE_RULES
title: Consensus Gate Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Consensus Gate Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Consensus Gate Rules

This is the local name for the independent audit gate defined in
[`contract-v2.md`](./contract-v2.md) §6 (Independent audit when required).

## Trigger Conditions
The consensus gate is NOT a default validator. It is only invoked when:
1. `risk_lane` is `L2_MATERIAL` or `L3_RED`.
2. `ambiguity_level` is `MEDIUM` or `HIGH`.
3. `change_profile` is `DIRTY_OR_AMBIGUOUS`.

## Consensus Operation
When triggered, the gate evaluates the overlapping code (e.g., between the current branch and a stash) or the high-risk migration logic to determine if PR creation is safe. The auditor must be independent of the implementer and must audit the exact frozen content head `C1` (§5, §6).

## Outcomes
Use the §6 audit verdicts, not a local pass/fail vocabulary:
- **PASS** or **PASS_WITH_RISKS** (non-blocking): the risk elements are deemed safe or intentional. Prep state may advance out of `PREP_BLOCKED`.
- **FAIL**, **NEEDS_SUPERVISOR**, or **SKIPPED** (when required): the risk is confirmed or unresolved. Prep state remains `PREP_BLOCKED` or `PREP_NEEDS_SUPERVISOR`.
