---
id: dopecon_bridge_runtime_truth_drift_report
title: Dopecon Bridge Runtime Truth Drift Report
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Confirmed dopecon-bridge drift between intended adapter-only role and present runtime usage patterns.
---
# dopecon-bridge - Drift Report

## High-value drifts

1. The service states that it must not be canonical for tasks, workflow, decisions, or progress, but Task Orchestrator currently uses bridge custom-data APIs for workflow persistence.
2. The bridge still exposes many mixed-purpose route groups, which increases the risk of consumers treating the bridge as more authoritative than intended.
3. The PM-plane architecture depends on bridge fail-closed behavior to defend the authority boundary, which means any relaxation here would have outsized impact.

## Impact

- dopecon-bridge should still be modeled as adapter-only
- but remediation must remove consumer dependence on bridge-local or bridge-mediated substitute truth paths
