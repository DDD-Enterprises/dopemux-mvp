# TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002

**Scanner-side regression coverage for the red-lane control-character bypass.**

```
PACKET_ID=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002
PARENT_PACKET=TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001
STATUS=AUTHORED_AWAITING_OPERATOR_AUTHORIZATION
BASE_SHA=33a38119f97611e391aab719151ffadbf541f06c   # origin/main
PROPOSED_LANE=L1
PARENT_LANE=L3
LANE_DEVIATION=operator to confirm (see §7)
IMPLEMENTATION_AUTHORITY=NOT_GRANTED
```

> This packet is a **salvage order**, not a fresh specification. The code it asks
> for already exists, already passes against the merged rule layer, and has
> already been shown non-vacuous. See §3 and §4.

---

## 1. Why this packet exists

The parent packet `…-001` closed a real authority defect: `FORBIDDEN_PATHS`
patterns used `$` (which matches *before* a trailing newline) and bare `.`
(which does not cross `\n` without `re.DOTALL`), so a path carrying an embedded
or trailing control character could slip past a wildcard subtree rule or be
mistaken for an exact exempt filename.

`…-001` was implemented **twice, independently**:

| | Branch | Head | State | Rules | Hook | Guard tests | **Scanner tests** |
|---|---|---|---|---|---|---|---|
| **A** | `fix/red-lane-path-regex-hardening-001` | `892b856d3` | **MERGED** as PR #1322 (`33a38119f`, 2026-09-04T17:33:34Z) | +34/−22 (re-anchor every pattern to `\Z`, add `re.DOTALL` where wildcards exist) | **+25/−0** | +97/−0 | **none** |
| **B** | `tp-dmx-pr1304-red-lane-path-regex-hardening-001` | `353bd8b24` | **OPEN** as PR #1321 | +13 (one blanket control-char rule) | untouched | +74 | **+44** |

A closed the defect. B closed the defect *and* wrote the scanner-side coverage.
Only A merged. The result on `main` today is a fixed rule layer whose fix is
pinned **only at the guard's call shape**.

### The residual, stated precisely

`FORBIDDEN_PATHS` has two consumers, and they call it differently:

- `src/dopemux/dcp/red_lane_scanner.py:39` — `pattern.match(fpath)`
  (start-anchored, not full-string), with `fpath` taken verbatim from the
  caller's `changed_files` list — no normalisation, no sanitisation.
- `.claude/hooks/dcp_surface_guard.py:127` — `p.search(rel)` (unanchored).

A's regression tests live in `tests/test_dcp_surface_guard.py` and exercise the
canonical layer through a helper that also uses `search`:

```python
def _matches_forbidden_pattern(rel: str) -> bool:
    return any(p.search(rel) for p in FORBIDDEN_PATHS)
```

`tests/dcp/test_dcp_0005_red_lane_scanner.py` (456 lines, 32 tests, no fixtures)
contains **zero** cases with a control character in a path. Nothing in the
merged tree exercises `match(fpath)` against a hostile path. The alarm was
repaired and tested; the second exit it protects was not.

---

## 2. Scope

```
RUNTIME_MUTATION:     none
TEST_MUTATION:        tests/dcp/test_dcp_0005_red_lane_scanner.py
READ_ONLY_CONSUMER:   src/dopemux/dcp/red_lane_scanner.py
                      src/dopemux/dcp/red_lane_rules.py
                      .claude/hooks/dcp_surface_guard.py
```

No runtime file is modified by this packet. If implementation finds that the
scanner cannot be pinned without touching a runtime file, **stop and escalate
scope** — do not mutate.

---

## 3. The change: port B's scanner block

**Source:** `353bd8b24:tests/dcp/test_dcp_0005_red_lane_scanner.py`, lines
**457–500** (44 lines, purely additive — appended after
`test_cli_exits_nonzero_on_incomplete_proof`). Merge-base of B and `main` is
`d032c25c3169eaf73ce40462ad3865fbb164371a`; the scanner test file is **byte
identical** between that merge-base and `33a38119f`, so the block appends
without conflict.

It adds two tests and one probe tuple:

- `test_scanner_blocks_newline_and_control_character_paths` — six probes through
  `RedLaneScanner.scan(changed_files=[...])`, asserting `Status.BLOCKED` and a
  `FORBIDDEN_PATH` finding for each:
  `services/dope-context/src/\nsecret.py`,
  `services/dope-context/src/index_profile.py\n`,
  `.github/workflows/embedded-audit.yml\n`,
  `services/task-orchestrator/x/\ny`,
  `services/dope-context/src/index_profile.py\t`,
  `services/dope-context/src/index_profile.py\r`
- `test_scanner_legitimate_exemptions_unaffected` — four clean paths
  (`embedded-audit.yml`, `pr-steward.yml`, `eval/run_eval.py`,
  `src/index_profile.py`) assert **no** `FORBIDDEN_PATH` finding, so the
  hardening cannot be satisfied by over-blocking.

### Explicitly NOT ported

| Excluded | Reason |
|---|---|
| B's `src/dopemux/dcp/red_lane_rules.py` +13 — a blanket `re.compile(r".*[\x00-\x1f\x7f]", re.DOTALL)` prepended to `FORBIDDEN_PATHS` | **Runtime mutation.** Out of scope, and functionally redundant with A's merged re-anchoring. |
| B's `tests/test_dcp_surface_guard.py` +74 | Superseded by A's merged +97 in the same file. |
| B's proof bundle (`AGY_LIVE_PROBE_SCRIPT.py`, `AUDITOR_REPORT.md`, …) | Collides on the `-001` proof dir path already occupied on `main`. See §6. |

**Why B's tests are portable despite B's different mechanism:** they assert
*behaviour* (`Status.BLOCKED` / absence of a `FORBIDDEN_PATH` finding), never the
shape of the regex. They were written against B's blanket rule and are green
against A's re-anchoring. That mechanism-independence is the property that makes
them worth salvaging rather than rewriting.

---

## 4. Pre-verification (already performed on `33a38119f`)

Run in a clean worktree at `BASE_SHA` with the 44-line block appended and no
other change. Reproducible; re-run before accepting.

| Check | Result |
|---|---|
| Two new tests, unmodified, against merged rules | **PASS** (2 passed) |
| Full `tests/dcp/test_dcp_0005_red_lane_scanner.py` | **PASS** (34 passed) |
| Anti-vacuity — anchor mutation | **BITES** |
| Anti-vacuity — DOTALL mutation | **BITES** |

Mutation detail — **name the needle**, because a different needle gives a
different count and a silent `str.replace` no-op reads as a passing test:

- **Anchor:** needle `\Z` → `$` in `src/dopemux/dcp/red_lane_rules.py`.
  **24 replacements, verified landed.**
  `test_scanner_blocks_newline_and_control_character_paths` fails —
  `services/dope-context/src/index_profile.py\n` returns `Status.UNKNOWN`,
  expected `Status.BLOCKED`.
- **DOTALL:** needle `", re.DOTALL"` → `""`. **6 removals, verified landed.**
  Same test fails — `services/task-orchestrator/x/\ny` returns `Status.UNKNOWN`.
  Note this is a **partial** mutation by design of the needle: the file contains
  **9** occurrences of `re.DOTALL`, and the 3 the needle misses are the
  multi-line patterns where the flag sits on its own line — the dope-context
  pattern among them. Those retain DOTALL, which is why the
  `services/dope-context/src/\nsecret.py` probe still blocks under this
  mutation. The task-orchestrator probe fails regardless, which is sufficient
  to establish non-vacuity. An auditor grepping `DOTALL` will count 9, not 6;
  that is expected, not a discrepancy.

Both mutation scripts assert a non-zero replacement count and re-read the file
before running pytest. A mutation that reports 0 replacements is a **failed
verification**, not a passing one.

---

## 5. Acceptance criteria

1. `tests/dcp/test_dcp_0005_red_lane_scanner.py` gains the two tests above; no
   other file in the repository is modified.
2. Full file green at `BASE_SHA` or its descendant.
3. Both mutations in §4 reproduced, each reported with its needle **and** its
   landed replacement count, each shown to fail
   `test_scanner_blocks_newline_and_control_character_paths`.
4. `test_scanner_legitimate_exemptions_unaffected` green — the fix must not be
   satisfiable by blanket over-blocking.
5. No `--no-verify`. No red-lane routing: the target test file is not red-lane
   restricted, but if a PreToolUse denial occurs, **stop** — do not write the
   path through Bash.
6. Report **PASS / FAIL / NOT_RUN** per criterion. `NOT_RUN` is never reported
   as `PASS`.

---

## 6. Governance findings (record, not adjudicate)

- **G-1 — Live PR collision.** PR #1321 (branch
  `tp-dmx-pr1304-red-lane-path-regex-hardening-001`, head `353bd8b24`) is
  **OPEN** against the same packet ID that PR #1322 merged. Both write
  `proof/TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001/`; that path on `main`
  is now A's bundle. Recommendation: once this block is salvaged, close #1321
  **as superseded**, crediting B for the scanner coverage. Operator decision.
- **G-2 — Parent had no packet document.** `…-001` exists on `main` only as a
  proof directory and as commit-message references; no file under
  `task-packets/` was ever authored for it. This `-002` is the first authored
  packet in the family.
- **G-3 — READ_ONLY_CONSUMER boundary already crossed on `main`.** The operator
  scope for this family declares `.claude/hooks/dcp_surface_guard.py`
  read-only. A's merged commit `892b856d3` added +25 lines to it (a
  `_has_control_chars` fail-closed short-circuit at lines 115–124). That commit
  **predates** the instruction, so it is not a violation — but `main` no longer
  matches the declared boundary, and this packet does not attempt to reconcile
  it. Operator decision.

---

## 7. Lane

The parent was `L3` under `DEFECT_CLASS=SECURITY_AUTHORITY_ENFORCEMENT_BYPASS`.
The authority defect itself is **closed on `main`** by #1322; this packet adds
test coverage only, mutates no runtime file, and cannot change enforcement
behaviour — which reads as `L1`.

Recorded as `PROPOSED_LANE=L1` against `PARENT_LANE=L3` rather than applied.
The operator's stated concern was precisely this coverage gap, so the
downgrade is **not** taken unilaterally. Confirm or override before execution.

---

## 8. Execution constraints

- No implementation authority is granted by this document. It is authored
  output; execution requires separate operator authorization.
- Never route around the red lane. A denied write is a stop, not an obstacle.
- Never `dopemux mcp down --services <x>` (degrades to a full-fleet
  `rm -f -s -v`). Use `up`.
- Never `--no-verify`.
- Re-probe the live rule layer rather than trusting this document's quotations;
  `main` has moved twice during this family's lifetime already.
