# Wave 0 — Offline Retrieval Evaluation Harness

Self-contained offline eval for `dope-context` retrieval quality. Everything
needed lives under this `eval/` directory; it imports `CodeChunker` from
`../src/preprocessing/code_chunker.py` (read-only) but never modifies
anything under `services/dope-context/src/` or `services/dope-context/tests/`.

## What it measures

For a fixed corpus (`services/dope-context/src/**/*.py`) and a fixed set of
35-45 natural-language, symptom-style queries with hand-authored ground
truth (`{rel_path, symbol}`), the harness embeds the corpus under several
embedding **profiles**, indexes each into a throwaway Qdrant collection,
runs the query set against it with exact (non-HNSW) cosine/dot search at
`top_k=20`, computes retrieval metrics, and deletes the collection.

### Profiles

| Profile | Document embedding | Query embedding | Notes |
|---|---|---|---|
| `A` | `voyage-context-4`, `contextualized_embed`, grouped per source file | `voyage-context-4`, `contextualized_embed` | Context-aware both sides |
| `B` | `voyage-code-4`, flat `embed` | `voyage-code-4`, flat `embed` | No cross-chunk context |
| `Bh` | `B` + a scope-header prefix (`# file: ...` / `# symbol: ...`) on the embedded document text | same as `B` | Header only on the document side |
| `Bhl` | `Bh` + a 1-2 sentence LLM-generated situating context (OpenAI `gpt-5.6-luna`) prepended to the document text | same as `B` | `NOT_RUN` if `OPENAI_API_KEY` is absent, or if any call fails after retries |
| `CTRL` | **reuses profile `A`'s already-computed** `voyage-context-4` contextual document embeddings (zero marginal doc-embedding cost) | `voyage-code-3`, flat `embed` | Deliberate historical index/query embedding-space mismatch, run as a control |

`CTRL` was added mid-task at the coordinator's request (citing
`TP-DOPECONTEXT-VECTOR-SPACE-0004` step 3, "measure the current broken
configuration as a control") to quantify how badly retrieval degrades when
the index and the query embeddings come from two different model spaces.

A later request to add two further profiles ("D" — dense-only on
`voyage-code-4`, which is definitionally identical to the already-specified
profile `B`, described as new — and "Dh" — hybrid BM25 + an unverified
`rerank-3` reranking model never part of this harness's scope) was
**declined**. It arrived through the same low-provenance channel as the
`CTRL` request but was internally inconsistent (a "new" profile that
duplicates an existing one) and introduced an unverified external
dependency; see the run report for details. It was not implemented.

### Metrics

- **Recall@5 / Recall@20** — fraction of a query's expected `{rel_path,
  symbol}` items found within the top-5 / top-20 results.
- **MRR** — mean reciprocal rank of the first hit that matches any expected
  item (0 if no hit in the returned top-k matches).
- **NDCG@10** — binary-relevance normalized discounted cumulative gain over
  the top-10 results (`1 / log2(rank + 1)` per relevant hit, divided by the
  ideal DCG for that query's number of expected items).
- **Identifier subset** — per profile, the count of queries whose text
  contains a camelCase or snake_case token, and Recall@20 computed over
  just that subset (added mid-task; a proxy for "does the profile still
  work when the query happens to mention a real identifier-shaped word,
  even though queries are meant to be symptom-style and non-verbatim").

### "Whole-file duplicate" chunk filtering

The task's literal instruction ("skip `chunk_type == 'module'`") doesn't
correspond to any value `CodeChunker` actually produces — `"module"` is not
in its `chunk_type` `Literal`. Reading `code_chunker.py` shows what
actually happens: Python's target-node list includes the AST `"module"`
node (the whole file), but the classification logic falls through to
`chunk_type = "block"` for it, with `symbol_name = None` and
`parent_symbol = None`, spanning the entire file. That's the real
whole-file duplicate. The harness filters
`chunk_type == "block" and symbol_name is None and parent_symbol is None`
(`is_whole_file_duplicate()` in `run_eval.py`), which is unambiguous here
because tree-sitter is available in the container, so the line-based
fallback chunker (which also emits `chunk_type == "block"`, but for
partial, non-whole-file spans) is never invoked for `.py` files.

## Ground truth honesty

Two categories of candidate ground truth were deliberately **excluded**
from `queries.jsonl` because the target symbol has a behaviorally
near-identical duplicate elsewhere in the corpus, which would make the
"correct" answer ambiguous:

- `CostTracker.add_request` — duplicated across three files
  (`voyage_embedder.py`, `contextualized_embedder.py`, and the reranker),
  each essentially the same running-cost accumulator.
- `_should_ignore` — a near-duplicate path-ignore predicate implemented
  independently in both `sync/file_synchronizer.py` and
  `autonomous/watchdog_monitor.py`.

## Guardrails

- Refuses to run at all unless `--corpus` resolves to a path ending in
  `services/dope-context/src` — never embeds anything outside it.
- Aborts a single profile (marked `FAILED`, not silently skipped) if its
  projected input tokens exceed 200,000, checked *before* any embedding API
  call for that profile.
- Every embedding / chat-completion API call is retried up to 3 times with
  exponential backoff before the harness gives up on that profile.
- Every throwaway Qdrant collection (`eval_<profile>_<8hex>`) is created
  fresh and deleted in a `try/finally`, regardless of whether the profile
  succeeded, failed, or was skipped.

## Running it

The `mcp-dope-context` container mounts this worktree **read-only**, so the
harness itself cannot write results back into the worktree — copy its
stdout JSON into `claudedocs/dope-context-eval-results-<date>.md` by hand
(not into this directory: the repo's `markdown-location-guard` hook rejects
any `.md` outside the canonical docs roots) (or redirect it to a file
outside the worktree and paste from there).

```bash
docker exec -i mcp-dope-context env \
  PYTHONPATH=/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src \
  python /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/run_eval.py \
  --corpus /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src \
  --queries /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/queries.jsonl \
  --profiles A,B,Bh,Bhl,CTRL \
  --json
```

Requires `VOYAGE_API_KEY` in the container environment (present as of this
run). `OPENAI_API_KEY` is optional — if absent, profile `Bhl` reports
`NOT_RUN` with that reason instead of failing the whole run.

## Budget

~96K corpus tokens. Embedding profiles `A`/`B`/`Bh`/`Bhl` at
$0.12/M tokens (voyage-context-4 / voyage-code-4) is on the order of
$0.06 total; the `Bhl` LLM-context generation pass (`gpt-5.6-luna`,
$0.20/M in, $1.20/M out) is on the order of $0.03 when it runs. `CTRL`
reuses `A`'s document embeddings (no marginal document cost) and only pays
for ~40 query embeddings on `voyage-code-3` ($0.18/M tokens) — negligible.
Exact, measured (not estimated) per-profile costs are reported in the
harness's own JSON output (`cost_usd` field) and copied into
`claudedocs/dope-context-eval-results-<date>.md`.
