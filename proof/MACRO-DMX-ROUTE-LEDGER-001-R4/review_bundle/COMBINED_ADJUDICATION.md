# Combined adjudication (MACRO-DMX-ROUTE-LEDGER-001-R4, W04)

Subject: merge head `989fe4651c050ec23619e5208da17d6152b477b0` (parents `ad8a141c6` and `97b6d5040496e2271c41d24c339d039303bbe6b1`, current origin/main); the seven audited content files are byte-identical to the repair commit `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0`. Written after both custody commits existed.

## Verdict rule applied

- Grok (PRIMARY, `grok-cli`/`grok-4.5`): `PASS_WITH_RISKS`, Q1-Q13 PASS, 8 findings, none BLOCKING. AGY (CORROBORATING, `agy`/`gemini-4-argon-high`): `PASS_WITH_RISKS`, Q1-Q13 PASS, 11 findings, none BLOCKING.
- Stricter-outcome rule: both verdicts are `PASS_WITH_RISKS`, so the stricter outcome is `PASS_WITH_RISKS`; `embedded_audit.verdict` is the primary's (Grok). The three findings only AGY raised (N11, N12, N13) were adjudicated against source: CONFIRMED, none BLOCKING, so they do not make the outcome stricter; they are recorded as residual risks.
- Neither auditor was shown the other's output, any R3 audit output or any R2 verdict text. Both received the earlier findings as untrusted claims (operator decision).
- Authority NONE: readiness stays with PR Steward and the operator.

## Union of findings (maximum severity; every one OPEN, the operator decides what to accept)

| Id | Max severity | Grok | AGY | Adjudication | Title |
|---|---|---|---|---|---|
| N1 | HIGH | HIGH | HIGH | CONFIRMED | The repaired code has not run in a real Claude Code session. |
| N2 | MEDIUM | MEDIUM | MEDIUM | CONFIRMED | receiptDir is not checked for symlinks; an explicit absolute directory is allowed; a trailing slash on the default value skips the state check. |
| N3 | MEDIUM | MEDIUM | MEDIUM | CONFIRMED | Closed receipt segments stay in memory for the process lifetime. |
| N4 | MEDIUM | MEDIUM | MEDIUM | CONFIRMED | A failed final flush at session.end loses the dirty tail. |
| N5 | MEDIUM | LOW | MEDIUM | CONFIRMED (by design, disclosed) | After /clear, receipts keep going to the pre-clear session file. |
| N11 | MEDIUM | - | MEDIUM | CONFIRMED | The `main` row of /route-ledger stays UNKNOWN when receipts are disabled (AGY only). |
| N8 | LOW | LOW | LOW | CONFIRMED | The debounce test advances 1000 ms for a 500 ms debounce. |
| N9 | LOW | LOW | LOW | CONFIRMED | The Agent call description (up to 80 characters) is recorded unredacted. |
| N12 | LOW | - | LOW | CONFIRMED (code path); whether the engine ever sends an empty string is UNKNOWN | An empty-string effort or advisor id would violate the schema's minLength 1 (AGY only). |
| N13 | LOW | - | LOW | CONFIRMED for the toast state; the second claim is NOT A DEFECT | After a hot reload the toast-once state is not restored (AGY only); a second claim about unjoined step receipts is not a defect. |
| N10 | INFO | INFO | INFO | CONFIRMED | The plugin API is early access; coexistence with another PLUGIN status line is unverified. |

Totals (union): 11 findings: 1 HIGH, 5 MEDIUM, 4 LOW, 1 INFO; none BLOCKING.

## Disagreements

- N5 severity: Grok LOW, AGY MEDIUM (kept MEDIUM, as in R2).
- Findings raised by one auditor only: N11, N12, N13 (AGY). Grok raised nothing AGY did not.
- Identity: Grok's answer says `grok-4.7` while the CLI was run with `-m grok-4.5` and every init event shows `grok-4.5`. UNRESOLVED; provider attestation UNKNOWN for both auditors.

## Other observations (docs and tests), all INFO

| Id | Source | Observation | Adjudication |
|---|---|---|---|
| O1 | AGY Q8 | README, how-to, plugin.json and the schema do not mention the byte-based rollover at about 3.5 MB (SEGMENT_BYTES_MAX = 3_500_000, register.tsx:39) that comes before maxReceiptsPerFile. | CONFIRMED (no mention found by search) |
| O2 | AGY Q8 | The how-to (lines 84-85) describes the file stem as the session id with characters outside A-Za-z0-9_- replaced by `_` but omits the truncation to 120 characters (register.tsx:326). | CONFIRMED |
| O3 | AGY Q8 | register.tsx:57-59 says the mod knows "five" of the binding keys; the BindingFields type has six top-level keys and the schema $comment says "these six". | CONFIRMED (cosmetic) |
| O4 | Grok Q8 | The how-to frontmatter `last_review` is 2026-10-23 although the file was edited in the repair. | CONFIRMED (cosmetic) |
| O5 | AGY Q7 | Untested: the byte-based rollover, unreadable segments and corrupt lines on rehydrate, the command handler's catch (`could not read the ledger.`, 0 matches in the test file), and the main row with receipts disabled. | CONFIRMED by search of the test file (absence of a matching test; not an exhaustive proof) |

## Repair

Q12 PASS from both auditors: the N6 timeout (`{ timeoutMs: TOAST_MS }`, test `toastTimeouts[0] > 4000`), the N7 status grammar (`advisor N[/B ⚠]` against the session budget and a separate `child M/B ⚠` segment, three tests) and the prefix removal (three toasts and two command errors, `.not.toMatch(/^route-ledger:/)`) were found in the code, the tests and both docs; neither auditor re-raised N6 or N7. The coordinator confirmed the same in R4 W01 (55 of 55 tests).

## Operator steps per finding

- **N1** (HIGH): Operator step: `claude --plugin-dir plugins/dopemux-route-ledger --setting-sources user` with `.control-tower/state` present; one pinned advisor-calling child, then one clean pinned child (expect `advisor 1 · child 1/0 ⚠` for both), one unpinned Agent call (an 8 s toast with no doubled prefix), then `/route` and `/route-ledger receipts`.
- **N2** (MEDIUM): Accept as a risk or repair (stat or realpath check; compare the trimmed value) and re-audit.
- **N3** (MEDIUM): Accept as a risk or evict closed segments after a successful flush.
- **N4** (MEDIUM): Accept as a risk or retry once at session.end.
- **N5** (MEDIUM): Accept as a documented behaviour, or rotate the stem if the host exposes a new session id.
- **N11** (MEDIUM): Accept, or keep the last main step outside the receipt segments.
- **N8** (LOW): Accept, or advance by the production constant.
- **N9** (LOW): Accept as documented.
- **N12** (LOW): Accept, or reject empty strings with text() as for the model.
- **N13** (LOW): Accept the repeat toast, or persist toast keys in the receipts.
- **N10** (INFO): Run with dopemux-pulse enabled during the live check.

## What the audits do not cover

- Neither auditor had tools: both judged the diff text only and could not run the code or the tests; they asked for the live session, the declaration file and markdownlint, all NOT_RUN.
- agy cannot be made tool-less (60 built-in tools, 11 global MCP servers). Its containment rests on the session-only request-review settings and the stream gate, and the stream shows no tool step; absence of a tool step is not proof the model had no capability.
- Exact-model evidence for the schema-required `gemini-3.1-pro-high` is unavailable; the AGY run is recorded as `auditor_tool: agy`, `auditor_model: gemini` and may not be treated as READY by PR Steward.
