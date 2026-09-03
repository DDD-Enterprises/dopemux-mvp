# AUDITOR_REPORT — TP-DMX-PR-STEWARD-COMMENTED-REVIEW-ADJUDICATION-001

**Auditor**: Claude Code CLI (Sonnet) — Tier-1 self-audit per AGENTS.md §9.1
**Audited head**: `af145c4b10b67fd9c4dbcd6ec44fb31cca73dfca`
**Verdict**: PASS

## Scope

`tools/pr_steward/classifier.py`, `tests/pr_steward/test_commented_review_adjudication.py`,
`docs/ops/pr-steward.md`. No other paths touched (verified via `git status --short` against
the packet's FORBIDDEN list, and via `git diff --stat` against `main`).

## Why Codex is not the auditor of record

Two rounds of adversarial red-team review were run via Codex (`codex:codex-rescue`) as the
originating directive required a reviewer from a different model family than the
implementer. Codex found a real bug in round 1; the fix was verified in round 2. That
review is preserved in `AUDIT.md` as supplementary evidence because it materially improved
the change. It is **not** recorded as the schema's `embedded_audit.auditor_tool` because
(a) `codex` is not in the enum in `schemas/proof/embedded_audit.schema.json`, and
(b) AGENTS.md §9.1 states plainly: "Codex is forbidden as a formal auditor." The formal
embedded audit below is a Claude Code self-audit against the diff, per the AGENTS.md §9.1
sanctioned route ("A Claude Code session may run the audit locally against the diff and
author the proof" — precedent `proof/TP-DCP-MCP-RO-0008`).

## Invariant-by-invariant check (against the originating directive's MANDATORY_TESTS / NEVER OVERRIDABLE list)

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
   comment bytes (see Finding F-ADJ001-HIGH-1 below). Tests: `TestConflictingReceipts`
   (four cases: differing content, byte-identical from same author, byte-identical from
   two different trusted authors, same parsed fields but different bytes).
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
    0 failed, 0 errors, run via `mise exec python@3.12 -- python -m pytest tests/pr_steward/ -q`.

## Finding

### F-ADJ001-HIGH-1 (RESOLVED): conflict dedup used parsed fields + adjudicator, not raw bytes

Identified by the round-1 Codex review. `_find_review_adjudication`'s original dedup
signature was `(review_id, head_sha, disposition, reason, adjudicator)`. Two failure
directions:

- Two comments with different raw bytes (e.g. different surrounding commentary) but
  identical parsed fields collapsed to one signature — a real difference was silently
  ignored, and the review would clear even though, strictly, two distinct receipt texts
  existed.
- Two byte-identical receipts posted by two different trusted approvers produced two
  distinct signatures (different `adjudicator`) and were therefore wrongly treated as
  conflicting, denying a clearance the documented rule says should apply.

Fixed by keying the dedup set on the raw `comment.get("body")` string itself (stored as
`_body` internally, stripped before the receipt dict is returned — verified it never
leaks into `rationale` or the ledger). `adjudicator` no longer participates in the
conflict comparison, only in the resulting rationale text. Re-verified in round-2 Codex
review that this does not create a piggyback path: the trusted-author gate
(`author not in trusted_approvers: continue`) is applied per-comment *before* any body is
added to the eligible set, so an untrusted comment can never enter the dedup comparison
regardless of its content.

## Verdict

**PASS.** All twelve invariants hold against the current diff (`af145c4b1`). The one real
defect found by adversarial review has been fixed, is covered by regression tests, and was
independently re-verified fixed. No unrelated files were touched. Test suite, ruff,
`git diff --check`, pre-commit, and a diff-scoped gitleaks scan are all clean.
