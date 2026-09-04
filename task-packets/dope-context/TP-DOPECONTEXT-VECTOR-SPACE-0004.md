---
id: TP-DOPECONTEXT-VECTOR-SPACE-0004
title: Tp Dopecontext Vector Space 0004
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Benchmark-gated decision closing the F-001 blocker, choosing between
  contextualized and code-3 vectors for code content retrieval.
---
# Task Packet: TP-DOPECONTEXT-VECTOR-SPACE-0004

## Objective

Decide, on evidence, which embedding model owns the code `content_vec` space,
and make index and query provably agree. This closes **F-001**, the remaining
blocker from the PR #1112 post-merge audit.

## Status

`DECISION_REQUIRED`

Budget is **approved** (see below). The remaining gate is the direction
decision itself: do not execute the implementation half until the benchmark has
run and a direction has been chosen on the measurements.

## Risk

`HIGH`

Determines the primary code-retrieval signal. Choosing wrong degrades every
`search_code` result with no visible failure.

## The Finding

`indexing_pipeline.py:283-289` embeds code content through
`ContextualizedEmbedder.embed_document(model="voyage-context-3")`, which
`resolve_context_model` rewrites to `voyage-context-4` on the
`contextualized_embeddings` endpoint. `server.py:1205-1209` embeds the content
query with `voyage-code-3` on the standard `embeddings` endpoint.

Both produce 1024-dimensional vectors, so Qdrant stores and searches them
without complaint. `content_weight` dominates `SearchProfile.implementation()`.
There is no error, no log, and no metric.

Voyage documentation is **silent** on cross-family comparability. The only
stated compatibility concerns `input_type` variants of the same model.

This is pre-existing. PR #1112 changed which contextualized model is used, not
the mismatch itself.

## Evidence Bearing on the Decision

Recorded because it cuts against the worst-case reading and should inform,
not be suppressed:

`voyage-code-3` and `voyage-context-4` ship an **identical tokenizer and
vocabulary** — both 151,665 entries, and a mixed code and CJK probe encodes to
byte-identical ids. That indicates common lineage and shared input processing.

It does **not** establish a shared output space. A common vocabulary constrains
the input side only; two models with identical vocabularies can still project
into entirely unaligned spaces. But it means the realistic outcome may be
partial degradation rather than noise, which is exactly why the benchmark is
worth running instead of assumed.

## The Two Directions

**A. Query with the contextualized model.** Keep contextualized document
vectors for code content and switch `search_code`'s content query to the same
contextualized model and endpoint. Preserves whatever document-awareness
advantage the contextualized model provides.

**B. Index with `voyage-code-3`.** Embed code content with the same model
already used for title and breadcrumb. Provably consistent, matches upstream
`zilliztech/claude-context`, requires no live calls to justify.

`TP-DOPECONTEXT-VOYAGE4-REPAIR-0002` deliberately did not implement either.

## Scope

### IN

- an offline retrieval benchmark comparing A and B on a fixed query set
- a recorded decision with the measured numbers behind it
- implementing the chosen direction so index and query agree
- a test asserting index/query model agreement for all six named vectors
- updating the modernization audit document with the outcome

### OUT

- the collection gate (see `TP-DOPECONTEXT-COLLECTION-GATE-0003`)
- chunking strategy changes
- reranker changes
- any change before the benchmark has produced numbers

## Invariants

- For every named vector, index model, endpoint, dimension, and dtype equal the
  query model, endpoint, dimension, and dtype.
- Equal dimensionality is never accepted as evidence of compatibility.
- The decision is recorded with the measurements that produced it, not with a
  rationale alone.
- No production collection is migrated by this packet.

## Budget — APPROVED 2026-07-26

Live Voyage calls for this benchmark are **funded**. The estimate below was
measured, not guessed: token counts come from the real
`voyageai/voyage-code-3` tokenizer over this repository, priced against vendor
rates verified 2026-07-26 (`voyage-context-4` $0.12/M, `voyage-code-3` $0.18/M).
Code content carries a 1.5x inflation factor for the generated context that is
prepended to each chunk before embedding.

| Corpus | Files | Tokens | A | B | Control | **All three** |
|---|---|---|---|---|---|---|
| `services/dope-context` `.py` | 41 | 95,711 | $0.017 | $0.026 | $0.052 | **$0.09** |
| whole repo `.py` | 2,902 | 6,888,067 | $1.24 | $1.86 | $3.72 | **$6.82** |
| repo `.py` + all `docs/*.md` | 8,086 | 21,080,178 | $2.57 | $3.86 | $7.72 | **$14.14** |

Query cost is negligible: ~50 queries x 3 vectors x ~20 tokens is under $0.001.

**Approved plan: run the 41-file dope-context corpus first at $0.09 to validate
the harness, then the whole-repo Python corpus at $6.82 for the measurement.
Ceiling $10.** Do not embed `docs/*.md`; it triples cost for a corpus that does
not exercise code retrieval.

Report actual spend against this ceiling in the proof bundle. If projected spend
exceeds $10, stop and re-estimate rather than continuing.

## Prerequisites — blocking

1. **`TP-DOPECONTEXT-TEST-HARNESS-0005`** should land first. Nine MCP tool tests
   currently fail with `TypeError: 'FunctionTool' object is not callable`,
   which is precisely the surface needed to verify this end to end. Without it,
   verification is limited to the function level.

## Allowed Files

- `services/dope-context/src/pipeline/indexing_pipeline.py`
- `services/dope-context/src/mcp/server.py`
- `services/dope-context/tests/test_vector_space_invariants.py`
- `docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md`
- `docs/03-reference/systems/dope-context/vector-space-benchmark-<date>.md`
- `task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md`
- `services/dope-context/eval/**` — **amendment 2026-09-03** (operator-approved
  in session, "Amend packet, commit here"): the offline benchmark harness,
  query set, and per-run results live here. The harness reads
  `services/dope-context/src/preprocessing/code_chunker.py` and
  `src/search/hybrid_search.py` read-only and writes only throwaway Qdrant
  collections prefixed `eval_`; nothing under `src/` or `tests/` is modified
  by benchmark runs. Reason: the review of the Rev 2.1 design (finding B12)
  found Wave 0 could not ship without a home for the harness.
- `services/dope-context/src/index_profile.py` — **amendment A2 2026-09-04,
  APPROVED** (see below). Canonical writer of
  `build_code_collection_profile()`, which is where `content_vec`'s model and
  endpoint are actually set. The D1 change lives here, not in
  `indexing_pipeline.py`.
- `services/dope-context/src/embeddings/model_registry.py` — **amendment A2
  2026-09-04, APPROVED** (see below). `MODEL_SPECS` does not
  contain `voyage-code-4`, and `_vector_profile()` calls `get_model_spec()` +
  `validate_dimension()`, both of which reject unregistered models. D1 cannot
  be implemented without registering it here first.

## Governance amendment A2 — Allowed-Files correction for the D1 implementation (2026-09-04)

```text
AMENDMENT_ID=A2
AMENDMENT_STATUS=APPROVED
APPROVED_BY=operator (session 3d420c77, 2026-09-04)
AMENDMENT_ADDS_ALLOWED_FILES=services/dope-context/src/index_profile.py, services/dope-context/src/embeddings/model_registry.py
REQUIRES_COMPANION_ADR_226_AMENDMENT=YES (regex extension; neither file is exempt today)
AUTHORIZES_CONTENT_EDITS=NO (path-level only; TEXT_RULES scanning still applies)
WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED (this amendment is scoped to these two files only)
```

**Finding (observed 2026-09-04, after the Wave 0 benchmark produced the D1
numbers).** This packet's Allowed Files do not cover where the D1 change
actually has to be made. The named files are wrong in two ways:

1. `content_vec`'s model and endpoint are set in
   `build_code_collection_profile()` at `services/dope-context/src/index_profile.py:245-292`
   — not in `indexing_pipeline.py` (which consumes an already-built profile)
   and not in `mcp/server.py` (which already queries with
   `content_profile.model`, verified at `server.py:1237`, so the query side
   needs no change at all). The packet named the two files that *don't* need
   editing and omitted the one that does.
2. `MODEL_SPECS` in `services/dope-context/src/embeddings/model_registry.py`
   registers seven models and `voyage-code-4` is not among them (live-verified
   2026-09-04: the flat `embed` endpoint supports it, the API's own
   unknown-model error lists it). `_vector_profile()` validates every model
   through `get_model_spec()` and `validate_dimension()`, both of which raise
   on an unregistered name — so the D1 target model must be registered before
   the profile can reference it.

**Scope.** Exactly these two files. This amendment does not lift the lane for
any other path under `services/dope-context/src/**`; Waves 1–4 still each
require their own packet enumeration and their own ADR-226 regex extension.

**Companion requirement.** ADR-226's carve-out regex in
`src/dopemux/dcp/red_lane_rules.py` currently exempts only `eval/`,
`src/pipeline/indexing_pipeline.py`, `src/mcp/server.py`, and
`tests/test_vector_space_invariants.py`. Both files added here are still
hard-blocked by that regex, so this packet amendment is inert on its own —
it must land together with the ADR-226 A2 amendment (exact regex change
specified there) or the files remain uneditable.

## Benchmark outcome — D1 and D3 decided on measurements (2026-09-04)

Packet Plan steps 4 and 5 ("Record the numbers…", "Choose a direction on the
measurements") are satisfied by
`claudedocs/dope-context-eval-results-2026-09-03.md` (commit `4561980fc`;
the write-up lives in `claudedocs/` rather than the
`docs/03-reference/systems/dope-context/vector-space-benchmark-<date>.md`
path named above because commit `ba5178715` relocated it for the
markdown-location-guard CI check).

Whole-repo corpus, 2,754 files / ~38K chunks, 41 queries, `top_k=20`, all
real paid API calls:

| Profile | Recall@5 | Recall@20 | MRR | NDCG@10 | Cost |
|---|---|---|---|---|---|
| A (`voyage-context-4`, contextualized) | 0.780 | 0.951 | 0.677 | 0.714 | $1.126 |
| **B (`voyage-code-4`, flat)** | **0.951** | **1.000** | **0.855** | **0.890** | $1.181 |
| Bh (B + scope header) | 0.951 | 1.000 | 0.729 | 0.788 | $1.327 |
| CTRL (index/query space mismatch) | 0.000 | 0.000 | 0.000 | 0.000 | $0.0002 |
| Bhl (phase-1 corpus only) | 1.000 | 1.000 | 0.795 | 0.848 | $0.627 |

**D1 — code vector space: `voyage-code-4` on the flat `embeddings` endpoint,
both index and query sides.** B wins every measured metric at whole-repo
distractor scale and is cheaper than both alternatives. A, the contextualized
option, is the weakest working profile — its cross-chunk context does not pay
off at scale. Phase 1's 33-file corpus could not discriminate (all three
profiles saturated at Recall 1.0); the whole-repo run is what made this
decision-grade. CTRL collapsing to an exact 0.0 confirms the metrics
discriminate rather than always-pass.

**D3 — LLM situating-context layer: off by default.** Bhl ties Bh and still
loses to B at phase-1 scale while costing ~40x more per query. A whole-repo
Bhl run was never made: real per-chunk extrapolation projects **~$51 for the
LLM step alone**, over 5x this packet's $10 ceiling, which is a stop
condition. Total real spend for the whole benchmark: **$4.95 of $10**.

## Governance amendment — DCP-RED-MERGE-SEAM-0001 carve-out (2026-09-03)

```text
SEAM_CARVEOUT_ADR=ADR-226
SEAM_CARVEOUT_STATUS=OPERATOR_APPROVED_2026-09-03_LANDED_WITH_ADR_226
SEAM_CARVEOUT_SCOPE=services/dope-context/eval/** + the three services/dope-context files in Allowed Files
SEAM_CARVEOUT_AUTHORIZES_CONTENT_EDITS=NO
WAVES_1_4_SRC_LIFT=NOT_AUTHORIZED
```

**Finding (observed 2026-09-03).** `src/dopemux/dcp/red_lane_rules.py`
carries a blanket `^services/dope-context/.*$` entry in `FORBIDDEN_PATHS`
(added 2026-06-04, commit `4a120ff8d`, identical on `origin/main`, no
recorded rationale for the `services/*` entries, no override path). Hook H1
therefore hard-denies every Edit/Write under the service — including all
four service paths in this packet's Allowed Files. The denial was observed
live on an Edit under `services/dope-context/eval/` (the pre-commit
trailing-whitespace fix; the hook keeps no denial log, so the exact file is
reconstructed, not recorded) and confirmed by a programmatic
`surface_guard_block` probe on `eval/run_eval.py` and `src/mcp/server.py`.
No workaround was attempted. Note that H1 imports the rules from the
checkout `CLAUDE_PROJECT_DIR` names: in a session rooted at a main checkout
that predates ADR-226 the denial persists even after the carve-out is on
this branch, so implementation must run in a session whose hook enforces
ADR-226's rules (post-merge, or rooted at this branch).

**Ruling.** Operator chose the ADR-224 pattern (narrow, ADR-anchored,
negative-lookahead carve-out; approval required before it lands) over
relocating the harness or stopping. See
`docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md` for scope,
invariants, alternatives, and rollback.

**Disclosure.** The harness files under `services/dope-context/eval/`
pre-existed this amendment as untracked files, created earlier the same day
by a delegated sub-agent via a path the hook does not guard (exact mechanism
UNKNOWN). Under the M11 precedent that was a route-around; nothing under
`services/dope-context/` has been committed and nothing will be until
ADR-226 is approved and landed.

**What this amendment does not do.** It does not lift the lane for
`services/dope-context/src/**`. Waves 1–4 of the retrieval redesign
(`claudedocs/dope-context-retrieval-redesign-2026-09-03.md`) must each
enumerate exact files in their own packets and extend ADR-226's regex by
amendment before implementation. It does not change this packet's
`DECISION_REQUIRED` gate.

**Stop conditions (in addition to the packet's own).** Stop and return to
operator if: any path under `services/dope-context/` other than `eval/**`
and the three named files becomes editable; a symlink appears under
`services/dope-context/eval/`; `TEXT_RULES` stops firing on forbidden
content inside a carved-out file; or the carve-out commit touches any
semantic file beyond `red_lane_rules.py`, the two test files, ADR-226, and
this packet.

## Required Chain

`analyze -> apilookup -> thinkdeep -> challenge -> consensus -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

`consensus` is required here because this is a judgement call with two
defensible answers, not a defect with one correct fix.

## Plan

1. Assemble a fixed query set with known-relevant targets drawn from this
   repository. Record it so the benchmark is repeatable.
2. Build both configurations into isolated, clearly named benchmark collections.
   Never write to a production collection.
3. Measure recall@k and MRR for A and B on the same query set. Also measure the
   current broken configuration as a control, to quantify what the mismatch
   actually costs.
4. Record the numbers, the query set, the corpus, and the date.
5. Choose a direction on the measurements. If A and B are within noise, choose
   B for consistency with upstream and lower operational complexity.
6. Implement the chosen direction so index and query agree.
7. Add the invariant test for all six named vectors.
8. Update the modernization audit document with the outcome and delete the
   "benchmark the current mixed code-vector strategy" residual item.

## Exact Commands

```bash
git status --short --branch
python -m compileall -q services/dope-context/src
PYTHONPATH=services/dope-context python -m pytest -q \
  services/dope-context/tests/test_vector_space_invariants.py
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
git diff --stat
git diff
```

Benchmark commands are intentionally not specified here; they depend on the
approved budget and corpus and must be recorded verbatim in the benchmark
document when run.

## Acceptance Criteria

- A benchmark document exists recording query set, corpus, date, and measured
  recall@k and MRR for direction A, direction B, and the current control.
- A direction is chosen and the choice cites the numbers.
- Code `content_vec` index model, endpoint, dimension, and dtype equal the
  `search_code` content query model, endpoint, dimension, and dtype.
- A test asserts index/query agreement for all six named vectors.
- Audit adversarial test A14 flips from FAIL to PASS.
- No production collection was written during benchmarking.
- The suite gains no failure beyond the pre-existing ones.

## Proof Requirements

Return verbatim: the benchmark document, every benchmark command with exit code,
the measured numbers for all three configurations, the chosen direction with its
justification, base and final head SHA, `git diff`, the A14 result, and PR
metadata with checks. Also return the actual Voyage spend against the approved
estimate.

## Rollback

1. Revert the implementation commits; the benchmark document stays as evidence.
2. Delete benchmark collections explicitly; never leave them adjacent to
   production collections.
3. Because index and query move together, rollback restores the previous
   configuration wholesale rather than leaving a split.

## Stop Conditions

Stop if:

- projected spend would exceed the approved $10 ceiling
- the benchmark would write to a production collection
- measured spend exceeds the approved $10 ceiling
- A and B differ by less than the measurement noise and no tiebreak is agreed
- the control measurement shows the current mismatch is NOT degrading results,
  which would falsify the finding and require re-analysis before any change
- embedded audit returns FAIL or NEEDS_SUPERVISOR

## Current Evidence

### OBSERVED

- index model resolves to `voyage-context-4` on the contextualized endpoint
- query model is `voyage-code-3` on the standard endpoint
- both 1024-dimensional; Qdrant accepts both silently
- vendor documentation is silent on cross-family comparability
- the two models share an identical tokenizer and 151,665-entry vocabulary
- upstream `zilliztech/claude-context` uses one model for both sides

### UNKNOWN

- the empirical retrieval cost of the mismatch
- whether contextualized code content outperforms `voyage-code-3` enough to
  justify the extra endpoint and complexity
- the cost of the benchmark itself

## Governance amendment A3 — withdraw A2's "no edit needed" claim; one test file left (2026-09-04)

```text
AMENDMENT_ID=A3
AMENDMENT_STATUS=APPROVED
APPROVED_BY=operator (session 3d420c77, 2026-09-04)
AMENDMENT_ADDS_ALLOWED_FILES=services/dope-context/tests/test_vector_profiles_and_migration.py
REQUIRES_COMPANION_ADR_226_AMENDMENT=YES (ADR-226 A3 regex extension)
WITHDRAWS=A2's claim that indexing_pipeline.py and mcp/server.py "need no edit"
WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED
```

**Correction to A2.** A2 argued that `src/pipeline/indexing_pipeline.py` and
`src/mcp/server.py` were "the wrong files" because neither sets `content_vec`'s
model or endpoint. The first half was right — the canonical writer is
`index_profile.py` — but the conclusion was wrong. Both files *consume*
`content_profile` while hardcoding the **contextualized embedder object**, so
neither dispatches on `content_profile.endpoint`. After D1 all three of these
would send a flat code model to an endpoint that accepts only
`voyage-context-*`:

* `indexing_pipeline.py:300` (index-side content embedding)
* `mcp/server.py:1235` (query-side content embedding)
* `mcp/server.py:960` (constructs `ContextualizedEmbedder` from
  `code_profile.content()`, failing at construction with
  `ValueError: Voyage model 'voyage-code-4' uses endpoint 'embeddings', not
  'contextualized_embeddings'`)

Both files were already in Allowed Files, so fixing them needed no new
authorization; A2's rationale is withdrawn so the record does not carry a
false justification.

**Ruling incorporated (operator, 2026-09-04).** `title_vec` and
`breadcrumb_vec` move to `voyage-code-4` along with `content_vec`. A2 framed
this as a "separate, unresolved question"; that was a false premise. All three
already resolved through `resolve_code_embed_model()` → `DEFAULT_CODE_MODEL`,
so they were never independent, and holding them back would have required
inventing a new knob and preserving a multi-model code collection — the exact
shape this packet exists to remove.

**What A3 is for.** With the above fixed, the service suite is 115 passed,
1 skipped, 4 failed, and all four failures are in one blocked file,
`services/dope-context/tests/test_vector_profiles_and_migration.py`. Each
asserts the pre-D1 contract and is supposed to change; the per-test detail and
the required premise rewrites are enumerated in ADR-226 amendment A3. No other
blocked test needs editing: the `120_000` assertions in
`test_voyage_modernization.py` and `test_reliability_repairs.py` name
`voyage-code-3` and `voyage-3-lite` literally, and those specs are unchanged.

**Registry values recorded (live-measured 2026-09-04).** `voyage-code-4` is
registered with `max_request_tokens=320_000`, **not** `voyage-code-3`'s
`120_000`: the vendor's 120K-group sentence does not list `voyage-code-4`, the
rate-limit tables group it with `voyage-4`/`voyage-3.5` (the 320K group), and a
live 60-input batch of 300,000 tokens was accepted and billed in full
(`total_tokens=299940`), which rules out a 120K ceiling empirically.

`per_input_tokens=32_000` is recorded with a warning: the flat endpoint
**silently truncates** rather than rejecting (a 320,000-token input returned
success and billed `total_tokens=31993`), so an oversized chunk is
half-embedded with no error. Upstream chunk-size enforcement is load-bearing.

**Stop conditions (unchanged, plus).** Stop and return to operator if any path
under `services/dope-context/` beyond `eval/**` and the six named files becomes
editable, or if closing these four tests would require weakening the
index/query agreement invariant rather than restating its premise.

### Erratum to A3 — `max_request_tokens` provenance, verbatim re-check (2026-09-04)

The `voyage-code-4` registry comment landed in `3e878cc8d` states that the
vendor's 120K-group sentence omits `voyage-code-4`. That was written from a
search snippet; it has since been confirmed against the page itself. The
sentence reads, verbatim:

> "The total number of tokens in the list is at most 1M for `voyage-4-lite`,
> `voyage-3.5-lite`; 320K for `voyage-4`, `voyage-3.5`, and `voyage-2`; and
> 120K for `voyage-4-large`, `voyage-3-large`, `voyage-code-3`,
> `voyage-large-2-instruct`, `voyage-finance-2`, `voyage-multilingual-2`, and
> `voyage-law-2`."

`voyage-code-4` is absent from it — so the committed claim is accurate. But it
is absent from **all three** groups, not just the 120K one: on that page it
appears only in the model table (`32,000` context, `1024` default). The
committed value of `320_000` is therefore an **inference** from the rate-limit
tables (which group `voyage-code-4` with `voyage-4`/`voyage-3.5`) plus a
measured `>=300,000` empirical floor — **not a vendor-documented figure**, and
the source comment should not be read as claiming otherwise.

Operational consequence: `max_request_tokens` sizes real batches
(`voyage_embedder.py`, `max_tokens=spec.max_request_tokens`). Too low costs
only extra round-trips; too high fails the request. **If indexing ever starts
failing on batch size, drop this to `120_000` first.**

This erratum lives here rather than in the source comment because the red-lane
hook began denying edits to `services/dope-context/**` again partway through
the session (see the note in the session record); the committed comment is
accurate as written, so no source change is required to close this.

### Operational consequence — pre-D1 code collections must be recreated (2026-09-04)

Round-4 independent audit finding `STRANDED_COLLECTIONS`. D1 changes the code
content vector's model and endpoint, both of which are recorded in the
collection manifest and compared field by field by
`compare_collection_manifests()`. Every code collection indexed before D1 will
therefore raise `CollectionCompatibilityError` on the next write.

This fails closed with an actionable message rather than corrupting silently,
and no automatic migration is provided on purpose: the two vector spaces are
not comparable, so an in-place upgrade would reintroduce the F-001 defect. The
required action is explicit re-indexing. Docs collections are unaffected.
Blast radius today is near zero — Qdrant holds no dopemux-mvp code index.

Full rationale, including why `INDEX_SCHEMA_VERSION` is deliberately not
bumped, is in ADR-226 under "Operational consequence of D1".

### Live validation of D1 — and a deployment finding (2026-09-04)

Executed against the real Voyage API inside `mcp-dope-context`, importing the
fixed source from the mounted worktree. Cost **$0.00006** total.

| Run | content/title/breadcrumb | docs | content_vector | errors | verdict |
|---|---|---|---|---|---|
| container env as-is | `voyage-code-3` / `embeddings` | 4 | `List[float]`, dim 1024 | 0 | PASS |
| override cleared | `voyage-code-4` / `embeddings` | 4 | `List[float]`, dim 1024 | 0 | PASS |

This is the first execution of the D1 path. It confirms the round-6 repairs:
documents are produced (not the `([], [])` swallow signature), `content_vector`
is a genuine list of floats rather than an `EmbeddingResponse`, and embedding
cost accrues.

**FINDING — D1 is currently INERT in the live deployment.** The running
`mcp-dope-context` container sets:

```
DOPE_CONTEXT_CODE_EMBED_MODEL=voyage-code-3
```

`resolve_code_embed_model()` reads that variable and falls back to
`DEFAULT_CODE_MODEL` only when it is unset, so the env value **overrides**
D1's `voyage-code-4` default. The first run above resolved all three code
vectors to `voyage-code-3` despite the code default having changed.

Consequences:

* The measured D1 benefit (whole-repo R@20 1.000 / MRR 0.855 on
  `voyage-code-4`, versus the contextualized profile's 0.951 / 0.677) is **not
  realised in the deployed service** until that variable is removed or set to
  `voyage-code-4`.
* This is **not** a correctness defect. Index and query both read the same
  profile, so they still agree and F-001 stays closed — the collection is
  simply built on the older model.
* The variable is **not** in `compose.yml` or the repo `.env`; it comes from
  the bespoke env file the container was started with. Landing D1 in code is
  therefore insufficient — the deployment configuration must be updated
  separately, and any pre-D1 collection recreated (see "Operational
  consequence of D1" in ADR-226).

Why six independent audit rounds could not have found this: it is a fact about
the running deployment's environment, not about the source. Static review of a
diff or even of the whole repository cannot observe it.
