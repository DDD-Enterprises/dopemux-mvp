---
id: TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002
title: Red-Lane Scanner Control-Character Fail-Closed Repair (Reconstructed, Clean Custody)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-04'
last_review: '2026-09-07'
next_review: '2026-10-07'
prelude: L3 runtime closure packet for a confirmed live control-character bypass
  in RedLaneScanner. This is the gate-reconstructed successor of the packet PR
  #1325 carried into unauthorized runtime/test implementation
  (TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002-GATE-RECONSTRUCTION-001,
  2026-09-07). Content is unchanged in substance from the last legitimate
  pre-runtime version at commit ffc4322b68f, except where this reconstruction's
  required repairs (execution-base binding, clean branch, donor object binding,
  anti-vacuity mutation evidence, audit lineage, authority language) apply.
---
# TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002 (Reconstructed)

**Scanner-side control-character fail-closed repair — clean custody successor
to the version of this packet that PR #1325 carried into unauthorized runtime
implementation.**

```
PACKET_ID=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002
PARENT_PACKET=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001
RECONSTRUCTION_PACKET=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002-GATE-RECONSTRUCTION-001
STATUS=ESCALATED_L3_AWAITING_RUNTIME_IMPLEMENTATION_AUTHORITY
PREVIOUS_STATUS=CONTAMINATED_ON_PR_1325 (unauthorized runtime/test/proof implementation observed; this document supersedes that custody, not its content claims)
SOURCE_GATE_COMMIT=ffc4322b68f89fc3a4b4ad71b374daff236936f4
EXECUTION_BASE_SHA=<computed fresh at execution time via `git rev-parse origin/main`; equal to 6a728f74c0311967f83213513308f97613e3f28d at reconstruction time, 2026-09-07T05:08Z>
BASE_SHA_AT_PRIOR_VERSION=33a38119f97611e391aab719151ffadbf541f06c  # ancestor, via #1328
RISK_LANE=L3
LANE_DEVIATION=none — operator confirmed L3 (2026-09-06 Decision)
IMPLEMENTATION_AUTHORITY=NOT_GRANTED
RUNTIME_IMPLEMENTATION=NOT_AUTHORIZED
TEST_IMPLEMENTATION=NOT_AUTHORIZED
PUSH=NO
PR_CREATION=NO
MERGE=NO
EXECUTION_BRANCH=fix/red-lane-scanner-fail-closed-002-clean
EXECUTION_BRANCH_COLLISION=0 (verified via git ls-remote --heads origin and git branch --list, 2026-09-07)
DELIVERY_VEHICLE=NEW_PR (not PR #1325)
```

> **Why this reconstruction exists.** PR #1325, which carried a copy of this
> packet, advanced through three rounds of unauthorized runtime and proof
> implementation (`582862ea5` initial short-circuit → `0ed8bd5ee` round-1
> review fixes → `6be339b7f`/`ac0f832d3` round-2/round-3 review fixes) without
> the explicit `AUTHORIZE_..._EXECUTION=YES` gate this packet has always
> required. `TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002-GATE-RECONSTRUCTION-001`
> rebuilds this packet from the last legitimate pre-runtime commit
> (`ffc4322b68f`), repairs the specific gaps a fresh worktree execution and
> live review findings surfaced, and rebinds it to a new, uncontaminated
> branch and PR. **This reconstruction did not change any of the technical
> claims below** (the bypass, its root cause, and the required fix are
> unchanged and were independently re-verified against current `main` during
> reconstruction); it changed only the custody, execution-binding, and
> authority scaffolding around them.

---

## 1. Why this packet exists (unchanged from the source gate commit)

### 1.1 What `…-001` (PR #1322, merged) actually fixed

`FORBIDDEN_PATHS` patterns used `$` (which matches immediately *before* a
trailing newline, not only true end-of-string) and bare `.` inside `.*`
wildcards (which does not cross `\n` without `re.DOTALL`). PR #1322
re-anchored every entry in `src/dopemux/dcp/red_lane_rules.py` to `\Z` and
added `re.DOTALL` to every wildcard-bearing pattern, and added an
unconditional control-character fail-closed short-circuit to
`.claude/hooks/dcp_surface_guard.py` (`_CONTROL_CHARS` / `_has_control_chars`,
lines 122–127; the check itself fires at line 147, before any pattern is
evaluated). That closed the defect **for the wildcard/subtree rules, and for
the guard consumer specifically** (the guard's fail-closed check catches
every control character regardless of which rule would otherwise apply).

### 1.2 The residual this packet's prior version found (scanner has no test coverage)

`FORBIDDEN_PATHS` has two consumers with different call shapes:

- `.claude/hooks/dcp_surface_guard.py:156` — `p.search(rel)`, but gated behind
  the unconditional control-character short-circuit at line 147. **Safe.**
- `src/dopemux/dcp/red_lane_scanner.py:39` — `pattern.match(fpath)`, called
  directly against `changed_files` entries with **no equivalent
  short-circuit**. `tests/dcp/test_dcp_0005_red_lane_scanner.py` (456 lines,
  32 tests) had zero control-character cases before this packet.

### 1.3 The residual review on PR #1325 found (this is new, and worse)

The prior version of this packet proposed closing 1.2 with **tests only**,
reasoning that `\Z` was already correct everywhere and only coverage was
missing. That reasoning is wrong for one class of rule. Independently
reproduced against current `main` twice — once at the source gate commit
(`6a728f74c…`) and again during this reconstruction, from a clean off-repo
extraction of `origin/main` at the same SHA:

```text
>>> RedLaneScanner(repo_root=".").scan(changed_files=["scripts/dopetask\n"])
Status.UNKNOWN, forbidden_findings=[]          # BYPASS (reconstruction-verified)

>>> RedLaneScanner(repo_root=".").scan(changed_files=["scripts/taskx\r"])
Status.UNKNOWN, forbidden_findings=[]          # BYPASS (reconstruction-verified)

>>> RedLaneScanner(repo_root=".").scan(
...     changed_files=["dopemux_pr_merge_specialist/queue_drain.py\n"])
Status.UNKNOWN, forbidden_findings=[]          # BYPASS (reconstruction-verified)

# control group — clean exact match correctly still blocks:
>>> RedLaneScanner(repo_root=".").scan(changed_files=["scripts/dopetask"])
Status.BLOCKED                                  # (reconstruction-verified)
```

**Root cause.** `…-001`'s exact-match rules (`scripts/dopetask`,
`scripts/taskx`, both `queue_drain.py` variants, `batch_resolve_and_merge.py`)
have no `.*` and no `DOTALL`; the anchor swap `$` → `\Z` is the *correct*
exact-end-of-string semantic in isolation, but it is a **regression** for
these five rules specifically: under the old `$`, a trailing `\n` used to
accidentally still match (`$` matches just before a final newline), so
`scripts/dopetask\n` used to be blocked. Under `\Z` it no longer matches, and
the scanner — unlike the guard — has nothing else standing in front of it.
The correctness fix for the wildcard rules created a live hole for the
exact-match rules, on the one consumer that has no independent fail-closed
layer. This is a **currently exploitable bypass on `main`**, not a
theoretical one; it directly touches `DEFECT_CLASS=SECURITY_AUTHORITY_ENFORCEMENT_BYPASS`.

---

## 2. Scope (unchanged — runtime mutation is in scope)

```
RUNTIME_MUTATION:     src/dopemux/dcp/red_lane_scanner.py
TEST_MUTATION:        tests/dcp/test_dcp_0005_red_lane_scanner.py
READ_ONLY:            src/dopemux/dcp/red_lane_rules.py
                      .claude/hooks/dcp_surface_guard.py
```

`red_lane_rules.py` stays untouched: reverting the exact-match rules' anchor
back to `$` would be wrong (it would resurrect the near-miss-exemption-spoof
risk `…-001` closed) and is explicitly forbidden by the operator's repair
choice. The hook stays untouched: it is already correct and out of scope.

**Required runtime behavior:**

```text
ANY ASCII C0 (0x00–0x1F) OR DEL (0x7F) BYTE IN a changed_files PATH
    -> Status.BLOCKED
    -> a blocking finding is recorded, category=MALFORMED_PATH_CONTROL_CHARACTER
       (see §2.1 on this category's basis)
    -> no filesystem handling is attempted for that path
```

This must be **unconditional** — evaluated before `FORBIDDEN_PATHS` matching
and before the "Check Source Text" loop (`red_lane_scanner.py:51–56`, which
currently does `os.path.join` / `os.path.exists` / `open()` on every
`changed_files` entry, malformed or not) — mirroring the hook's placement
and rationale exactly: fail closed on malformed input rather than depend on
every current and future `FORBIDDEN_PATHS` entry having exactly correct
anchoring.

If, during implementation, this genuinely cannot be satisfied by a
scanner-local change alone, **stop and escalate scope again** — do not touch
`red_lane_rules.py` or the hook without a fresh decision.

### 2.1 Category basis (reconstruction gate check, recorded per governing packet §8)

`Finding.category` (`src/dopemux/dcp/red_lane.py`) is a plain `str` field
with no schema or taxonomy enum constraining it anywhere in this repository.
`schemas/dcp/dcp_red_lane_taxonomy.instance.json`'s `lanes` list is a
distinct namespace (`DCP-RED-*` lane IDs used for path-block metadata);
existing scanner-defined `Finding.category` strings already in production on
`main` — `MALFORMED_PROOF`, `STALE_PROOF`, `SELF_CERTIFICATION`,
`UNCLASSIFIED_RISK`, `CI_OR_WORKFLOW_MUTATION`, `FORBIDDEN_PATH` — appear in
none of the taxonomy JSON's lanes and in no JSON schema either. Adding
`MALFORMED_PATH_CONTROL_CHARACTER` as a new `Finding.category` value
therefore requires no change to any schema or taxonomy file and is
consistent with the established ad-hoc scanner-category pattern.
**This reconstruction reads the governing packet's `STOP=SCOPE_ESCALATION_REQUIRED`
condition as scoped to a new *public schema/taxonomy* category, and treats it
as not triggered here** — flagged explicitly (see
`00_RECONSTRUCTION_CUSTODY.json`, `taxonomy_category_gate_check`) so a
supervisor can override this reading before authorizing execution if a
stricter interpretation was intended.

---

## 3. The change

Two parts, both required:

### 3.1 Add the scanner-side short-circuit

A single unconditional check at the top of `RedLaneScanner.scan()` — before
the `FORBIDDEN_PATHS` loop and before the source-text loop — that scans every
`changed_files` entry for a C0/DEL byte and, on a hit, records a blocking
finding for that path and skips all further processing (pattern matching,
`is_safe_false_positive`, filesystem access) for it. Implementation is free
to choose the exact finding shape as long as `RedLaneReport.status` resolves
to `Status.BLOCKED` and the finding is distinguishable from an ordinary
`FORBIDDEN_PATH` finding for audit purposes. **The corresponding test must
assert non-invocation of `os.path.exists`/`open` by mocking them and
asserting `assert_not_called()`, not merely inspect the report's shape** —
a live PR #1325 review finding (thread `PRRT_kwDOPyIw986fySn2`) confirmed a
shape-only assertion can pass even when the short-circuit's filesystem-skip
invariant is silently broken by a later refactor.

### 3.2 Regression coverage — supersedes the prior "port only" plan

The prior version proposed porting exactly PR #1321's 44-line block
(`353bd8b24:tests/dcp/test_dcp_0005_red_lane_scanner.py`, appended after line
456) and stopping there. That block is still worth keeping — it exercises
real behavior, not regex shape — but it only covers the wildcard subtrees
already proven safe. It must be supplemented, not treated as sufficient.

**Deterministic donor retrieval, object-verified at two levels** (fixes the
P2 portability finding on the contaminated PR, repaired further by this
reconstruction to pin the blob, not just the commit):

```bash
git fetch origin pull/1321/head:refs/remotes/origin/pr1321-donor
test "$(git rev-parse refs/remotes/origin/pr1321-donor)" \
  = "353bd8b245beb2c137f1ef94b45227d885328fed"

test "$(git rev-parse \
  353bd8b245beb2c137f1ef94b45227d885328fed:tests/dcp/test_dcp_0005_red_lane_scanner.py)" \
  = "720c4d23db8ad337d435de0a872ef20f95ee1730"
```

Both checks passed when independently re-run during this reconstruction
(2026-09-07); see `00_RECONSTRUCTION_CUSTODY.json`, `donor_binding`. If
either differs at execution time: `STOP=DONOR_IDENTITY_MISMATCH`. Only
scanner-side test behavior may be ported from PR #1321 — not
`red_lane_rules.py`, not `test_dcp_surface_guard.py`, not any proof bundle,
and never as a wholesale cherry-pick.

A donor block that cannot be retrieved and object-verified this way must not
be "reconstructed from memory" — write fresh tests asserting the same
behavior instead, and say so plainly in the resulting proof.

**Full required regression matrix** (all against `RedLaneScanner.scan`,
asserting `Status.BLOCKED` + a blocking finding unless marked ALLOW):

```text
# exact-match rules — the newly discovered gap (all control-char classes, not just \n)
scripts/dopetask\n                                          -> BLOCK
scripts/taskx\r                                             -> BLOCK
scripts/batch_resolve_and_merge.py\t                        -> BLOCK
src/dopemux_pr_merge_specialist/queue_drain.py\x7f           -> BLOCK
dopemux_pr_merge_specialist/queue_drain.py\n                -> BLOCK

# wildcard rules (PR #1321's donor set — already safe, must stay safe)
services/dope-context/src/\nsecret.py                        -> BLOCK
services/dope-context/src/index_profile.py\n                 -> BLOCK
services/task-orchestrator/x/\ny                              -> BLOCK
.github/workflows/embedded-audit.yml\n                        -> BLOCK   # exemption-spoof
services/dope-context/src/index_profile.py\t                 -> BLOCK
services/dope-context/src/index_profile.py\r                 -> BLOCK

# arbitrary malformed path — not itself a forbidden path anywhere,
# proving the fail-closed rule is unconditional, not scoped to protected subtrees
docs/readme.md\n                                              -> BLOCK
some/totally/unrelated/file.txt\x01                           -> BLOCK

# clean-control: legitimate paths at and near the C0/DEL boundary must be unaffected
.github/workflows/embedded-audit.yml                          -> ALLOW
.github/workflows/pr-steward.yml                              -> ALLOW
services/dope-context/eval/run_eval.py                        -> ALLOW
services/dope-context/src/index_profile.py                    -> ALLOW
README.md                                                     -> ALLOW
path with a literal space and a tilde~                        -> ALLOW  # 0x20, 0x7E: not C0/DEL
```

13 of these rows are the anti-vacuity mutation matrix in §4; the 6
`ALLOW` rows and the remaining clean rows are not re-asserted under mutation.

---

## 4. Pre-verification methodology (repairs the P1 mutation-isolation finding, and the round-2/3 evidence-accuracy findings live on PR #1325)

The prior version's §4 ran two mutations sequentially in one worktree without
resetting between them — the first mutation (anchor `\Z`→`$`) already makes
the newline probe fail, so the second mutation (removing `re.DOTALL`) could
report "BITES" even if it had no effect. That is a false-positive risk in
the *proof*, not in the fix. Each mutation must be independently isolated,
and — repaired in this reconstruction, per governing packet §9 — **every
probe result must be collected before any expectation is evaluated**, not
asserted one at a time with an early abort:

```text
for each mutation M in {control-char short-circuit removed}:
    1. git worktree reset to EXECUTION_BASE_SHA + this packet's clean implementation commit
    2. verify the tree is exactly that (git status clean, git diff empty)
    3. apply exactly M (a single, named, reversible change), assert and
       record its landed change count (must be non-zero)
    4. run the full 13-probe regression matrix from §3.2 to completion,
       recording {probe_id, probe_class, input_representation,
       expected_status, actual_status, finding_categories, result} for
       every probe before evaluating any single expectation
    5. reset the worktree again, and prove git status --porcelain is empty
       after restoration
```

**Expected shape, stated explicitly so it cannot be mis-reported** (a live,
unresolved PR #1325 finding — thread `PRRT_kwDOPyIw986fya9B` — caught this
exact class of over-claim in round 2 of the contaminated implementation):
under the mutation, the 5 exact-match probes and the 2 arbitrary-malformed
probes (7 total) are expected to revert fully to `Status.UNKNOWN` with zero
findings — the true original bypass. The 6 wildcard/exemption-spoof probes
are expected to **remain `Status.BLOCKED`**, via the independent, unmutated
`FORBIDDEN_PATH` rule from `red_lane_rules.py` — only their finding category
changes, not their status. Reporting all 13 as reverting to `UNKNOWN` is
inaccurate and must not be repeated.

For this packet there is effectively one mutation to isolate (removing the
new short-circuit), since `red_lane_rules.py` is read-only and unmutated.
If the implementation also re-runs the existing `red_lane_rules.py` anchor/
DOTALL mutations as a non-regression check (recommended, since this packet
sits directly next to that code), those must be isolated from each other and
from the new mutation using the same reset discipline — not chained.

**Also fix the stale counts from the prior version:** at `EXECUTION_BASE_SHA`,
`red_lane_rules.py` contains **23** occurrences of `\Z` and **9** occurrences
of `re.DOTALL` at the time of this reconstruction (2026-09-07) — re-verify at
whatever `EXECUTION_BASE_SHA` implementation actually runs against, since
`main` moves. Any mutation script must assert its own landed replacement
count and fail loudly on a zero-count or unexpected-count result rather than
silently proceeding.

---

## 5. Acceptance criteria

1. `src/dopemux/dcp/red_lane_scanner.py` gains the unconditional
   control-character short-circuit described in §2–3.1. No change to
   `red_lane_rules.py` or `.claude/hooks/dcp_surface_guard.py`.
2. `tests/dcp/test_dcp_0005_red_lane_scanner.py` gains regression coverage
   for the full §3.2 matrix (exact-match, wildcard, exemption-spoof,
   arbitrary-malformed, clean-control) — donor content retrieved and
   commit-and-blob-verified per §3.2, not reconstructed from memory —
   including the filesystem-non-invocation assertion from §3.1.
3. Full scanner test file green.
4. The isolated mutation in §4 is reproduced, with all 13 matrix probes
   individually recorded: the 7 exact-match/arbitrary-malformed probes fail
   (revert to `Status.UNKNOWN`) and the 6 wildcard/exemption-spoof probes
   remain `Status.BLOCKED` under the same mutation.
5. All `ALLOW` cases in §3.2 remain unaffected — the fix must not be
   satisfiable by over-blocking every path with any byte ≥ 0x7F or similar
   shortcuts.
6. No `--no-verify`. If a PreToolUse denial occurs while editing
   `red_lane_scanner.py` (it should not — it is not itself a red-lane path),
   **stop** — do not route around it.
7. Report **PASS / FAIL / NOT_RUN** per criterion. `NOT_RUN` is never
   reported as `PASS`.
8. This packet's own machine-readable companion
   (`task-packets/TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002.json`)
   validates against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
   — confirmed `DRAFT7_SCHEMA=PASS` for this reconstructed version, see
   `06_SCHEMA_VALIDATION.json`.
9. `IMPLEMENTATION_HEAD` is recorded as the exact substantive commit; the
   fresh independent audit and every later proof-only commit are bound to it
   by `git merge-base --is-ancestor`, per governing packet §12.
10. CI and PR Steward outcomes are recorded as a distinct, later-arriving
    signal from local validation, never asserted inside a proof document
    written before those gates could have run — a live, unresolved PR #1325
    finding (thread `PRRT_kwDOPyIw986fya82`) caught exactly this
    self-referential-timing problem.

---

## 6. Governance findings (record, not adjudicate)

- **G-1 — Live PR collision.** PR #1321 (branch
  `tp-dmx-pr1304-red-lane-path-regex-hardening-001`, head `353bd8b24`) remains
  **OPEN, unmerged, non-mergeable** (re-verified 2026-09-07: `mergeable=false`).
  Its scanner-test block is still worth salvaging (§3.2) but its own runtime
  approach (a blanket `re.compile(r".*[\x00-\x1f\x7f]", re.DOTALL)` prepended
  to `FORBIDDEN_PATHS`) is not what this packet uses — the operator's chosen
  repair strategy is a scanner-local short-circuit instead. Close #1321 as
  superseded, crediting it for the donor test content, once this packet's
  runtime fix lands on `main`. Operator decision; not self-authorized here.
- **G-2 — Parent had no packet document.** `…-001` exists on `main` only as a
  proof directory and commit-message references; this `-002` remains the
  first authored packet in the family.
- **G-3 — `READ_ONLY_CONSUMER` boundary already crossed on `main`, by history,
  not by this packet.** PR #1322's merged commit `892b856d3` added the
  control-character short-circuit to `.claude/hooks/dcp_surface_guard.py`
  (lines 122–153) before any packet declared that file read-only. Ratified
  by operator decision (2026-09-06): **do not revert** — it is useful
  fail-closed defense and removing it would only serve historical-scope
  tidiness. Recorded as `CURRENT_HOOK_BEHAVIOR=RATIFIED`,
  `ORIGINAL_SCOPE=READ_ONLY_CONSUMER`, `LANDED_SCOPE_HISTORY=CONFLICTING`,
  `RETROACTIVE_HISTORY_REWRITE=NO`. This packet's own scope keeps the hook
  read-only going forward; the historical mismatch is preserved as
  governance history, not repaired.
- **G-4 — The exact-match-rule scanner bypass in §1.3** was not in the
  original `…-001` threat model at all (its regression matrix only covered
  wildcard subtrees) and was not caught by `…-001`'s own two independent
  implementations (PR #1322 merged, PR #1321 open) or by two rounds of
  embedded audit on PR #1323/#1322's family. It was caught by automated PR
  review (`chatgpt-codex-connector`) on this packet's own *test-only* draft.
  Recorded for the record: a "test-only, no runtime mutation" self-assessment
  is not self-verifying — it should be treated as a claim requiring the same
  adversarial scrutiny as a runtime change, not as inherently lower-risk.
- **G-5 — new, this reconstruction.** Between the source gate commit
  (`ffc4322b68f`) and this reconstruction, PR #1325 advanced through
  unauthorized runtime implementation across three review rounds without the
  operator gate this packet has always required, and continued to receive
  new unauthorized commits (round-3 review-finding fixes) **during the
  reconstruction session itself** — see `00_RECONSTRUCTION_CUSTODY.json`,
  `live_drift_during_reconstruction`. Recorded for the record: an authority
  gap, once created, does not self-close by continued diligent-looking work
  on the same unauthorized branch; only an explicit operator authorization
  or an explicit operator stop closes it. PR #1325's own round-3 review still
  carries 3 threads with no reply at all as of this reconstruction, which is
  independent evidence that the branch remains actively unstable, not merely
  procedurally unauthorized.

---

## 7. Lane

`RISK_LANE=L3` under `DEFECT_CLASS=SECURITY_AUTHORITY_ENFORCEMENT_BYPASS`,
confirmed by operator decision 2026-09-06 (not downgraded to L1 — the prior
version's proposed downgrade is withdrawn along with the rest of that
version's scope). This packet mutates a runtime enforcement file
(`red_lane_scanner.py`); it is not test-only.

```
PROVEN_GUARD_LEVEL_BYPASS=NO (guard already safe, unaffected by this finding)
PROVEN_SCANNER_LEVEL_BYPASS=YES (reproduced in §1.3, and independently re-reproduced during reconstruction)
PROVEN_END_TO_END_CLIENT_EXPLOIT=UNKNOWN
KNOWN_EXPLOITATION=NO
```

---

## 8. Execution constraints

- **`RUNTIME_IMPLEMENTATION=NOT_AUTHORIZED`. `TEST_IMPLEMENTATION=NOT_AUTHORIZED`.**
  This document is authored/reconstructed output only. Neither the
  2026-09-06 scoping decision nor this reconstruction authorizes writing
  `red_lane_scanner.py`, its tests, or any proof file. A separate, explicit
  authorization is required before any mutation under §2 begins:

  ```
  AUTHORIZE_TP_DMX_PR1304_RED_LANE_PATH_REGEX_HARDENING_002_EXECUTION=YES
  ```

  Until that exact gate is issued: `RED_LANE_RUNTIME_IMPLEMENTATION=STOP`.
- **`MERGE=NO`. `PUSH=NO`. `PR_CREATION=NO` under this reconstruction packet.**
  Execution authority, once granted, targets a **new** branch
  (`fix/red-lane-scanner-fail-closed-002-clean`, verified collision-free) and
  a **new** PR — never PR #1325 or its branch
  (`tp/red-lane-scanner-coverage-002`), which remains `CONTAMINATED_CUSTODY`
  and forensic-reference-only.
- Never route around the red lane. A denied write is a stop, not an
  obstacle.
- Never `dopemux mcp down --services <x>` (degrades to a full-fleet
  `rm -f -s -v`). Use `up`.
- Never `--no-verify`.
- Re-probe the live rule layer rather than trusting this document's
  quotations before implementing — `main` has moved multiple times during
  this family's lifetime already (`892b856d3` → `33a38119f` → `6a728f74c`
  and counting), and PR #1325's own head moved twice while this
  reconstruction was in progress.

---

## 9. Reconstruction disposition (this document's own custody)

See the sibling evidence files in this reconstruction packet for full detail:

- `00_RECONSTRUCTION_CUSTODY.json` — SHA/blob/PR reharvest, live-drift record,
  taxonomy-category gate judgment call, branch-collision check, schema
  validator identity.
- `03_REVIEW_FINDING_DISPOSITION.json` — disposition of all 21 PR #1325
  review threads (13 resolved/outdated, 8 unresolved, 3 with no reply at
  reharvest time), mapped against this reconstruction's repairs.
- `06_SCHEMA_VALIDATION.json` — Draft-7 validation result for both the
  as-retrieved source JSON and this reconstructed JSON.
- `07_RECONSTRUCTION_VALIDATION.json` — field-scoped deterministic checks
  proving the required repairs actually landed in this document and its
  JSON companion (not merely asserted).
- `08_RECONSTRUCTION_REPORT.md` — narrative summary and diff-style account
  of every substantive edit relative to the source gate commit.
