# MACRO-DMX-MEMORY-BRIDGE-001-R5 — follow-ups from the accepted PASS_WITH_RISKS verdict

Audited content head: `bce150b5858528bfb26b3b15e3248cb1294a65e5`. Auditor: grok-cli / grok-4.5, tool-less, one attempt. Verdict: `PASS_WITH_RISKS`, Q1-Q14 all PASS, no new findings.

Operator decision, 2026-10-30, in chat: "accept into notes".

Every finding below was OPEN in the auditor's output and is now `ACCEPTED_RISK` in `PROOF.json`. None was repaired; all are INFO.

| ID | Severity | Finding | Direction (coordinator's reading, not a decision to repair) |
|---|---|---|---|
| N7 | INFO | The mod has never run in a real Claude Code session; proof is test-kit only. | Live smoke test: one session completes a todo and ends; after 10 quiet minutes a second session starts; check the status line, the outbox files and `.dopemux/chronicle.sqlite`. |
| N8 | INFO | The `tool.call` hook observes with `void` after returning `next(e)`'s result. | Leave as a design note unless a live run shows a digest missing a file. |
| N9 | INFO | `$.process` on the desktop surface is UNKNOWN; the git segment and the ledger replay depend on it. | Check in the desktop app during the live smoke test (status shows `(ledger unavailable)` if absent). |
| N10 | INFO | An outer AbovePrompt hook that omits `next(e)` (Pulse's focus band) hides the welcome-back band. | Optional: ask Pulse to wrap `next(e)` too, which would make both bands show. |
| N11 | INFO | Relay residuals: duplicate delivery from an idle live session (ledger no-op), bounded re-relay after a cap drop, only the eight newest earlier files scanned. | Leave as disclosed; revisit only if live use shows stranded rows. |

Earlier findings N1-N6 (first three audits) and N12 (fourth audit) are repaired at this head.

## Rules for acting on these

- A code or docs repair changes the audited subject and needs a new audit on an operator-approved route.
- Live-run verification is an operator step and is `NOT_RUN` here.
- Attestation of audit independence, signing, push and merge stay with the operator.
