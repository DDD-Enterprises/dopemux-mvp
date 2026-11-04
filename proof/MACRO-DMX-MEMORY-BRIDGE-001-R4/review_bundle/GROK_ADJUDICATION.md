# Coordinator adjudication of the Grok audit - MACRO-DMX-MEMORY-BRIDGE-001-R4

Coordinator: claude-opus-5-5. Written after the raw artifacts were committed (`01ac4dc6f`) and after reading the verdict; each finding was checked against the committed source at content head `88e7b7de3a43b50b4c4cdac7fc340f21bda03e40`.

**Overall**: I concur with `PASS_WITH_RISKS`. All 14 questions are PASS, including Q13 (relay safety). N3, N4 and N6 are REPAIRED; N1, N2 and N5 stay repaired; N7 and N8 are unchanged by decision. Of the new findings, N9, N10 and N11 are the already-disclosed limits restated, and N12 (LOW) is a pre-existing, theoretical file-key collision in `safeId`. No BLOCKING, HIGH or MEDIUM finding. The auditor self-reported `grok-4`; the CLI init event shows `grok-4.5`. Provider-attested identity is UNKNOWN and `audit_identity.independence` stays unattested.

## Closure of earlier findings

| Id | Auditor disposition | Coordinator adjudication |
|---|---|---|
| N1 | STILL_REPAIRED | STILL_REPAIRED (concur): no commit hash or PR number in the how-to or README (grep at the frozen head). |
| N2 | STILL_REPAIRED | STILL_REPAIRED (concur): `register.tsx` registers 'Queue a note for the capture ledger'; the test asserts it. |
| N3 | REPAIRED | REPAIRED (concur): the cause is fixed. `adoptEarlier` relays quiet earlier sessions' undelivered task and note rows into this session's ring with their original id; `renderStatus` counts only replayable rows in this process's rings; `foldedPending` is gone. 18 new tests, written failing first, cover adoption, the quiet rule, the age limit, the cap, dedup, settled ids, kinds, memory-only and `/clear`. The coordinator re-read the 101-line code diff. |
| N4 | REPAIRED | REPAIRED (concur): `decisionsOf` runs on `answer.slice(0, MAX_ANSWER_SCAN_CHARS)` with `MAX_ANSWER_SCAN_CHARS = 200_000`; tests cover inside, beyond and a 4 MB answer. |
| N5 | STILL_REPAIRED | STILL_REPAIRED (concur): the README describes `attempts` as attempts that ran, failed ones plus the final successful one. |
| N6 | REPAIRED | REPAIRED (concur): the field and the unreachable branch are removed; the `/clear` fold keeps the dead and dropped counts. |
| N7 | STILL_PRESENT | STILL_PRESENT by decision (concur): never run live. |
| N8 | STILL_PRESENT | STILL_PRESENT by decision (concur): the `tool.call` hook observes with `void` after returning the result; design note. |

## Findings open at this head

| Id | Auditor severity | Adjudication |
|---|---|---|
| N7 | INFO | STILL_PRESENT, disclosure; INFO |
| N8 | INFO | STILL_PRESENT, design note; INFO |
| N9 | INFO | CONFIRMED as a disclosure; INFO |
| N10 | INFO | CONFIRMED as a disclosure; INFO |
| N11 | INFO | CONFIRMED as the disclosed relay residuals; INFO |
| N12 | LOW | CONFIRMED in code; LOW; pre-existing and theoretical |

### N7 (INFO) - docs/02-how-to/memory-bridge.md

**Auditor**: Mod has never run in a real Claude Code session; all proof is mocked unit tests.

**Adjudication**: STILL_PRESENT, disclosure; INFO.

No real session has loaded the mod. The operator's live smoke test is the clearing action.

### N8 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: tool.call observes via void after returning next(e)'s result.

**Adjudication**: STILL_PRESENT, design note; INFO.

Unchanged since the first audited head; the host result is never altered or delayed.

### N9 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: $.process availability on the desktop surface is UNKNOWN; git segment and ledger replay may never run there.

**Adjudication**: CONFIRMED as a disclosure; INFO.

`$.process` is documented CLI-only; `emitOnce` and `dirtyFileCount` degrade to 'unavailable' or omit the git segment, and the status says `(ledger unavailable)`. The same fact was disclosed in every audit; no defect.

### N10 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: If Pulse (or any prepend plugin) is the outer AbovePrompt hook and draws without next(e), the welcome-back band is hidden.

**Adjudication**: CONFIRMED as a disclosure; INFO.

The Pulse band caveat (an outer plugin that draws without `next(e)` hides this band) is tested and documented; plugin order is UNKNOWN.

### N11 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Relay residuals: idle live session >10m can dual-emit (ledger no-op); cap-dropped sent copy may be re-relayed while source remains among eight newest files; only eight newest earlier files are candidates.

**Adjudication**: CONFIRMED as the disclosed relay residuals; INFO.

Exactly the residuals stated in the amendment record and the prompt: a live session idle for more than 10 minutes can have rows delivered twice (a ledger no-op, `INSERT OR IGNORE` on the event id); a relayed row whose sent copy is later dropped by the 1 MiB cap can be relayed again while the source is among the eight newest earlier files (another no-op, ends at 7 days); a quiet file beyond the eight newest earlier files is not reached until newer files age out, and its rows are lost to the relay after 7 days.

### N12 (LOW) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: safeId can map distinct session ids to one filename (non-alnum collapsed to _), risking ring/file collision for pathological ids.

**Adjudication**: CONFIRMED in code; LOW; pre-existing and theoretical.

`safeId` (`register.tsx:266-269`) replaces characters outside `[A-Za-z0-9_-]` with `_` and truncates to 80, so two session ids that differ only in such characters or after 80 characters would share a file. Claude Code session ids are UUID-shaped (hex and hyphens), which `safeId` maps to themselves, so no real collision is expected. The function dates from the first build commit `e561166a6` and was in both earlier audited heads; it is not a regression of this change. A collision-proof key (for example a short hash suffix) would be a small follow-up.

## What the audit does not settle

- The auditor had no tools. Its `needs_more_evidence` items (an independent re-run of the gates; a live session and a real `dopemux capture emit`) are answered only by the coordinator's own gate run at this head (validate exit 0, 123 tests, `tsc` 2.1.309 exit 0, docs validators, change-contract preflight PASS) and remain NOT_RUN for live behaviour.
- Nothing was repaired after this audit; no second audit of this head was run. Signing, attestation, push and the PR stay with the operator.
