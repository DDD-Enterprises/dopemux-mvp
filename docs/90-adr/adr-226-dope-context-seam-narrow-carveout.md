---
id: ADR-226
title: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for the dope-context benchmark harness and packet-0004 files
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-03'
last_review: '2026-09-03'
next_review: '2026-12-03'
prelude: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for services/dope-context/eval/ and the three service files in TP-DOPECONTEXT-VECTOR-SPACE-0004's Allowed Files (adr) for dopemux documentation and developer workflows.
status: accepted
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - ADR-224
    - TP-DOPECONTEXT-VECTOR-SPACE-0004
    - TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
---
# ADR-226: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for the dope-context benchmark harness and packet-0004 files

════════════════════════════════════════════════════════════

## Status

* Accepted — drafted 2026-09-03 in an agent session; operator approved the
  same day ("Approve — land both commits") after reviewing the validated
  diff. The guard change lands in the commit that carries this ADR.

## Date

* 2026-09-03

## Owners

* Supervisor (DDD-Enterprises), executed by Claude (agent session) under
  `TP-DOPECONTEXT-VECTOR-SPACE-0004`, governance amendment 2026-09-03.

────────────────────────────────────────────────────────────

## Context

`DCP-RED-MERGE-SEAM-0001` is a tool-enforced, PreToolUse hard-deny red lane
(`.claude/hooks/dcp_surface_guard.py`, backed by
`src/dopemux/dcp/red_lane_rules.py::FORBIDDEN_PATHS`) that blocks inline
Edit/Write/NotebookEdit calls to a fixed list of paths regardless of
task-packet authorization. One entry is a blanket pattern covering the
entire dope-context service:

```python
re.compile(r"^services/dope-context/.*$"),
```

Provenance, as observed on 2026-09-03:

* Added 2026-06-04 in commit `4a120ff8d` ("TP-DCP-0005 red-lane scanner"),
  together with sibling blankets for `services/task-orchestrator/`,
  `services/dopecon-bridge/`, `services/working-memory-assistant/`,
  `docker/mcp-servers-source/conport/` and `src/conport/`. Neither the
  commit message nor the packet artifacts found in `task-packets/` record a
  rationale for the `services/*` entries specifically. The grouping is
  consistent with "DCP tooling must not mutate MCP-server services", but
  that intent is **UNRECORDED** and this ADR does not assert it.
* Identical on `origin/main`; no environment or allowlist override exists in
  the hook.
* Broader than the seam's documented invariant: `docs/03-reference/dcp/README.md`
  describes `DCP-RED-MERGE-SEAM-0001` only in terms of
  `src/dopemux_pr_merge_specialist/queue_drain.py`'s `execute=True` seam and
  `scripts/batch_resolve_and_merge.py`. ADR-224 already noted this
  documented-vs-actual drift and left it unreconciled; this ADR does the
  same (see Non-goals).
* Prior art both ways: `claudedocs/m11-red-lane-blocker-2026-07-29.md`
  hit the `services/task-orchestrator/` blanket and correctly ruled "do not
  route around" (no Bash-around-the-hook, no `--no-verify`); ADR-224 /
  `TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R` Phase A then established the
  reviewed, ADR-anchored, negative-lookahead carve-out as the sanctioned
  way to narrow a blanket entry.

The concrete trigger: `TP-DOPECONTEXT-VECTOR-SPACE-0004` (status
`DECISION_REQUIRED`, budget approved) is a benchmark-gated packet whose
Allowed Files include three service files —
`services/dope-context/src/pipeline/indexing_pipeline.py`,
`services/dope-context/src/mcp/server.py`,
`services/dope-context/tests/test_vector_space_invariants.py` — and, by
operator-approved amendment on 2026-09-03, the offline benchmark harness
directory `services/dope-context/eval/**`. Every one of those paths is
hard-blocked by the blanket entry, so neither the harness's baseline commit
nor the packet's implementation half can proceed via the normal tool path.
The block was observed live earlier in the same session: the hook denied
an Edit under `services/dope-context/eval/` (the pre-commit
trailing-whitespace fix in `results-2026-09-03.md`; the hook writes no
denial log, so the exact path is reconstructed from the pre-commit
finding, not from a record). A programmatic `surface_guard_block` probe
then confirmed the block for `services/dope-context/eval/run_eval.py` and
`services/dope-context/src/mcp/server.py`. No workaround was attempted.

Disclosure: the harness files under `services/dope-context/eval/` already
existed, untracked, before this ADR was drafted. They were created earlier
the same day by a delegated sub-agent through a path the hook does not
guard (the hook covers Edit/Write/NotebookEdit only). Exactly how is
UNKNOWN. By the M11 standard that was a route-around; the files were
therefore **not committed** until this carve-out is approved, and their
content is subject to the same review as any other packet-0004 output.

Pain points:

* The blanket pattern blocks *every* dope-context edit, including a
  benchmark harness that reads `src/` read-only and writes only throwaway
  `eval_`-prefixed Qdrant collections.
* The retrieval redesign this packet gates (Waves 1–4,
  `claudedocs/dope-context-retrieval-redesign-2026-09-03.md`) cannot be
  implemented through the governed tool path at all while the blanket
  stands.
* Widening the seam wholesale (removing the `services/dope-context/` entry)
  would silently lift the lane for the whole service, including the MCP
  server entrypoint and Dockerfile, without the per-file review the seam's
  own message demands.

Constraints:

* This ADR authorizes a **path-level** exemption only. `TEXT_RULES`
  content scanning (`red_lane_scanner.py`) must remain fully active on the
  carved-out paths.
* Only paths already named in packet 0004's Allowed Files are exempted. No
  other file under `services/dope-context/` becomes editable.
* The hook's primary path reading (`_repo_relative`) is lexical — it does
  not resolve `..` — so a directory-scoped exemption must be paired with an
  explicit traversal guard. Since the independent audit (F-001, see
  "Independent audit" below) the block tier also evaluates a realpath
  reading and — since round 2, F-001-A — a case-folded reading of the
  whole repo-relative path, not just the root; the traversal guard stays
  as defence-in-depth.
* The change must not disturb the sibling service blankets or the
  fallback ⊆ live sync invariant.

────────────────────────────────────────────────────────────

## Decision

Replace the blanket `services/dope-context/` forbidden-path pattern in
`FORBIDDEN_PATHS` with a single regex that forbids everything under
`services/dope-context/` **except** (a) the `eval/` directory subtree and
(b) the three exact packet-0004 files, implemented via negative lookahead
anchored to the literal path (not a prefix or substring match), plus a
companion pattern that re-blocks any `..` segment anywhere under the
service so the directory exemption cannot be used to traverse out of
`eval/`:

```python
re.compile(
    r"^services/dope-context/"
    r"(?!eval/)"
    r"(?!src/pipeline/indexing_pipeline\.py$)"
    r"(?!src/mcp/server\.py$)"
    r"(?!tests/test_vector_space_invariants\.py$)"
    r".*$"
),
re.compile(r"^services/dope-context/(?:.*/)?\.\.(?:/|$)"),
```

Invariants:

* Exempted from the path-level block: every path under
  `services/dope-context/eval/` (any depth), and exactly
  `services/dope-context/src/pipeline/indexing_pipeline.py`,
  `services/dope-context/src/mcp/server.py`,
  `services/dope-context/tests/test_vector_space_invariants.py`.
* Still hard-blocked: every other path under `services/dope-context/`,
  including the rest of `src/` and `tests/`, `Dockerfile`,
  `constraints.txt`, near-miss names (`evaluation.py`, `server.py.bak`),
  same-named files in other directories (`src/mcp/sub/server.py`,
  `src/server.py`), the bare name `services/dope-context/eval` (not the
  directory), and any path containing an exact `..` segment
  (`eval/../src/mcp/server.py`, `../dope-context/...`).
* Sibling blankets (`services/task-orchestrator/`,
  `services/dopecon-bridge/`, `services/working-memory-assistant/`,
  `docker/mcp-servers-source/conport/`, `src/conport/`) are unchanged.
* `TEXT_RULES` scanning in `red_lane_scanner.py` continues to apply to all
  changed files, including the carved-out paths. A forbidden-text match
  (e.g. `gh pr merge`) inside `eval/run_eval.py` still yields a `BLOCKED`
  scan via `MERGE_SEAM_VIOLATION`, independent of the path carve-out.
* `_FALLBACK_COMPILED` in `.claude/hooks/dcp_surface_guard.py` is
  unchanged: it never included a `services/*` entry, so
  `tests/test_dcp_surface_guard.py::test_fallback_patterns_covered_by_live_rules`
  continues to hold without modification.
* No symlinks may exist under `services/dope-context/eval/` (a symlink
  inside the exempted directory could write through to a blocked path). A
  filesystem test pins this, and since audit F-001 the hook also resolves
  an existing symlink at edit time and blocks when its target is a blocked
  path.

Non-goals:

* This ADR does not authorize the content of any edit. What may be written
  to the exempted paths is governed by packet 0004 (and, for the harness,
  its 2026-09-03 amendment) — including its `DECISION_REQUIRED` gate on
  the implementation half.
* This ADR does not carve out `services/dope-context/src/**` for the
  retrieval redesign's Waves 1–4. Each wave's packet must enumerate exact
  files, and those files must be added here by a further ADR amendment
  using the same mechanism. A blanket `src/**` exemption was considered and
  rejected (Alternative A).
* This ADR does not reconcile the documented-vs-actual scope drift of
  `DCP-RED-MERGE-SEAM-0001` (the README still undercounts the seam's
  blocked-path list; the `services/*` entries have no recorded rationale).
  That remains a separate governance cleanup, as ADR-224 already noted.

────────────────────────────────────────────────────────────

## Alternatives Considered

**A. Remove the `services/dope-context/` entry from `FORBIDDEN_PATHS`
entirely, or exempt `src/**`.** Pros: unblocks Waves 1–4 in one step, no
regex complexity. Cons: lifts the lane for the MCP server entrypoint,
Dockerfile, embedder and search modules without per-file review, and
would be the first service-wide lift of a `services/*` blanket with no
recorded rationale to weigh it against. Rejected as far broader than the
reviewed need; the per-wave amendment path is the cost of keeping the
seam meaningful.

**B. Keep the blanket; relocate the harness to `tools/dope-context-eval/`
and defer `src/` edits.** Pros: zero governance change today; the
baseline could be committed immediately. Cons: leaves packet 0004's own
Allowed Files unexecutable through the governed path, moves the harness
away from the code it benchmarks (the packet amendment deliberately homed
it under the service), and only postpones this ADR to the first wave.
Rejected by operator ruling on 2026-09-03 in favor of the ADR-224 pattern.

**C. Continue writing through an unguarded path (Bash/heredoc), as the
harness files were originally created.** Pros: none that survive review.
Cons: this is exactly the route-around `claudedocs/m11-red-lane-blocker-2026-07-29.md`
ruled out and the seam's own message forbids; it also leaves the hook
lying about what is editable. Rejected — and the pre-existing harness
files are disclosed above rather than quietly committed.

**D. Runtime allowlist file read by the guard.** Rejected for the reasons
given in ADR-224 Alternative C: a mutable configuration surface for a
hard-deny boundary loses the ADR-reviewed intent the moment it is edited
without a fresh ADR.

────────────────────────────────────────────────────────────

## Propagation (observed 2026-09-03)

Hook H1 loads `FORBIDDEN_PATHS` from the checkout that `CLAUDE_PROJECT_DIR`
points at. In the authoring session that checkout was the main working
copy (detached at `e07ff3efc`), whose rules predate this ADR, so an Edit
to `services/dope-context/eval/results-2026-09-03.md` was still denied
after the carve-out landed on the branch (reproduced: main's dispatcher
exits 2 with a deny payload; the branch's dispatcher exits 0). This ADR
therefore takes effect for a given session only once its rules are the
ones that session's hook imports — i.e. after this branch merges, or when
the session is rooted at a checkout of this branch. One operator-authorized
exception was made in the authoring session: with the carve-out already
approved and landed on the branch, the operator explicitly authorized a
single Bash-side line repair of `results-2026-09-03.md:49` (restoring the
`OPENAI_API_KEY` token that a redaction pass had stripped) so that the
carve-out commit would not ship known-wrong content. One further
operator-authorized Bash-side change under the seam followed in a successor
commit: `git mv` of that results file out of `eval/` plus the matching
convention update in `services/dope-context/eval/README.md` (see the
relocation note below). No other Bash-side edits under the seam were made.

Relocation note (2026-09-03): the results file now lives at
`claudedocs/dope-context-eval-results-2026-09-03.md`. The repository's
`markdown-location-guard` pre-commit hook (run in CI, not by the local
`.githooks/pre-commit`, which only runs `scripts/preflight.sh`) rejects any
`.md` outside the canonical docs roots, so eval result write-ups must live
under `claudedocs/` or `docs/` regardless of this carve-out; the historical
path references above are kept as written.

## Independent audit (2026-09-03)

Route: AGY (`agy --model gemini-3.1-pro-high --output-format json
--print=...`), Tier-1 route #1, on frozen head `720991c41`; the CLI log
records the requested model propagated to the backend
(`promptLength=211583, model="gemini-3.1-pro-high"`). Verdict on that
head: **FAIL**, one BLOCKER.

* **F-001 CONFIRMED (pre-existing, fixed here).** `_repo_relative` in
  `.claude/hooks/dcp_surface_guard.py` was purely lexical, so
  `<root>/../<worktree>/<blocked>`, a case-variant root (`/USERS/...` is
  the same file on macOS's default filesystem) and a symlink alias of the
  root all produced strings no `^`-anchored pattern matched — for every
  red-lane path, `queue_drain.py` included. Reproduced programmatically
  before the fix. Fix: `_repo_relative_candidates` evaluates the raw,
  realpath and case-folded-root readings and the block tier denies if any
  matches; the same candidates feed the warn tier (the round-2 fix below
  extends the fold to the intra-repo path). Seven tests pin the
  bypass forms plus the two things that must keep working (new file under
  `eval/`, paths outside the root).
* **F-002 REJECTED.** Claimed the packet-0004 diff was absent from the PR;
  the prompt contained all 11 diff headers including
  `task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md`.
* **F-003 REJECTED.** Claimed the traversal regex matches names ending in
  `..`; it matches only an exact `..` segment (`something..`, `..foo`,
  `a../b.py` do not match — verified).
* **F-004** (test coverage for the bypass forms) is subsumed by the F-001
  fix.
* Auditor's one unverifiable claim (README's `--corpus` guard) is
  verified at `services/dope-context/eval/run_eval.py:662`.

**Round 2 (delta re-audit of F-001, same route and model, head
`1d87cb732`): `CLOSED_WITH_RISKS`, one HIGH residual, F-001-A.** The
round-1 fix folded case only on the root prefix; on macOS's default
filesystem `SERVICES/dope-context/src/search/hybrid_search.py` and
`src/dopemux_pr_merge_specialist/QUEUE_DRAIN.py` are the protected files
but matched no `^`-anchored, case-sensitive pattern. Reproduced at
`1d87cb732`; fixed in `a4f86c48c`: `_repo_relative_candidates` now yields
the exact-case reading first and a case-folded reading of the entire
repo-relative path second, and any candidate matching the lane denies.
`eval/**` still passes in exact case; a case-variant of the carve-out
itself (`EVAL/run_eval.py`) is denied fail-closed. Eight further tests
(37 total); scanner suite unchanged (32). Two errata in the round-2
prompt are recorded in the bundle's `PROVENANCE.json` — the prompt
misnamed the top-level `services/dope-context/README.md` as carved out
(it is not; it was and is denied), and the auditor's example path
`src/mcp/server.py` is not in the lane in this repo, so the class was
reproduced with the two specimens above.

**Round 3 (delta re-audit of F-001-A, same route and model, head
`9ef316d1b` — hook, tests and rules byte-identical to `a4f86c48c`):
`CLOSED`, zero residual risks, zero regressions.** The auditor confirmed
the case-folded candidate closes the intra-repo case-variant class, that
a case-variant of the carve-out (`EVAL/`) still denies because the
exact-case candidate fails the negative lookahead, and enumerated
thirteen bypass forms considered (unicode case, NFC/NFD, symlinks inside
`eval/`, hard links, `./` and `//` segments, Windows separators, 8.3
names, URL encoding, the empty-candidate fallback). F-001 is therefore
auditor-closed as of round 3; the round-2 remediation record's only
remaining `NOT_RUN` bucket is CI on PR #1304.

The proof bundle, raw auditor output and the re-audit on the post-fix
frozen head live under `proof/pr_merge/embedded-audit/pr-1304/`.

## Consequences

* **Easier**: the benchmark harness can be committed and iterated, and
  packet 0004's three service files can be edited (once its
  `DECISION_REQUIRED` gate clears) via the normal Edit/Write tool path.
* **Harder/unchanged**: every other dope-context path is exactly as hard
  to edit as before. Waves 1–4 each require an ADR amendment naming exact
  files before implementation — deliberate friction.
* **Testing**: focused tests at both layers pin the boundary.
  Hook layer (`tests/test_dcp_surface_guard.py`): six carved-out positives
  across Edit/Write/NotebookEdit; thirteen still-blocked negatives covering
  sibling `src/` files, `tests/conftest.py`, `Dockerfile`, near-miss names,
  nested/same-named files, the bare `eval` name, and three traversal
  forms; one sibling-services-untouched check; one no-symlinks filesystem
  check. Scanner layer (`tests/dcp/test_dcp_0005_red_lane_scanner.py`):
  carve-out clean, siblings-still-blocked (including a traversal and a
  sibling service), and a `TEXT_RULES`-still-active proof on
  `eval/run_eval.py`.
* **Failure modes removed**: none — a narrowing exemption, not a removed
  check.
* **Failure modes introduced**: one considered and closed. A directory
  exemption plus a lexical normalizer would have allowed
  `eval/../src/x.py`; the companion `..`-segment pattern and its tests
  close it. The independent audit then found the pre-existing, wider
  form of the same weakness (F-001) and it is fixed in this change — see
  "Independent audit" below. Residual: a symlink created under `eval/`
  between the hook check and the write (TOCTOU) is caught only by the
  filesystem test. Accepted and pinned as a stop condition in the packet
  amendment.

────────────────────────────────────────────────────────────

## Migration Strategy

* Step 1 (this ADR): land the narrowed `FORBIDDEN_PATHS` regex, the
  traversal guard, and the focused tests, together with the packet-0004
  governance amendment, as a single commit on the redesign branch
  (`claude/dope-context-retrieval-redesign-2026-09-03`) **after operator
  approval**. No `src/` or `tests/` content under the service changes in
  this step.
* Step 2 (packet 0004, already authorized by its amendment): commit the
  benchmark harness under `services/dope-context/eval/` and run the
  baseline.
* Step 3 (packet 0004, gated on `DECISION_REQUIRED` clearing): edit the
  three named service files per the chosen direction.
* Step 4 (future, per wave): amend this ADR's regex with each wave's exact
  files as their packets are authored and authorized.

Rollback (this ADR only): `git revert <this-commit-sha>` restores the
blanket `services/dope-context/.*` block and removes the tests. Nothing
pushed at draft time, so no remote state to unwind.

────────────────────────────────────────────────────────────

## Verification

* Tests added: `tests/test_dcp_surface_guard.py` (4 new functions,
  table-driven, plus 7 F-001 bypass tests) and
  `tests/dcp/test_dcp_0005_red_lane_scanner.py` (3 new).
* Commands to run:
  `PYTHONPATH=src python -m pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
* Expected signals: full pass, including the pre-existing ADR-224 tests
  and `test_fallback_patterns_covered_by_live_rules` (unaffected).
* Live check: `surface_guard_block("Edit", {"file_path": <root>/services/dope-context/eval/run_eval.py}, <root>)`
  returns `None`; the same call for
  `services/dope-context/src/search/hybrid_search.py` and for
  `services/dope-context/eval/../src/mcp/server.py` returns a
  `DCP-RED-MERGE-SEAM-0001` block message.

────────────────────────────────────────────────────────────

## Notes

* ADR numbering: ADR-225 is already used on two unmerged branches
  (`adr-225-conport-append-only-retire.md` on `938ecfc44`'s branch and the
  pr-readiness-invalidation carve-out on PR #1287's `c59ee17bf`). This ADR
  takes 226 to avoid a third collision; the existing double-booking of 225
  is noted for the governance cleanup above.
* Waves 1–4 of the retrieval redesign remain blocked at the lane until
  their packets enumerate files and this ADR is amended — tracked in the
  packet-0004 governance amendment as a stop condition, not a TODO.
* Related: `TP-DOPECONTEXT-VECTOR-SPACE-0004` (Allowed Files + 2026-09-03
  amendment), ADR-224 (mechanism precedent),
  `claudedocs/m11-red-lane-blocker-2026-07-29.md` (do-not-route-around
  precedent).

────────────────────────────────────────────────────────────

## Amendment A2 — extend the carve-out to the two files the D1 implementation actually needs (2026-09-04)

```text
AMENDMENT_ID=ADR-226-A2
AMENDMENT_STATUS=APPROVED
APPROVED_BY=operator (session 3d420c77, 2026-09-04)
APPROVAL_SCOPE=path-level exemption as specified below; the content change is
  authorized only as written under "What lands with this amendment"
COMPANION_PACKET_AMENDMENT=TP-DOPECONTEXT-VECTOR-SPACE-0004 amendment A2 (same date)
ADDS_EXEMPTIONS=services/dope-context/src/index_profile.py, services/dope-context/src/embeddings/model_registry.py
AUTHORIZES_CONTENT_EDITS=NO (path-level only; TEXT_RULES scanning unchanged)
WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED
```

### Why

The Wave 0 benchmark (completed 2026-09-04, results in
`claudedocs/dope-context-eval-results-2026-09-03.md`, commit `4561980fc`)
settled D1 on measurements: code `content_vec` moves to `voyage-code-4` on
the flat `embeddings` endpoint. Implementing that decision requires editing
two files that the original carve-out does not exempt, and that packet 0004's
Allowed Files did not name:

1. **`services/dope-context/src/index_profile.py`** —
   `build_code_collection_profile()` (lines 245-292) is the canonical writer
   of `content_vec`'s `model` and `endpoint`. The original packet named
   `src/pipeline/indexing_pipeline.py` and `src/mcp/server.py`, but neither
   sets those fields: the pipeline consumes an already-built profile, and
   `search_code` already queries with `content_profile.model`
   (`server.py:1237`), so the query side needs no edit at all. The two
   originally-exempted service files are, for D1, the wrong files.
2. **`services/dope-context/src/embeddings/model_registry.py`** —
   `MODEL_SPECS` does not contain `voyage-code-4`, and `_vector_profile()`
   validates every model through `get_model_spec()` and
   `validate_dimension()`, both of which raise on an unregistered name. The
   target model must be registered before any profile can name it.

### Exact regex change

In `src/dopemux/dcp/red_lane_rules.py`, the ADR-226 carve-out entry gains two
negative lookaheads (additions marked `+`); everything else is unchanged:

```python
    re.compile(
        r"^services/dope-context/"
        r"(?!eval/)"
        r"(?!src/pipeline/indexing_pipeline\.py$)"
        r"(?!src/mcp/server\.py$)"
+       r"(?!src/index_profile\.py$)"
+       r"(?!src/embeddings/model_registry\.py$)"
        r"(?!tests/test_vector_space_invariants\.py$)"
        r".*$"
    ),
```

The companion traversal-refusal entry
(`^services/dope-context/(?:.*/)?\.\.(?:/|$)`) is unchanged and continues to
cover the newly-exempted paths, so `eval/../src/index_profile.py` and
`src/embeddings/../search/dense_search.py` stay blocked.

### Invariants preserved

* Anchored `$` on both new lookaheads — `index_profile.py.bak`,
  `index_profile.py.orig`, and `src/embeddings/model_registry.py.tmp` remain
  blocked, as do same-named files in other directories
  (`src/search/index_profile.py` would still be blocked, since the lookahead
  is rooted at `services/dope-context/`).
* Whole-path case-folding from the F-001-A fix (commit `a4f86c48c`) applies
  unchanged, so `SRC/INDEX_PROFILE.PY` is still denied fail-closed.
* `TEXT_RULES` content scanning in `red_lane_scanner.py` is untouched; the
  exempted paths are exempt from the *path* block only, not from content
  rules.
* Everything else under `services/dope-context/src/**` — including
  `search/dense_search.py`, `search/hybrid_search.py`,
  `preprocessing/code_chunker.py`, and `pipeline/docs_pipeline.py` — remains
  hard-blocked.

### What lands with this amendment

Path-level exemption only. The authorized content change, specified here so
the diff is reviewable before the lane opens:

* `model_registry.py`: add a `voyage-code-4` entry to `MODEL_SPECS`
  (`endpoint="embeddings"`, `default_dimension=1024`, standard
  `_DIMENSIONS`, `price_per_million_tokens=0.12`); flip
  `DEFAULT_CODE_MODEL` from `"voyage-code-3"` to `"voyage-code-4"`; mark the
  superseded `voyage-code-3`, `voyage-context-3`, and `voyage-3-lite` entries
  `legacy=True`.

  **Limits — live-measured 2026-09-04, do not copy `voyage-code-3`'s values.**
  Two probes against the real API (total billed $0.04):

  * `per_input_tokens=32_000` — **confirmed, but the failure mode differs
    from the contextualized endpoint.** Submitting a single 320,000-token
    input returned success, not an error, and billed `total_tokens=31993`:
    `voyage-code-4` on the flat endpoint **silently truncates** at ~32K
    rather than rejecting. Contrast `contextualized_embed`, which refuses
    outright ("Contextualized chunk embeddings do not support truncation").
    This is a correctness hazard for the indexing pipeline, not just a
    quota detail: an oversized chunk would be *half-embedded with no
    error surfaced*, producing a vector that silently represents only the
    first ~32K tokens of the content. Chunk-size enforcement upstream is
    therefore load-bearing for D1 and must not be assumed to be guarded by
    the API.
  * `max_request_tokens` — **`voyage-code-3`'s 120,000 is wrong for
    `voyage-code-4`.** A 60-input batch totalling 300,000 tokens was
    accepted and billed in full (`total_tokens=299940`). The true ceiling is
    therefore **>300,000 and was not pinned** — the probe established a
    lower bound, not the limit. Either bind this to a vendor-documented
    figure before landing, or carry a deliberately conservative value with a
    comment saying it is a self-imposed floor rather than the API's ceiling.
    Do not record 120,000 as if it were measured.

  Note that the 32,000 / 120,000 pair the registry currently carries for
  `voyage-code-3` matches exactly the two limits the Wave 0 benchmark hit on
  the *contextualized* endpoint — which raises the question of whether
  `voyage-code-3`'s own row was populated from the wrong endpoint's limits.
  Out of scope for this amendment, but worth an entry on the audit's residual
  list.
* `index_profile.py`: in `build_code_collection_profile()`, `content_vec`
  changes from `model=ctx_model, endpoint="contextualized_embeddings"` to the
  resolved code model on `endpoint="embeddings"`, so index and query agree.
  Whether `title_vec`/`breadcrumb_vec` also move from `voyage-code-3` to
  `voyage-code-4` is a separate, unresolved question — it is consistent and
  cheaper ($0.12/M vs $0.18/M) but is beyond D1's literal wording and is
  **not** authorized by this amendment without an explicit ruling.

### Rollback

Revert the two lookahead lines. The lane returns to its 2026-09-03 shape with
no other state to unwind; any commits made under the amendment stay in
history and would need their own revert.

### Verification before landing

* `PYTHONPATH=src python -m pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
  — expected full pass, including `test_fallback_patterns_covered_by_live_rules`
  (the fallback tuple is a subset and is unaffected by adding exemptions).
* `surface_guard_block("Edit", {"file_path": <root>/services/dope-context/src/index_profile.py}, <root>)`
  returns `None`; the same call for
  `services/dope-context/src/search/dense_search.py` and for
  `services/dope-context/eval/../src/index_profile.py` still returns a
  `DCP-RED-MERGE-SEAM-0001` block message.
* A new case asserting `src/embeddings/model_registry.py` is exempt while
  `src/embeddings/voyage_embedder.py` is still blocked — the two live in the
  same directory, which is exactly the near-miss this anchoring must survive.

────────────────────────────────────────────────────────────

## Amendment A3 — carve out the one blocked test file the landed D1 change invalidates (2026-09-04)

```text
AMENDMENT_ID=ADR-226-A3
AMENDMENT_STATUS=APPROVED
APPROVED_BY=operator (session 3d420c77, 2026-09-04)
COMPANION_PACKET_AMENDMENT=TP-DOPECONTEXT-VECTOR-SPACE-0004 amendment A3 (same date)
ADDS_EXEMPTIONS=services/dope-context/tests/test_vector_profiles_and_migration.py
AUTHORIZES_CONTENT_EDITS=NO (path-level only; TEXT_RULES scanning unchanged)
WAVES_1_4_SRC_LIFT=STILL_NOT_AUTHORIZED
```

### Why

A2 was written from a static reading and got one thing wrong, which the
implementation then exposed empirically. A2 asserted that
`src/pipeline/indexing_pipeline.py` and `src/mcp/server.py` "need no edit".
That is false. Both pass `content_profile.model` but **hardcode the
contextualized embedder object** rather than dispatching on
`content_profile.endpoint`:

* `indexing_pipeline.py:300` — `self.contextualized_embedder.embed_document(...)`
* `mcp/server.py:1235` — `contextual_embedder.embed_document(...)`
* `mcp/server.py:960` — constructs `ContextualizedEmbedder(default_model=code_profile.content().model, ...)`

After D1 all three would hand `voyage-code-4` to the contextualized endpoint,
which accepts only the `voyage-context-*` family. The third one fails at
*construction* time and was caught by `test_mcp_server.py::test_index_workspace_tool`
raising `ValueError: Voyage model 'voyage-code-4' uses endpoint 'embeddings',
not 'contextualized_embeddings'`. Both files were already in Allowed Files, so
correcting them required no new amendment — but A2's claim is withdrawn, and
the record should say so rather than leave a wrong rationale standing.

### What this amendment is actually for

With those fixed, the suite is **115 passed, 1 skipped, 4 failed**, and every
remaining failure is in a single **blocked** file,
`services/dope-context/tests/test_vector_profiles_and_migration.py`. Each one
asserts the pre-D1 contract, so each is *supposed* to change; none is a defect:

1. `test_six_named_vector_index_query_profiles_identical` (L40-43) — asserts
   `code.content().endpoint == "contextualized_embeddings"`,
   `code.title().model == "voyage-code-3"`,
   `code.breadcrumb().model == "voyage-code-3"`, and
   `docs.content().model == code.content().model`. D1 falsifies all four by
   design; docs stay contextualized while code goes flat, so the code and docs
   content models are no longer equal.
2. `test_profile_mutations_change_collection_identity[<lambda>0]` (L71) —
   expects `build_code_collection_profile(contextual_model="voyage-context-3")`
   to change the collection digest. `contextual_model` is now inert for code
   profiles, so the digest correctly does not move. The parameter is retained
   for signature compatibility; the mutation case must move to a parameter that
   still participates in code identity (e.g. `code_model=`).
3. `test_endpoint_change_changes_collection_identity` (L88-94) — its premise is
   that the code profile carries *mixed* endpoints. D1 makes the code profile
   uniform, which is the entire point.
4. `test_context3_rollback_moves_all_contextual_paths_together` (L162, L167) —
   asserts the contextual rollback env var also moves code `content_vec`, and
   that `code.title().model` stays `voyage-code-3`. After D1 the contextual
   rollback governs docs only; code has no contextualized vector for it to
   move. This test needs its premise rewritten, not its literals swapped.

### Exact regex change

```python
    re.compile(
        r"^services/dope-context/"
        r"(?!eval/)"
        r"(?!src/pipeline/indexing_pipeline\.py$)"
        r"(?!src/mcp/server\.py$)"
        r"(?!src/index_profile\.py$)"
        r"(?!src/embeddings/model_registry\.py$)"
        r"(?!tests/test_vector_space_invariants\.py$)"
+       r"(?!tests/test_vector_profiles_and_migration\.py$)"
        r".*$"
    ),
```

### Invariants preserved

Unchanged from A2: anchored `$` (so `.bak`/`.orig`/`.tmp` variants and
same-named files elsewhere stay blocked), whole-path case folding, the
traversal-refusal companion entry, and `TEXT_RULES` content scanning. Every
other file under `services/dope-context/tests/` — `conftest.py`,
`test_mcp_server.py`, `test_voyage_modernization.py`,
`test_reliability_repairs.py` — remains hard-blocked, and none of them needs
an edit: their `120_000` assertions name `voyage-code-3` and `voyage-3-lite`
literally, and those specs are unchanged.

### Rollback

Revert the one lookahead line. Note that reverting A3 alone leaves the four
tests failing; a full rollback of D1 means reverting the A2 implementation
commit as well, which restores the old assertions' truth.

### Verification before landing

* The four named tests pass with their premises rewritten, not deleted.
* `surface_guard_block` still denies `tests/conftest.py`,
  `tests/test_mcp_server.py`, and
  `tests/test_vector_profiles_and_migration.py.bak`.
* Full suite returns to zero failures.

────────────────────────────────────────────────────────────

## Operational consequence of D1 — existing code collections are stranded (2026-09-04)

Raised by the round-4 independent audit as `STRANDED_COLLECTIONS`
(`proof/pr_merge/embedded-audit/pr-1304/round4/`). It was a real disclosure
gap: neither A2, A3, nor the D1 commit recorded it.

**What happens.** D1 changes the code collection's content model from
`voyage-context-4` on `contextualized_embeddings` to `voyage-code-4` on
`embeddings`. `build_collection_manifest()` records model and endpoint, and
`compare_collection_manifests()` compares them field by field. Any code
collection indexed before D1 therefore mismatches on both `model` and
`endpoint`, and every subsequent write to it raises
`CollectionCompatibilityError`.

**This is by design, not a defect.** The failure is loud, fails closed, and
carries an actionable message ("recreate the collection explicitly instead of
mixing vector generations"). Mixing a contextualized and a flat vector
generation in one collection is exactly the F-001 class of silent corruption
this packet exists to end, so refusing the write is correct. The audit rated
this HIGH on the assumption it was undisclosed and unmitigated; the disclosure
gap was real, the silent-corruption risk was not.

**Required operator action.** Every pre-D1 code collection must be explicitly
recreated (re-indexed). There is deliberately **no automatic migration**:
vectors from the two spaces are not comparable, so a silent in-place upgrade
would be precisely the mistake D1 removes. Docs collections are unaffected.

**Blast radius at the time of writing.** Near zero. Qdrant currently holds one
collection belonging to an unrelated project; there is no production
dopemux-mvp code index to migrate.

**Not changed:** `INDEX_SCHEMA_VERSION` stays `dope-context-v2`. The manifest
comparison already catches this on model and endpoint, and bumping the schema
version would additionally strand *docs* collections, which D1 does not touch.
