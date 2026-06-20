# PM Sync Contract

## Canonical Ledger

Use `docs/planes/pm/task-orchestrator-leantime-followups.md` as the canonical human-readable queue and fallback audit log.

## Sync Modes

- `best-effort` (default):
  - Probe task-orchestrator health.
  - Attempt live ticket updates when reachable.
  - Always append ledger fallback entries.
- `required`:
  - Same behavior as best-effort, but fail closed if live sync cannot complete.
- `off`:
  - Skip live sync attempts.

## Live Update Endpoint

Use task-orchestrator coordination API:

- `POST /api/coordination/operations`
- Operation: `update_progress`
- `source_plane`: `pm`
- Payload should include ticket id, baseline, timestamp, and a progress note.

## Failure Handling

If health probe or live update fails:

1. Capture error details in structured output.
2. Append fallback ledger entries for each impacted ticket with retry metadata (`reason`, `retry_after_utc`).
3. Mark blocking only when sync mode is `required`.

If no ticket identifiers can be discovered:

1. Record a pending-sync ledger entry with `missing ticket identifiers`.
2. Include retry metadata so PM orchestration can re-attempt after IDs are linked.
