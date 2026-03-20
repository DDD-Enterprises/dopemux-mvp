---
id: SUPERVISED_OPS_MONITORING
title: Supervised Ops Monitoring
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Supervised Ops Monitoring (explanation) for dopemux documentation and developer
  workflows.
---
# Supervised Operations Monitoring

## Overview
Ongoing monitoring of the high-risk arbitration lane ensures that the GO_SUPERVISED_ONLY posture remains effective and safe. This document defines the metrics and rolling windows used for health reporting.

## Monitoring Windows
- **Last 5 Runs**: Immediate health snapshot.
- **Last 10 Runs**: Stability trend.
- **Current Release**: Cumulative performance for the active version.

## Core Metrics
1. **Signoff Compliance**: Percentage of supervised runs with a valid `OPERATOR_SIGNOFF`.
2. **Acceptance Rate**: Ratio of accepted vs. rejected guidance.
3. **Incident Rate**: Frequency of MAJOR or CRITICAL incidents.
4. **Runtime Stability**: Provider success rate (non-timeout/non-refusal).
5. **Posture Drift**: Actions taken outside the authorized `ALLOWED_ACTIONS_MATRIX`.

## Review Cadence
Operational health reports are generated after every 5 supervised runs or weekly, whichever comes first.
