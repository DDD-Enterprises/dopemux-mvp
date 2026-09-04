---
id: DOPE_CONTEXT_MODERNIZATION_AUDIT_2026_07_22
title: Dope Context Modernization Audit 2026 07 22
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-22'
last_review: '2026-07-22'
next_review: '2026-10-20'
prelude: Evidence-backed audit of dope-context, upstream Claude Context divergence,
  current Voyage models, tokenization, indexing defects, and migration work.
---
# Dope-Context Modernization Audit

## Verdict

`SELECTIVE_REFRESH_REQUIRED`

A wholesale refresh from `zilliztech/claude-context` is rejected. Upstream has
become a TypeScript and Milvus-oriented indexing engine. Dope-context is a
Python, FastMCP, Qdrant retrieval service with Dopemux-specific code and docs
collections, three named code vectors, contextualized docs, autonomous
indexing, hybrid search, and MCP response controls.

Replacing the service would discard useful behavior while changing storage and
runtime architecture without evidence that the migration improves retrieval.
The correct policy is selective backporting of proven upstream patterns.

## Evidence Baseline

### OBSERVED: Dopemux

- Canonical runtime: `services/dope-context/src/mcp/server.py`
- Canonical container entrypoint: `python -m src.mcp.server`
- Base inspected: `b2ee5f11de04861c202d31241f909d83d85fbe41`
- Code and docs indexes are derived Qdrant artifacts.
- Source files remain authoritative.

### OBSERVED: upstream

- Repository inspected: `zilliztech/claude-context`
- Upstream head inspected: `6fc318b4e3ce58e2898b00a9c3538ead9e24dee5`
- Useful patterns:
  - deterministic roots built from sorted paths
  - one gitignore-aware matcher with negation support
  - explicit model capability errors
  - model and dimension registry tests

### OBSERVED: Voyage

Official Voyage material checked on 2026-07-22 establishes:

- docs default: `voyage-context-4`
- code default: `voyage-code-3`
- general family: `voyage-4-large`, `voyage-4`, `voyage-4-lite`
- rerankers: `rerank-2.5`, `rerank-2.5-lite`
- model-specific tokenization is required for accurate request accounting
- context-4 supports 256, 512, 1024, and 2048 dimensions
- pre-chunked contextual documents should normally use zero overlap
- `voyageai` 0.5.0 is the current Python SDK release

## Fixed Defects

1. **Legacy docs model**
   - Default changed from `voyage-context-3` to `voyage-context-4`.
   - Context-3 remains an explicit rollback option.

2. **Dimension-unsafe caches**
   - Cache identity now includes model, input type, dimension, dtype, and
     chunking mode.

3. **Incorrect pricing**
   - Code-3 and context-3 embedding prices were corrected.
   - Reranking is now priced by processed tokens, not request count.

4. **Incorrect token accounting**
   - Voyage request accounting now uses the model-specific Voyage tokenizer
     when available.
   - A conservative deterministic fallback is used when tokenizer assets are
     unavailable.
   - MCP response budgeting remains separate and explicitly approximate.

5. **Unsafe document replacement**
   - Existing points are no longer deleted before extraction and embedding.
   - Replacement points are inserted first, then only stale points are removed.

6. **Basename collision cleanup**
   - Cleanup now matches exact source paths or workspace-relative URIs.

7. **Random point identity**
   - Document points now use deterministic UUIDv5 identifiers.

8. **Invisible index configuration**
   - Payloads now include model, dimension, dtype, schema version, chunker
     version, and an index fingerprint.

9. **Request-limit blindness**
   - Embedding and rerank inputs are bounded by count and token ceilings.

## Recommended Tokenization and Chunking

### Code

- ~~Keep `voyage-code-3` until benchmark evidence supports a replacement.~~
  **Superseded 2026-09-04**: the evidence now exists — see "Code vector-space
  benchmark outcome". Code vectors are `voyage-code-4` on the flat endpoint.
- Split at AST and complete-symbol boundaries first.
- Use Voyage-token-aware fallback chunks.
- Benchmark a 300 to 900 token target band.
- Add overlap only to fallback text chunks, not complete symbols.

### Structured docs

- Use `voyage-context-4`.
- Preserve Markdown and section boundaries.
- Pre-chunk with zero overlap by default.
- Benchmark 400 to 800 Voyage-token chunks against server auto-chunking.

### Long or weakly structured docs

- Evaluate context-4 auto-chunking for PDFs, transcripts, and manuals.
- Persist returned chunk text, source hash, model, dimension, dtype, chunker
  version, and index fingerprint.

### MCP output

Do not reuse Voyage tokenization as a fake exact count for an unknown downstream
consumer model. Keep three distinct metrics:

- embedding request tokens
- reranker processed tokens
- approximate MCP response tokens

## Remaining High-Priority Work

1. Add a collection-level manifest and fail closed when model, dimension,
   dtype, chunker, or discovery rules conflict.
2. Reindex into versioned shadow collections instead of mixing vector schemas.
3. Port one gitignore matcher with negation support for initial indexing and
   sync.
4. Add a sorted-path root digest covering file hashes and index configuration.
5. Replace character-sized fallback chunks with Voyage-token-sized chunks.
6. Add deleted-file reconciliation and bounded streaming upserts.

The former item 3 — "Benchmark the current mixed code-vector strategy against
all-code-3 vectors" — is **CLOSED**; see "Code vector-space benchmark outcome"
below.

## Code vector-space benchmark outcome (2026-09-04)

Run under `TP-DOPECONTEXT-VECTOR-SPACE-0004`. Whole-repo corpus: 2,754 files,
~38K chunks, 41 queries, `top_k=20`. Full write-up and raw JSON in
`claudedocs/dope-context-eval-results-2026-09-03.md`.

| Profile | Model / endpoint | R@5 | R@20 | MRR | NDCG@10 | Cost |
|---|---|---|---|---|---|---|
| **B** | `voyage-code-4` flat, both sides | 0.951 | **1.000** | **0.855** | **0.890** | $1.181 |
| Bh | B + scope header | 0.951 | 1.000 | 0.729 | 0.788 | $1.327 |
| A | `voyage-context-4` contextualized | 0.780 | 0.951 | 0.677 | 0.714 | $1.126 |
| CTRL | deliberate index/query mismatch | 0.000 | 0.000 | 0.000 | 0.000 | $0.0002 |

The question the residual item posed is answered, though not as it was framed:
the contest was never "mixed vs all-code-3" but "contextualized vs flat", and
the flat profile won every metric while costing less than the header variant.
CTRL collapsing to exactly 0.000 confirms the metrics discriminate rather than
always passing. `voyage-code-3` was not benchmarked at all — it was superseded
by `voyage-code-4`, which is both newer and cheaper ($0.12/M vs $0.18/M).

Implemented as D1: all three code vectors (`content_vec`, `title_vec`,
`breadcrumb_vec`) now resolve to `voyage-code-4` on the flat `embeddings`
endpoint, so index and query share one space by construction. Docs collections
remain contextualized on `voyage-context-4`.

Two vendor behaviours measured during this work, both load-bearing:

* The flat endpoint **silently truncates** at ~32K tokens per input rather than
  rejecting — a 320,000-token input returned success and billed 31,993. An
  oversized chunk is therefore half-embedded with no error. Upstream chunk-size
  enforcement cannot be delegated to the API.
* `voyage-code-4`'s per-request token ceiling is **not documented**: it is
  absent from the vendor's 1M/320K/120K grouping sentence entirely. The
  registry carries 320,000, inferred from the rate-limit tables plus a measured
  ≥300,000 floor. If batch sizing ever fails, drop it to 120,000 first.

Superseded by this outcome: the "keep `voyage-code-3` until benchmark evidence
supports a replacement" recommendation above, and the ACCEPTED entry "use
context-4 for docs and code-3 for code". The REJECTED entry "unbenchmarked
code-model switching" stands — this switch was benchmarked.

## Migration Gate

1. Create versioned shadow collections.
2. Write a collection manifest.
3. Reindex without mutating the active collection.
4. Measure Recall@K, MRR or NDCG@10, determinism, latency, tokens, and cost.
5. Dual-read during a bounded trial.
6. Cut over only when acceptance thresholds pass.
7. Preserve the rollback pointer.
8. Delete the old collection only through an approved cleanup packet.

## Decisions

### ACCEPTED

- Preserve Python, FastMCP, and Qdrant.
- Selectively backport upstream deterministic-indexing patterns.
- Use context-4 for docs and code-3 for code. **Amended 2026-09-04**: code
  moved to `voyage-code-4` (flat endpoint) on benchmark evidence; docs remain
  on context-4.
- Use model-specific tokenization for Voyage limits and cost.
- Make index compatibility explicit and versioned.

### REJECTED

- Wholesale upstream replacement
- Qdrant-to-Milvus migration for cosmetic parity
- unbenchmarked code-model switching
- mixed model or dimension vectors in one collection
- treating character counts or tiktoken counts as exact Voyage usage
