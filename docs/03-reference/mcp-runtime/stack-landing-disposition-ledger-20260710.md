---
id: mcp-runtime-stack-landing-disposition-20260710
title: MCP runtime stack cumulative landing disposition ledger
type: reference
owner: @hu3mann
last_review: 2026-07-10
next_review: 2026-10-08
---

# MCP Runtime Stack Landing — Ancestor Disposition Ledger

**Landing source tip (pre-rebase):** `dc04fd43d` (#1031 cumulative head)  
**Landing branch:** `codex/tp-dmx-mcp-runtime-stack-landing`  
**Base:** current `main` (after accidental early merges of #1021/#1022/#1023)

## Packet disposition

| PR | Packet | Live outcome | Disposition |
|----|--------|--------------|-------------|
| #1022 | 001 doctor | **MERGED** to main (2026-07-10) before freeze | Historical; findings re-applied on landing |
| #1023 | 002 lifecycle | **MERGED** to main before freeze | Historical; findings re-applied on landing |
| #1027 | 003 repair/fleet | OPEN; **freeze** — do not merge | SUPERSEDE after landing |
| #1028 | 004 leases | Merged into stack intermediate | SUPERSEDED by landing |
| #1029 | 005 TO identity | OPEN; freeze | SUPERSEDE after landing |
| #1030 | 006 proof | Merged into stack intermediate | SUPERSEDED (do not treat as governance alone) |
| #1031 | 006R cumulative | Merged into intermediate | **SOURCE** for landing; not direct main merge |

## Landing repairs applied (A–E)

| Area | Status |
|------|--------|
| A Env/config reporting (PARTIAL envrc, redaction, desired-services, --repo force) | Applied via cherry-pick + verify |
| B Port allocation/leases (occupied fixed/singleton block, scope, no unsafe fallback) | Applied + unit tests |
| C TO identity (wrapper not live proof; ID mismatch CONFLICT; normalized IDs) | Applied + unit tests |
| D Proof harness (JSON parse, redaction, BLOCKED exit, relative paths) | Applied; invalid redacted JSON repaired |
| E Live runtime re-proof | **PENDING** operator live dNh campaign against final head |

## Non-MCP

| PR | Disposition |
|----|-------------|
| #1021 | **MERGED** (preferred notification copy) |
| #1024 | **CLOSED** as duplicate of #1021 |
| #1025 | FROZEN; repair then merge after MCP landing |
| #1026 | FROZEN; last after re-census |
