# EXEC-012 / DR04 — Amendment 030 evidence

Live-dispatch evidence for `MACRO-DMX-DR04-EXEC-012-LIVE-DISPATCH-029` under operator
amendment 030 (Routes A and D moved to API-metered inference) and operator option "b"
(agent_message arity repair, a second Route D attempt, and Route A).

**Start here → [`SUPERVISOR_HANDOFF.md`](SUPERVISOR_HANDOFF.md)** · machine-readable return in
[`SUPERVISOR_RETURN.json`](SUPERVISOR_RETURN.json) · full working log in `CHECKPOINT.md`.

## Result in one line

Route D ran live three times and produced no research report; attempt 3 established that the
cause is a **structural defect in the frozen retrieval budget** (6 codex turns vs 6 retrieval
slots leaves no turn to write the report). Route A never reached a provider — it requires a
macOS Terminal.app process ancestry. **Spend $8.28 of a $10 ceiling.**

## Layout

| Path | Contents |
|---|---|
| `SUPERVISOR_HANDOFF.md` | The handoff — findings, outcomes, decisions needed |
| `SUPERVISOR_RETURN.json` | Machine-readable return |
| `CHECKPOINT.md` | Chronological working log, including every trap and correction |
| `evidence/` | Per-dispatch result records, the API-route probe, the topology blocker, the lead-error pattern, Route A's authorization |
| `shared_contracts/` | `message_arity.py` (the repair) and the W01 parity contracts both routes import by absolute path |
| `route_d/attempt_01..03/` | Per-turn receipts (full event streams), ledgers, retrieval captures |

## Reading notes

- **Nothing here was adopted or activated.** All work was performed on a revertible copy; the
  audited original surface was never edited and re-verified clean after every dispatch.
- **`turn_*_request.json` files are excluded** (~3.7 MB). Each is the same ~319–412 KB payload
  dominated by an unchanged 233 KB acceptance schema. The receipts carry the substance.
- **Receipts include the child's stderr**, which on this provider path contains a benign
  `codex_models_manager` warning plus the raw `/v1/models` response body. That is preserved
  as-recorded rather than trimmed, because the receipts are hash-covered evidence.
- **Token counts are exact**, taken from `turn.completed` usage. Dollar figures assume
  $10/$50 per million and are **not** verified against a price sheet.
