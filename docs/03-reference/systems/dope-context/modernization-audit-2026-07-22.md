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

- Keep `voyage-code-3` until benchmark evidence supports a replacement.
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
3. Benchmark the current mixed code-vector strategy against all-code-3 vectors.
4. Port one gitignore matcher with negation support for initial indexing and
   sync.
5. Add a sorted-path root digest covering file hashes and index configuration.
6. Replace character-sized fallback chunks with Voyage-token-sized chunks.
7. Add deleted-file reconciliation and bounded streaming upserts.

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
- Use context-4 for docs and code-3 for code.
- Use model-specific tokenization for Voyage limits and cost.
- Make index compatibility explicit and versioned.

### REJECTED

- Wholesale upstream replacement
- Qdrant-to-Milvus migration for cosmetic parity
- unbenchmarked code-model switching
- mixed model or dimension vectors in one collection
- treating character counts or tiktoken counts as exact Voyage usage
