---
title: dope-context Wave Plan — Reconciliation Record (post-#1304)
date: 2026-09-04
author: Claude (Opus 5), session 5dd97667
status: RECORD — reconciliation only; no product code changed, no red-lane rule changed
base: origin/main f7f0ed626 (PR #1304 merged at 5af1509ca)
branch: claude/dope-context-wave-reconciliation-001
reconciles: claudedocs/dope-context-retrieval-redesign-2026-09-03.md (Rev 2.3)
produces: task-packets/dope-context/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007.md, ADR-226 amendment A5 (PROPOSED)
---

# 0. Reading guide

Six findings, one ruling, one re-cut plan. If you read three things:

1. **The Wave 1 you were about to implement is the superseded one** (§2, R-1). The redesign
   document carries *two* wave plans and says the later one wins. The handoff quoted the earlier.
   Reconciled against the later, Wave 1 is smaller and cheaper in governance than the ~9 new
   exemptions the handoff estimated — **5, split into two independently-approvable amendments**.
2. **"Manifest-compatible" survives as Wave 1's boundary, but for a different reason** (§4). The
   re-embed-cost argument that created it is spent. The reviewability argument that replaces it is
   stronger, and it *evicts* two files Rev 2 had left inside Wave 1.
3. **The red lane is not enforced in this session's project directory** (§2, R-6). Not stale —
   absent. Absence of a denial is not authorization.

Nothing here authorizes an edit under `services/dope-context/`. A5 is `PROPOSED`.

---

# 1. What this reconciles, and against what

| Layer | Source | Status |
|---|---|---|
| Plan of record | `claudedocs/dope-context-retrieval-redesign-2026-09-03.md`, Revision 2.3 | read in full |
| Governance | `docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md` incl. A2/A3/A4 | read in full |
| Packet | `task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md` (`DECISION_REQUIRED`) | read |
| Packet | `task-packets/dope-context/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002.md` (`AUTHORIZED_FOR_IMPLEMENTATION`) | read |
| Landed code | `services/dope-context/**` at `f7f0ed626` | inspected file-by-file for every Wave 1 item |
| Landed lane | `src/dopemux/dcp/red_lane_rules.py` at `f7f0ed626` | matches the handoff's quoted carve-out verbatim |
| Baseline | `mise exec -- python -m pytest tests -q` in `services/dope-context` | **PASS — 124 passed, 1 skipped** (re-run here, not quoted) |
| Guard | `PYTHONPATH=src pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -q` | **PASS — 69 passed** (re-run here) |

Truth order applied: **landed code outranks the plan document, and the plan document's later
revision outranks its earlier sections.** Both directions of that rule fired below.

---

# 2. Findings

## R-1 — The redesign document contains two Wave 1 definitions, and the handoff quoted the superseded one

`claudedocs/dope-context-retrieval-redesign-2026-09-03.md` specifies waves twice:

* **§7 "Implementation plan"** — Waves 0–5. This is where "Defaults unchanged in this wave (still
  context-4 on code) so no manifest bump" lives, and where the owner-file list the handoff
  tabulated comes from.
* **Revision 2, §R2.2 item "7 Waves (supersedes; file-disjoint)"** — Waves 0–4, re-cut in response
  to review findings B5 (manifest bump out of Wave 1) and B6 (waves not file-disjoint).

Revision 2's own header states: *"Where this revision conflicts with the numbered sections above,
**this revision wins**."* Revision 2.1 §7 then adds `model_registry.py` to Wave 1's scope.

The two Wave 1 definitions are materially different:

| | §7 Wave 1 (handoff's basis) | Rev 2 + Rev 2.1 Wave 1 (governing) |
|---|---|---|
| `voyage_embedder.py` | yes | yes |
| `indexing_pipeline.py` | yes (exclude + sleep) | yes (sleep/gather/RAM) |
| `mcp/server.py` | yes (exclude, filter_language, flags) | **no** — split across Rev-2 W2/W3 |
| `model_registry.py` | yes (via Rev 2.1 §7) | yes (via Rev 2.1 §7) |
| `voyage_reranker.py` | yes | yes |
| `token_budget.py` | yes | yes |
| `model_tokenizer.py` | yes | yes |
| `contextualized_embedder.py` | yes | **no** |
| `document_processor.py` | yes (C12 only) | **no** |
| `openai_generator.py` | yes | **no** — Rev-2 W4 (`context/*`) |
| `claude_generator.py` | yes | **no** — Rev-2 W4 (`context/*`) |
| `code_chunker.py` | **no** | **yes** |

**Consequence.** The handoff's "A5 ≈ 9 new exemptions" is computed from the superseded list. It is
not wrong arithmetic; it is the right arithmetic on the wrong Wave 1. §5 and §6 below re-derive it.

## R-2 — Rev 2's re-cut is itself defective in three ways; the reconciliation must rule, not inherit

1. **`code_chunker.py` sits inside a wave Rev 2 calls "behaviour only, manifest-compatible".** It
   cannot. `CODE_CHUNKER_VERSION` (`services/dope-context/src/index_profile.py:35`) is a member of
   `VectorProfile.fingerprint_payload()` (`services/dope-context/src/index_profile.py:77-89`), which feeds
   `fingerprint_profiles()` → `profile_digest` → the collection *name*. Any change to
   `code_chunker.py` that changes chunk output requires bumping that constant, which is
   manifest-affecting by construction. **Ruled: evicted from Wave 1** (§4, §6).
2. **Rev 2's re-cut silently deleted §7's Wave 2 (chunking v2) and orphaned four files.** No Rev-2
   wave owns `document_processor.py`, `contextualized_embedder.py`, `pipeline/docs_pipeline.py`, or
   `search/bm25_index.py`, and the whole of design §4.3 (chunking v2, cAST split-and-merge,
   fence-aware markdown, file-summary chunks) has no wave at all. **Ruled: chunking is restored as a
   wave** (§6); each orphan is homed there or in the sync wave.
3. **`server.py` carries C1 and C13 but is not in Rev 2's Wave 1.** Rev 2 splits it across W2/W3.
   It is already exempt (base carve-out), so pulling C1/C13 forward into Wave 1 costs **no
   amendment**. It is safe only because the waves are sequential — noted so a future parallel
   re-cut does not inherit the shortcut silently.

## R-3 — C12 is not a trivial bug fix; it is manifest-affecting

The handoff proposes splitting A5 by risk with `document_processor.py` in the *low-risk* lane
alongside `model_tokenizer.py` and `token_budget.py`. It does not belong there.

C12 is `"\\n\\n".join(...)` at `src/preprocessing/document_processor.py:143,154` and
`"\\n".join(...)` at `:173` — literal two-character `\n` sequences inserted into extracted
PDF/DOCX/HTML text. Fixing it **changes the text that gets chunked and embedded** for every
extracted document. That requires bumping `DOCS_CHUNKER_VERSION`
(`services/dope-context/src/index_profile.py:36`, currently `"document_processor.v2-voyage-token-accounting"`), which is in
`fingerprint_payload()` and therefore strands every existing docs collection.

D1 deliberately left docs collections alone (ADR-226, "Operational consequence of D1": *"Docs
collections are unaffected"*). C12 in Wave 1 would undo that on a one-line change filed as trivial.
**Ruled: C12 moves to the chunking wave**, where a `DOCS_CHUNKER_VERSION` bump is expected and
disclosed.

## R-4 — Three Wave 1 items are already closed on `main`; one owner file drops out entirely

Full item-level state in §5. The three that the handoff's open-items list does not account for:

* **E3** (`RerankQueryTooLargeError` swallowed into a silent dense-only fallback) — **closed.**
  `voyage_reranker.py:29-33,180` raises loudly (F-014), `:258` sets `degraded=True` on the fallback
  path, and `mcp/server.py:1351-1353,1380-1381` surfaces `reranked`, `rerank_degraded`, and
  `rerank_failure_reason` in the response.
* **E11** (unbounded embedding cache) — **closed.** `voyage_embedder.py:188-201` (`_cache_response`)
  expires then evicts oldest-first against `max_cache_entries` (F-012).
* **E21** (cost summary computes hit ratio before counting requests) — **closed.**
  `CostTracker.add_request` increments `total_requests` first in both
  `voyage_embedder.py:78-79` and `contextualized_embedder.py:60-61`.

**Consequence:** with E3 closed and the reranker's retry-once path belonging to the retrieval wave
(§7 W4), `voyage_reranker.py` has **no remaining Wave 1 work of its own** beyond E1 retry parity.
That removes it from the low-risk lane and is worth one exemption fewer than Rev 2 implies.

## R-5 — A4 left a residual: `EmbeddingRequest.truncation` still defaults to `True`

ADR-226 A4 required flipping the `truncation` defaults to `False`. Both **public method** defaults
were flipped — `voyage_embedder.py:278` (`embed`) and `:339` (`embed_batch`), commit `7f799306c`.
The **frozen dataclass** default was not: `EmbeddingRequest.truncation: bool = True` at
`voyage_embedder.py:43`.

It is latent today, not live: the only production constructor is `voyage_embedder.py:259`, which
passes `truncation=` explicitly; the other three are in `tests/test_voyage_modernization.py`. But
it is exactly the shape of defect A4 was written to end — *"a fix for the callers we happen to know
about, not for the defect"* — and it is a fail-open default on a file the round-5 auditor already
ruled must fail closed.

**Zero governance cost to fix:** `voyage_embedder.py` is already exempt under A4.
Filed into Wave 1a.

## R-6 — DCP-RED-MERGE-SEAM-0001 is **absent**, not stale, in this session's project directory

The handoff's constraint reads: *"The hook's rules come from `$CLAUDE_PROJECT_DIR`. A main-rooted
session enforces main's copy. Re-probe rather than assume."* Re-probed. The result is worse than
"stale", and it changes what the constraint means in practice.

The main working copy `/Users/hue/code/dopemux-mvp` is on branch `pr-92`, whose tree does not
contain the guard at all:

* `.claude/hooks/dcp_surface_guard.py` — **does not exist** (`.claude/hooks/` holds only
  `check_energy.sh`, `log_progress.sh`, `prompt_analyzer.py`, `save_context.sh`).
* `src/dopemux/dcp/red_lane_rules.py` — **does not exist** (`src/dopemux/dcp/` holds only a stale
  `__pycache__`).
* `.claude/settings.json` `PreToolUse` registers one hook, `check_energy.sh`, on matcher
  `thinkdeep|morph|batch_edit|refactor|deep_research` — which matches no file-writing tool.
* No other settings layer supplies it either: `.claude/settings.local.json`,
  `~/.claude/settings.json` and `~/.claude/settings.local.json` contain zero references to
  `dcp_surface_guard`. The guard is unregistered at every layer, not merely missing from one.

So a session rooted at the main checkout in its current state enforces **nothing** on
`services/dope-context/**`. An Edit there is silently permitted. The handoff's rule "if the Edit
tool denies a path, that is the answer" is sound in one direction only; its converse does not hold
here. **Absence of a denial is not authorization.** Wave 1 implementation must run from a worktree
off `origin/main` (which does carry both files, verified) — not merely to pick up the carve-out,
but to have a lane at all.

---

# 3. Wave-vs-reality delta table

`§7` = redesign §7 Waves 0–5. `R2` = Revision 2 §R2.2 re-cut Waves 0–4. Commits are on
`origin/main` via merge `5af1509ca` (PR #1304).

| Wave | Assumed | What landed | Verdict |
|---|---|---|---|
| **§7 W0 / R2 W0** — eval harness + model decision | benchmark decides D1; no product code | harness landed (`6205ab8c2`, `3da4aac9c`, `e7553dd90`); smoke results `claudedocs/dope-context-eval-results-2026-09-03.md`; carve-out for `eval/**` landed with ADR-226 (`720991c41`) | **DONE, with a caveat.** The whole-repo (~$6.82) decision-grade run is **NOT_RUN**; `Bhl` blocked on an empty `OPENAI_API_KEY` in `mcp-dope-context`. Packet 0004 correctly stays `DECISION_REQUIRED`. D1 was ruled by the operator on the smoke run + vendor evidence, not on the funded benchmark. |
| **§7 W0 (implicit)** — no product code | "this document and the audit are the only files" | D1 implemented inside Wave 0's packet: `3e878cc8d` (registry `voyage-code-4`, `DEFAULT_CODE_MODEL`, `index_profile.py` content_vec → flat endpoint, `server.py`, `indexing_pipeline.py`), `e80cda77d` (4 test premises restated), `982ecd107` (batch ceiling + test rigour), `eec45ec48` (2 BLOCKERs in the flat path), `77f96ab55` + `7f799306c` (truncation, `SearchRequest`) | **VOID.** Wave 0 shipped Wave-2-class work (model + endpoint = two `fingerprint_payload()` fields). This is the mechanism behind ADR-226's `STRANDED_COLLECTIONS` disclosure. |
| **§7 W1** — correctness fixes, manifest-compatible | 11 owner files, "defaults unchanged … so no manifest bump" | superseded by R2 W1 (R-1). Of its items: E3/E11/E21 **already closed**; registry `voyage-code-4` + `DEFAULT_CODE_MODEL` **done** (`3e878cc8d`); truncation flip **done** (`7f799306c`); the rest open (§5) | **PARTLY DONE, PREMISE VOID, DEFINITION SUPERSEDED.** Re-cut as Wave 1a/1b/1c (§6). |
| **R2 W1** — behaviour only, manifest-compatible | 6 files incl. `code_chunker.py` | same landed state | **DEFECTIVE AS SCOPED** (R-2.1). `code_chunker.py` evicted; `server.py` pulled in; `voyage_reranker.py` reduced to E1 parity (R-4). |
| **§7 W2** — chunking v2 (code + docs) | `code_chunker.py`, `document_processor.py`, new `chunk_sizing.py` | nothing landed | **INTACT but ORPHANED** — R2's re-cut has no successor wave for it (R-2.2). **Restored** as Wave 2 (§6), now also carrying C12 (R-3). |
| **§7 W3** — identity v2 + streaming + worktree sync (needs D2) | `workspace.py`, `index_profile.py`, pipelines, `sync/*`, `autonomous/*`, new `identity.py`/`git_universe.py` | nothing landed. D2 **approved** by operator (Rev 2.3) as a design decision only; `WAVES_1_4_SRC_LIFT=NOT_AUTHORIZED` unchanged | **INTACT.** R2 split it: schema/identity → R2 W2, sync/autonomy → R2 W3. Adopted (§6 Waves 3 and 4). |
| **§7 W4 / R2 W2** — retrieval v2, Qdrant-native hybrid | `dense_search.py`, `hybrid_search.py`, delete `bm25_index.py`, `server.py` search handlers | only `dense_search.py`'s dead `SearchRequest` import deleted (`7f799306c`, A4) — a crash-loop fix, not retrieval work | **INTACT.** Note the design's `models.Document`/`fastembed` sparse route was already refuted (B4) and replaced by a client-side `SparseEncoder` (R2 §4.5); that supersession stands. |
| **§7 W5** — model default switch + docs + packet closure | `DEFAULT_CODE_MODEL="voyage-code-4"`, Dockerfile envs, README, packet closure, container rebuild + live reindex | `DEFAULT_CODE_MODEL` flip **done** (`3e878cc8d`); everything else open. R2's re-cut **dropped this wave entirely** | **HALF-CONSUMED BY D1.** The code half is done; the deployment + closure half is not, and R2 has no home for it. **Restored** as Wave 6 (§6). The deployed `mcp-dope-context` still runs `DOPE_CONTEXT_CODE_EMBED_MODEL=voyage-code-3` from a runtime env, so **D1 is inert in production** — that is Wave 6's work, not a Wave 1 concern. |
| **R2 W4** — context generation | `context/*` | nothing landed | **INTACT**, and de-prioritised: D3 ruled the LLM context layer **off by default**, and its measuring arm (`Bhl`) is NOT_RUN. Becomes Wave 5, gated on `Bhl`. |

---

# 4. Ruling on the manifest boundary

**Question posed by the handoff:** Wave 2 was the schema-change wave; D1 already made the schema
change. Does Wave 2 still exist as scoped, or does it absorb what is left of Wave 1?

**Ruling: Wave 2 stands as scoped. It absorbs nothing, and nothing absorbs it. What D1 destroyed is
B5's *rationale* for the Wave 1 boundary, not the boundary itself — which is retained on a
different and better justification.**

Reasoning, in three parts.

**(a) What D1 actually consumed is narrow.** D1 changed exactly two fields of one named vector:
`content_vec.model` (`voyage-context-4` → `voyage-code-4`) and `content_vec.endpoint`
(`contextualized_embeddings` → `embeddings`) in `build_code_collection_profile()`. Both are members
of `fingerprint_payload()`, so the code collection's digest — and therefore its name — moved, and
`compare_collection_manifests()` now mismatches any pre-D1 code collection. That is the whole of it.

D1 did **not** touch: `INDEX_SCHEMA_VERSION` (deliberately left at `dope-context-v2` — bumping it
would have stranded docs collections too), `CODE_CHUNKER_VERSION` / `DOCS_CHUNKER_VERSION`, workspace
identity (`md5(workspace_path)` is unchanged; `identity_version` does not exist yet), the payload
schema, sparse vectors (there are none), or the docs profile.

Rev-2 Wave 2's content is precisely the set D1 left alone: `identity_version: 2`, project-scoped
collection naming, `wt_<id>` membership keys, relative `file_path`, `sparse_encoder_version`,
`sparse_avg_len`. **None of it was consumed.** The wave stands.

**(b) B5's cost argument is spent, and was thin when written.** B5 read: *"Manifest bump in Wave 1
forces a full re-embed before any benefit lands."* Three facts retire it:

* The design itself records (§2, worktrees) that Qdrant holds exactly **one** collection, belonging
  to an unrelated project: *"There is no live dopemux-mvp index to migrate — the redesign is a cold
  start."*
* ADR-226's `STRANDED_COLLECTIONS` section records **"Blast radius at the time of writing. Near
  zero."**
* The deployed service still resolves code embeddings to `voyage-code-3` from a runtime env var, so
  it has not adopted D1 at all.

There is no corpus whose re-embed a manifest bump could force. The cost that justified the boundary
does not exist.

**(c) The boundary is retained on a governance justification instead.** Under ADR-226 the lane opens
one file at a time, by amendment, and Alternative A (blanket `src/**`) was rejected precisely so
each opening stays reviewable. That mechanism is only affordable if an amendment can be judged
without reasoning about collection lifecycle. So:

> **Wave 1's "manifest-compatible" constraint is retained as a *reviewability* property, not a
> re-embed-cost property. A wave that cannot move any member of `fingerprint_payload()` is a wave
> whose ADR-226 amendment an operator can approve on the diff alone.**

**Corollary — this is what makes the ruling bite.** `fingerprint_payload()` includes
`chunker_version`. Therefore *any* file whose change alters chunk output is manifest-affecting and
cannot be in Wave 1, regardless of how small the diff is. That evicts **`code_chunker.py`** (which
Rev 2 put in Wave 1 in the same sentence that called Wave 1 manifest-compatible — R-2.1) and
**`document_processor.py`/C12** (which the handoff put in the *low-risk* A5 lane — R-3). Both go to
Wave 2, where the version bumps are expected and disclosed.

---

# 5. Wave 1's content: item-level state at `f7f0ed626`

Every row verified against the file, not against the plan. Struck items are done and need no work.

| Item | Where | State | Evidence |
|---|---|---|---|
| ~~Registry `voyage-code-4`~~ | `model_registry.py:68-77` | **DONE** | `3e878cc8d`, refined `982ecd107` |
| ~~`DEFAULT_CODE_MODEL` flip~~ | `model_registry.py:157` | **DONE** (this is D1 / §7 W5's code half) | `3e878cc8d` |
| ~~E3 rerank failure surfaced~~ | `voyage_reranker.py:29-33,180,258`; `server.py:1351-1353` | **DONE** (F-014) | pre-existing on main |
| ~~E11 bounded embed cache~~ | `voyage_embedder.py:188-201` | **DONE** (F-012) | pre-existing on main |
| ~~E21 request counted before ratio~~ | `voyage_embedder.py:78-79`; `contextualized_embedder.py:60-61` | **DONE** | pre-existing on main |
| ~~`truncation` public defaults → False~~ | `voyage_embedder.py:278,339` | **DONE** (A4) | `7f799306c` |
| ~~`SearchRequest` dead import~~ | `dense_search.py` | **DONE** (A4) | `7f799306c` |
| **R-5 residual: dataclass default** | `voyage_embedder.py:43` | **OPEN** — `EmbeddingRequest.truncation: bool = True` | latent; only prod constructor `:259` passes explicitly |
| **E1 retries** | `voyage_embedder.py:129`, `contextualized_embedder.py:109`, `voyage_reranker.py:112` | **OPEN, all three** — `AsyncClient(api_key=api_key)`, no `max_retries` | one exempt file, two blocked |
| **E16 limiter sleeps in the lock** | `voyage_embedder.py:140-154` | **OPEN** — `await asyncio.sleep(wait_seconds)` is inside `async with self._rate_limit_lock`; TPM unlimited | |
| **E10 unbounded tokenizer cache** | `model_tokenizer.py:57,111,122` | **OPEN** — plain `Dict`, no eviction, process-lifetime | blocked file |
| **E2/E4 degraded flags never set** | `token_budget.py:35-36` | **OPEN** — `budget_starvation` / `degraded_guarantee_applied` are declared and never assigned anywhere | blocked file |
| **E17 real token counts** | `token_budget.py:49` | **OPEN** — `ceil(len(utf-8)/3)` maxed against a lexical count. *Asymmetric, not total: **docs** payloads already carry a real Voyage token count (`docs_pipeline.py:208` writes `token_count`, sourced from `document_processor.py:507,541`), so E17 is **observable on `docs_search` today**. **Code** payloads carry no token key at all — `indexing_pipeline.py` writes none — so only that half waits on the CHUNKING wave.* | blocked file |
| **C1 exclude passthrough** | `server.py:981,1073` | **OPEN** — `:981` substitutes `["*test*","*__pycache__*"]`, *replacing* the dataclass default (`.venv`, `node_modules`, `.worktrees`, …); `:1073` passes the caller's `None` straight through | exempt file |
| **C6 per-file 2.0 s sleep** | `indexing_pipeline.py:484` | **OPEN** | exempt file |
| **C13 `filter_language`** | `server.py:1309-1310` | **OPEN** — writes `filter_by["language"]` while the payload stores the suffix. *Query-side canonicalisation is Wave 1; storing a canonical `language` in the payload is Wave 2.* | exempt file |
| **Registry `rerank-3` / `rerank-3-lite`** | `model_registry.py` | **OPEN** — absent | exempt file |
| **`voyageai>=0.5.0` runtime assert** | — | **OPEN** — `constraints.txt:2` pins `voyageai>=0.5.0,<0.6`, but the only runtime checks are indirect capability probes (`voyage_embedder.py:227-236`, `contextualized_embedder.py:249-250`) | exempt file |
| E7 raise-not-placeholder | `openai_generator.py:173,267` | **OPEN** | **not Wave 1** under Rev 2 → Wave 5 |
| E8 `reasoning_effort` + model | `openai_generator.py:59,86,141-142` — still `gpt-5-mini`, `max_completion_tokens=200`, no `reasoning_effort` | **OPEN** | **not Wave 1** → Wave 5 |
| E9 price from registry | `claude_generator.py:66-67,115` — hardcoded `0.25/1.25`, `claude-3-5-haiku-20241022` | **OPEN** | **not Wave 1** → Wave 5 |
| C12 `"\n"` literal | `document_processor.py:143,154,173` | **OPEN** | **not Wave 1** (R-3) → Wave 2 |

**`gpt-5-mini` shutdown is 2026-12-11.** E8 is on a clock even though D3 ruled the layer off by
default. Wave 5 has a deadline; it should not be scheduled last by default.

---

# 6. Re-cut wave plan

Waves are **named** as well as numbered, because this is the third numbering in play. Wave 1 aligns
across all three plans; later numbers do not. Crosswalk column is authoritative for tracing.

| # | Name | = §7 | = R2 | Manifest-affecting? | New exemptions |
|---|---|---|---|---|---|
| 1 | BEHAVIOUR | W1 (minus generators, chunkers) | W1 (minus `code_chunker.py`, plus `server.py`) | **No** — that is its definition (§4) | **5**, split A5a / A5b |
| 2 | CHUNKING | W2 (restored) + C12 | *none — orphaned by the re-cut* | Yes (`CODE_`/`DOCS_CHUNKER_VERSION`) | `code_chunker.py`, `document_processor.py`, new `chunk_sizing.py`, tests |
| 3 | IDENTITY + RETRIEVAL | W3 (identity half) + W4 | W2 | Yes (`identity_version`, payload schema, sparse) | `workspace.py`, `hybrid_search.py`, new `sparse_encoder.py`, new `identity.py`, tests |
| 4 | SYNC | W3 (sync half) | W3 | No (consumes W3's schema) | `sync/*`, `autonomous/*`, `docs_pipeline.py`, tests |
| 5 | CONTEXTGEN | W1 residue | W4 | No | `context/*`, tests |
| 6 | CLOSURE | W5 residue after D1 | *none — dropped by the re-cut* | No | none (docs/packets/deploy) |

File-disjointness holds pairwise across 1–6 with two sequencing constraints, both inherited:

* Waves 1, 3 and 4 each touch `server.py` (already exempt). **Sequential**, as Rev 2 required for
  W2/W3. Waves 2 and 5 are the only ∥-safe pair.
* Wave 2 must precede Wave 3: Wave 3's fingerprint v2 has to include the chunker versions Wave 2
  settles, or the collection is recreated twice.

Under the §4 ruling, file-disjointness is now doing double duty — it is what makes each wave's
ADR-226 amendment reviewable on its own. That is worth stating in each amendment's rationale.

## Wave 1, split by governance cost (not only by risk)

The handoff proposed splitting A5 by risk: bug-fix files separately from provider/generator files.
Under the governing Wave 1 the generators are not in scope at all (R-1), and one of the three files
it called low-risk is manifest-affecting (R-3). The split that survives is by **governance cost**:

**Wave 1a — source files all already exempt; needs one new *test* file.**
`voyage_embedder.py` (A4), `indexing_pipeline.py` (base), `server.py` (base), `model_registry.py` (A2).
Items: E1 on the flat embedder · E16 · R-5 dataclass residual · C1 · C6 · C13 (query-side) ·
`rerank-3`/`rerank-3-lite` registry rows · `voyageai>=0.5.0` runtime assert.

> Wave 1a is **not** zero-exemption, and it would be a false economy to pretend otherwise. Every
> file under `services/dope-context/tests/` is blocked except the two carved out for D1's profile
> work, neither of which is the right home for retry/limiter/exclude tests. Shipping 1a without a
> test file would be exactly the failure this programme already paid for: *"Six audit rounds and a
> green 123-test suite coexisted with a completely broken indexing path."* One new test file is the
> cheapest possible honest answer.

**Wave 1b — two leaf utility modules.** `model_tokenizer.py` (E10), `token_budget.py` (E2/E4/E17).
No vendor API surface, no manifest input, no callers outside the service.

**Wave 1c — two Voyage client modules.** `contextualized_embedder.py`, `voyage_reranker.py` — E1
retry parity only. These change retry and therefore billing behaviour against a live paid API. Same
"blast radius beyond this packet" class that A4 flagged for the truncation flip, so they get their
own approval.

**A5 therefore proposes 5 exemptions in 2 sub-amendments:**

* **A5a** — `tests/test_wave1_behaviour.py` (new), `src/utils/model_tokenizer.py`,
  `src/utils/token_budget.py`. Enables Waves 1a + 1b.
* **A5b** — `src/embeddings/contextualized_embedder.py`, `src/rerank/voyage_reranker.py`. Enables
  Wave 1c.

A5a alone is a coherent deliverable: Wave 1 still lands E1 on the flat path D1 actually uses, plus
every other open item except retry parity on the contextualized and rerank clients. **A5b is
recommended but severable.**

Versus the handoff's estimate: **5, not ~9** — and 3 of the 5 carry no vendor surface at all.

---

# 7. What this record produces

| Artifact | Path | Status |
|---|---|---|
| This record | `claudedocs/dope-context-wave-reconciliation-2026-09-04.md` | written |
| Wave 1 packet | `task-packets/dope-context/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007.md` | `AWAITING_AMENDMENT_A5` |
| ADR-226 A5 | appended to `docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md` | **PROPOSED** — no `APPROVED_BY`, regex **not** applied |
| Redesign pointer | Revision 3 stub in `claudedocs/dope-context-retrieval-redesign-2026-09-03.md` | written |

`src/dopemux/dcp/red_lane_rules.py` is **unchanged**. Every prior amendment landed its regex only
after operator approval; A5 follows that precedent.

---

# 8. Open items this reconciliation does not close

Carried forward from the handoff and packet 0004, unchanged and still open:

1. **D1 is inert in the deployed service.** `mcp-dope-context` sets
   `DOPE_CONTEXT_CODE_EMBED_MODEL=voyage-code-3` at runtime. Wave 6. Blocked on the container
   recreate, which is itself blocked on `tp-dmx-mcp-reset-recovery-001`'s 4 live worktrees.
2. **The whole-repo benchmark (~$6.82) is NOT_RUN**; `Bhl` needs `OPENAI_API_KEY` inside the
   container. Packet 0004 stays `DECISION_REQUIRED`. Wave 5's D3 gate depends on it.
3. **`.envrc.dopemux-mcp` is stale** (2026-07-29, predates `HOST_CODE_PARENT_DIR`); fix is
   `dopemux mcp init`, and the installed CLI is too old to have it.
4. **A14** retired as unrecoverable and substituted — **not** marked PASS. Packet 0004 carries a
   proposed ruling awaiting an operator decision.
5. **`consensus`** is NOT_RUN in the Required Chain; PAL has no container and `compose.yml` defines
   it with `build:`, so restoring it is a fleet operation.
6. **`voyage-code-3`'s registry limits may be wrong.** ADR-226 A2 notes its `32,000`/`120,000` pair
   matches the *contextualized* endpoint's limits exactly, raising the question of whether that row
   was populated from the wrong endpoint. Unresolved; touches `model_registry.py`, which is exempt,
   so Wave 1a *could* close it — deliberately not scoped in, because it needs a live probe.
7. **The guard is absent from the `pr-92` checkout** (R-6). Not this programme's to fix, but anyone
   relying on tool-level denial in this repo should know.

---

# 9. Validation status of this record

| Check | Result |
|---|---|
| `services/dope-context` suite at `f7f0ed626` | **PASS** — 124 passed, 1 skipped (re-run, 1.81 s) |
| DCP guard + red-lane scanner suites | **PASS** — 69 passed |
| Carve-out regex on `main` matches the handoff's quoted text | **PASS** — `red_lane_rules.py:45-63`, verbatim |
| Every §5 row verified against the file, not the plan | **PASS** |
| `chunker_version` ∈ `fingerprint_payload()` (basis of the §4 corollary) | **PASS** — `services/dope-context/src/index_profile.py:77-89` |
| `pr-92` checkout lacks the guard (R-6) | **PASS** — both paths confirmed absent |
| Whole-repo benchmark | **NOT_RUN** — unchanged; not this record's scope |
| Independent audit of this record (AGY/Gemini) | **NOT_RUN** |
| Any product code changed | **none** |
| Any red-lane rule changed | **none** |

Remaining uncertainty, stated: E17 is verifiable in Wave 1 on the **docs** path only, because
`docs_pipeline.py:208` already writes a real `token_count` into the payload; the **code** half stays
inert until the CHUNKING wave writes an equivalent key, and an implementer may reasonably defer that
half. The packet says so rather than presenting E17 as uniformly verifiable. C1's correct default set is
inferred from `indexing_pipeline.py:48`'s dataclass field; whether `server.py:981`'s `*test*`
exclusion is *also* wanted is a product question the packet flags rather than answers.
