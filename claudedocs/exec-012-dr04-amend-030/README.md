# EXEC-012 / DR04 — Amendment 030 evidence

Live-dispatch evidence for `MACRO-DMX-DR04-EXEC-012-LIVE-DISPATCH-029` under operator
amendment 030 (Routes A and D moved to API-metered inference) and operator option "b"
(agent_message arity repair, a second Route D attempt, and Route A).

**Start here → [`SUPERVISOR_HANDOFF.md`](SUPERVISOR_HANDOFF.md)** · machine-readable return in
[`SUPERVISOR_RETURN.json`](SUPERVISOR_RETURN.json) · full working log in `CHECKPOINT.md`.

> **Corrected 2026-09-11** from the first published commit `bc4249ee`. Claims were corrected in
> place; records were not touched. Read [`ERRATA/ERRATA.md`](ERRATA/ERRATA.md) for every change,
> the two defects recorded but deliberately **not** applied, and an open operator question about
> public disclosure.

## Result in one line

Route D ran live three times and produced no research report; attempt 3 established that the
cause is a **structural defect in the frozen retrieval budget** (6 codex turns vs 6 retrieval
slots leaves no turn to write the report). Route A never reached a provider — it requires a
macOS Terminal.app process ancestry. **Spend $8.13 of a $10 ceiling** ($8.02 across Route D's
three attempts plus a $0.11 probe).

## Layout

| Path | Contents |
|---|---|
| `SUPERVISOR_HANDOFF.md` | The handoff — findings, outcomes, decisions needed |
| `SUPERVISOR_RETURN.json` | Machine-readable return |
| `CHECKPOINT.md` | Chronological working log, including every trap and correction |
| `evidence/` | Per-dispatch result records, the API-route probe, the topology blocker, the lead-error pattern, Route A's authorization |
| `shared_contracts/` | `message_arity.py` (the repair) and the W01 parity contracts both routes import by absolute path. These ran from `W01/` in the working tree; [`ERRATA/PATH_MAP.json`](ERRATA/PATH_MAP.json) maps the `W01/...` paths cited inside the records to their published paths here. |
| `ERRATA/` | Post-publication corrections, unapplied defect records, the repair route record, and the disclosure re-confirmation request |
| `route_d/attempt_01..03/` | Per-turn receipts (full event streams), ledgers, retrieval captures |

## Reading notes

- **Nothing here was adopted or activated.** All work was performed on a revertible copy; the
  audited original surface was never edited and re-verified clean after every dispatch.
- **`turn_*_request.json` files are excluded** (~3.7 MB). Each is the same ~319–412 KB payload
  dominated by an unchanged 233 KB acceptance schema. The receipts carry the substance.
- **Receipts include the child's stderr**, which on this provider path contains a benign
  `codex_models_manager` warning plus the raw `/v1/models` response body — 136 account-visible
  model ids, in nine turn receipts. That is preserved as-recorded rather than trimmed, because the
  receipts are hash-covered evidence, and since the working-tree originals were reaped these are
  now the only copies. See [`ERRATA/DISCLOSURE_RECONFIRMATION.md`](ERRATA/DISCLOSURE_RECONFIRMATION.md).
- **Token counts are exact**, taken from `turn.completed` usage. Dollar figures assume
  $10/$50 per million and are **not** verified against a price sheet. The full reconciled ledger
  is in `SUPERVISOR_RETURN.json` → `SPEND.ledger`.
