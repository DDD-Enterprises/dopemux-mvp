---
id: AGENT_TEMPLATE
title: Agent Template
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Agent Template (explanation) for dopemux documentation and developer workflows.
---
# Vibe Agent Template for PR-Prep-Specialist

Superseded by [`operator-contract.md`](../../operator-contract.md).

This file previously defined a fixed six-checkpoint execution sequence, a
mandatory `BRANCH_STATE.json` / ... / `PR_HANDOFF_BUNDLE.json` artifact per
checkpoint, `Draft Posture: {CREATE_READY/DRAFT_RECOMMENDED/BLOCKED}`, and
`Risk Hint: {LOW/MEDIUM/HIGH}` as current agent behavior, plus a
`PACKAGE_ONLY → DRAFT_FIRST → SUPERVISED_FINAL` posture progression. That
ceremony, risk vocabulary, and posture model are retired.

## Current behavior

Vibe's behavior for `pr-prep-specialist` is the same conditional S0-S8
workflow, `L0-L3` risk lanes, prep states, and V2 handoff schema defined
canonically in [`operator-contract.md`](../../operator-contract.md). There
is no fixed checkpoint count or fixed artifact list, no `risk_hint`
LOW/MEDIUM/HIGH field, and no `SUPERVISED_FINAL` posture that grants
non-draft or merge-ready PR creation independent of the operator contract's
`DRAFT_ONLY` default (§S4) and explicit operator/Task Packet authorization.

## Platform-specific notes

- **Plan mode**: Vibe may still use a text-only planning phase that stops
  before any repository write and waits for explicit operator go-ahead;
  this is a Vibe invocation convention, not a separate behavioral contract.
- **Operator review**: Vibe may still solicit an explicit operator decision
  (proceed / stop / escalate / retry) between workflow stages; the decision
  vocabulary and its consequences are governed by `operator-contract.md`
  §5-§6, not by a Vibe-specific state machine.
- **Output format**: whatever the actual run produces per the V2 handoff
  schema (`operator-contract.md` §9).

This stub is kept only so existing links into this filename keep resolving.
