---
id: conport-kg-role-decision
title: ConPort KG Role Decision and Authority Boundary
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Defines the fail-closed role decision for conport-kg and restates the non-canonical status of graph outputs until a runtime-real service exists.
---
# ConPort KG Role Decision and Authority Boundary

## Role decision

Selected outcome: `quarantined_not_runtime_real`

Reason:

- no active runtime source
- no repo-proven deployment artifact
- no callable surface
- no validated dependency path

## Authority boundary

Until `conport-kg` becomes runtime-real, the architecture treats these as non-canonical:

- graph nodes
- graph indexes
- mirrors
- graph projections
- graph-derived summaries

No graph output may stand in for canonical ConPort decision, progress, or durable context truth.

## Rejected alternative

`projection_query_only` was not selected because the packet did not prove a live graph service.
