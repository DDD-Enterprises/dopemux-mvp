You are an independent auditor. This working tree is a git worktree pinned at exact commit 5224218c67 (originally on branch feat/local-audit-proof-binding-001, draft PR #1236, base main). First run `git rev-parse HEAD` and confirm it starts with 5224218c67.

## Background

This is round 6 (R6) of TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001, a repair to `scripts/audit/sign_local_audit_proof.sh` (the local signer for embedded-audit proofs; the trusted acceptance engine itself, `scripts/audit/local_audit_acceptance.py`, is unchanged this round). Five prior rounds preceded this one (R1 `ab57983171`/`05c41b3e6b`, R2 `cdc83dda65`, R3 `a26474698c`, R4 `8e9b802729`, R5 `5adc090065`, all independently audited PASS). After R5 was pushed, two more live review findings surfaced on PR #1236, both about the signer's filesystem-based preflight diverging from the trusted acceptance engine's git-blob-based reality. This round's commit `5224218c67` (message: "fix(audit): R6 repair — signer rejects symlinked packet artifacts and uncommitted bundles") claims to fix them. Verify that claim independently — do not trust the commit message or my characterization below.

The 2 findings, verbatim:

1. **P2** (scripts/audit/sign_local_audit_proof.sh:95, chatgpt-codex-connector): "Reject symlinked packet artifacts before signing" — unlike the prior symlink-only bundle-ENTRY case (R5), a symlink AT the report_path itself, or a symlinked review_bundle ROOT, still passes this preflight: `Path.is_file()` and `Path.is_dir()` follow symlinks, and `rglob()` sees regular files beneath a symlinked directory. The script signs successfully, but the committed symlink has mode `120000`; `evaluate_local_audit()` rejects the report as non-regular (or the bundle as non-tree) in CI. Requested: explicitly reject symlinks on the report path and the bundle root, not just entries within it.
2. **P2** (scripts/audit/sign_local_audit_proof.sh:91, chatgpt-codex-connector): "Validate packet bundle from committed Git tree" — when the required packet bundle is untracked or modified only in the working tree, the filesystem-based checks pass and the signer reports "proof shape OK", even though CI reads the bundle from the enforced PR-head's committed git blobs. The printed "next steps" only stage the PR-scoped proof directory (`git add ${PROOF_DIR}/`), so following them literally would leave the packet bundle absent or stale at the pushed head, guaranteeing `packet_proof_absent` or similar rejection in CI. Requested: require the bundle to already be committed at the expected tree state, or stage both proof trees.

## Scope — verify each independently, do not take my summary on faith

1. Run `git log --oneline -16` and `git show 5224218c67 --stat` for the R6 diff.
2. For finding #1: independently confirm that `pathlib.Path.is_file()` and `Path.is_dir()` follow symlinks in Python (you can test this directly: `python3 -c "import os,tempfile,pathlib; d=tempfile.mkdtemp(); real=pathlib.Path(d)/'real.txt'; real.write_text('x'); link=pathlib.Path(d)/'link.txt'; link.symlink_to(real); print(link.is_file(), link.is_symlink())"`). Then read the fix in `scripts/audit/sign_local_audit_proof.sh` in THIS worktree — does it now explicitly check `is_symlink()` for BOTH the report file AND the review_bundle root directory (not just entries inside it, which R5 already covered)?
3. For finding #2: read the fix. Does it now check `git status --porcelain -- <packet_dir>` (or equivalent) and fail closed if there are any uncommitted changes under the packet bundle directory? Does the check correctly distinguish "clean/committed" from "dirty/untracked/modified"? Construct your own quick scratch git repo to verify: init a repo, create an uncommitted file under a directory, run `git status --porcelain -- <that-directory>` yourself and confirm it produces non-empty output; then commit it and confirm the same command produces empty output.
4. Run and confirm these tests pass, and that they genuinely exercise the scenarios described (construct real git repos / real symlinks, not just asserting strings): `python3 -m pytest tests/audit/test_local_audit_acceptance.py::test_signer_preflight_rejects_uncommitted_packet_bundle tests/audit/test_local_audit_acceptance.py::test_signer_preflight_rejects_symlinked_report_and_bundle_root -v`
5. Dogfooding check: this repository's own real PR #1236 proof bundle (`proof/TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001/` and `proof/pr_merge/embedded-audit/pr-1236/`) is legitimately committed. Run `bash scripts/audit/sign_local_audit_proof.sh 1236` yourself in this worktree (you do NOT have the real signing key, so the final `ssh-keygen -Y sign` step will fail — that's fine and expected) and confirm the PREFLIGHT portion still prints "proof shape OK" for this legitimate, already-committed bundle, i.e. the R6 fix does not produce a false-positive rejection for the correct case.
6. Think adversarially once more: is there any other way the signer's preflight could diverge from what the trusted acceptance engine actually sees at the committed PR head? Consider: a packet bundle that's committed but then modified afterward without re-committing (partially dirty), a bundle where only SOME files are committed and others are new/untracked, or a bundle committed on a different branch/worktree than the one being signed in. State explicitly whether you found anything, and if so describe it precisely.
7. Run `python3 -m pytest tests/audit -q` and report exact pass/fail/skip counts (count dots in the progress output directly if the final summary line doesn't render).
8. Run `bash -n scripts/audit/sign_local_audit_proof.sh` to confirm valid syntax.
9. Anything ELSE wrong, fragile, incomplete, or newly introduced by this R6 diff — including any regression versus R1-R5 protections, or any usability regression (e.g. an overly strict check that would reject a perfectly legitimate, fully-committed bundle).

## Required output

Markdown with:
- Verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR
- For EACH of the 2 findings: RESOLVED / PARTIALLY RESOLVED (why) / STILL PRESENT (why), with the actual commands you ran and their real output.
- Your adversarial analysis from step 6, explicitly.
- Confirmation from the dogfooding check in step 5.
- The real pytest counts.
- Any newly-introduced risk, regression, or usability false-positive versus R1-R5.
- One-paragraph bottom line: is this R6 commit ready to be treated as the controlling audited head for a fresh canonical proof bundle?

Do not edit files. Read-only audit.
