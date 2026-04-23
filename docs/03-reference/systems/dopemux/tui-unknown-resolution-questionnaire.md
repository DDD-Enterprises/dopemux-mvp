---
id: tui-unknown-questionnaire
title: TUI Round 2 UNKNOWN Resolution Questionnaire
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-23'
last_review: '2026-04-23'
next_review: '2026-04-23'
prelude: Seven open questions blocking implementation steps in the TUI Round 2 build order.
---

# TUI Round 2 UNKNOWN Resolution Questionnaire

**Date**: 2026-04-23
**Status**: Partially Resolved
**Scope**: Seven items carried forward from SPEC.md §9.5 (v2.0a §11.5)
**Impact**: U1 remains partially open and still blocks broad source wiring. U2 and U3 remain open. U4, U5, U6, and U7 are resolved for this spec pass.

---

## U1: `Source` Adapter HTTP/RPC Surface Per Backend

**Status**: PARTIAL

**Resolution applied**:
`dope-context` only is resolved to HTTP/JSON over bearer token from env, cursor pagination, and a structured filter object. The other six backends (`task-orchestrator`, `leantime`, `conport`, `dope-memory`, `dopecon-bridge`, `dopetask`) remain unresolved and must not be normalized by assumption.

**What remains open**:
For the six unresolved backends, protocol, auth model, pagination contract, and filter surface still need explicit runtime decisions.

**Why it still blocks implementation**:
`Source` trait's concrete methods may now be written for `dope-context`, but multi-backend production wiring remains blocked for the other six services. Build step 3 is unblocked for `dope-context` rows only; build step 8 remains partial outside that slice.

---

## U2: `dopetask` Health Endpoint Path

**Status**: PENDING

**Exact decision needed**:
Does `dopetask` expose its own `/health` endpoint directly, or is its health surfaced only via `task-orchestrator` as a dependency rollup?

**Why it blocks implementation**:
`[4]Services` health row for `dopetask` must show either a direct probe result or a rolled-up status with a different glyph meaning. Blocks build step 12; currently degraded to "unknown" placeholder.

**Suggested default if fast**:
Direct `/health` on `dopetask` — it's execution-critical and a rollup hides failure modes. If `dopetask` is strictly a worker with no HTTP surface, promote the rollup answer and document it explicitly in the Source adapter table.

**Fallback if not decided**:
Render as "unknown" on `[4]Services` and mark as TBD. Non-blocking for MVP.

---

## U3: Event Stream Rate Limits and Tail Retention

**Status**: PENDING

**Exact decision needed**:
Max events/sec the `[5]Events` pane will subscribe to without backpressure; tail retention window (minutes of history kept in the client ring buffer).

**Why it blocks implementation**:
Frame budget (`max(2 fps, event-driven)`) and memory ceiling depend on this. Too permissive and the TUI drops frames on burst; too tight and operators miss events during context switch. Blocks build step 13 (event stream pane) and step 12 (packet lifecycle with reaper events).

**Suggested default if fast**:
200 events/sec cap with client-side coalescing, 15-minute tail buffer. Tune after first week of real load. If upstream event rate is unknown, start with 50 events/sec and scale up.

**Fallback if not decided**:
Use 100 events/sec and 10-minute buffer; mark as experimental and plan first tuning session 1 week post-launch.

---

## U4: Role Model for Non-`[a]` Canonical Writes

**Status**: RESOLVED

**Resolution applied**:
The TUI uses exactly two human roles: `operator` and `approver`. A session may carry `operator`, `approver`, or both.

**Operational rule**:
Non-`[a]` canonical writes (`[H] send`, `[c]`, `[x]`, `[p]`, and any write-bearing `[o]` flow) require `operator`. `[a] approve` requires `approver`. No third role is introduced by this decision.

**Implementation effect**:
Build step 9 may wire the role resolver against the two-role session model without waiting for another role pass. Unknown-role sessions render action glyphs but confirm modals must refuse with a role-required message rather than silently succeeding.

---

## U5: Display Priority When Unread PKT and Unread PKB Coexist on the Same Task

**Status**: RESOLVED

**Resolution applied**:
Render the newest unread packet in the single row-affordance slot. If timestamps tie, PM mode prefers `PKB`, Implementer mode prefers `PKT`. If timestamps remain tied after mode-aware preference, fall back to lexical packet-type ordering (`PKB` before `PKT`) for stable redraws.

**Implementation effect**:
Build step 6 may implement a deterministic precedence algorithm rather than a heuristic or dual-glyph compromise.

---

## U6: `[EDGE]` Chip Reuse on PKB Recommendation Arrival — Brand-Voice Review

**Status**: RESOLVED

**Resolution applied**:
`[EDGE]` is not approved for PKB scope-edge arrival on the envelope. `[LOGGED]` remains on the envelope. Scope-edge meaning is rendered in packet body or inspector copy only. `[OVERRIDE]` is explicitly rejected for this meaning.

**Approved fallback copy**:
1. PKB arrival line: `[LOGGED] PKB-0481 received. Scope-edge recommendation in body.`
2. Scope-edge body text: `Scope edge: This recommendation extends beyond the current agreed scope. Review before any workflow transition or metadata write.`
3. Confirm modal text:
   `Confirm: apply recommended transition`
   `target: task-orchestrator`
   `action: transition after scope-edge review`
   `affected: T-1203 via PKB-0481`
   `role required: operator`
4. Role-required refusal: `[BLOCKER] Operator role required. Scope-edge recommendation cannot be actioned in this session.`

**Implementation effect**:
Build step 14 may proceed with a closed result: `[LOGGED]` on the envelope, body-rendered scope-edge meaning, and no chip vocabulary change.

---

## U7: Pin-State Schema: Owner and Field Name

**Status**: RESOLVED

**Resolution applied**:
`dope-memory` owns the pin mirror state. The chronicle receipt field is `pinned_at: timestamp|null`.

**Append-only rule**:
Pin and unpin each write a new dope-memory receipt. Unpin writes a new receipt with `pinned_at: null`; the reaper reads the latest receipt per packet id.

**Implementation effect**:
Build step 11 may implement pin/unpin against append-only receipt semantics without mutating prior receipts.

---

## Resolution Tracking

| Item | Decision | Decided By | Date | Notes |
|------|----------|-----------|------|-------|
| U1 | PARTIAL: dope-context resolved (HTTP/JSON + bearer + cursor + structured filter); 6 remaining | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | `dope-context` only; six backend transport decisions still open |
| U2 | PENDING | | | Direct endpoint preferred; rollup acceptable if no direct surface |
| U3 | PENDING | | | 200 events/sec + 15-min buffer suggested; tune post-launch |
| U4 | RESOLVED | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | Two-role session model: `operator`, `approver`, or both |
| U5 | RESOLVED | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | Newest unread wins; mode-aware tie break; stable fallback ordering |
| U6 | RESOLVED: `[LOGGED]` remains on the envelope; `[EDGE]` not approved for PKB arrival | Packet TP-DMX-TUI-U6-BRAND-CLOSURE-004 | 2026-04-23 | Scope-edge meaning is body-rendered only; no new chip |
| U7 | RESOLVED | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | Append-only dope-memory receipt with `pinned_at` |

---

## Next Steps

1. Resolve the six non-`dope-context` transport decisions as engineering/runtime work.
2. Resolve U2 and U3 against runtime evidence.
3. Proceed with implementation planning using the resolved U4/U5/U6/U7 constraints and the partial U1 constraint as hard bounds.
