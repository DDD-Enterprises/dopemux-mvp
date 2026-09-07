---
id: TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002
title: Red-Lane Scanner Control-Character Fail-Closed Repair
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-04'
last_review: '2026-09-06'
next_review: '2026-10-06'
prelude: L3 runtime closure packet for a confirmed live control-character bypass
  in RedLaneScanner, discovered during review of this packet's own prior
  test-only version. Supersedes that version; runtime mutation is now in scope.
---
# TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002

**Scanner-side control-character fail-closed repair — supersedes the test-only
version of this packet.**

```
PACKET_ID=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002
PARENT_PACKET=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001
STATUS=ESCALATED_L3_AWAITING_RUNTIME_IMPLEMENTATION_AUTHORITY
PREVIOUS_STATUS=AUTHORED_AWAITING_OPERATOR_AUTHORIZATION (test-only, superseded)
BASE_SHA=6a728f74c0311967f83213513308f97613e3f28d   # origin/main, current
BASE_SHA_AT_PRIOR_VERSION=33a38119f97611e391aab719151ffadbf541f06c  # ancestor, via #1328
RISK_LANE=L3
LANE_DEVIATION=none — operator confirmed L3 (2026-09-06 Decision)
IMPLEMENTATION_AUTHORITY=NOT_GRANTED
RUNTIME_IMPLEMENTATION=NOT_YET_AUTHORIZED_BY_THIS_DECISION
MERGE=NO
```

> **Why this version exists.** The prior version of this packet (test-only,
> `PROPOSED_LANE=L1`) was itself put up for review on PR #1325. Automated
> review (`chatgpt-codex-connector`) on that PR found that the packet's own
> "no runtime mutation needed" claim was false: it ran the scanner against an
> exact-match forbidden path plus a trailing newline and got a silent bypass.
> That claim is confirmed below, independently reproduced. This version
> replaces the prior scope; it does not append to it.

---

## 1. Why this packet exists (rewritten)

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
reproduced against current `main` (`6a728f74c…`):

```text
>>> RedLaneScanner(repo_root=".").scan(changed_files=["scripts/dopetask\n"])
Status.UNKNOWN, forbidden_findings=[]          # BYPASS

>>> RedLaneScanner(repo_root=".").scan(changed_files=["scripts/taskx\n"])
Status.UNKNOWN, forbidden_findings=[]          # BYPASS

>>> RedLaneScanner(repo_root=".").scan(
...     changed_files=["dopemux_pr_merge_specialist/queue_drain.py\n"])
Status.UNKNOWN, forbidden_findings=[]          # BYPASS

# control group — DOTALL wildcard rules correctly still block:
>>> RedLaneScanner(repo_root=".").scan(changed_files=["services/task-orchestrator/x/\ny"])
Status.BLOCKED
>>> RedLaneScanner(repo_root=".").scan(changed_files=["services/dope-context/src/\nsecret.py"])
Status.BLOCKED
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

## 2. Scope (revised — runtime mutation is now in scope)

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
    -> a blocking finding is recorded
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
`FORBIDDEN_PATH` finding for audit purposes.

### 3.2 Regression coverage — supersedes the prior "port only" plan

The prior version proposed porting exactly PR #1321's 44-line block
(`353bd8b24:tests/dcp/test_dcp_0005_red_lane_scanner.py`, appended after line
456) and stopping there. That block is still worth keeping — it exercises
real behavior, not regex shape — but it only covers the wildcard subtrees
already proven safe. It must be supplemented, not treated as sufficient.

**Deterministic donor retrieval** (fixes the P2 portability finding on this
packet's own PR): PR #1321's head is not guaranteed reachable from a fresh
clone. Before porting, the branch must be fetched explicitly and its content
hash verified, e.g.:

```bash
git fetch origin pull/1321/head:tp-1321-donor
git rev-parse tp-1321-donor   # must equal 353bd8b245beb2c137f1ef94b45227d885328fed
git show 353bd8b24:tests/dcp/test_dcp_0005_red_lane_scanner.py \
  | sha256sum   # record and compare against a pinned value before extracting lines
```

A donor block that cannot be retrieved and hash-verified this way must not be
"reconstructed from memory" — write fresh tests asserting the same behavior
instead, and say so plainly in the resulting proof.

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

---

## 4. Pre-verification methodology (repairs the P1 mutation-isolation finding)

The prior version's §4 ran two mutations sequentially in one worktree without
resetting between them — the first mutation (anchor `\Z`→`$`) already makes
the newline probe fail, so the second mutation (removing `re.DOTALL`) could
report "BITES" even if it had no effect. That is a false-positive risk in
the *proof*, not in the fix. Each mutation must be independently isolated:

```text
for each mutation M in {control-char short-circuit removed}:
    1. git worktree reset to BASE_SHA + this packet's clean implementation commit
    2. verify the tree is exactly that (git status clean, git diff empty)
    3. apply exactly M, assert and record its landed change count
    4. run the full regression matrix from §3.2
    5. record which specific probes fail and their actual Status
    6. reset the worktree again before the next mutation
```

For this packet there is effectively one mutation to isolate (removing the
new short-circuit), since `red_lane_rules.py` is read-only and unmutated.
If the implementation also re-runs the existing `red_lane_rules.py` anchor/
DOTALL mutations as a non-regression check (recommended, since this packet
sits directly next to that code), those must be isolated from each other and
from the new mutation using the same reset discipline — not chained.

**Also fix the stale counts from the prior version:** at `BASE_SHA`,
`red_lane_rules.py` contains **23** occurrences of `\Z` (not 24) and **9**
occurrences of `re.DOTALL` (not stated incorrectly, but re-verify at
whatever `BASE_SHA` implementation actually runs against — `main` moves).
Any mutation script must assert its own landed replacement count and fail
loudly on a zero-count or unexpected-count result rather than silently
proceeding.

---

## 5. Acceptance criteria

1. `src/dopemux/dcp/red_lane_scanner.py` gains the unconditional
   control-character short-circuit described in §2–3.1. No change to
   `red_lane_rules.py` or `.claude/hooks/dcp_surface_guard.py`.
2. `tests/dcp/test_dcp_0005_red_lane_scanner.py` gains regression coverage
   for the full §3.2 matrix (exact-match, wildcard, exemption-spoof,
   arbitrary-malformed, clean-control) — donor content retrieved and
   hash-verified per §3.2, not reconstructed from memory.
3. Full scanner test file green.
4. The isolated mutation in §4 is reproduced: removing the short-circuit
   causes the exact-match probes (`scripts/dopetask\n`, etc.) to fail —
   these are the probes that were previously silently passing (bypassing),
   so they are the ones that matter for proving this fix is non-vacuous.
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
   validates against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

---

## 6. Governance findings (record, not adjudicate)

- **G-1 — Live PR collision.** PR #1321 (branch
  `tp-dmx-pr1304-red-lane-path-regex-hardening-001`, head `353bd8b24`) remains
  **OPEN, unmerged, non-mergeable**. Its scanner-test block is still worth
  salvaging (§3.2) but its own runtime approach (a blanket
  `re.compile(r".*[\x00-\x1f\x7f]", re.DOTALL)` prepended to
  `FORBIDDEN_PATHS`) is not what this packet uses — the operator's chosen
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
- **G-4 — new, this version.** The exact-match-rule scanner bypass in §1.3
  was not in the original `…-001` threat model at all (its regression matrix
  only covered wildcard subtrees) and was not caught by `…-001`'s own two
  independent implementations (PR #1322 merged, PR #1321 open) or by two
  rounds of embedded audit on PR #1323/#1322's family. It was caught by
  automated PR review (`chatgpt-codex-connector`) on this packet's own
  *test-only* draft, which is the artifact that would have shipped it if
  the draft had been merged as originally scoped. Recorded for the
  record: a "test-only, no runtime mutation" self-assessment is not
  self-verifying — it should be treated as a claim requiring the same
  adversarial scrutiny as a runtime change, not as inherently lower-risk.

---

## 7. Lane

`RISK_LANE=L3` under `DEFECT_CLASS=SECURITY_AUTHORITY_ENFORCEMENT_BYPASS`,
confirmed by operator decision 2026-09-06 (not downgraded to L1 — the prior
version's proposed downgrade is withdrawn along with the rest of that
version's scope). This packet mutates a runtime enforcement file
(`red_lane_scanner.py`); it is not test-only.

```
PROVEN_GUARD_LEVEL_BYPASS=NO (guard already safe, unaffected by this finding)
PROVEN_SCANNER_LEVEL_BYPASS=YES (reproduced in §1.3)
PROVEN_END_TO_END_CLIENT_EXPLOIT=UNKNOWN
KNOWN_EXPLOITATION=NO
```

---

## 8. Execution constraints

- **`RUNTIME_IMPLEMENTATION=NOT_YET_AUTHORIZED_BY_THIS_DECISION`.** This
  document is authored output only. The operator's 2026-09-06 decision
  authorized scoping this packet and repairing this document; it did
  **not** authorize writing `red_lane_scanner.py` or its tests. A separate,
  explicit authorization is required before any mutation under §2 begins.
- **`MERGE=NO`.** PR #1325 stays open and unmerged while it carries this
  packet document. It must not be merged as a documentation-only PR now
  that its own scope calls for a runtime change — merge it (or a successor
  PR) only once the runtime fix and its proof are attached and independently
  audited.
- Never route around the red lane. A denied write is a stop, not an
  obstacle.
- Never `dopemux mcp down --services <x>` (degrades to a full-fleet
  `rm -f -s -v`). Use `up`.
- Never `--no-verify`.
- Re-probe the live rule layer rather than trusting this document's
  quotations before implementing — `main` has moved multiple times during
  this family's lifetime already (`892b856d3` → `33a38119f` → `6a728f74c`
  and counting).
