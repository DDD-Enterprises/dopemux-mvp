# Auditor Report — TP-DMX-CI-AUDIT-EVIDENCE-GATE-001-A5-R5-FINALIZATION-TRUST-CLOSURE-001

Independent Claude Sonnet 5 audit for PR #1330 R5 finalization-trust-closure content,
frozen head `25326aca3ef3e3d40ff9d0da68d8aa61fc0a2b67`, accepted parent `7c0cf162b31f73ed9ec3fec6f3db93bceca2711a` (the prior R4-audited,
proof-published head). Isolated subprocess invocation, no tools, no mutation authority,
no memory of the orchestrating session's implementation work.

## Verdict

```json
{
  "status": "COMPLETED",
  "verdict": "PASS",
  "audited_head": "25326aca3ef3e3d40ff9d0da68d8aa61fc0a2b67",
  "audited_tree": "4978ab7459707377ccdef79a5ec1ececfa92237a",
  "validation_status": "NOT_RUN"
}
```

## Rationale

Static review of the 6 canonical source/workflow files and 3 test files in the accepted_parent..frozen_head diff. All five scoped capabilities are implemented correctly and fail-closed: (1) MERGE_READINESS.json is authenticated via verify_pr_steward_readiness_artifact using the same workflow/run/PR/head/base identity binding, exact-single-artifact selection, not-expired/bounded-size checks, safe zip-member extraction (shared _archive_member_bytes helper now used by both proof and readiness paths, guaranteeing parity), byte-identical local-vs-downloaded comparison, and post-download identity recheck as the audit-proof path. (2) PR_STEWARD_SOURCE_RECEIPT.json is emitted inside the trusted artifact by pr-steward.yml from workflow-internal values and is only ever cross-checked against externally-resolved identity: steward run_id comes from the live commit status, not the receipt; artifact name is derived from caller-supplied expected_pr/expected_head_sha, not the receipt; every receipt field is compared to caller-supplied or GitHub-fetched values. (3) verify_workflow_artifact is now always called with audit_run_id=trusted_audit_run_id from the authenticated receipt in the NOT_REQUIRED path; the run ID remains a locator only because verify_workflow_artifact independently re-verifies workflow id/path/name, run repository/status/conclusion/event, artifact-run head consistency, proof semantics, digest, member bytes, live PR state, and post-download metadata. test_authenticated_source_receipt_pins_exact_audit_run_with_ambiguous_repo_artifacts demonstrates repo-wide ambiguity no longer blocks and the unpinned lookup is never issued. (4) _resolve_steward_run_id_from_readiness_status filters statuses to the exact context, selects the unique latest by timestamp, requires that single entry's state be success, and does not consult older entries; test_latest_steward_readiness_status_must_be_successful confirms an older success cannot rescue a newer non-success. (5) repo=None is resolved once via client.repo or resolve_repo_slug() and written back to client.repo in _merge_prepared_result, require_steward_finalization_gate, and _run_gate; the same resolved slug flows to steward_gate, both verifiers, live PR verification, and run_merge_with_fallback. Preserved contracts: strict PASS/PASS still allows without network; PASS_WITH_RISKS on either side still denies; NOT_REQUIRED/SKIPPED canonical-form checks are unchanged. Every new failure mode in steward_gate is inside try/except Exception returning a _deny; no fall-through to allow exists. Mirror hunks are textually identical to src/ in the supplied patch; byte-identity of all 12 mirrors is an operator-verified claim not independently executed here. Operator-supplied pytest/ruff receipts are treated as claims; nothing was executed. No blocking defect found.

## Findings

1. NONBLOCKING COVERAGE GAP: DENY_READINESS_CHANGED (steward_gate.py) has no direct test analogous to test_local_proof_replacement_during_authentication_denies. Fail-closed by inspection.
2. NONBLOCKING COVERAGE GAP: DENY_AUDIT_RUN_ID_MISMATCH has no test exercising a caller-supplied audit_run_id that disagrees with the receipt's audit_run_id at the steward_gate/CLI level. Fail-closed by inspection.
3. NONBLOCKING COVERAGE GAP: test_retrieval_failure_has_no_offline_fallback covers only the five audit fetch methods, not the six new fetch_steward_*/download_steward_artifact methods, for RuntimeError propagation.
4. NONBLOCKING OBSERVATION: fetch_steward_readiness_status uses the combined-status endpoint, which GitHub already dedupes to one entry per context; the latest/tie-break logic is defense-in-depth largely unexercised by live data.
5. NONBLOCKING OBSERVATION: the combined-status call is unpaginated (default 30 contexts); a head with >30 contexts could omit the PR Steward context, causing a fail-closed denial (availability, not security).
6. NONBLOCKING OBSERVATION: GITHUB_ACTIONS_DETAILS_URL_RE (pre-existing, reused) doesn't bind owner/repo in target_url, but client.repo scoping (client_repo_mismatch) makes this moot.
7. NONBLOCKING OBSERVATION (contract detail): _archive_member_bytes tightens the pre-existing proof path (rejects traversal/symlink members archive-wide, not just the target); reason code for '../PROOF.json' changed to proof_archive_member_unsafe (acknowledged in test comment); allow/deny outcome for well-formed archives is unchanged.
8. NONBLOCKING OBSERVATION: redundant staleness re-check after successful authentication (harmless duplicate).
9. NONBLOCKING OBSERVATION: duplicate live-PR fetch (fetch_steward_pr and fetch_audit_pr both hit pulls/{pr_id}).
10. NONBLOCKING OBSERVATION: the 'forged_local_audit_run_id' test parametrization actually exercises local_readiness_bytes_mismatch, not run-id logic (test name overstates coverage).
11. VERIFIED EDGE (not a defect): receipt-write step is if: success() while status-publish is if: always(); a failed receipt step still fails closed via steward_run_not_successful or missing-receipt-member checks.
12. VERIFIED: receipt fields are sourced from workflow-internal values (GITHUB_RUN_ID, steps.audit_run.outputs.id, steps.audit.outputs.*, steps.proof.outputs.*); base_sha output is bound before the hard conclusion gate.
13. VERIFIED: run.head_sha for the workflow_run-triggered PR Steward run is correctly not bound to expected_head_sha (candidate-head binding instead comes from artifact name, readiness/receipt content, and live PR head).
14. VERIFIED: allowed steward run events {workflow_run, workflow_dispatch} match workflow triggers; workflow_dispatch requires default-branch head_branch and PR base.ref, mirroring the audit-proof verifier.

## Remaining risks

1. PRE-EXISTING TRUST ASSUMPTION (inherited): steward run_id authenticity ultimately depends on statuses:write being restricted to the trusted CI identity; downstream checks substantially limit forgery impact but status-creator identity is not itself verified.
2. PRE-EXISTING LIMITATION (explicitly preserved per scope): strict PASS/PASS finalization performs no network authentication of either artifact.
3. PRE-EXISTING / DEFERRED (noted in workflow comment, out of packet scope): branch protection still references the old check-name context; this diff correctly does not modify branch protection.
4. PRE-EXISTING TRUST ASSUMPTION: resolve_repo_slug() depends on the merge specialist's own top-level checkout/git config, not the untrusted PR worktree — same assumption as existing callers.
5. VALIDATION RECEIPTS ARE CLAIMS: pytest and ruff results are operator-reported, not independently executed (validation_status NOT_RUN).
6. MIRROR PARITY IS OPERATOR-VERIFIED: textual comparison of supplied patch hunks matches; full byte-identity of all 12 mirrors was not independently executed by this review.
7. TIE-BREAK FAIL-CLOSED: identical-timestamp statuses deny rather than choose — safe direction, not a bypass.

## Inspected paths

- src/dopemux_pr_merge_specialist/github_api.py
- src/dopemux_pr_merge_specialist/queue_drain.py
- src/dopemux_pr_merge_specialist/steward_gate.py
- src/dopemux_pr_merge_specialist/workflow_artifact_verifier.py
- src/dopemux_pr_steward/cli.py
- .github/workflows/pr-steward.yml
- tests/dopemux_cli/test_pr_steward_cmd.py
- tests/pr_merge_specialist/test_finalization_gate.py
- tests/pr_merge_specialist/test_workflow_artifact_verifier.py
- .claude/skills/.../{github_api,queue_drain,steward_gate,workflow_artifact_verifier}.py (patch hunks textually compared to src/, not byte-diffed)
- .github/skills/.../{github_api,queue_drain,steward_gate,workflow_artifact_verifier}.py (patch hunks textually compared to src/, not byte-diffed)
- templates/skills/.../{github_api,queue_drain,steward_gate,workflow_artifact_verifier}.py (patch hunks textually compared to src/, not byte-diffed)

## Evidence references

- workflow_artifact_verifier.py:_archive_member_bytes
- workflow_artifact_verifier.py:_resolve_steward_run_id_from_readiness_status
- workflow_artifact_verifier.py:verify_pr_steward_readiness_artifact
- workflow_artifact_verifier.py:verify_workflow_artifact
- steward_gate.py:steward_gate
- queue_drain.py:require_steward_finalization_gate
- queue_drain.py:_merge_prepared_result
- cli.py:_run_gate
- github_api.py:GitHubClient.fetch_steward_readiness_status
- .github/workflows/pr-steward.yml:'Select and download independent audit artifact'
- .github/workflows/pr-steward.yml:'Write PR Steward source receipt'
- .github/workflows/pr-steward.yml:'Publish readiness status on candidate PR head'
- test_workflow_artifact_verifier.py:test_exact_authenticated_steward_readiness_binds_bytes_and_source_receipt
- test_workflow_artifact_verifier.py:test_latest_steward_readiness_status_must_be_successful
- test_workflow_artifact_verifier.py:test_steward_source_receipt_identity_mismatch_denies
- test_finalization_gate.py:test_authenticated_source_receipt_pins_exact_audit_run_with_ambiguous_repo_artifacts
- test_finalization_gate.py:test_live_queue_finalization_uses_client_repo_and_exact_pr_state
- test_finalization_gate.py:test_strict_pass_does_not_require_network_authentication
