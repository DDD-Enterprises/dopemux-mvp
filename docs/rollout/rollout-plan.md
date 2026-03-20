---
id: ROLLOUT_PLAN
title: Rollout Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Rollout Plan (explanation) for dopemux documentation and developer workflows.
---
# Rollout Plan: PR Merge Specialist

## Strategy
Safe, evidence-first adoption across selected pilot repositories and agent environments. The rollout follows an incremental tier model to minimize operational risk.

## Phases
1. **Phase 1: Discovery (Tier 0)**: Enable advisory-only mode in pilot repos. Collect baseline telemetry without any mutations.
2. **Phase 2: Bounded Mutation (Tier 1)**: Enable safe mutations (metadata, body updates, local verification) behind gated feature flags.
3. **Phase 3: Managed Remediation (Tier 2)**: Enable review replies and guarded thread resolutions for high-sophistication operators.
4. **Phase 4: Full Enqueue (Tier 3)**: Enable automated queue admission under strict platform policy.

## Success Criteria
- Zero unauthorized mutations.
- 100% adherence to the Operator Contract.
- Demonstrable throughput improvement in pilot repos.
- High operator confidence in generated remediation plans.
