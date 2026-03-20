---
id: FAILURE_POLICY
title: Failure Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Failure Policy (explanation) for dopemux documentation and developer workflows.
---
# Arbitration Failure Policy

## Failure Taxonomy

| Failure Class | Definition | Action |
| :--- | :--- | :--- |
| **TIMEOUT** | Provider failed to respond within budget. | Retry once, then DEFER. |
| **REFUSAL** | Model refused to answer due to safety or policy. | Immediate DEFER. |
| **INVALID_JSON** | Output could not be parsed as JSON. | Retry once, then DEFER. |
| **SCHEMA_INVALID** | JSON parsed but missing mandatory fields. | Immediate DEFER. |
| **AUTH_ERROR** | Provider credentials failed or expired. | Immediate DEFER. |
| **RATE_LIMIT** | Exceeded provider quota. | Exponential backoff or DEFER. |

## Fail-Closed Rules
1. **Never Fallback to Weak Logic**: If a high-reasoning model fails, do not silently downgrade to a faster, less capable model without explicit policy approval.
2. **Explicit Defer Reason**: All runtime-triggered deferrals must cite the failure class and provider metadata in the `HumanEscalationPacket`.
3. **Trace Retention**: All failed payloads and error logs must be preserved in `proof/pr_merge/arbitration/`.
