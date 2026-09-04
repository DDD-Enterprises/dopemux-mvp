---
id: second-brain-knowledge-compiler-materialized-wiki-v1
title: "Second Brain Knowledge Compiler and Materialized Wiki V1"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Apply accepted Second Brain authority law to derived claims, materialized Wiki pages, and receipts.
---

# Second Brain Knowledge Compiler and Materialized Wiki V1

This reference applies accepted ADR-SB-001 through ADR-SB-010 without changing
their decision bodies.

## Pipeline

1. Input cites dereferenced, digest-bound canonical source snapshots.
2. Provider policy evaluates before disclosure; `UNKNOWN` denies.
3. Compiler emits source-linked claims.
4. Only dereferenced, non-conflicting claims become eligible for materialization.
5. Materializer writes managed Wiki regions and a deterministic receipt.
6. Purge propagates to derived surfaces and remains receipt-bound.

## Authority

Compiler input declares output authority `DERIVED_NON_CANONICAL`. Compiled
claims, Wiki pages, and receipts keep that label. Wiki is a derived read model,
not a canonical decision, progress, PM, workflow, chronicle, or retrieval
writer. Canonical source wins every conflict. Silent write-back is forbidden.

Managed and human-authored regions stay distinguishable. Freshness, snapshot
revisions, claim references, content hashes, and purge state remain explicit.
