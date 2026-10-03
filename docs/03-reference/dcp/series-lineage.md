---
id: REF-DCP-SERIES-LINEAGE
title: Series Lineage and Authority Map (R6 / 0000S)
type: reference
owner: Control Tower | Current
last_review: 2026-10-03
next_review: 2026-11-03
author: '@hu3mann'
date: '2026-10-03'
prelude: Series Lineage and Authority Map (R6 / 0000S) (reference) for dopemux documentation
  and developer workflows.
---
# Series Lineage and Authority Map

Records the canonical lineage and authority order for the DCP Model Routing series. Supersedes PR #1138.

## Lineage Progression

- **0000R / 0000S**: Reconciliation and series map (superseded and integrated into current main documentation).
- **0001R**: Domain model, red lanes, proof pointers (integrated on `main`).
- **0002 - 0006**: Classifier, backend policy, lane engine (integrated on `main`).
- **0007I / 0007T / 0007A**: Input adapters, test corpus, trusted adapter registry (integrated on `main`).
- **0008**: Inert backend runner contract and `RunnerAdapter` protocol (integrated in R6).
- **0009**: Runner capability registry with invocation disabled (integrated in R6).

## Authority Invariant

Never let extracted artifacts outrank the runtime they describe. Runtime code, config, compose wiring, tests, and active entrypoints govern system behavior.
