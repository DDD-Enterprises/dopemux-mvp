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
[`operator-contract.md`](./operator-contract.md) §6 (Independent audit when
required).

## Trigger conditions

The audit gate is not a default validator. It is invoked when:

1. `risk_lane` is `L2_MATERIAL` or `L3_RED` (§4).
2. Scope/drift/overlap classification (§5 S1) resolves to `CONFLICTING` or
   materially `UNKNOWN`.
3. The active Task Packet or repository policy otherwise requires it.

## Operation

When triggered, the gate binds one independent audit to the exact frozen
substantive content head `C1` (§5 S5, S6). The auditor must be independent of
the implementer.

## Outcomes

Use the §6 audit verdicts, not the legacy local pass/fail vocabulary:

- **PASS** or **PASS_WITH_RISKS** (explicitly non-blocking): prep state may
  advance out of `PREP_BLOCKED` / `PREP_COMPLETE_AWAITING_AUDIT` (§6 prep
  states).
- **FAIL**, **NEEDS_SUPERVISOR**, or **SKIPPED** when required: prep state
  remains `PREP_BLOCKED` or `PREP_NEEDS_SUPERVISOR`.

This stub is kept only so existing links into this filename keep resolving.
