---
id: SCALE_GATE_POLICY
title: Scale Gate Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Scale Gate Policy (explanation) for dopemux documentation and developer workflows.
---
# Scale-Gate Policy

## Overview
Scale-gates define the criteria for maintaining, restricting, or expanding the operational authority of the arbitration lane.

## Gate Decision Thresholds

| Decision | Criteria | Action |
| :--- | :--- | :--- |
| **CONTINUE_SUPERVISED** | Signoff Compliance = 100%, Incidents = 0. | Maintain current posture. |
| **PAUSE_AND_REVIEW** | Incident Rate > 5% OR Runtime Stability < 90%. | Suspend new cases; audit logs. |
| **RESTRICT_CASE_SET** | High override rate (> 30%) on specific tags. | Disable affected case categories. |
| **ROLLBACK_TO_ADVISORY** | Any safety breach or unauthorized mutation. | Immediate downgrade to advisory-only. |
| **EVALUATE_EXPANSION** | Acceptance > 90% across 20+ runs. | Propose expansion in next packet. |

## Rationale Requirements
Every scale-gate decision must cite the specific `OPS_HEALTH_REPORT` window and sample size.
