---
id: ADR-225
title: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for two PR-readiness-invalidation workflow files (Phase B)
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-31'
last_review: '2026-08-31'
next_review: '2026-11-30'
prelude: Extend ADR-224's narrow DCP-RED-MERGE-SEAM-0001 carve-out to the two PR-readiness-invalidation workflow files (adr) for dopemux documentation and developer workflows.
status: accepted
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - ADR-224
    - TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
    - TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A15-R1
---
# ADR-225: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for two PR-readiness-invalidation workflow files (Phase B)

════════════════════════════════════════════════════════════

## Status

* Accepted

## Date

* 2026-08-31

## Owners

* Supervisor (DDD-Enterprises), executed by Claude (agent session), Phase B of
  `TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R`

────────────────────────────────────────────────────────────

## Context

ADR-224 narrowed `DCP-RED-MERGE-SEAM-0001`'s blanket `.github/workflows/.*`
path-level block (`src/dopemux/dcp/red_lane_rules.py::FORBIDDEN_PATHS`) to
exempt exactly two top-level workflow files: `embedded-audit.yml` and
`pr-steward.yml`. That ADR explicitly scoped itself to those two files only
and stated: "This ADR does not widen the carve-out to any other workflow
file, present or future. A new carve-out for a different file requires its
own ADR." This is that ADR.

The concrete trigger:
`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A15-R1` needed to add
`issue_comment` (PR conversation comment) support to the two-stage PR
readiness invalidation mechanism, so that a new conversation comment on a
PR correctly resets the readiness quiet-clock the same way review activity
already does. That requires editing:

* `.github/workflows/pr-readiness-invalidator.yml` — add an `issue_comment`
  trigger and branch the receipt-writing logic to resolve PR identity and
  live head SHA via a trusted API call (since `issue_comment` events, unlike
  `pull_request*` events, carry no `pull_request` object in their payload).
* `.github/workflows/pr-readiness-invalidation-writer.yml` — accept receipts
  from that new event type, sourcing PR identity from the receipt +
  independently re-fetched live PR data instead of the workflow run's
  `pull_requests` association (which GitHub does not reliably populate for
  `issue_comment`-triggered runs, since they carry no head-branch context at
  trigger time).

The edit was attempted and hard-blocked by the guard mid-packet, with no
workaround attempted (per governance: the seam requires "an ADR + task
packet" to lift, not an inline edit or bypass) — the supervisor was informed
and authorized this narrow Phase-B extension rather than either descoping
the issue-comment work or routing around the block.

Both files were read in full during that packet. Neither contains, nor is
being asked to gain, any merge-automation or PR-mutation capability: the
observer emits a strict, schema-validated JSON receipt (no side effects
beyond an artifact upload); the writer only publishes a `pending` commit
status (`gh api .../statuses/...`), gated behind exhaustive identity
cross-checks against a second, independently-fetched trusted API call. This
mirrors exactly the shape of capability ADR-224 already accepted for
`embedded-audit.yml`/`pr-steward.yml`.

Constraints (same as ADR-224, restated for this extension):

* This ADR authorizes a path-level exemption only, not a content-level one.
  `TEXT_RULES` content scanning (`red_lane_scanner.py`) remains fully active
  on both newly-carved-out files.
* Every other path under `.github/workflows/` — including the two files
  ADR-224 already exempted, which remain exempted — must remain governed
  exactly as before. This ADR only adds two new exact filenames to the
  existing negative-lookahead exemption; it does not touch or relax any
  other `FORBIDDEN_PATHS` entry.
* `_FALLBACK_COMPILED` in `.claude/hooks/dcp_surface_guard.py` is left
  unchanged, exactly as ADR-224 left it: it never included a workflows
  entry, so the fallback-⊆-live sync invariant
  (`tests/test_dcp_surface_guard.py::test_fallback_patterns_covered_by_live_rules`)
  continues to hold without modification.

────────────────────────────────────────────────────────────

## Decision

Extend the existing negative-lookahead regex in `FORBIDDEN_PATHS` (introduced
by ADR-224) with two additional exact top-level filenames:

```python
re.compile(
    r"^\.github/workflows/"
    r"(?!embedded-audit\.yml$)(?!pr-steward\.yml$)"
    r"(?!pr-readiness-invalidator\.yml$)(?!pr-readiness-invalidation-writer\.yml$)"
    r".*$"
),
```

Invariants:

* Exactly four top-level workflow files are now exempted from the
  path-level block: `embedded-audit.yml`, `pr-steward.yml` (from ADR-224,
  unchanged), `pr-readiness-invalidator.yml`, and
  `pr-readiness-invalidation-writer.yml` (new in this ADR).
* Any other file under `.github/workflows/` — including subdirectories, and
  including near-miss names such as `pr-readiness-invalidator.yml.bak` or a
  same-named file nested under a subdirectory — remains hard-blocked.
* `TEXT_RULES` scanning in `red_lane_scanner.py` is untouched by this
  change and continues to apply unconditionally to all changed files,
  including all four carved-out workflow files. A forbidden-text match
  (e.g. a `gh pr merge` invocation) in any of them still produces a
  `BLOCKED` scan result via `MERGE_SEAM_VIOLATION`/other `TEXT_RULES`
  categories, independent of the path-level carve-out.

Non-goals:

* This ADR does not authorize editing the content of
  `embedded-audit.yml`/`pr-steward.yml` beyond what ADR-224 already
  authorized (unchanged).
* This ADR does not widen the carve-out to any other workflow file, present
  or future. A new carve-out for a different file requires its own ADR —
  same restriction ADR-224 placed on itself.
* This ADR does not reconcile the documented-vs-actual scope drift of
  `DCP-RED-MERGE-SEAM-0001` that ADR-224 already noted as a separate,
  out-of-scope governance cleanup.

────────────────────────────────────────────────────────────

## Alternatives Considered

**A. Remove the `.github/workflows/` entry from `FORBIDDEN_PATHS` entirely.**
Same rejection as ADR-224: reopens the seam for every workflow file, far too
broad for this narrow need.

**B. Hand-edit the two files outside the tool (raw filesystem write bypassing
the Edit tool).** Same rejection as ADR-224: does not fix the guard for
future sessions, defeats the purpose of a tool-enforced guard.

**C. Fold this into a wholesale re-review of ADR-224 rather than a new ADR.**
Rejected: ADR-224 explicitly reserved the right to remain narrowly scoped
and required a fresh ADR for any additional file, specifically so each
carve-out gets its own independent review of what capability is actually
being granted. Re-opening ADR-224 would blur that boundary for no benefit.

────────────────────────────────────────────────────────────

## Consequences

* **Easier**: the two named PR-readiness-invalidation workflow files can now
  be edited via the normal Edit/Write tool path, without a raw-filesystem
  bypass, enabling
  `TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A15-R1`'s S3 to proceed.
* **Harder/unchanged**: every other workflow file (including any not yet
  carved out) remains exactly as hard to edit as before.
* **Testing**: new focused tests at both the hook layer
  (`tests/test_dcp_surface_guard.py`) and the scanner layer
  (`tests/dcp/test_dcp_0005_red_lane_scanner.py`) pin the extension's exact
  boundaries: the two newly-exempted files, one still-blocked sibling
  workflow, one near-miss filename, one nested same-named file, and one
  proof that `TEXT_RULES` still fires on a carved-out file with forbidden
  content — mirroring ADR-224's test shape exactly.
* **Failure modes removed**: none — this is a narrowing exemption, not a
  removal of a check. The blocked set only shrinks by exactly two additional
  exact paths.
* **Failure modes introduced**: none identified. Verified against the same
  near-miss and nested-path cases ADR-224 verified, confirming the
  negative-lookahead-plus-`$`-anchor form does not accidentally broaden.

────────────────────────────────────────────────────────────

## Migration Strategy

* Step 1 (this ADR, Phase B): land the extended `FORBIDDEN_PATHS` regex plus
  its focused tests, in a clean worktree off
  `a06e21ae81a6ee3683c1c56ccedb1c56b866c718`, as a single local commit. No
  workflow file content changes in this step.
* Step 2 (immediately following, same packet): with the carve-out in place,
  wire `issue_comment` trigger + trusted-PR-resolution support into
  `.github/workflows/pr-readiness-invalidator.yml` and
  `.github/workflows/pr-readiness-invalidation-writer.yml`, mirroring the
  already-implemented template versions under
  `src/dopemux/templates/init/.github/workflows/`.
* Step 3: re-run the full DCP guard suite plus the PR-readiness-invalidation
  security suite (`tests/ci/test_pr_readiness_invalidation_security.py`,
  including its root/template byte-parity assertion) against the wired
  workflows to confirm no regression.

Rollback (this ADR only): `git revert <this-phase-B-commit-sha>` restores
the ADR-224-only two-file carve-out. Nothing pushed independently in Phase
B — it is integrated into the existing A15-R1 worktree before any push.

────────────────────────────────────────────────────────────

## Verification

* Tests added: `tests/test_dcp_surface_guard.py` (4 new: two carve-out
  positives, one near-miss-filename negative, one nested-path negative) and
  `tests/dcp/test_dcp_0005_red_lane_scanner.py` (3 new: carve-out clean,
  sibling-still-blocked, TEXT_RULES-still-active) — same shape as ADR-224's
  own verification set, applied to the two new files.
* Commands to run: `pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
* Expected signals: full pass, including the pre-existing
  `test_fallback_patterns_covered_by_live_rules` sync test (unaffected,
  since the fallback list never covered workflows).
* TDD discipline: RED confirmed for all 4 new positive-carve-out assertions
  before the regex change (failing for the correct reason — the guard
  blocking edits it should now allow); anti-vacuity confirmed by temporarily
  reverting the regex extension and reconfirming the same 4 assertions fail
  again before restoring the fix.

────────────────────────────────────────────────────────────

## Notes

* This ADR is Phase B of `TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R`; ADR-224 was
  Phase A. Both authorize the guard mechanism only — the actual workflow
  content wiring is a separately-tracked step within the packet that
  triggered each phase, per each ADR's own Migration Strategy.
* Documented-vs-actual scope drift of `DCP-RED-MERGE-SEAM-0001`
  (`docs/03-reference/dcp/README.md` not listing the workflows entry) is
  still not addressed here, consistent with ADR-224's own deferral.
* Related: `TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A15-R1` S3
  (issue-comment finality repair) — the packet whose blocked edit motivated
  this carve-out extension.
