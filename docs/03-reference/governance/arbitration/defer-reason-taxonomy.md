---
id: DEFER_REASON_TAXONOMY
title: Defer Reason Taxonomy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Defer Reason Taxonomy (explanation) for dopemux documentation and developer
  workflows.
---
# Defer Reason Taxonomy

## Overview
Every human escalation must be accompanied by one or more canonical defer reasons to guide the operator's review.

## Taxonomy

| Reason | Definition |
| :--- | :--- |
| **LOW_CONFIDENCE** | Adjudication results fell below policy-required confidence thresholds. |
| **INSUFFICIENT_EVIDENCE** | Essential code, review, or verification context was missing from the evidence bundle. |
| **UNRESOLVED_REVIEWER_INTENT** | Conflicting or ambiguous feedback from reviewers requires human clarification. |
| **HIGH_RISK_POLICY_GATE** | The conflict touches critical boundaries (Security, API, Migration) that mandate human review. |
| **UNSAFE_SYNTHESIS** | The proposed synthesized end-state is too complex for autonomous patching. |
| **MIGRATION_OR_SCHEMA_AMBIGUITY** | Database or schema changes require expert validation of implementation choice. |
| **VERIFICATION_BURDEN** | Required verification steps are too extensive or risky for automated execution. |
| **NO_SAFE_CANDIDATE** | All analyzed merge strategies were rejected by the Challenger or Arbiter. |
