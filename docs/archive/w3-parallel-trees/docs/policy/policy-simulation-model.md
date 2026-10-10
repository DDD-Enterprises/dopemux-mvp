---
id: POLICY_SIMULATION_MODEL
title: Policy Simulation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Policy Simulation Model (explanation) for dopemux documentation and developer
  workflows.
---
# Policy Simulation Model

## Overview
The Policy Simulation framework allows operators to test candidate policy changes (e.g., readiness thresholds, escalation rules) against historical data to predict their impact on throughput and safety.

## Simulation Inputs
1. **Historical Proof Bundle**: Authoritative state snapshot from a prior run.
2. **Current Policy**: The baseline for comparison.
3. **Candidate Policy**: The proposed changes to be evaluated.

## Replay Logic
1. **Load Artifacts**: Parse `QUEUE_STATE_SNAPSHOT.json` and `FEEDBACK_INGEST_SNAPSHOT.json`.
2. **Inject Policy**: Override the active `QueueManager` engines with candidate settings.
3. **Recompute**: Generate a simulated `PRMergeReport` without performing any mutations.
4. **Diff**: Compare the simulated status, score, and blockers against the baseline.

## Outcome Metrics
- **Decision Delta**: Did the status change from `blocked` to `merge_ready` or vice-versa?
- **Escalation Delta**: Did the frequency of human-defer events change?
- **Risk Surface**: Did the simulation allow a previously blocked high-risk conflict?
