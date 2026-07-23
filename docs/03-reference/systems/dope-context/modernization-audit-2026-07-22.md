# Dope-Context Modernization Audit — 2026-07-22

## Verdict

**SELECTIVE_REFRESH_REQUIRED**

A wholesale refresh from `zilliztech/claude-context` is **rejected**.

The upstream project has evolved into a TypeScript indexing engine centered on
Milvus/Zilliz, while dope-context is a Python/FastMCP/Qdrant retrieval service
with Dopemux-specific code/docs separation, three named vectors, contextualized
document embeddings, autonomous indexing, token-budgeted MCP output, and
workspace-scoped collections.

Replacing dope-context with upstream would discard working Dopemux-specific
capabilities. The correct strategy is to selectively adopt upstream patterns
that improve deterministic discovery and incremental indexing while preserving
dope-context's authority boundary and runtime architecture.

## Evidence Baseline

### OBSERVED — Dopemux runtime

- Canonical runtime: `services/dope-context/src/mcp/server.py`
- Canonical container entrypoint: `python -m src.mcp.server`
- Code/docs store: Qdrant workspace-scoped collections
- Code retrieval: three named vectors plus BM25 hybrid fusion and optional
  Voyage reranking
- Docs retrieval: contextualized embeddings in docs collections
- Main repository base inspected:
  `b2ee5f11de04861c202d31241f909d83d85fbe41`

### OBSERVED — upstream

- Repository: `zilliztech/claude-context` (published package name has shifted
  toward `code-context`)
- Upstream head inspected:
  `6fc318b4e3ce58e2898b00a9c3538ead9e24dee5`
- Current upstream patterns worth adopting:
  - deterministic Merkle root construction from sorted paths
  - shared gitignore-aware matcher with negation support
  - explicit model availability errors
  - broader embedding-model registry and dimension tests

### OBSERVED — current Voyage surface

Official Voyage sources checked on 2026-07-22 establish:

- `voyage-context-4` is the current contextualized document model.
- `voyage-code-3` remains the current code-specialized embedding model.
- `voyage-4-large`, `voyage-4`, and `voyage-4-lite` are the current general
  embedding family.
- `rerank-2.5` and `rerank-2.5-lite` are the current rerankers.
- Modern Voyage models use model-specific tokenizers. Token counting must pass
  the model name to `Client.tokenize()` / `Client.count_tokens()`.
- `voyage-context-4` supports 256, 512, 1024, and 2048 dimensions, grouped
  pre-chunked inputs, client chunking, and server auto-chunking.
- Supplied contextualized chunks should normally have no overlap.
- `voyageai` 0.5.0 is the current Python package release.
- Current token pricing:
  - `voyage-context-4`: $0.12 / 1M tokens
  - `voyage-context-3`: $0.18 / 1M tokens
  - `voyage-code-3`: $0.18 / 1M tokens
  - `rerank-2.5`: $0.05 / 1M processed tokens

## Confirmed Defects

### FIXED in this slice

1. **Legacy docs model**
   - Runtime code and payloads were pinned to `voyage-context-3`.
   - Default is now `voyage-context-4`, with an explicit rollback switch.

2. **Dimension-unsafe caches**
   - Contextualized cache keys omitted output dimension.
   - A cached 1024-dimensional result could satisfy a later 256-dimensional
     request.
   - Cache identity now includes model, input type, dimension, dtype, and
     chunking mode.

3. **Incorrect embedding pricing**
   - `voyage-code-3` was accounted at $0.12 / 1M instead of $0.18 / 1M.
   - `voyage-context-3` was accounted at $0.12 / 1M instead of $0.18 / 1M.

4. **Incorrect reranker pricing**
   - Reranking was charged internally as $0.05 per 1,000 requests.
   - Voyage prices reranking by processed tokens.
   - Accounting now uses model-specific token totals.

5. **Foreign tokenizers used as authoritative**
   - Docs used `cl100k_base`; MCP output used `len(text) // 4`.
   - Neither is an exact Voyage count.
   - Embedding/rerank request accounting now uses Voyage's model-specific
     tokenizer with a conservative no-network fallback.
   - MCP response budgeting remains separate and explicitly approximate.

6. **Pre-delete data-loss window**
   - Docs indexing deleted existing vectors before extraction/embedding.
   - A processing or API failure could erase the last good index.
   - The pipeline now upserts deterministic replacements first and deletes
     only stale leftovers after successful insertion.

7. **Basename collision deletion**
   - Reindex cleanup matched document basenames.
   - `docs/a/guide.md` could delete chunks for `docs/b/guide.md`.
   - Cleanup now matches exact absolute source path or workspace-relative URI.

8. **Random document point IDs**
   - Payload chunk IDs were deterministic but Qdrant point IDs were random.
   - Retries could create duplicate points.
   - Qdrant point IDs are now deterministic UUIDv5 values.

9. **Invisible index incompatibility**
   - Payloads did not identify vector dimension, dtype, schema version, or a
     model/chunker fingerprint.
   - These fields are now persisted for compatibility checks and migration.

10. **Request-limit blindness**
    - Embedding/rerank batches did not enforce Voyage input/token ceilings.
    - Inputs are now partitioned by both count and model token limits.

## Unfixed Findings / Next Packets

### HIGH

1. **Collection-level migration gate**
   - Payload fingerprints are necessary but insufficient.
   - Collection metadata must store one canonical index manifest.
   - Startup and indexing must fail closed if collection vector size/model/
     chunker differ from the requested configuration.

2. **Code content vector strategy**
   - Code title/breadcrumb vectors use `voyage-code-3`.
   - Code content currently routes through the contextualized document
     embedder after LLM-generated context augmentation.
   - This should be benchmarked against a simpler all-`voyage-code-3`
     three-vector design. Do not switch by taste.

3. **Code discovery semantics**
   - Code discovery uses simplistic glob/sub-string exclusion.
   - It does not correctly implement `.gitignore` negation or shared discovery
     semantics between initial indexing and sync.
   - Selectively port upstream's single ignore matcher pattern using Python
     `pathspec`, and keep paths sorted before hashing/indexing.

4. **Incremental root fingerprint**
   - Snapshot serialization is deterministic enough for many cases, but there
     is no explicit sorted-path root digest covering file hashes plus index
     configuration.
   - Add a Merkle-style or canonical-manifest root.

### MEDIUM

5. **Character-sized chunks**
   - Document chunk size is still character-based.
   - Payload token counts are now corrected, but chunk boundaries are not yet
     model-token-based.

6. **Whole-workspace sequential indexing**
   - Code indexing is mostly sequential and materializes large batches in
     memory.
   - Introduce bounded producer/consumer concurrency and streaming Qdrant
     upserts after model/token migration is stable.

7. **Deletion reconciliation**
   - Docs sync needs an explicit pass for files deleted from disk, with proof
     that stale-vector cleanup is scoped to the workspace collection.

8. **Route/documentation contradiction**
   - Some custom route decorators in `mcp/server.py` are commented while
     reference docs claim the routes are active.
   - Resolve through runtime tests, not documentation edits alone.

## Recommended Tokenization and Chunking Architecture

### Code

- Model: `voyage-code-3`
- Splitter: AST/symbol boundaries first; token-aware fallback second.
- Target chunk band: benchmark 300–900 Voyage tokens.
- Overlap: only across fallback text chunks, not complete AST symbols.
- Preserve:
  - symbol name
  - qualified name
  - file path
  - language
  - start/end lines
  - content hash
- Embed content, title, and breadcrumb with one compatible model/dimension
  unless retrieval benchmarks prove mixed models improve quality.

### Structured documentation

- Model: `voyage-context-4`
- Keep semantic Markdown/header boundaries.
- Pre-chunk with **zero overlap** by default.
- Count with the `voyage-context-4` tokenizer.
- Benchmark 400–800 token chunks versus Voyage auto-chunking.
- Store returned chunk text whenever auto/client chunking is used.

### Flat and long documents

- Prefer `voyage-context-4` auto-chunking for PDFs, transcripts, and manuals
  where local structure extraction is weak.
- Persist:
  - returned `chunk_texts`
  - chunker version
  - model
  - dimension/dtype
  - source hash
  - index fingerprint

### MCP output

- Do not use Voyage tokenization to pretend the eventual consumer model is
  known.
- Continue with a conservative generic estimator, but separate:
  - embedding request tokens
  - reranker processed tokens
  - MCP response budget estimate
- Report the estimator as approximate.

## Index Migration Plan

1. Create versioned shadow collections, for example:
   - `code_<workspace>_v2`
   - `docs_<workspace>_v2`
2. Write a collection manifest:
   - source root
   - model(s)
   - dimension/dtype
   - chunker version
   - discovery rules hash
   - canonical file-root hash
3. Reindex without mutating v1.
4. Run a fixed retrieval benchmark:
   - Recall@K
   - MRR / NDCG@10
   - deterministic ordering
   - latency
   - tokens and cost
5. Dual-read v1/v2 for a bounded trial.
6. Cut over only if acceptance thresholds pass.
7. Retain rollback pointer until v2 proves stable.
8. Delete v1 only through an explicit operator-approved cleanup packet.

## Architecture Decision

### REJECTED

- Replacing dope-context wholesale with upstream Claude Context.
- Changing Qdrant to Milvus merely to resemble upstream.
- Switching code embeddings to a general model without benchmark evidence.
- Mixing dimensions/models in an existing collection.
- Treating character counts or tiktoken counts as exact Voyage usage.

### ACCEPTED

- Preserve Python/FastMCP/Qdrant architecture.
- Selectively backport deterministic discovery and incremental-index patterns.
- Move docs to `voyage-context-4`.
- Keep `voyage-code-3` for code until benchmark evidence supports another
  design.
- Use model-specific tokenization for API limits/cost.
- Make index configuration explicit, versioned, and migration-safe.
