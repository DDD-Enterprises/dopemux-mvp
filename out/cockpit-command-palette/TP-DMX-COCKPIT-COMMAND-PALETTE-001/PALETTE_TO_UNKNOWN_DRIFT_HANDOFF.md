# Palette → Unknown / Drift Queue Handoff

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines how the Command Palette routes unknown, blocked, drifted, and stale-proof rows into the Unknown / Drift Queue (`UNKNOWN_DRIFT_QUEUE_SPEC.md`). The queue is non-executable. The palette never reclassifies a row in this handoff; reclassification requires a packet.

## 1. Triggers For This Handoff

The palette routes a row to the Unknown/Drift Queue when **any** of the following triggers are present (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §1):

| Trigger | Source signal |
| --- | --- |
| Unknown class | `safe_ui_exposure == UNKNOWN` |
| Defined-but-not-registered | `activation_status == DEFINED_NOT_REGISTERED` |
| Optional import unknown | `activation_status == OPTIONAL_IMPORT_UNKNOWN` |
| Deprecated blocked | `activation_status == DEPRECATED_BLOCKED` (also routes to `ShowBlockedReason`; queue tracks the row) |
| Conflicting authority | `authority_domain == 'unknown / conflicting'` |
| Blocked in Cockpit | `safe_ui_exposure == BLOCKED_IN_COCKPIT` (visible in queue and as blocked row) |
| Missing coverage with another unknown axis | `current_cockpit_coverage == MISSING` and any other field unknown |
| Unknown coverage with another unknown axis | `current_cockpit_coverage == UNKNOWN` and any other field unknown |
| Stale proof | runtime detection of expired/missing post-action proof |
| Drifted classification | row classification disagrees with current authority docs |
| Required parameter unresolved | `parameter_schema.required_parameters` contains `UNKNOWN` |
| Routing decision denied | `allowed_palette_outcomes` empty after rules in `PALETTE_ROUTING_RULES.md` §7 |

## 2. Handoff Payload (Required Fields)

The palette delivers the following payload. Every field is required; missing values render as `UNKNOWN` per `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4.

| Field | Source | Notes |
| --- | --- | --- |
| `trigger_reason` | one of the categories in §1 | The primary reason the row entered the queue. |
| `command_path` | `command_path` (or `UNKNOWN`) | Verbatim. |
| `parent_group` | `parent_group` | Verbatim. |
| `authority_domain` | `authority_domain` (may be `unknown / conflicting` or `UNKNOWN`) | Verbatim. |
| `canonical_writer` | `canonical_writer` (may be `UNKNOWN`) | Verbatim. |
| `safe_ui_exposure` | `safe_ui_exposure` | Verbatim, including `UNKNOWN` and `BLOCKED_IN_COCKPIT`. |
| `cockpit_placement` | `cockpit_placement` | Verbatim. |
| `current_cockpit_coverage` | `current_cockpit_coverage` | Verbatim. |
| `activation_status` | `activation_status` | Verbatim. |
| `source_file_symbol` | `source_file:source_symbol` | Always preserved when available; required for defined-but-not-registered rows. |
| `block_reason` | `blocked_reason` (may be `NOT_APPLICABLE`) | Required for `BLOCKED_IN_COCKPIT` and `DEPRECATED_BLOCKED` rows. |
| `unknown_reason` | `unknown_reason` | Required when row is in any unknown state. |
| `last_seen_activation_status` | `activation_status` | Reproduced for queue display. |
| `required_investigation_packet` | derived (e.g. `OPUS_REMEDIATION_PLAN.md` §1 sequencing) | When known; otherwise `INVESTIGATION_PACKET_REQUIRED`. |
| `last_evidence_timestamp` | from carried evidence stream | When available; otherwise `UNKNOWN`. |
| `last_proof_reference` | from carried evidence stream | When available; otherwise `UNKNOWN`. |
| `palette_request_id` | UUID generated at handoff | Correlation id for evidence/audit logs. |
| `palette_index_row_hash` | SHA-256 of normalized row | Drift detection. |

## 3. Queue Behavior After Handoff

The Unknown/Drift Queue:

- Renders the row using the per-row fields enumerated in `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4.
- Provides **no** execution affordance under any condition (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3).
- Provides no copy-as-run shortcut that bypasses Palette + Safe Action Gate.
- Does not silently reclassify the row.
- Does not promote the row out of the queue without a packet artifact reference (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5).

## 4. Reclassification Refusal

The palette refuses any operator action that would reclassify the row inside this handoff. Reclassification requires:

| Promotion category | Required evidence |
| --- | --- |
| Unknown → known | Authority owner identified; classification assigned; placement assigned; gate tier determined; via packet. |
| Defined-but-not-registered → registered | Runtime registration repaired or row rejected; updated inventory; activation flipped. |
| Conflicting authority → resolved | ConPort decision linking to system-docs change; updated authority_domain. |
| Missing coverage → covered | Screen contract added; placement updated; gate tier set. |
| Blocked → external-only / display | Replacement command (if any); external workflow documented; reclassification through packet. |
| Stale proof → fresh | Re-execute the gated action and capture proof, or mark `EXTERNAL_ONLY` if proof cannot be captured. |

The palette must include the `required_investigation_packet` reference where known so the operator has a clear next action.

## 5. Reachability From The Queue Back To The Palette

- The queue's rows are searchable from the palette via filter axes (`PALETTE_ROUTING_RULES.md` §3 placement; `COMMAND_PALETTE_SPEC.md` §2 axes).
- The palette filter syntax `status:UNKNOWN`, `status:BLOCKED`, `coverage:MISSING`, `proof:STALE` returns rows that are currently in the queue.
- Selecting a queued row from the palette re-displays the same blocked/unknown state per `PALETTE_BLOCKED_UNKNOWN_STATES.md`.

## 6. Audit / Event Receipt

The palette records a queue-route receipt to the evidence stream:

- `palette_request_id`
- `palette_index_row_hash`
- timestamp (UTC)
- `trigger_reason`
- `command_path` (or `UNKNOWN`)
- `authority_domain`
- `safe_ui_exposure`
- `activation_status`
- `current_cockpit_coverage`

The receipt is captured even when the operator simply previews a queued row; the palette never silently drops a queue route.

## 7. Forbidden In This Handoff

- Reclassifying the row inside the queue.
- Promoting the row out of the queue without a packet reference.
- Permitting an execution affordance.
- Permitting a copy-as-run shortcut that bypasses Palette + Safe Action Gate.
- Suppressing `BLOCKED_IN_COCKPIT` rows from the queue.
- Hiding `unknown_reason` or `block_reason` text.
- Auto-retrying a stale-proof action.

## 8. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/OPUS_REMEDIATION_PLAN.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_BLOCKED_UNKNOWN_STATES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
