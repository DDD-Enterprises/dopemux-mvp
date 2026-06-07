---
id: build-series
title: Build Series
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Build Series (reference) for dopemux documentation and developer workflows.
---
# Development Factory Build Series

Ordered packet series. Each packet is a prerequisite for the next where indicated.

**Re-sequenced after `TP-DMX-EVIDENCE-GATE-VERIFY-001`** (HEAD `8042f9f9f`): the verification gate found that several "build-from-scratch" assumptions were stale — the RTE S7 gate, SP-contract enforcement, and DCP seam scanner all have implementation present at HEAD. The order below front-loads **verify-and-close** work over **build-from-scratch** work, and inserts a docs-correction trust-repair packet first.

**Completed:**
- ✅ `TP-DMX-DDF-DOCS-001` — governance foundation docs
- ✅ `TP-DMX-EVIDENCE-GATE-VERIFY-001` — read-only verification of the 12 evidence gates

| Order | Packet ID | Purpose | Prerequisite |
|------:|-----------|---------|-------------|
| 1 | `TP-DMX-DDF-DOCS-CORRECT-001` | This packet — correct stale DDF doc claims against verification findings | `TP-DMX-EVIDENCE-GATE-VERIFY-001` |
| 2 | `TP-RTE-S7-DRIFT-FIX-001` | **Verify-and-close:** run the S7 truth-split gate against injected drift, confirm FAIL (implementation present at HEAD — do not rebuild) | `TP-DMX-DDF-DOCS-CORRECT-001` |
| 3 | `TP-RTE-SP-PHASE-CONTRACT-001` | **Verify:** confirm `SP_CONTRACT_MISSING` blocks ungated SP (blocker present at HEAD — do not rebuild) | `TP-RTE-S7-DRIFT-FIX-001` |
| 4 | `TP-DMX-SERVICES-INVENTORY-001` | Build the real `services/` invocation graph; closes VG-003, VG-010, VG-011 | `TP-DMX-DDF-DOCS-CORRECT-001` |
| 5 | `TP-DMX-ORCH-NAMING-BOUNDARY-001` | Document Kotlin MCP vs Python FastAPI boundary (VG-002/VG-009 evidence ready) | `TP-DMX-DDF-DOCS-CORRECT-001` |
| 6 | `TP-DMX-DCP-SEAM-ENFORCEMENT-001` | Wire the existing `RedLaneScanner` into CI/steward (code present at HEAD, unwired — do not rebuild) | `TP-DMX-SERVICES-INVENTORY-001` |
| 7 | `TP-DMX-MODEL-ROUTING-POLICY-001` | Formalize model routing policy as versioned YAML schema | `TP-DMX-DDF-DOCS-CORRECT-001` |
| 8 | `TP-DMX-DOPETASK-SPEC-RESTORE-001` | **Verify canonical/freshness:** spec exists at `docs/03-reference/spec/dopetask/` and is valid (VG-001) — confirm it is authoritative and not outdated, do not restore | `TP-DMX-DDF-DOCS-CORRECT-001` |
| 9 | `TP-DMX-OBLIGATION-LEDGER-001` | Formalize obligation ledger schema and initial population | `TP-DMX-DDF-DOCS-CORRECT-001` |
| 10 | `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001` | JSON schema for execution capsule + `EXECUTION_CAPSULE_TEMPLATE.md` | `TP-DMX-OBLIGATION-LEDGER-001` |
| 11 | `TP-DMX-DEVELOPMENT-FACTORY-CONTROLLER-DESIGN-001` | Architecture design for the Factory Controller service | `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001` |
| 12 | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` | Define `LIVE_WRITE_READY` contract schema (true L4+ blocker, unchanged) | `TP-RTE-SP-PHASE-CONTRACT-001`, `TP-DMX-AGENT-AUTHORITY-001` |
| 13 | `TP-DMX-DCP-SEAM-LIFT-001` | Lift the DCP-RED-MERGE-SEAM — only after `LIVE_WRITE_READY` and seam enforcement are proven | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001`, `TP-DMX-DCP-SEAM-ENFORCEMENT-001` |

**`TP-DMX-AGENT-AUTHORITY-001` remains a required prerequisite** for `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` (VG-008 confirmed agent authority is unresolved — three families, near-zero tests, not imported by active code). It is scheduled as a follow-on to `TP-DMX-SERVICES-INVENTORY-001` (declare canonical agent family, deprecate others) and must complete before packet 12.

## Rationale for Ordering

Docs **correction** first (trust repair), then the RTE verify-and-close pair, then the services invocation graph and authority resolution, then schema/controller work, then the live-write unblock chain.

**Why docs correction first:** `TP-DMX-EVIDENCE-GATE-VERIFY-001` found materially stale claims in the foundation docs (monitoring-dashboard port 8098 not 1561; S7/SP/seam implementation present, not missing). Building automation on docs known to be wrong is the exact failure mode the evidence gate exists to prevent. The map is repaired before the next expedition.

**Why verify-and-close before build-from-scratch:** The S7 gate, SP-contract blocker, and DCP `RedLaneScanner` all have implementation present at HEAD `8042f9f9f`. Re-implementing them would duplicate working code and risk regression. The correct work is to *verify* the existing behavior (run S7 against injected drift; confirm `SP_CONTRACT_MISSING` blocks; confirm/wire the scanner) and close the obligation — not rebuild.

**Why services inventory and agent authority before LIVE_WRITE_READY:** `LIVE_WRITE_READY` is meaningless until the set of agents that can declare it is known and verified. Agent authority cannot be declared until the services invocation graph (VG-003) is complete.

**Why the controller design after the capsule schema:** The Factory Controller's responsibilities depend on what execution capsules look like. Designing the controller before the schema would produce a design that cannot be implemented without rework.

**Why the DCP-RED-MERGE-SEAM lift is last:** Lifting the seam requires that `LIVE_WRITE_READY` is defined and that seam enforcement (the `RedLaneScanner` wiring) is proven in CI/steward. `LIVE_WRITE_READY` remains the true L4+ blocker and is unaffected by the other corrections — all upstream dependencies must be settled before the seam can be lifted by an authorized operator.
