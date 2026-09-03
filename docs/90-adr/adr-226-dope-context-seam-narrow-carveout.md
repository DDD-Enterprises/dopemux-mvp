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
