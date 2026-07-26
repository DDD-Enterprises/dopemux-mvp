---
id: TP-DOPECONTEXT-VECTOR-SPACE-0004
title: Tp Dopecontext Vector Space 0004
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Benchmark-gated decision closing the F-001 blocker, choosing between
  contextualized and code-3 vectors for code content retrieval.
---
# Task Packet: TP-DOPECONTEXT-VECTOR-SPACE-0004

## Objective

Decide, on evidence, which embedding model owns the code `content_vec` space,
and make index and query provably agree. This closes **F-001**, the remaining
blocker from the PR #1112 post-merge audit.

## Status

`DECISION_REQUIRED`

This packet is **not** implementable as written. It requires an operator
decision and a budget approval before any code changes. Do not execute the
implementation half until the benchmark has run and a direction is chosen.

## Risk

`HIGH`

Determines the primary code-retrieval signal. Choosing wrong degrades every
`search_code` result with no visible failure.

## The Finding

`indexing_pipeline.py:283-289` embeds code content through
`ContextualizedEmbedder.embed_document(model="voyage-context-3")`, which
`resolve_context_model` rewrites to `voyage-context-4` on the
`contextualized_embeddings` endpoint. `server.py:1205-1209` embeds the content
query with `voyage-code-3` on the standard `embeddings` endpoint.

Both produce 1024-dimensional vectors, so Qdrant stores and searches them
without complaint. `content_weight` dominates `SearchProfile.implementation()`.
There is no error, no log, and no metric.

Voyage documentation is **silent** on cross-family comparability. The only
stated compatibility concerns `input_type` variants of the same model.

This is pre-existing. PR #1112 changed which contextualized model is used, not
the mismatch itself.

## Evidence Bearing on the Decision

Recorded because it cuts against the worst-case reading and should inform,
not be suppressed:

`voyage-code-3` and `voyage-context-4` ship an **identical tokenizer and
vocabulary** — both 151,665 entries, and a mixed code and CJK probe encodes to
byte-identical ids. That indicates common lineage and shared input processing.

It does **not** establish a shared output space. A common vocabulary constrains
the input side only; two models with identical vocabularies can still project
into entirely unaligned spaces. But it means the realistic outcome may be
partial degradation rather than noise, which is exactly why the benchmark is
worth running instead of assumed.

## The Two Directions

**A. Query with the contextualized model.** Keep contextualized document
vectors for code content and switch `search_code`'s content query to the same
contextualized model and endpoint. Preserves whatever document-awareness
advantage the contextualized model provides.

**B. Index with `voyage-code-3`.** Embed code content with the same model
already used for title and breadcrumb. Provably consistent, matches upstream
`zilliztech/claude-context`, requires no live calls to justify.

`TP-DOPECONTEXT-VOYAGE4-REPAIR-0002` deliberately did not implement either.

## Scope

### IN

- an offline retrieval benchmark comparing A and B on a fixed query set
- a recorded decision with the measured numbers behind it
- implementing the chosen direction so index and query agree
- a test asserting index/query model agreement for all six named vectors
- updating the modernization audit document with the outcome

### OUT

- the collection gate (see `TP-DOPECONTEXT-COLLECTION-GATE-0003`)
- chunking strategy changes
- reranker changes
- any change before the benchmark has produced numbers

## Invariants

- For every named vector, index model, endpoint, dimension, and dtype equal the
  query model, endpoint, dimension, and dtype.
- Equal dimensionality is never accepted as evidence of compatibility.
- The decision is recorded with the measurements that produced it, not with a
  rationale alone.
- No production collection is migrated by this packet.

## Prerequisites — blocking

1. **Budget approval for live Voyage calls.** The benchmark requires real
   embedding requests. Cost scales with corpus and query-set size and must be
   estimated and approved before execution. No live call may be made without it.
2. **`TP-DOPECONTEXT-TEST-HARNESS-0005`** should land first. Nine MCP tool tests
   currently fail with `TypeError: 'FunctionTool' object is not callable`,
   which is precisely the surface needed to verify this end to end. Without it,
   verification is limited to the function level.

## Allowed Files

- `services/dope-context/src/pipeline/indexing_pipeline.py`
- `services/dope-context/src/mcp/server.py`
- `services/dope-context/tests/test_vector_space_invariants.py`
- `docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md`
- `docs/03-reference/systems/dope-context/vector-space-benchmark-<date>.md`
- `task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md`

## Required Chain

`analyze -> apilookup -> thinkdeep -> challenge -> consensus -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

`consensus` is required here because this is a judgement call with two
defensible answers, not a defect with one correct fix.

## Plan

1. Assemble a fixed query set with known-relevant targets drawn from this
   repository. Record it so the benchmark is repeatable.
2. Build both configurations into isolated, clearly named benchmark collections.
   Never write to a production collection.
3. Measure recall@k and MRR for A and B on the same query set. Also measure the
   current broken configuration as a control, to quantify what the mismatch
   actually costs.
4. Record the numbers, the query set, the corpus, and the date.
5. Choose a direction on the measurements. If A and B are within noise, choose
   B for consistency with upstream and lower operational complexity.
6. Implement the chosen direction so index and query agree.
7. Add the invariant test for all six named vectors.
8. Update the modernization audit document with the outcome and delete the
   "benchmark the current mixed code-vector strategy" residual item.

## Exact Commands

```bash
git status --short --branch
python -m compileall -q services/dope-context/src
PYTHONPATH=services/dope-context python -m pytest -q \
  services/dope-context/tests/test_vector_space_invariants.py
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
git diff --stat
git diff
```

Benchmark commands are intentionally not specified here; they depend on the
approved budget and corpus and must be recorded verbatim in the benchmark
document when run.

## Acceptance Criteria

- A benchmark document exists recording query set, corpus, date, and measured
  recall@k and MRR for direction A, direction B, and the current control.
- A direction is chosen and the choice cites the numbers.
- Code `content_vec` index model, endpoint, dimension, and dtype equal the
  `search_code` content query model, endpoint, dimension, and dtype.
- A test asserts index/query agreement for all six named vectors.
- Audit adversarial test A14 flips from FAIL to PASS.
- No production collection was written during benchmarking.
- The suite gains no failure beyond the pre-existing ones.

## Proof Requirements

Return verbatim: the benchmark document, every benchmark command with exit code,
the measured numbers for all three configurations, the chosen direction with its
justification, base and final head SHA, `git diff`, the A14 result, and PR
metadata with checks. Also return the actual Voyage spend against the approved
estimate.

## Rollback

1. Revert the implementation commits; the benchmark document stays as evidence.
2. Delete benchmark collections explicitly; never leave them adjacent to
   production collections.
3. Because index and query move together, rollback restores the previous
   configuration wholesale rather than leaving a split.

## Stop Conditions

Stop if:

- budget approval for live calls has not been granted
- the benchmark would write to a production collection
- measured spend exceeds the approved estimate
- A and B differ by less than the measurement noise and no tiebreak is agreed
- the control measurement shows the current mismatch is NOT degrading results,
  which would falsify the finding and require re-analysis before any change
- embedded audit returns FAIL or NEEDS_SUPERVISOR

## Current Evidence

### OBSERVED

- index model resolves to `voyage-context-4` on the contextualized endpoint
- query model is `voyage-code-3` on the standard endpoint
- both 1024-dimensional; Qdrant accepts both silently
- vendor documentation is silent on cross-family comparability
- the two models share an identical tokenizer and 151,665-entry vocabulary
- upstream `zilliztech/claude-context` uses one model for both sides

### UNKNOWN

- the empirical retrieval cost of the mismatch
- whether contextualized code content outperforms `voyage-code-3` enough to
  justify the extra endpoint and complexity
- the cost of the benchmark itself
