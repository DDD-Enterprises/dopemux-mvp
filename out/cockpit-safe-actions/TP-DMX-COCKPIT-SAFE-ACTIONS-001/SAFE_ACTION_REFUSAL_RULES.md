# Safe Action Gate Refusal Rules

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the enumerated refusal triggers the Safe Action Gate must detect and the routing each refused action must follow. Refusal is fail-closed; the gate never silently ignores a refusal trigger and never lets a refused action execute. Every refusal emits a gate event/receipt per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md`.

## 1. Refusal Outcomes (Where Refused Actions Go)

A refused action routes to exactly one of:

| Routing destination | When |
| --- | --- |
| **`ShowBlockedReason`** (handed back to originating surface) | `safety_class == BLOCKED_IN_COCKPIT` or `activation_status == DEPRECATED_BLOCKED`. |
| **Unknown / Drift Queue** | Every other refusal trigger (UNKNOWN class, missing fields, authority conflict, stale proof, etc.). |
| **Re-render (return to upstream surface)** | Stale `palette_index_row_hash` (`INDEX_DRIFT`) — the upstream surface re-renders the preview before the gate can re-open. |
| **Originating surface for re-resolution** | `PARAM_UNRESOLVED` and `DEFAULT_UNKNOWN` if the upstream surface offers parameter resolution; otherwise Unknown/Drift Queue. |

The gate never routes a refused action to itself again on the same payload. Re-attempt requires a new upstream handoff with a fresh `palette_request_id` and a fresh `palette_index_row_hash`.

## 2. Refusal Trigger Catalog

### 2.1 Identity & Resolution Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Missing command | `command == UNKNOWN` | `COMMAND_UNRESOLVED` | Unknown/Drift Queue |
| Required parameter unresolved | `resolved_params.required[*] == UNKNOWN` | `PARAM_UNRESOLVED` | Originating surface for re-resolution; else Unknown/Drift Queue |
| Optional default unknown | `resolved_params.optional[*].value == UNKNOWN` | `DEFAULT_UNKNOWN` | Originating surface for re-resolution; else Unknown/Drift Queue |
| Cwd outside worktree | `cwd` is `UNKNOWN`, `/tmp`, or any non-worktree path | `CWD_UNRESOLVED` or `CWD_OUT_OF_WORKTREE` | Unknown/Drift Queue |
| Worktree metadata unresolved | `worktree_metadata.branch == UNKNOWN`, etc. | `WORKTREE_METADATA_UNRESOLVED` | Unknown/Drift Queue |
| Dirty worktree where tier requires clean | `worktree_metadata.dirty == true` and tier is destructive write | `WORKTREE_DIRTY` | Unknown/Drift Queue |

### 2.2 Authority & Writer Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Unknown authority | `authority_domain == UNKNOWN` | `AUTHORITY_UNKNOWN` | Unknown/Drift Queue |
| Conflicting authority | `authority_domain == 'unknown / conflicting'` | `AUTHORITY_CONFLICT` | Unknown/Drift Queue |
| Unknown canonical writer | `canonical_writer == UNKNOWN` | `WRITER_UNKNOWN` | Unknown/Drift Queue |

### 2.3 Class & Tier Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Blocked class arriving at confirm path | `safety_class == BLOCKED_IN_COCKPIT` | `BLOCKED_IN_COCKPIT` | `ShowBlockedReason` |
| Unknown class | `safety_class == UNKNOWN` | `UNKNOWN_CLASS` | Unknown/Drift Queue |
| External-only class arriving at confirm path | `safety_class == EXTERNAL_ONLY` | `EXTERNAL_ONLY` | `Inspect`/`CopyCommand` only at originating surface |
| Non-executable tier on confirm path | `gate_tier in {T0, T0i, TX, TU}` arrives at confirm flow | `NON_EXECUTABLE_TIER` | Routing destination per the tier (TX ⇒ blocked display; TU ⇒ Unknown/Drift Queue; T0/T0i route back to inspect) |
| Gate tier unknown | `gate_tier == UNKNOWN` | `GATE_TIER_UNKNOWN` | Unknown/Drift Queue |

### 2.4 Activation Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Activation deprecated/blocked | `activation_status == DEPRECATED_BLOCKED` | `DEPRECATED_BLOCKED` | `ShowBlockedReason` |
| Activation defined-but-not-registered | `activation_status == DEFINED_NOT_REGISTERED` | `NOT_ACTIVE` | Unknown/Drift Queue |
| Activation optional-import-unknown | `activation_status == OPTIONAL_IMPORT_UNKNOWN` | `NOT_ACTIVE` | Unknown/Drift Queue |
| Activation status unknown | `activation_status == UNKNOWN` | `NOT_ACTIVE` | Unknown/Drift Queue |

### 2.5 Side-Effect & Proof Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Side effects unknown for executable tier | `side_effects == UNKNOWN` for T1–T6 | `SIDE_EFFECTS_UNKNOWN` | Unknown/Drift Queue |
| Side effects empty for executable tier | `side_effects == []` for T1–T6 | `SIDE_EFFECTS_EMPTY` | Unknown/Drift Queue |
| Expected proof unknown for executable tier | `expected_proof == UNKNOWN` for T1–T6 | `PROOF_REQUIREMENT_UNKNOWN` | Unknown/Drift Queue |
| Missing proof target | tier requires explicit proof target (e.g., T1 `output_target_path`, T6 `output_or_proof_target`) and target is `UNKNOWN` | `PROOF_TARGET_UNKNOWN` | Unknown/Drift Queue |

### 2.6 Rollback & Abort Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Rollback unknown for destructive tier | `rollback_or_abort == UNKNOWN` for T3 destructive, T4, T5, T6 | `ROLLBACK_UNKNOWN` | Unknown/Drift Queue |
| Rollback insufficient for tier | `rollback_or_abort.kind == NOT_APPLICABLE` for tier that requires rollback | `ROLLBACK_INSUFFICIENT` | Unknown/Drift Queue |

### 2.7 Remote Mutation Failures (T4)

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Remote-mutation policy missing | `remote_mutation_policy_reference` not present | `REMOTE_MUTATION_POLICY_MISSING` | Unknown/Drift Queue |
| Remote-mutation policy not approved for this row | policy reference exists but does not approve the row | `REMOTE_MUTATION_POLICY_NOT_APPROVED` | Unknown/Drift Queue |
| Remote endpoint unknown | `remote_target_endpoint == UNKNOWN` | `REMOTE_ENDPOINT_UNKNOWN` | Unknown/Drift Queue |
| Remote account/context unknown | `remote_account_or_context == UNKNOWN` | `REMOTE_ACCOUNT_UNKNOWN` | Unknown/Drift Queue |
| Idempotency key unknown | `idempotency_key == UNKNOWN` (when policy requires) | `IDEMPOTENCY_KEY_UNKNOWN` | Unknown/Drift Queue |

### 2.8 Service & Execution Handoff Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Service id unknown (T5) | `service_id == UNKNOWN` | `SERVICE_ID_UNKNOWN` | Unknown/Drift Queue |
| Pre-state snapshot missing (T5) | `pre_state_snapshot == UNKNOWN` | `PRE_STATE_SNAPSHOT_MISSING` | Unknown/Drift Queue |
| Expected state transition unknown (T5) | `expected_state_transition == UNKNOWN` | `STATE_TRANSITION_UNKNOWN` | Unknown/Drift Queue |
| TP id unknown (T6) | `tp_or_task_id == UNKNOWN` | `TP_ID_UNKNOWN` | Unknown/Drift Queue |
| Runner id unknown (T6) | `runner_id == UNKNOWN` | `RUNNER_ID_UNKNOWN` | Unknown/Drift Queue |
| Branch unknown (T6) | `branch == UNKNOWN` | `BRANCH_UNKNOWN` | Unknown/Drift Queue |
| TP gate absent (T6) | `tp_gate_present == false` | `TP_GATE_ABSENT` | Unknown/Drift Queue |

### 2.9 Provenance & Correlation Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Source provenance unknown (executable tier) | `source_provenance.source_file == UNKNOWN` etc. | `PROVENANCE_UNKNOWN` | Unknown/Drift Queue |
| Palette request id missing | `palette_request_id == UNKNOWN` | `REQUEST_ID_MISSING` | Unknown/Drift Queue |
| Index row hash missing | `palette_index_row_hash == UNKNOWN` | `INDEX_HASH_MISSING` | Unknown/Drift Queue |
| Index row hash stale | `palette_index_row_hash` mismatch with current index | `INDEX_DRIFT` | Re-render at upstream surface; require new handoff |

### 2.10 Stale Handoff & Stale Proof

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Stale handoff timestamp | `created_at_utc` older than configured stale window | `STALE_HANDOFF` | Re-render at upstream surface |
| Stale proof on a previously gated action | runtime detects expired/missing post-action proof | `STALE_PROOF_GATE` | Unknown/Drift Queue with `STALE_PROOF` tag |

### 2.11 Origin & Intent Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Surface origin unknown | `surface_origin == UNKNOWN` | `SURFACE_ORIGIN_UNKNOWN` | Unknown/Drift Queue |
| Unsafe surface origin | `surface_origin` is a deep-link, URL parameter, keyboard shortcut, or background trigger that bypasses the upstream surface | `UNSAFE_SOURCE_SURFACE` | Unknown/Drift Queue |
| Operator intent unknown (executable tier) | `operator_intent == UNKNOWN` | `INTENT_UNKNOWN` | Unknown/Drift Queue |

### 2.12 Confirmation-Flow Failures

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Typed confirmation mismatch (T4/T5/T6) | typed value does not match expected token | `TYPED_CONFIRMATION_MISMATCH` | Re-prompt at gate; if abandoned, abort and emit refusal event/receipt |
| Diff not acknowledged (T2 with UNKNOWN diff) | operator did not toggle `Accept UNKNOWN diff` | `DIFF_NOT_ACKNOWLEDGED` | Re-prompt at gate; if abandoned, abort |
| Operator aborted | operator clicks Abort | `OPERATOR_ABORTED` | Emit abort event/receipt; return; no execution |
| Operator timed out | confirm flow exceeds configured timeout | `OPERATOR_TIMEOUT` | Emit timeout event/receipt; return; no execution |

### 2.13 Authority Drift Mid-Flow

| Trigger | Field affected | Refusal reason | Routing |
| --- | --- | --- | --- |
| Authority resolution lost mid-flow | `authority_domain` becomes `unknown / conflicting` after preflight rendered | `AUTHORITY_DRIFT_MID_FLOW` | Unknown/Drift Queue |
| Class disagrees with carried-forward classification | gate observes class change between handoff and confirm | `CLASS_DRIFT_MID_FLOW` | Block until reclassified through a packet (gate cannot reclassify) |

## 3. Refusal Always Emits A Gate Event/Receipt

Every refusal triggers a gate event/receipt per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md`. The receipt includes:

- `gate_request_id`
- `palette_request_id` if applicable
- `tier`
- `safety_class`
- `authority_domain`
- `canonical_writer`
- preflight status (`UNKNOWN_FIELDS: [field, ...]` if applicable)
- `refusal_reason` (one of the enumerated reasons above)
- routing destination (`UNKNOWN_DRIFT_QUEUE`, `SHOW_BLOCKED_REASON`, `RE_RENDER`, `ORIGINATING_SURFACE`)
- timestamps

Refusal events/receipts are append-only; they are never deleted or rewritten by the gate.

## 4. Refusal Always Surfaces The Reason To The Operator

The gate UI displays the refusal reason and the routing destination using the primitive states defined in `SAFE_ACTION_GATE_UI_PRIMITIVES.md`. Specifically:

- For `BLOCKED_IN_COCKPIT` and `DEPRECATED_BLOCKED`: the gate hands back to the originating surface to render the blocked-row inspector.
- For all other refusals: the gate displays the refusal panel with the missing/conflicting fields, the refusal reason, and a `Continue to Drift Queue` affordance.
- For `INDEX_DRIFT`: the gate displays a `Re-render preview` affordance that returns the operator to the upstream surface.
- For `STALE_HANDOFF`: the gate displays a `Re-render preview` affordance that requires the operator to re-issue the handoff.
- For `OPERATOR_ABORTED` and `OPERATOR_TIMEOUT`: the gate closes; no further routing, but the event/receipt is still recorded.

The gate never silently dismisses a refusal.

## 5. Refusal Cannot Be Bypassed

The gate must:

- Refuse without exception when any enumerated trigger fires.
- Refuse without exception when the typed confirmation token does not match (T4/T5/T6).
- Refuse without exception when the surface origin is unsafe (deep-link, URL parameter, keyboard shortcut bypassing the surface).
- Refuse without exception when an `UNKNOWN` row reaches the confirm path.
- Refuse without exception when a `BLOCKED_IN_COCKPIT` row reaches any execution path.
- Refuse without exception when authority drift or class drift is detected mid-flow.

Refusals cannot be overridden by:

- Operator preference, "remember my choice", or session state.
- A retry that does not include a fresh upstream handoff.
- A re-render that does not refresh the `palette_index_row_hash`.
- A reclassification attempt inside the gate (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5).

## 6. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §2, §4, §5
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:classes`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §3, §5
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md` §6
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §3, §7
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md` §7, §9
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1, §4
