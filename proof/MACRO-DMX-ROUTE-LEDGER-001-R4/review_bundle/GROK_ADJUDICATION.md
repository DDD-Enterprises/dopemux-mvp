# Grok adjudication (MACRO-DMX-ROUTE-LEDGER-001-R4, W04)

Written by the coordinator AFTER both custody commits existed (`0e1755a5a` Grok, `118e1ecfc` AGY). Every finding below was checked against the source at the audited head `989fe4651c050ec23619e5208da17d6152b477b0` (its seven content files are identical to `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0`). Severities are the auditor's own.

**Route**: grok-cli 1.0.70, configured model `grok-4.5`, tool-less recipe, primary. **Auditor self-report**: `grok-4.7`. **Status**: `PASS_WITH_RISKS`. **Questions**: Q1-Q13 all PASS. **Tools used (auditor's statement)**: none. **Instruction-like content**: False.

**Identity note**: the CLI init event of every run shows `grok-4.5` (`-m grok-4.5`; `grok models` lists `grok-4.7` as the CLI default), but the answer says `grok-4.7`. A model's statement about itself is a claim, not attestation; the mismatch is UNRESOLVED and provider-attested identity stays UNKNOWN. (R2's Grok answer said `grok-4`.)

## Findings

| Id | Auditor severity | Adjudication | Evidence at the audited head |
|---|---|---|---|
| N1 | HIGH | CONFIRMED | The N6/N7/prefix repair is covered only by the offline mock kit (register.test.ts, 55 tests). The pre-repair code (content head 93969e7a3) WAS loaded live by the operator on 2026-10-30 (status line, over-budget advisor toast, /route-ledger table, background Agent joins, advisor_call receipts attributed to the right agent, 36 schema-valid rows), but nothing ran the repaired head: GATES_PRE_AUDIT.txt lists the live session as NOT_RUN. |
| N2 | MEDIUM | CONFIRMED | register.tsx:729-737 (initSession): hasDotDot, empty/root and, for the default, exists(STATE_DIR) are checked; $.fs.stat is never called, so a symlink at or under an explicit receiptDir is followed. AGY adds: line 733 compares the RAW config with DEFAULT_RECEIPT_DIR while line 729 trims trailing separators, so `.control-tower/state/route-ledger/` is treated as an explicit directory and is created on first write even where `.control-tower/state` is absent. Absolute explicit directories are allowed by design (disclosed limitation vii). |
| N3 | MEDIUM | CONFIRMED | register.tsx:634-649 (currentSegment) pushes each new segment onto s.segments and nothing evicts a closed one; rehydrate (:758-795) loads every matching file; lastMainStep (:512-521) scans all segments. Memory grows linearly with receipts. |
| N4 | MEDIUM | CONFIRMED | register.tsx:653-664 (flushSegments) counts a failed write and leaves the segment dirty; the session.end handler schedules one flush and awaits the chain once, with no retry, so receipts still dirty after a failed final write are lost when the process ends. The ` · receipts ✗` status shows the failure only while the session runs. |
| N5 | LOW | CONFIRMED (by design, disclosed) | The session.end handler returns next(e) untouched for reason `clear`, and no session.start follows a /clear, so s.sessionId and s.fileStem are never refreshed (disclosed limitation v). Severity DISAGREEMENT: Grok LOW, AGY MEDIUM; R2 rated it MEDIUM; the union keeps MEDIUM. |
| N8 | LOW | CONFIRMED | register.test.ts:290 `const DEBOUNCE_MS = 1_000` and :242 advances it; register.tsx:41 `STATUS_DEBOUNCE_MS = 500`: a regression up to 1000 ms would still pass. |
| N9 | LOW | CONFIRMED | register.tsx:915 slices `e.description` to DESCRIPTION_MAX (80, :37); it is written into agent_request receipts and the unpinned toast; the prompt itself is never recorded (disclosed limitation viii). |
| N10 | INFO | CONFIRMED | README Limits and the how-to say so. Coexistence with the operator's own `statusLine` command was seen live on the pre-repair code; coexistence with another plugin (dopemux-pulse) was not run. The mod loaded on CLI 2.1.312 and 2.1.314 without error. |

**Not raised by this auditor**: N11, N12, N13 (AGY-only findings; adjudicated in AGY_ADJUDICATION.md and COMBINED_ADJUDICATION.md).

## Repair (N6, N7, prefix)

Q12 PASS from both auditors: the N6 timeout (`{ timeoutMs: TOAST_MS }`, test `toastTimeouts[0] > 4000`), the N7 status grammar (`advisor N[/B ⚠]` against the session budget and a separate `child M/B ⚠` segment, three tests) and the prefix removal (three toasts and two command errors, `.not.toMatch(/^route-ledger:/)`) were found in the code, the tests and both docs; neither auditor re-raised N6 or N7. The coordinator confirmed the same in R4 W01 (55 of 55 tests).

## Other observations raised in the answers

| Id | Source | Observation | Adjudication |
|---|---|---|---|
| O4 | Grok Q8 | The how-to frontmatter `last_review` is 2026-10-23 although the file was edited in the repair. | CONFIRMED (cosmetic) |

## `needs_more_evidence` (auditor's list, unchanged)

- Live Claude Code session loading the repaired tip (post-4fcdc9761 / merge head) with observed status, toasts, /route-ledger, spawn join, advisor_call attribution, and schema-valid receipts
- Whether /route is accepted on the target CLI build
- Coexistence with dopemux-pulse or other plugin status lines
- markdownlint result (NOT_RUN on this host)
- Real hook time budgets and ordering beyond offline mocks
- claude-code API declaration file (not in DIFF) to confirm turn.step/agent.spawn/tool.call shapes
