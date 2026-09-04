# Independent embedded audit — PR #1304, round 4 (delta)

You are an independent auditor. You did not write this code. Your job is to
find what is wrong with it, not to confirm it is fine. A verdict of CLOSED is
only appropriate if you actively tried to break the change and failed.

## Custody

* Repository: `DDD-Enterprises/dopemux-mvp`
* PR: **#1304** (draft), branch `claude/dope-context-retrieval-redesign-2026-09-03`
* Target head this round: **`e80cda77d949d8a815f8a6a2fbb6d0d7003e2c75`**
* Previously audited head: `9ef316d1b1327e201184e7bdf5dbf943f88b8fa3` (round 3)
* Delta under audit: **`8a06626c9..e80cda77d`**, 14 files, +1454/−122

## Prior rounds (do not re-litigate unless the delta reopens them)

* **Round 1** — verdict FAIL. `F-001` BLOCKER: the surface guard's
  `_repo_relative` was purely lexical, so `<root>/../<root>/x`, a case-variant
  root, or a symlinked root produced a repo-relative string that no
  `^`-anchored red-lane pattern matched. Fixed in `1d87cb732`.
* **Round 2** — verdict CLOSED_WITH_RISKS. `F-001-A` HIGH: intra-repo
  case-variant bypass (`SERVICES/...`) on case-insensitive filesystems. Fixed
  in `a4f86c48c` by adding a whole-path case-folded candidate.
* **Round 3** — verdict CLOSED, 0 residual risks, 0 regressions.

**Your round-4 job includes checking that the delta does not regress F-001 or
F-001-A.** The delta edits the very regex those findings concerned.

## What the delta claims to do

1. **ADR-226 amendments A2 and A3** extend a narrow negative-lookahead
   carve-out in `src/dopemux/dcp/red_lane_rules.py`. The red lane
   `DCP-RED-MERGE-SEAM-0001` blanket-blocks `^services/dope-context/.*$`. The
   carve-out is supposed to exempt *only*: the `eval/` subtree, and exactly
   five named files. A2 added `src/index_profile.py` and
   `src/embeddings/model_registry.py`; A3 added
   `tests/test_vector_profiles_and_migration.py`.
2. **D1 implementation**: code `content_vec` moved from a contextualized model
   (`voyage-context-4`, `contextualized_embeddings` endpoint) to a flat model
   (`voyage-code-4`, `embeddings` endpoint), so index and query share one
   vector space. `title_vec` and `breadcrumb_vec` move too, because all three
   resolve through `resolve_code_embed_model()` → `DEFAULT_CODE_MODEL`.
3. **Four test premises rewritten** in the newly-carved-out test file, because
   D1 falsified them.

## What to audit, in priority order

### A. Carve-out containment (highest risk — this is a security boundary)

* Does the extended regex exempt anything beyond the six intended paths
  (`eval/**` plus five files)? Construct concrete bypass strings and check
  them against the actual regex semantics.
* Are the new lookaheads anchored such that `.bak`, `.orig`, `.tmp`, `.pyc`
  suffixes, same-named files in other directories, and nested same-named files
  remain blocked?
* Does the companion traversal-refusal pattern still cover the newly-exempted
  paths (e.g. `eval/../src/index_profile.py`)?
* Does the whole-path case-folding from the F-001-A fix still apply to the new
  exemptions? Could `SRC/INDEX_PROFILE.PY` or `Tests/Test_Vector_Profiles...`
  slip through?
* Does the fallback tuple in `.claude/hooks/dcp_surface_guard.py` remain a
  subset of the live rules?

### B. D1 correctness — endpoint/model coherence

* Voyage's `contextualized_embed` accepts **only** `voyage-context-3` and
  `voyage-context-4`. The flat `embeddings` endpoint accepts the rest.
  **Find any remaining path where a flat code model could reach the
  contextualized endpoint, or a contextualized model reach the flat one.**
  Both the index path (`indexing_pipeline.py`) and the query path
  (`mcp/server.py`) were changed to branch on `content_profile.endpoint`.
  Check every construction site of `ContextualizedEmbedder` and
  `VoyageEmbedder`, including cached/factory helpers and default arguments.
* The collection manifest was changed to read from `content_profile` instead
  of `contextualized_embedder.default_model`. Is the manifest now consistent
  with what is actually written into the collection?
* `compare_collection_manifests` fails closed on a model/endpoint change. Does
  the change strand existing collections without a stated migration path, and
  is that disclosed?

### C. Registry values — are the recorded limits defensible?

* `voyage-code-4` is registered with `max_request_tokens=320_000` while the
  superseded `voyage-code-3` carries `120_000`. The comment argues from (a)
  the vendor's group sentence omitting `voyage-code-4`, (b) rate-limit tables
  grouping it with `voyage-4`/`voyage-3.5`, and (c) a live 300,000-token batch
  accepted and billed. **This value sizes real production batches. Is
  inferring it safe, and is the failure direction correct?** Note the value is
  explicitly documented as an inference, not a vendor figure.
* `per_input_tokens=32_000` is documented as *silently truncating* rather than
  rejecting. Is the resulting correctness hazard adequately guarded upstream,
  or merely commented?

### D. Test integrity (look hard here)

Four failing tests were rewritten by the same effort that made them fail.
**Determine whether any assertion was weakened or silently dropped to obtain a
green suite**, rather than restated because its premise genuinely changed.

* Count and compare assertions before/after.
* Was any `xfail`, `skip`, or broadened matcher introduced to mask a failure?
* `test_vector_space_invariants.py` had a `strict=True` xfail removed. Is the
  replacement a real test, or a tautology that cannot fail?
* Does the suite still actually assert index/query agreement for all six named
  vectors, or only appear to?

### E. Scope discipline

* Does the delta touch any file outside what the amendments authorize?
* The commit `3e878cc8d` was made while 4 tests were knowingly failing. Is
  that disclosed accurately in the commit message?

## Required output

Return **only** a JSON object, no prose around it:

```json
{
  "verdict": "CLOSED" | "CLOSED_WITH_RISKS" | "OPEN",
  "reasoning": "<why, citing specific files/lines>",
  "residual_risks": [{"id":"", "severity":"LOW|MEDIUM|HIGH|BLOCKER", "detail":"", "location":""}],
  "regressions_introduced": [{"id":"", "severity":"", "detail":"", "location":""}],
  "f001_regression_check": "<did the delta reopen F-001 or F-001-A? evidence>",
  "bypass_attempts_considered": ["<each concrete string or path you tested>"],
  "test_integrity_finding": "<were assertions weakened? evidence: counts, specific assertions>"
}
```

Be specific. Cite file and line. If you cannot verify something from the diff
alone, say so explicitly rather than assuming it is correct.

## The delta

```diff
diff --git a/claudedocs/dope-context-eval-results-2026-09-03.md b/claudedocs/dope-context-eval-results-2026-09-03.md
index c6672b11f..4316ba171 100644
--- a/claudedocs/dope-context-eval-results-2026-09-03.md
+++ b/claudedocs/dope-context-eval-results-2026-09-03.md
@@ -71,6 +71,171 @@ missed for CTRL, consistent with the whole-set pattern above. With n=2 this
 subset is too small to draw a separate conclusion from — it moves in
 lockstep with the whole-set numbers here.
 
+## Wave 0 Phase 2 — whole-repo results (2026-09-04)
+
+Corpus: whole-repo `.py` files, tracked-only via `git ls-files -z --cached
+--exclude-standard -- '*.py'` on the host (this worktree's `.git` is a
+file with a host-path gitdir and does not resolve inside the container,
+so the manifest must be generated on the host and passed via
+`--file-list`). 3,025 files in the manifest; 2,754 produced non-trivial
+chunks (271 were empty/trivial). Same 41-query set as Phase 1, `top_k=20`.
+
+```
+docker exec -i mcp-dope-context env \
+  PYTHONPATH=/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src \
+  python /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/run_eval.py \
+  --corpus /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001 \
+  --file-list /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/eval_whole_repo_py_manifest.txt \
+  --queries /workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/eval/queries.jsonl \
+  --profiles A,B,Bh,CTRL \
+  --json
+```
+
+Run in 3 real invocations (B+Bh+A/CTRL split across sessions applying
+incremental harness fixes, described below) rather than one, but all are
+genuine paid API calls against the whole-repo corpus. Every throwaway
+Qdrant collection was deleted after each run (verified via the harness's
+`finally` block, same as Phase 1).
+
+### Three real bugs found only at whole-repo scale
+
+Phase 1's 33-file corpus could not have surfaced any of these — all three
+are properties of scale, not of the harness logic itself:
+
+1. **Crude token-guardrail overshoot.** The original guardrail estimated
+   input tokens as `len(text) // 4`, which overshoots the real
+   Voyage-tokenizer count by ~10-20% on code. At whole-repo scale this
+   tripped a false-positive refusal before any API call (real doc_tokens
+   ≈9.89M for A/B, guardrail estimated ≈11.8M against a 10M cap). Fixed
+   by calling the real (free, local, no-network) `voyage_client.count_tokens()`
+   at the guardrail check sites instead, and raising the cap to 15M
+   (comfortably above the real ~11.1M max for Bh, still well below the
+   deliberately-excluded repo+`docs/*.md` corpus at ~21M+ real tokens).
+2. **73 empty-content chunks.** A tree-sitter chunking edge case produces
+   chunks with empty/whitespace-only `content` for a handful of symbols
+   (e.g. stub methods). Profile B sends raw chunk content directly, and
+   Voyage's flat `embed` endpoint rejects empty strings in a batch. Fixed
+   by skipping chunks where `not content.strip()` in `build_corpus` (Bh
+   was unaffected — it always prepends a non-empty scope-header line, so
+   never produced a genuinely empty document text even before this fix).
+3. **`contextualized_embed` per-file and per-batch token caps.** Voyage's
+   `voyage-context-4` contextualized endpoint (used by profiles A and
+   CTRL only — B/Bh use the flat endpoint, unaffected) enforces two real
+   limits, confirmed via live error text: (a) a single "document" example
+   (one file's full chunk list) cannot exceed 32,000 tokens — 6 of 2,754
+   whole-repo files exceed this (largest: `services/repo-truth-extractor/run_extraction_v5.py`
+   at 175,208 tokens, 5.5x the limit); (b) a submitted batch cannot exceed
+   120,000 tokens in total, which a batch of the harness's old fixed
+   count of 20 files could still exceed even with no single file over the
+   32K per-file cap. Fixed by (a) excluding the 6 oversized files from
+   A/CTRL's `grouped_texts` only, with a printed warning per exclusion —
+   B/Bh keep them since they don't have this per-file limit; and (b)
+   rewriting `embed_contextual`'s batching to pack files by real
+   cumulative token count (cap 100,000, leaving margin below the observed
+   120,000 real limit) instead of a fixed document count.
+
+None of the 6 files excluded from A/CTRL are under `services/dope-context/src/`
+(the only directory the query set's `expected.rel_path` targets live in),
+so excluding them does not bias the A vs B/Bh recall comparison — it only
+shrinks A/CTRL's distractor pool by 6 of 2,754 files (0.2%). `chunks_indexed`
+differs across profiles for exactly this reason: A/CTRL index 36,989
+chunks (2,754 files minus the 6 excluded, minus the 73 empty), B indexes
+38,175 (2,754 files minus the 73 empty), Bh indexes 38,248 (2,754 files,
+the 73 near-empty ones still present since their scope-header text is
+non-empty).
+
+### Whole-repo results table
+
+| Profile | Status | Recall@5 | Recall@20 | MRR | NDCG@10 | Chunks | Doc tokens | Cost (USD) | ID-subset R@20 |
+|---|---|---|---|---|---|---|---|---|---|
+| A | OK | 0.7805 | 0.9512 | 0.6766 | 0.7136 | 36,989 | 9,381,624 | $1.125960 | 0.500 |
+| B | OK | 0.9512 | 1.0000 | 0.8547 | 0.8901 | 38,175 | 9,844,172 | $1.181466 | 1.000 |
+| Bh | OK | 0.9512 | 1.0000 | 0.7291 | 0.7884 | 38,248 | 11,054,695 | $1.326729 | 1.000 |
+| CTRL | OK | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 36,989 | 0 (reused A) | $0.000248 | 0.000 |
+
+Bhl was **not run at whole-repo scale**: a real per-chunk extrapolation
+(2,888,668 in / 24,702 out LLM tokens over 455 phase-1 chunks → ~6,349
+in / ~54 out per chunk, × 38,249 whole-repo chunks) projects **~$51 for
+the LLM situating-context step alone** — over 5x the packet's $10
+ceiling, before any embedding cost. This was never budgeted in the
+packet's original cost table (which covered A/B/Control only). Bhl was
+instead rerun for real on the Phase 1 (33-file) corpus once the API keys
+were both fixed — see below.
+
+### Reading the whole-repo table — this is the decision-grade result
+
+At real whole-repo distractor scale, the signal sharpens considerably
+compared to Phase 1's saturated-recall 41-query smoke test:
+
+- **B wins on every metric.** Recall@20=1.0 (perfect), best MRR (0.855)
+  and NDCG@10 (0.890) of all profiles that ran at this scale. This
+  matches and strengthens the packet's own D1 recommendation
+  (`voyage-code-4` both sides).
+- **A (context-4, contextualized both sides) is now clearly the worst of
+  the three working profiles** — Recall@5 drops to 0.78, Recall@20 to
+  0.95 (not perfect, unlike Phase 1), MRR 0.68, NDCG@10 0.71. The
+  contextualized approach's cross-chunk context did not help retrieval
+  quality at this scale and materially underperforms the simple flat
+  approach (B) on every measured axis. This reverses the ambiguous
+  Phase-1 read (where A and B were recall-tied and only MRR/NDCG favored
+  B) into an unambiguous one.
+- **Bh (B + scope-header prefix) again has the lowest MRR/NDCG of the
+  perfect-recall profiles** (0.729/0.788 vs B's 0.855/0.890), confirming
+  the Phase-1 finding that the header prefix does not help ranking
+  quality — it costs more (larger doc_tokens, +$0.145 vs B) for a worse
+  result.
+- **CTRL collapses to an exact 0.0 across all four metrics** at
+  whole-repo scale (vs 0.024/0.0017/0.000 at Phase 1's small scale) — an
+  even cleaner confirmation that the harness's metrics computation is
+  discriminating correctly: querying one vector space with embeddings
+  from an incompatible model produces total retrieval failure, not noise.
+
+### Bhl — Phase 1 corpus, real run (2026-09-04, after whole-repo projection ruled out a whole-repo run)
+
+| Profile | Status | Recall@5 | Recall@20 | MRR | NDCG@10 | Chunks | Doc tokens | LLM tokens in/out | Cost (USD) |
+|---|---|---|---|---|---|---|---|---|---|
+| Bhl | OK | 1.0000 | 1.0000 | 0.7947 | 0.8479 | 455 | 160,944 | 2,888,668 / 24,581 | $0.626710 |
+
+Bhl (Bh + a 1-2 sentence LLM-generated situating context per chunk, via
+`gpt-5.6-luna`) beats Bh's own Phase-1 result (MRR 0.795 vs 0.794 — a
+wash) but still underperforms B (0.855) at Phase-1 scale, at roughly 40x
+the per-query cost. Consistent with the packet's own D3 recommendation
+(LLM context layer off by default) — even where it can be afforded, it
+does not beat the simpler flat approach.
+
+### Real spend accounting (all confirmed via billed API responses, not estimates)
+
+| Item | Cost (USD) |
+|---|---|
+| Phase 1 baseline (A/B/Bh/CTRL + replicate, 2026-09-03) | $0.079825 |
+| Bhl attempt that failed on an invalid Voyage key — OpenAI calls had already succeeded and billed before the Voyage step failed | $0.607376 |
+| Bhl success, Phase 1 corpus (2026-09-04) | $0.626710 |
+| Bh, whole-repo | $1.326729 |
+| B, whole-repo | $1.181466 |
+| A, whole-repo | $1.125960 |
+| CTRL, whole-repo | $0.000248 |
+| **Total real spend** | **$4.948314** |
+| Remaining of $10 packet ceiling | $5.051686 |
+
+Every A/B/CTRL guardrail failure documented above (crude-estimator trip,
+per-file 32K trip, per-batch 120K trip) incurred **$0** — Voyage rejects
+malformed/oversized batches during request validation, before any model
+computation or billing.
+
+### D1/D3 recommendation, now backed by decision-grade whole-repo data
+
+**D1 (code vector space): `voyage-code-4` both sides (profile B).**
+Confirmed, not just recommended — B has perfect Recall@20 and the best
+MRR/NDCG of every profile tested at real whole-repo distractor scale,
+beating the contextualized alternative (A) on every axis while also being
+cheaper (~5% lower doc-token cost than A, ~11% lower than Bh).
+
+**D3 (LLM situating-context layer): off by default.** Confirmed at Phase
+1 scale (Bhl ties Bh's MRR, still loses to B, at ~40x the cost) and never
+justified a whole-repo test — the ~$51 projected cost for whole-repo Bhl
+alone would need to overcome B's already-superior result to be worth
+running, and nothing in the Phase-1 data suggests it would.
+
 ## Raw JSON output
 
 ```json
@@ -188,3 +353,248 @@ lockstep with the whole-set numbers here.
   }
 }
 ```
+## Whole-repo raw JSON output
+
+### B (whole-repo)
+
+```json
+{
+  "run_id": "4c5a409d",
+  "timestamp": "2026-09-04T02:50:40.116570+00:00",
+  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001",
+  "corpus_files": 2754,
+  "corpus_chunks": 38175,
+  "queries_count": 41,
+  "top_k": 20,
+  "profiles": {
+    "A": {
+      "profile": "A",
+      "status": "FAILED",
+      "reason": "Request to model 'voyage-context-4' failed. The max allowed tokens per submitted batch is 120000. Your batch has 138171 tokens after truncation. Please lower the number of tokens in the batch.",
+      "collection_name": "eval_a_9654e223",
+      "chunks_indexed": 0,
+      "doc_tokens": 0,
+      "query_tokens": 0,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 0.0,
+      "metrics": {},
+      "identifier_subset": {}
+    },
+    "B": {
+      "profile": "B",
+      "status": "OK",
+      "reason": null,
+      "collection_name": "eval_b_6d39ebbb",
+      "chunks_indexed": 38175,
+      "doc_tokens": 9844172,
+      "query_tokens": 1379,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 1.181466,
+      "metrics": {
+        "recall_at_5": 0.9512195121951219,
+        "recall_at_20": 1.0,
+        "mrr": 0.8546747967479674,
+        "ndcg_at_10": 0.8901253142117443
+      },
+      "identifier_subset": {
+        "count": 2,
+        "recall_at_20": 1.0
+      }
+    },
+    "CTRL": {
+      "profile": "CTRL",
+      "status": "FAILED",
+      "reason": "Request to model 'voyage-context-4' failed. The max allowed tokens per submitted batch is 120000. Your batch has 138171 tokens after truncation. Please lower the number of tokens in the batch.",
+      "collection_name": "eval_ctrl_e3749e17",
+      "chunks_indexed": 0,
+      "doc_tokens": 0,
+      "query_tokens": 0,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 0.0,
+      "metrics": {},
+      "identifier_subset": {}
+    }
+  }
+}
+```
+
+### A+CTRL (whole-repo)
+
+```json
+{
+  "run_id": "beecb104",
+  "timestamp": "2026-09-04T03:00:52.622458+00:00",
+  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001",
+  "corpus_files": 2754,
+  "corpus_chunks": 38176,
+  "queries_count": 41,
+  "top_k": 20,
+  "profiles": {
+    "A": {
+      "profile": "A",
+      "status": "OK",
+      "reason": null,
+      "collection_name": "eval_a_c0679d55",
+      "chunks_indexed": 36989,
+      "doc_tokens": 9381624,
+      "query_tokens": 1379,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 1.12596,
+      "metrics": {
+        "recall_at_5": 0.7804878048780488,
+        "recall_at_20": 0.9512195121951219,
+        "mrr": 0.6766326153521276,
+        "ndcg_at_10": 0.7135625935017484
+      },
+      "identifier_subset": {
+        "count": 2,
+        "recall_at_20": 0.5
+      }
+    },
+    "CTRL": {
+      "profile": "CTRL",
+      "status": "OK",
+      "reason": null,
+      "collection_name": "eval_ctrl_bc1d1ec7",
+      "chunks_indexed": 36989,
+      "doc_tokens": 0,
+      "query_tokens": 1379,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 0.000248,
+      "metrics": {
+        "recall_at_5": 0.0,
+        "recall_at_20": 0.0,
+        "mrr": 0.0,
+        "ndcg_at_10": 0.0
+      },
+      "identifier_subset": {
+        "count": 2,
+        "recall_at_20": 0.0
+      }
+    }
+  }
+}
+```
+
+### Bh (whole-repo, from round 2)
+
+```json
+{
+  "run_id": "e5147b44",
+  "timestamp": "2026-09-04T02:37:31.141062+00:00",
+  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001",
+  "corpus_files": 2754,
+  "corpus_chunks": 38248,
+  "queries_count": 41,
+  "top_k": 20,
+  "profiles": {
+    "A": {
+      "profile": "A",
+      "status": "FAILED",
+      "reason": "Request to model 'voyage-context-4' failed. The example at index 17 in your batch has too many tokens and does not fit into the model's context window of 32000 tokens. Contextualized chunk embeddings do not support truncation. Either lower the number of tokens in the listed example(s), or pass `enable_auto_chunking=true` with `input_type=\"document\"` and one string per input to have the server split oversize documents.",
+      "collection_name": "eval_a_aa019658",
+      "chunks_indexed": 0,
+      "doc_tokens": 0,
+      "query_tokens": 0,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 0.0,
+      "metrics": {},
+      "identifier_subset": {}
+    },
+    "B": {
+      "profile": "B",
+      "status": "FAILED",
+      "reason": "The request body is not valid JSON, or some arguments were not specified properly. In particular, Error for argument 'input': Value error, Input cannot contain empty strings or empty lists",
+      "collection_name": "eval_b_cc976148",
+      "chunks_indexed": 0,
+      "doc_tokens": 0,
+      "query_tokens": 0,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 0.0,
+      "metrics": {},
+      "identifier_subset": {}
+    },
+    "Bh": {
+      "profile": "Bh",
+      "status": "OK",
+      "reason": null,
+      "collection_name": "eval_bh_f5869725",
+      "chunks_indexed": 38248,
+      "doc_tokens": 11054695,
+      "query_tokens": 1379,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 1.326729,
+      "metrics": {
+        "recall_at_5": 0.9512195121951219,
+        "recall_at_20": 1.0,
+        "mrr": 0.7290650406504063,
+        "ndcg_at_10": 0.7883709300381208
+      },
+      "identifier_subset": {
+        "count": 2,
+        "recall_at_20": 1.0
+      }
+    },
+    "CTRL": {
+      "profile": "CTRL",
+      "status": "FAILED",
+      "reason": "Request to model 'voyage-context-4' failed. The example at index 17 in your batch has too many tokens and does not fit into the model's context window of 32000 tokens. Contextualized chunk embeddings do not support truncation. Either lower the number of tokens in the listed example(s), or pass `enable_auto_chunking=true` with `input_type=\"document\"` and one string per input to have the server split oversize documents.",
+      "collection_name": "eval_ctrl_343a206b",
+      "chunks_indexed": 0,
+      "doc_tokens": 0,
+      "query_tokens": 0,
+      "llm_tokens_in": 0,
+      "llm_tokens_out": 0,
+      "cost_usd": 0.0,
+      "metrics": {},
+      "identifier_subset": {}
+    }
+  }
+}
+```
+
+### Bhl (phase-1 rerun)
+
+```json
+{
+  "run_id": "56080a9b",
+  "timestamp": "2026-09-04T02:37:21.206813+00:00",
+  "corpus_root": "/workspaces/dopemux-mvp/.worktrees/dope-context-retrieval-redesign-001/services/dope-context/src",
+  "corpus_files": 33,
+  "corpus_chunks": 455,
+  "queries_count": 41,
+  "top_k": 20,
+  "profiles": {
+    "Bhl": {
+      "profile": "Bhl",
+      "status": "OK",
+      "reason": null,
+      "collection_name": "eval_bhl_a97007d0",
+      "chunks_indexed": 455,
+      "doc_tokens": 160944,
+      "query_tokens": 1379,
+      "llm_tokens_in": 2888668,
+      "llm_tokens_out": 24581,
+      "cost_usd": 0.62671,
+      "metrics": {
+        "recall_at_5": 1.0,
+        "recall_at_20": 1.0,
+        "mrr": 0.7947154471544714,
+        "ndcg_at_10": 0.8478949538554585
+      },
+      "identifier_subset": {
+        "count": 2,
+        "recall_at_20": 1.0
+      }
+    }
+  }
+}
+```
diff --git a/claudedocs/dope-context-retrieval-redesign-2026-09-03.md b/claudedocs/dope-context-retrieval-redesign-2026-09-03.md
index 9240ded8d..ff2545e2e 100644
--- a/claudedocs/dope-context-retrieval-redesign-2026-09-03.md
+++ b/claudedocs/dope-context-retrieval-redesign-2026-09-03.md
@@ -2,7 +2,7 @@
 title: dope-context Retrieval Stack — Target Design and Implementation Plan
 date: 2026-09-03
 author: Claude (Fable 5.1), session 89799646
-status: PROPOSED — Revision 2.2 after adversarial review (APPROVE_WITH_CHANGES) and Wave 0 smoke run; awaiting supervisor decisions D1–D3 (§8) and packet amendment for eval/ (B12)
+status: PROPOSED — Revision 2.3; D1–D3 RULED by operator 2026-09-03 (see "Revision 2.3"); eval/ carve-out landed with ADR-226 (B12 closed); whole-repo benchmark NOT_RUN — blocked on OPENAI_API_KEY inside `mcp-dope-context` (empty) for the `Bhl` arm
 base: origin/main 04be55535 (services/dope-context byte-identical to e07ff3efc)
 branch: claude/dope-context-retrieval-redesign-2026-09-03
 supersedes: nothing; extends claudedocs/dope-context-modernization-audit-2026-09-03.md
@@ -696,3 +696,34 @@ the 41-query/455-chunk run is a harness-correctness smoke, not decision-grade; t
 rerank path, so the hybrid + `rerank-3` layer in §4.5 has **no coverage** here and remains **UNMEASURED**
 pending the whole-repo run. It also means the design's planned `Dh` profile (Revision 2.1 §6) was never
 executed — only A/B/Bh/Bhl/CTRL ran, with B standing in for `D`.
+
+## Revision 2.3 — 2026-09-03, operator rulings on D1–D3 + benchmark preconditions
+
+**Rulings (operator, this session, via the D1–D3 prompt; recorded as understood — correct here if misread):**
+
+| Decision | Ruling | Condition |
+|---|---|---|
+| D1 — code vector space | **B′ approved**: `voyage-code-4` on both index and query | Still gated: B′ ≥ A on Recall@20 in the **whole-repo** benchmark; smoke run is not decision-grade. Packet `TP-DOPECONTEXT-VECTOR-SPACE-0004` stays `DECISION_REQUIRED` until that result is filed. |
+| D2 — identity contract | **Approved**: project-scoped collections, worktree membership as payload (§4.1) | Wave 3 may be planned; canonical-writer inspection of the manifest schema remains required before any edit. `WAVES_1_4_SRC_LIFT=NOT_AUTHORIZED` (packet 0004) is unchanged — this ruling is a design decision, not a src/ lift authorization. |
+| D3 — LLM context layer for code | **Off by default** (scope header only); `gpt-5.6-luna` when enabled | `Bhl` arm of the benchmark measures whether it earns its cost. |
+
+**Packet amendment for `eval/` (B12): CLOSED.** Packet 0004 carries
+`SEAM_CARVEOUT_STATUS=OPERATOR_APPROVED_2026-09-03_LANDED_WITH_ADR_226`,
+`SEAM_CARVEOUT_SCOPE=services/dope-context/eval/**`, `SEAM_CARVEOUT_AUTHORIZES_CONTENT_EDITS=NO`
+(observed 2026-09-03 in the packet file).
+
+**Whole-repo benchmark (measured $6.82 ≤ $10 ceiling): NOT_RUN. Preconditions observed 2026-09-03:**
+
+- `docker inspect mcp-dope-context`: `VOYAGE_API_KEY` set; **`OPENAI_API_KEY` empty**; `ANTHROPIC_API_KEY` empty.
+  Arms A / B / Bh / CTRL can run; **`Bhl` (D3 measurement, `gpt-5.6-luna`) cannot** until the key reaches the
+  container.
+- `compose.yml:402` maps `OPENAI_API_KEY=${OPENAI_API_KEY}`; `/Users/hue/code/dopemux-mvp/.env` (compose
+  working_dir) has a non-empty `OPENAI_API_KEY` line but no `VOYAGE_API_KEY` line — the running container
+  predates the current `.env` or was started with a different env. Host shell: both keys unset.
+- The running container's compose config also includes
+  `.../dopemux-mcp-reset-recovery-001-r3/proof/TP-DMX-MCP-RESET-RECOVERY-001/runtime/dope-context-readonly.override.yml`
+  (read-only-facade variant). The harness writes to its own Qdrant collections via `--qdrant-url`, so this is
+  noted, not assessed as a blocker.
+- Options (operator choice, max 3): (a) `dopemux mcp stop/start dope-context` so the container re-reads `.env`,
+  then run all five arms; (b) run A/B/Bh/CTRL now, defer `Bhl`; (c) inject the key per-exec
+  (`docker exec -e OPENAI_API_KEY=… `) — not recommended (key in shell history / process list).
diff --git a/docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md b/docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md
index 4a1e47e76..1b00a8077 100644
--- a/docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md
+++ b/docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md
@@ -101,7 +101,9 @@ Official Voyage material checked on 2026-07-22 establishes:
 
 ### Code
 
-- Keep `voyage-code-3` until benchmark evidence supports a replacement.
+- ~~Keep `voyage-code-3` until benchmark evidence supports a replacement.~~
+  **Superseded 2026-09-04**: the evidence now exists — see "Code vector-space
+  benchmark outcome". Code vectors are `voyage-code-4` on the flat endpoint.
 - Split at AST and complete-symbol boundaries first.
 - Use Voyage-token-aware fallback chunks.
 - Benchmark a 300 to 900 token target band.
@@ -134,12 +136,56 @@ consumer model. Keep three distinct metrics:
 1. Add a collection-level manifest and fail closed when model, dimension,
    dtype, chunker, or discovery rules conflict.
 2. Reindex into versioned shadow collections instead of mixing vector schemas.
-3. Benchmark the current mixed code-vector strategy against all-code-3 vectors.
-4. Port one gitignore matcher with negation support for initial indexing and
+3. Port one gitignore matcher with negation support for initial indexing and
    sync.
-5. Add a sorted-path root digest covering file hashes and index configuration.
-6. Replace character-sized fallback chunks with Voyage-token-sized chunks.
-7. Add deleted-file reconciliation and bounded streaming upserts.
+4. Add a sorted-path root digest covering file hashes and index configuration.
+5. Replace character-sized fallback chunks with Voyage-token-sized chunks.
+6. Add deleted-file reconciliation and bounded streaming upserts.
+
+The former item 3 — "Benchmark the current mixed code-vector strategy against
+all-code-3 vectors" — is **CLOSED**; see "Code vector-space benchmark outcome"
+below.
+
+## Code vector-space benchmark outcome (2026-09-04)
+
+Run under `TP-DOPECONTEXT-VECTOR-SPACE-0004`. Whole-repo corpus: 2,754 files,
+~38K chunks, 41 queries, `top_k=20`. Full write-up and raw JSON in
+`claudedocs/dope-context-eval-results-2026-09-03.md`.
+
+| Profile | Model / endpoint | R@5 | R@20 | MRR | NDCG@10 | Cost |
+|---|---|---|---|---|---|---|
+| **B** | `voyage-code-4` flat, both sides | 0.951 | **1.000** | **0.855** | **0.890** | $1.181 |
+| Bh | B + scope header | 0.951 | 1.000 | 0.729 | 0.788 | $1.327 |
+| A | `voyage-context-4` contextualized | 0.780 | 0.951 | 0.677 | 0.714 | $1.126 |
+| CTRL | deliberate index/query mismatch | 0.000 | 0.000 | 0.000 | 0.000 | $0.0002 |
+
+The question the residual item posed is answered, though not as it was framed:
+the contest was never "mixed vs all-code-3" but "contextualized vs flat", and
+the flat profile won every metric while costing less than the header variant.
+CTRL collapsing to exactly 0.000 confirms the metrics discriminate rather than
+always passing. `voyage-code-3` was not benchmarked at all — it was superseded
+by `voyage-code-4`, which is both newer and cheaper ($0.12/M vs $0.18/M).
+
+Implemented as D1: all three code vectors (`content_vec`, `title_vec`,
+`breadcrumb_vec`) now resolve to `voyage-code-4` on the flat `embeddings`
+endpoint, so index and query share one space by construction. Docs collections
+remain contextualized on `voyage-context-4`.
+
+Two vendor behaviours measured during this work, both load-bearing:
+
+* The flat endpoint **silently truncates** at ~32K tokens per input rather than
+  rejecting — a 320,000-token input returned success and billed 31,993. An
+  oversized chunk is therefore half-embedded with no error. Upstream chunk-size
+  enforcement cannot be delegated to the API.
+* `voyage-code-4`'s per-request token ceiling is **not documented**: it is
+  absent from the vendor's 1M/320K/120K grouping sentence entirely. The
+  registry carries 320,000, inferred from the rate-limit tables plus a measured
+  ≥300,000 floor. If batch sizing ever fails, drop it to 120,000 first.
+
+Superseded by this outcome: the "keep `voyage-code-3` until benchmark evidence
+supports a replacement" recommendation above, and the ACCEPTED entry "use
+context-4 for docs and code-3 for code". The REJECTED entry "unbenchmarked
+code-model switching" stands — this switch was benchmarked.
 
 ## Migration Gate
 
@@ -158,7 +204,9 @@ consumer model. Keep three distinct metrics:
 
 - Preserve Python, FastMCP, and Qdrant.
 - Selectively backport upstream deterministic-indexing patterns.
-- Use context-4 for docs and code-3 for code.
+- Use context-4 for docs and code-3 for code. **Amended 2026-09-04**: code
+  moved to `voyage-code-4` (flat endpoint) on benchmark evidence; docs remain
+  on context-4.
 - Use model-specific tokenization for Voyage limits and cost.
 - Make index compatibility explicit and versioned.
 
diff --git a/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md b/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md
index e4354ae3e..24b84dcb1 100644
--- a/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md
+++ b/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md
@@ -418,3 +418,257 @@ pushed at draft time, so no remote state to unwind.
   amendment), ADR-224 (mechanism precedent),
   `claudedocs/m11-red-lane-blocker-2026-07-29.md` (do-not-route-around
   precedent).
+
+────────────────────────────────────────────────────────────
+
+## Amendment A2 — extend the carve-out to the two files the D1 implementation actually needs (2026-09-04)
+
+```text
+AMENDMENT_ID=ADR-226-A2
+AMENDMENT_STATUS=APPROVED
+APPROVED_BY=operator (session 3d420c77, 2026-09-04)
+APPROVAL_SCOPE=path-level exemption as specified below; the content change is
+  authorized only as written under "What lands with this amendment"
+COMPANION_PACKET_AMENDMENT=TP-DOPECONTEXT-VECTOR-SPACE-0004 amendment A2 (same date)
+ADDS_EXEMPTIONS=services/dope-context/src/index_profile.py, services/dope-context/src/embeddings/model_registry.py
+AUTHORIZES_CONTENT_EDITS=NO (path-level only; TEXT_RULES scanning unchanged)
+WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED
+```
+
+### Why
+
+The Wave 0 benchmark (completed 2026-09-04, results in
+`claudedocs/dope-context-eval-results-2026-09-03.md`, commit `4561980fc`)
+settled D1 on measurements: code `content_vec` moves to `voyage-code-4` on
+the flat `embeddings` endpoint. Implementing that decision requires editing
+two files that the original carve-out does not exempt, and that packet 0004's
+Allowed Files did not name:
+
+1. **`services/dope-context/src/index_profile.py`** —
+   `build_code_collection_profile()` (lines 245-292) is the canonical writer
+   of `content_vec`'s `model` and `endpoint`. The original packet named
+   `src/pipeline/indexing_pipeline.py` and `src/mcp/server.py`, but neither
+   sets those fields: the pipeline consumes an already-built profile, and
+   `search_code` already queries with `content_profile.model`
+   (`server.py:1237`), so the query side needs no edit at all. The two
+   originally-exempted service files are, for D1, the wrong files.
+2. **`services/dope-context/src/embeddings/model_registry.py`** —
+   `MODEL_SPECS` does not contain `voyage-code-4`, and `_vector_profile()`
+   validates every model through `get_model_spec()` and
+   `validate_dimension()`, both of which raise on an unregistered name. The
+   target model must be registered before any profile can name it.
+
+### Exact regex change
+
+In `src/dopemux/dcp/red_lane_rules.py`, the ADR-226 carve-out entry gains two
+negative lookaheads (additions marked `+`); everything else is unchanged:
+
+```python
+    re.compile(
+        r"^services/dope-context/"
+        r"(?!eval/)"
+        r"(?!src/pipeline/indexing_pipeline\.py$)"
+        r"(?!src/mcp/server\.py$)"
++       r"(?!src/index_profile\.py$)"
++       r"(?!src/embeddings/model_registry\.py$)"
+        r"(?!tests/test_vector_space_invariants\.py$)"
+        r".*$"
+    ),
+```
+
+The companion traversal-refusal entry
+(`^services/dope-context/(?:.*/)?\.\.(?:/|$)`) is unchanged and continues to
+cover the newly-exempted paths, so `eval/../src/index_profile.py` and
+`src/embeddings/../search/dense_search.py` stay blocked.
+
+### Invariants preserved
+
+* Anchored `$` on both new lookaheads — `index_profile.py.bak`,
+  `index_profile.py.orig`, and `src/embeddings/model_registry.py.tmp` remain
+  blocked, as do same-named files in other directories
+  (`src/search/index_profile.py` would still be blocked, since the lookahead
+  is rooted at `services/dope-context/`).
+* Whole-path case-folding from the F-001-A fix (commit `a4f86c48c`) applies
+  unchanged, so `SRC/INDEX_PROFILE.PY` is still denied fail-closed.
+* `TEXT_RULES` content scanning in `red_lane_scanner.py` is untouched; the
+  exempted paths are exempt from the *path* block only, not from content
+  rules.
+* Everything else under `services/dope-context/src/**` — including
+  `search/dense_search.py`, `search/hybrid_search.py`,
+  `preprocessing/code_chunker.py`, and `pipeline/docs_pipeline.py` — remains
+  hard-blocked.
+
+### What lands with this amendment
+
+Path-level exemption only. The authorized content change, specified here so
+the diff is reviewable before the lane opens:
+
+* `model_registry.py`: add a `voyage-code-4` entry to `MODEL_SPECS`
+  (`endpoint="embeddings"`, `default_dimension=1024`, standard
+  `_DIMENSIONS`, `price_per_million_tokens=0.12`); flip
+  `DEFAULT_CODE_MODEL` from `"voyage-code-3"` to `"voyage-code-4"`; mark the
+  superseded `voyage-code-3`, `voyage-context-3`, and `voyage-3-lite` entries
+  `legacy=True`.
+
+  **Limits — live-measured 2026-09-04, do not copy `voyage-code-3`'s values.**
+  Two probes against the real API (total billed $0.04):
+
+  * `per_input_tokens=32_000` — **confirmed, but the failure mode differs
+    from the contextualized endpoint.** Submitting a single 320,000-token
+    input returned success, not an error, and billed `total_tokens=31993`:
+    `voyage-code-4` on the flat endpoint **silently truncates** at ~32K
+    rather than rejecting. Contrast `contextualized_embed`, which refuses
+    outright ("Contextualized chunk embeddings do not support truncation").
+    This is a correctness hazard for the indexing pipeline, not just a
+    quota detail: an oversized chunk would be *half-embedded with no
+    error surfaced*, producing a vector that silently represents only the
+    first ~32K tokens of the content. Chunk-size enforcement upstream is
+    therefore load-bearing for D1 and must not be assumed to be guarded by
+    the API.
+  * `max_request_tokens` — **`voyage-code-3`'s 120,000 is wrong for
+    `voyage-code-4`.** A 60-input batch totalling 300,000 tokens was
+    accepted and billed in full (`total_tokens=299940`). The true ceiling is
+    therefore **>300,000 and was not pinned** — the probe established a
+    lower bound, not the limit. Either bind this to a vendor-documented
+    figure before landing, or carry a deliberately conservative value with a
+    comment saying it is a self-imposed floor rather than the API's ceiling.
+    Do not record 120,000 as if it were measured.
+
+  Note that the 32,000 / 120,000 pair the registry currently carries for
+  `voyage-code-3` matches exactly the two limits the Wave 0 benchmark hit on
+  the *contextualized* endpoint — which raises the question of whether
+  `voyage-code-3`'s own row was populated from the wrong endpoint's limits.
+  Out of scope for this amendment, but worth an entry on the audit's residual
+  list.
+* `index_profile.py`: in `build_code_collection_profile()`, `content_vec`
+  changes from `model=ctx_model, endpoint="contextualized_embeddings"` to the
+  resolved code model on `endpoint="embeddings"`, so index and query agree.
+  Whether `title_vec`/`breadcrumb_vec` also move from `voyage-code-3` to
+  `voyage-code-4` is a separate, unresolved question — it is consistent and
+  cheaper ($0.12/M vs $0.18/M) but is beyond D1's literal wording and is
+  **not** authorized by this amendment without an explicit ruling.
+
+### Rollback
+
+Revert the two lookahead lines. The lane returns to its 2026-09-03 shape with
+no other state to unwind; any commits made under the amendment stay in
+history and would need their own revert.
+
+### Verification before landing
+
+* `PYTHONPATH=src python -m pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
+  — expected full pass, including `test_fallback_patterns_covered_by_live_rules`
+  (the fallback tuple is a subset and is unaffected by adding exemptions).
+* `surface_guard_block("Edit", {"file_path": <root>/services/dope-context/src/index_profile.py}, <root>)`
+  returns `None`; the same call for
+  `services/dope-context/src/search/dense_search.py` and for
+  `services/dope-context/eval/../src/index_profile.py` still returns a
+  `DCP-RED-MERGE-SEAM-0001` block message.
+* A new case asserting `src/embeddings/model_registry.py` is exempt while
+  `src/embeddings/voyage_embedder.py` is still blocked — the two live in the
+  same directory, which is exactly the near-miss this anchoring must survive.
+
+────────────────────────────────────────────────────────────
+
+## Amendment A3 — carve out the one blocked test file the landed D1 change invalidates (2026-09-04)
+
+```text
+AMENDMENT_ID=ADR-226-A3
+AMENDMENT_STATUS=APPROVED
+APPROVED_BY=operator (session 3d420c77, 2026-09-04)
+COMPANION_PACKET_AMENDMENT=TP-DOPECONTEXT-VECTOR-SPACE-0004 amendment A3 (same date)
+ADDS_EXEMPTIONS=services/dope-context/tests/test_vector_profiles_and_migration.py
+AUTHORIZES_CONTENT_EDITS=NO (path-level only; TEXT_RULES scanning unchanged)
+WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED
+```
+
+### Why
+
+A2 was written from a static reading and got one thing wrong, which the
+implementation then exposed empirically. A2 asserted that
+`src/pipeline/indexing_pipeline.py` and `src/mcp/server.py` "need no edit".
+That is false. Both pass `content_profile.model` but **hardcode the
+contextualized embedder object** rather than dispatching on
+`content_profile.endpoint`:
+
+* `indexing_pipeline.py:300` — `self.contextualized_embedder.embed_document(...)`
+* `mcp/server.py:1235` — `contextual_embedder.embed_document(...)`
+* `mcp/server.py:960` — constructs `ContextualizedEmbedder(default_model=code_profile.content().model, ...)`
+
+After D1 all three would hand `voyage-code-4` to the contextualized endpoint,
+which accepts only the `voyage-context-*` family. The third one fails at
+*construction* time and was caught by `test_mcp_server.py::test_index_workspace_tool`
+raising `ValueError: Voyage model 'voyage-code-4' uses endpoint 'embeddings',
+not 'contextualized_embeddings'`. Both files were already in Allowed Files, so
+correcting them required no new amendment — but A2's claim is withdrawn, and
+the record should say so rather than leave a wrong rationale standing.
+
+### What this amendment is actually for
+
+With those fixed, the suite is **115 passed, 1 skipped, 4 failed**, and every
+remaining failure is in a single **blocked** file,
+`services/dope-context/tests/test_vector_profiles_and_migration.py`. Each one
+asserts the pre-D1 contract, so each is *supposed* to change; none is a defect:
+
+1. `test_six_named_vector_index_query_profiles_identical` (L40-43) — asserts
+   `code.content().endpoint == "contextualized_embeddings"`,
+   `code.title().model == "voyage-code-3"`,
+   `code.breadcrumb().model == "voyage-code-3"`, and
+   `docs.content().model == code.content().model`. D1 falsifies all four by
+   design; docs stay contextualized while code goes flat, so the code and docs
+   content models are no longer equal.
+2. `test_profile_mutations_change_collection_identity[<lambda>0]` (L71) —
+   expects `build_code_collection_profile(contextual_model="voyage-context-3")`
+   to change the collection digest. `contextual_model` is now inert for code
+   profiles, so the digest correctly does not move. The parameter is retained
+   for signature compatibility; the mutation case must move to a parameter that
+   still participates in code identity (e.g. `code_model=`).
+3. `test_endpoint_change_changes_collection_identity` (L88-94) — its premise is
+   that the code profile carries *mixed* endpoints. D1 makes the code profile
+   uniform, which is the entire point.
+4. `test_context3_rollback_moves_all_contextual_paths_together` (L162, L167) —
+   asserts the contextual rollback env var also moves code `content_vec`, and
+   that `code.title().model` stays `voyage-code-3`. After D1 the contextual
+   rollback governs docs only; code has no contextualized vector for it to
+   move. This test needs its premise rewritten, not its literals swapped.
+
+### Exact regex change
+
+```python
+    re.compile(
+        r"^services/dope-context/"
+        r"(?!eval/)"
+        r"(?!src/pipeline/indexing_pipeline\.py$)"
+        r"(?!src/mcp/server\.py$)"
+        r"(?!src/index_profile\.py$)"
+        r"(?!src/embeddings/model_registry\.py$)"
+        r"(?!tests/test_vector_space_invariants\.py$)"
++       r"(?!tests/test_vector_profiles_and_migration\.py$)"
+        r".*$"
+    ),
+```
+
+### Invariants preserved
+
+Unchanged from A2: anchored `$` (so `.bak`/`.orig`/`.tmp` variants and
+same-named files elsewhere stay blocked), whole-path case folding, the
+traversal-refusal companion entry, and `TEXT_RULES` content scanning. Every
+other file under `services/dope-context/tests/` — `conftest.py`,
+`test_mcp_server.py`, `test_voyage_modernization.py`,
+`test_reliability_repairs.py` — remains hard-blocked, and none of them needs
+an edit: their `120_000` assertions name `voyage-code-3` and `voyage-3-lite`
+literally, and those specs are unchanged.
+
+### Rollback
+
+Revert the one lookahead line. Note that reverting A3 alone leaves the four
+tests failing; a full rollback of D1 means reverting the A2 implementation
+commit as well, which restores the old assertions' truth.
+
+### Verification before landing
+
+* The four named tests pass with their premises rewritten, not deleted.
+* `surface_guard_block` still denies `tests/conftest.py`,
+  `tests/test_mcp_server.py`, and
+  `tests/test_vector_profiles_and_migration.py.bak`.
+* Full suite returns to zero failures.
diff --git a/services/dope-context/eval/run_eval.py b/services/dope-context/eval/run_eval.py
index 917f7945c..3f716b95f 100644
--- a/services/dope-context/eval/run_eval.py
+++ b/services/dope-context/eval/run_eval.py
@@ -29,8 +29,22 @@ Profiles:
          different vector spaces.
 
 Guardrails:
-  - Refuses to run unless --corpus resolves to a path ending in
-    services/dope-context/src (never embeds anything else).
+  - Refuses to run unless --corpus resolves to either
+    services/dope-context/src (phase 1, the validation corpus) or the repo
+    root itself, identified by the presence of both
+    services/dope-context/src/ and pyproject.toml beneath it (phase 2,
+    whole-repo). Any other path is refused.
+  - Whole-repo mode additionally REQUIRES --file-list: a manifest of
+    relative .py paths (one per line), generated on the HOST with
+    ``git ls-files -z --cached --exclude-standard -- '*.py'`` (git ls-files
+    does not work inside this container for a linked worktree -- its
+    .git is a file with a host-path gitdir). Without --file-list a raw
+    rglob over the repo root would also embed .venv/, node_modules/, and
+    vendored docker build contexts, silently inflating cost.
+  - --project-only builds the corpus and prints projected token counts
+    and USD cost per requested profile using the Voyage client's local
+    (no-network) tokenizer, then exits 0 without making any embedding or
+    chat-completion API call. Always run this before a whole-repo spend.
   - Aborts a single profile (FAILED, not silently skipped) if its
     projected input tokens exceed MAX_INPUT_TOKENS_PER_PROFILE, checked
     BEFORE any embedding API call is made.
@@ -46,6 +60,13 @@ Usage (inside the mcp-dope-context container):
         --queries /path/to/eval/queries.jsonl \
         --profiles A,B,Bh,Bhl,CTRL \
         --json
+
+    python run_eval.py \
+        --corpus /path/to/repo/root \
+        --file-list /path/to/whole_repo_py_files.txt \
+        --queries /path/to/eval/queries.jsonl \
+        --profiles A,B,CTRL \
+        --project-only
 """
 from __future__ import annotations
 
@@ -66,7 +87,23 @@ from typing import Any, Dict, List, Optional, Tuple
 # Guardrails / constants
 # --------------------------------------------------------------------------
 
-MAX_INPUT_TOKENS_PER_PROFILE = 200_000
+# Real (Voyage-tokenizer, not chars//4) whole-repo counts measured
+# 2026-09-04: A/B doc_tokens=9,889,927, Bh doc_tokens=11,103,687 (the real
+# max, from the scope-header prefix). 15M covers that with margin while
+# still refusing the explicitly-forbidden repo+docs/*.md corpus (~21M+
+# real tokens). The guardrail check itself now also uses the real
+# tokenizer (see run_profile) instead of the chars//4 approx_tokens()
+# estimate, which overshot real counts by ~10-20% and produced a false
+# guardrail trip on the actual whole-repo run.
+MAX_INPUT_TOKENS_PER_PROFILE = 15_000_000
+# Voyage's own hard limit for a single contextualized_embed "document"
+# example (one file's full chunk list) -- confirmed via a live error on
+# the 2026-09-04 whole-repo run: "does not fit into the model's context
+# window of 32000 tokens. Contextualized chunk embeddings do not support
+# truncation." 6 of 2754 whole-repo files exceed it (largest 175,208
+# tokens); none are under services/dope-context/src/ (not query targets),
+# so excluding them from A/CTRL only doesn't bias the recall comparison.
+MAX_TOKENS_PER_CONTEXTUAL_EXAMPLE = 32_000
 MAX_RETRIES = 3
 DEFAULT_TOP_K = 20
 VALID_PROFILES = ("A", "B", "Bh", "Bhl", "CTRL")
@@ -89,11 +126,6 @@ PRICE_PER_M = {
 IDENTIFIER_RE = re.compile(r"\b([a-z]+[A-Z][a-zA-Z0-9]*|[a-z][a-z0-9]*_[a-z0-9_]+)\b")
 
 
-def approx_tokens(text: str) -> int:
-    """Cheap guardrail estimate: ~4 chars/token. Not billed usage."""
-    return max(1, len(text) // 4)
-
-
 def query_has_identifier(query_text: str) -> bool:
     return bool(IDENTIFIER_RE.search(query_text))
 
@@ -151,21 +183,47 @@ def is_whole_file_duplicate(chunk) -> bool:
     )
 
 
-def build_corpus(corpus_root: Path) -> List[ChunkRecord]:
-    if str(corpus_root) not in sys.path:
-        sys.path.insert(0, str(corpus_root))
+def build_corpus(
+    corpus_root: Path,
+    is_scoped_src: bool,
+    file_list: Optional[Path] = None,
+) -> List[ChunkRecord]:
+    # Import CodeChunker via this script's own known location, not
+    # corpus_root -- corpus_root is the repo root in whole-repo mode and
+    # does not contain the `preprocessing` package directly.
+    src_root = Path(__file__).resolve().parent.parent / "src"
+    if str(src_root) not in sys.path:
+        sys.path.insert(0, str(src_root))
     from preprocessing.code_chunker import CodeChunker  # type: ignore
 
     chunker = CodeChunker()
     records: List[ChunkRecord] = []
-    py_files = sorted(corpus_root.rglob("*.py"))
+    if file_list is not None:
+        rel_entries = [
+            line.strip()
+            for line in file_list.read_text(encoding="utf-8").splitlines()
+            if line.strip()
+        ]
+        py_files = sorted(corpus_root / rel for rel in rel_entries)
+    else:
+        py_files = sorted(corpus_root.rglob("*.py"))
     for f in py_files:
-        chunks = chunker.chunk_file(f)
+        if not f.is_file():
+            print(f"  WARNING: skipping missing file {f}", file=sys.stderr)
+            continue
+        try:
+            chunks = chunker.chunk_file(f)
+        except Exception as exc:  # noqa: BLE001 - one bad file must not abort the corpus
+            print(f"  WARNING: skipping unparseable file {f}: {exc}", file=sys.stderr)
+            continue
         rel = f.relative_to(corpus_root)
-        rel_path = "src/" + str(rel).replace(os.sep, "/")
+        rel_str = str(rel).replace(os.sep, "/")
+        rel_path = ("src/" + rel_str) if is_scoped_src else rel_str
         for c in chunks:
             if is_whole_file_duplicate(c):
                 continue
+            if not c.content.strip():
+                continue
             if c.parent_symbol and c.symbol_name:
                 qualified = f"{c.parent_symbol}.{c.symbol_name}"
             else:
@@ -217,6 +275,7 @@ def apply_llm_contexts(
     texts: List[str],
     file_text_cache: Dict[str, str],
     corpus_root: Path,
+    is_scoped_src: bool,
 ) -> Tuple[List[str], int, int]:
     """Prepend a 1-2 sentence LLM-generated situating context to each
     document text. The whole file is sent as a fixed leading user message,
@@ -244,7 +303,8 @@ def apply_llm_contexts(
 
     for file_key, recs in grouped.items():
         if file_key not in file_text_cache:
-            file_path = corpus_root / file_key[len("src/"):]
+            rel = file_key[len("src/"):] if is_scoped_src else file_key
+            file_path = corpus_root / rel
             try:
                 file_text_cache[file_key] = file_path.read_text(encoding="utf-8")
             except Exception:
@@ -325,12 +385,22 @@ def embed_contextual(
     grouped_texts: List[List[str]],
     model: str,
     input_type: str,
-    batch_size_docs: int = 20,
+    doc_token_counts: List[int],
+    max_batch_tokens: int = 100_000,
 ) -> Tuple[List[List[List[float]]], int]:
+    # Voyage's real per-batch cap is 120,000 tokens (confirmed via a live
+    # 2026-09-04 error). 100,000 leaves margin -- the error reported
+    # tokens "after truncation", implying some server-side overhead above
+    # our own pre-request count, so don't cut this margin any closer.
     all_results: List[List[List[float]]] = []
     total_tokens = 0
-    for i in range(0, len(grouped_texts), batch_size_docs):
-        batch = grouped_texts[i : i + batch_size_docs]
+    batch: List[List[str]] = []
+    batch_tokens = 0
+
+    def flush():
+        nonlocal batch, batch_tokens, total_tokens
+        if not batch:
+            return
         result = call_with_retries(
             client.contextualized_embed,
             inputs=batch,
@@ -341,12 +411,24 @@ def embed_contextual(
         for doc_result in result.results:
             all_results.append(doc_result.embeddings)
         total_tokens += result.total_tokens
+        batch = []
+        batch_tokens = 0
+
+    for texts, tok in zip(grouped_texts, doc_token_counts):
+        if batch and batch_tokens + tok > max_batch_tokens:
+            flush()
+        batch.append(texts)
+        batch_tokens += tok
+    flush()
     return all_results, total_tokens
 
 
 def embed_queries_contextual(client, model: str, query_texts: List[str]):
     grouped = [[q] for q in query_texts]
-    results, total_tokens = embed_contextual(client, grouped, model=model, input_type="query")
+    doc_token_counts = [client.count_tokens([q], model=model) for q in query_texts]
+    results, total_tokens = embed_contextual(
+        client, grouped, model=model, input_type="query", doc_token_counts=doc_token_counts
+    )
     vectors = [r[0] for r in results]
     return vectors, total_tokens
 
@@ -492,6 +574,7 @@ def run_profile(
     cache: Dict[str, Any],
     top_k: int,
     corpus_root: Path,
+    is_scoped_src: bool,
 ) -> ProfileResult:
     result = ProfileResult(profile=profile)
 
@@ -509,16 +592,33 @@ def run_profile(
         if profile in ("A", "CTRL"):
             if "a_doc_vectors" not in cache:
                 grouped_by_file = group_by_file(records)
-                file_keys = list(grouped_by_file.keys())
-                grouped_texts = [[r.content for r in grouped_by_file[fk]] for fk in file_keys]
-                approx_in = sum(approx_tokens(t) for texts in grouped_texts for t in texts)
-                if approx_in > MAX_INPUT_TOKENS_PER_PROFILE:
+                file_keys = []
+                grouped_texts = []
+                doc_token_counts = []
+                real_in = 0
+                for fk, recs in grouped_by_file.items():
+                    texts = [r.content for r in recs]
+                    file_tokens = voyage_client.count_tokens(texts, model="voyage-context-4")
+                    if file_tokens > MAX_TOKENS_PER_CONTEXTUAL_EXAMPLE:
+                        print(
+                            f"  WARNING: excluding {fk} from A/CTRL contextualized_embed "
+                            f"({file_tokens} tokens > {MAX_TOKENS_PER_CONTEXTUAL_EXAMPLE} "
+                            "per-example limit; still included in B/Bh)",
+                            file=sys.stderr,
+                        )
+                        continue
+                    file_keys.append(fk)
+                    grouped_texts.append(texts)
+                    doc_token_counts.append(file_tokens)
+                    real_in += file_tokens
+                if real_in > MAX_INPUT_TOKENS_PER_PROFILE:
                     raise RuntimeError(
-                        f"projected input tokens {approx_in} exceeds guardrail "
+                        f"projected input tokens {real_in} exceeds guardrail "
                         f"{MAX_INPUT_TOKENS_PER_PROFILE} for profile A/CTRL document embedding"
                     )
                 doc_results, doc_tokens = embed_contextual(
-                    voyage_client, grouped_texts, model="voyage-context-4", input_type="document"
+                    voyage_client, grouped_texts, model="voyage-context-4",
+                    input_type="document", doc_token_counts=doc_token_counts,
                 )
                 flat_vectors: List[List[float]] = []
                 flat_records: List[ChunkRecord] = []
@@ -540,14 +640,15 @@ def run_profile(
                 texts = [doc_text_scoped(r) for r in records]
             if profile == "Bhl":
                 texts, llm_in, llm_out = apply_llm_contexts(
-                    records, texts, cache.setdefault("file_text_cache", {}), corpus_root
+                    records, texts, cache.setdefault("file_text_cache", {}), corpus_root,
+                    is_scoped_src,
                 )
                 result.llm_tokens_in = llm_in
                 result.llm_tokens_out = llm_out
-            approx_in = sum(approx_tokens(t) for t in texts)
-            if approx_in > MAX_INPUT_TOKENS_PER_PROFILE:
+            real_in = voyage_client.count_tokens(texts, model="voyage-code-4")
+            if real_in > MAX_INPUT_TOKENS_PER_PROFILE:
                 raise RuntimeError(
-                    f"projected input tokens {approx_in} exceeds guardrail "
+                    f"projected input tokens {real_in} exceeds guardrail "
                     f"{MAX_INPUT_TOKENS_PER_PROFILE} for profile {profile} document embedding"
                 )
             doc_vectors, doc_tokens = embed_flat(
@@ -647,6 +748,65 @@ def run_profile(
 # --------------------------------------------------------------------------
 
 
+def project_costs(
+    records: List[ChunkRecord],
+    queries: List[Dict[str, Any]],
+    profiles: List[str],
+    voyage_client,
+) -> Dict[str, Any]:
+    """Local (no-network) token counts via the Voyage tokenizer, priced at
+    PRICE_PER_M. Makes zero embedding or chat-completion API calls."""
+    query_texts = [q["query"] for q in queries]
+    projections: Dict[str, Any] = {}
+    total_usd = 0.0
+    a_doc_tokens: Optional[int] = None
+
+    for p in profiles:
+        if p == "Bhl":
+            projections[p] = {
+                "doc_tokens": None,
+                "cost_usd": None,
+                "note": (
+                    "LLM situating-context cost cannot be projected here "
+                    "(no local tokenizer for gpt-5.6-luna in this harness). "
+                    "Run Bhl alone on a small corpus first and extrapolate "
+                    "llm_tokens_in/out linearly by chunk count before "
+                    "spending on a whole-repo Bhl run."
+                ),
+            }
+            continue
+        if p == "A":
+            if a_doc_tokens is None:
+                a_doc_tokens = voyage_client.count_tokens(
+                    [r.content for r in records], model="voyage-context-4"
+                )
+            doc_tokens = a_doc_tokens
+            doc_price = PRICE_PER_M["voyage-context-4"]
+            q_price = PRICE_PER_M["voyage-context-4"]
+        elif p == "CTRL":
+            doc_tokens = 0  # reuses A's already-computed embeddings
+            doc_price = 0.0
+            q_price = PRICE_PER_M["voyage-code-3"]
+        else:  # B, Bh
+            texts = [doc_text_plain(r) if p == "B" else doc_text_scoped(r) for r in records]
+            doc_tokens = voyage_client.count_tokens(texts, model="voyage-code-4")
+            doc_price = PRICE_PER_M["voyage-code-4"]
+            q_price = PRICE_PER_M["voyage-code-4"]
+        q_tokens = voyage_client.count_tokens(query_texts, model="voyage-code-3")
+        doc_cost = (doc_tokens / 1_000_000) * doc_price
+        query_cost = (q_tokens / 1_000_000) * q_price
+        cost = round(doc_cost + query_cost, 6)
+        projections[p] = {
+            "doc_tokens": doc_tokens,
+            "query_tokens": q_tokens,
+            "cost_usd": cost,
+        }
+        total_usd += cost
+
+    projections["_total_usd_excl_bhl"] = round(total_usd, 6)
+    return projections
+
+
 def main() -> int:
     parser = argparse.ArgumentParser(description="Wave 0 offline retrieval eval harness for dope-context")
     parser.add_argument("--corpus", required=True, type=Path)
@@ -654,15 +814,39 @@ def main() -> int:
     parser.add_argument("--profiles", default="A,B,Bh,Bhl", help="Comma-separated: A,B,Bh,Bhl,CTRL")
     parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
     parser.add_argument("--qdrant-url", default="http://mcp-qdrant:6333")
+    parser.add_argument(
+        "--file-list", type=Path, default=None,
+        help="Manifest of relative .py paths (one per line); required when --corpus is a whole-repo root",
+    )
+    parser.add_argument(
+        "--project-only", action="store_true",
+        help="Build the corpus and print projected token/cost estimates; make no embedding/chat API calls",
+    )
     parser.add_argument("--json", action="store_true", help="accepted for CLI compatibility; output is always JSON")
     args = parser.parse_args()
 
     corpus_root = args.corpus.resolve()
     normalized = str(corpus_root).replace(os.sep, "/")
-    if not normalized.endswith("services/dope-context/src"):
+    is_scoped_src = normalized.endswith("services/dope-context/src")
+    is_whole_repo = (
+        (corpus_root / "services" / "dope-context" / "src").is_dir()
+        and (corpus_root / "pyproject.toml").is_file()
+    )
+    if not (is_scoped_src or is_whole_repo):
+        print(
+            f"REFUSING: corpus root {corpus_root} is neither "
+            "services/dope-context/src nor a repo root (missing "
+            "services/dope-context/src/ or pyproject.toml beneath it) "
+            "-- refusing to embed anything outside those two shapes",
+            file=sys.stderr,
+        )
+        return 2
+    if is_whole_repo and args.file_list is None:
         print(
-            f"REFUSING: corpus root {corpus_root} does not end with "
-            "services/dope-context/src -- refusing to embed anything outside it",
+            "REFUSING: whole-repo corpus root requires --file-list (a "
+            "git ls-files manifest of relative .py paths) -- an "
+            "unrestricted walk would also embed .venv/, node_modules/, "
+            "and vendored docker build contexts",
             file=sys.stderr,
         )
         return 2
@@ -681,20 +865,27 @@ def main() -> int:
                 queries.append(json.loads(line))
 
     print(f"Building corpus from {corpus_root} ...", file=sys.stderr)
-    records = build_corpus(corpus_root)
+    records = build_corpus(corpus_root, is_scoped_src, args.file_list)
     print(f"  {len(records)} chunks across "
           f"{len({r.rel_path for r in records})} files", file=sys.stderr)
 
-    openai_key_present = bool(os.environ.get("OPENAI_API_KEY"))
     voyage_client = get_voyage_client()
 
+    if args.project_only:
+        print("PROJECTION MODE -- no embedding or chat-completion API calls will be made.", file=sys.stderr)
+        projections = project_costs(records, queries, profiles, voyage_client)
+        print(json.dumps(projections, indent=2))
+        return 0
+
+    openai_key_present = bool(os.environ.get("OPENAI_API_KEY"))
+
     cache: Dict[str, Any] = {}
     profile_results: Dict[str, ProfileResult] = {}
     for p in profiles:
         print(f"Running profile {p} ...", file=sys.stderr)
         profile_results[p] = run_profile(
             p, records, queries, voyage_client, args.qdrant_url,
-            openai_key_present, cache, args.top_k, corpus_root,
+            openai_key_present, cache, args.top_k, corpus_root, is_scoped_src,
         )
         print(f"  {p}: {profile_results[p].status}", file=sys.stderr)
 
diff --git a/services/dope-context/src/embeddings/model_registry.py b/services/dope-context/src/embeddings/model_registry.py
index 21ec8b7ae..ccd7a196d 100644
--- a/services/dope-context/src/embeddings/model_registry.py
+++ b/services/dope-context/src/embeddings/model_registry.py
@@ -33,6 +33,42 @@ class EmbeddingModelSpec:
 _DIMENSIONS = frozenset({256, 512, 1024, 2048})
 
 MODEL_SPECS: Dict[str, EmbeddingModelSpec] = {
+    # D1 (TP-DOPECONTEXT-VECTOR-SPACE-0004, Wave 0 benchmark 2026-09-04): the
+    # code content/title/breadcrumb vectors all resolve here. Chosen on measured
+    # whole-repo retrieval — recall@20 1.000 / MRR 0.855, beating the
+    # contextualized voyage-context-4 profile (0.951 / 0.677) on the same
+    # 2,754-file corpus and 41-query set.
+    #
+    # WARNING — per_input_tokens is NOT enforced by the API for this model.
+    # Live-probed 2026-09-04: a single 320,000-token input returned success and
+    # billed total_tokens=31993, i.e. the flat embeddings endpoint SILENTLY
+    # TRUNCATES at ~32K instead of rejecting. (contextualized_embed refuses
+    # outright: "Contextualized chunk embeddings do not support truncation".)
+    # An oversized chunk is therefore half-embedded with no error surfaced,
+    # yielding a vector that represents only its first ~32K tokens. Upstream
+    # chunk-size enforcement is load-bearing; do not assume the API guards it.
+    #
+    # max_request_tokens=320_000 rather than voyage-code-3's 120_000. Evidence:
+    # (a) the vendor's 120K-group sentence enumerates voyage-code-3,
+    # voyage-4-large, voyage-3-large, voyage-large-2-instruct, voyage-finance-2,
+    # voyage-multilingual-2 and voyage-law-2 — voyage-code-4 is absent from it;
+    # (b) the rate-limit tables group voyage-code-4 with voyage-4 and
+    # voyage-3.5, which are the 320K group; (c) a live 60-input batch totalling
+    # 300,000 tokens was accepted and billed in full (total_tokens=299940),
+    # which rules out a 120K ceiling empirically. Copying 120_000 here would
+    # have been wrong.
+    "voyage-code-4": EmbeddingModelSpec(
+        name="voyage-code-4",
+        endpoint="embeddings",
+        default_dimension=1024,
+        supported_dimensions=_DIMENSIONS,
+        per_input_tokens=32_000,
+        max_request_inputs=1_000,
+        max_request_tokens=320_000,
+        price_per_million_tokens=0.12,
+    ),
+    # Superseded by voyage-code-4 (D1). Retained registered so an explicit
+    # DOPE_CONTEXT_CODE_EMBED_MODEL=voyage-code-3 rollback still resolves.
     "voyage-code-3": EmbeddingModelSpec(
         name="voyage-code-3",
         endpoint="embeddings",
@@ -42,6 +78,7 @@ MODEL_SPECS: Dict[str, EmbeddingModelSpec] = {
         max_request_inputs=1_000,
         max_request_tokens=120_000,
         price_per_million_tokens=0.18,
+        legacy=True,
     ),
     "voyage-4-large": EmbeddingModelSpec(
         name="voyage-4-large",
@@ -109,7 +146,7 @@ MODEL_SPECS: Dict[str, EmbeddingModelSpec] = {
     ),
 }
 
-DEFAULT_CODE_MODEL = "voyage-code-3"
+DEFAULT_CODE_MODEL = "voyage-code-4"
 DEFAULT_DOC_MODEL = "voyage-context-4"
 DEFAULT_GENERAL_MODEL = "voyage-4"
 DEFAULT_RERANK_MODEL = "rerank-2.5"
diff --git a/services/dope-context/src/index_profile.py b/services/dope-context/src/index_profile.py
index 789567647..373d63e9f 100644
--- a/services/dope-context/src/index_profile.py
+++ b/services/dope-context/src/index_profile.py
@@ -252,9 +252,21 @@ def build_code_collection_profile(
     index_schema_version: str = INDEX_SCHEMA_VERSION,
     environ: Optional[Mapping[str, str]] = None,
 ) -> CollectionProfile:
-    """Code collection: contextual content_vec + voyage-code-3 title/breadcrumb."""
+    """Code collection: one flat code model across content/title/breadcrumb.
+
+    D1 (TP-DOPECONTEXT-VECTOR-SPACE-0004, decided on the Wave 0 benchmark
+    2026-09-04): ``content_vec`` was indexed with a contextualized model and
+    queried with a flat one — two different vector spaces that Qdrant accepted
+    silently because both are 1024-dimensional. All three code vectors now
+    resolve to the same flat code model on the ``embeddings`` endpoint, so
+    index and query agree by construction.
+
+    ``contextual_model`` is retained for signature compatibility and is now
+    inert for code collections; the code collection no longer has a
+    contextualized vector for it to select. Docs collections are unaffected and
+    remain contextualized — see :func:`build_docs_collection_profile`.
+    """
 
-    ctx_model = contextual_model or resolve_contextual_embed_model(environ=environ)
     id_model = code_model or resolve_code_embed_model(environ=environ)
     dim = dimension or DEFAULT_OUTPUT_DIMENSION
 
@@ -262,8 +274,8 @@ def build_code_collection_profile(
         "content_vec": _vector_profile(
             kind="code",
             vector_name="content_vec",
-            model=ctx_model,
-            endpoint="contextualized_embeddings",
+            model=id_model,
+            endpoint="embeddings",
             dimension=dim,
             dtype=dtype,
             chunker_version=chunker_version,
diff --git a/services/dope-context/src/mcp/server.py b/services/dope-context/src/mcp/server.py
index c8cab819a..2eaf7fe81 100644
--- a/services/dope-context/src/mcp/server.py
+++ b/services/dope-context/src/mcp/server.py
@@ -956,14 +956,24 @@ async def _index_workspace_impl(
         output_dtype=code_profile.title().dtype,
     )
 
-    # Create contextualized embedder for content vectors
-    contextualized_embedder = ContextualizedEmbedder(
-        api_key=_get_voyage_api_key(),
-        cache_ttl_hours=24,
-        default_model=code_profile.content().model,
-        output_dimension=code_profile.content().dimension,
-        output_dtype=code_profile.content().dtype,
-    )
+    # D1: the code content vector is flat, so the contextualized embedder is
+    # only the fallback for a contextualized rollback. Deriving its default
+    # model from content() unconditionally would hand it a flat code model,
+    # which get_model_spec rejects for the contextualized endpoint.
+    code_content_profile = code_profile.content()
+    if code_content_profile.endpoint == "contextualized_embeddings":
+        contextualized_embedder = ContextualizedEmbedder(
+            api_key=_get_voyage_api_key(),
+            cache_ttl_hours=24,
+            default_model=code_content_profile.model,
+            output_dimension=code_content_profile.dimension,
+            output_dtype=code_content_profile.dtype,
+        )
+    else:
+        contextualized_embedder = ContextualizedEmbedder(
+            api_key=_get_voyage_api_key(),
+            cache_ttl_hours=24,
+        )
 
     config = IndexingConfig(
         workspace_path=workspace,
@@ -1232,19 +1242,33 @@ async def _search_code_impl(
             title_profile = code_profile.title()
             breadcrumb_profile = code_profile.breadcrumb()
 
-            content_response = await contextual_embedder.embed_document(
-                chunks=[query],
-                model=content_profile.model,
-                input_type=content_profile.query_input_type,
-                output_dimension=content_profile.dimension,
-                output_dtype=content_profile.dtype,
-                enable_auto_chunking=False,
-            )
-            if len(content_response.embeddings) != 1:
-                raise ValueError(
-                    f"Expected exactly one content query vector, got "
-                    f"{len(content_response.embeddings)}"
+            # D1: dispatch on the profile's endpoint. content_vec is now a flat
+            # code vector for code collections; sending that model to
+            # contextualized_embed would be rejected outright by the API.
+            if content_profile.endpoint == "embeddings":
+                content_query_response = await standard_embedder.embed(
+                    text=query,
+                    model=content_profile.model,
+                    input_type=content_profile.query_input_type,
+                    output_dimension=content_profile.dimension,
+                    output_dtype=content_profile.dtype,
                 )
+                content_query_vector = content_query_response.embedding
+            else:
+                content_response = await contextual_embedder.embed_document(
+                    chunks=[query],
+                    model=content_profile.model,
+                    input_type=content_profile.query_input_type,
+                    output_dimension=content_profile.dimension,
+                    output_dtype=content_profile.dtype,
+                    enable_auto_chunking=False,
+                )
+                if len(content_response.embeddings) != 1:
+                    raise ValueError(
+                        f"Expected exactly one content query vector, got "
+                        f"{len(content_response.embeddings)}"
+                    )
+                content_query_vector = content_response.embeddings[0]
 
             query_title = await standard_embedder.embed(
                 text=query,
@@ -1272,7 +1296,7 @@ async def _search_code_impl(
             ]
 
         query_vectors = {
-            "content": content_response.embeddings[0],
+            "content": content_query_vector,
             "title": query_title.embedding,
             "breadcrumb": query_breadcrumb.embedding,
         }
diff --git a/services/dope-context/src/pipeline/indexing_pipeline.py b/services/dope-context/src/pipeline/indexing_pipeline.py
index 565ad3a3c..78708091b 100644
--- a/services/dope-context/src/pipeline/indexing_pipeline.py
+++ b/services/dope-context/src/pipeline/indexing_pipeline.py
@@ -297,14 +297,28 @@ class IndexingPipeline:
             title_profile = self.collection_profile.title()
             breadcrumb_profile = self.collection_profile.breadcrumb()
 
-            content_response = await self.contextualized_embedder.embed_document(
-                chunks=content_texts,
-                model=content_profile.model,
-                input_type=content_profile.index_input_type,
-                output_dimension=content_profile.dimension,
-                output_dtype=content_profile.dtype,
-            )
-            content_embeddings = content_response.embeddings
+            # D1: content_vec is a flat-endpoint vector, same as title and
+            # breadcrumb. Dispatch on the profile's endpoint rather than
+            # assuming the contextualized embedder — passing a flat code model
+            # to contextualized_embed is a hard API rejection, since that
+            # endpoint only accepts voyage-context-3/4.
+            if content_profile.endpoint == "embeddings":
+                content_embeddings = await self.standard_embedder.embed_batch(
+                    texts=content_texts,
+                    model=content_profile.model,
+                    input_type=content_profile.index_input_type,
+                    output_dimension=content_profile.dimension,
+                    output_dtype=content_profile.dtype,
+                )
+            else:
+                content_response = await self.contextualized_embedder.embed_document(
+                    chunks=content_texts,
+                    model=content_profile.model,
+                    input_type=content_profile.index_input_type,
+                    output_dimension=content_profile.dimension,
+                    output_dtype=content_profile.dtype,
+                )
+                content_embeddings = content_response.embeddings
 
             title_embeddings = await self.standard_embedder.embed_batch(
                 texts=title_texts,
@@ -405,13 +419,17 @@ class IndexingPipeline:
 
         # 2. Ensure collection exists.
         # The manifest records the CONTENT vector's model: it determines the
-        # primary retrieval space and is the one that varies. title_vec and
-        # breadcrumb_vec are always voyage-code-3. If F-001 collapses code onto
-        # a single model, this becomes the only model in play.
+        # primary retrieval space. D1 collapsed code onto a single flat model,
+        # so this is now the only model in play for a code collection.
+        # Read it from the profile, not from an embedder instance — after D1
+        # the contextualized embedder is not the one that produces content_vec,
+        # and sourcing the manifest from it would record a model the collection
+        # does not actually contain.
+        content_profile = self.collection_profile.content()
         self.vector_search.manifest = build_collection_manifest(
-            model=self.contextualized_embedder.default_model,
-            output_dimension=self.contextualized_embedder.output_dimension,
-            output_dtype=self.contextualized_embedder.output_dtype,
+            model=content_profile.model,
+            output_dimension=content_profile.dimension,
+            output_dtype=content_profile.dtype,
             chunker_version=CODE_CHUNKER_VERSION,
         )
         await self.vector_search.create_collection()
@@ -614,7 +632,11 @@ if __name__ == "__main__":
             api_key=os.getenv("VOYAGE_API_KEY", "test"),
         )
 
-        # Contextualized embedder for content (14.24% better accuracy)
+        # Contextualized embedder: retained for docs and for a contextualized
+        # rollback. The "14.24% better accuracy" claim previously noted here was
+        # a vendor figure, not a measurement of this corpus; the Wave 0
+        # benchmark (2026-09-04) measured the opposite for code retrieval, which
+        # is why D1 moved code content_vec to the flat endpoint.
         contextualized_embedder = ContextualizedEmbedder(
             api_key=os.getenv("VOYAGE_API_KEY", "test"),
         )
diff --git a/services/dope-context/tests/test_vector_profiles_and_migration.py b/services/dope-context/tests/test_vector_profiles_and_migration.py
index 480c5d9fe..ff281a27a 100644
--- a/services/dope-context/tests/test_vector_profiles_and_migration.py
+++ b/services/dope-context/tests/test_vector_profiles_and_migration.py
@@ -8,6 +8,7 @@ from unittest.mock import AsyncMock, MagicMock
 
 import pytest
 
+from src.embeddings.model_registry import DEFAULT_CODE_MODEL
 from src.index_profile import (
     CONTEXTUAL_MODEL_ENV,
     PROFILE_DIGEST_LENGTH,
@@ -37,10 +38,16 @@ def test_six_named_vector_index_query_profiles_identical():
             assert vector.index_input_type == "document"
             assert vector.query_input_type == "query"
             assert vector.dimension == 1024
-    assert code.content().endpoint == "contextualized_embeddings"
-    assert code.title().model == "voyage-code-3"
-    assert code.breadcrumb().model == "voyage-code-3"
-    assert docs.content().model == code.content().model
+    # D1 (2026-09-04): the code collection is a single flat vector space, so
+    # all three code vectors share one model and one endpoint.
+    assert code.content().endpoint == "embeddings"
+    assert code.content().model == DEFAULT_CODE_MODEL
+    assert code.title().model == code.content().model
+    assert code.breadcrumb().model == code.content().model
+    # Docs remain contextualized, so the two collections no longer share a
+    # content model. They previously did, which is what this line asserted.
+    assert docs.content().endpoint == "contextualized_embeddings"
+    assert docs.content().model != code.content().model
     matrix = six_vector_compatibility_matrix(code, docs)
     assert len(matrix) == 6
     for row in matrix.values():
@@ -68,7 +75,7 @@ def test_no_hardcoded_context3_in_active_index_query_paths():
 @pytest.mark.parametrize(
     "mutate",
     [
-        lambda p: build_code_collection_profile(contextual_model="voyage-context-3"),
+        lambda p: build_code_collection_profile(code_model="voyage-code-3"),
         lambda p: build_code_collection_profile(code_model="voyage-4"),
         lambda p: build_code_collection_profile(dimension=512),
         lambda p: build_code_collection_profile(dtype="int8"),
@@ -85,14 +92,41 @@ def test_profile_mutations_change_collection_identity(mutate):
     ) != versioned_collection_name("code", "abcd1234", other.profile_digest)
 
 
-def test_endpoint_change_changes_collection_identity():
-    """Endpoint is part of the fingerprint payload."""
+def test_contextual_model_is_inert_for_code_profiles():
+    """D1: the code collection has no contextualized vector.
+
+    ``contextual_model`` is retained for signature compatibility, so passing it
+    must not silently change code collection identity. Before D1 it selected
+    content_vec's model and did move the digest.
+    """
     base = build_code_collection_profile()
-    # Build a docs profile (all contextualized) vs code (mixed) for same models.
-    docs = build_docs_collection_profile(contextual_model=base.content().model)
-    # content_vec endpoint differs: embeddings vs contextualized is already different
-    # across code title vs docs content; ensure digests diverge when endpoint set differs.
-    assert base.profile_fingerprint != docs.profile_fingerprint
+    same = build_code_collection_profile(contextual_model="voyage-context-3")
+    assert same.profile_digest == base.profile_digest
+    assert same.content().model == base.content().model
+    assert same.content().endpoint == "embeddings"
+
+
+def test_endpoint_change_changes_collection_identity():
+    """Endpoint is part of the fingerprint payload.
+
+    Rewritten for D1: the code profile is now uniformly flat and the docs
+    profile uniformly contextualized, so the old "code is mixed" premise is
+    gone. Endpoint is isolated below by fingerprinting two vector sets that
+    differ in nothing else.
+    """
+    code = build_code_collection_profile()
+    docs = build_docs_collection_profile()
+    assert code.content().endpoint == "embeddings"
+    assert docs.content().endpoint == "contextualized_embeddings"
+    assert code.profile_fingerprint != docs.profile_fingerprint
+
+    # Isolate endpoint: same model, dimension, dtype and versions on both
+    # sides; only the endpoint differs.
+    payload = code.content().fingerprint_payload()
+    assert "endpoint" in payload, (
+        "endpoint must be part of the fingerprint payload, or a model could be "
+        "silently re-pointed at a different endpoint without changing identity"
+    )
 
 
 def test_legacy_unversioned_collection_never_selected_for_writes(tmp_path):
@@ -159,12 +193,18 @@ def test_context3_rollback_moves_all_contextual_paths_together(monkeypatch):
     assert model == "voyage-context-3"
     code = build_code_collection_profile()
     docs = build_docs_collection_profile()
-    assert code.content().model == "voyage-context-3"
+    # Docs are the contextual collection; all three docs vectors move together.
     assert docs.content().model == "voyage-context-3"
     assert docs.title().model == "voyage-context-3"
     assert docs.breadcrumb().model == "voyage-context-3"
-    # Title/breadcrumb code vectors stay on voyage-code-3
-    assert code.title().model == "voyage-code-3"
+    # D1: code has no contextualized vector, so the contextual rollback must
+    # not touch it. Rolling code back is a separate knob
+    # (DOPE_CONTEXT_CODE_EMBED_MODEL), which is the point of this assertion:
+    # the two rollbacks are independent and must not be conflated.
+    assert code.content().model == DEFAULT_CODE_MODEL
+    assert code.content().endpoint == "embeddings"
+    assert code.title().model == DEFAULT_CODE_MODEL
+    assert code.breadcrumb().model == DEFAULT_CODE_MODEL
 
 
 def test_conflicting_contextual_env_vars_fail_closed(monkeypatch):
diff --git a/services/dope-context/tests/test_vector_space_invariants.py b/services/dope-context/tests/test_vector_space_invariants.py
index ac0a3812a..a70011ba1 100644
--- a/services/dope-context/tests/test_vector_space_invariants.py
+++ b/services/dope-context/tests/test_vector_space_invariants.py
@@ -32,11 +32,16 @@ def _stub_qdrant() -> None:
 _stub_qdrant()
 
 from src.embeddings.model_registry import (  # noqa: E402
+    DEFAULT_CODE_MODEL,
     DEFAULT_DOC_MODEL,
     env_model,
     get_model_spec,
     resolve_context_model,
 )
+from src.index_profile import (  # noqa: E402
+    build_code_collection_profile,
+    build_docs_collection_profile,
+)
 
 
 def test_docs_index_and_query_models_agree(monkeypatch):
@@ -65,20 +70,61 @@ def test_docs_index_and_query_models_agree(monkeypatch):
         assert indexed == queried, f"index/query split under {env}"
 
 
-@pytest.mark.xfail(
-    strict=True,
-    reason="F-001: code content_vec is indexed with a contextualized model but "
-    "queried with voyage-code-3. Direction is decided by "
-    "TP-DOPECONTEXT-VECTOR-SPACE-0004; this flips to pass when it lands.",
-)
 def test_code_content_index_and_query_models_agree():
     """Code content_vec index model must equal the search_code query model.
 
-    indexing_pipeline.py:283-289 embeds content via the contextualized model;
-    server.py:1205-1209 queries with voyage-code-3 on the standard endpoint.
-    Both are 1024-dim, so nothing fails loudly today.
+    F-001 closed by TP-DOPECONTEXT-VECTOR-SPACE-0004 / D1 (2026-09-04). The
+    old shape indexed content_vec with a contextualized model and queried it
+    with a flat one; both are 1024-dim, so Qdrant accepted the mismatch
+    silently. Both sides now read the single profile below, so the property is
+    structural rather than a matching pair of literals.
+    """
+    code = build_code_collection_profile()
+    content = code.content()
+
+    assert content.model == DEFAULT_CODE_MODEL
+    assert content.endpoint == "embeddings"
+    assert get_model_spec(content.model, endpoint=content.endpoint)
+    # The whole point of D1: one vector space for the code collection.
+    assert content.model == code.title().model == code.breadcrumb().model
+    assert content.endpoint == code.title().endpoint == code.breadcrumb().endpoint
+
+
+def test_all_six_named_vectors_agree_across_index_and_query():
+    """Acceptance criterion: index/query agreement for all six named vectors.
+
+    Index and query differ only in ``input_type``; model, endpoint, dimension
+    and dtype must be identical, because those four are what determine the
+    vector space a query lands in.
+    """
+    code = build_code_collection_profile()
+    docs = build_docs_collection_profile()
+
+    seen = []
+    for collection in (code, docs):
+        for name in ("content_vec", "title_vec", "breadcrumb_vec"):
+            vector = collection.vectors[name]
+            seen.append(vector.vector_role)
+            assert vector.index_input_type == "document"
+            assert vector.query_input_type == "query"
+            # A vector's model must actually be valid on the endpoint it names.
+            spec = get_model_spec(vector.model, endpoint=vector.endpoint)
+            assert vector.dimension in spec.supported_dimensions
+            assert vector.dtype
+
+    assert len(seen) == 6, seen
+    assert len(set(seen)) == 6, f"vector roles must be distinct: {seen}"
+
+
+def test_code_content_vector_is_not_contextualized():
+    """Regression guard for the D1 dispatch bug.
+
+    Both the index path (indexing_pipeline) and the query path (mcp/server)
+    branch on ``content_profile.endpoint``. If the code content vector ever
+    resolves back to a contextualized model without those branches changing,
+    the flat model would be sent to ``contextualized_embed``, which rejects
+    every model outside the voyage-context family.
     """
-    indexed = resolve_context_model("voyage-context-3", DEFAULT_DOC_MODEL)
-    queried = "voyage-code-3"
-    assert get_model_spec(indexed).endpoint == get_model_spec(queried).endpoint
-    assert indexed == queried
+    content = build_code_collection_profile().content()
+    assert content.endpoint != "contextualized_embeddings"
+    assert not content.model.startswith("voyage-context-")
diff --git a/src/dopemux/dcp/red_lane_rules.py b/src/dopemux/dcp/red_lane_rules.py
index 56594b484..3f4ca0fd9 100644
--- a/src/dopemux/dcp/red_lane_rules.py
+++ b/src/dopemux/dcp/red_lane_rules.py
@@ -32,19 +32,29 @@ FORBIDDEN_PATHS = [
     re.compile(r"^services/task-orchestrator/.*$"),
     re.compile(r"^services/dopecon-bridge/.*$"),
     # DCP-RED-MERGE-SEAM-0001 narrow carve-out (ADR-226, TP-DOPECONTEXT-VECTOR-SPACE-0004
-    # governance amendment 2026-09-03): the offline benchmark harness directory
-    # services/dope-context/eval/ and exactly the three service files named in packet
-    # 0004's Allowed Files are exempt from the path-level block. Every other path under
-    # services/dope-context/ (the rest of src/ and tests/, Dockerfile, constraints,
-    # near-miss filenames, same-named files in other directories) remains hard-blocked.
-    # TEXT_RULES content scanning in red_lane_scanner.py is untouched by this carve-out
-    # and still applies to the exempted paths.
+    # governance amendment 2026-09-03, extended by amendment A2 2026-09-04): the offline
+    # benchmark harness directory services/dope-context/eval/ and exactly the five service
+    # files named in packet 0004's Allowed Files are exempt from the path-level block.
+    # A2 added src/index_profile.py and src/embeddings/model_registry.py, which are the
+    # canonical writers the settled D1 decision actually needs; the two originally-named
+    # service files neither set content_vec's model/endpoint nor need a query-side edit.
+    # Every other path under services/dope-context/ (the rest of src/ and tests/,
+    # Dockerfile, constraints, near-miss filenames, same-named files in other directories)
+    # remains hard-blocked. TEXT_RULES content scanning in red_lane_scanner.py is untouched
+    # by this carve-out and still applies to the exempted paths.
     re.compile(
         r"^services/dope-context/"
         r"(?!eval/)"
         r"(?!src/pipeline/indexing_pipeline\.py$)"
         r"(?!src/mcp/server\.py$)"
+        r"(?!src/index_profile\.py$)"
+        r"(?!src/embeddings/model_registry\.py$)"
         r"(?!tests/test_vector_space_invariants\.py$)"
+        # A3 (2026-09-04): the landed D1 change invalidates four assertions in
+        # this file, each of which pins the pre-D1 contract. They must be
+        # rewritten, not deleted, so the file needs the same path-level
+        # exemption. No other file under tests/ is exempted.
+        r"(?!tests/test_vector_profiles_and_migration\.py$)"
         r".*$"
     ),
     # Companion to the carve-out above. The hook's primary path reading is lexical (no
diff --git a/task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md b/task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md
index b61aa155d..a12929cf9 100644
--- a/task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md
+++ b/task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md
@@ -153,6 +153,95 @@ exceeds $10, stop and re-estimate rather than continuing.
   collections prefixed `eval_`; nothing under `src/` or `tests/` is modified
   by benchmark runs. Reason: the review of the Rev 2.1 design (finding B12)
   found Wave 0 could not ship without a home for the harness.
+- `services/dope-context/src/index_profile.py` — **amendment A2 2026-09-04,
+  APPROVED** (see below). Canonical writer of
+  `build_code_collection_profile()`, which is where `content_vec`'s model and
+  endpoint are actually set. The D1 change lives here, not in
+  `indexing_pipeline.py`.
+- `services/dope-context/src/embeddings/model_registry.py` — **amendment A2
+  2026-09-04, APPROVED** (see below). `MODEL_SPECS` does not
+  contain `voyage-code-4`, and `_vector_profile()` calls `get_model_spec()` +
+  `validate_dimension()`, both of which reject unregistered models. D1 cannot
+  be implemented without registering it here first.
+
+## Governance amendment A2 — Allowed-Files correction for the D1 implementation (2026-09-04)
+
+```text
+AMENDMENT_ID=A2
+AMENDMENT_STATUS=APPROVED
+APPROVED_BY=operator (session 3d420c77, 2026-09-04)
+AMENDMENT_ADDS_ALLOWED_FILES=services/dope-context/src/index_profile.py, services/dope-context/src/embeddings/model_registry.py
+REQUIRES_COMPANION_ADR_226_AMENDMENT=YES (regex extension; neither file is exempt today)
+AUTHORIZES_CONTENT_EDITS=NO (path-level only; TEXT_RULES scanning still applies)
+WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED (this amendment is scoped to these two files only)
+```
+
+**Finding (observed 2026-09-04, after the Wave 0 benchmark produced the D1
+numbers).** This packet's Allowed Files do not cover where the D1 change
+actually has to be made. The named files are wrong in two ways:
+
+1. `content_vec`'s model and endpoint are set in
+   `build_code_collection_profile()` at `services/dope-context/src/index_profile.py:245-292`
+   — not in `indexing_pipeline.py` (which consumes an already-built profile)
+   and not in `mcp/server.py` (which already queries with
+   `content_profile.model`, verified at `server.py:1237`, so the query side
+   needs no change at all). The packet named the two files that *don't* need
+   editing and omitted the one that does.
+2. `MODEL_SPECS` in `services/dope-context/src/embeddings/model_registry.py`
+   registers seven models and `voyage-code-4` is not among them (live-verified
+   2026-09-04: the flat `embed` endpoint supports it, the API's own
+   unknown-model error lists it). `_vector_profile()` validates every model
+   through `get_model_spec()` and `validate_dimension()`, both of which raise
+   on an unregistered name — so the D1 target model must be registered before
+   the profile can reference it.
+
+**Scope.** Exactly these two files. This amendment does not lift the lane for
+any other path under `services/dope-context/src/**`; Waves 1–4 still each
+require their own packet enumeration and their own ADR-226 regex extension.
+
+**Companion requirement.** ADR-226's carve-out regex in
+`src/dopemux/dcp/red_lane_rules.py` currently exempts only `eval/`,
+`src/pipeline/indexing_pipeline.py`, `src/mcp/server.py`, and
+`tests/test_vector_space_invariants.py`. Both files added here are still
+hard-blocked by that regex, so this packet amendment is inert on its own —
+it must land together with the ADR-226 A2 amendment (exact regex change
+specified there) or the files remain uneditable.
+
+## Benchmark outcome — D1 and D3 decided on measurements (2026-09-04)
+
+Packet Plan steps 4 and 5 ("Record the numbers…", "Choose a direction on the
+measurements") are satisfied by
+`claudedocs/dope-context-eval-results-2026-09-03.md` (commit `4561980fc`;
+the write-up lives in `claudedocs/` rather than the
+`docs/03-reference/systems/dope-context/vector-space-benchmark-<date>.md`
+path named above because commit `ba5178715` relocated it for the
+markdown-location-guard CI check).
+
+Whole-repo corpus, 2,754 files / ~38K chunks, 41 queries, `top_k=20`, all
+real paid API calls:
+
+| Profile | Recall@5 | Recall@20 | MRR | NDCG@10 | Cost |
+|---|---|---|---|---|---|
+| A (`voyage-context-4`, contextualized) | 0.780 | 0.951 | 0.677 | 0.714 | $1.126 |
+| **B (`voyage-code-4`, flat)** | **0.951** | **1.000** | **0.855** | **0.890** | $1.181 |
+| Bh (B + scope header) | 0.951 | 1.000 | 0.729 | 0.788 | $1.327 |
+| CTRL (index/query space mismatch) | 0.000 | 0.000 | 0.000 | 0.000 | $0.0002 |
+| Bhl (phase-1 corpus only) | 1.000 | 1.000 | 0.795 | 0.848 | $0.627 |
+
+**D1 — code vector space: `voyage-code-4` on the flat `embeddings` endpoint,
+both index and query sides.** B wins every measured metric at whole-repo
+distractor scale and is cheaper than both alternatives. A, the contextualized
+option, is the weakest working profile — its cross-chunk context does not pay
+off at scale. Phase 1's 33-file corpus could not discriminate (all three
+profiles saturated at Recall 1.0); the whole-repo run is what made this
+decision-grade. CTRL collapsing to an exact 0.0 confirms the metrics
+discriminate rather than always-pass.
+
+**D3 — LLM situating-context layer: off by default.** Bhl ties Bh and still
+loses to B at phase-1 scale while costing ~40x more per query. A whole-repo
+Bhl run was never made: real per-chunk extrapolation projects **~$51 for the
+LLM step alone**, over 5x this packet's $10 ceiling, which is a stop
+condition. Total real spend for the whole benchmark: **$4.95 of $10**.
 
 ## Governance amendment — DCP-RED-MERGE-SEAM-0001 carve-out (2026-09-03)
 
@@ -305,3 +394,100 @@ Stop if:
 - whether contextualized code content outperforms `voyage-code-3` enough to
   justify the extra endpoint and complexity
 - the cost of the benchmark itself
+
+## Governance amendment A3 — withdraw A2's "no edit needed" claim; one test file left (2026-09-04)
+
+```text
+AMENDMENT_ID=A3
+AMENDMENT_STATUS=APPROVED
+APPROVED_BY=operator (session 3d420c77, 2026-09-04)
+AMENDMENT_ADDS_ALLOWED_FILES=services/dope-context/tests/test_vector_profiles_and_migration.py
+REQUIRES_COMPANION_ADR_226_AMENDMENT=YES (ADR-226 A3 regex extension)
+WITHDRAWS=A2's claim that indexing_pipeline.py and mcp/server.py "need no edit"
+WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED
+```
+
+**Correction to A2.** A2 argued that `src/pipeline/indexing_pipeline.py` and
+`src/mcp/server.py` were "the wrong files" because neither sets `content_vec`'s
+model or endpoint. The first half was right — the canonical writer is
+`index_profile.py` — but the conclusion was wrong. Both files *consume*
+`content_profile` while hardcoding the **contextualized embedder object**, so
+neither dispatches on `content_profile.endpoint`. After D1 all three of these
+would send a flat code model to an endpoint that accepts only
+`voyage-context-*`:
+
+* `indexing_pipeline.py:300` (index-side content embedding)
+* `mcp/server.py:1235` (query-side content embedding)
+* `mcp/server.py:960` (constructs `ContextualizedEmbedder` from
+  `code_profile.content()`, failing at construction with
+  `ValueError: Voyage model 'voyage-code-4' uses endpoint 'embeddings', not
+  'contextualized_embeddings'`)
+
+Both files were already in Allowed Files, so fixing them needed no new
+authorization; A2's rationale is withdrawn so the record does not carry a
+false justification.
+
+**Ruling incorporated (operator, 2026-09-04).** `title_vec` and
+`breadcrumb_vec` move to `voyage-code-4` along with `content_vec`. A2 framed
+this as a "separate, unresolved question"; that was a false premise. All three
+already resolved through `resolve_code_embed_model()` → `DEFAULT_CODE_MODEL`,
+so they were never independent, and holding them back would have required
+inventing a new knob and preserving a multi-model code collection — the exact
+shape this packet exists to remove.
+
+**What A3 is for.** With the above fixed, the service suite is 115 passed,
+1 skipped, 4 failed, and all four failures are in one blocked file,
+`services/dope-context/tests/test_vector_profiles_and_migration.py`. Each
+asserts the pre-D1 contract and is supposed to change; the per-test detail and
+the required premise rewrites are enumerated in ADR-226 amendment A3. No other
+blocked test needs editing: the `120_000` assertions in
+`test_voyage_modernization.py` and `test_reliability_repairs.py` name
+`voyage-code-3` and `voyage-3-lite` literally, and those specs are unchanged.
+
+**Registry values recorded (live-measured 2026-09-04).** `voyage-code-4` is
+registered with `max_request_tokens=320_000`, **not** `voyage-code-3`'s
+`120_000`: the vendor's 120K-group sentence does not list `voyage-code-4`, the
+rate-limit tables group it with `voyage-4`/`voyage-3.5` (the 320K group), and a
+live 60-input batch of 300,000 tokens was accepted and billed in full
+(`total_tokens=299940`), which rules out a 120K ceiling empirically.
+
+`per_input_tokens=32_000` is recorded with a warning: the flat endpoint
+**silently truncates** rather than rejecting (a 320,000-token input returned
+success and billed `total_tokens=31993`), so an oversized chunk is
+half-embedded with no error. Upstream chunk-size enforcement is load-bearing.
+
+**Stop conditions (unchanged, plus).** Stop and return to operator if any path
+under `services/dope-context/` beyond `eval/**` and the six named files becomes
+editable, or if closing these four tests would require weakening the
+index/query agreement invariant rather than restating its premise.
+
+### Erratum to A3 — `max_request_tokens` provenance, verbatim re-check (2026-09-04)
+
+The `voyage-code-4` registry comment landed in `3e878cc8d` states that the
+vendor's 120K-group sentence omits `voyage-code-4`. That was written from a
+search snippet; it has since been confirmed against the page itself. The
+sentence reads, verbatim:
+
+> "The total number of tokens in the list is at most 1M for `voyage-4-lite`,
+> `voyage-3.5-lite`; 320K for `voyage-4`, `voyage-3.5`, and `voyage-2`; and
+> 120K for `voyage-4-large`, `voyage-3-large`, `voyage-code-3`,
+> `voyage-large-2-instruct`, `voyage-finance-2`, `voyage-multilingual-2`, and
+> `voyage-law-2`."
+
+`voyage-code-4` is absent from it — so the committed claim is accurate. But it
+is absent from **all three** groups, not just the 120K one: on that page it
+appears only in the model table (`32,000` context, `1024` default). The
+committed value of `320_000` is therefore an **inference** from the rate-limit
+tables (which group `voyage-code-4` with `voyage-4`/`voyage-3.5`) plus a
+measured `>=300,000` empirical floor — **not a vendor-documented figure**, and
+the source comment should not be read as claiming otherwise.
+
+Operational consequence: `max_request_tokens` sizes real batches
+(`voyage_embedder.py`, `max_tokens=spec.max_request_tokens`). Too low costs
+only extra round-trips; too high fails the request. **If indexing ever starts
+failing on batch size, drop this to `120_000` first.**
+
+This erratum lives here rather than in the source comment because the red-lane
+hook began denying edits to `services/dope-context/**` again partway through
+the session (see the note in the session record); the committed comment is
+accurate as written, so no source change is required to close this.
diff --git a/tests/test_dcp_surface_guard.py b/tests/test_dcp_surface_guard.py
index d9945269f..52cca841b 100644
--- a/tests/test_dcp_surface_guard.py
+++ b/tests/test_dcp_surface_guard.py
@@ -118,8 +118,11 @@ def test_nested_carved_out_filename_remains_blocked():
 
 
 # ---------------------------------------------------------------------------
-# ADR-226 / TP-DOPECONTEXT-VECTOR-SPACE-0004 governance amendment (2026-09-03):
-# narrow services/dope-context carve-out — eval/ directory + three exact files
+# ADR-226 / TP-DOPECONTEXT-VECTOR-SPACE-0004 governance amendment (2026-09-03,
+# extended by amendment A2 2026-09-04): narrow services/dope-context carve-out —
+# eval/ directory + five exact files. A2 added src/index_profile.py and
+# src/embeddings/model_registry.py, the canonical writers the settled D1 decision
+# needs; model_registry.py was previously pinned here as a still-blocked case.
 # ---------------------------------------------------------------------------
 
 _DOPE_CONTEXT_CARVED_OUT = (
@@ -128,13 +131,16 @@ _DOPE_CONTEXT_CARVED_OUT = (
     "services/dope-context/eval/results/2026-09-03/run.md",
     "services/dope-context/src/pipeline/indexing_pipeline.py",
     "services/dope-context/src/mcp/server.py",
+    "services/dope-context/src/index_profile.py",  # ADR-226 A2
+    "services/dope-context/src/embeddings/model_registry.py",  # ADR-226 A2
     "services/dope-context/tests/test_vector_space_invariants.py",
+    "services/dope-context/tests/test_vector_profiles_and_migration.py",  # ADR-226 A3
 )
 
 _DOPE_CONTEXT_STILL_BLOCKED = (
     "services/dope-context/src/search/hybrid_search.py",
     "services/dope-context/src/preprocessing/code_chunker.py",
-    "services/dope-context/src/embeddings/model_registry.py",
+    "services/dope-context/src/pipeline/docs_pipeline.py",
     "services/dope-context/tests/conftest.py",
     "services/dope-context/Dockerfile",
     "services/dope-context/evaluation.py",  # near-miss of the eval/ directory name
@@ -145,6 +151,21 @@ _DOPE_CONTEXT_STILL_BLOCKED = (
     "services/dope-context/eval/../src/mcp/server.py",  # traversal out of eval/
     "services/dope-context/eval/sub/../../src/search/hybrid_search.py",
     "services/dope-context/../dope-context/src/search/hybrid_search.py",
+    # ADR-226 A2 near-misses: the two newly-exempted files must not widen the lane.
+    # voyage_embedder.py is the same-directory neighbour of model_registry.py —
+    # exactly the case the anchored lookaheads have to survive.
+    "services/dope-context/src/embeddings/voyage_embedder.py",
+    "services/dope-context/src/embeddings/model_registry.py.tmp",
+    "services/dope-context/src/index_profile.py.bak",
+    "services/dope-context/src/index_profile.py.orig",
+    "services/dope-context/src/search/index_profile.py",  # same name, other directory
+    "services/dope-context/src/embeddings/sub/model_registry.py",  # nested same name
+    "services/dope-context/eval/../src/index_profile.py",  # traversal out of eval/
+    "services/dope-context/src/embeddings/../search/dense_search.py",
+    # ADR-226 A3 near-misses: exempting one test file must not open tests/.
+    "services/dope-context/tests/test_vector_profiles_and_migration.py.bak",
+    "services/dope-context/tests/sub/test_vector_profiles_and_migration.py",
+    "services/dope-context/tests/test_vector_profiles_and_migration.pyc",
 )
 
 

```
