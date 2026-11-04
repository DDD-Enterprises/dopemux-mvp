# MACRO-DMX-MEMORY-BRIDGE-001-R6 — Issuance Record (flaky-test fix + base update after #1482)

**Issued**: 2026-10-30 by the Control Tower supervisor session (Claude Code desktop, `claude-opus-5-5`).
**Operator instructions**: "Update main first", then "Fix it first"; merge order "Run it in order" (#1482, #1483, #1485, #1484), relayed by the commissioning session.
**State at issuance**: branch head `c1256c060` = local, unpushed merge of `origin/main` `97b6d5040` (Pulse) into the R5 branch; R5 audited subject `bce150b58` (operator-accepted). PR #1483 draft at `bff3fd46e`; PR #1482 OPEN (not merged). Authority: NONE.

## Execution gate

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R6_EXECUTION=YES
```

The final audit of the merged head (after #1482) needs its own line, which you can send now or later:

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R6_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT
```

## Package members

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `8e07297c2501b6e58dca3b05274873641833c753af5fbd8228a6f7e99cd339db` |
| `EXECUTION_BINDING.json` | `891e05e8fd9fd2266f3666668b50afa30e44ba897a2debc42cfcb4687f196d06` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `6b0aec4d28a09a74fc591aeb1c6597f62c0347898dbd0651a5f26e59f29e141b` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `ba0dce253a5e554c0184fef3d270f8dc28d31cdd8238db5467d35b77cb6ed747` |

## Workstreams

| WS | When | What | Write allowlist | Route |
|---|---|---|---|---|
| W01 | now | Reproduce the flake under 6-way concurrent load, find the race, make the key-table test wait deterministically for the outbox write (bounded wait helper; no weakened assertion, no skipped test, no unbounded sleep); prove it with 12 concurrent runs and 0 failures. If the cause is a product race in `register.tsx`, stop with NEEDS_SUPERVISOR (out of scope). | `plugins/dopemux-memory-bridge/hooks/register.test.ts` only | claude-sonnet-5-5 (flaky-test root cause needs judgment; Haiku would tend to paper over it) |
| W02 | after #1482 MERGED | Sync the then-current main with the app's sync tool (other sessions' edits restored byte-identical), run every gate incl. all plugins on main and repeated concurrent runs, freeze the merged head, prepare the R6 audit bundle. | `proof/MACRO-DMX-MEMORY-BRIDGE-001-R6/` | local-shell (the coordinator; no model call) |

Then: one Grok audit of the merged head (on your route line; the prompt carries one line per earlier finding, the lesson from R5), adjudication, unsigned `PROOF.json`, and a new sign script bound to that head. Push and signing stay yours.

## PROPOSED allowances

W01: 30 min, 300,000 tokens, 100 tool uses, 1 Sonnet attempt + 1 retry. W02: no model call, 60 min of work after the gate opens. Macro: 400,000 tokens, 2 dispatches; intermediate audits 0; advisor 0. Audit outside the budget: 1 attempt, 0 retries (about $0.08).

## Validation at issuance

`ct validate-macro` STATIC_VALID; `ct validate-binding` PASS; `task_packet.v2` schema PASS ×2; pins MATCH.

## Evidence of the flake (coordinator, at `c1256c060`)

7 sequential runs: 134/134 each. 6 concurrent runs: 4 pass; 2 fail with `AssertionError: expect(received).toBeGreaterThan() Expected: > 0 Received: 0` in `session id "xxxxxxxxxxxxxxxxxxxxxxxx" writes only the outbox key xxxxxxxxxxxxxxxxxxxxxxxx` (the two >80-character ids). The same test was in the R5 audited subject `bce150b58`; the R5 audit did not flag it.
