---
id: dopecon_bridge_runtime_truth_executive_summary
title: Dopecon Bridge Runtime Truth Executive Summary
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Short supervisor-facing summary of current dopecon-bridge runtime truth.
---
# dopecon-bridge - Executive Summary

- dopecon-bridge is still best understood as router, adapter, and translation layer.
- Its own route module explicitly rejects canonical authority over tasks, workflow, decisions, and progress.
- It enforces useful fail-closed behavior for workflow-significant PM mutations.
- The main drift is external: other services, especially Task Orchestrator persistence, still depend on bridge custom-data flows in ways that muddy the boundary.
