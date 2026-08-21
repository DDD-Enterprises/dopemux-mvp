You are an independent auditor. This working tree is a git worktree pinned at exact commit 8e9b802729 (originally on branch feat/local-audit-proof-binding-001, draft PR #1236, base main). First run `git rev-parse HEAD` and confirm it starts with 8e9b802729.

## Background

This is round 4 (R4) of TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001, a repair to `scripts/audit/local_audit_acceptance.py` (the fail-closed acceptance engine for signed local embedded-audit proofs). Three prior rounds preceded this one (R1 `ab57983171`/`05c41b3e6b`, R2 `cdc83dda65`, R3 `a26474698c`, all independently audited PASS). After R3 was pushed, one more live review finding surfaced on PR #1236. This round's commit `8e9b802729` (message: "fix(audit): R4 repair — reject reserved pr_merge namespace as a PACKET_ID") claims to fix it. Verify that claim independently — do not trust the commit message or my characterization below.

The finding, verbatim:

**P2** (scripts/audit/local_audit_acceptance.py:507, chatgpt-codex-connector): "Constrain packet IDs before widening proof scope" — when the signed `report_path` is `proof/pr_merge/AUDITOR_REPORT.md`, the trusted schema's `report_path` pattern (`^proof/[^/]+/AUDITOR(_REPAIR(_[0-9]+)?)?_REPORT\.md$`) accepts `pr_merge` as a valid PACKET_ID (since the wildcard segment has no way to know that name is reserved), making the second allowed diff-scope prefix `proof/pr_merge/`. Since `proof/pr_merge/embedded-audit/pr-<N>/` is the SHARED root every PR's own signed proof lives under (not just this one PR's), a proof successor commit could then modify or delete ANY OTHER PR's historical signed attestation while the "proof-only delta" check still passes, because everything under `proof/pr_merge/` — including other PRs' proofs — would fall inside the (wrongly widened) allow-list. Requested fix: reject reserved/non-task-packet IDs before constructing the allow-list prefix, or validate against exact packet-bundle paths rather than an unconstrained derived directory.

## Scope — verify each independently, do not take my summary on faith

1. Run `git log --oneline -12` and `git show 8e9b802729 --stat` for the R4 diff.
2. Confirm the vulnerability was real BEFORE this commit: check out the parent commit's version of `_extract_packet_id` (`git show a26474698c:scripts/audit/local_audit_acceptance.py | grep -A30 'def _extract_packet_id'`) and independently confirm that, prior to R4, `report_path = "proof/pr_merge/AUDITOR_REPORT.md"` would schema-match and derive `packet_id = "pr_merge"`. You can verify the schema pattern match directly: `python3 -c "import re,json; s=json.load(open('schemas/proof/embedded_audit.schema.json')); print(re.match(s['properties']['report_path']['pattern'], 'proof/pr_merge/AUDITOR_REPORT.md'))"`.
3. Read the fix in `_extract_packet_id` in the CURRENT (R4) tree. Does it reject a derived segment equal to `RESERVED_PACKET_NAMESPACE`? Where is `RESERVED_PACKET_NAMESPACE` defined, and is it derived from the same `PROOF_DIR_TEMPLATE` constant the rest of the module uses for the PR-scoped proof path (so it can't silently drift out of sync), or is it a separate hard-coded literal that could diverge?
4. Confirm the fix actually closes the vulnerability end-to-end: read and RUN `tests/audit/test_local_audit_acceptance.py::test_extract_packet_id_rejects_reserved_pr_merge_namespace` and `tests/audit/test_local_audit_acceptance.py::test_report_path_colliding_with_reserved_namespace_is_rejected_end_to_end` directly (`python3 -m pytest tests/audit/test_local_audit_acceptance.py::test_extract_packet_id_rejects_reserved_pr_merge_namespace tests/audit/test_local_audit_acceptance.py::test_report_path_colliding_with_reserved_namespace_is_rejected_end_to_end -v`). Confirm both pass and genuinely exercise the scenario (not a name-only assertion that happens to pass for the wrong reason).
5. Think adversarially: is there any OTHER string a malicious/careless signer could put in report_path that would still let the diff-scope allow-list widen to touch paths outside this one packet's own directory? For example: what about a packet_id containing path-traversal-looking characters that are technically `[^/]+` (no literal slash) but might behave unexpectedly when concatenated into `f"{packet_dir}/"` and compared via Python string `.startswith()` against real git diff paths (which are always repo-root-relative, no `..`)? State explicitly whether you found any such residual bypass, and if so describe it precisely.
6. Run `python3 -m pytest tests/audit -q` and report exact pass/fail/skip counts.
7. Run `bash -n scripts/audit/sign_local_audit_proof.sh` to confirm valid syntax (unrelated to this fix, but confirms nothing else broke).
8. Anything ELSE wrong, fragile, incomplete, or newly introduced by this R4 diff — including any regression versus R1/R2/R3 protections.

## Required output

Markdown with:
- Verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR
- Explicit confirmation the vulnerability was real pre-R4 (with your own reproduction, not just trusting the finding text).
- Explicit statement whether the fix is RESOLVED / PARTIALLY RESOLVED (why) / STILL PRESENT (why), with the actual commands you ran and their real output.
- Your adversarial analysis from step 5, explicitly.
- The real pytest counts.
- Any newly-introduced risk or regression versus R1/R2/R3.
- One-paragraph bottom line: is this R4 commit ready to be treated as the controlling audited head for a fresh canonical proof bundle?

Do not edit files. Read-only audit.
