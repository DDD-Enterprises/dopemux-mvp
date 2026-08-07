---
id: ADR-224
title: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for two embedded-audit workflow files
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-03'
last_review: '2026-08-03'
next_review: '2026-11-03'
prelude: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for two embedded-audit workflow files (adr) for dopemux documentation and developer workflows.
status: accepted
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
    - TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001
---
# ADR-224: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for two embedded-audit workflow files

════════════════════════════════════════════════════════════

## Status

* Accepted

## Date

* 2026-08-03

## Owners

* Supervisor (DDD-Enterprises), executed by Claude (agent session), Phase A of
  `TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R`

────────────────────────────────────────────────────────────

## Context

`DCP-RED-MERGE-SEAM-0001` is a tool-enforced, PreToolUse hard-deny red lane
(`.claude/hooks/dcp_surface_guard.py`, backed by
`src/dopemux/dcp/red_lane_rules.py::FORBIDDEN_PATHS`) that blocks inline
edits to a fixed list of paths regardless of task-packet authorization. One
entry in that list is a blanket pattern covering the entire workflows
directory:

```python
re.compile(r"^\.github/workflows/.*$"),
```

This is broader than the seam's own documented invariant. `docs/03-reference/dcp/README.md`
describes `DCP-RED-MERGE-SEAM-0001`'s constraint only in terms of
`src/dopemux_pr_merge_specialist/queue_drain.py`'s `execute=True` seam and
`scripts/batch_resolve_and_merge.py` — it does not mention
`.github/workflows/` at all. The code-level rule has grown past the
documented scope at some point after the README was last reviewed; this ADR
does not attempt to reconcile that broader drift, only to carve a narrow,
reviewed exception out of the current blanket rule.

The concrete trigger: `TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001`
(S3, commit `54eee6743b`) needed to wire a new function,
`schema_validate_embedded_audit()` (in `scripts/audit/run_embedded_audit.py`,
already merged in that packet's S3 commit and covered by its own tests), into
the two CI workflows that gate embedded-audit proofs:
`.github/workflows/embedded-audit.yml` and `.github/workflows/pr-steward.yml`.
Both files were read in full during that packet and confirmed to contain no
auditor-tool- or auditor-model-specific logic — the wiring needed is a single
additional function call in each, already proven correct against the schema
and against the shared `enforce_independent_audit_proof` gate via unit and
integration tests. The edit was attempted and hard-blocked by the guard, with
no workaround attempted (per governance: the seam requires "an ADR + task
packet" to lift, not an inline edit or bypass).

Pain points:

* The blanket pattern blocks *any* workflow edit, including narrowly-scoped,
  fully-tested, non-merge-related additions like this one.
* Widening the seam wholesale (removing the workflows entry entirely) would
  reopen the seam's original purpose — preventing DCP-adjacent code from
  quietly gaining GitHub-mutation or merge-automation capability via CI
  workflow edits — for all ~dozens of files under `.github/workflows/`, most
  of which are unrelated to this admission and have not been reviewed here.

Constraints:

* This ADR's own authorizing decision (`SEAM_LIFT_001R_PHASE_A=AUTHORIZED`)
  explicitly forbids Phase A from editing either workflow file's content —
  only the guard mechanism and its tests may change in this phase.
* `TEXT_RULES` content-level scanning (`red_lane_scanner.py`) must remain
  fully active on the carved-out files; this ADR authorizes a path-level
  exemption only, not a content-level one.
* Every other path under `.github/workflows/` must remain blocked exactly as
  before.

────────────────────────────────────────────────────────────

## Decision

Replace the blanket `.github/workflows/` forbidden-path pattern in
`FORBIDDEN_PATHS` with a single regex that forbids everything under
`.github/workflows/` **except** the two exact top-level filenames
`embedded-audit.yml` and `pr-steward.yml`, implemented via negative
lookahead so the exemption is anchored to the literal filename at the end of
the path (not a prefix or substring match):

```python
re.compile(
    r"^\.github/workflows/"
    r"(?!embedded-audit\.yml$)(?!pr-steward\.yml$)"
    r".*$"
),
```

Invariants:

* Only `.github/workflows/embedded-audit.yml` and
  `.github/workflows/pr-steward.yml` (exact top-level paths) are exempted
  from the path-level block.
* Any other file under `.github/workflows/` — including subdirectories, and
  including near-miss names such as `embedded-audit.yml.bak` or a same-named
  file nested under a subdirectory — remains hard-blocked.
* `TEXT_RULES` scanning in `red_lane_scanner.py` is untouched by this
  change and continues to apply unconditionally to all changed files,
  including the two carved-out workflow files. A forbidden-text match (e.g.
  a `gh pr merge` invocation) in either file still produces a `BLOCKED`
  scan result via `MERGE_SEAM_VIOLATION`/other `TEXT_RULES` categories,
  independent of the path-level carve-out.
* `_FALLBACK_COMPILED` in `.claude/hooks/dcp_surface_guard.py` is left
  unchanged: it never included a workflows entry in the first place, so the
  fallback-⊆-live sync invariant (`tests/test_dcp_surface_guard.py::test_fallback_patterns_covered_by_live_rules`)
  continues to hold without modification.

Non-goals:

* This ADR does not authorize editing the content of either workflow file.
  That is a separate, later phase (or a follow-up packet) once this carve-out
  lands and is reviewed.
* This ADR does not reconcile the documented vs. actual scope drift of
  `DCP-RED-MERGE-SEAM-0001` noted above (the README undercounts the seam's
  real blocked-path list). That is out of scope here and is noted for a
  separate governance cleanup.
* This ADR does not widen the carve-out to any other workflow file, present
  or future. A new carve-out for a different file requires its own ADR.

────────────────────────────────────────────────────────────

## Alternatives Considered

**A. Remove the `.github/workflows/` entry from `FORBIDDEN_PATHS` entirely.**
Pros: simplest change, no regex complexity. Cons: reopens the seam for every
workflow file, including CI-authority-critical ones with actual merge/PR
mutation logic (e.g. anything invoking `gh pr merge`) — exactly what the
seam exists to prevent. Rejected as far too broad for the narrow, reviewed
need at hand.

**B. Keep the blanket block; hand-edit the two files as an "operator seam
lift" outside the tool (e.g. raw filesystem write bypassing Claude's Edit
tool).** Pros: no code change to the guard. Cons: does not fix the
guard for future sessions/agents, relies on a human remembering to repeat
the bypass every time, and defeats the purpose of a tool-enforced guard by
routing around it rather than governing it. Rejected — this is the "inline
edit workaround" the seam's own message explicitly warns against.

**C. Add an allowlist file (e.g. `.dcp-seam-allowlist.json`) that the guard
reads at runtime, rather than hardcoding the two filenames in the regex.**
Pros: extensible without future ADRs. Cons: introduces a new mutable
runtime authority surface for a hard-deny security boundary — exactly the
kind of soft, driftable configuration the seam is designed to avoid — and
none of the exemption's narrow, ADR-reviewed intent survives if that file is
later edited without a fresh ADR. Rejected in favor of an explicit,
ADR-anchored regex.

────────────────────────────────────────────────────────────

## Consequences

* **Easier**: the two named workflow files can now be edited (by a
  subsequent, separately-authorized phase) via the normal Edit/Write tool
  path, without requiring a raw-filesystem bypass.
* **Harder/unchanged**: every other workflow file remains exactly as hard to
  edit as before — no regression in the seam's coverage for anything else.
* **Testing**: new focused tests at both the hook layer
  (`tests/test_dcp_surface_guard.py`) and the scanner layer
  (`tests/dcp/test_dcp_0005_red_lane_scanner.py`) pin the carve-out's exact
  boundaries: the two exempted files, one still-blocked sibling workflow,
  one near-miss filename, one nested same-named file, and one proof that
  `TEXT_RULES` still fires on a carved-out file with forbidden content.
* **Failure modes removed**: none — this is a narrowing exemption, not a
  removal of a check. The blocked set only shrinks by exactly two exact
  paths; all other failure-mode coverage (`TEXT_RULES`, other
  `FORBIDDEN_PATHS` entries, the fallback sync invariant) is unchanged.
* **Failure modes introduced**: none identified. The regex was verified
  against near-miss and nested-path cases specifically to rule out an
  accidental broadening (e.g. a naive `.startswith()`-style exemption would
  have also exempted `embedded-audit.yml.bak` or nested copies — the
  negative-lookahead-plus-`$`-anchor form does not).

────────────────────────────────────────────────────────────

## Migration Strategy

* Step 1 (this ADR, Phase A): land the narrowed `FORBIDDEN_PATHS` regex plus
  its focused tests, in a clean worktree off `origin/main`, as a single
  local commit. No workflow file content changes in this step.
* Step 2 (future, separately authorized): with the carve-out in place, wire
  `schema_validate_embedded_audit()` (already implemented and tested in
  `scripts/audit/run_embedded_audit.py` per
  `TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001` S3) into
  `.github/workflows/embedded-audit.yml` and `.github/workflows/pr-steward.yml`,
  per the exact patch already documented in that packet's
  `proof/TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001/S3_WORKFLOW_BINDING.md`.
* Step 3 (future): re-run the full DCP guard suite plus the embedded-audit /
  PR Steward integration suites against the wired workflows to confirm no
  regression, then proceed through that packet's remaining stages.

Rollback (this ADR only): `git revert <this-phase-A-commit-sha>` restores
the blanket `.github/workflows/.*` block. Nothing pushed in Phase A, so no
remote state to unwind.

────────────────────────────────────────────────────────────

## Verification

* Tests added: `tests/test_dcp_surface_guard.py` (5 new: two carve-out
  positives, one sibling-workflow negative, one near-miss-filename negative,
  one nested-path negative) and `tests/dcp/test_dcp_0005_red_lane_scanner.py`
  (3 new: carve-out clean, sibling-still-blocked, TEXT_RULES-still-active).
* Commands to run: `pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
* Expected signals: full pass, including the pre-existing
  `test_fallback_patterns_covered_by_live_rules` sync test (unaffected,
  since the fallback list never covered workflows).

────────────────────────────────────────────────────────────

## Notes

* Follow-up packet/phase needed to actually wire the two workflow files —
  tracked as Step 2/3 above, gated on this ADR's acceptance and on a fresh
  supervisor authorization (this ADR authorizes the guard carve-out only,
  not the workflow edits themselves).
* Documented-vs-actual scope drift of `DCP-RED-MERGE-SEAM-0001`
  (`docs/03-reference/dcp/README.md` not listing the workflows entry, or the
  several `services/*` and `docker/*` entries also present in
  `FORBIDDEN_PATHS`) is noted here as an observation, not addressed — a
  separate governance cleanup would need its own ADR to either narrow the
  code to match the README or update the README to match the code.
* Related: `TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001` S3
  (`proof/TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001/S3_WORKFLOW_BINDING.md`,
  `S3_HANDOFF.md`) — the packet whose blocked edit motivated this carve-out.
