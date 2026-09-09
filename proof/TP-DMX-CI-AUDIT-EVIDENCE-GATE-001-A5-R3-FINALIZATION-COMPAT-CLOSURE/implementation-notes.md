# R3 S1-S4 implementation notes

## Scope

- Added finalization test matrix before runtime repair.
- Added one exact finalization predicate: strict `PASS` pair or two independently exact trusted not-required records.
- Preserved raw FINALIZATION status, `required`, and `skip_reason` values.
- Preserved REMEDIATION uppercase normalization and `PASS_WITH_RISKS` acceptance.
- Removed queue drain's broader duplicate finalization interpretation; it now consumes `steward_gate` result.
- Synchronized only six packet-authorized mirror modules.
- Updated finalization reference documentation.
- Replaced inherited R1 `worktree.path` absolute value with portable `"."`.

## TDD evidence

- RED: exit 1; 8 failed, 65 passed. Failures matched missing exact not-required behavior, direct-gate `PASS_WITH_RISKS` leak, raw metadata loss, and pre-TTL rejection.
- GREEN: exit 0; 118 passed in focused finalization file.
- Existing direct steward gate: exit 0; 6 passed.
- Template contracts: exit 0; 3 passed.

## Integrity evidence

- `steward_gate.py` SHA-256: `4280f2e456bdbc741ba05f754ec6795eb6dbde166fb11239c806dea60bb399a0` across four copies.
- `queue_drain.py` SHA-256: `d925b94f9cf8944dee49e91e77a13c808cd8c11d5c9c528fb1a6240afc158d39` across four copies.
- Parsed inherited R1 proof before/after differs only at `worktree.path`; after value is `"."`.
- Inherited R1 embedded-audit schema: 1/1 PASS.
- Inherited R1 review manifest: five entries, zero mismatches.
- Signature coupling: NOT_APPLICABLE; no signature file observed, and review manifest does not cover `PROOF.json`.
- `git diff --check`: PASS.
- Narrow Ruff check for changed predicate module and test file: PASS.

## Remaining validation ownership

- Complete suite: NOT_RUN; root-owned after focused green.
- Changed-contract validation, pre-commit, secret scan, commits, audit, and GitHub closure: NOT_RUN; root-owned.
- Formal independent L3 audit: NOT_RUN.
- Non-gating whole-module Ruff probe on `queue_drain.py`: FAIL with 79 existing-file diagnostics outside changed finalization block; baseline comparison NOT_RUN and no cleanup attempted.
