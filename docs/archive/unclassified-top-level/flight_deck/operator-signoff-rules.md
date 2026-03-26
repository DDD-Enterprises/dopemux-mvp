---
id: OPERATOR_SIGNOFF_RULES
title: Operator Signoff Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Signoff Rules (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Flight Deck Operator Sign-off Rules

## Overview
Tactical actions (Patching, Code implementation) require formal operator sign-off.

## Sign-off Requirements
1. **Intelligence Review**: The operator must review the `MISSION INTELLIGENCE` panel before action.
2. **Strategy Alignment**: The action must match the `PRIMARY DIRECTIVE` unless an override is recorded.
3. **Patch Verification**: Synthesized code must be visually inspected in the "Proposed Implementation" card.
4. **Log Requirement**: Every sign-off must include a rationale string.

## Operational Ledger
All sign-offs are logged to `proof/pr_merge/flight_deck/ops/OPERATOR_SIGNOFF_LOG.jsonl`.
