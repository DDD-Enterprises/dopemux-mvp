---
id: TP-DOPECONTEXT-SERVICE-HARDENING-0006
title: Tp Dopecontext Service Hardening 0006
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Remaining medium and low severity hardening from the PR 1112 audit,
  covering SDK drift, silent degradation, caches, and tokenizer retries.
---
# Task Packet: TP-DOPECONTEXT-SERVICE-HARDENING-0006

## Objective

Close the medium and low severity findings from the PR #1112 post-merge audit
that neither blocked acceptance nor fit inside the bounded repair. Each is
independently small; together they remove three classes of silent failure —
version drift, invisible degradation, and unbounded growth.

## Status

`IMPLEMENTATION_CANDIDATE`

Closes **F-006, F-010, F-011, F-012, F-014, F-015**. No dependency on the two
blocker packets; may land in parallel.

## Risk

`MEDIUM`

Touches dependency resolution and the reranker request shape. The SDK bump is
the only part that can break the container.

## Findings Covered

### F-010 — three environments, three SDKs

`constraints.txt` pins `voyageai>=0.5.0,<0.6` for the **image only**.
`pyproject.toml` still declares `voyageai>=0.2.0`, so the repository and CI
resolve **0.3.7**, whose `contextualized_embed` lacks the auto-chunking
parameters the code offers. The running container has a third version, **0.4.1**.

Separately, `rerank()` has **no `return_documents` parameter in any version**.
`voyage_reranker._api_rerank` passes it, so every rerank call raises `TypeError`
and takes the compatibility branch — which also strips `truncation`. The primary
path is dead code.

### F-011 — rerank failure is invisible

Any exception returns the original ordering with `tokens_used=0` and
`cost_usd=0.0`, and `RerankResponse` carries no failure indicator. A persistently
failing reranker degrades quality permanently while the MCP response looks normal.

### F-014 — reranker limits unenforced

Vendor documents a per-query limit of 8,000 tokens and a combined query plus
document limit of 32,000. Neither is enforced. An oversized query produces an API
rejection that F-011 then swallows.

### F-006 — undeclared tokenizer network dependency

`VoyageTokenCounter` calls `voyageai.Client.tokenize`, which is
`Tokenizer.from_pretrained(f"voyageai/{model}")` — an HTTP fetch to
`huggingface.co`. The SDK's `lru_cache` does not memoize the raised failure, so a
blocked Hub costs one failed request **per unique chunk**. Neither the Dockerfile
nor the service documentation declares this egress requirement.

### F-012 — unbounded caches, shared references

Both embedding caches are unbounded dicts with lazy TTL eviction only on key
hit. Expired entries for texts never queried again are never reclaimed. Cached
responses hand out the stored embedding list **by reference**, so an in-place
mutation by any consumer corrupts the cache for every later hit.

### F-015 — point-ID determinism depends on `workspace_id`

`_point_id_for_chunk` builds `dope-context:{workspace_id}:{doc_id}:{ordinal}`.
Every tool path passes `str(workspace)`, but the startup-initialised
`_docs_pipeline` global passes `os.getenv("WORKSPACE_ID", "default")`. Two roots
sharing that value collide on point identity. The global is currently unreached,
so the exposure is latent. `WORKSPACE_HASH_OVERRIDE` provides a second mechanism
by which two workspaces can be forced onto one collection.

## Scope

### IN

- `voyageai>=0.5.0,<0.6` in `pyproject.toml`, lockfile refreshed
- remove `return_documents` from the rerank call and the `TypeError` retry
- a degradation indicator on `RerankResponse`, surfaced in MCP metadata
- explicit 8,000-token query validation for reranking
- tokenizer loaded once per model with the failure memoized, plus a documented
  `huggingface.co` egress requirement
- bounded caches with copy-on-read for embedding lists
- `workspace_id` derived from the resolved workspace path, or the unused global
  deleted
- tests for each

### OUT

- the collection gate, the vector-space decision, the test harness repair
- base image or `uv` digest pinning
- vendoring tokenizer assets into the image
- any change to chunking, search profiles, or ranking

## Invariants

- Repository, CI, and image resolve the same Voyage SDK version.
- No parameter is sent to the SDK that the installed version does not accept.
- Degraded results are always distinguishable from healthy ones by the caller.
- A cached embedding cannot be mutated by a consumer.
- Point IDs remain deterministic and collision-safe.
- No live Voyage call during validation.

## Allowed Files

- `pyproject.toml`
- `uv.lock`
- `services/dope-context/src/rerank/voyage_reranker.py`
- `services/dope-context/src/utils/model_tokenizer.py`
- `services/dope-context/src/embeddings/voyage_embedder.py`
- `services/dope-context/src/embeddings/contextualized_embedder.py`
- `services/dope-context/src/mcp/server.py`
- `services/dope-context/Dockerfile`
- `services/dope-context/tests/test_voyage_modernization.py`
- `services/dope-context/tests/test_service_hardening.py`
- `docs/03-reference/systems/dope-context/deployment.md`
- `task-packets/dope-context/TP-DOPECONTEXT-SERVICE-HARDENING-0006.md`

## Required Chain

`analyze -> apilookup -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

`apilookup` is required: the reranker parameter set must be re-verified against
current vendor documentation, not against this packet.

## Plan

1. Raise `voyageai` in `pyproject.toml` to match `constraints.txt`, refresh the
   lockfile, and confirm the repo environment and image agree.
2. Drop `return_documents` and simplify `_api_rerank` so `truncation` is no
   longer collateral damage of a compatibility retry.
3. Add a degradation field to `RerankResponse` and surface it in the metadata
   `search_code` and `docs_search` already return.
4. Validate query tokens against the 8,000 limit and fail loudly.
5. Pre-warm the tokenizer once per model at construction; memoize the failure on
   the counter so a blocked Hub costs one attempt, not one per chunk. Document
   the egress requirement in the deployment doc.
6. Bound both caches and return copies of embedding lists.
7. Derive `workspace_id` from the resolved path in `_initialize_components`, or
   delete the unused global; record which and why.
8. Test each, including a test that the reranker request contains no parameter
   absent from the installed SDK signature.

## Exact Commands

```bash
git status --short --branch
python -m compileall -q services/dope-context/src
uv lock --check || uv lock
uv run --extra services python -c \
  "import voyageai, inspect; from voyageai import AsyncClient; \
print(voyageai.__version__); print(inspect.signature(AsyncClient.rerank)); \
print(inspect.signature(AsyncClient.contextualized_embed))"
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
docker build -f services/dope-context/Dockerfile -t dope-context:tp-harden-0006 .
docker run --rm --network none --entrypoint python \
  dope-context:tp-harden-0006 -c \
  "import voyageai; print(voyageai.__version__)"
git diff --stat
git diff
```

## Acceptance Criteria

- `pyproject.toml`, `uv.lock`, and the image all resolve `voyageai>=0.5.0,<0.6`.
- The rerank call passes no parameter absent from the installed signature, and
  `truncation` is preserved.
- `RerankResponse` exposes degradation, and it reaches MCP metadata.
- A query above 8,000 tokens fails loudly rather than silently falling back.
- Tokenizer load is attempted once per model, not once per unique text.
- The `huggingface.co` egress requirement is documented.
- Caches are bounded and return copies.
- `workspace_id` is root-derived, or the unused global is gone.
- Audit adversarial test A6b flips from FAIL to PASS.
- The suite gains no failure beyond the pre-existing ones.

## Proof Requirements

Return verbatim: base and final head SHA, `git diff`, the SDK version and
signatures from both the repo environment and the image, the pytest summary
before and after, the Docker build and no-network smoke output, the A6b result,
and PR metadata with checks.

## Rollback

1. Revert the packet commits.
2. The SDK bump is the only change with container impact; if the image breaks,
   revert `pyproject.toml` and `uv.lock` together and rebuild.
3. No index or collection is touched, so nothing needs restoring.

## Stop Conditions

Stop if:

- the SDK bump breaks the container build or the no-network smoke
- current vendor documentation contradicts the reranker limits stated here
- bounding the caches measurably degrades indexing throughput
- deriving `workspace_id` would change point IDs for an existing index
- embedded audit returns FAIL or NEEDS_SUPERVISOR

## Current Evidence

### OBSERVED

- Image `voyageai 0.5.0`; repo environment `0.3.7`; running container `0.4.1`.
- `rerank()` has no `return_documents` in either 0.3.7 or 0.5.0.
- `Client.tokenizer` is `Tokenizer.from_pretrained("voyageai/{model}")` and
  re-raises without memoizing, so `lru_cache` never caches the failure.
- All five tokenizer repos return HTTP 200, so the path works with egress.
- Vendor: rerank max 1,000 documents and 600K total tokens both already match
  the code; the 8,000 per-query and 32,000 pair limits do not.

### UNKNOWN

- whether raising the SDK in `pyproject.toml` perturbs other services sharing it
- practical memory ceiling appropriate for the bounded caches
