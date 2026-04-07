---
id: leantime_runtime_truth_drift_report
title: Leantime Runtime Truth Drift Report
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Current Leantime integration drift and evidence limits in this repository.
---
# Leantime - Drift Report

## Confirmed drift or evidence limits

1. The strongest repo evidence is adapter and contract logic, not the upstream Leantime application source.
2. JSON-RPC is clearly evidenced; a primary MCP contract is not.
3. Workflow authority remains outside Leantime, so PM-facing statuses can drift from workflow legality if reflection paths are not kept healthy.

## Impact

- Leantime can be treated as PM record authority with confidence.
- Internal Leantime storage or plugin-runtime specifics remain outside this repo's hard evidence set.
