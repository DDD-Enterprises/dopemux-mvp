---
id: TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001
title: MCP Just-Works M1 Follow-ups (status lease ports, dry-run leases, expired build PID, cancel forwarding)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-19'
last_review: '2026-11-19'
next_review: '2027-02-17'
prelude: Companion to the L2 packet that closes the four follow-ups left open when
  PR 1503 merged. Covers routing, code anchors and the hand-off shape; the JSON
  packet is the authority.
---
# TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001

Companion to `task-packets/TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001.json`. The JSON is the authority; this file adds routing, code anchors and the hand-off shape.

- Base: `main` at `365f70ce2edc907d14356d82d2843104dbdaa434` (merge of PR #1503, MACRO-DMX-MCP-JUST-WORKS-M1-001)
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1-followups`
- Branch: `fix/mcp-just-works-m1-followups`
- Lane: L2. `MERGE_AUTHORIZED=NO`. Branch push and one draft PR are authorized; nothing else on GitHub is.

## Routes

```
TP_ROUTE
workstream=implement (S0-S8)
runner=codex
model=UNKNOWN
effort=UNKNOWN
skills=NONE
why=Owner asked for a Codex-executed packet; no model or effort pin was given, so the owner sets both at launch.
```

```
TP_ROUTE
workstream=gates (commands inside S0, S7)
runner=local-shell
model=NONE
effort=UNKNOWN
skills=NONE
why=Deterministic test, lint and diff-scope commands.
```

```
TP_ROUTE
workstream=independent-audit (S9, held until head freeze)
runner=grok
model=UNKNOWN
effort=UNKNOWN
skills=independent-audit
why=The implementer is Codex, so the controlling audit must be a non-Codex route; Grok governed the PR #1503 audits. The owner confirms the exact model at launch.
```

## The four items and where they live (line numbers at the base commit)

| Item | Defect | Anchor |
|---|---|---|
| A | `dopemux mcp status` shows envrc ports after a start leased replacements | `src/dopemux/mcp/lifecycle.py` `_resolve_ports` (377), `_leased_ports` (293), `_status_result` (3219) |
| B | `start --dry-run` / `restart --dry-run` write port leases | `src/dopemux/mcp/lifecycle.py` `_mutable_facts` (1026) calls `_resolve_ports(..., allocate=True)`; `src/dopemux/mcp/port_allocator.py` `allocate_ports` (274) already accepts `persist` and `dry_run` |
| C | A build older than `DOPEMUX_MCP_BUILD_TIMEOUT_SECS` loses its PID while alive, so reconnects can stack builds | `src/dopemux/mcp/launcher.py` `_live_build_pid` (400, age test at 411), caller at 440; rule copied in `src/dopemux/mcp/reap.py` (507-518) |
| D | Runner cancel of an in-flight tool call is not forwarded to the backend | `src/dopemux/mcp/stdio_proxy.py` `forward` and its `_inflight` cancel scopes |

Background for B: a first attempt on 2026-11-12 was stopped before any edit because five tests in `tests/unit/test_mcp_lifecycle_ports_from_leases.py` assert that a dry run allocates leases, and the `_start` helper there defaults to `dry_run=True`. Those tests encode the defect. S3 rewrites them; it does not delete them.

Background for C: the owner chose "fix in a follow-up" on 2026-11-15 rather than hold PR #1503. The Codex review asked for the expired build to be terminated before its PID is discarded, or kept tracked until it exits. This packet takes the first option, with a PID-identity check so a recycled PID is never signalled.

## Host state Codex must leave alone

About 20 containers from the M1 acceptance run are still up (`dopemux-*-55ab-*`, `*-570c-*`, `*-d79c-*`), plus two throwaway repos and the automatic-reap kill switch `~/.dopemux/mcp/runtime/reap.disabled`. Cleanup is a separate owner decision. All tests in this packet are hermetic and need none of it.

## Hand-off message (in this order)

1. **Status:** exactly one of `READY_FOR_AUDIT`, `BLOCKED`, `NEEDS_SUPERVISOR`, `INCOMPLETE`.
2. Gates table: each command, its exit code, its bucket (`PASS`, `FAIL`, `NOT_RUN`, `UNKNOWN`).
3. Blockers, each with the exact action that clears it.
4. Proof path, plus requested vs observed route per workstream.
5. What this packet did not authorize: merge, signing, thread resolution, steward phrase, host cleanup.

## Auditor verdict contract (S9)

The auditor returns `PASS`, `PASS_WITH_RISKS` or `FAIL`, the audited head SHA, and findings each with severity, file:line and a failing scenario. It checks in particular: each of A-D has a test that failed on the base for the stated reason; no read-only command writes the lease registry; no code path signals a PID without the identity check; the cancel notification uses the backend request id; nothing outside the allowlist changed.
