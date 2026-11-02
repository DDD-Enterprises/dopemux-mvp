# MACRO-DMX-MEMORY-BRIDGE-001-R6 — follow-ups from the accepted PASS_WITH_RISKS verdict

Audited content head: `1cddbfb339650c4f8f02e87cb62e7aa8f08f90e1`. Auditor: grok-cli / grok-4.5, tool-less, one attempt. Verdict: `PASS_WITH_RISKS`, Q1-Q14 all PASS, C1-C4 REPAIRED, no new findings.

Operator decision, 2026-11-01, in chat: "Yes, accept them" (the answer to: accept N7-N11, all INFO, for the R6 head, as for R5).

Every finding below was OPEN in the auditor's output and is now `ACCEPTED_RISK` in `PROOF.json`. None was repaired; all are INFO. They were also accepted for the R5 head `bce150b58` on 2026-10-30 (`proof/MACRO-DMX-MEMORY-BRIDGE-001-R5/review_bundle/FOLLOWUPS.md`).

| ID | Severity | Finding | Direction (coordinator's reading, not a decision to repair) |
|---|---|---|---|
| N7 | INFO | The mod has never run in a real Claude Code session; proof is test-kit only. | Live smoke test: one session completes a todo and ends; after 10 quiet minutes a second session starts; check the status line, the outbox files and `.dopemux/chronicle.sqlite`. |
| N8 | INFO | The `tool.call` hook observes with `void` after returning `next(e)`'s result. | Leave as a design note unless a live run shows a digest missing a file. |
| N9 | INFO | `$.process` on the desktop surface is UNKNOWN; the git segment and the ledger replay depend on it. | Check in the desktop app during the live smoke test (status shows `(ledger unavailable)` if absent). |
| N10 | INFO | An outer AbovePrompt hook that omits `next(e)` (Pulse's focus band) hides the welcome-back band. | Optional: ask Pulse to wrap `next(e)` too, which would make both bands show. |
| N11 | INFO | Relay residuals: duplicate delivery from an idle live session (ledger no-op), bounded re-relay after a cap drop, only the eight newest earlier files scanned. | Leave as disclosed; revisit only if live use shows stranded rows. |

Earlier findings N1-N6 and N12 stay repaired, and the Copilot findings C1-C4 are repaired at this head.

## Not decided here

- C4 (R2 wall-time cap exceeded): ratifying the overrun after the fact, or recording R2's aggregate as `NEEDS_SUPERVISOR`, is a separate operator decision (`ERRATUM_R2_WALL_CAP.md`). This acceptance does not settle it.
- The residual `📮 memory-only` label (a rename changes code) is not a finding; the docs explain it.

## Rules for acting on these

- A code or docs repair changes the audited subject and needs a new audit on an operator-approved route.
- Live-run verification is an operator step and is `NOT_RUN` here.
- Attestation of audit independence, signing, push and merge stay with the operator.
