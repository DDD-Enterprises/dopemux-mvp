---
id: LIVE_TRIAL_GUARDRAILS
title: Live Trial Guardrails
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Live Trial Guardrails (explanation) for dopemux documentation and developer
  workflows.
---
# Live Trial Guardrails

## Overview
These guardrails ensure that the high-risk arbitration lane operates safely during the supervised live trial.

## Safety Rules
1. **Advisory-First**: All lane outputs are advisory only. No code or state mutation may occur without explicit human approval.
2. **Fail-Closed**: Any runtime, schema, or evidence failure MUST result in an immediate `DEFER_TO_HUMAN` decision.
3. **Blast Radius Limits**:
    - **CRITICAL**: Defer-only mode.
    - **HIGH**: Advisory-only mode.
    - **MEDIUM**: Supervised patch-planning allowed.
4. **Operator Authority**: Human integrators may override any model-role decision with a recorded rationale.
5. **No Policy Drift**: The lane must not attempt to modify repo-level policies or branch protection rules.

## Abort Triggers
The trial must be suspended if:
- Any unauthorized mutation is detected.
- Incident rate (misleading or unsafe output) exceeds 2%.
- Runtime stability falls below 95% success rate.
