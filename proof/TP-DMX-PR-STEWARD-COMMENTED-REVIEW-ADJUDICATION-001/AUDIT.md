# AUDIT — TP-DMX-PR-STEWARD-COMMENTED-REVIEW-ADJUDICATION-001

Three review passes preceded the controlling audit of record. All are preserved here as
supplementary/historical evidence; the current `embedded_audit` field in `PROOF.json` and
`AUDITOR_REPORT.md` is the AGY / Gemini 3.1 Pro High run (see below), per
`docs/ops/embedded-audit.md` Tier-1 route #1.

## Pass 0 (superseded) — Claude Code self-audit, verdict PASS

Performed by the implementing session itself against commit `af145c4b1`. Superseded as
the audit of record because `docs/ops/embedded-audit.md`'s Local Claude Code / CLI route
requires the auditing session to not be the one that wrote the diff — a condition this
pass did not meet. Its invariant-by-invariant walkthrough matched the AGY run's
conclusions on all ten invariants; full text below for the record.

<details>
<summary>Full superseded Claude Code self-audit report</summary>

**Auditor**: Claude Code CLI (Sonnet) — Tier-1 self-audit per AGENTS.md §9.1
**Audited head**: `af145c4b10b67fd9c4dbcd6ec44fb31cca73dfca`
**Verdict**: PASS

### Scope

`tools/pr_steward/classifier.py`, `tests/pr_steward/test_commented_review_adjudication.py`,
`docs/ops/pr-steward.md`. No other paths touched (verified via `git status --short` against
the packet's FORBIDDEN list, and via `git diff --stat` against `main`).

### Invariant-by-invariant check (against the originating directive's MANDATORY_TESTS / NEVER OVERRIDABLE list)

1. **No receipt → historical COMMENTED P1/P2 review stays MUST_FIX.** Confirmed:
   `_classify_reviews` only reaches `_find_review_adjudication` inside the `else` branch
   taken when the review is neither unknown-author nor `CHANGES_REQUESTED`; with no
   matching receipt, `receipt is None` and the original `_body_disposition` result stands.
   Test: `TestNoReceipt`.
2. **Valid trusted exact-head receipt clears; ledger conserved; original preserved.**
   Confirmed: `_review_item`'s `body` is built from the *original* review body, never the
   receipt; only `disposition`/`blocking`/`rationale` change. Item count is unaffected —
   the receipt logic never adds/removes ledger entries, only reclassifies an existing one.
   Tests: `TestValidReceipt`, `TestLedgerConservation`.
3. **Wrong head → no clearance.** `_find_review_adjudication` requires
   `receipt["head_sha"] == pr_head_sha` exactly. Test: `TestWrongHead`.
4. **Wrong review_id → no clearance.** Exact string equality required. Test:
   `TestWrongReviewId`.
5. **Untrusted author → no clearance.** `author not in trusted_approvers` skips the
   comment before it is even parsed as a candidate. Test: `TestUntrustedAuthor`.
6. **Malformed receipt → no clearance.** `_parse_review_adjudication_receipt` requires all
   four fields, exact `disposition` value, non-empty `review_id`/`reason`, and a
   40-lowercase-hex `head_sha`; any failure returns `None`, which
   `_find_review_adjudication` skips. Tests: `TestMalformedReceipt` (missing field, short
   SHA).
7. **Two conflicting eligible receipts → no clearance.** Fixed in af145c4b1 to compare raw
   comment bytes (see finding below). Tests: `TestConflictingReceipts` (four cases:
   differing content, byte-identical from same author, byte-identical from two different
   trusted authors, same parsed fields but different bytes).
8. **CHANGES_REQUESTED + otherwise-valid receipt → still blocking.** The
   `CHANGES_REQUESTED`/`REQUEST_CHANGES` branch in `_classify_reviews` returns before the
   `else` branch that consults receipts is ever reached — structurally unreachable, not
   just untested. Test: `TestChangesRequestedNeverOverridable`.
9. **Unresolved inline thread remains blocking.** `_classify_threads` is a wholly separate
   code path never touched by this change. Test: `TestUnresolvedThreadUnaffected`.
10. **Valid receipt issue-comment itself is nonblocking**, even when its `reason=` text
    contains "P1"/"P2" substrings. `_classify_comments` checks
    `_parse_review_adjudication_receipt(body) is not None` for a trusted `issue_comment`
    author *before* falling through to the ordinary `_body_disposition` P1/P2 heuristic.
    Test: `TestReceiptCommentItselfIsNonblocking`.
11. **Review-ledger conservation count remains exact.** Unaffected — no items added or
    removed by this change, only reclassified. Test: `TestLedgerConservation`.
12. **Existing review/comment/thread classification tests remain green.** Full
    `tests/pr_steward/` suite: 286 passed (284 pre-existing + 2 new fix-regression tests),
    0 failed, 0 errors.

### Finding: conflict dedup used parsed fields + adjudicator, not raw bytes (RESOLVED)

Identified by the round-1 Codex review below. Fixed by keying the dedup set on the raw
comment body string, dropping `adjudicator` from the comparison — see the AGY report's
citations for the exact fixed lines.

</details>

## Pass 1 (informal/supplementary) — Codex adversarial review, two rounds

Requested because the originating directive required a reviewer from a different model
family than the implementer (Claude Sonnet 5). Not a valid `embedded_audit.auditor_tool`
and explicitly excluded per AGENTS.md §9.1 ("Codex is forbidden as a formal auditor").

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

## Pass 2 (controlling) — AGY / Gemini 3.1 Pro High, verdict PASS_WITH_RISKS

This is the audit of record. Full report, invariant citations, and two new findings
(neither Pass 0 nor Pass 1 documented them — both non-security UX limitations, no
false-clearance/false-denial) are in `AUDITOR_REPORT.md`. Raw evidence (model-selection
proof, exact invocation, full audit prompt, raw JSON transcript) is in `review_bundle/`.
No code changes were required or made as a result of this pass; the implementation
content is unchanged from `af145c4b10b67fd9c4dbcd6ec44fb31cca73dfca`. This proof update
is itself a proof-only successor commit.
