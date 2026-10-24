# MACRO-DMX-ROUTE-LEDGER-001-R2 — follow-ups from the accepted PASS_WITH_RISKS verdict

Audited content head: `93969e7a3ca2775c7b435e1ce1b6528ad2173c4a`. Auditor: grok-cli / grok-4.5, tool-less. Verdict: `PASS_WITH_RISKS`.

Operator decision, 2026-10-24, in chat:

> Accept both PASS_WITH_RISKS verdicts as-is: Memory Bridge R2 at 52855fb35 and Route Ledger R2 at 93969e7a3. Record the open findings as follow-ups and prepare the proof and signing steps; I will attest, sign and push myself.

Every finding below was OPEN in the auditor's output and is now `ACCEPTED_RISK` in `PROOF.json`. None was repaired.
The directions are the coordinator's reading of each finding's title, not decisions to repair.

| ID | Severity | Finding | Direction |
|---|---|---|---|
| N1 | HIGH | Mod never run live; hook ordering, tool_use_id population and status coexistence are UNKNOWN. | Run the mod live (`claude --plugin-dir plugins/dopemux-route-ledger`) and record hook ordering, tool_use_id population and status coexistence. Verification, not a code change. |
| N2 | MEDIUM | Explicit absolute or symlinked receiptDir is not constrained beyond host permissions. | Reject or document an absolute or symlinked `receiptDir`. |
| N3 | MEDIUM | In-memory receipts of closed segments are never released (linear growth per session). | Release in-memory receipts of closed segments after they are flushed. |
| N4 | MEDIUM | A failed final flush at a real session end loses the unflushed tail of receipts. | Retry or surface a failed final flush so the unflushed tail is not silently lost. |
| N5 | MEDIUM | After /clear receipts keep going to the old session id's file. | Re-key the receipt file on `/clear`, or document that receipts continue in the old session's file. |
| N6 | LOW | Unpinned toast does not set a timeout. | Give the unpinned toast a timeout like the budget toasts. |
| N7 | LOW | Status segment N/B uses session total with the child budget; docs do not say which budget. | State in the docs which budget the `N/B` status segment uses, or change the segment. |
| N8 | LOW | Test debounce slack (1000 ms vs 500 ms). | Align the test debounce (1000 ms) with the code (500 ms). |
| N9 | LOW | Agent description (80 chars) is persisted in receipts. | Stop persisting the 80-character Agent description, or document that it can carry user text. |
| N10 | INFO | API drift and Pulse coexistence remain unverified. | Re-check declaration drift and Pulse coexistence during the live run. |

## Rules for acting on these
- A code or docs repair changes the audited subject, so it needs a new audit on an operator-approved route. The old verdict stays as it is.
- Live-run verification (a real Claude Code session) is an operator step and is `NOT_RUN` here.
- Attestation of audit independence, signing, push and merge stay with the operator.
