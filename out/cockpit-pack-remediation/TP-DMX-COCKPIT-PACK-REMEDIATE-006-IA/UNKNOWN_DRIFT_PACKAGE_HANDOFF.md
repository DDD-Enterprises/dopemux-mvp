# Unknown / Drift Queue Package Handoff

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This file specifies the package-level handoff for the Unknown / Drift Queue. The queue is a **non-executable** visibility surface. The Palette routes UNKNOWN/MISSING/BLOCKED-visibility/STALE-PROOF rows here; the Safe Action Gate routes refused/incomplete-proof/stale-proof actions here. The queue **never** executes anything and **never** reclassifies a row in place.

## 1. Surface Role Recap

- Non-executable visibility queue (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §3).
- Tracks the gap between the inventory and the IA without giving the operator an execution affordance.
- Reachable from Overview drift summary, Palette filters (`status:UNKNOWN`, `status:BLOCKED`, `coverage:MISSING`, `proof:STALE`), and Settings/Admin/Runtime as a read-only drift inspector (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §6).

## 2. Triggers For Routing Into The Queue

Triggers are unified across the Palette-side handoff (`PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1) and the Gate-side handoff (`SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1). The queue must accept all of these:

| Source | Triggers |
| --- | --- |
| Palette index validation | Failed `RV-1 .. RV-11` from `COMMAND_PALETTE_INDEX_SCHEMA.json`. |
| Activation | `DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`. |
| Authority | `unknown / conflicting`, `canonical_writer == UNKNOWN`. |
| Class | `UNKNOWN` (the class itself); `BLOCKED_IN_COCKPIT` (visibility-only — also routed to `ShowBlockedReason`). |
| Coverage | `MISSING` or `UNKNOWN` combined with another unknown axis. |
| Parameters | `parameter_schema.required_parameters` contains `UNKNOWN` (`PARAM_UNRESOLVED`). |
| Routing denial | `allowed_palette_outcomes` empty after `PALETTE_ROUTING_RULES.md` §7 (`OUTCOME_DENIED`). |
| Gate refusal (any) | All triggers in `SAFE_ACTION_REFUSAL_RULES.md` §2 (except `BLOCKED_IN_COCKPIT`/`DEPRECATED_BLOCKED` which route to `ShowBlockedReason`). |
| Stale proof | `STALE_PROOF_GATE` from runtime detection. |
| Drifted classification | `AUTHORITY_DRIFT_MID_FLOW`, `CLASS_DRIFT_MID_FLOW`, `INDEX_DRIFT`. |
| Stale handoff | `STALE_HANDOFF` (older than configured stale window). |
| Unsafe origin | `UNSAFE_SOURCE_SURFACE` (deep-link, URL parameter, keyboard shortcut bypassing surface). |

## 3. Counts From Carried Inventory (Lower Bound)

The minimum number of inventory rows that will appear in the queue is bounded by:

- `coverage.MISSING = 284`
- `coverage.UNKNOWN = 32`
- `safe_ui_exposure.UNKNOWN = 5`
- `safe_ui_exposure.BLOCKED_IN_COCKPIT = 48` (visibility only)
- `activation_status.DEFINED_NOT_REGISTERED = 30`
- `activation_status.OPTIONAL_IMPORT_UNKNOWN = 2`
- `activation_status.DEPRECATED_BLOCKED = 7`
- `authority_domain.unknown / conflicting = 14`

(Source: `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1; `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`.)

## 4. Per-Row Required Fields

Every queued row must show (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §4; `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §2; `SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md` §2):

- `trigger_reason`.
- `command_path` (or `UNKNOWN`) or `source_file:source_symbol` for defined-but-not-registered rows.
- `authority_domain` (or `unknown / conflicting`).
- `canonical_writer` (or `UNKNOWN`).
- `safety_class` (verbatim, including `BLOCKED_IN_COCKPIT` / `UNKNOWN`).
- `cockpit_placement` (verbatim).
- `current_cockpit_coverage` (verbatim).
- `activation_status` (verbatim).
- `gate_tier` (verbatim).
- `block_reason` (when applicable; `NOT_APPLICABLE` for non-blocked rows).
- `unknown_reason` (free-text human reason).
- `last_seen_activation_status`.
- `required_investigation_packet` (or `INVESTIGATION_PACKET_REQUIRED` if not yet known).
- `last_evidence_timestamp` (or `UNKNOWN`).
- `last_proof_reference` (or `UNKNOWN`).
- `palette_request_id` and/or `gate_request_id` (correlation).
- `palette_index_row_hash` and/or `action_row_hash` (drift detection).

Missing fields render as `UNKNOWN`, never blank.

## 5. Promotion / Demotion Rules

Rows leave the queue only via packet evidence (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5; `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §4). The queue itself is **not** an admin tool.

| Promotion category | Required evidence |
| --- | --- |
| Unknown → known | Authority owner identified; classification assigned; placement assigned; gate tier determined; via packet. |
| Defined-but-not-registered → registered | Runtime registration repaired or row explicitly rejected; updated inventory; activation status flipped. |
| Conflicting authority → resolved | ConPort decision linking to system-docs change; updated `authority_domain`. |
| Missing coverage → covered | Screen contract added (`SCREEN_CONTRACT_MATRIX.md`); placement field updated; gate tier set. |
| Blocked → external-only / display | Replacement command (if any); external workflow documented; reclassification through packet. |
| Stale proof → fresh | Re-execute the gated action and capture proof; or mark `EXTERNAL_ONLY` if proof cannot be captured. |

The queue surfaces the `required_investigation_packet` reference where known, so the operator has a clear next action.

## 6. UI Primitive Requirements (Package-Level)

The queue must, at the primitive level (no final visuals approved here), render:

- A row list primitive listing queued rows with the per-row fields in §4.
- A filter primitive supporting `status:UNKNOWN`, `status:BLOCKED`, `coverage:MISSING`, `proof:STALE` (matching Palette filters).
- A `Blocked state` primitive (deferred to `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §2.12) for rows whose `safety_class == BLOCKED_IN_COCKPIT` or `activation_status == DEPRECATED_BLOCKED`.
- An `Unknown state` primitive (deferred to `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §2.13) for rows whose state is `UNKNOWN`.
- A `Stale-proof state` primitive (deferred to `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §2.11) for rows tagged `STALE_PROOF`.
- A read-only investigation packet link primitive when `required_investigation_packet` is known.

These primitives are inputs to the Cockpit package remediation and the runtime renderer. **No final screens are approved here.**

## 7. Forbidden In This Surface (Carried From Upstream)

- **No execution from the queue under any condition** (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3).
- No copy-as-run shortcut that bypasses Palette + Safe Action Gate.
- No silent reclassification inside the queue.
- No "promote" affordance that changes the row's class without packet approval.
- No automatic retry of stale-proof actions.
- No suppression of `BLOCKED_IN_COCKPIT` rows; they remain visible as blocked.
- No final screens.

## 8. Audit / Event Receipts

Two receipt streams converge in the queue:

- **Palette routing receipt** per `PALETTE_PROOF_REQUIREMENTS.md` §3 with `selected_outcome: ShowUnknownDriftReason` and `handoff_outcome: refused|rerouted|unknown`.
- **Gate refusal/stale-proof event** per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` (`gate_refuse`, `gate_proof_incomplete`, `gate_proof_stale`).

Both reference `palette_request_id` and (for gate events) `gate_request_id` for end-to-end correlation. Receipts are append-only, UTC-timestamped, and never silently dropped.

## 9. Recommended Downstream Packet

`TP-DMX-COCKPIT-UNKNOWN-DRIFT-001` wires the Unknown/Drift Queue surface, finalizes the row-list / filter / detail primitives, and connects the surface to the evidence stream. Promotions/demotions remain owned by their respective reclassification packets (per category in §5). This packet does not authorize the runtime wiring; it documents the contract.

## 10. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/OPUS_REMEDIATION_PLAN.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_BLOCKED_UNKNOWN_STATES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
