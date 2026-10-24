# MACRO-DMX-MEMORY-BRIDGE-001-R2 — follow-ups from the accepted PASS_WITH_RISKS verdict

Audited content head: `52855fb35ea40f420bdacdcab9e092f8d15292c6`. Auditor: grok-cli / grok-4.5, tool-less. Verdict: `PASS_WITH_RISKS`.

Operator decision, 2026-10-24, in chat:

> Accept both PASS_WITH_RISKS verdicts as-is: Memory Bridge R2 at 52855fb35 and Route Ledger R2 at 93969e7a3. Record the open findings as follow-ups and prepare the proof and signing steps; I will attest, sign and push myself.

Every finding below was OPEN in the auditor's output and is now `ACCEPTED_RISK` in `PROOF.json`. None was repaired.
The directions are the coordinator's reading of each finding's title, not decisions to repair.

| ID | Severity | Finding | Direction |
|---|---|---|---|
| N1 | MEDIUM | How-to claims code HEAD `1ce149a76` and verification at that commit; frozen audit head is `52855fb35ea40f420bdacdcab9e092f8d15292c6`. | Remove the pinned commit SHA and test count from the how-to (the same fix the Pulse follow-up applied). This is the defect behind the auditor's Q9 FAIL. |
| N2 | MEDIUM | Slash command description says 'Store a note in the capture ledger' while the command reply and intent require queued-not-stored messaging. | Reword the `/bridge-note` command description so it says the note is queued, not stored. |
| N3 | LOW | Status pending includes other sessions' replayable rows that this mod will never send, so 📮 N pending can stick until those files change outside this process. | Count only this session's rows as pending, or label the other sessions' rows in the status. |
| N4 | LOW | decisionsOf runs RegExp matchAll on the full unbounded assistant answer before any size bound. | Bound the answer text before running the decision regex. |
| N5 | LOW | Successful ledger emit increments attempts; docs describe attempts as failed-delivery counters. | Reword the README's description of `attempts`, or stop incrementing it on a successful emit. |
| N6 | INFO | On /clear, fold path that increments foldedPending from isReplayable is unreachable. | Remove the unreachable fold branch on `/clear`. |
| N7 | INFO | Live behaviour, real ledger emit, desktop $.process, fs.write atomicity, and pre-commit hooks remain NOT_RUN / UNKNOWN as disclosed. | Run the mod live and check desktop `$.process`, a real ledger emit, `$.fs.write` atomicity and Pulse band ordering. |

## Rules for acting on these
- A code or docs repair changes the audited subject, so it needs a new audit on an operator-approved route. The old verdict stays as it is.
- Live-run verification (a real Claude Code session) is an operator step and is `NOT_RUN` here.
- Attestation of audit independence, signing, push and merge stay with the operator.
