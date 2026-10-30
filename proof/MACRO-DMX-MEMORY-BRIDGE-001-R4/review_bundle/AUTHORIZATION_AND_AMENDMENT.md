# Authorization and amendment record - MACRO-DMX-MEMORY-BRIDGE-001-R4

All lines below were typed by the operator in this session's chat on 2026-10-30 (not relayed).

1. `Repair N3, N4, N6` (answer after the R3 re-audit). The coordinator issued R4 v1 (preserved here as `ISSUED_V1_*`).
2. `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R4_EXECUTION=YES`
3. `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R4_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`
4. The operator switched the coordinator session to `claude-opus-5-5` (`/model`) and then wrote: `redesign N3 with opus and complete fixes`.

No workstream had been dispatched and no repository file had changed when instruction 4 arrived.

## Amendment v1 → v2 (coordinator: claude-opus-5-5)

Only the N3 design changed. Findings (N3, N4, N6), write allowlists (W01: `register.tsx`, `register.test.ts`; W02: `README.md`, `docs/02-how-to/memory-bridge.md`), routes (W01 Sonnet, W02 Haiku → Sonnet), allowances and the audit route are unchanged.

| | v1 (issued) | v2 (executed) |
|---|---|---|
| N3 | Label earlier sessions' unsent rows: a status suffix ` · N left by earlier sessions`; rows stay stranded forever | Fix the cause: at session start, relay (adopt by copy, same id) the undelivered task and note rows of earlier sessions whose outbox has been quiet for at least 10 minutes and that are at most 7 days old, at most 50 per start; the source file is never written; the replay delivers them with `event_id = row.id`, which the ledger's `INSERT OR IGNORE` makes idempotent (checked in `src/dopemux/memory/capture_client.py` at the insert, around line 540). `📮 N pending` counts only rows this process will deliver. |
| N6 | Remove the unreachable `/clear` branch | Same, as a consequence of removing `foldedPending` |
| N4 | `decisionsOf` scans the first 200,000 characters | Unchanged |
| Docs (W02) | Document the suffix; keep the 'Not built' row | Document the relay; remove the 'Not built' row 'Replay of other sessions' pending rows' |

Why the redesign is the better fix: the suffix only made a stranded row visible; it still never reached the ledger. The relay keeps the single-writer rule (no session writes another session's file), needs no new delivery path, and is safe under concurrency because duplicate delivery is a ledger no-op. Residuals it accepts: a live session idle for more than 10 minutes with undelivered rows may see them delivered by another session too (harmless); a relayed row whose 'sent' copy is later dropped by the 1 MiB cap may be relayed again by a later session while the original file stays in the newest-eight window (another ledger no-op, bounded by the 7-day age limit).

Authority reading: instruction 4 is the operator's own direction to change the N3 design and complete the fixes after authorizing R4, with no other scope change. The coordinator executes the amended v2 under authorizations 2 and 3 plus instruction 4, records it here, and keeps the issued v1 unchanged beside it. Still excluded: push, PR update, signing, attestation, merge, a second audit of this head, any advisor call.

## Package hashes

| Member | v1 (issued) | v2 (executed) |
|---|---|---|
| `MACRO_PACKET.json` | `73a4d94b9fcac84459fd784f7cf732ba273c99350d83b0386c392f00852186e2` | `550154776a84015bcfb979d317cbf7aa155061b2159d95d2f39e368aa6d52513` |
| `EXECUTION_BINDING.json` | `5311efc04375a5f5dc927b490a6f9858c3e1cef742a32e866f1551318c8c2889` | `fd3ecf9218aace4d32aab7fa3afae553afd059cf354d432afbc9b6451e75d0d2` |
| `W01 TASK_PACKET.json` | `5b2ad0c47f52385379cb7bae2a072cdd3717c0c23ce7375626fbe4c181fac7ae` | `3c10cab3c7ed1f348a28b30f647a33fe87aad4e016b1f9d61112fe2e9ede6b73` |
| `W02 TASK_PACKET.json` | `c97aafe57cd2bec48472923f5d0f3429659b25b5ff75fbee04bf11ff366f15ce` | `3f77395ee4c969868f610bf9dc76f9f8ee45232d6ad12fa5aebfcdb871c32528` |

v2 validation: `ct validate-macro` STATIC_VALID; `ct validate-binding` PASS; `task_packet.v2` schema PASS ×2; pins MATCH.
