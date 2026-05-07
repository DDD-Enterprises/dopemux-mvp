# Safe Action Gate Event Receipts

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the event/receipt shape the Safe Action Gate must emit at every stage of the gate's lifecycle (open, refuse, confirm, abort, timeout, proof-capture). Event/receipt emission is normative. No secrets are stored. The gate emits a receipt regardless of outcome.

## 1. Receipt Lifecycle

A single gate invocation produces one **gate request** identified by `gate_request_id`. That request emits one or more **lifecycle events** as the gate progresses:

```
[gate_open]
  └── [refuse | abort | timeout | confirmed]
                              │
                              └── [proof_captured | proof_incomplete | proof_stale]
```

Every event is append-only, recorded with a UTC timestamp, and correlated with the upstream `palette_request_id` (when applicable).

## 2. Event Type Catalog

| Event type | When emitted | Required outcome state |
| --- | --- | --- |
| `gate_open` | Gate receives upstream payload and renders preflight. | Initial event for every gate request. |
| `gate_refuse` | Gate refuses per `SAFE_ACTION_REFUSAL_RULES.md`. | Includes `refusal_reason` and routing destination. |
| `gate_abort` | Operator clicks Abort in the gate. | Includes `abort_kind: operator_aborted`. |
| `gate_timeout` | Confirm flow exceeds configured timeout. | Includes `abort_kind: operator_timeout`. |
| `gate_confirmed` | Operator confirmed (with typed confirmation match where required). | Includes `confirmation_status: confirmed`. |
| `gate_proof_captured` | Runtime authority emitted proof; gate captured all required artifacts. | Includes `proof_status: captured`. |
| `gate_proof_incomplete` | Runtime authority emitted proof but required artifacts are missing. | Includes `proof_status: incomplete` and missing-artifact list. |
| `gate_proof_stale` | Previously captured proof has expired or is missing on a row that requires fresh proof. | Includes `proof_status: stale`. |

Every event is recorded for the **same** `gate_request_id` so that downstream consumers can correlate the full lifecycle.

## 3. Receipt Schema (Normative)

```
{
  "gate_request_id": "<UUID generated at gate_open>",
  "palette_request_id": "<UUID from upstream payload, or null if origin != COMMAND_PALETTE>",
  "action_row_hash": "<SHA-256 of the gate's preflight object at gate_open>",
  "tier": "<one of T0, T0i, T1, T2, T3, T4, T5, T6, TX, TU>",
  "safety_class": "<one of DISPLAY_ONLY, INSPECT_ACTION, CONFIRM_REQUIRED, COMMAND_PALETTE_ONLY, BLOCKED_IN_COCKPIT, EXTERNAL_ONLY, UNKNOWN>",
  "authority_domain": "<one of ten enumerated authorities or UNKNOWN>",
  "canonical_writer": "<comma-joined writers or UNKNOWN>",
  "preflight_status": "<resolved | unknown_fields:[<field>,...]>",
  "confirmation_status": "<not_required | pending | confirmed | aborted | timeout | refused>",
  "execution_status": "<not_attempted | initiated | succeeded | failed | aborted_in_flight>",
  "proof_status": "<not_required | not_yet_captured | captured | incomplete | stale>",
  "proof_artifacts": {
    "<artifact_name>": "<artifact_value or hash>",
    "...": "..."
  },
  "refusal_reason": "<one of enumerated refusal reasons in SAFE_ACTION_REFUSAL_RULES.md or null>",
  "routing_destination": "<one of UNKNOWN_DRIFT_QUEUE | SHOW_BLOCKED_REASON | RE_RENDER | ORIGINATING_SURFACE | NOT_APPLICABLE>",
  "surface_origin": "<one of COMMAND_PALETTE, SETTINGS_ADMIN_RUNTIME, PM, IMPLEMENTER, OVERVIEW, SERVICES, EVENTS, UNKNOWN>",
  "operator_id": "<string or NULL_NOT_AUTHENTICATED>",
  "event_type": "<one of gate_open, gate_refuse, gate_abort, gate_timeout, gate_confirmed, gate_proof_captured, gate_proof_incomplete, gate_proof_stale>",
  "event_timestamp_utc": "<ISO-8601 UTC>",
  "gate_open_timestamp_utc": "<ISO-8601 UTC>",
  "confirm_timestamp_utc": "<ISO-8601 UTC or null>",
  "proof_timestamp_utc": "<ISO-8601 UTC or null>",
  "typed_confirmation_match": "<true | false | not_required>",
  "diff_acknowledged": "<diff | unknown_diff_accepted | not_applicable | null>",
  "remote_mutation_policy_reference": "<string or null>",
  "tp_or_task_id": "<string or null>",
  "service_id": "<string or null>",
  "stale_proof_tag": "<true | false>",
  "schema_version": "dopemux.cockpit.safe_action_gate.receipt.v1"
}
```

### Field notes

- `gate_request_id` is unique per gate invocation; a single operator click produces exactly one gate request.
- `action_row_hash` is the SHA-256 of the preflight object captured at `gate_open`. If the row drifts mid-flow, the gate emits a `gate_refuse` event with `refusal_reason: AUTHORITY_DRIFT_MID_FLOW` or `CLASS_DRIFT_MID_FLOW`.
- `palette_request_id` is `null` when the surface origin is not `COMMAND_PALETTE` (e.g., a contextual-surface origin in PM/Implementer/Overview/Services/Events).
- `operator_id` is captured **when authentication is in scope** for the deployment; it is `NULL_NOT_AUTHENTICATED` when authentication is not yet wired (consistent with `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 6 not yet satisfied).
- `proof_artifacts` carries the artifacts described in `SAFE_ACTION_PROOF_REQUIREMENTS.md` §2; values are paths, hashes, status strings, or excerpts. **Secrets MUST be redacted** before inclusion.
- `event_timestamp_utc` is the ISO-8601 UTC timestamp of the event itself; `gate_open_timestamp_utc` / `confirm_timestamp_utc` / `proof_timestamp_utc` are the timestamps of the corresponding lifecycle markers.

## 4. Receipt Per Event Type (Required Fields)

| Event type | Always required | Required when applicable |
| --- | --- | --- |
| `gate_open` | `gate_request_id`, `palette_request_id` (null if not palette), `tier`, `safety_class`, `authority_domain`, `canonical_writer`, `preflight_status`, `surface_origin`, `event_type`, `event_timestamp_utc`, `gate_open_timestamp_utc`, `schema_version` | `action_row_hash` (SHA-256 of preflight object) |
| `gate_refuse` | All `gate_open` fields plus `refusal_reason`, `routing_destination`, `confirmation_status: refused` | `unknown_fields` list when `preflight_status` indicates `unknown_fields:[...]` |
| `gate_abort` | All `gate_open` fields plus `confirmation_status: aborted`, `event_type: gate_abort` | n/a |
| `gate_timeout` | All `gate_open` fields plus `confirmation_status: timeout`, `event_type: gate_timeout` | n/a |
| `gate_confirmed` | All `gate_open` fields plus `confirmation_status: confirmed`, `confirm_timestamp_utc`, `typed_confirmation_match` | `diff_acknowledged` for T2; `tp_or_task_id` for T6; `service_id` for T5; `remote_mutation_policy_reference` for T4 |
| `gate_proof_captured` | All `gate_confirmed` fields plus `proof_status: captured`, `proof_timestamp_utc`, `proof_artifacts` (per tier) | `execution_status: succeeded` |
| `gate_proof_incomplete` | All `gate_confirmed` fields plus `proof_status: incomplete`, `proof_timestamp_utc`, `proof_artifacts` (partial), `routing_destination: UNKNOWN_DRIFT_QUEUE` | `stale_proof_tag: true` |
| `gate_proof_stale` | All `gate_open` fields plus `proof_status: stale`, `routing_destination: UNKNOWN_DRIFT_QUEUE`, `stale_proof_tag: true` | n/a |

## 5. No Secrets In Receipts

The gate must redact:

- API keys, OAuth tokens, bearer tokens, session cookies.
- Passwords, passphrases, private keys.
- PII (email addresses, phone numbers, account numbers) **unless** PII is the explicit subject of the action and policy permits it.
- Full request/response bodies for remote calls; capture only the excerpt the governance policy allows.
- Environment variable values that the inventory or policy flags as sensitive.

The gate's redaction strategy is normative; the runtime renderer packet (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) implements the redaction logic.

## 6. Receipt Append-Only

- Receipts are append-only in the evidence stream. The gate never edits or deletes a recorded receipt.
- A `gate_proof_captured` event for a previously `gate_proof_incomplete` request **does not delete** the incomplete event; it appends a new event with updated `proof_status` and updated artifacts.
- A `gate_proof_stale` event on a row with prior `gate_proof_captured` **does not edit** the prior event; it appends a stale event referencing the prior `gate_request_id`.

## 7. Correlation With Upstream Receipts

| Upstream surface | Upstream receipt schema | Correlation field |
| --- | --- | --- |
| Command Palette | `PALETTE_PROOF_REQUIREMENTS.md` §3 | `palette_request_id` |
| Settings/Admin/Runtime | per `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §6 | `palette_request_id` (carried through admin handoff) |
| Contextual surface in PM/Implementer/Overview/Services/Events | TBD per `TP-DMX-COCKPIT-RUNTIME-RENDER-001` | `surface_origin` plus a surface-local correlation id (defined by the runtime packet) |

The gate writes its receipts to the same evidence stream as the upstream surface so that end-to-end audit trails stitch together.

## 8. Receipt Recorded Even On Refusal Or Abort

The gate must:

- Record a `gate_refuse` receipt for every refusal trigger (`SAFE_ACTION_REFUSAL_RULES.md`).
- Record a `gate_abort` receipt when the operator clicks Abort.
- Record a `gate_timeout` receipt when the confirm flow times out.
- Record a `gate_proof_stale` receipt when the runtime detects stale proof.
- Record a `gate_proof_incomplete` receipt when the runtime emits proof that is missing required artifacts.

The gate **never** silently discards an event.

## 9. Forbidden In Receipt Behavior

- Suppressing a receipt for any event type.
- Reusing a `gate_request_id` across distinct gate invocations.
- Editing or deleting a recorded receipt.
- Recording `proof_status: captured` before proof artifacts are present.
- Recording `confirmation_status: confirmed` before the operator has clicked confirm (and matched the typed token where required).
- Recording `execution_status: succeeded` without a corresponding `gate_proof_captured` event.
- Storing secrets in `proof_artifacts`.
- Substituting local-time timestamps for UTC.

## 10. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §3, §4
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §4, §5
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md` §3, §6, §7, §8
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §6
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §6
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §6
