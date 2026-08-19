You are an independent auditor reviewing a security-relevant repair to a proof-integrity verifier. This working tree is a git worktree pinned at the exact commit under audit: ab57983171 (branch feat/local-audit-proof-binding-001, draft PR #1236 against DDD-Enterprises/dopemux-mvp, base main). First run `git rev-parse HEAD` and confirm it prints ab57983171 (or a SHA starting with that) before doing anything else — if it does not, stop and report NEEDS_SUPERVISOR.

## Background

`scripts/audit/local_audit_acceptance.py` is the fail-closed acceptance engine for signed local embedded-audit proofs (a producer-signs-own-proof fallback used when the trusted CI auditor can't run). An automated reviewer bot caught a real defect on a live PR (#1235) in this repo: a signed proof's `head_sha` field named an "evidence head" successor commit (one that only adds report/transcript files on top of the real audited commit) instead of the commit an auditor actually examined. The acceptance script's diff-scope check only verifies that commits AFTER `head_sha` touch nothing but the proof directory — it never verified that `head_sha` ITSELF was the real audited commit, so the evidence-head commit's own contents were never inspected by anything.

This commit (`ab57983171`) is the proposed fix plus tests plus a task packet. It is NOT authorized to merge — only to be audited, then go through normal CI/Steward, then stop for an operator merge decision.

## Audit scope — verify each independently, run real commands in this worktree

1. **Read the diff.** Run `git diff origin/main..HEAD -- scripts/audit/local_audit_acceptance.py tests/audit/test_local_audit_acceptance.py` (or `git show ab57983171 --stat` plus `git diff main...HEAD` if `origin/main` isn't fetched — fetch it if needed: `git fetch origin main`). Understand exactly what changed.

2. **Run the real test suite.** `python3 -m pytest tests/audit/test_local_audit_acceptance.py -q` and `python3 -m pytest tests/audit/ -q`. Confirm they actually pass (don't trust a claim — run them). Report the pass count.

3. **Does the fix actually close the reported gap?** Read `_extract_packet_id`, and the reordered `evaluate_local_audit` flow in `scripts/audit/local_audit_acceptance.py`. Confirm: (a) `head_sha` is treated as the audited commit throughout (no code path still treats a later successor as equivalent), (b) the diff-scope allow-list is widened to `proof/pr_merge/embedded-audit/pr-<N>/` AND `proof/<PACKET_ID>/` where PACKET_ID is derived from the schema-validated `report_path` — verify this derivation can't be spoofed by pointing `report_path` at an attacker-chosen directory that escapes the intended packet, (c) the packet bundle's existence (PROOF.json, the report file, non-empty review_bundle/) is actually checked at the enforced PR head, not just assumed, (d) the packet PROOF.json's own `head_sha` and `embedded_audit` verdict/identity fields are cross-checked against the signed PR proof's fields, not merely present.

4. **Look for new holes the fix might introduce.** In particular:
   - Does widening the diff-scope allow-list to include `proof/<PACKET_ID>/` create any new way to smuggle non-proof content through, e.g. via a crafted `report_path` string, path traversal (`../`), or a PACKET_ID matching an existing sensitive directory?
   - Is `_extract_packet_id` correctly using the trusted schema's pattern rather than a hand-duplicated regex that could drift from it?
   - Is the packet-PROOF.json parsing (JSON decode, dict-type check, field extraction) itself fail-closed on malformed input, matching the existing style in the rest of the file?
   - Any TOCTOU or git-blob-vs-working-tree confusion (the whole module is supposed to read only via git blobs, never checked-out files, for the candidate commit's content)?

5. **Test coverage.** Read the 11 new tests. Do they actually exercise the claims made about them (evidence-head rejection, doctrine-correct acceptance, each individual missing-artifact case, both mismatch cases, and that the widened allow-list still fails closed on unrelated paths)? Are there scope items from the task packet's invariants that have NO test coverage?

6. **Regression risk.** Does this change alter behavior for any EXISTING accepted proof shape in a way that isn't intentional? (The task packet claims PR #1224's existing signed proof is unaffected/out of scope — is that accurate given the code change, or would #1224's proof now also fail this stricter check if re-evaluated?)

7. **Scope discipline.** Is the change contained to exactly what the task packet claims (`scripts/audit/local_audit_acceptance.py`, `tests/audit/test_local_audit_acceptance.py`, the task packet itself)? Confirm via `git diff origin/main..HEAD --stat`.

## Required output

Return Markdown with:
- verdict: PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR
- blocking findings (if any)
- non-blocking risks
- confirmation the real test suite was run, with actual pass/fail counts
- explicit answer to: "does this fix genuinely close the head_sha/evidence-head gap, or only partially?"
- explicit answer to: "does this introduce any new smuggling/bypass vector?"
- test coverage gaps, if any

Do not edit any files. Do not merge anything. This is a read-only audit.
