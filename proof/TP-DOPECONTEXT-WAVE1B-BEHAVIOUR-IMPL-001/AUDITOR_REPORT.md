# AUDITOR_REPORT — TP-DOPECONTEXT-WAVE1B-BEHAVIOUR-IMPL-001

## Relationship to TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007

This is a **distinct packet ID and proof directory** from
`proof/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007/`, which already existed on
`origin/main` (landed via PR #1318) and audits different content: the
packet *specification document itself* being admitted
(`AWAITING_AMENDMENT_A5` status, no code touched, head `fecb5f3a3`). This
packet audits the actual **code implementation** that packet specifies,
once ADR-226 Amendment A5a was approved.

## Subject

PR #1323: `feat(dope-context): ADR-226 Amendment A5a — Wave 1b behaviour
fixes`. Lands the operator-approved A5a regex exemption (3 lookaheads) plus
the Wave 1b content it gates. A5b (`contextualized_embedder.py`,
`voyage_reranker.py`) is untouched, per operator HOLD.

- Base: `33a38119f97611e391aab719151ffadbf541f06c` (origin/main after #1322)
- Head: `564bc6e6390d9c4e173e0fc07344f15aa0520712`

## Auditor

`agy` (Google Antigravity CLI), model `gemini-3.1-pro-high`.

## Round 1 (head `b6192d577`)

**PASS** — 10/10 findings confirmed. Full findings in
`review_bundle/AGY_AUDIT_R1_RAW.json`.

## Round 1 follow-up: Copilot findings

Automated review on PR #1323 found two legitimate issues, both fixed:

1. `server.py`'s `raw_results` always included a `token_count` key even
   when the value was untrustworthy (`None`), adding unnecessary payload
   weight and a falsy-but-present key for a downstream reader to trip on.
   Fixed: the key is now omitted entirely when not trustworthy, never set
   to `None`.
2. `token_budget.py`'s `token_count` validation used
   `isinstance(exact_count, int)`, but `bool` is an `int` subclass in
   Python (`isinstance(True, int)` is `True`), so a payload with
   `token_count=True` could have been read as count `1` and silently
   disabled truncation for arbitrarily large content. Fixed: `bool` is now
   explicitly excluded before the `isinstance(int)` check.

Both fixes were squashed into the original content commit and re-audited
(round 2) rather than left as a separate proof-only-adjacent commit, since
they touch content files, not proof directories.

## Round 2 (head `564bc6e63`, current)

**PASS** — 10/10 findings confirmed, 0 remaining risks, both Copilot
findings independently verified fixed.

| ID | Severity | Title | Status |
|---|---|---|---|
| F-DIFF-SCOPE | BLOCKING | Diff touches exactly the 8 expected files; A5b files untouched | RESOLVED |
| F-RED-LANE-REGEX | BLOCKING | Exactly 3 new lookaheads, `\Z`-anchored, `re.DOTALL`, no A5b lookahead | RESOLVED |
| F-CACHE-BOUND | HIGH | Tokenizer cache genuinely bounded; no-TTL reasoning sound | RESOLVED |
| F-TOKEN-BUDGET | HIGH | Starvation flags correct; token_count preference sound; bool-exclusion fix confirmed | RESOLVED |
| F-SERVER-DOCS | HIGH | token_count conditional correct; omit-not-None fix confirmed | RESOLVED |
| F-TEST-EXEC | MEDIUM | Both suites re-run: 76 passed (guard); 133 passed/1 skipped (dope-context) | RESOLVED |
| F-TEST-AUTHENTICITY | HIGH | Tests exercise real code paths; digests independently reproduced | RESOLVED |
| F-MUTATION | HIGH | Auditor independently performed its own mutation test on E17 | RESOLVED |
| F-DOCS-ACCURACY | MEDIUM | ADR-226 and packet Status accurately describe what landed | RESOLVED |
| F-SECRETS | BLOCKING | No secrets/credentials in the diff | RESOLVED |

Full auditor output: `review_bundle/AGY_AUDIT_RAW.json` (round 2),
`review_bundle/AGY_AUDIT_R1_RAW.json` (round 1).

## Additional validation (performed by the operator session, not re-run by the auditor)

- Full `tests/dcp/` red-lane suite: 185 passed, 1 deselected
- Required-CI-scope unit lane: 1878 passed, 2 pre-existing quarantines, 0 new failures
- `scripts/brand_lint.py`: 0 errors, 0 warnings
- All three fixes (E10, E2/E4, E17) mutation-tested independently by the operator session
