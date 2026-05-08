# Command Palette Contract

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)
**Upstream packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**ia_verdict:** CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION
**safe_for_claude_design:** NO
**READY_FOR_CLAUDE_DESIGN:** not approved

This document defines the canonical contract for the Cockpit Command Palette. It is normative for the downstream Cockpit shell remediation packets (`TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA`, `TP-DMX-COCKPIT-RUNTIME-RENDER-001`). It produces no runtime code, no Cockpit package edits, no final screens, and no Claude Design uploads.

## 1. Role Statement

The Command Palette is a **global broker, not an executor**. It is the only canonical home for the 139 inventory rows whose carried placement is `Command Palette` (`COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Command Palette = 139`) and the discovery surface for any other row the operator addresses by command path or by intent rather than by the row's mode home.

The palette **discovers, classifies, previews, and routes**. It does not execute. It does not own any authority slice. It is reachable by global hotkey from every primary mode and from every secondary surface.

## 2. The Palette Is Not A Sixth Top-Level Authority Mode

The reconciled IA has exactly five top-level modes: PM, Implementer, Overview, Services, Events (`REVISED_COCKPIT_IA.md` §2). The Command Palette is one of four added secondary surfaces (`REVISED_COCKPIT_IA.md` §3) and:

- Does not appear in the primary mode bar.
- Does not appear as a top-level entry in mode navigation.
- Does not own state, truth, decisions, or PM workflow.
- Does not subsume PM, Implementer, Overview, Services, or Events.
- Does not replace Settings/Admin/Runtime, the Safe Action Gate, or the Unknown/Drift Queue.
- Does not invent new authority. Every palette row is owned by the authority domain the inventory assigns it.

## 3. Capabilities (Allowed)

The palette must support all of the following simultaneously. These capabilities exist together; they cannot be disabled or short-circuited.

| Capability | Definition |
| --- | --- |
| Discovery | Surface command rows by path, parent group, intent, or filter axis (see §6). |
| Filtering | Filter by command path, authority domain, safety class, placement, canonical writer, proof requirement, source provenance, activation status. |
| Classification display | Render every row with its authority owner, safety class, placement badge, proof requirement, activation status. Missing fields render `UNKNOWN`, never blank. |
| Parameter preview | Display fully resolved invocation, including required and optional parameters (defaults made explicit), `cwd`/worktree target, output target, side-effect summary, expected proof, before any handoff. |
| Routing | Route the row to exactly one downstream surface (Inspect drawer, Safe Action Gate, Settings/Admin/Runtime, Unknown/Drift Queue, or external copy-command flow) per `PALETTE_ROUTING_RULES.md`. |
| Provenance preservation | Carry `source_file`, `source_symbol`, `evidence_path_or_command`, `authority_domain`, `canonical_writer`, `proof_requirement` end-to-end. |
| Fail-closed behavior | When any required field is unresolved, refuse to invoke the gate. Route to Unknown/Drift Queue with reason. |

## 4. Forbidden Behaviors (Hard No)

The palette **must never** do any of the following. Each forbidden item maps to evidence in upstream artifacts.

| Forbidden | Source rule |
| --- | --- |
| Execute any command itself. | `COMMAND_PALETTE_SPEC.md` §1; the palette is a broker. |
| Silently route around the Safe Action Gate. | `COMMAND_PALETTE_SPEC.md` §1; `SAFE_ACTION_GATE_SPEC.md` §1. |
| Auto-confirm a `CONFIRM_REQUIRED` row. | `COMMAND_EXPOSURE_POLICY.json:classes.CONFIRM_REQUIRED.forbidden_ui_form` (no auto-run on selection). |
| Run a `BLOCKED_IN_COCKPIT` row through any path. | `COMMAND_EXPOSURE_POLICY.json:classes.BLOCKED_IN_COCKPIT.forbidden_ui_form`. |
| Promote an `UNKNOWN` row into execution. | `COMMAND_EXPOSURE_POLICY.json:classes.UNKNOWN.forbidden_ui_form`; `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3. |
| Hide authority owner, safety class, or required gate state from the operator. | `COMMAND_PALETTE_SPEC.md` §1. |
| Default destructive parameters or apply implicit defaults that change side effects. | `COMMAND_PALETTE_SPEC.md` §4 and §6. |
| Place `COMMAND_PALETTE_ONLY` rows on a mode home screen via the palette. | `COMMAND_EXPOSURE_POLICY.json:classes.COMMAND_PALETTE_ONLY.forbidden_ui_form`. |
| Add a direct destructive button to any row. | `SAFE_ACTION_GATE_SPEC.md` §5. |
| Reclassify an `UNKNOWN` row inside the palette. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5; reclassification requires a packet. |
| Hidden retries, background reroutes, or success chips before result exists. | `COMMAND_PALETTE_SPEC.md` §6; `COMMAND_EXPOSURE_POLICY.json:classes.INSPECT_ACTION.forbidden_ui_form`. |
| Collapse multiple authority domains into a single control brain. | `REVISED_COCKPIT_IA.md` §5; authority boundaries are preserved per row. |

## 5. Invariants The Palette Must Preserve

Every palette row carries the following invariants from index to gate handoff. Loss of any invariant is a fail-closed condition and routes the row to the Unknown/Drift Queue.

- **Authority domain.** From `authority_domain` in the inventory; one of the ten values enumerated in `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.authority_domain`.
- **Canonical writer.** Derived from authority domain + system docs; if multiple writers exist, all writers must be listed (`SAFE_ACTION_GATE_SPEC.md` §2).
- **Source provenance.** `source_file`, `source_symbol`, `evidence_path_or_command` carried verbatim.
- **Safety class.** One of `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED`, `COMMAND_PALETTE_ONLY`, `BLOCKED_IN_COCKPIT`, `EXTERNAL_ONLY`, `UNKNOWN`.
- **Proof requirement.** Derived from class + governance gate; tier mapping per `SAFE_ACTION_GATE_SPEC.md` §1.
- **Cockpit placement.** From `likely_cockpit_placement`; one of PM, Implementer, Overview, Services, Events, Command Palette, Settings/Admin, External/Not Cockpit, UNKNOWN.
- **Activation status.** From `activation_status`; one of `ACTIVE`, `DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`, `DEPRECATED_BLOCKED`.
- **Coverage status.** From `current_Cockpit_coverage`; one of `PARTIAL`, `MISSING`, `UNKNOWN`, `OUT_OF_SCOPE`.

## 6. Search Axes

Every search axis must work simultaneously and independently. The palette must surface which axis matched so the operator does not get a false-positive hit (`COMMAND_PALETTE_SPEC.md` §2).

| Axis | Field source | Example query |
| --- | --- | --- |
| Command path | `command_path`, `parent_group`, `source_symbol` | `dopetask doctor` |
| Authority domain | `authority_domain` | `authority:dopetask execution handoff` |
| Safety class | `safe_UI_exposure` | `class:CONFIRM_REQUIRED` |
| Cockpit placement | `likely_cockpit_placement` | `place:Settings/Admin` |
| Canonical writer | derived | `writer:ConPort` |
| Proof requirement | derived | `proof:required` |
| Source provenance | `source_file`, `source_symbol`, `evidence_path_or_command` | `source:routing_cli.py` |
| Activation status | `activation_status` | `status:DEFINED_NOT_REGISTERED` |
| Coverage status | `current_Cockpit_coverage` | `coverage:MISSING` |

## 7. Allowed Outcomes

A palette result must resolve into exactly one of these outcomes. The palette must never collapse multiple outcomes into a single click. Routing is governed by `PALETTE_ROUTING_RULES.md`.

| Outcome | When | Effect |
| --- | --- | --- |
| Inspect | `DISPLAY_ONLY`, `INSPECT_ACTION`. | Open inspector with command path, authority owner, last result, evidence path; no mutation. |
| Copy command | Operator opts to run externally; `EXTERNAL_ONLY`. | Copy fully resolved invocation to clipboard; log clipboard event in evidence stream. |
| Open Safe Action Gate | `CONFIRM_REQUIRED`; class-specific gate (T1–T6). | Hand the resolved command to the Safe Action Gate; never execute. |
| Open Settings/Admin/Runtime | Admin/runtime row (routing/profile/env/MCP/service-startup/hooks/runtime/admin/debug). | Navigate to the Settings surface; the gate is invoked from there. |
| Show blocked reason | `BLOCKED_IN_COCKPIT`. | Show block class, reason, replacement command (if any), required external workflow; no execute affordance. |
| Show unknown / drift reason | `UNKNOWN`, `OPTIONAL_IMPORT_UNKNOWN`, `DEFINED_NOT_REGISTERED`, conflicting authority, missing coverage, stale proof. | Show why the row is unknown; route to Unknown/Drift Queue. |

## 8. Authority Boundaries Preserved

The palette does not move authority. The boundaries documented in `REVISED_COCKPIT_IA.md` §5 remain canonical:

- **Dopemux** — Operator control, CLI coordination, shell/runtime framing.
- **Dopetask** — Execution handoff runtime; only via explicit handoff and proof gates.
- **Task-orchestrator** — Workflow coordination and workflow-significant transitions.
- **ConPort** — Structured decision/progress/context/custom-data slices.
- **Dope-memory** — Chronicle and historical receipt authority only.
- **Dope-context** — Code/docs retrieval/indexing only.
- **Dopecon-bridge** — Adapter/proxy/event transport only.
- **ADHD Engine** — Advisory operator-support / cognitive-state surface only.
- **Repo Truth Extractor** — Audit/extraction runtime and evidence artifact generator only.
- **Routing/model-provider support** — LiteLLM/CCR routing only.

The palette displays each row's owner. It never substitutes its own ownership.

## 9. What This Contract Does Not Approve

- No final palette screens. Primitive-level only.
- No runtime code edits.
- No Cockpit package HTML/CSS/React edits.
- No ZIP edits.
- No Claude Design uploads.
- No execution capability inside the palette.
- No reclassification of `UNKNOWN` rows.
- No promotion of `BLOCKED_IN_COCKPIT` rows to executable.
- No staging, commits, pushes, or PRs.

## 10. Source Artifacts (Authoritative Inputs)

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/REVISED_COCKPIT_IA.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_MAPPING_DECISIONS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UPDATED_COVERAGE_DECISION.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/OPUS_REMEDIATION_PLAN.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/PROOF.json`
