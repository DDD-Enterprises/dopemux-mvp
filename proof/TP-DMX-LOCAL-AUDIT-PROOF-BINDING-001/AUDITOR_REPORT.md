# Auditor Report — TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 (controlling: R5)

**Audited commit**: `5adc090065aae3c9d88a32022787a42d6c7b26c4`
**Auditor**: `agy` / `gemini-3.1-pro-high`, `--mode plan`, read-only git worktree audit

This is the CONTROLLING report. It supersedes the R1-R4 audits preserved in
`review_bundle/` as non-controlling historical evidence.

## Verdict: PASS

Independent verification of the R5 commit `5adc090065` on
`feat/local-audit-proof-binding-001`, addressing 2 fresh findings from live
review on PR #1236.

### Findings disposition

1. **P2 (symlink-only review bundles/report_path)**: **RESOLVED**.
   Independently reproduced: `git ls-tree` reports a symlink's mode as
   `120000` while its object TYPE is still `blob` (its blob content is a
   target path string, not stored evidence) — the R3 gitlink fix's
   type-only check (`type == "blob"`) did not catch this. R5 adds
   `_REGULAR_FILE_MODES = {"100644", "100755"}` and `_is_regular_file`,
   checking git MODE (not merely type) in both `_tree_has_entries`
   (review_bundle) and the report_path exact-file check — the double
   application was necessary, since a symlinked `report_path` could
   otherwise bypass the same class of check. Confirmed via direct test
   execution (`test_review_bundle_symlink_only_is_rejected`,
   `test_report_path_as_symlink_is_rejected`, both passed).
2. **P2 (signer packet-ID derivation drift)**: **RESOLVED**. The signer
   script previously re-derived `packet_id` via its own inline
   pattern-match-and-split logic, never learning about R4's `pr_merge`
   reservation. R5 removes that parallel logic and imports the ACTUAL
   `_extract_packet_id` from `local_audit_acceptance.py`, guaranteeing
   parity going forward. Confirmed via direct test execution
   (`test_signer_preflight_rejects_reserved_pr_merge_packet_id`, passed).

### Adversarial analysis (independently performed)
Checked empty blobs (not a structural vulnerability — a valid committed
file), legacy/unusual modes (excluded from `_REGULAR_FILE_MODES`, fail
closed), newline-containing path injection (safely isolated by the
tab-split before mode/type parsing), and deeply nested trees (flattened
correctly by `ls-tree -r`, only terminal entries checked). No new bypasses
found.

### Pytest counts (real execution, not summarized)
- `tests/audit`: **403 passed, 1 skipped**

### Newly-introduced risks / regressions vs R1-R4
None identified. R4's reserved-namespace protection is strictly preserved
and now additionally propagates to the signer, closing the drift risk for
good.

### Bottom line
Commit `5adc090065` resolves both outstanding findings with fail-closed
logic and is ready to be treated as the controlling audited head for this
canonical proof bundle.

---

Full raw transcript and prompt: `review_bundle/AGY_AUDIT_R5_RAW.json`,
`review_bundle/AGY_AUDIT_R5_PROMPT.md`. One prior invocation attempt for
this round returned top-level `status: ERROR` (an internal cascade-step
failure unrelated to the audit's substance — "no such directory") despite
containing plausible-looking content; per standing policy that run was NOT
promoted to a verdict and is preserved as
`review_bundle/AGY_AUDIT_R5_ATTEMPT1_ERROR_STATUS_NONCONTROLLING.json` —
its conclusions happen to corroborate the clean controlling run above, but
are explicitly non-controlling. R1-R4 audits remain in `review_bundle/` as
superseded historical evidence.
