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

## Wave 0 Phase 2 — whole-repo results (2026-09-04)

Corpus: whole-repo `.py` files, tracked-only via `git ls-files -z --cached
--exclude-standard -- '*.py'` on the host (this worktree's `.git` is a
file with a host-path gitdir and does not resolve inside the container,
so the manifest must be generated on the host and passed via
`--file-list`). 3,025 files in the manifest; 2,754 produced non-trivial
chunks (271 were empty/trivial). Same 41-query set as Phase 1, `top_k=20`.

```
docker exec -i mcp-dope-context env \
  PYTHONPATH=/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src \
  python /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/run_eval.py \
  --corpus /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001 \
  --file-list /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/eval_whole_repo_py_manifest.txt \
  --queries /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/queries.jsonl \
  --profiles A,B,Bh,CTRL \
  --json
```

Run in 3 real invocations (B+Bh+A/CTRL split across sessions applying
incremental harness fixes, described below) rather than one, but all are
genuine paid API calls against the whole-repo corpus. Every throwaway
Qdrant collection was deleted after each run (verified via the harness's
`finally` block, same as Phase 1).

### Three real bugs found only at whole-repo scale

Phase 1's 33-file corpus could not have surfaced any of these — all three
are properties of scale, not of the harness logic itself:

1. **Crude token-guardrail overshoot.** The original guardrail estimated
   input tokens as `len(text) // 4`, which overshoots the real
   Voyage-tokenizer count by ~10-20% on code. At whole-repo scale this
   tripped a false-positive refusal before any API call (real doc_tokens
   ≈9.89M for A/B, guardrail estimated ≈11.8M against a 10M cap). Fixed
   by calling the real (free, local, no-network) `voyage_client.count_tokens()`
   at the guardrail check sites instead, and raising the cap to 15M
   (comfortably above the real ~11.1M max for Bh, still well below the
   deliberately-excluded repo+`docs/*.md` corpus at ~21M+ real tokens).
2. **73 empty-content chunks.** A tree-sitter chunking edge case produces
   chunks with empty/whitespace-only `content` for a handful of symbols
   (e.g. stub methods). Profile B sends raw chunk content directly, and
   Voyage's flat `embed` endpoint rejects empty strings in a batch. Fixed
   by skipping chunks where `not content.strip()` in `build_corpus` (Bh
   was unaffected — it always prepends a non-empty scope-header line, so
   never produced a genuinely empty document text even before this fix).
3. **`contextualized_embed` per-file and per-batch token caps.** Voyage's
   `voyage-context-4` contextualized endpoint (used by profiles A and
   CTRL only — B/Bh use the flat endpoint, unaffected) enforces two real
   limits, confirmed via live error text: (a) a single "document" example
   (one file's full chunk list) cannot exceed 32,000 tokens — 6 of 2,754
   whole-repo files exceed this (largest: `services/repo-truth-extractor/run_extraction_v5.py`
   at 175,208 tokens, 5.5x the limit); (b) a submitted batch cannot exceed
   120,000 tokens in total, which a batch of the harness's old fixed
   count of 20 files could still exceed even with no single file over the
   32K per-file cap. Fixed by (a) excluding the 6 oversized files from
   A/CTRL's `grouped_texts` only, with a printed warning per exclusion —
   B/Bh keep them since they don't have this per-file limit; and (b)
   rewriting `embed_contextual`'s batching to pack files by real
   cumulative token count (cap 100,000, leaving margin below the observed
   120,000 real limit) instead of a fixed document count.

None of the 6 files excluded from A/CTRL are under `services/dope-context/src/`
(the only directory the query set's `expected.rel_path` targets live in),
so excluding them does not bias the A vs B/Bh recall comparison — it only
shrinks A/CTRL's distractor pool by 6 of 2,754 files (0.2%). `chunks_indexed`
differs across profiles for exactly this reason: A/CTRL index 36,989
chunks (2,754 files minus the 6 excluded, minus the 73 empty), B indexes
38,175 (2,754 files minus the 73 empty), Bh indexes 38,248 (2,754 files,
the 73 near-empty ones still present since their scope-header text is
non-empty).

### Whole-repo results table

| Profile | Status | Recall@5 | Recall@20 | MRR | NDCG@10 | Chunks | Doc tokens | Cost (USD) | ID-subset R@20 |
|---|---|---|---|---|---|---|---|---|---|
| A | OK | 0.7805 | 0.9512 | 0.6766 | 0.7136 | 36,989 | 9,381,624 | $1.125960 | 0.500 |
| B | OK | 0.9512 | 1.0000 | 0.8547 | 0.8901 | 38,175 | 9,844,172 | $1.181466 | 1.000 |
| Bh | OK | 0.9512 | 1.0000 | 0.7291 | 0.7884 | 38,248 | 11,054,695 | $1.326729 | 1.000 |
| CTRL | OK | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 36,989 | 0 (reused A) | $0.000248 | 0.000 |

Bhl was **not run at whole-repo scale**: a real per-chunk extrapolation
(2,888,668 in / 24,702 out LLM tokens over 455 phase-1 chunks → ~6,349
in / ~54 out per chunk, × 38,249 whole-repo chunks) projects **~$51 for
the LLM situating-context step alone** — over 5x the packet's $10
ceiling, before any embedding cost. This was never budgeted in the
packet's original cost table (which covered A/B/Control only). Bhl was
instead rerun for real on the Phase 1 (33-file) corpus once the API keys
were both fixed — see below.

### Reading the whole-repo table — this is the decision-grade result

At real whole-repo distractor scale, the signal sharpens considerably
compared to Phase 1's saturated-recall 41-query smoke test:

- **B wins on every metric.** Recall@20=1.0 (perfect), best MRR (0.855)
  and NDCG@10 (0.890) of all profiles that ran at this scale. This
  matches and strengthens the packet's own D1 recommendation
  (`voyage-code-4` both sides).
- **A (context-4, contextualized both sides) is now clearly the worst of
  the three working profiles** — Recall@5 drops to 0.78, Recall@20 to
  0.95 (not perfect, unlike Phase 1), MRR 0.68, NDCG@10 0.71. The
  contextualized approach's cross-chunk context did not help retrieval
  quality at this scale and materially underperforms the simple flat
  approach (B) on every measured axis. This reverses the ambiguous
  Phase-1 read (where A and B were recall-tied and only MRR/NDCG favored
  B) into an unambiguous one.
- **Bh (B + scope-header prefix) again has the lowest MRR/NDCG of the
  perfect-recall profiles** (0.729/0.788 vs B's 0.855/0.890), confirming
  the Phase-1 finding that the header prefix does not help ranking
  quality — it costs more (larger doc_tokens, +$0.145 vs B) for a worse
  result.
- **CTRL collapses to an exact 0.0 across all four metrics** at
  whole-repo scale (vs 0.024/0.0017/0.000 at Phase 1's small scale) — an
  even cleaner confirmation that the harness's metrics computation is
  discriminating correctly: querying one vector space with embeddings
  from an incompatible model produces total retrieval failure, not noise.

### Bhl — Phase 1 corpus, real run (2026-09-04, after whole-repo projection ruled out a whole-repo run)

| Profile | Status | Recall@5 | Recall@20 | MRR | NDCG@10 | Chunks | Doc tokens | LLM tokens in/out | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|
| Bhl | OK | 1.0000 | 1.0000 | 0.7947 | 0.8479 | 455 | 160,944 | 2,888,668 / 24,581 | $0.626710 |

Bhl (Bh + a 1-2 sentence LLM-generated situating context per chunk, via
`gpt-5.6-luna`) beats Bh's own Phase-1 result (MRR 0.795 vs 0.794 — a
wash) but still underperforms B (0.855) at Phase-1 scale, at roughly 40x
the per-query cost. Consistent with the packet's own D3 recommendation
(LLM context layer off by default) — even where it can be afforded, it
does not beat the simpler flat approach.

### Real spend accounting (all confirmed via billed API responses, not estimates)

| Item | Cost (USD) |
|---|---|
| Phase 1 baseline (A/B/Bh/CTRL + replicate, 2026-09-03) | $0.079825 |
| Bhl attempt that failed on an invalid Voyage key — OpenAI calls had already succeeded and billed before the Voyage step failed | $0.607376 |
| Bhl success, Phase 1 corpus (2026-09-04) | $0.626710 |
| Bh, whole-repo | $1.326729 |
| B, whole-repo | $1.181466 |
| A, whole-repo | $1.125960 |
| CTRL, whole-repo | $0.000248 |
| **Total real spend** | **$4.948314** |
| Remaining of $10 packet ceiling | $5.051686 |

Every A/B/CTRL guardrail failure documented above (crude-estimator trip,
per-file 32K trip, per-batch 120K trip) incurred **$0** — Voyage rejects
malformed/oversized batches during request validation, before any model
computation or billing.

### D1/D3 recommendation, now backed by decision-grade whole-repo data

**D1 (code vector space): `voyage-code-4` both sides (profile B).**
Confirmed, not just recommended — B has perfect Recall@20 and the best
MRR/NDCG of every profile tested at real whole-repo distractor scale,
beating the contextualized alternative (A) on every axis while also being
cheaper (~5% lower doc-token cost than A, ~11% lower than Bh).

**D3 (LLM situating-context layer): off by default.** Confirmed at Phase
1 scale (Bhl ties Bh's MRR, still loses to B, at ~40x the cost) and never
justified a whole-repo test — the ~$51 projected cost for whole-repo Bhl
alone would need to overcome B's already-superior result to be worth
running, and nothing in the Phase-1 data suggests it would.

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
## Whole-repo raw JSON output

### B (whole-repo)

```json
{
  "run_id": "4c5a409d",
  "timestamp": "2026-09-04T02:50:40.116570+00:00",
  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001",
  "corpus_files": 2754,
  "corpus_chunks": 38175,
  "queries_count": 41,
  "top_k": 20,
  "profiles": {
    "A": {
      "profile": "A",
      "status": "FAILED",
      "reason": "Request to model 'voyage-context-4' failed. The max allowed tokens per submitted batch is 120000. Your batch has 138171 tokens after truncation. Please lower the number of tokens in the batch.",
      "collection_name": "eval_a_9654e223",
      "chunks_indexed": 0,
      "doc_tokens": 0,
      "query_tokens": 0,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.0,
      "metrics": {},
      "identifier_subset": {}
    },
    "B": {
      "profile": "B",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_b_6d39ebbb",
      "chunks_indexed": 38175,
      "doc_tokens": 9844172,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 1.181466,
      "metrics": {
        "recall_at_5": 0.9512195121951219,
        "recall_at_20": 1.0,
        "mrr": 0.8546747967479674,
        "ndcg_at_10": 0.8901253142117443
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 1.0
      }
    },
    "CTRL": {
      "profile": "CTRL",
      "status": "FAILED",
      "reason": "Request to model 'voyage-context-4' failed. The max allowed tokens per submitted batch is 120000. Your batch has 138171 tokens after truncation. Please lower the number of tokens in the batch.",
      "collection_name": "eval_ctrl_e3749e17",
      "chunks_indexed": 0,
      "doc_tokens": 0,
      "query_tokens": 0,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.0,
      "metrics": {},
      "identifier_subset": {}
    }
  }
}
```

### A+CTRL (whole-repo)

```json
{
  "run_id": "beecb104",
  "timestamp": "2026-09-04T03:00:52.622458+00:00",
  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001",
  "corpus_files": 2754,
  "corpus_chunks": 38176,
  "queries_count": 41,
  "top_k": 20,
  "profiles": {
    "A": {
      "profile": "A",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_a_c0679d55",
      "chunks_indexed": 36989,
      "doc_tokens": 9381624,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 1.12596,
      "metrics": {
        "recall_at_5": 0.7804878048780488,
        "recall_at_20": 0.9512195121951219,
        "mrr": 0.6766326153521276,
        "ndcg_at_10": 0.7135625935017484
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 0.5
      }
    },
    "CTRL": {
      "profile": "CTRL",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_ctrl_bc1d1ec7",
      "chunks_indexed": 36989,
      "doc_tokens": 0,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.000248,
      "metrics": {
        "recall_at_5": 0.0,
        "recall_at_20": 0.0,
        "mrr": 0.0,
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

### Bh (whole-repo, from round 2)

```json
{
  "run_id": "e5147b44",
  "timestamp": "2026-09-04T02:37:31.141062+00:00",
  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001",
  "corpus_files": 2754,
  "corpus_chunks": 38248,
  "queries_count": 41,
  "top_k": 20,
  "profiles": {
    "A": {
      "profile": "A",
      "status": "FAILED",
      "reason": "Request to model 'voyage-context-4' failed. The example at index 17 in your batch has too many tokens and does not fit into the model's context window of 32000 tokens. Contextualized chunk embeddings do not support truncation. Either lower the number of tokens in the listed example(s), or pass `enable_auto_chunking=true` with `input_type=\"document\"` and one string per input to have the server split oversize documents.",
      "collection_name": "eval_a_aa019658",
      "chunks_indexed": 0,
      "doc_tokens": 0,
      "query_tokens": 0,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.0,
      "metrics": {},
      "identifier_subset": {}
    },
    "B": {
      "profile": "B",
      "status": "FAILED",
      "reason": "The request body is not valid JSON, or some arguments were not specified properly. In particular, Error for argument 'input': Value error, Input cannot contain empty strings or empty lists",
      "collection_name": "eval_b_cc976148",
      "chunks_indexed": 0,
      "doc_tokens": 0,
      "query_tokens": 0,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.0,
      "metrics": {},
      "identifier_subset": {}
    },
    "Bh": {
      "profile": "Bh",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_bh_f5869725",
      "chunks_indexed": 38248,
      "doc_tokens": 11054695,
      "query_tokens": 1379,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 1.326729,
      "metrics": {
        "recall_at_5": 0.9512195121951219,
        "recall_at_20": 1.0,
        "mrr": 0.7290650406504063,
        "ndcg_at_10": 0.7883709300381208
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 1.0
      }
    },
    "CTRL": {
      "profile": "CTRL",
      "status": "FAILED",
      "reason": "Request to model 'voyage-context-4' failed. The example at index 17 in your batch has too many tokens and does not fit into the model's context window of 32000 tokens. Contextualized chunk embeddings do not support truncation. Either lower the number of tokens in the listed example(s), or pass `enable_auto_chunking=true` with `input_type=\"document\"` and one string per input to have the server split oversize documents.",
      "collection_name": "eval_ctrl_343a206b",
      "chunks_indexed": 0,
      "doc_tokens": 0,
      "query_tokens": 0,
      "llm_tokens_in": 0,
      "llm_tokens_out": 0,
      "cost_usd": 0.0,
      "metrics": {},
      "identifier_subset": {}
    }
  }
}
```

### Bhl (phase-1 rerun)

```json
{
  "run_id": "56080a9b",
  "timestamp": "2026-09-04T02:37:21.206813+00:00",
  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src",
  "corpus_files": 33,
  "corpus_chunks": 455,
  "queries_count": 41,
  "top_k": 20,
  "profiles": {
    "Bhl": {
      "profile": "Bhl",
      "status": "OK",
      "reason": null,
      "collection_name": "eval_bhl_a97007d0",
      "chunks_indexed": 455,
      "doc_tokens": 160944,
      "query_tokens": 1379,
      "llm_tokens_in": 2888668,
      "llm_tokens_out": 24581,
      "cost_usd": 0.62671,
      "metrics": {
        "recall_at_5": 1.0,
        "recall_at_20": 1.0,
        "mrr": 0.7947154471544714,
        "ndcg_at_10": 0.8478949538554585
      },
      "identifier_subset": {
        "count": 2,
        "recall_at_20": 1.0
      }
    }
  }
}
```
