You are an independent auditor. This working tree is a git worktree pinned at exact commit 05c41b3e6b (branch feat/local-audit-proof-binding-001, draft PR #1236, base main). First run `git rev-parse HEAD` and confirm it starts with 05c41b3e6b.

## Background

An earlier independent audit (verdict PASS) examined commit ab57983171 on this same branch — the substantive verifier fix plus 59 tests. That audit flagged two minor test-coverage gaps as non-blocking: no direct test for `packet_proof_malformed` (invalid JSON in the packet PROOF.json) and no direct test for the `_extract_packet_id` defensive branch when a report_path doesn't match the schema pattern. This is a NARROW follow-up: commit 05c41b3e6b adds exactly two new tests on top of ab57983171 to close those two gaps, and nothing else.

## Scope — verify each independently

1. Run `git diff ab57983171..05c41b3e6b --stat` and `git diff ab57983171..05c41b3e6b`. Confirm the ONLY change is additions to `tests/audit/test_local_audit_acceptance.py` — no production code in `scripts/audit/local_audit_acceptance.py` changed, no other file touched.
2. Run `python3 -m pytest tests/audit/test_local_audit_acceptance.py -q` and `python3 -m pytest tests/audit/ -q`. Confirm they pass and report exact counts.
3. Read the two new tests (`test_packet_proof_malformed_json_is_rejected` and `test_extract_packet_id_returns_none_for_non_matching_report_path`). Do they genuinely exercise what they claim — malformed JSON in the packet proof correctly rejected with `packet_proof_malformed`, and `_extract_packet_id` correctly returning `None` for a non-matching report_path (and the correct packet id for a matching one)?
4. Anything wrong, fragile, or misleading about these two specific tests.

## Required output

Markdown with: verdict (PASS/PASS_WITH_RISKS/FAIL/NEEDS_SUPERVISOR), confirmation the diff is test-only, confirmation the real test suite passed with counts, and a one-line verdict on whether these two additions genuinely close the two gaps the prior audit named.

Do not edit files. Read-only audit.
