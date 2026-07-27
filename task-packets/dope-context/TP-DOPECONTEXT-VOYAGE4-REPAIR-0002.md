---
id: TP-DOPECONTEXT-VOYAGE4-REPAIR-0002
title: Tp Dopecontext Voyage4 Repair 0002
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Repair packet closing the blocking vector-compatibility, collection-gate,
  and rollback defects found by the post-merge audit of PR #1112.
---
# Task Packet: TP-DOPECONTEXT-VOYAGE4-REPAIR-0002

## Objective

Make dope-context retrieval provably single-space and make existing Qdrant
collections fail closed on incompatible configuration, closing the three
blocking findings from the post-merge audit of PR #1112 without changing the
Python, FastMCP, and Qdrant architecture.

## Status

`IMPLEMENTATION_CANDIDATE`

Depends on `TP-DOPECONTEXT-VOYAGE4-0001` (merged as PR #1112, commit
`4b42268775d1f94e26500c758128da3e11b151d5`).

## Risk

`HIGH`

Touches collection creation semantics and the model selection that determines
vector space identity. A wrong change here silently degrades every search
result while all process checks stay green.

## Audit Provenance

Findings referenced below are from `TP-DOPECONTEXT-VOYAGE4-POSTMERGE-OPUS-AUDIT-001`
(verdict `FAIL`, disposition `REPAIR_REQUIRED`, 17 findings, 3 blocking).

Two audit observations set the urgency and the safety margin:

- The merged code is **not deployed**. The running `mcp-dope-context` container
  was built 2026-06-20 and created 2026-07-01, both predating the 2026-07-23
  merge; it has no `model_registry` module. Deployment, not re-indexing, is the
  gating event.
- The target Qdrant holds **zero collections**
  (`curl -s http://localhost:6333/collections` -> `{"result":{"collections":[]}}`).
  There is no existing index to migrate or contaminate, so this repair can land
  before first deploy with no migration step.

## Scope

### IN

- code content vector: make index model and query model identical (F-001, interim)
- collection-level compatibility manifest, written and validated fail-closed (F-002)
- symmetric contextualized model resolution for index and query paths (F-003)
- `token_count_exact` honesty in the single-text embed path (F-004)
- stale reconciliation by `file_path` and `doc_id`, not only `source_path`/`source_uri` (F-004)
- one payload scan per index run instead of one per document (F-007)
- model, dimension, dtype, and fingerprint provenance on code payloads (F-009)
- `voyageai>=0.5.0,<0.6` in `pyproject.toml` so repo, CI, and image agree (F-010)
- drop the undocumented `return_documents` rerank parameter (F-010)
- surface reranker degradation instead of silently returning input order (F-011)
- memoize tokenizer-load failure so a blocked Hub is not retried per chunk (F-006)
- `voyage-3-lite` request ceiling corrected to 120,000 (F-013)
- explicit reranker per-query token limit (F-014)
- whole-item MCP budgeting that can never return zero results (F-017)
- tests locking each of the above

### OUT

- choosing the permanent F-001 direction (benchmark-gated, see Stop Conditions)
- any live Voyage embedding or rerank request
- creating, migrating, mutating, or deleting any Qdrant collection
- repairing the nine pre-existing `FunctionTool` test failures (F-008)
- bounding or copy-on-read for the embedding caches (F-012)
- `workspace_id` derivation cleanup (F-015)
- AST-first chunking, gitignore negation matcher, canonical index root,
  deleted-file reconciliation
- proof tooling, schema, scope manifest, or pre-commit filters
- replacing Qdrant with Milvus or importing upstream Claude Context
- base image or `uv` digest pinning

## Invariants

- Source code and documents remain authoritative; Qdrant remains derived.
- For every named vector, the index model, endpoint, dimension, and dtype equal
  the query model, endpoint, dimension, and dtype.
- No insert proceeds into a collection whose manifest disagrees with the active
  configuration.
- Rollback is one documented variable that moves index and query together.
- Failure always preserves the last good index; replacements are upserted before
  stale points are deleted.
- No estimated token count is ever reported as exact.
- MCP truncation always returns at least one result when input is non-empty.
- Voyage request accounting and MCP response budgeting stay separate.
- No secret or API key enters source, tests, logs, or proof.

## Allowed Files

- `services/dope-context/src/embeddings/model_registry.py`
- `services/dope-context/src/embeddings/voyage_embedder.py`
- `services/dope-context/src/utils/model_tokenizer.py`
- `services/dope-context/src/utils/token_budget.py`
- `services/dope-context/src/rerank/voyage_reranker.py`
- `services/dope-context/src/search/dense_search.py`
- `services/dope-context/src/pipeline/docs_pipeline.py`
- `services/dope-context/src/pipeline/indexing_pipeline.py`
- `services/dope-context/src/mcp/server.py`
- `services/dope-context/tests/test_voyage_modernization.py`
- `services/dope-context/tests/test_docs_pipeline_invariants.py`
- `services/dope-context/tests/test_vector_space_invariants.py`
- `pyproject.toml`
- `docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md`
- `task-packets/dope-context/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002.md`

## Required Chain

`analyze -> apilookup -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

## Plan

1. **Close the code vector split (F-001, interim).** In
   `indexing_pipeline._process_file`, embed `content_vec` with the same
   `voyage-code-3` document call already used for title and breadcrumb, so index
   and query occupy one space. Put the contextualized code-content path behind an
   explicit opt-in flag, default off, and record in the audit doc that enabling it
   also requires switching the `search_code` content query to the contextualized
   model. Do not delete the contextualized path.
2. **Add the collection manifest (F-002).** Write model, endpoint, dimension,
   dtype, `chunker_version`, and `index_schema_version` at collection creation.
   On an existing collection, read the manifest and refuse to insert when it
   disagrees with the active configuration, naming the conflicting field. Add an
   explicit opt-in recreate path; never rewrite a collection in place.
3. **Make rollback symmetric (F-003).** Remove the hard-coded
   `embed_model = "voyage-context-3"` literal in `_docs_search_impl` and resolve
   the query model from the same configured source the index path uses. Document
   `DOPE_CONTEXT_DOC_EMBED_MODEL` as the single rollback variable.
4. **Stop over-claiming exactness (F-004).** Propagate `token_counts[0].exact`
   into `embed()`'s response, or set the flag true only when the API actually
   returned `total_tokens`. Align `embed_batch()` to the same rule.
5. **Reconcile legacy payloads and hoist the scan (F-004, F-007).** Match stale
   points on `source_path`, `source_uri`, `file_path`, and `doc_id`. Fetch
   payloads once per `index_workspace` run and index them in memory, or replace
   the scroll with a filter on the indexed `source_path` keyword field.
6. **Give code payloads provenance (F-009).** Write `embed_model`,
   `embed_dimension`, `embed_dtype`, `index_schema_version`, and
   `index_fingerprint` from `indexing_pipeline`, attributing per vector.
7. **Reconcile the SDK (F-010).** Raise `voyageai` to `>=0.5.0,<0.6` in
   `pyproject.toml`, refresh the lockfile, and drop `return_documents` from the
   rerank call rather than relying on a `TypeError` retry that also discards
   `truncation`.
8. **Make degradation visible (F-011, F-014).** Add a failure indicator to
   `RerankResponse`, surface it in the MCP metadata already returned by
   `search_code` and `docs_search`, and reject queries above the documented
   8,000-token reranker limit instead of falling back silently.
9. **Stop the retry storm (F-006).** Load the tokenizer once per model at
   construction and memoize the failure, so a blocked Hugging Face Hub costs one
   attempt per model rather than one per unique chunk. Document the
   `huggingface.co` egress requirement.
10. **Fix registry and budgeting edges (F-013, F-017).** Set `voyage-3-lite`
    `max_request_tokens` to 120,000. Budget over the whole serialized item so an
    untrimmed sibling such as `context` cannot starve the response, and guarantee
    at least one result is emitted, degrading the first item instead of returning
    an empty list.
11. **Lock it with tests.** Add `test_vector_space_invariants.py` asserting index
    and query agreement for all six named vectors, fail-closed insert on manifest
    conflict, and that the legacy flag cannot split index from query. Extend the
    two existing suites for exactness propagation, legacy reconciliation, single
    scan, and non-empty truncation.
12. Run the full validation set, embedded audit, and PR Steward against the final
    head.

## Exact Commands

```bash
git status --short --branch
git diff --stat
git diff --check
python -m compileall -q services/dope-context/src
PYTHONPATH=services/dope-context python -m pytest -q \
  services/dope-context/tests/test_vector_space_invariants.py \
  services/dope-context/tests/test_voyage_modernization.py \
  services/dope-context/tests/test_docs_pipeline_invariants.py
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
uv lock --check || uv lock
docker build -f services/dope-context/Dockerfile -t dope-context:tp-repair-0002 .
docker run --rm --network none -e VOYAGE_API_KEY=test-not-a-secret \
  --entrypoint python dope-context:tp-repair-0002 \
  -c "import voyageai; from src.embeddings.model_registry import MODEL_SPECS; \
print(voyageai.__version__); print(sorted(MODEL_SPECS))"
rg -n "voyage-context|voyage-code|content_vec|input_type|index_fingerprint|resolve_context_model" \
  services/dope-context/src
git diff --stat
git diff
git status --short --branch
```

## Acceptance Criteria

- Code `content_vec` index model, endpoint, dimension, and dtype equal the
  `search_code` content query model, endpoint, dimension, and dtype.
- Docs index and query resolve the contextualized model from the same source.
- `DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3=1` alone cannot split index from query.
- Collection creation writes a manifest; insertion into a conflicting collection
  fails closed and names the conflicting field.
- Code payloads carry model, dimension, dtype, schema version, and fingerprint.
- `embed()` never reports an estimated token count as exact.
- Stale reconciliation finds payloads carrying only `file_path` or only `doc_id`.
- `index_workspace` performs one full payload scan, not one per document.
- Reranking omits `return_documents`, enforces the 8,000-token query limit, and
  reports degradation in MCP metadata.
- Tokenizer load failure is attempted once per model, not once per unique text.
- `voyage-3-lite` `max_request_tokens` is 120,000.
- Non-empty input to `truncate_code_results` and `truncate_docs_results` always
  returns at least one result.
- `pyproject.toml`, `uv.lock`, and the image all resolve `voyageai>=0.5.0,<0.6`.
- Focused and service suites pass, with no new failures relative to the nine
  pre-existing `FunctionTool` failures.
- Docker build and no-network smoke pass.
- Embedded audit is PASS or non-blocking PASS_WITH_RISKS.
- PR Steward emits READY before merge.

## Proof Requirements

Return verbatim:

- base and final head SHA
- `git status` before and after
- `git diff --stat` and `git diff`
- every validation command and exit code
- test, Docker, and no-network smoke output
- before/after counts for the pre-existing `FunctionTool` failures, proving none
  were added
- embedded audit identity, invocation, verdict, and findings
- PR metadata, reviews, threads, checks, and merge readiness

## Rollback

1. Revert the packet commits.
2. Use `DOPE_CONTEXT_DOC_EMBED_MODEL=voyage-context-3` as the single documented
   rollback variable. Never use `DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3=1` alone.
3. Do not deploy the reverted image against a populated Qdrant without first
   probing `/collections` for existing model generations.
4. Never mix model generations in one collection; recreate instead.

## Stop Conditions

Stop if:

- the base moves with overlapping dope-context changes
- a required file falls outside the allowlist
- a benchmark is proposed that would require live billable Voyage calls without
  separate approval
- any operation would create, migrate, mutate, or delete a Qdrant collection
- a live validation would expose an API key
- the manifest gate would reject a collection an operator expects to work, and
  the resolution is unclear
- the full suite gains any failure beyond the nine pre-existing ones
- embedded audit returns FAIL or NEEDS_SUPERVISOR
- proof or checks are stale relative to the PR head

## Open Decision

The permanent fix for F-001 is **not** decided by this packet. Two directions are
valid:

- **A.** Embed the code content query with the contextualized model, keeping
  contextualized document vectors.
- **B.** Index `content_vec` with `voyage-code-3`, matching upstream.

This packet implements **B as the interim**, because it is provably consistent,
matches upstream `zilliztech/claude-context`, and requires no live calls. Choosing
between A and B requires the retrieval benchmark the merged audit document already
lists as residual work item 3. That benchmark needs billable Voyage calls and
separate approval.

Relevant evidence for whoever runs it: `voyage-code-3` and `voyage-context-4` ship
an **identical tokenizer and vocabulary** (both 151,665 entries; a mixed code and
CJK probe encodes to byte-identical ids). That indicates common lineage and
constrains the input side only. It does not establish a shared output space, but it
means direction A may cost less than the worst case, so the benchmark is worth
running rather than assumed.

## Current Evidence

### OBSERVED

- Merged implementation audited at `4b42268775d1f94e26500c758128da3e11b151d5`;
  zero post-merge drift on every dope-context surface.
- Adversarial batteries: A14, A15, A16, A13, A4, A6b, B4, B6, C1 all FAIL against
  merged main; B1, B2, B3, B5 PASS (idempotence and failure preservation hold).
- Full service suite at merged main: `9 failed, 34 passed, 1 skipped`; identical
  nine failures at pre-merge base `603871f96a`, so pre-existing.
- Image builds; no-network import smoke passes with `voyageai 0.5.0`.
- Repo environment resolves `voyageai 0.3.7`; running container has `0.4.1`.
- Target Qdrant holds zero collections; running container predates the merge.

### UNKNOWN

- empirical retrieval cost of the F-001 mismatch
- whether any other host runs dope-context against a populated Qdrant
- embedded auditor verdict for this packet
- final GitHub CI state
- PR Steward merge readiness
