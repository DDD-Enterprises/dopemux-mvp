# Development Factory Build Series

Ordered packet series. Each packet is a prerequisite for the next where indicated.

| Order | Packet ID | Purpose | Prerequisite |
|------:|-----------|---------|-------------|
| 1 | `TP-DMX-DDF-DOCS-001` | This docs packet — governance foundation | — |
| 2 | `TP-DMX-EVIDENCE-GATE-VERIFY-001` | Verify component evidence quality; re-verify key INFERRED items from runtime | `TP-DMX-DDF-DOCS-001` |
| 3 | `TP-DMX-MODEL-ROUTING-POLICY-001` | Formalize model routing policy as versioned YAML schema | `TP-DMX-DDF-DOCS-001` |
| 4 | `TP-RTE-S7-DRIFT-FIX-001` | Fix always-PASS S7 drift gate stub | `TP-DMX-DDF-DOCS-001` |
| 5 | `TP-RTE-SP-PHASE-CONTRACT-001` | Enforce phase-contract gating for SP pipeline | `TP-RTE-S7-DRIFT-FIX-001` |
| 6 | `TP-DMX-ORCH-NAMING-BOUNDARY-001` | Document Kotlin MCP vs Python FastAPI boundary | `TP-DMX-DDF-DOCS-001` |
| 7 | `TP-DMX-DOPETASK-SPEC-RESTORE-001` | Restore `dopetask-canonical-spec.json` at `docs/03-reference/spec/dopetask/` | `TP-DMX-DDF-DOCS-001` |
| 8 | `TP-DMX-OBLIGATION-LEDGER-001` | Formalize obligation ledger schema and initial population | `TP-DMX-DDF-DOCS-001` |
| 9 | `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001` | JSON schema for execution capsule + `EXECUTION_CAPSULE_TEMPLATE.md` | `TP-DMX-OBLIGATION-LEDGER-001` |
| 10 | `TP-DMX-DEVELOPMENT-FACTORY-CONTROLLER-DESIGN-001` | Architecture design for the Factory Controller service | `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001` |
| 11 | `TP-DMX-SERVICES-INVENTORY-001` | Audit all ~29 uninventoried `services/` directories | `TP-DMX-DDF-DOCS-001` |
| 12 | `TP-DMX-AGENT-AUTHORITY-001` | Declare canonical agent family, deprecate others | `TP-DMX-SERVICES-INVENTORY-001` |
| 13 | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` | Define LIVE_WRITE_READY contract schema | `TP-RTE-SP-PHASE-CONTRACT-001`, `TP-DMX-AGENT-AUTHORITY-001` |
| 14 | `TP-DMX-DCP-SEAM-ENFORCEMENT-001` | Add runtime enforcement to DCP-RED-MERGE-SEAM (currently docs-only) | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` |

## Rationale for Ordering

Docs first (this packet), then evidence verification, then the two critical RTE gate fixes, then authority resolution, then schema work, then controller design, then the live-write unblock chain.

**Why docs first:** The governance foundation (this packet) defines terminology, decision context, and the open-question surface that every subsequent packet depends on. Agents executing later packets must share a single authoritative vocabulary.

**Why evidence verification second:** Packets 3 through 14 rely on component-status claims derived from static analysis. Several of those claims are marked INFERRED. Verifying them from runtime before writing policy documents avoids laundering assumptions into schemas.

**Why model routing policy third (parallel-eligible with evidence verify):** Cheap models making architecture decisions is a known root cause of hallucinated authority. Formalizing the routing policy early prevents it from being violated during the rest of the series.

**Why the RTE gate fixes before authority and schema work:** The S7 drift stub (`TP-RTE-S7-DRIFT-FIX-001`) and SP phase-contract gate (`TP-RTE-SP-PHASE-CONTRACT-001`) are P0-class runtime defects. Fixing them before defining schemas ensures the schemas describe the corrected system, not the broken one.

**Why services inventory and agent authority before LIVE_WRITE_READY:** LIVE_WRITE_READY is meaningless until the set of agents that can declare it is known and verified. Agent authority cannot be declared until the services inventory is complete.

**Why the controller design after the capsule schema:** The Factory Controller's responsibilities depend on what execution capsules look like. Designing the controller before the schema would produce a design that cannot be implemented without rework.

**Why DCP-RED-MERGE-SEAM enforcement last:** Runtime enforcement of the seam requires that LIVE_WRITE_READY is defined, agent authority is resolved, and the capsule execution path is designed. All upstream dependencies must be settled before enforcement can be wired correctly.
