You are an independent auditor. This working tree is a git worktree pinned at exact commit 60391753f5 (originally on branch feat/local-audit-proof-binding-001, draft PR #1236, base main). First run `git rev-parse HEAD` and confirm it starts with 60391753f5.

## Background

This is the combined R7+R8 audit of TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 (neither round has been independently audited as a controlling head yet -- R7 was audited PASS_WITH_RISKS but never became the controlling proof before R8 landed on top of it, so this audit covers both diffs together). Six prior rounds preceded this one (R1 through R6, all independently audited PASS or PASS_WITH_RISKS, all still controlling scripts/audit/local_audit_acceptance.py -- the trusted acceptance engine itself has been UNCHANGED since R4).

R7 (commit ae90ff3c33) fixed: a symlinked packet_proof_path (proof/<PACKET_ID>/PROOF.json) not being rejected by the signer preflight, and a stale operator runbook (docs/ops/embedded-audit.md) describing the pre-R6 commit ordering.

R8 (commit 60391753f5) fixed: a symlinked packet_dir itself (proof/<PACKET_ID>) not being guarded, which would silently bypass every leaf-level symlink check R5-R7 added (since Path.is_symlink() only inspects the final path component, not ancestors). This finding was surfaced by the R7 independent audit's OWN adversarial analysis, not a live GitHub review comment.

## IMPORTANT: severity taxonomy for this audit

Every review finding from R5 onward has been in `scripts/audit/sign_local_audit_proof.sh` (the LOCAL SIGNER's filesystem-based preflight), not `scripts/audit/local_audit_acceptance.py` (the TRUSTED ACCEPTANCE ENGINE CI actually runs, which reads committed git blobs and has been unchanged since R4). Every one of these findings has the same shape: the signer's local preflight might say "OK" for something the trusted acceptance engine would still correctly reject once pushed. This is a **diagnostic-quality / operator-UX gap** (a bad proof might need an extra round-trip to discover it's bad), NOT a **trust-boundary bypass** (nothing has ever let CI actually ACCEPT invalid content) -- the system has remained fail-closed throughout.

Apply this classification explicitly in your findings:
- If you find something that would let `local_audit_acceptance.py` (the CI-side engine) ACCEPT a proof it should reject -- i.e. an actual security/trust bypass -- call this out as BLOCKING regardless of where it lives.
- If you find something where the SIGNER's local preflight might diverge from what CI ultimately decides (a false "OK" locally, or a false rejection locally, that CI's real check would resolve correctly either way) -- classify this as a NON-BLOCKING documented risk, not a blocking finding. Name it precisely, but do not withhold PASS for it alone.

This is the operator's own established severity model (already applied to name a materially identical case non-blocking in the R6 proof bundle) -- your job is to correctly classify findings against it, not to treat every asymmetry between the signer and the engine as blocking.

## Scope

1. Run `git log --oneline -20` and `git diff ae90ff3c33^..60391753f5 --stat` for the combined R7+R8 diff (i.e. everything since the last controlling audit at R6's `5224218c67`).
2. Verify the R7 fixes: symlinked packet_proof_path rejection, and the runbook documentation update in `docs/ops/embedded-audit.md`.
3. Verify the R8 fix: read the restructured symlink-guard block in `scripts/audit/sign_local_audit_proof.sh` (search for `packet_dir_ok`). Confirm it correctly guards ALL FIVE downstream checks that depend on `packet_dir` (report_file, review_bundle_dir presence, review_bundle_dir contents, git-dirty check, packet_proof_path) -- enumerate each one and confirm it's actually gated by `packet_dir_ok`, not accidentally left ungated.
4. Run and confirm these tests pass and genuinely exercise their scenarios: `python3 -m pytest tests/audit/test_local_audit_acceptance.py::test_signer_preflight_rejects_symlinked_packet_proof tests/audit/test_local_audit_acceptance.py::test_signer_preflight_rejects_symlinked_packet_dir -v`
5. Dogfooding: run `bash scripts/audit/sign_local_audit_proof.sh 1236` against the real, already-committed, legitimate PR #1236 bundle in this worktree. Confirm the preflight still prints "proof shape OK" -- no false-positive regression across R7+R8 combined.
6. Adversarial pass, WITH THE TAXONOMY ABOVE IN MIND: look for anything else in the signer's packet-bundle-reading logic that could still diverge from `local_audit_acceptance.py`'s actual git-blob-based checks. For each thing you find, explicitly classify it as BLOCKING (CI-side acceptance bypass) or NON-BLOCKING (signer-preflight-only divergence, fails closed regardless) per the taxonomy above. Do not automatically treat every such finding as blocking.
7. Separately: confirm `scripts/audit/local_audit_acceptance.py` itself has NOT changed since R4 (`git diff 8e9b802729..60391753f5 -- scripts/audit/local_audit_acceptance.py` should be empty) -- the trusted acceptance engine's own logic has been stable for 4 rounds; only the signer's preflight has kept moving.
8. Run `python3 -m pytest tests/audit -q` and report exact pass/fail/skip counts.
9. Run `bash -n scripts/audit/sign_local_audit_proof.sh` to confirm valid syntax.

## Required output

Markdown with:
- Verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR
- Confirmation R7 and R8 fixes are both RESOLVED, with actual commands/output.
- Explicit confirmation from step 7 that the acceptance engine itself is unchanged since R4.
- Your classified adversarial findings from step 6 (if any), each explicitly labeled BLOCKING or NON-BLOCKING per the taxonomy, with reasoning.
- Dogfooding confirmation from step 5.
- Real pytest counts.
- One-paragraph bottom line: is this R7+R8 commit ready to be treated as the controlling audited head for a fresh canonical proof bundle? If your verdict is PASS_WITH_RISKS, list every risk by name.

Do not edit files. Read-only audit.
