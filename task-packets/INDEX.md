---
id: INDEX
title: Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-03-22'
next_review: '2026-06-20'
prelude: Index (explanation) for dopemux documentation and developer workflows.
---
📑 Dopemux Task Packet Index
Canonical Registry · Execution History · Change Traceability
════════════════════════════════════════════════════════════
🎯 Purpose
This index is the authoritative registry of all Task Packets in Dopemux.
It exists to provide:
Traceability from design → execution
Visibility into active and completed work
A deterministic audit trail of system evolution
If a change cannot be traced to a Task Packet listed here, it is considered out of process.
────────────────────────────────────────────────────────────
🧭 How to Use This Index
Active packets indicate work in progress
Completed packets represent executed and audited changes
Superseded packets are preserved for history but must not be reused
This file should be updated whenever:
A new Task Packet is created
A packet changes status
A packet is superseded by another packet
────────────────────────────────────────────────────────────
🟡 Active Task Packets

| Packet ID | Subsystem | Title | Status | Related ADR |
| --- | --- | --- | --- | --- |
| TP-SIA-EXEC-0001 | Workflow Plane | Packet Execution Domain Models + Lease Store | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0002 | Workflow Plane | Packet Manifest V2 + Sidecar Contract | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0003 | Workflow Plane | Explicit Routing Slots + Cost Policy | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0004 | Workflow Plane | Supervisor Service + Canonical Commit Flow | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0005 | Workflow Plane | Implementer Runner Adapter Contract | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0006 | Workflow Plane | Auditor Runner + Proof Bundle Manifest | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0007 | Workflow Plane | Manual Handoff + Operator Resume Semantics | Ready | SIA Packet Execution ADR |
| TP-SIA-EXEC-0008 | Workflow Plane | Replay Repro Suite + Projection Hardening | Ready | SIA Packet Execution ADR |
| TP-DMX-AIG-001 | Adaptive Ingress Plane | Service Census + Ingress Map + First Safe Slice | Ready | ADR — Adopt a Dopemux Adaptive Ingress Plane with Local Runtime Shims |
| TP-DMX-REPOHYG-001 | Repo Hygiene | Branch and worktree audit with deterministic cleanup plan | Ready | N/A |
| TP-DMX-REPOHYG-002 | Repo Hygiene | Execute phase2 safe archive cleanup | Ready | N/A |
| TP-DMX-REPOHYG-003 | Repo Hygiene | Resolve blocked and ambiguous cleanup survivors | Ready | N/A |
| TP-DMX-RTEAUDIT-001 | Repo Truth Extractor | Assemble pre-live audit pack for GPT-5.4 Pro | Ready | N/A |
| PACKET_031 | Memory | Dual Capture Adapters, Single Ledger | Executing | ADR-213 |
| PACKET_032 | Memory | Chronicle Promotion Guards | Pending Audit | ADR-214 |

────────────────────────────────────────────────────────────
🟢 Completed Task Packets

| Packet ID | Subsystem | Title | Completion Date | Outcome |
| --- | --- | --- | --- | --- |
| TP-PM-ARCH-04A | PM Plane | Canonical PMTask Model + Store (Unit-only) | 2026-03-22 | Accepted |
| TP- PM-ARCH-04B | PM Plane | Canonical pm.* Events + Adapters | 2026-03-22 | Accepted |
| PACKET_024 | Infra | MCP Health Surface Hardening | 2026-01-26 | Accepted |
| PACKET_021 | Memory | Deterministic Chronicle Schema | 2026-01-18 | Accepted |

────────────────────────────────────────────────────────────
⚪ Superseded Task Packets

| Packet ID | Superseded By | Reason |
| --- | --- | --- |
| PACKET_017 | PACKET_021 | Incomplete determinism guarantees |

────────────────────────────────────────────────────────────
🧠 Index Maintenance Rules
Never delete historical packets
Never reuse packet IDs
Status changes must be explicit
Completed packets require an audit outcome
Superseded packets must reference the replacing packet
────────────────────────────────────────────────────────────
Final Rule
If it’s not indexed here, it didn’t happen.
