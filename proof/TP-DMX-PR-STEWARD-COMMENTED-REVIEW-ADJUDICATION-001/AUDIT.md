# AUDIT — TP-DMX-PR-STEWARD-COMMENTED-REVIEW-ADJUDICATION-001

Two independent adversarial review rounds via Codex (`codex:codex-rescue`), requested
because the originating directive required a reviewer from a different model family than
the implementer (Claude Sonnet 5). These are supplementary evidence; the schema-of-record
`embedded_audit` field in `PROOF.json` is a Claude Code self-audit — see
`AUDITOR_REPORT.md` for why (Codex is not a valid `embedded_audit.auditor_tool` and
AGENTS.md §9.1 forbids Codex as a formal auditor).

## Round 1 — verdict FAIL (pre-fix, commit c48554e29)

Codex job `task-mtkx2i11-td1k8i`. Full findings:

> 1. Verdict: FAIL
> 2. Test Suite Result: sandbox lacked a writable temp dir for the literal pytest
>    invocation; a read-only-compatible rerun gave 238 passed, 46 errors — all temp-dir
>    fixture/setup failures unrelated to this change, not adjudication assertion
>    failures. The feature-specific file alone: 13 passed.
> 3. Invariant walkthrough: HOLDS on CHANGES_REQUESTED exclusion, exact review_id/head_sha
>    binding, trusted-author gating, malformed-receipt rejection, unresolved-thread/CI
>    independence.
> 4. BROKEN: conflicting/differing eligible receipts were not detected when differing
>    bytes parsed to the same signature (dedup ignored non-field lines / extra bytes).
> 5. BROKEN: byte-identical duplicate receipts from two different trusted approvers
>    conflicted, because the dedup signature included `adjudicator`, contrary to the
>    "byte-identical duplicates count once" rule in the docs.

## Fix (commit af145c4b1)

`_find_review_adjudication` changed to key conflict detection on the raw comment `body`
string, dropping `adjudicator` and the parsed-field tuple from the comparison entirely.
Two regression tests added:
`test_byte_identical_body_from_two_different_trusted_authors_is_not_a_conflict`,
`test_same_parsed_fields_but_different_raw_bytes_is_a_conflict`. Docs updated to state the
comparison is byte-for-byte on the raw comment body.

## Round 2 — verdict PASS (post-fix, commit af145c4b1)

> 1. Fix correctness — PASS. `_body` is internal only ... does not leak into the returned
>    receipt/rationale path. Trust gate still applies per comment before parse/dedup.
>    Piggyback bypass: refuted — an untrusted author's comment is skipped at the trust
>    check before it ever reaches body parsing or dedup.
> 2. Diff review (c48554e29..af145c4b1) — matches the described fix, scope-clean. Only
>    three files touched. No unrelated changes slipped in.
> 3. Test results — PASS on the real (non-noise) run. The literal `pytest tests/pr_steward/
>    -q .` command (trailing dot) broadens collection into unrelated duplicate-basename
>    test trees and fails — a collection-scope artifact, not a sandbox or pr-steward
>    regression. Targeted rerun: 286 passed in 2.04s. The two new regression tests: 2
>    passed.
> 4. Regression check on the other 7 invariants — all HOLD (CHANGES_REQUESTED,
>    head/review_id binding, untrusted-author rejection, malformed-receipt rejection,
>    ledger conservation, receipt-comment self-nonblocking, CI/audit/thread/security-release
>    independence).
> 5. Final verdict: PASS. The fix is sound: the trust gate is enforced independently of and
>    prior to the body-based dedup, `_body` doesn't leak into the ledger output, and no
>    piggyback bypass exists. Both originally-flagged bugs are fixed and covered by
>    regression tests. All previously-HELD invariants still hold, and the diff introduces
>    no unrelated changes.

Both rounds confirmed: no push, edit, merge, or PR #1287 mutation was performed during
either audit — read-only throughout.
