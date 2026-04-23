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
**Status**: Fully Resolved
**Scope**: Seven items carried forward from SPEC.md §9.5 (v2.0a §11.5)
**Impact**: All seven items (U1-U7) are now resolved. Multi-backend source wiring is unblocked. Implementation can proceed with frozen transport contracts and immutable role/display/state/memory contracts.

---

## U1: `Source` Adapter HTTP/RPC Surface Per Backend

**Status**: RESOLVED

**Resolution applied**:
All seven transports defined and locked. `dope-context` uses HTTP/JSON over bearer token from env, cursor pagination, and structured filter object. The six remaining backends (`task-orchestrator`, `leantime`, `conport`, `dope-memory`, `dopecon-bridge`, `dopetask`) each follow HTTP/JSON over HTTPS with bearer auth and cursor pagination.

**Transport-Specific Details**:
1. **task-orchestrator**: POST /transitions/{id} for workflow state changes; GET /work-items/{id}/workflow for queries
2. **leantime**: PATCH /tickets/{id} for metadata updates; GET /tickets/{id}/metadata for queries
3. **conport**: POST /progress-entries and POST /decisions for writes; GET /work-items/{id}/context for queries
4. **dope-memory**: POST /chronicle-entries only (append-only); GET /chronicle/{id} for timeline queries; corrections via supersedes_id
5. **dopecon-bridge**: POST /proxy/conport with policy-wrapped forwarding to canonical ConPort; role-gating enforced (shift-Y)
6. **dopetask**: GET /health for direct health probing; POST /execute for task commands; POST /heartbeat for status (execution-only, no canonical writes)

**Common Contract Elements**:
All seven transports use:
- Protocol: HTTP/JSON over HTTPS
- Auth: Bearer token from DOPEMUX_<SERVICE>_API_KEY env variable
- Pagination: Cursor-based (page_token, max_results)
- Idempotency: X-Idempotency-Key header required
- Error format: {error: string, code: string}

**Why this decision**:
Production wiring requires explicit, immutable transport contracts per backend. Append-only semantics (dope-memory), adapter-only proxy pattern (dopecon-bridge), and execution-only isolation (dopetask) preserve authority boundaries and prevent unintended cross-service mutations. Bearer-token auth over HTTPS with cursor pagination provides consistent auth model and scalable result handling across all seven services.

---

## U2: `dopetask` Health Endpoint Path

**Status**: RESOLVED

**Resolution applied**:
`dopetask` exposes its own `/health` endpoint directly. Services pane probes dopetask directly every 5 seconds. Response format: `{status: "healthy|degraded|critical", uptime: seconds, workers_active: int, timestamp: ISO8601}`. HTTP status codes: 200 (healthy), 503 (degraded), 500 (critical). Response time < 50ms, no external dependencies.

**Why this decision**:
Execution-critical service; direct endpoint ensures sub-5-second failure detection without cascading dependencies. Health rollup via task-orchestrator would create detection blind spot precisely when it's most needed.

**Implementation effect**:
Build step 12 may implement `[4]Services` health row for dopetask as a direct probe result with "real-time" glyph. No rolled-up aggregation; each service owns its health reporting.

**See also**: ADR-220 (dopetask-direct-health-endpoint.md) for full architectural decision

---

## U3: Event Stream Rate Limits and Tail Retention

**Status**: RESOLVED

**Resolution applied**:
Server-side rate limit: 200 events/sec (3.3 events/frame at 60 FPS). Client-side tail buffer: 15 minutes (900 seconds) covering ADHD context-switch windows. Client-side coalescing debounce: 50ms (event deduplication for rapid updates). Fallback config available: 100 events/sec + 10-minute buffer + 100ms debounce if timeline pressures emerge.

**Telemetry hooks**:
events_dropped (rate-limited), events_coalesced (debounced), buffer_fullness (%), client_lag (ms). Post-launch tuning enabled via environment variables; no breaking API changes.

**Why this decision**:
200 evt/sec balances real-time responsiveness with frame budget. 15-minute tail buffer preserves ADHD context across interruptions (tab switch, app switch, notifications). Coalescing reduces noise from progress spinners and task updates. Conservative defaults safe for launch; telemetry-driven optimization post-week-2.

**Implementation effect**:
Build step 13 may implement event stream pane with hard rate limit enforcement at server, ring buffer at client, and coalescing for noisy event types. Memory budget: ~225KB per client.

**See also**: ADR-221 (event-stream-rate-limits.md) for full architectural decision

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
| U1 | RESOLVED: All seven transports defined and locked: dope-context (HTTP/JSON + bearer + cursor + filter) + six backends (task-orchestrator, leantime, conport, dope-memory, dopecon-bridge, dopetask) | Packet TP-DMX-TUI-TRANSPORT-ARCHITECTURE-005 | 2026-04-23 | All transports frozen; implementation can proceed; dopecon-bridge adapter-only (policy-wrapped proxy); dopetask execution-only (no canonical state); dope-memory append-only (chronicle) |
| U2 | RESOLVED: Direct `/health` on dopetask, no aggregation | ADR-220 | 2026-04-23 | Direct probe ensures <5sec failure detection; sub-50ms response |
| U3 | RESOLVED: 200 evt/sec + 15-min buffer + 50ms debounce | ADR-221 | 2026-04-23 | Balanced for frame budget & ADHD context windows; post-launch tuning enabled |
| U4 | RESOLVED | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | Two-role session model: `operator`, `approver`, or both |
| U5 | RESOLVED | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | Newest unread wins; mode-aware tie break; stable fallback ordering |
| U6 | RESOLVED: `[LOGGED]` remains on the envelope; `[EDGE]` not approved for PKB arrival | Packet TP-DMX-TUI-U6-BRAND-CLOSURE-004 | 2026-04-23 | Scope-edge meaning is body-rendered only; no new chip |
| U7 | RESOLVED | Packet TP-DMX-TUI-DOCS-PATCH-003 | 2026-04-23 | Append-only dope-memory receipt with `pinned_at` |

---

## Next Steps

1. All seven transports (U1 items) are now frozen and locked. Implementation can proceed immediately.
2. All seven items (U1-U7) are resolved. Implementation planning can use all resolved constraints as hard bounds.
3. Source wiring for all seven backends (task-orchestrator, leantime, conport, dope-memory, dopecon-bridge, dopetask, dope-context) is unblocked.
