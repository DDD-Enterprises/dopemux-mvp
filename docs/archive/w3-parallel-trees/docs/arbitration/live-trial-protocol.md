---
id: LIVE_TRIAL_PROTOCOL
title: Live Trial Protocol
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Live Trial Protocol (explanation) for dopemux documentation and developer
  workflows.
---
# Live Trial Protocol

## Overview
The supervised live trial transitions the arbitration lane from shadow evaluation to informing real merge decisions under human control.

## Execution Workflow
1. **Selection**: Choose cases from the `SHADOW_READY` shortlist.
2. **Assignment**: Assign an `operator_owner` and `trial_mode` (ADVISORY, DEFER_ONLY, or SUPERVISED_PATCH).
3. **Execution**: Run the full arbitration lane via `pr-fix --id <id> --runtime LIVE`.
4. **Handoff**: Present the `HumanEscalationPacket` or `MergeExecutionPlan` to the operator.
5. **Feedback**: Capture operator acceptance, overrides, and usefulness notes.
6. **Logging**: Record incidents and runtime stability in `proof/pr_merge/arbitration/live/`.

## Trial Modes
- **LIVE_ADVISORY**: Full lane runs; no automated mutation.
- **LIVE_SUPERVISED_PATCH_PLAN**: Lane may suggest patches; operator must manually apply.
- **LIVE_DEFER_ONLY**: Lane restricted to generating deferral summaries.
