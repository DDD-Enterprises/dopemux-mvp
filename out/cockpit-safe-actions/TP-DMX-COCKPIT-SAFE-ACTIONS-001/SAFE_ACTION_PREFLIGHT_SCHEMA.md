# Safe Action Gate Preflight Schema (Human-Readable)

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)
**Companion file:** `SAFE_ACTION_PREFLIGHT_SCHEMA.json`

This document explains every preflight field the Safe Action Gate must collect and display before rendering a confirm affordance, and the fail-closed behavior when any field is unresolved. Every field traces back to the carried `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` payload, the `COMMAND_PALETTE_INDEX_SCHEMA.json` row schema, or upstream-surface equivalent. The preflight schema is normative.

## 1. Fail-Closed Rule (Apex Invariant)

If **any** required field for the row's assigned tier resolves to `UNKNOWN`, the gate **MUST NOT** render a confirm affordance. Instead, the gate routes the action to the Unknown/Drift Queue with the missing-field reason (see `SAFE_ACTION_REFUSAL_RULES.md`). The gate:

- Never invents values for missing fields.
- Never silently substitutes defaults.
- Never auto-confirms.
- Never treats a `BLOCKED_IN_COCKPIT` or `UNKNOWN` row as confirmable.
- Never renders a confirm affordance with `UNKNOWN` field state.

Missing fields render as the literal string `UNKNOWN`, never blank. The operator always sees the missing-field state and the refusal reason.

## 2. Field Reference

### `command` (string) — REQUIRED for all tiers

- **What:** Fully resolved invocation including subcommands. No shell-escape ambiguity. Verbatim from upstream payload.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `command`, or Settings/Admin/Runtime equivalent, or contextual surface.
- **Missing behavior:** `UNKNOWN` ⇒ gate refuses, routes to Unknown/Drift Queue with reason `COMMAND_UNRESOLVED`.

### `resolved_params` (object) — REQUIRED for T0i–T6

- **What:** Map of required and optional parameters with values resolved per `PALETTE_PARAMETER_PREVIEW_SPEC.md`. The required map's values are never `UNKNOWN`; the optional map records whether each value was the explicit default (`was_default: true`).
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `resolved_params.required` and `resolved_params.optional`.
- **Missing behavior:** Any required value `UNKNOWN` ⇒ refuse with reason `PARAM_UNRESOLVED`. Any optional default `UNKNOWN` ⇒ refuse with reason `DEFAULT_UNKNOWN`.

### `cwd` (string) — REQUIRED for T0i–T6

- **What:** Absolute path within the current worktree. Resolved against the current worktree, never `/tmp` or any non-worktree path.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `cwd`.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `CWD_UNRESOLVED`. Outside worktree ⇒ refuse with reason `CWD_OUT_OF_WORKTREE`.

### `worktree_metadata` (object) — REQUIRED for T0i–T6

- **What:** Runtime worktree info. Includes `branch`, `detached`, `dirty`, `worktree_root`. The gate uses `dirty` to enforce clean-worktree requirements for tiers that demand it (e.g., destructive T3 writes).
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `worktree_metadata`.
- **Missing behavior:** `UNKNOWN` for required sub-fields ⇒ refuse with reason `WORKTREE_METADATA_UNRESOLVED`. Dirty when tier requires clean ⇒ refuse with reason `WORKTREE_DIRTY`.

### `authority_domain` (string) — REQUIRED for all tiers

- **What:** Authority domain that owns the action. One of the ten enumerated domains in `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.authority_domain`.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `authority_domain`.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `AUTHORITY_UNKNOWN`. `unknown / conflicting` ⇒ refuse with reason `AUTHORITY_CONFLICT`.

### `canonical_writer` (string) — REQUIRED for T0i–T6

- **What:** System or service that owns the write/state mutation. If multiple writers exist, all writers are listed comma-separated. Required for the gate to display every writer for T2–T6 actions.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `canonical_writer`.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `WRITER_UNKNOWN`.

### `safety_class` (string) — REQUIRED for all tiers

- **What:** Safety class governing the row's allowed UI form. One of the seven enumerated classes in `COMMAND_EXPOSURE_POLICY.json:classes`.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `safety_class` (from `safe_ui_exposure`).
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `UNKNOWN_CLASS`. `BLOCKED_IN_COCKPIT` ⇒ refuse with reason `BLOCKED_IN_COCKPIT`. `EXTERNAL_ONLY` ⇒ refuse with reason `EXTERNAL_ONLY`.

### `gate_tier` (string) — REQUIRED for all tiers

- **What:** Confirmation tier. Carried verbatim from upstream surface. The gate never reclassifies. Only T1–T6 reach a confirm affordance.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `gate_tier`.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `GATE_TIER_UNKNOWN`. `T0`/`T0i`/`TX`/`TU` arriving at the confirm path ⇒ refuse with reason `NON_EXECUTABLE_TIER` and route appropriately.

### `side_effects` (array of string) — REQUIRED for T1–T6

- **What:** Enumerated side effects. Must not be empty for any executable tier (T1–T6). One or more of: `config mutation`, `write local`, `write remote`, `start service`, `stop service`, `execution handoff`, `generated artifact`, `none`.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `side_effects` (from `parameter_schema.side_effects`).
- **Missing behavior:** `UNKNOWN` or empty for executable tier ⇒ refuse with reason `SIDE_EFFECTS_UNKNOWN`.

### `expected_proof` (string) — REQUIRED for all tiers

- **What:** Proof category the gate must capture after execution. One of the ten enumerated categories in `COMMAND_PALETTE_INDEX_SCHEMA.json:fields.proof_requirement.enum`.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `expected_proof` (from `proof_requirement`).
- **Missing behavior:** `UNKNOWN` for executable tier ⇒ refuse with reason `PROOF_REQUIREMENT_UNKNOWN`.

### `rollback_or_abort` (object) — REQUIRED for T1–T6

- **What:** Explicit rollback path, abort token, or `NOT_APPLICABLE` with documented reason. Required for executable tiers; the gate displays the rollback plan in the preflight panel.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `rollback_or_abort`.
- **Missing behavior:** `UNKNOWN` for destructive tier (T3, T4, T5, T6, and T2 with destructive scope) ⇒ refuse with reason `ROLLBACK_UNKNOWN`.

### `source_provenance` (object) — REQUIRED for all tiers

- **What:** End-to-end provenance: `source_file`, `source_symbol`, `evidence_path_or_command`. Used for audit trail and operator inspection.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `source_provenance`.
- **Missing behavior:** `UNKNOWN` for executable tier ⇒ refuse with reason `PROVENANCE_UNKNOWN`. For T0/T0i/TX/TU display, missing provenance is shown as `UNKNOWN` but does not block the read-only display.

### `palette_request_id` (string) — REQUIRED for T0i–T6, TX, TU

- **What:** UUID generated at upstream handoff. Correlation id for evidence/audit logs. The gate event/receipt records the same id.
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `palette_request_id` or upstream-surface equivalent.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `REQUEST_ID_MISSING`.

### `palette_index_row_hash` (string) — REQUIRED for T1–T6

- **What:** SHA-256 of the normalized index row at handoff time. Lets the gate verify the row hasn't drifted in flight (INDEX_DRIFT detection).
- **Source:** `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 `palette_index_row_hash`.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `INDEX_HASH_MISSING`. Stale (does not match current index hash) ⇒ refuse with reason `INDEX_DRIFT` and force re-render.

### `surface_origin` (string) — REQUIRED for all tiers

- **What:** Which surface originated this gate invocation. One of `COMMAND_PALETTE`, `SETTINGS_ADMIN_RUNTIME`, `PM`, `IMPLEMENTER`, `OVERVIEW`, `SERVICES`, `EVENTS`, `UNKNOWN`.
- **Source:** Upstream surface emits this field at handoff.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `SURFACE_ORIGIN_UNKNOWN`. Unsafe origin (deep-link, URL parameter, keyboard shortcut bypassing surface) ⇒ refuse with reason `UNSAFE_SOURCE_SURFACE`.

### `operator_intent` (string) — REQUIRED for T0i–T6

- **What:** What the operator intends. One of `INSPECT_ONLY`, `CONFIRM_AND_RUN`, `CONFIRM_AND_DRY_RUN`, `ABORT`, `UNKNOWN`.
- **Source:** Upstream surface (operator's selected outcome).
- **Missing behavior:** `UNKNOWN` for executable tier ⇒ refuse with reason `INTENT_UNKNOWN`.

### `created_at_utc` (string) — REQUIRED for all tiers

- **What:** ISO-8601 UTC timestamp recording when the upstream surface produced the action request. The gate uses this to detect stale handoffs.
- **Source:** Generated at handoff time at upstream surface.
- **Missing behavior:** `UNKNOWN` ⇒ refuse with reason `STALE_HANDOFF_UNKNOWN_TIMESTAMP`. A handoff older than the configured stale window is refused with reason `STALE_HANDOFF`.

## 3. Tier Field-Set Summary

The following tiers require **all** of: `command`, `resolved_params`, `cwd`, `worktree_metadata`, `authority_domain`, `canonical_writer`, `safety_class`, `gate_tier`, `side_effects`, `expected_proof`, `rollback_or_abort`, `source_provenance`, `palette_request_id`, `palette_index_row_hash`, `surface_origin`, `operator_intent`, `created_at_utc`:

- **T1** plus tier-specific: `output_target_path`, `overwrite_behavior`.
- **T2** plus tier-specific: `config_target_file_or_service`, `effective_config_diff_or_unknown_flag`.
- **T3** plus tier-specific: `write_target_path`, `side_effect_classification`.
- **T4** plus tier-specific: `remote_target_endpoint`, `remote_account_or_context`, `idempotency_key`, `remote_mutation_policy_reference`, `typed_confirmation`.
- **T5** plus tier-specific: `service_id`, `service_scope`, `expected_state_transition`, `pre_state_snapshot`, `typed_confirmation`.
- **T6** plus tier-specific: `tp_or_task_id`, `runner_id`, `branch`, `output_or_proof_target`, `tp_gate_present`, `typed_confirmation`.

T0 (DISPLAY_ONLY): `command`, `authority_domain`, `safety_class`, `gate_tier`, `source_provenance`, `surface_origin`, `created_at_utc`.

T0i (INSPECT_ACTION): T0 set plus `resolved_params`, `cwd`, `worktree_metadata`, `canonical_writer`, `palette_request_id`, `operator_intent`. No side-effect-bearing fields required (inspect has no write).

TX (BLOCKED_IN_COCKPIT): T0 set plus `block_reason`, `replacement_command_or_NOT_APPLICABLE`, `required_external_workflow_or_NOT_APPLICABLE`, `palette_request_id`.

TU (UNKNOWN): T0 set with `command_or_UNKNOWN` and `authority_domain_or_UNKNOWN`, plus `unknown_reason`, `required_investigation_packet_or_UNKNOWN`, `palette_request_id`.

(See `SAFE_ACTION_GATE_TIER_SCHEMA.json` for the canonical per-tier preflight field lists, including tier-specific extensions.)

## 4. Fail-Closed Behaviors By Field Class

| Field class | Field examples | Fail-closed when |
| --- | --- | --- |
| Command identity | `command`, `resolved_params`, `cwd` | UNKNOWN, outside worktree |
| Authority | `authority_domain`, `canonical_writer` | UNKNOWN, conflicting |
| Class / Tier | `safety_class`, `gate_tier` | UNKNOWN, BLOCKED, EXTERNAL_ONLY, non-executable tier on confirm path |
| Side effects | `side_effects` | UNKNOWN, empty for T1–T6 |
| Proof | `expected_proof` | UNKNOWN for T1–T6 |
| Rollback | `rollback_or_abort` | UNKNOWN for destructive tier |
| Provenance | `source_provenance` | UNKNOWN for executable tier |
| Correlation | `palette_request_id`, `palette_index_row_hash`, `created_at_utc` | UNKNOWN, stale, drift |
| Origin/intent | `surface_origin`, `operator_intent` | UNKNOWN, unsafe origin |

## 5. Fail-Closed Routing

When any field fails closed, the gate routes per `SAFE_ACTION_REFUSAL_RULES.md`:

- `BLOCKED_IN_COCKPIT` ⇒ `ShowBlockedReason` (handed back to originating surface).
- All other fail-closed reasons ⇒ Unknown/Drift Queue with the enumerated reason.

The gate emits a refusal event/receipt per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` regardless of routing destination. The gate never silently drops a refused action.

## 6. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §2, §4, §5
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json:fields`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2, §3
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §2, §4
