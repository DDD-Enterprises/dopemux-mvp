# Safe Action Gate → Unknown / Drift Queue Handoff

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines how the Safe Action Gate routes failed, refused, and stale-proof actions into the Unknown / Drift Queue (`UNKNOWN_DRIFT_QUEUE_SPEC.md`). The queue is non-executable. The gate never reclassifies a row in this handoff; reclassification requires a packet (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5).

This handoff is the gate-side counterpart to `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`. The two handoffs share schema and intent; the gate-side handoff fires when refusal happens at the gate (after the upstream surface has already passed handoff validation).

## 1. Triggers For This Handoff

The gate routes a row to the Unknown/Drift Queue when **any** of the following are true. (Triggers are a superset of the upstream-surface refusal triggers because the gate enforces additional invariants such as typed confirmation and stale-proof detection.)

| Trigger | Source signal | Reason code |
| --- | --- | --- |
| Required preflight field UNKNOWN | Any field in `SAFE_ACTION_PREFLIGHT_SCHEMA.json` resolves to `UNKNOWN` for the assigned tier | enumerated reason from `SAFE_ACTION_REFUSAL_RULES.md` §2 (e.g., `COMMAND_UNRESOLVED`, `PARAM_UNRESOLVED`, `CWD_UNRESOLVED`, `AUTHORITY_UNKNOWN`, `WRITER_UNKNOWN`) |
| Authority conflict | `authority_domain == 'unknown / conflicting'` | `AUTHORITY_CONFLICT` |
| Unknown class | `safety_class == UNKNOWN` | `UNKNOWN_CLASS` |
| Activation non-ACTIVE | `activation_status` in {`DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`} | `NOT_ACTIVE` |
| Side effects unknown / empty for executable tier | `side_effects` UNKNOWN or empty for T1–T6 | `SIDE_EFFECTS_UNKNOWN` / `SIDE_EFFECTS_EMPTY` |
| Expected proof unknown for executable tier | `expected_proof == UNKNOWN` for T1–T6 | `PROOF_REQUIREMENT_UNKNOWN` |
| Rollback unknown for destructive tier | `rollback_or_abort == UNKNOWN` for T3 destructive, T4, T5, T6 | `ROLLBACK_UNKNOWN` |
| Remote-mutation policy missing/not approved (T4) | `remote_mutation_policy_reference` missing or not approved | `REMOTE_MUTATION_POLICY_MISSING` / `REMOTE_MUTATION_POLICY_NOT_APPROVED` |
| Service id / TP id / runner id unknown | tier-specific identifier UNKNOWN | `SERVICE_ID_UNKNOWN` / `TP_ID_UNKNOWN` / `RUNNER_ID_UNKNOWN` |
| TP gate absent (T6) | `tp_gate_present == false` | `TP_GATE_ABSENT` |
| Typed confirmation mismatch (T4/T5/T6) — operator-abandoned | typed value never matches and operator abandons | `TYPED_CONFIRMATION_MISMATCH` (after timeout) |
| Index drift | `palette_index_row_hash` mismatch with current index | `INDEX_DRIFT` (also routes back to upstream surface for re-render; the queue records the drift event) |
| Stale handoff timestamp | `created_at_utc` older than configured stale window | `STALE_HANDOFF` |
| Stale proof on previously gated action | runtime detects expired/missing post-action proof | `STALE_PROOF_GATE` |
| Authority drift mid-flow | authority resolution lost after preflight rendered | `AUTHORITY_DRIFT_MID_FLOW` |
| Class drift mid-flow | gate observes class change between handoff and confirm | `CLASS_DRIFT_MID_FLOW` |
| Surface origin unsafe | deep-link, URL parameter, keyboard shortcut bypassing surface | `UNSAFE_SOURCE_SURFACE` |

`BLOCKED_IN_COCKPIT` and `DEPRECATED_BLOCKED` rows are **not** routed to the Unknown/Drift Queue by the gate; they are routed to `ShowBlockedReason` at the originating surface (per `SAFE_ACTION_REFUSAL_RULES.md` §1). The Unknown/Drift Queue still tracks blocked rows via the upstream Palette handoff (`PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1) for visibility.

## 2. Handoff Payload (Required Fields)

The gate delivers the following payload to the Unknown/Drift Queue. Every field is required; missing values render as `UNKNOWN` per `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4. Schema parallels `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §2.

| Field | Source | Notes |
| --- | --- | --- |
| `trigger_reason` | One of the reason codes in §1 | Primary reason the gate routed to the queue. |
| `gate_request_id` | UUID generated at gate_open | Correlation id (gate-side). |
| `palette_request_id` | from upstream payload (or null) | Correlation with upstream surface; null if surface origin is not `COMMAND_PALETTE`. |
| `action_row_hash` | SHA-256 of preflight object | Drift detection. |
| `command_path` | `command` (or `UNKNOWN`) | Verbatim. |
| `parent_group` | derived from upstream payload | Verbatim if known. |
| `authority_domain` | `authority_domain` (may be `unknown / conflicting` or `UNKNOWN`) | Verbatim. |
| `canonical_writer` | `canonical_writer` (may be `UNKNOWN`) | Verbatim. |
| `safety_class` | `safety_class` | Verbatim. |
| `cockpit_placement` | derived from upstream payload | Verbatim if known. |
| `current_cockpit_coverage` | derived from upstream payload | Verbatim if known. |
| `activation_status` | derived from upstream payload | Verbatim if known. |
| `gate_tier` | `gate_tier` | Verbatim. |
| `unknown_fields` | list of fields that resolved to `UNKNOWN` | Empty if refusal trigger is not field-related. |
| `block_reason` | when applicable | `NOT_APPLICABLE` for non-blocked rows. |
| `unknown_reason` | when applicable | Free-text human reason. |
| `last_seen_activation_status` | from upstream payload | For visibility. |
| `required_investigation_packet` | derived (e.g., from `OPUS_REMEDIATION_PLAN.md` §1 sequencing) | When known; otherwise `INVESTIGATION_PACKET_REQUIRED`. |
| `last_evidence_timestamp` | from carried evidence stream | When available; otherwise `UNKNOWN`. |
| `last_proof_reference` | from carried evidence stream | When available; otherwise `UNKNOWN`. |
| `surface_origin` | `surface_origin` | Verbatim. |
| `gate_open_timestamp_utc` | from gate event/receipt | UTC. |
| `event_timestamp_utc` | UTC of this handoff event | UTC. |

## 3. Queue Behavior After Gate-Side Handoff

The Unknown/Drift Queue:

- Renders the row using the per-row fields enumerated in `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4.
- Provides **no** execution affordance under any condition (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3).
- Provides no copy-as-run shortcut that bypasses Palette + Safe Action Gate.
- Does not silently reclassify the row.
- Does not promote the row out of the queue without a packet artifact reference (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5).
- For `STALE_PROOF_GATE` rows: tags the row with the `stale_proof` badge and surfaces the row in the Overview drift summary (`SAFE_ACTION_GATE_SPEC.md` §4).

## 4. Reclassification Refusal

The gate refuses any operator action that would reclassify the row inside this handoff. Reclassification requires the same packet evidence enumerated in `UNKNOWN_DRIFT_QUEUE_SPEC.md` §5 and `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §4. The gate must include the `required_investigation_packet` reference where known so the operator has a clear next action.

## 5. Audit / Event Receipt

Per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md`, the gate emits a refusal or stale-proof event/receipt for every gate-side handoff:

- For refusal triggers: `gate_refuse` event with `routing_destination: UNKNOWN_DRIFT_QUEUE`.
- For stale-proof: `gate_proof_stale` event with `routing_destination: UNKNOWN_DRIFT_QUEUE` and `stale_proof_tag: true`.
- For incomplete proof: `gate_proof_incomplete` event with `routing_destination: UNKNOWN_DRIFT_QUEUE`.

The receipt includes:

- `gate_request_id`
- `palette_request_id` (when applicable)
- `action_row_hash`
- `tier`
- `safety_class`
- `authority_domain`
- `canonical_writer`
- `refusal_reason` or `proof_status`
- `routing_destination: UNKNOWN_DRIFT_QUEUE`
- UTC timestamps

The receipt is recorded regardless of whether the operator visits the queue.

## 6. Reachability From The Queue Back To The Gate

- The queue's rows are reachable from the palette via filter axes (`status:UNKNOWN`, `status:BLOCKED`, `coverage:MISSING`, `proof:STALE`).
- Selecting a queued row from the palette re-displays the same blocked/unknown state per `PALETTE_BLOCKED_UNKNOWN_STATES.md`.
- A queued row with `STALE_PROOF` may, after promotion through a packet, be re-handed-off to the gate via the upstream surface; the gate is **never** entered directly from the queue.

## 7. Forbidden In This Handoff

- Reclassifying the row inside the queue.
- Promoting the row out of the queue without a packet reference.
- Permitting an execution affordance.
- Permitting a copy-as-run shortcut that bypasses Palette + Safe Action Gate.
- Suppressing `BLOCKED_IN_COCKPIT` rows from queue visibility (the upstream Palette handoff still tracks blocked rows; the gate does not bypass that).
- Hiding `unknown_reason` or `block_reason` text.
- Auto-retrying a stale-proof action.
- Substituting a generic error message for the enumerated refusal reason.
- Suppressing the gate event/receipt for any handoff.

## 8. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §3, §4, §5, §6
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §3, §4
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1, §2, §6
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_BLOCKED_UNKNOWN_STATES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md` §4, §6
