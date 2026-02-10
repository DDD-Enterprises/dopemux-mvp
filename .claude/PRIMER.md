# 🧭 Dopemux Development Primer

### Investigations · ADRs · Task Packets · Audits

════════════════════════════════════════════════════════════

## 🎯 Purpose

This PRIMER defines how Dopemux evolves when the answer is unclear, architecture may be wrong, or a subsystem needs redesign.

This document is procedural.
It is not a spec and not a roadmap.

Ground rules:

* Current implementation is the source of truth.
* Historical docs are idea sources, not ground truth.
* If it is not auditable, it does not exist.

────────────────────────────────────────────────────────────

## 🧩 When to Use This PRIMER

Use this PRIMER when:

* Starting a new subsystem push (PM plane, ADHD, search, bridge, memory)
* You suspect truth splits, drift, or hidden failure modes
* You need multi-model separation (Opus for semantics, Sonnet for implementation)
* You are producing ADRs or binding design deltas

Do not use this PRIMER for:

* Tiny bug fixes already fully scoped
* Mechanical lint cleanup covered by a Task Packet

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-NEGOTIABLES (PROCESS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. No fabrication

* If unknown, mark UNKNOWN and request evidence.

2. Evidence-first

* Every load-bearing claim must cite repo file paths and relevant identifiers (function name, section, or line range if available).

3. Spec before implementation

* Do not implement code until semantics and invariants are frozen.

4. Smallest irreversible unit

* Isolate and explicitly justify anything hard to undo.

5. Multi-model separation

* Deep semantics and truth-model decisions are not mixed with implementation.

6. Workflows are outputs

* Investigations may produce temporary workflows.
* Only ADRs and Task Packets canonize workflows.

────────────────────────────────────────────────────────────

## 🤖 Multi-Model Strategy (Roles, Not Brands)

Use roles and keep them separate:

A) Investigator / Architect (deep semantics)

* Defines truth models, invariants, contracts, risks
* Produces DESIGN_DELTA and ADR drafts
* Does not implement code

B) Implementer (mechanical change)

* Applies minimal diffs
* Adds tests proving invariants
* Runs exact commands and captures outputs verbatim

C) Auditor / Verifier

* Confirms evidence matches claims
* Checks acceptance criteria
* Updates risk register / decision log

Any handoff between roles must produce a binding handoff artifact.

────────────────────────────────────────────────────────────

## 🧭 Mandatory Phases (Run in Order)

════════════════════════════════════════════════════════════

## Phase 0 — Scope Lock

────────────────────────────────────────────────────────────
Outputs:

* Target subsystem
* Scope IN / OUT
* Success criteria
* Stop conditions
* Evidence plan (what to read/run first)

## Phase 1 — Inventory

────────────────────────────────────────────────────────────
Outputs:

* Component inventory
* Entry points
* Data stores
* External dependencies
* Surfaces (CLI, MCP, hooks, APIs)
* What is active vs dead vs aspirational

## Phase 2 — Failure & Drift Audit

────────────────────────────────────────────────────────────
Outputs:

* Determinism leaks
* Truth splits
* Provenance breaks
* Trust boundary violations
* Operational failure modes
  Label each finding:
* Observed (proven)
* Inferred (plausible, needs proof)
* Unknown (missing evidence)

## Phase 3 — Design Delta

────────────────────────────────────────────────────────────
Outputs:

* What must change
* What must not change
* Invariants to enforce
* Why current architecture fails (with evidence)
* Constraints imposed by current code

## Phase 4 — ADR Synthesis

────────────────────────────────────────────────────────────
Outputs:

* ADRs that freeze decisions
* Alternatives considered
* Consequences
* Migration strategy

## Phase 5 — Task Packets

────────────────────────────────────────────────────────────
Outputs:

* One or more task packets per ADR
* Minimal diffs, exact commands, tests, acceptance, rollback, stop conditions

## Phase 6 — Handoff Artifact

────────────────────────────────────────────────────────────
Outputs:

* Frozen invariants
* What may change vs must not change
* Evidence summary and test results
* Known unresolved issues
* Next recommended packet ordering

────────────────────────────────────────────────────────────

## 🧷 Binding Artifact Names (Recommended)

* reports/DESIGN_DELTA_<subsystem>_<date>.md
* docs/adr/ADR-XXXX-<short-title>.md
* reports/HANDOFF_<packetA>*to*<packetB>.md
* reports/PACKET_<id>*<subsystem>*<date>.md

────────────────────────────────────────────────────────────

## 🛑 Stop Conditions

If you cannot proceed due to missing evidence:

* Halt
* Request specific file paths or exact command outputs
* Do not guess

────────────────────────────────────────────────────────────

## 🧨 Final Rule

Work that cannot be reproduced is incomplete.