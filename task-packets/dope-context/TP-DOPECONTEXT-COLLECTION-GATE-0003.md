---
id: TP-DOPECONTEXT-COLLECTION-GATE-0003
title: Tp Dopecontext Collection Gate 0003
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Collection-level compatibility manifest that fails closed before any
  insert, closing the F-002 blocker from the PR 1112 post-merge audit.
---
# Task Packet: TP-DOPECONTEXT-COLLECTION-GATE-0003

## Objective

Make an incompatible Qdrant collection impossible to write into. Persist a
compatibility manifest when a collection is created and validate it fail-closed
before any point is inserted, so a model, dimension, dtype, or chunker change
can never silently mix vector generations.

## Status

`IMPLEMENTATION_CANDIDATE`

Closes **F-002**, the remaining blocker that `TP-DOPECONTEXT-VOYAGE4-REPAIR-0002`
deliberately deferred. Depends on nothing; may land before or after
`TP-DOPECONTEXT-VECTOR-SPACE-0004`.

## Risk

`HIGH`

Changes collection creation and insertion semantics. A gate that is too strict
bricks indexing for every workspace; a gate that is too loose does nothing.

## Design Inputs

A read-only inventory of every Qdrant caller established the following. These
are `OBSERVED` and materially narrow the design.

- **The chokepoint is clean.** Exactly three production insert sites exist:
  `indexing_pipeline.py:446`, `indexing_pipeline.py:503`, and
  `docs_pipeline.py:277`. All route through
  `MultiVectorSearch.insert_points_batch`.
- **Nothing bypasses it.** No code constructs a Qdrant client directly to write
  code or docs collections. The only direct `QdrantClient` in the repository is
  `scripts/deploy/migration/backfill_embeddings_simple.py`, which writes the
  unrelated `ddg_global_decisions` collection.
- **`create_collection()` is called twice per index run** —
  `server.py:924` and then again at `indexing_pipeline.py:383` on the same
  instance. The gate MUST be idempotent or it will fail against its own first
  call. This is the single most important constraint in this packet.
- **Collections are per workspace**: `code_{hash}` / `docs_{hash}` where `hash`
  is `md5(resolved_path)[:8]`, overridable by `WORKSPACE_HASH_OVERRIDE`.
- **Tests never build real collections**; they stub `create_collection` to
  return `None`, so stubs will need the manifest surface added.
- **Target Qdrant currently holds zero collections**, so this can land with no
  migration path at all.

## Scope

### IN

- a manifest written at collection creation recording model, endpoint,
  dimension, dtype, `chunker_version`, and `index_schema_version`
- fail-closed validation before insert, naming the conflicting field
- idempotent behaviour when `create_collection` is called on a collection this
  process just created
- an explicit opt-in recreate path for a deliberate migration
- code payload provenance (F-009) so existing code points become classifiable
- tests covering conflict rejection, idempotence, and the recreate path

### OUT

- migrating, rewriting, or deleting any existing collection
- the F-001 vector-space decision (see `TP-DOPECONTEXT-VECTOR-SPACE-0004`)
- shadow or versioned collections
- changing collection naming or the workspace hash
- the six findings already closed by `TP-DOPECONTEXT-VOYAGE4-REPAIR-0002`

## Invariants

- Source code and documents remain authoritative; Qdrant remains derived.
- `create_collection()` is idempotent and safe to call repeatedly.
- No insert proceeds into a collection whose manifest disagrees with the active
  configuration.
- A conflict names the specific field that disagrees, with both values.
- The gate never deletes or rewrites data; it refuses.
- An operator can always recreate deliberately, never accidentally.
- Failure preserves the last good index.

## Design Decision — manifest storage (resolved 2026-07-26)

Plan step 1 is **closed**. All three candidates were tested empirically against
a throwaway collection on the local Qdrant, which was empty before and after.

**Qdrant has no collection-level metadata API.** `AsyncQdrantClient` exposes no
`config`-writing surface; the only collection-scoped stores are aliases and the
points themselves.

| Option | Result |
|---|---|
| **Sidecar file** | **REJECTED.** The existing chunk-snapshot sidecar lives at `~/.dope-context/snapshots/{workspace_hash}/` — host home. Qdrant data lives in the Docker volume `dope-decision-graph-qdrant-data`. **The two have independent lifecycles.** Wipe the volume and the sidecar still asserts compatibility for a collection that no longer exists; wipe home (new machine, fresh container) and every surviving collection reads as unmanifested. A manifest must share the lifecycle of what it describes. |
| **Collection alias** | Works — `update_collection_aliases` / `get_collection_aliases` round-trips, shares the collection lifecycle, and never appears in search results. But an alias is only a *name*: it can carry a fingerprint hash and nothing else, which cannot satisfy the invariant "a conflict names the specific field that disagrees, with both values." |
| **Sentinel point** | **CHOSEN**, with a caveat proven rather than assumed. |

**The sentinel hazard is real, not hypothetical.** A zero-vector manifest point
*does* come back from a query — measured:

```
SEARCH returns:      [('0001', 1.0, 'data'), ('00ff', 0.0, True)]   <- manifest leaked
SEARCH w/ must_not:  [('0001', 1.0)]                                <- excluded cleanly
```

DOT distance scores it 0.0 so it ranks last, but it is still returned and would
be counted against `top_k`.

**Decision: sentinel point carrying the full structured manifest**, because it
is the only option that both shares the collection's lifecycle and can carry
field-level detail. Requirements that follow:

1. Reserved deterministic ID, e.g. `uuid5(NAMESPACE_URL, f"dope-context:manifest:{collection}")`.
2. Payload flag `__manifest__: true`; zero vectors for every named vector.
3. **Exclude at both reader chokepoints, which are the only two that exist:**
   - `MultiVectorSearch.search()` (`dense_search.py:277`) — merge a
     `must_not __manifest__` condition into the caller's filter.
   - `MultiVectorSearch.get_all_payloads()` (`dense_search.py:442`) — skip it.
     This one matters more than it looks: `get_all_payloads` feeds the **BM25
     index** (`server.py:970`), the **docs stale reconciliation**
     (`docs_pipeline.py:208`) and **sync** (`server.py:2381, 2412`). An
     unfiltered manifest point would pollute BM25 and could be deleted as a
     stale doc chunk.
4. Optionally also write the fingerprint as an alias: a cheap
   existence/compatibility pre-check that needs no point read. Nice to have,
   not required.

Add a test asserting the manifest point is absent from both `search()` and
`get_all_payloads()` results — that is the regression that would otherwise leak
silently.

## Allowed Files

- `services/dope-context/src/search/dense_search.py`
- `services/dope-context/src/search/docs_search.py`
- `services/dope-context/src/pipeline/indexing_pipeline.py`
- `services/dope-context/src/pipeline/docs_pipeline.py`
- `services/dope-context/src/embeddings/model_registry.py`
- `services/dope-context/tests/test_collection_gate.py`
- `services/dope-context/tests/test_docs_pipeline_invariants.py`
- `task-packets/dope-context/TP-DOPECONTEXT-COLLECTION-GATE-0003.md`

## Required Chain

`analyze -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

## Plan

1. **DONE** — manifest storage is decided; see "Design Decision" above. Implement
   the sentinel point with exclusion at both reader chokepoints.
2. Write the manifest in `create_collection` on the creation path only.
3. On the existing-collection path, read the manifest and compare against the
   active configuration. Matching manifest returns quietly, which preserves the
   double-call idempotence at `server.py:924` and `indexing_pipeline.py:383`.
   Missing manifest on a populated collection is a conflict; missing manifest on
   an empty collection may be adopted.
4. Enforce at insert, not only at create: validate once per
   `MultiVectorSearch` instance and refuse `insert_points_batch` on conflict.
5. Add the opt-in recreate path, gated on an explicit argument or environment
   flag, never on a default.
6. Add code payload provenance (F-009), attributing per vector because
   `content_vec` and `title_vec`/`breadcrumb_vec` may use different models.
7. Update the test stubs to carry the manifest surface.
8. Test: conflicting model rejected; conflicting dimension rejected; conflicting
   dtype rejected; conflicting chunker rejected; matching manifest passes twice
   in a row; empty collection adopts; recreate path works only when opted in.

## Exact Commands

```bash
git status --short --branch
git diff --check
python -m compileall -q services/dope-context/src
PYTHONPATH=services/dope-context python -m pytest -q \
  services/dope-context/tests/test_collection_gate.py \
  services/dope-context/tests/test_docs_pipeline_invariants.py
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
docker build -f services/dope-context/Dockerfile -t dope-context:tp-gate-0003 .
git diff --stat
git diff
```

## Acceptance Criteria

- A collection created by this code carries a manifest.
- `create_collection` called twice in one run succeeds both times.
- Insert into a collection whose manifest disagrees fails closed, naming the
  field and both values.
- An empty collection with no manifest is adopted rather than rejected.
- A populated collection with no manifest is rejected.
- Recreate happens only under an explicit opt-in.
- Code payloads carry model, dimension, dtype, schema version, and fingerprint.
- The suite gains no failure beyond the nine pre-existing `FunctionTool` ones.
- Audit adversarial test A15 flips from FAIL to PASS.
- Audit adversarial test A16 flips from FAIL to PASS.

## Proof Requirements

Return verbatim: base and final head SHA, `git status` before and after,
`git diff --stat` and `git diff`, every validation command with exit code, the
pytest summary before and after with the pre-existing failure count unchanged,
the A15 and A16 adversarial results, and PR metadata with checks.

## Rollback

1. Revert the packet commits; the manifest is additive and unread by old code.
2. No collection is mutated by this packet, so there is nothing to restore.
3. If the gate proves too strict in practice, disable enforcement via the opt-in
   flag rather than deleting the manifest.

## Stop Conditions

Stop if:

- the sentinel manifest leaks into `search()` or `get_all_payloads()` results
- the gate would reject a collection an operator reasonably expects to work and
  the resolution is unclear
- idempotence cannot be preserved across the double `create_collection` call
- any design requires mutating or deleting an existing collection
- the suite gains a failure beyond the nine pre-existing ones
- embedded audit returns FAIL or NEEDS_SUPERVISOR

## Current Evidence

### OBSERVED

- `dense_search.py:129-137` returns early on an existing collection, validating
  nothing.
- Docs payloads carry `index_fingerprint`; nothing ever reads it.
- Code payloads carry no provenance at all.
- Three production insert sites, no bypassing writers.
- `create_collection` is invoked twice per index run.
- Target Qdrant holds zero collections.

### UNKNOWN

- whether any other host runs dope-context against a populated Qdrant
- which manifest storage option survives operational reality best
