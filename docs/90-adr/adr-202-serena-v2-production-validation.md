---
id: ADR-202-serena-v2-production-validation
title: ADR 202 Serena V2 Production Validation
type: adr
owner: '@hu3mann'
last_review: '2026-03-31'
next_review: '2026-06-29'
author: '@hu3mann'
date: '2026-03-31'
prelude: Supersedes the earlier Serena v2 production-ready claim with current repo-truth deployment and validation constraints.
status: superseded
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-202: Serena v2 Production Validation

## Status

Superseded on `2026-03-31`.

## Historical note

An earlier version of this ADR treated the local `services/serena/` tree as production-ready and effectively deployed. That is no longer the authoritative repo interpretation.

## Current decision

Do not treat the local `services/serena/` implementation as the deployed Serena runtime or as production-ready by documentation alone.

Current repo truth:

- the repo-proven deployed Serena path is the dockerized wrapper under `docker/mcp-servers-source/serena/`
- the richer local `services/serena/` tree is an `implementation_candidate`
- the local candidate now has clean pytest collection and a passing non-skipped local suite surface, but database-gated tests still skip when local Postgres test initialization is unavailable
- the complete-system integration harness still contains synthetic target-achievement checks, so it must not be used as sole evidence of production readiness

## Consequences

- PM-plane dependency remains restricted to the sanctioned technical-context contract until deployment proof changes
- local Serena docs must distinguish deployed wrapper truth from the local implementation candidate
- future readiness claims must be backed by runtime proof, not architecture prose alone

## Current authority

- [capability-manifest.md](/Users/hue/code/dopemux-mvp/docs/systems/serena/capability-manifest.md)
- [deployment-alignment-and-sanctioned-contract.md](/Users/hue/code/dopemux-mvp/docs/systems/serena/deployment-alignment-and-sanctioned-contract.md)
- [runtime-candidate-inventory.md](/Users/hue/code/dopemux-mvp/docs/systems/serena/runtime-candidate-inventory.md)
