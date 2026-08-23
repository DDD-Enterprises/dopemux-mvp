---
id: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
stage: PHASE_A
artifact: PHASE_A_VALIDATION
---
# Phase A validation — guard carve-out + ADR-224

## Scope implemented

Commit `9e113e68d0` on top of `origin/main` at
`ff08e573b4259ac7456dae1a9985968603e9111d` (verified undrifted). Exactly 4
files changed:

```
docs/90-adr/adr-224-dcp-workflow-seam-narrow-carveout.md   (new)
src/dopemux/dcp/red_lane_rules.py                          (modified, 12 lines)
tests/dcp/test_dcp_0005_red_lane_scanner.py                (modified, +44 lines)
tests/test_dcp_surface_guard.py                            (modified, +40 lines)
```

No `.github/workflows/*` file content was edited in Phase A.

## Test results

```
pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v
  → 42 passed (34 pre-existing + 8 new focused carve-out tests)

pytest tests/dcp/ -v
  → 173 passed, 1 failed
  → the 1 failure is test_16_no_forbidden_files_modified, proven pre-existing
    and identical on origin/main in BASELINE_FAILURE_PROOF.md — not a
    regression from this change.
```

New focused tests added:

* `tests/test_dcp_surface_guard.py`: `test_embedded_audit_workflow_is_carved_out`,
  `test_pr_steward_workflow_is_carved_out`, `test_other_workflow_files_remain_blocked`,
  `test_near_miss_backup_filename_remains_blocked`,
  `test_nested_carved_out_filename_remains_blocked`.
* `tests/dcp/test_dcp_0005_red_lane_scanner.py`:
  `test_carved_out_workflow_paths_are_not_forbidden_path_findings`,
  `test_other_workflow_paths_still_forbidden_path_blocked`,
  `test_carved_out_workflow_still_subject_to_text_rules` — this last test
  proves `TEXT_RULES` content scanning still fires (`MERGE_SEAM_VIOLATION`)
  on a carved-out file whose content contains forbidden text, confirming the
  carve-out is path-only, not a content exemption.

## Other gates

```
git diff --check --cached      → exit 0, clean
pre-commit run --files <the 4 changed files>
                                → all hooks Passed or Skipped (no-files),
                                  including change-contract-preflight and
                                  docs-frontmatter-guard
secret-pattern scan (sk-/ghp_/AKIA/private-key/api-key patterns)
                                → 1 hit, pre-existing fake-secret test
                                  fixture at tests/dcp/test_dcp_0005_red_lane_scanner.py:197
                                  (predates this diff, outside the added hunk,
                                  itself a negative-test fixture for the
                                  scanner's own redact_secret_like() logic —
                                  not a real credential)
```

## Verdict

`PASS` for the scope actually authorized in Phase A (ADR + guard carve-out +
focused tests). No workflow content changed. No regression introduced
against `origin/main`'s existing test posture.
