---
id: TP-DOPECONTEXT-VOYAGE4-0001
title: Tp Dopecontext Voyage4 0001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-22'
last_review: '2026-07-22'
next_review: '2026-10-20'
prelude: Task packet for Voyage 4 model modernization, token accounting, and
  deterministic failure-safe dope-context document indexing.
---
# Task Packet: TP-DOPECONTEXT-VOYAGE4-0001

## Objective

Modernize the canonical dope-context Voyage integration and make document
indexing token-aware, dimension-safe, deterministic, and failure-preserving
without replacing the Python, FastMCP, and Qdrant architecture.

## Status

`IMPLEMENTATION_CANDIDATE`

Completion requires current-head CI, embedded audit, and PR Steward proof.

## Risk

`MEDIUM-HIGH`

Model and vector-schema changes can contaminate derived Qdrant indexes even
though source files remain authoritative.

## Scope

### IN

- current Voyage model registry and defaults
- model-specific token accounting
- embedding and contextual cache correctness
- token-bounded request partitioning
- reranker token pricing
- docs index version and fingerprint metadata
- deterministic docs point IDs
- failure-safe document replacement
- exact-source stale cleanup
- focused tests, audit, and container constraints

### OUT

- replacing Qdrant with Milvus
- wholesale upstream Claude Context import
- production collection migration or deletion
- broad MCP server refactoring
- code chunker redesign
- live Voyage calls
- unrelated systems or dependencies

## Invariants

- Source code and documents remain authoritative.
- Qdrant collections remain derived retrieval artifacts.
- dope-context remains retrieval authority only.
- Existing document vectors are not deleted before replacements are ready.
- Model, dimension, dtype, and chunker changes remain visible.
- Context-3 remains an explicit bounded rollback.
- Code defaults to `voyage-code-3`.
- API token accounting and MCP output budgeting remain separate.
- No secret or API key enters source, tests, logs, or proof.

## Allowed Files

- `services/dope-context/Dockerfile`
- `services/dope-context/constraints.txt`
- `services/dope-context/src/embeddings/model_registry.py`
- `services/dope-context/src/embeddings/voyage_embedder.py`
- `services/dope-context/src/embeddings/contextualized_embedder.py`
- `services/dope-context/src/utils/model_tokenizer.py`
- `services/dope-context/src/utils/token_budget.py`
- `services/dope-context/src/rerank/voyage_reranker.py`
- `services/dope-context/src/pipeline/docs_pipeline.py`
- `services/dope-context/tests/test_docs_pipeline_invariants.py`
- `services/dope-context/tests/test_voyage_modernization.py`
- `docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md`
- `task-packets/dope-context/TP-DOPECONTEXT-VOYAGE4-0001.md`

## Required Chain

`analyze -> apilookup -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

## Plan

1. Add one current Voyage capability, pricing, and dimension registry.
2. Add model-aware token counting with conservative fallback.
3. Modernize embedding, contextualized embedding, and rerank clients.
4. Persist an explicit document index compatibility fingerprint.
5. Replace random IDs and pre-delete cleanup with deterministic safe upserts.
6. Add focused migration and regression tests.
7. Constrain the service image to the compatible Voyage SDK.
8. Run CI, embedded audit, and PR Steward against the final head.

## Exact Commands

```bash
git status --short --branch
git diff --stat
git diff --check
python -m compileall -q services/dope-context/src
python -m py_compile services/dope-context/tests/test_docs_pipeline_invariants.py
python -m py_compile services/dope-context/tests/test_voyage_modernization.py
PYTHONPATH=services/dope-context python -m pytest -q \
  services/dope-context/tests/test_docs_pipeline_invariants.py \
  services/dope-context/tests/test_voyage_modernization.py
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
docker build -f services/dope-context/Dockerfile \
  -t dope-context:tp-voyage4 .
git diff --stat
git diff
git status --short --branch
```

## Acceptance Criteria

- Docs default to `voyage-context-4`.
- Code defaults to `voyage-code-3`.
- Reranking defaults to `rerank-2.5`.
- Cache identity includes model and vector shape.
- Voyage request accounting uses model-aware tokenization when available.
- Request batching respects count and token ceilings.
- Reranker cost uses processed tokens.
- Docs payloads record actual model, dimension, dtype, schema, and fingerprint.
- Docs point IDs are deterministic.
- Failed embedding does not pre-delete the last good document index.
- Same-basename documents cannot delete one another.
- Focused and service tests pass.
- Embedded audit is PASS or non-blocking PASS_WITH_RISKS.
- PR Steward emits READY before merge.

## Proof Requirements

Return verbatim:

- base and final head SHA
- `git status` before and after
- `git diff --stat`
- `git diff`
- every validation command and exit code
- test, Docker, and CI output
- embedded audit identity, invocation, verdict, and findings
- PR metadata, reviews, threads, checks, and merge readiness

## Rollback

1. Revert the packet commits.
2. Use `DOPE_CONTEXT_DOC_EMBED_MODEL=voyage-context-3` only for bounded rollback.
3. Keep old collections until a separately approved migration.
4. Restore the previous collection pointer instead of rewriting source data.
5. Never mix context-3 and context-4 vectors in one collection.

## Stop Conditions

Stop if:

- the base moves with overlapping dope-context changes
- a required file is outside the allowlist
- the installed SDK cannot support context-4 parameters
- collection vector size conflicts with the requested dimension
- any operation would delete a complete collection
- a live validation would expose an API key
- embedded audit returns FAIL or NEEDS_SUPERVISOR
- proof or checks are stale relative to the PR head

## Current Evidence

### OBSERVED

- Isolated focused test reconstruction: `15 passed`
- Python module compilation: PASS
- No live Voyage request was made.
- No production Qdrant collection was touched.

### UNKNOWN

- complete dope-context suite
- Docker build result
- embedded auditor verdict
- final GitHub CI state
- PR Steward merge readiness
