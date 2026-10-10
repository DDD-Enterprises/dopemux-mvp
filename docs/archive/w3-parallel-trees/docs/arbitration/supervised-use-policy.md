---
id: SUPERVISED_USE_POLICY
title: Supervised Use Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Supervised Use Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Supervised Use Policy

## Overview
This policy governs how operators interact with and use the outputs of the High-Risk Arbitration Lane in production environments.

## Operating Principles
1. **Advisory Default**: Recommendations are starting points for human review, not final verdicts.
2. **Audit Requirement**: Operators must verify the evidence bundle references before accepting a merge plan.
3. **Rationalized Overrides**: Any disagreement with the Arbiter or Consensus Decision must be logged with a rationale.
4. **Verification Enforcement**: Passing CI/local verification is a non-negotiable prerequisite for any supervised merge.

## Permitted Actions (Supervised)
- Using the **Evidence Pack** to accelerate manual diff review.
- Accepting an **Arbiter Decision** for low-complexity semantic overlaps.
- Manually applying a **Synthesized Patch** after line-by-line inspection.
- Enqueuing a PR based on a validated **Merge Execution Plan**.

## Forbidden Actions
- Automatic merging of high-risk conflicts.
- Silent suppression of Challenger objections.
- Bypassing the `HumanReviewEngine` handoff for `HIGH_RISK` cases.
