---
id: TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007
title: Tp Dopecontext Wave1 Behaviour 0007
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-04'
last_review: '2026-09-04'
next_review: '2026-12-04'
prelude: Behaviour-only, manifest-compatible re-cut of dope-context Wave 1,
  gated on ADR-226 amendment A5.
---
# Task Packet: TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007

## Objective

Land the behaviour-only, manifest-compatible half of the dope-context
retrieval redesign: the correctness defects that do not move any member of
`VectorProfile.fingerprint_payload()`. This closes the remaining open items of
Wave 1 as re-cut by the reconciliation record, without touching chunking,
identity, retrieval schema, sync, or the LLM context-generation layer, all of
which move the manifest or sit outside the governing Wave 1 definition.

## Status

`AWAITING_AMENDMENT_A5`

Wave 1a's four source files — `voyage_embedder.py`, `indexing_pipeline.py`,
`server.py`, `model_registry.py` — are already exempt under the base ADR-226
carve-out, amendment A2, and amendment A4. But Wave 1a still cannot ship
without one new test file, `tests/test_wave1_behaviour.py`, which is not yet
exempt. Wave 1b needs two more files (`model_tokenizer.py`, `token_budget.py`)
and Wave 1c needs two more (`contextualized_embedder.py`,
`voyage_reranker.py`) — four additional files beyond the one Wave 1a needs, so
five files total remain gated. No implementation may begin on Wave 1b or
Wave 1c before ADR-226 amendment A5 is approved and its regex lands in
`src/dopemux/dcp/red_lane_rules.py`. Wave 1a's own test file also requires A5
(specifically the A5a sub-amendment) before it can be created; until then
Wave 1a cannot ship either, because a change without a driving test is exactly
the failure mode this programme has already paid for once.

## Provenance and supersession

- This packet implements Wave 1 (BEHAVIOUR) of
  `claudedocs/dope-context-retrieval-redesign-2026-09-03.md`, **as reconciled**
  by `claudedocs/dope-context-wave-reconciliation-2026-09-04.md`.
- The redesign document carries two Wave 1 definitions. Its Revision 2, §R2.2,
  states plainly that it supersedes the earlier §7 plan, and Revision 2.1 §7
  further adds `model_registry.py` to Wave 1's scope. This packet follows the
  governing Revision 2 (+2.1) definition, not §7's superseded one.
- Three rulings from the reconciliation record are applied on top of Revision
  2's own scope:
  - `code_chunker.py` is **evicted**. `CODE_CHUNKER_VERSION`
    (`services/dope-context/src/index_profile.py:35`) is a member of
    `VectorProfile.fingerprint_payload()`
    (`services/dope-context/src/index_profile.py:77-89`), so any
    change to that file that alters chunk output is manifest-affecting by
    construction and cannot sit in a wave defined as manifest-compatible.
  - `server.py` is **pulled in**, even though Revision 2 splits it across
    later waves. It is already exempt under the base carve-out, so bringing
    its C1/C13 items forward into Wave 1 costs no new amendment. This is safe
    only because the waves are sequential (see Sequencing below); a future
    parallel re-cut must not inherit this shortcut silently.
  - `voyage_reranker.py` is **reduced to E1 retry parity only**. Its other
    named item, E3 (silent dense-only fallback on rerank failure), is already
    closed on `main` — see "Already done" below.
- This packet delivers the remaining E-series scope of
  `TP-DOPECONTEXT-VOYAGE4-REPAIR-0002` (`AUTHORIZED_FOR_IMPLEMENTATION`,
  high-priority repairs F-004, F-006, F-007, F-010, F-017 and bounded items
  F-008-F-015). It does not close that packet; it is cited here as the origin
  of that scope, not superseded.
- This packet does not change `TP-DOPECONTEXT-VECTOR-SPACE-0004`'s
  `DECISION_REQUIRED` gate, and it does not depend on that packet's whole-repo
  benchmark (`Bhl`, NOT_RUN). Wave 1's items are independent of the D1/D3
  model decision.

## Already done — struck, with citations

Verified against the file at `origin/main` `f7f0ed626`, not against the plan.
These need no work in this packet.

| Item | Where | Evidence |
|---|---|---|
| ~~Registry `voyage-code-4`~~ | `model_registry.py:68-77` | `3e878cc8d`, refined `982ecd107` |
| ~~`DEFAULT_CODE_MODEL` flip~~ | `model_registry.py:157` | `3e878cc8d` |
| ~~E3 rerank failure surfaced~~ | `voyage_reranker.py:29-33,180,258`; `server.py:1351-1353,1380-1381` | F-014, pre-existing on `main` |
| ~~E11 bounded embed cache~~ | `voyage_embedder.py:188-201` | F-012, pre-existing on `main` |
| ~~E21 request counted before ratio~~ | `voyage_embedder.py:78-79`; `contextualized_embedder.py:60-61` | pre-existing on `main` |
| ~~`truncation` public defaults flipped to `False`~~ | `voyage_embedder.py:278,339` | `7f799306c`, ADR-226 A4 |
| ~~`SearchRequest` dead import deleted~~ | `dense_search.py` | `7f799306c`, ADR-226 A4 |

## Scope — Wave 1a (no new source exemptions)

Files: `src/embeddings/voyage_embedder.py`, `src/pipeline/indexing_pipeline.py`,
`src/mcp/server.py`, `src/embeddings/model_registry.py`, plus new
`tests/test_wave1_behaviour.py`.

- **R-5 residual.** `EmbeddingRequest.truncation: bool = True` at
  `voyage_embedder.py:43`. ADR-226 A4 flipped both public method defaults
  (`embed` at `:278`, `embed_batch` at `:339`) but not the frozen dataclass
  default. Latent today — the only production constructor
  (`voyage_embedder.py:259`) passes `truncation=` explicitly, and the other
  three call sites are in `tests/test_voyage_modernization.py` — but it is a
  fail-open default on a file the round-5 auditor already ruled must fail
  closed. Done means: the dataclass default is `False`.
- **E1 (flat path).** `voyage_embedder.py:129` builds
  `AsyncClient(api_key=api_key)` with no `max_retries`. Done means:
  `max_retries=5` with jittered backoff on 429/5xx.
- **E16.** `voyage_embedder.py:140-154`: `await asyncio.sleep(wait_seconds)`
  runs inside `async with self._rate_limit_lock`, so every concurrent caller
  serialises behind the sleep instead of behind the rate check alone. Only
  RPM is limited; TPM is not. Done means: the sleep moves outside the lock,
  and a TPM limiter is added from the registry's token-rate fields.
- **C1.** `server.py:981` substitutes `["*test*", "*__pycache__*"]`, which
  *replaces* rather than extends the dataclass default at
  `indexing_pipeline.py:48` (`.venv`, `node_modules`, `.worktrees`, `dist`,
  `build`, `site-packages`); `server.py:1073` passes the caller's `None`
  straight through instead of falling back to that default. Measured
  consequence in the audit: 220,846 files discovered versus roughly 3,072
  with the dataclass defaults applied. Done means: when the caller supplies
  no `exclude_patterns`, the dataclass default applies unmodified. **Flagged
  as a product question, not decided here:** whether `*test*` should also be
  excluded by default is a behaviour choice, not a bug fix, and this packet
  does not make that call.
- **C6.** `indexing_pipeline.py:484`: `await asyncio.sleep(delay_per_file)`,
  roughly 102 minutes of pure sleep over a 3,072-file corpus. Done means: the
  sleep is deleted.
- **C13.** `server.py:1309-1310` sets `filter_by["language"] = filter_language`
  while the payload stores the file suffix (e.g. `py`), so
  `filter_language="python"` can never match. Done means: query-side
  canonicalisation only — mapping the caller's language name to the stored
  suffix form before the filter is built. Storing a canonical `language`
  field in the payload itself is **CHUNKING-wave work**, not this packet's,
  because it changes chunk payloads and therefore the manifest.
- **Registry additions.** Add `rerank-3` and `rerank-3-lite` behind
  `DOPE_CONTEXT_ALLOW_PREVIEW_MODELS` (prices verified 2026-09-03: $0.05 and
  $0.02 per M tokens respectively). Add a `voyageai>=0.5.0` runtime assert:
  `constraints.txt:2` pins `voyageai>=0.5.0,<0.6`, but the only runtime checks
  today are indirect capability probes at `voyage_embedder.py:227-236` and
  `contextualized_embedder.py:249-250`.

## Scope — Wave 1b (needs ADR-226 A5a)

Files: `src/utils/model_tokenizer.py`, `src/utils/token_budget.py`.

- **E10.** `model_tokenizer.py`: `_cache` at `:57`, `:111`, `:122` is an
  unbounded plain dict, held for the process lifetime. Done means: mirror the
  already-proven eviction pattern at `voyage_embedder.py:188-201`
  (`_cache_response`) — expire, then evict oldest-first against a bound.
- **E2/E4.** `token_budget.py:35-36` declares `budget_starvation` and
  `degraded_guarantee_applied` and never assigns either anywhere in the file.
  Done means: both are actually set on the paths they are meant to signal.
- **E17.** `token_budget.py:49` estimates tokens as the larger of
  `ceil(len(text.encode("utf-8")) / 3)` and a lexical count, rather than
  reading a real count. The limit here is **asymmetric, not total**:
  - **Docs payloads already carry a real Voyage token count.**
    `docs_pipeline.py:208` writes `token_count` into the point payload,
    sourced from `document_processor.py:507,541`. E17 is therefore a real,
    testable Wave 1 improvement on the `docs_search` budgeting path today.
  - **Code payloads carry no token key at all.** `indexing_pipeline.py`
    writes none, so that half is prefer-payload plumbing which stays inert
    until the CHUNKING wave writes an equivalent key.

  Done means: `token_budget` prefers a payload-supplied count where one
  exists and falls back to the labelled heuristic where it does not.
  Deferring the code half to CHUNKING is legitimate; deferring both would
  give up an improvement that is available now.

## Scope — Wave 1c (needs ADR-226 A5b; severable)

Files: `src/embeddings/contextualized_embedder.py:109`,
`src/rerank/voyage_reranker.py:112`. E1 retry parity only — the same
`max_retries`/backoff fix as Wave 1a's flat-path E1, applied to these two
clients.

A5b is recommended but severable from A5a. Approving A5a alone still lands E1
on the flat embedding path D1 actually uses in production, plus every other
open item in this packet except retry parity on the contextualized and
rerank clients.

## Explicitly out of scope

- `preprocessing/code_chunker.py` — manifest-affecting:
  `CODE_CHUNKER_VERSION`
  (`services/dope-context/src/index_profile.py:35`) is a member of
  `fingerprint_payload()`
  (`services/dope-context/src/index_profile.py:77-89`). Any behaviour
  change here bumps the manifest. → CHUNKING wave.
- `preprocessing/document_processor.py` / C12 (`:143`, `:154`, `:173` emit
  literal `\n` two-character sequences instead of real newlines) — manifest-
  affecting for the same reason, via `DOCS_CHUNKER_VERSION`
  (`services/dope-context/src/index_profile.py:36`). Fixing it changes the
  extracted text, hence the chunk content, hence the embeddings, and would
  strand every existing docs
  collection — the exact thing D1 deliberately left alone. → CHUNKING wave.
- `context/openai_generator.py`, `context/claude_generator.py` (E7, E8, E9)
  — not in the governing Wave 1 definition; D3 ruled the LLM context layer
  off by default. → CONTEXTGEN wave. **Record explicitly:** `gpt-5-mini`
  shuts down 2026-12-11, so that wave carries a hard deadline and should not
  be scheduled last by default.
- The container recreate and the live `mcp-dope-context` service's
  `DOPE_CONTEXT_CODE_EMBED_MODEL=voyage-code-3` runtime override — deployment
  work, not behaviour work. → CLOSURE wave.
- `voyage-code-3`'s possibly-wrong registry limits (ADR-226 A2 notes its
  `32,000`/`120,000` pair matches the *contextualized* endpoint's limits
  exactly, not the flat endpoint's). `model_registry.py` is exempt, so
  Wave 1a *could* close this, but it needs a live API probe to confirm before
  changing a shipped limit — deliberately not scoped into this packet.

## Allowed Files

- `task-packets/dope-context/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007.md` — this
  packet.
- `claudedocs/dope-context-wave-reconciliation-2026-09-04.md` — the
  reconciliation record this packet implements.
- `docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md` — the governing
  ADR. Editable only to record an amendment's outcome; the carve-out regex in
  `src/dopemux/dcp/red_lane_rules.py` lands only on operator approval of A5,
  as A2, A3 and A4 each did.
- `services/dope-context/src/embeddings/voyage_embedder.py` — authorized by
  ADR-226 amendment **A4**.
- `services/dope-context/src/pipeline/indexing_pipeline.py` — authorized by
  the **base** ADR-226 carve-out.
- `services/dope-context/src/mcp/server.py` — authorized by the **base**
  ADR-226 carve-out.
- `services/dope-context/src/embeddings/model_registry.py` — authorized by
  ADR-226 amendment **A2**.
- `services/dope-context/tests/test_wave1_behaviour.py` (new) —
  **PENDING A5a. Not editable until approved.**
- `services/dope-context/src/utils/model_tokenizer.py` —
  **PENDING A5a. Not editable until approved.**
- `services/dope-context/src/utils/token_budget.py` —
  **PENDING A5a. Not editable until approved.**
- `services/dope-context/src/embeddings/contextualized_embedder.py` —
  **PENDING A5b. Not editable until approved. Severable from A5a.**
- `services/dope-context/src/rerank/voyage_reranker.py` —
  **PENDING A5b. Not editable until approved. Severable from A5a.**

No path outside this list may be edited. In particular, `code_chunker.py`,
`document_processor.py`, `context/openai_generator.py`,
`context/claude_generator.py`, and everything under `services/dope-context/`
not named above remain hard-blocked by `src/dopemux/dcp/red_lane_rules.py`.

## Acceptance Criteria

Every criterion reports PASS, FAIL, or NOT_RUN. NOT_RUN is never collapsed
into PASS.

- **Suite green.** Baseline is **124 passed, 1 skipped** at `f7f0ed626`
  (independently re-run in the reconciliation record). The suite must not
  regress below that baseline after Wave 1 lands.
- **Guard suites green.** Baseline **69 passed**
  (`test_dcp_surface_guard.py` + `test_dcp_0005_red_lane_scanner.py`).
- **No member of `fingerprint_payload()` changes.** This is Wave 1's defining
  constraint, and it must be asserted by a test, not by inspection: assert
  that `build_code_collection_profile().profile_digest` and
  `build_docs_collection_profile().profile_digest` are byte-identical before
  and after Wave 1's changes. This is the criterion that makes the wave
  reviewable on its diff alone, per the reconciliation's §4 ruling.
- **Every open item has a test that actually drives the changed code path**
  — not a substring scan of the source. Specifically:
  - a test that awaits `_check_rate_limit` under contention and proves the
    rate-limit lock is not held across the sleep (E16);
  - a test that drives the retry path against a mocked 429 response and
    observes an actual retry with backoff (E1, all applicable clients);
  - a test that calls the discovery path with no `exclude_patterns` argument
    and asserts the dataclass default from `indexing_pipeline.py:48` is what
    actually applied (C1).
- **Every new assertion is mutation-tested.** For each new test, introduce
  the defect it is meant to catch and confirm the test fails; then restore
  the fix and confirm it passes. Assert the mutation actually landed — a
  `str.replace` that silently no-ops fails invisibly, and a bad experiment
  looks exactly like a weak test.
- **Source-scanning tests use AST, not substring matching.** Any test that
  inspects source for a pattern (e.g. "does this constructor pass
  `truncation=`") parses the file and checks the syntax tree, not a
  string search.

## Execution constraints

Carried from the reconciliation record §2 R-6 and the programme's standing
rules. All apply for the lifetime of this packet.

- **Implement from a worktree off `origin/main`, never from the main
  checkout.** The main working copy at `/Users/hue/code/dopemux-mvp` is on
  branch `pr-92`, whose tree contains neither
  `.claude/hooks/dcp_surface_guard.py` nor `src/dopemux/dcp/red_lane_rules.py`,
  and whose `.claude/settings.json` registers only `check_energy.sh` on a
  matcher that matches no file-writing tool. DCP-RED-MERGE-SEAM-0001 is
  therefore **absent, not stale**, in that checkout: an Edit under
  `services/dope-context/` would be silently permitted there. **Absence of a
  denial is not authorization.**
- Never route around the red lane with Bash or a heredoc — that is the M11
  precedent violation ADR-226 already records as Alternative C, rejected.
- Never `--no-verify`.
- Never `dopemux mcp down --services dope-context` (or any other single
  service) — it degrades to a full-fleet `rm -f -s -v`; use `up`.
- Report PASS / FAIL / NOT_RUN for every check; never collapse NOT_RUN into
  PASS.

## Sequencing

Wave 1 (this packet) must precede CHUNKING and IDENTITY+RETRIEVAL, because
Waves 1, 3, and 4 of the re-cut plan all touch `server.py` and are therefore
sequential, not parallel. CHUNKING must in turn precede IDENTITY+RETRIEVAL:
IDENTITY+RETRIEVAL's fingerprint v2 must include the chunker versions
CHUNKING settles, or the collection would be recreated twice.
