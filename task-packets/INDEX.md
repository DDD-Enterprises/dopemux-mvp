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
| TP-DMX-REPOHYG-004 | Repo Hygiene | Lost-work audit, stash preservation, and conservative cleanup | Ready | N/A |
| TP-DMX-REPOHYG-005 | Repo Hygiene | Remaining work disposition audit and cleanup-safe local pruning | Ready | N/A |
| TP-DMX-REPOHYG-006 | Repo Hygiene | Deep remaining work audit and recovery queue classification | Ready | N/A |
| TP-DMX-REPOHYG-007 | Repo Hygiene | Recover CLI/system audit hardening tranche from PR #554 | Ready | N/A |
| TP-DMX-RTEAUDIT-001 | Repo Truth Extractor | Assemble pre-live audit pack for GPT-5.4 Pro | Ready | N/A |
| TP-DMX-RTEINT-001 | Repo Truth Extractor | Integrate current RTE branch deltas into staging audit branch | Ready | N/A |
| TP-DMX-RTECANON-001 | Repo Truth Extractor | Establish `dopemux rte` as the canonical operator entrypoint | Ready | N/A |
| TP-DMX-AGENTS-CODEX-ENDTOEND-0001 | Agent Guidance | Make Codex execute TP lifecycle end-to-end by default | Ready | N/A |
| TP-DMX-COMPOSE-RESTORE-001 | Infra | Restore canonical Docker Compose authority | Ready | N/A |
| DMX-COCKPIT-STATIC-002 | UI Cockpit | Expose deterministic static cockpit renderer through guarded CLI wrapper | Merged (PR #528) | N/A |
| TP-DMX-COCKPIT-RUNTIME-RENDER-001 | UI Cockpit | Wire runtime renderer primitives to accepted Cockpit IA package contract | Active | N/A |
| TP-DMX-COCKPIT-SETTINGS-RUNTIME-001 | UI Cockpit | Wire Settings/Admin/Runtime primitive surface to runtime renderer | Active | N/A |
| TP-DMX-COCKPIT-UNKNOWN-DRIFT-001 | UI Cockpit | Wire Unknown / Drift Queue primitive surface to runtime renderer | Active | N/A |
| TP-DMX-COCKPIT-INVENTORY-REGEN-001 | UI Cockpit | Regenerate current-head Cockpit command/surface inventory artifacts | Active | N/A |
| TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001 | UI Cockpit | Repair Cockpit runtime contract-fidelity gaps | Active | N/A |
| TP-DMX-COCKPIT-DESIGN-PICKUP-001 | UI Cockpit | Create current-state Cockpit design pickup brief after pack-to-main consolidation | Active | N/A |
| PACKET_031 | Memory | Dual Capture Adapters, Single Ledger | Executing | ADR-213 |
| PACKET_032 | Memory | Chronicle Promotion Guards | Pending Audit | ADR-214 |
| DMX-COCKPIT-PMIMPL-PACK-001 | Cockpit / PM Plane | PM/Implementer cockpit processing pack | Ready | N/A |

────────────────────────────────────────────────────────────
🟢 Completed Task Packets

| Packet ID | Subsystem | Title | Completion Date | Outcome |
| --- | --- | --- | --- | --- |
| TP-DMX-RTEAUDIT-110 | Repo Truth Extractor | Gemini deep PAL audit across UX, prompts, routing, and operator readiness | 2026-04-23 | Accepted (Conditional Go) |
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
