---
id: pm-plane-synthesized-read-contracts
title: PM Plane Synthesized Read Contracts
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Canonical source, supporting lanes, and normalization rules for synthesized PM-plane reads.
---
# PM Plane Synthesized Read Contracts

## `pm_get_project_snapshot`

- canonical source: `Leantime`
- supporting sources: `Task Orchestrator`, `ConPort`

## `pm_get_work_item_360`

- canonical source: `Leantime`
- supporting sources: `Task Orchestrator`, `ConPort`, `dope-memory`, `Serena`, `dope-context`

## `pm_get_decision_timeline`

- canonical source: `ConPort`
- supporting sources: `dope-memory`, `Leantime`

## `pm_get_execution_context`

- canonical source: `Task Orchestrator`
- supporting sources: `Leantime`, `ConPort`, `Serena`, `dope-memory`

## Shared rule

Every synthesized contract preserves lane-by-lane provenance instead of collapsing all planes into one record.
