# Wave 0 Results — 2026-09-03

Run against the real `mcp-dope-context` / `mcp-qdrant` containers via:

```
docker exec -i mcp-dope-context env \
  PYTHONPATH=/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src \
  python /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/run_eval.py \
  --corpus /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src \
  --queries /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/queries.jsonl \
  --profiles A,B,Bh,Bhl,CTRL \
  --json
```

Corpus: 33 files, 455 chunks (after excluding whole-file duplicate
"module"-as-block chunks). 41 queries. `top_k=20`. Exit code 0. All 5
throwaway Qdrant collections (`eval_a_176ef01d`, `eval_b_6ca3e49a`,
`eval_bh_aa225a31`, `eval_ctrl_065f17b9`, plus none created for
`Bhl` since it was `NOT_RUN`) were confirmed deleted after the run —
verified via a live `get_collections()` call against `mcp-qdrant`
showing zero `eval_*` collections remaining.

## Results table

| Profile | Status | Recall@5 | Recall@20 | MRR | NDCG@10 | Chunks | Doc tokens | Query tokens | Cost (USD) | ID-subset n | ID-subset R@20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | OK | 1.000 | 1.000 | 0.8537 | 0.8914 | 455 | 127,130 | 1,379 | $0.015421 | 2 | 1.000 |
| B | OK | 1.000 | 1.000 | 0.9187 | 0.9396 | 455 | 126,693 | 1,379 | $0.015369 | 2 | 1.000 |
| Bh | OK | 1.000 | 1.000 | 0.7935 | 0.8461 | 455 | 137,861 | 1,379 | $0.016709 | 2 | 1.000 |
| Bhl | **NOT_RUN** | — | — | — | — | — | — | — | $0.000000 | — | — |
| CTRL | OK | 0.000 | 0.0244 | 0.0017 | 0.000 | 455 | 0 (reused A) | 1,379 | $0.000248 | 2 | 0.000 |

Total measured cost across all profiles that ran: **$0.047747**.

Replicate: re-running B and Bh on 2026-09-03 (labelled D/Dh, since removed — B already uses voyage-code-4) reproduced MRR/NDCG identical to four decimals; Voyage embeddings are deterministic across runs. Cost of the replicate: $0.032078.

### Reading the table

- **A vs B**: both hit perfect Recall@5/@20 on this 41-query set. B (flat
  , no cross-chunk context) actually edges out A on MRR and
  NDCG@10 (0.9187/0.9396 vs 0.8537/0.8914) — the top hit lands correctly
  more often under B than under A on this corpus/query mix. This is a real
  measured result, not an estimate; with only 41 queries it should be read
  as a signal, not a verdict — a wider Wave 1 query set would sharpen it.
- **Bh** (B + scope-header prefix on document text) has the same perfect
  recall but the *lowest* MRR/NDCG of the three working profiles
  (0.7935/0.8461) — the header prefix does not help ranking quality here,
  and by these two rank-sensitive metrics it mildly hurts it.
- **Bhl**: `OPENAI_API_KEY` is not set in the
  container (confirmed via a live env check before the run), so the
  harness skipped it entirely per its designed fallback — no embedding or
  LLM calls were made for this profile, and its cost is $0.
- **CTRL** (index = profile A's real voyage-context-4 document vectors,
  queries = voyage-code-3 flat embeddings — the historical embedding-space
  mismatch): Recall@5 collapses to 0.0, Recall@20 to 0.024, MRR to 0.0017,
  NDCG@10 to 0.0. This is the expected signature of querying one vector
  space with embeddings from an incompatible model/space, and it is useful
  as a sanity check that the harness's metrics computation is actually
  discriminating (a harness bug that always returns 1.0 regardless of
  input would not have produced this collapse). Query-side cost only
  ($0.000248 for ~1,379 tokens at $0.18/M on `voyage-code-3`); document
  side cost is $0 because it reused A's already-computed embeddings
  rather than re-embedding.

### Identifier-subset metric

Only 2 of the 41 queries contain a camelCase/snake_case token (queries are
intentionally symptom-style and non-verbatim, so this is expected to be a
small subset). Both are found within top-20 for A/B/Bh, and both are
missed for CTRL, consistent with the whole-set pattern above. With n=2 this
subset is too small to draw a separate conclusion from — it moves in
lockstep with the whole-set numbers here.

## Raw JSON output

```json
{
  "run_id": "1035c556",
  "timestamp": "2026-09-03T12:30:14.722593+00:00",
  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src",
  "corpus_files": 33,
  "corpus_chunks": 455,
  "queries_count": 41,
  "top_k": 20,
  "profiles": {
    "A": {
      "profile": "A",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_a_176ef01d",
      "chunks_indexed": 455,
      "doc_tokens": 127130,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.015421,
      "metrics": {
        "recall_at_5": 1.0,
        "recall_at_20": 1.0,
        "mrr": 0.8536585365853658,
        "ndcg_at_10": 0.8914009275261381
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 1.0
      }
    },
    "B": {
      "profile": "B",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_b_6ca3e49a",
      "chunks_indexed": 455,
      "doc_tokens": 126693,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.015369,
      "metrics": {
        "recall_at_5": 1.0,
        "recall_at_20": 1.0,
        "mrr": 0.9186991869918698,
        "ndcg_at_10": 0.9396029027874593
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 1.0
      }
    },
    "Bh": {
      "profile": "Bh",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_bh_aa225a31",
      "chunks_indexed": 455,
      "doc_tokens": 137861,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.016709,
      "metrics": {
        "recall_at_5": 1.0,
        "recall_at_20": 1.0,
        "mrr": 0.7934959349593496,
        "ndcg_at_10": 0.8460593466504235
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 1.0
      }
    },
    "Bhl": {
      "profile": "Bhl",
      "status": "NOT_RUN",
      "reason": "OPENAI_API_KEY not set in mcp-dope-context container",
      "collection_name": null,
      "chunks_indexed": 0,
      "doc_tokens": 0,
      "query_tokens": 0,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.0,
      "metrics": {},
      "identifier_subset": {}
    },
    "CTRL": {
      "profile": "CTRL",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_ctrl_065f17b9",
      "chunks_indexed": 455,
      "doc_tokens": 0,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.000248,
      "metrics": {
        "recall_at_5": 0.0,
        "recall_at_20": 0.024390243902439025,
        "mrr": 0.0017421602787456446,
        "ndcg_at_10": 0.0
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 0.0
      }
    }
  }
}
```
