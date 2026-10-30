# AGY adjudication (MACRO-DMX-ROUTE-LEDGER-001-R4, W04)

Written by the coordinator AFTER both custody commits existed (`0e1755a5a` Grok, `118e1ecfc` AGY). Every finding below was checked against the source at the audited head `989fe4651c050ec23619e5208da17d6152b477b0` (its seven content files are identical to `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0`). Severities are the auditor's own.

**Route**: agy 1.4.11, `gemini-4-argon-high`, sealed, session-only request-review hardening, corroborating. **Auditor self-report**: `Gemini 4 Argon (High)`. **Status**: `PASS_WITH_RISKS`. **Questions**: Q1-Q13 all PASS. **Tools used (auditor's statement)**: none. **Instruction-like content**: False.

**Identity note**: the answer says `Gemini 4 Argon (High)`, consistent with the configured id `gemini-4-argon-high` shown by the init event of every run; still a claim, not attestation.

## Findings

| Id | Auditor severity | Adjudication | Evidence at the audited head |
|---|---|---|---|
| N1 | HIGH | CONFIRMED | The N6/N7/prefix repair is covered only by the offline mock kit (register.test.ts, 55 tests). The pre-repair code (content head 93969e7a3) WAS loaded live by the operator on 2026-10-30 (status line, over-budget advisor toast, /route-ledger table, background Agent joins, advisor_call receipts attributed to the right agent, 36 schema-valid rows), but nothing ran the repaired head: GATES_PRE_AUDIT.txt lists the live session as NOT_RUN. |
| N2 | MEDIUM | CONFIRMED | register.tsx:729-737 (initSession): hasDotDot, empty/root and, for the default, exists(STATE_DIR) are checked; $.fs.stat is never called, so a symlink at or under an explicit receiptDir is followed. AGY adds: line 733 compares the RAW config with DEFAULT_RECEIPT_DIR while line 729 trims trailing separators, so `.control-tower/state/route-ledger/` is treated as an explicit directory and is created on first write even where `.control-tower/state` is absent. Absolute explicit directories are allowed by design (disclosed limitation vii). |
| N3 | MEDIUM | CONFIRMED | register.tsx:634-649 (currentSegment) pushes each new segment onto s.segments and nothing evicts a closed one; rehydrate (:758-795) loads every matching file; lastMainStep (:512-521) scans all segments. Memory grows linearly with receipts. |
| N4 | MEDIUM | CONFIRMED | register.tsx:653-664 (flushSegments) counts a failed write and leaves the segment dirty; the session.end handler schedules one flush and awaits the chain once, with no retry, so receipts still dirty after a failed final write are lost when the process ends. The ` · receipts ✗` status shows the failure only while the session runs. |
| N5 | MEDIUM | CONFIRMED (by design, disclosed) | The session.end handler returns next(e) untouched for reason `clear`, and no session.start follows a /clear, so s.sessionId and s.fileStem are never refreshed (disclosed limitation v). Severity DISAGREEMENT: Grok LOW, AGY MEDIUM; R2 rated it MEDIUM; the union keeps MEDIUM. |
| N8 | LOW | CONFIRMED | register.test.ts:290 `const DEBOUNCE_MS = 1_000` and :242 advances it; register.tsx:41 `STATUS_DEBOUNCE_MS = 500`: a regression up to 1000 ms would still pass. |
| N9 | LOW | CONFIRMED | register.tsx:915 slices `e.description` to DESCRIPTION_MAX (80, :37); it is written into agent_request receipts and the unpinned toast; the prompt itself is never recorded (disclosed limitation viii). |
| N10 | INFO | CONFIRMED | README Limits and the how-to say so. Coexistence with the operator's own `statusLine` command was seen live on the pre-repair code; coexistence with another plugin (dopemux-pulse) was not run. The mod loaded on CLI 2.1.312 and 2.1.314 without error. |
| N11 | MEDIUM | CONFIRMED | register.tsx:685-695 (commit) pushes a receipt onto s.segments only when s.receiptsEnabled; lastMainStep (:512-521) reads only s.segments; tally (:375-389) does not keep main-loop steps (agent_id null) in s.agents; routeTable (:533-546) takes the main row from lastMainStep. With receipts off (for example no `.control-tower/state`) the main row therefore shows UNKNOWN for requested, observed, effort and match even after main steps ran. No test combines main-loop steps with disabled receipts: the only disabled-receipts command test checks the `receipts` argument (register.test.ts:1138-1144) and the all-UNKNOWN main row at :1068 is for an empty ledger. Auditor severity MEDIUM kept; the coordinator's view is LOW in practice: ` · ledger off` is shown in the status, the agent rows and advisor counts are unaffected, no data is lost. |
| N12 | LOW | CONFIRMED (code path); whether the engine ever sends an empty string is UNKNOWN | register.tsx:913 and :957 accept any string effort (including ""); toBindingFields (:274-276) turns it into selection.effort and effort_requested "" while receipt.schema.json requires minLength 1 at both; noteStep (:944) accepts any string advisor id while advisor_use_id requires minLength 1 (verified in the schema). |
| N13 | LOW | CONFIRMED for the toast state; the second claim is NOT A DEFECT | (a) toastOnce (:463-464) keeps its keys in s.toasted; rehydrate (:758-795) and initSession do not repopulate it and the module state restarts on a hot reload, so an advisor call after the reload can toast an already-exceeded budget again: a repeat toast, nothing lost. (b) tally (:377-384) creates a record with requestedModel null for a step of an agent whose request was never joined. That behaviour is accurately described, but it is not a defect in the coordinator's reading: a step receipt's requested_model is the engine's per-step model, not the Agent call's alias, so adopting it would make `match` trivially yes; UNKNOWN is the honest cell for an unjoined agent. |

**Not raised by this auditor**:  (none: this auditor raised every finding in the union).

## Repair (N6, N7, prefix)

Q12 PASS from both auditors: the N6 timeout (`{ timeoutMs: TOAST_MS }`, test `toastTimeouts[0] > 4000`), the N7 status grammar (`advisor N[/B ⚠]` against the session budget and a separate `child M/B ⚠` segment, three tests) and the prefix removal (three toasts and two command errors, `.not.toMatch(/^route-ledger:/)`) were found in the code, the tests and both docs; neither auditor re-raised N6 or N7. The coordinator confirmed the same in R4 W01 (55 of 55 tests).

## Other observations raised in the answers

| Id | Source | Observation | Adjudication |
|---|---|---|---|
| O1 | AGY Q8 | README, how-to, plugin.json and the schema do not mention the byte-based rollover at about 3.5 MB (SEGMENT_BYTES_MAX = 3_500_000, register.tsx:39) that comes before maxReceiptsPerFile. | CONFIRMED (no mention found by search) |
| O2 | AGY Q8 | The how-to (lines 84-85) describes the file stem as the session id with characters outside A-Za-z0-9_- replaced by `_` but omits the truncation to 120 characters (register.tsx:326). | CONFIRMED |
| O3 | AGY Q8 | register.tsx:57-59 says the mod knows "five" of the binding keys; the BindingFields type has six top-level keys and the schema $comment says "these six". | CONFIRMED (cosmetic) |
| O5 | AGY Q7 | Untested: the byte-based rollover, unreadable segments and corrupt lines on rehydrate, the command handler's catch (`could not read the ledger.`, 0 matches in the test file), and the main row with receipts disabled. | CONFIRMED by search of the test file (absence of a matching test; not an exhaustive proof) |

AGY's Q2 point about a trailing slash on the default path is folded into N2, its Q3 edge cases into N12, and its Q6 points (a)-(c) into N11 and N13.

## `needs_more_evidence` (auditor's list, unchanged)

- Live Claude Code session execution of the repaired head (4fcdc9761 / 989fe4651) verifying status line rendering, toast duration/prefix, command registration, and receipt output.
- Inspection of the engine-laid plugins/dopemux-route-ledger/tsconfig.json and the claude-code type declaration file (not included in the diff).
- Git log/diff verification outside the seven content files for the merge commit 989fe4651c050ec23619e5208da17d6152b477b0.
