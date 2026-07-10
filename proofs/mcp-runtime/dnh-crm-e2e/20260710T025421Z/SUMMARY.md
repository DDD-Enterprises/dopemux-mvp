# TP-DMX-MCP-RUNTIME-006 Summary

**overall_status:** `BLOCKED` (safe preflight stopped live mutation)

## Core proof question

Can dNh_CRM use Dopemux MCP without colliding with dopemux-mvp / wrong TO?

**Answer this run:** Not yet green — system correctly **refused** unsafe TO use and repair allocation hit a foreign fixed-port lease.

## What was proven

| Area | Result |
|------|--------|
| Commands 001–005 present | YES |
| doctor --repo dNh | RAN (status FAIL — expected pre-start) |
| repair-config --dry-run | FAILED allocate: 7890 leased to `/Users/alice/code/project-a` |
| start --dry-run | BLOCKED: TO UNKNOWN owner + lease mismatches |
| Fail-closed TO identity (005) | WORKED (not forced PASS) |
| Live start | SKIPPED |
| ~/.claude.json mutation | NONE |
| Agent bootstrap doc on dNh | MISSING (apply never ran) |
| .mcp.json transports | PASS (sse/http/http) |

## Guard dog moments (not failures)

1. TO on :7890 with unproven identity → start blocked
2. Foreign lease on 7890 → repair allocate blocked  
3. No wrong-project container stopped
4. No live start without dry-run clearance

## Operator follow-ups

1. Clean stale port-leases entry for test path project-a on 7890
2. Identify :7890 listener; do not adopt unlabeled
3. Re-run e2e with `--live`

Proof path: `proofs/mcp-runtime/dnh-crm-e2e/20260710T025421Z`
