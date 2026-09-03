# AUDITOR_REPORT — TP-DMX-PR-STEWARD-COMMENTED-REVIEW-ADJUDICATION-001

**Auditor**: AGY / Google Antigravity, model `gemini-3.1-pro-high` — Tier-1 route #1 per
`docs/ops/embedded-audit.md`, independent of the implementer (Claude Sonnet 5 / Claude Code)
by model family and runtime.
**Audited head**: `af145c4b10b67fd9c4dbcd6ec44fb31cca73dfca`
**Invocation**: `agy --model gemini-3.1-pro-high --output-format json --print-timeout 8m --print='<full audit prompt>'`, conversation id from the full audit run in `review_bundle/AGY_AUDIT_RAW.json`. Model selection proven with no fallback: `review_bundle/AGY_MODEL_SELFCHECK.md`, `review_bundle/AGY_VERSION.txt` (CLI 1.1.25), `review_bundle/AGY_MODELS.txt` (`gemini-3.1-pro-high` present, unambiguous). Full prompt in `review_bundle/AGY_AUDIT_PROMPT.txt` (self-contained: full diff + full post-fix `classifier.py` + full test file, no tool/filesystem access given to the auditor — pure prompt-based review).
**Verdict**: **PASS_WITH_RISKS**

A prior Claude Code self-audit (PASS) and two rounds of supplementary Codex red-team
review (FAIL round 1, PASS round 2) preceded this run and are preserved in `AUDIT.md`.
This AGY run is the **controlling** audit of record for `embedded_audit` in `PROOF.json`,
per `docs/ops/embedded-audit.md` Tier-1 route #1 — it supersedes the Claude self-audit,
which did not satisfy this repo's independence requirement ("independent of the
implementer as long as the auditing session is not the one that wrote the diff").

## Invariant-by-invariant verdict (verbatim from the AGY run, citations against `af145c4b1`)

1. **CHANGES_REQUESTED never overridable** — HOLDS. `classifier.py:556-561`: `CHANGES_REQUESTED` is trapped in an `elif` that unconditionally sets `MUST_FIX`/`blocking=True`; never reaches the `else:` at line 565 where the receipt lookup happens.
2. **Exact review_id + head_sha binding** — HOLDS. `classifier.py:1428-1429`: any mismatch on either field skips the receipt.
3. **Only trusted logins eligible** — HOLDS. `classifier.py:1422-1423`: `if author not in trusted_approvers: continue`.
4. **Malformed receipts don't clear** — HOLDS. `classifier.py:1381-1389`: subset-of-required-fields check, exact disposition string, non-empty values, strict `^[0-9a-f]{40}$` SHA match.
5. **Conflict rule (raw-byte comparison; byte-identical = one)** — HOLDS. `classifier.py:1434-1441`: `distinct_bodies = {r["_body"] for r in eligible}` collapses byte-identical bodies regardless of author; `len(distinct_bodies) != 1` fails closed.
6. **Unresolved threads / CI / audit / security-release unaffected** — HOLDS, structurally. `_classify_threads` (687-848), `_classify_checks` (880-977), embedded-audit (260-265), security-release (278-316) are distinct sequential blocks in `build_artifacts`; none invoke `_find_review_adjudication`.
7. **Ledger item count unchanged** — HOLDS. `classifier.py:597`: `items.append(...)` executes exactly once per review regardless of receipt outcome.
8. **Receipt comment itself nonblocking despite P1/P2 text** — HOLDS. `classifier.py:649-658`: trusted, well-formed issue-comment receipts intercept the ordinary P1/P2 heuristic.
9. **No cross-PR / global state leakage** — HOLDS. `classifier.py:1428`: `_find_review_adjudication` is a pure function comparing only against the `pr_head_sha` passed from the current invocation's harvested PR payload.
10. **`_body` bookkeeping field never leaks into output** — HOLDS. `classifier.py:1442`: `return {k: v for k, v in eligible[0].items() if k != "_body"}` strips it before return.

## New findings (neither Claude nor Codex documented these)

### F-ADJ001-AGY-INFO-1: unknown-author precedence blocks adjudication of unknown-reviewer P1/P2 reviews

If an unknown/untrusted reviewer posts a `COMMENTED` review containing a P1/P2 marker,
`_classify_reviews`'s `_known_author` check (`classifier.py:552`) assigns
`UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION` *before* the `else:` branch that would consult a
receipt is ever reached. A trusted approver cannot use this mechanism to clear that
specific review. This slightly narrows the mechanism's stated scope ("reclassify... from
whatever blocking disposition it would otherwise get") but is safely fail-closed, not a
vulnerability — it makes the mechanism strictly narrower than documented, never broader.
Status: ACCEPTED_RISK (functional scope note, not a defect requiring a code change).

### F-ADJ001-AGY-INFO-2: multiline `reason=` text is silently truncated to its first line

`_parse_review_adjudication_receipt` tokenizes via `body.splitlines()` and matches
`^(review_id|head_sha|disposition|reason)=(.*)$` per line; the `(.*)` capture stops at the
line break, so a multi-line reason keeps only its first line — later lines don't match the
field regex and are dropped. The receipt still clears the review correctly; only the
recorded rationale text loses trailing context. Status: ACCEPTED_RISK (UX limitation, not
a correctness or security defect — no false clearance, no false denial).

## Additional adversarial checks performed (no issues found)

- **Duplicate marker blocks in one comment**: `lines.index()` finds only the first marker
  occurrence, and `if key not in fields` ignores duplicate field lines, so a comment can
  only ever yield one deterministic receipt — cannot be used to smuggle a second, different
  receipt in the same comment.
- **Duplicate comment objects from GraphQL pagination overlap**: harmless — identical raw
  bytes collapse into one element of the `distinct_bodies` set, avoiding a false conflict.
- **Spot-checked 3 of the 15 regression tests by hand against the classifier logic**
  (`test_byte_identical_body_from_two_different_trusted_authors_is_not_a_conflict`,
  `test_same_parsed_fields_but_different_raw_bytes_is_a_conflict`,
  `test_receipt_comment_is_nonblocking_even_when_reason_quotes_p2`) — all three exercise
  exactly what they claim.

## Verdict

**PASS_WITH_RISKS.** All ten invariants hold under adversarial review, including two
attack surfaces (multi-marker comments, pagination duplication) that neither prior review
round considered. The two findings are functional/UX narrowing effects with no
false-clearance or false-denial security impact; per this run's own assessment, no code
change is required to merge this onto trusted main. Both are recorded as `ACCEPTED_RISK`
in `PROOF.json`.
