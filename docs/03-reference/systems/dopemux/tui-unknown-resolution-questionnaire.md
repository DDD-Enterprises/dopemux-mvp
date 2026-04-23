---
id: tui-unknown-questionnaire
title: TUI Round 2 UNKNOWN Resolution Questionnaire
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-23'
last_review: '2026-04-23'
next_review: '2026-04-23'
prelude: Seven open questions blocking implementation steps in the TUI Round 2 build order.
---

# TUI Round 2 UNKNOWN Resolution Questionnaire

**Date**: 2026-04-23
**Status**: Open
**Scope**: Seven items carried forward from SPEC.md §9.5 (v2.0a §11.5)
**Impact**: Each item blocks one or more build steps. Resolution required before step 3.

---

## U1: `Source` Adapter HTTP/RPC Surface Per Backend

**Exact decision needed**:
For each of `task-orchestrator`, `leantime`, `conport`, `dope-memory`, `dope-context`, `dopecon-bridge`, `dopetask`: pick protocol (HTTP/JSON, gRPC, local socket), auth model (bearer, mTLS, unix-socket peer cred, none), pagination contract (cursor, offset, none), and filter surface (query params, structured filter object, server-side preset only).

**Why it blocks implementation**:
`Source` trait's concrete methods cannot be written without a per-backend contract. Blocks build steps 3–8. Mock implementations can proceed in parallel, but production deployment requires this surface defined.

**Suggested normalization target** (not assumed reality):
HTTP/JSON + bearer token from env + cursor pagination + structured filter object for all seven services. Real implementations will diverge; this is the preferred target for alignment work. Note: `dopecon-bridge` may require different auth (e.g., no auth for local adapter pattern).

**Fallback if not decided**:
Use HTTP/JSON as baseline; ship with documented contract mismatches and upgrade plan.

---

## U2: `dopetask` Health Endpoint Path

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

**Exact decision needed**:
Who may invoke `[H] send`, `[c]` (clear/cancel — pane-dependent), `[x]` (close/kill — pane-dependent), `[p] pin`, `[o] open`? Are these gated by the same role that gates `[a] approve`, by a looser operator role, or ungated for any authenticated TUI session?

**Why it blocks implementation**:
Confirm modal rendering and action-availability checks need a role resolver. Blocks build step 9 (role model wire). Cannot ship until clear.

**Suggested default if fast**:
Single `operator` role for all non-`[a]` human actions; `[a] approve` remains on its own `approver` role. Two roles total. Revisit when a third actor class appears (e.g., auditor, readonly observer).

**Fallback if not decided**:
Ungated for MVP (all authenticated users can `[H] send`, `[p] pin`, etc.). Add role gating in next sprint as a compliance feature.

---

## U5: Display Priority When Unread PKT and Unread PKB Coexist on the Same Task

**Exact decision needed**:
When a task row has both an unread PM→Implementer packet and an unread Implementer→PM packet, which unread indicator renders in the narrow task-row affordance? Both? Most recent? PKT-first-PKB-second? A combined glyph?

**Why it blocks implementation**:
Row rendering function has a single affordance slot. Blocks build step 6 (task list pane detail). Cannot leave ambiguous.

**Suggested default if fast**:
Show most-recent unread only, with mode-aware tiebreak: in PM mode prefer PKB (replies are what PM needs to see); in Implementer mode prefer PKT (new work is what Implementer needs to see). The other is visible one level deeper on drill-down into the packet pane.

**Fallback if not decided**:
Show PKT priority always (work-from-PM-first convention); document as provisional and revisit after user feedback.

---

## U6: `[EDGE]` Chip Reuse on PKB Recommendation Arrival — Brand-Voice Review

**Exact decision needed**:
When a PKB arrives carrying a recommendation that crosses an agreed scope edge, does it chip `[EDGE]` (reusing the existing closed vocabulary), or does it require a new chip? Brand-voice gate must confirm `[EDGE]` reads as "scope edge crossed" and not as "experimental" or "fringe".

**Why it blocks implementation**:
Adding a chip is a closed-vocabulary amendment and needs the brand-voice pass before it lands in rendering. Blocks build step 14 (supporting views, PKB chip rendering).

**Suggested default if fast**:
Hold `[EDGE]` as preferred fallback. **Pending brand review — do not let this read like approval.** Reserve final decision until brand-voice pass completes. Use `[OVERRIDE]` as interim placeholder if needed.

**Fallback if not decided**:
Use `[LOGGED]` (packet sent, always correct); upgrade chip after brand-voice review in next release.

---

## U7: Pin-State Schema: Owner and Field Name

**Exact decision needed**:
Confirm `dope-memory` owns pin state (not `dopemux`). Name the exact field on the chronicle receipt that carries pin state (e.g. `pinned: bool`, `pin_state: enum`, `pinned_at: timestamp|null`). Confirm that unpin writes a new receipt rather than mutating the old one.

**Why it blocks implementation**:
Reaper query and pin-toggle action both need a stable read path. Blocks build step 11 (pin state implementation).

**Suggested default if fast**:
`dope-memory` owns pin state and is append-only in spirit. Field: `pinned_at: timestamp|null` on the chronicle receipt (null = not pinned, non-null = pinned at that time). Unpin writes a new receipt with `pinned_at: null` and a back-reference to original; the reaper reads latest receipt per packet id.

**Fallback if not decided**:
Use `pinned: bool` on both envelope and receipt (simpler schema, mutable on receipt). Migrate to append-only schema in next sprint if append-only assumption becomes important.

---

## Resolution Tracking

| Item | Decision | Decided By | Date | Notes |
|------|----------|-----------|------|-------|
| U1 | PENDING | | | Normalization target ready; real implementation TBD per service |
| U2 | PENDING | | | Direct endpoint preferred; rollup acceptable if no direct surface |
| U3 | PENDING | | | 200 events/sec + 15-min buffer suggested; tune post-launch |
| U4 | PENDING | | | `operator` + `approver` roles suggested; two roles total |
| U5 | PENDING | | | Most-recent + mode-aware tiebreak suggested |
| U6 | PENDING | | | **Pending brand-voice review — do not finalize** |
| U7 | PENDING | | | Append-only chronicle with `pinned_at` field suggested |

---

## Next Steps

1. User resolves U1–U7 via inline or separate decision session
2. Each resolution is added to SPEC.md §11.5 (resolved) or §9.5 (remaining)
3. Build order adjusts based on remaining blockers
4. Implementation proceeds with resolved items as hard constraints

**Timeline**: U6 requires brand-voice pass (schedule separately). Others can be resolved inline.
