You are an independent auditor. This working tree is a git worktree pinned at exact commit cdc83dda65 (originally on branch feat/local-audit-proof-binding-001, draft PR #1236, base main). First run `git rev-parse HEAD` and confirm it starts with cdc83dda65.

## Background

This is round 2 (R2) of TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001, a repair to `scripts/audit/local_audit_acceptance.py` (the fail-closed acceptance engine for signed local embedded-audit proofs). Two prior independent audits (this file's ancestor commits ab57983171 and 05c41b3e6b) both returned PASS. After that, live PR #1236 received real automated code review with 7 comments, some genuine defects. This round's commit `cdc83dda65` (message: "fix(audit): R2 repair — exact blob/tree checks, packet_id identity, signer preflight parity") claims to fix them. Verify that claim independently — do not trust the commit message or my characterization below.

The 7 original review findings, verbatim:

1. **P1** (scripts/audit/local_audit_acceptance.py:502, chatgpt-codex-connector): "Prevent proof-only rewrites from redefining audited head" — an unaudited commit E could add code, a later commit could rewrite packet PROOF.json's head_sha to E and sign PR proof with the same E; `git diff E..HEAD` would contain only allowed proof paths, so the check would wrongly accept code that was never audited.
2. **P2** (line 482, chatgpt-codex-connector): "Require report path to resolve to a file" — the old check used `git ls-tree -r --name-only <rev> -- <path>`, which matches any descendant under a string prefix, so a directory literally named `AUDITOR_REPORT.md` containing `evidence.txt` would satisfy "report exists" without the required file ever existing.
3. **Copilot** (lines 508 and 519): "Packet bundle PROOF.json not validated for internal identity vs derived PACKET_ID" — nothing checked that the packet PROOF.json's own `packet_id` field agreed with the PACKET_ID this module derives from the signed `report_path`.
4. **P1** (task-packets/TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001.json:51, chatgpt-codex-connector): "Make every task-packet step schema-valid" — every step had a `status` field (undeclared) instead of a required non-empty `validation` array, so the packet fails schema validation.
5. **P2** (line 485, chatgpt-codex-connector): "Require review_bundle to be a nonempty tree" — same string-prefix bug as #2: a regular file or symlink named `review_bundle` would satisfy the old check without any real directory/evidence existing.
6. **P2** (line 479, chatgpt-codex-connector): "Validate packet bundle before signing" — `scripts/audit/sign_local_audit_proof.sh`'s preflight only checked PR-proof identity/status/model, not the new canonical-bundle requirements, so a broken bundle would sign locally ("proof shape OK") and only fail later in CI.
7. **P1** (proof/pr_merge/embedded-audit/pr-1236/PROOF.json:4, chatgpt-codex-connector): "Re-pin proof to commit in proposed history" — claimed `05c41b3e...` is not an ancestor of a squash-preview merge commit `ee653c64...`. I (the operator's assistant) checked this against the LIVE branch (not a squash preview) and found `05c41b3e6b` IS an ancestor of the current PR head via `git merge-base --is-ancestor` — please independently re-verify this yourself against this worktree's actual history and state whether finding #7 is applicable to the real branch or was anchored to a GitHub squash-merge preview artifact that doesn't reflect real branch history.

## Scope — verify each independently, do not take my summary on faith

1. Run `git log --oneline -8` to see this branch's real commit history. Run `git show cdc83dda65 --stat` for the R2 diff.
2. For finding #1 (P1, proof-only rewrite redefining audited head): read the module's new docstring "LIMITATION" section (search for `ATTESTED_AUDITED_SHA`) and the code path from `audited_sha = str(proof.get("head_sha")...)` through the packet-proof checks. Does the repair adequately document this as an inherent trust-model limitation (operator attestation, not cryptographic proof) rather than silently leaving it unaddressed? Is the STRUCTURAL guarantee it does enforce (no commit after the attested SHA can add code outside the two allowed proof trees) still real and unweakened? State plainly whether you agree this is the right disposition (document + bound the blast radius) versus something that should have been fixed differently.
3. For finding #2 (report_path resolving to a directory): find `_tree_type` and how `packet_report_absent` is now checked (should use exact blob check, not `_tree_has_entries`). Confirm a directory named like the report file is now correctly rejected. Read the new test `test_report_path_resolving_to_directory_is_rejected` in `tests/audit/test_local_audit_acceptance.py` and confirm it actually exercises this.
4. For finding #5 (review_bundle as a file): find the fixed `_tree_has_entries` (should now check `_tree_type(...) == "tree"` before ls-tree). Read `test_review_bundle_as_a_file_is_rejected` and confirm it exercises this.
5. For finding #3 (packet_id identity): find the new `packet_proof_packet_id_mismatch` check. Read `test_packet_proof_packet_id_mismatch_is_rejected` and confirm it exercises this correctly.
6. For finding #4 (task packet schema): run `python3 -c "import json,jsonschema; jsonschema.validate(json.load(open('task-packets/TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001.json')), json.load(open('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json')))"` and confirm it validates cleanly with no error.
7. For finding #6 (signer preflight parity): read the diff to `scripts/audit/sign_local_audit_proof.sh`. Does its Python preflight heredoc now independently re-derive PACKET_ID from report_path and check the packet bundle (report file, review_bundle dir, packet PROOF.json existence/head_sha/packet_id/verdict-identity) using the SAME logic the trusted acceptance engine enforces? Run `bash -n scripts/audit/sign_local_audit_proof.sh` to confirm it's syntactically valid.
8. For finding #7 (ancestor check): run `git merge-base --is-ancestor 05c41b3e6bebaa6b8854af5da0dbad9207ac5227 HEAD && echo ANCESTOR || echo NOT_ANCESTOR` in this worktree. State the actual result and whether finding #7 is applicable to this real branch history.
9. Run `python3 -m pytest tests/audit -q` and report exact pass/fail/skip counts. Run `python3 -m pytest tests/audit/test_local_audit_acceptance.py -q -v 2>&1 | tail -20` and confirm the 3 new regression tests (report-as-directory, review_bundle-as-file, packet_id-mismatch) are present and passing.
10. Anything ELSE wrong, fragile, incomplete, or newly introduced by this R2 diff that the 7 findings didn't already name — including any NEW smuggling/bypass vector the fix itself might introduce.

## Required output

Markdown with:
- Verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR
- For EACH of the 7 findings above: state explicitly whether it is now RESOLVED, PARTIALLY RESOLVED (with why), or STILL PRESENT (with why) — don't just say "looks fixed."
- The real pytest counts (not summarized/rounded).
- Any newly-introduced risk.
- One-paragraph bottom line: is this R2 commit ready to be treated as the controlling audited head for a fresh canonical proof bundle?

Do not edit files. Read-only audit.
