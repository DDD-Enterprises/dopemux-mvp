---
id: task_orchestrator_runtime_truth_drift_report
title: Task Orchestrator Runtime Truth Drift Report
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Confirmed Task Orchestrator drift between authority intent and current runtime behavior.
---
# Task Orchestrator - Drift Report

## High-value drifts

1. The service is the intended workflow authority, but the project workflow transition HTTP route still returns an explicit unavailable result.
2. Workflow persistence currently runs through dopecon-bridge custom-data categories, which weakens the clean boundary that says the bridge is adapter-only.
3. The PM-plane architecture assumes a canonical workflow authority, but the runtime still mixes direct service logic, PM helper delegation, and bridge-mediated persistence.

## Drift impact

- workflow authority is conceptually clear but not fully enforced at the runtime boundary
- bridge dependency creates authority confusion and complicates remediation sequencing
- supervisor docs must separate target ownership from present persistence substrate
