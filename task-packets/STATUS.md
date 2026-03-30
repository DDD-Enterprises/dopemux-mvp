---
id: STATUS
title: Status
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-03-27'
next_review: '2026-06-20'
prelude: Status (explanation) for dopemux documentation and developer workflows.
---
📊 Dopemux Execution Status
Subsystem Health · Change Velocity · Risk Awareness
════════════════════════════════════════════════════════════
🎯 Purpose
This document provides a snapshot view of Dopemux execution state across subsystems.
It answers one question quickly:
“Where are we stable, and where are we changing?”
────────────────────────────────────────────────────────────
🧭 Status Legend
🟢 Stable — No active packets, invariants holding
🟡 In Progress — Active Task Packets exist
🔴 At Risk — Blocked, failing, or unresolved audit issues
────────────────────────────────────────────────────────────
🧠 Subsystem Status
Memory Stack
Status: 🟡 In Progress
Active Packets:
PACKET_031 — Dual Capture Adapters
PACKET_032 — Promotion Guards
Risk Notes:
Capture surface divergence under evaluation
Promotion determinism under audit
────────────────────
PM / Task Management Plane
Status: 🟡 In Progress
Active Packets:
PM-CONTINUE-05 — Transition Binding
PM-CONTINUE-06 — Project Context + Sprint Snapshot
PM-CONTINUE-07 — Knowledge + Technical Context
PM-CONTINUE-08 — Truth Rebaseline
Notes:
Canonical PM read/write entrypoints now exist under `src/dopemux/pm/`
Metadata writes route to Leantime; progress writes route to ConPort
Workflow reads and project-scoped transitions now route through Task Orchestrator runtime state
Project context routes through ConPort; sprint snapshot routes through Leantime; knowledge and technical reads now exist as normalized canonical-backend wrappers
Remaining risk: project-scoped workflow views still treat unscoped runtime tasks as in-scope, and the newer PM reads are backend-thin rather than richly multi-source
────────────────────
Workflow / Execution Control Plane
Status: 🟡 In Progress
Active Packets:
TP-SIA-EXEC-0001 — Packet Execution Domain Models + Lease Store
TP-SIA-EXEC-0002 — Packet Manifest V2 + Sidecar Contract
TP-SIA-EXEC-0003 — Explicit Routing Slots + Cost Policy
TP-SIA-EXEC-0004 — Supervisor Service + Canonical Commit Flow
TP-SIA-EXEC-0005 — Implementer Runner Adapter Contract
TP-SIA-EXEC-0006 — Auditor Runner + Proof Bundle Manifest
TP-SIA-EXEC-0007 — Manual Handoff + Operator Resume Semantics
TP-SIA-EXEC-0008 — Replay Repro Suite + Projection Hardening
Notes:
Execution architecture frozen in ADR; implementation sequence staged and ready
Critical risk remains queue-loss versus canonical truth until the series is executed
────────────────────
ADHD Support Plane
Status: 🟢 Stable
Active Packets:
None
Notes:
Architectural assumptions unchallenged
Requires fresh Phase 0 inventory
────────────────────
Search & Retrieval
Status: 🟡 In Progress
Active Packets:
None (design investigation only)
Notes:
Ranking determinism flagged for review
Embedding lifecycle not yet audited
────────────────────────────────────────────────────────────
⚠️ Cross-Cutting Risks
Multi-capture source convergence correctness
Test coverage skew across services
CI masking failures due to unrelated legacy errors
────────────────────────────────────────────────────────────
🧠 Update Rules
Update this file when:
Packet status changes
New risks emerge
A subsystem transitions between states
Keep this concise and factual
Avoid speculation
────────────────────────────────────────────────────────────
🧨 Final Rule
If a subsystem’s status is unclear, it is not stable.
