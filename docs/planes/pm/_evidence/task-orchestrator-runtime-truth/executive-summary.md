---
id: task_orchestrator_runtime_truth_executive_summary
title: Task Orchestrator Runtime Truth Executive Summary
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Short supervisor-facing summary of the current Task Orchestrator runtime truth.
---
# Task Orchestrator - Executive Summary

- Task Orchestrator is still the correct target workflow authority.
- The active runtime is the FastAPI app in `services/task-orchestrator/app/main.py`.
- It exposes workflow reads and PM write helpers over HTTP.
- It enforces key fail-closed gates in service logic and tests.
- The two main runtime gaps are:
  - project-scoped workflow transition is still unbound
  - workflow persistence still depends on dopecon-bridge custom-data

This packet supports treating Task Orchestrator as workflow authority in architecture, while also treating its present persistence path as remediation debt.
