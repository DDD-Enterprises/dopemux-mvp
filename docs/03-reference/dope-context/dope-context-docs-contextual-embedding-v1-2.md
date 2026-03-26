---
id: dope_context_docs_contextual_embedding_v1
title: Dope Context Docs Contextual Embedding v1
type: reference
owner: '@hu3mann'
last_review: '2026-02-26'
next_review: '2026-05-27'
author: '@hu3mann'
date: '2026-02-26'
prelude: Contract for grouped docs contextual embedding with voyage-context-3 and deterministic retrieval provenance.
---
# Dope-Context: Docs Contextual Embedding (voyage-context-3) - v1

## Objective
Guarantee high-quality documentation retrieval by using contextualized chunk embeddings:
- Docs chunks are embedded with document-level context baked into every chunk vector.
- Implementation uses `voyage-context-3` with grouped-by-document inputs (ordered chunks per doc).

## Hard Invariants (Fail Closed)
For each document:
1. Chunk ordinals MUST be contiguous: `0..N-1`.
2. Returned embeddings MUST equal `N`.
3. Each embedding MUST map to a specific `chunk_id + ordinal`.
4. Any mismatch => that document is NOT indexed (no partial upsert).

## Required Metadata Per Chunk Vector
- workspace_id
- instance_id
- source_type = "doc"
- source_uri (file path)
- doc_id
- chunk_id
- ordinal
- content_hash
- embed_model = "voyage-context-3"
- chunker_version

## Retrieval Contract
docs_search MUST:
- embed queries in the same embedding space as docs chunks (`voyage-context-3` query mode)
- run dense retrieval + lexical retrieval
- fuse deterministically (RRF)
- optionally rerank via Voyage reranker
- return provenance: lane_used, fusion_strategy, rerank_used, embed_model_used, timings_ms

## Trinity Boundaries (Enforced)
- Search plane authority: `code_results`, `docs_results`, fusion and reranking behavior
- Memory plane authority: decision records and summaries returned via bridge integration
- `search_all` integrates decision records as read-only enrichment and never mutates decision state
- Decision enrichment defaults to Top-3 (`decision_limit=3`) and is hard-clamped to 10

## Startup Indexing Contract
- Dopemux startup commands trigger a batch bootstrap pass (`index_workspace` + `index_docs`)
- After bootstrap, ongoing updates run through autonomous async watchers
- Bootstrap is idempotent per workspace snapshot unless forced
