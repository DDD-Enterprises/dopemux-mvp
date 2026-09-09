# Auditor Report — TP-DMX-CI-AUDIT-EVIDENCE-GATE-001-A5-R4-FINALIZATION-AUTHENTICITY-CLOSURE-001

Publication of the already-completed independent Claude Sonnet 5 audit for
PR #1330 exact frozen substantive content head `34386f315dd7ca32cfd5c009c50281d4a34dd8b7`.
This is a proof-only republication; the verdict, findings, and risks below
are reproduced verbatim from the raw audit evidence (`/private/tmp/dmx-s4-hook.gWqV1q/final-audit/`)
with no reinterpretation or re-execution.

## Verdict

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "audited_head": "34386f315dd7ca32cfd5c009c50281d4a34dd8b7",
  "audited_tree": "6087a939bb336dc7eb929f87a374780f60e28f9d",
  "validation_status": "NOT_RUN"
}
```

## Rationale

This is a static, tool-free review of the supplied diff/context only; I did not execute tests, ruff, or any command myself, and treat the packet's reported command outputs as claims, not independent evidence. The commit adds workflow_artifact_verifier.py plus wiring in steward_gate.py, github_api.py, queue_drain.py, dopemux_pr_steward/cli.py, and pr-steward.yml so that the previously purely-local 'NOT_REQUIRED' (trusted change-contract SKIPPED) finalization evidence is now additionally authenticated against a live GitHub Actions artifact download, with exact byte-for-byte comparison of the downloaded PROOF.json against the local proof. Tracing the logic by hand: (1) the new authentication path is scoped strictly to the FINALIZATION class and only when proof_embedded_audit_status=='SKIPPED' after local semantic validation via independent_audit_errors already passed (steward_gate.py:100-121); the strict-PASS path is untouched and does not invoke any network call, confirmed by the added test test_strict_pass_does_not_require_network_authentication. (2) Any exception from verify_workflow_artifact (WorkflowArtifactError or a bare RuntimeError from github_api.py's retrieval helpers) is caught and converted to DENY_AUDIT_ARTIFACT_AUTHENTICITY (steward_gate.py:133-155) — there is no offline fallback path I could find. (3) verify_workflow_artifact.py binds repository, workflow id/path/name, run id/workflow_id/path/name/status/conclusion/event/run_attempt, artifact name/id/expired/size/digest, exact single PROOF.json zip member (rejecting nested paths, symlinks, oversized entries, and duplicate/ambiguous names), byte-identical downloaded vs local proof, then re-fetches artifact/run metadata post-download and requires exact dict equality to catch a race/tamper during the verification window, and finally re-checks the live PR head/base/state as the last network call before returning. (4) steward_gate.py additionally re-reads the local proof file after verification and denies with DENY_AUDIT_PROOF_CHANGED if it changed underneath the check, closing a local-file TOCTOU window. (5) Caller identity propagation looks correct end-to-end: the CLI (dopemux_pr_steward/cli.py:181-195) and queue_drain._merge_prepared_result (queue_drain.py:584-590) both pass the same GitHubClient instance whose .repo equals the expected_repo argument, and verify_workflow_artifact independently asserts client.repo == expected_repo as a defense-in-depth check. (6) Mirror parity across .claude/, .github/, src/, and templates/ for the four modified modules is byte-identical in the diff hunks shown, and test_template_contracts.py was extended to assert this for all three non-canonical locations in addition to the pre-existing templates-vs-src loop (now including workflow_artifact_verifier.py in MODULES). (7) Scope constraints were respected: embedded-audit.yml, run_embedded_audit.py, schemas, signer/credential files, and job permissions are unchanged; only pr-steward.yml (in scope, as the consumer) was modified, and it fails closed via the existing 'set -euo pipefail' shell context if the new verify_workflow_artifact call raises. I found no logic bypass, no injection risk (all subprocess calls use argv lists, never shell=True, and expected_repo is regex-constrained before being interpolated into any endpoint string), and bounded reads/sizes throughout (MAX_ARCHIVE_BYTES, MAX_PROOF_BYTES) mitigate zip-bomb/DoS-via-oversized-artifact concerns. The added test suite (tests/pr_merge_specialist/test_workflow_artifact_verifier.py) is unusually thorough, covering exact-match/ambiguity, digest presence/absence, retrieval-failure-per-method, download races, workflow_dispatch ref trust, and CLI end-to-end forged-vs-genuine bytes; existing finalization tests were updated only where HEAD_SHA/BASE_SHA needed to become valid 40-hex (required by the new sha_invalid regex) and were augmented with new deny-path tests, without weakening any previously-DENYing assertion I could locate in the diff. Given the depth of static evidence but the complete absence of any execution on my part, and a few legitimate non-blocking risk notes below, PASS_WITH_RISKS rather than a clean PASS is the calibrated verdict.

## Findings

1. No blocking correctness or security defects identified in the diff by static trace-through of steward_gate.py, workflow_artifact_verifier.py, github_api.py, queue_drain.py, dopemux_pr_steward/cli.py, and pr-steward.yml.
2. The new online-authentication gate is correctly scoped to the FINALIZATION + NOT_REQUIRED(SKIPPED) case only; STRICT PASS finalization and REMEDIATION class are unaffected and remain purely local, per steward_gate.py:100-156 and the added test test_strict_pass_does_not_require_network_authentication in tests/pr_merge_specialist/test_finalization_gate.py.
3. Fail-closed on retrieval/authentication failure is enforced with no offline fallback: any exception in verify_workflow_artifact() is caught and converted to DENY_AUDIT_ARTIFACT_AUTHENTICITY in steward_gate.py:133-155, exercised by tests/pr_merge_specialist/test_workflow_artifact_verifier.py::test_retrieval_failure_has_no_offline_fallback and tests/pr_merge_specialist/test_finalization_gate.py::test_finalization_authentication_unavailable_denies.
4. Local-proof TOCTOU is closed: steward_gate.py re-reads audit_proof_path after network verification and denies with DENY_AUDIT_PROOF_CHANGED if bytes changed mid-check (steward_gate.py:144-145), exercised by test_local_proof_replacement_during_authentication_denies.
5. Caller identity (repo) is propagated consistently: CLI (dopemux_pr_steward/cli.py:188) and queue_drain._merge_prepared_result (queue_drain.py:586-587) both pass the same GitHubClient whose .repo matches expected_repo; workflow_artifact_verifier.py:99 independently asserts client.repo == expected_repo as defense in depth.
6. Mirror parity for the four changed modules (github_api.py, queue_drain.py, steward_gate.py, workflow_artifact_verifier.py) across src/, templates/, .claude/, and .github/ is byte-identical per the diff hunks and the manifest's mirrors[].equal=true entries; test_template_contracts.py was extended to assert byte equality for .claude/.github mirrors and workflow_artifact_verifier.py was added to the pre-existing templates-vs-src MODULES parity loop.
7. Scope was respected: no changes to .github/workflows/embedded-audit.yml, scripts/audit/run_embedded_audit.py, schemas, signer/credential files, or job permissions; the only workflow changed (pr-steward.yml) is the intended consumer of the new verifier, and its permissions block is untouched.
8. Bounded-size/anti-zip-bomb and anti-zip-slip controls are present (MAX_ARCHIVE_BYTES, MAX_PROOF_BYTES, exact-filename-only single-member match, symlink rejection) in workflow_artifact_verifier.py:137-149.

## Remaining risks

1. Non-blocking, pre-existing (not introduced by this diff): the STRICT PASS finalization path (both merge_readiness and audit proof status=='PASS') still relies entirely on locally-supplied JSON bytes with no online GitHub authentication, unlike the newly-hardened NOT_REQUIRED path. This asymmetry predates this commit and is out of this diff's scope, but remains a standing trust gap worth a future packet.
2. Operational (intended tradeoff, not a bug): finalization for NOT_REQUIRED evidence now depends on the embedded-audit GitHub Actions artifact still being retrievable (not expired/deleted) at merge time. If artifact retention lapses between audit-time and a delayed merge, steward_gate will correctly DENY per the fail-closed contract, but this introduces a new availability dependency operators should be aware of.
3. download_audit_artifact() in github_api.py bypasses the client's existing retry/backoff wrapper (_run) and performs a single subprocess.run with no retry, so a single transient network blip during artifact download will fail closed rather than retry — acceptable per the fail-closed contract but a possible source of spurious denials under flaky network conditions.
4. The new verify_workflow_artifact() call embedded in pr-steward.yml's heredoc has no explicit try/except or stderr diagnostic message before failing (unlike the adjacent 'Validate audit workflow-run identity' step), so operators will see a raw Python traceback rather than a curated error line; this is a minor observability gap, not a security or correctness issue.
5. This review is static only; I did not execute the test suite, ruff, or any script referenced in the packet's validation summary myself, so I cannot independently corroborate the reported 1263/2/2 pytest counts or ruff findings beyond reading the diff and inline test code.

## Inspected paths

- .github/workflows/pr-steward.yml
- src/dopemux_pr_merge_specialist/github_api.py
- src/dopemux_pr_merge_specialist/queue_drain.py
- src/dopemux_pr_merge_specialist/steward_gate.py
- src/dopemux_pr_merge_specialist/workflow_artifact_verifier.py
- src/dopemux_pr_steward/cli.py
- tests/dopemux_cli/test_pr_steward_cmd.py
- tests/pr_merge_specialist/test_finalization_gate.py
- tests/pr_merge_specialist/test_template_contracts.py
- tests/pr_merge_specialist/test_workflow_artifact_verifier.py
- .claude/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/{github_api,queue_drain,steward_gate,workflow_artifact_verifier}.py (mirror, byte-diff verified equal to src)
- .github/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/{github_api,queue_drain,steward_gate,workflow_artifact_verifier}.py (mirror, byte-diff verified equal to src)
- templates/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/{github_api,queue_drain,steward_gate,workflow_artifact_verifier}.py (mirror, byte-diff verified equal to src)
- .github/workflows/embedded-audit.yml (unchanged, read-only context only)
- scripts/audit/run_embedded_audit.py (unchanged, read-only context only, reused via import)

## Evidence references

- src/dopemux_pr_merge_specialist/steward_gate.py:100-121 — authentication scoped only to FINALIZATION + proof_embedded_audit_status=='SKIPPED' after independent_audit_errors passes
- src/dopemux_pr_merge_specialist/steward_gate.py:133-155 — try/except around verify_workflow_artifact with DENY_AUDIT_ARTIFACT_AUTHENTICITY on any exception, no offline fallback
- src/dopemux_pr_merge_specialist/steward_gate.py:144-145 — post-verification re-read of audit_proof_path with DENY_AUDIT_PROOF_CHANGED on mismatch
- src/dopemux_pr_merge_specialist/workflow_artifact_verifier.py:74-96 — expected_repo/pr/sha format validation and local proof identity binding before any network call
- src/dopemux_pr_merge_specialist/workflow_artifact_verifier.py:98-126 — workflow/run identity, status/conclusion, event allowlist, artifact-run head consistency, freshness check
- src/dopemux_pr_merge_specialist/workflow_artifact_verifier.py:128-149 — bounded archive/proof size limits, exact single PROOF.json member, symlink rejection, byte-exact comparison
- src/dopemux_pr_merge_specialist/workflow_artifact_verifier.py:151-168 — post-download recheck of artifact/run equality (race mitigation) and live PR head/base/state binding, workflow_dispatch ref trust
- src/dopemux_pr_merge_specialist/queue_drain.py:584-590 — github_client=client, expected_repo=client.repo passed together to require_steward_finalization_gate
- src/dopemux_pr_steward/cli.py:181-195 — CLI constructs GitHubClient(repo=args.repo, ...) matching expected_repo=args.repo
- .github/workflows/pr-steward.yml:293-309 — new verify_workflow_artifact call gated on embedded_audit.required is False, using AUDIT_RUN_ID as a pinned locator, inside the existing set -euo pipefail run block
- tests/pr_merge_specialist/test_workflow_artifact_verifier.py:122-269 — exact-tuple binding test matrix, retrieval-failure-per-method, download-race, digest-optional, existing-GitHubClient-route tests
- tests/pr_merge_specialist/test_finalization_gate.py:409-454 — forged-proof denial, authentication-unavailable denial, local-proof-replacement denial, strict-pass-no-network tests
- tests/pr_merge_specialist/test_template_contracts.py:55-58 — new byte-equality assertions for .claude/.github mirrors of the four changed modules
