# Palette → Settings/Admin/Runtime Handoff

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines how the Command Palette routes admin/runtime rows to the Settings/Admin/Runtime surface. The palette never bypasses Settings/Admin/Runtime when the row's placement is `Settings/Admin`. Settings/Admin/Runtime is a major secondary surface; it is reached and not skipped. The Safe Action Gate is invoked **from** Settings/Admin/Runtime, not directly from the palette, for these rows.

## 1. When This Handoff Fires

The palette routes to Settings/Admin/Runtime when, and only when, all of the following are true:

- The row's `cockpit_placement` is `Settings/Admin`, **or** the row belongs to a flow group enumerated in `SETTINGS_ADMIN_RUNTIME_SPEC.md` §2:
  - Routing / Model Provider
  - Profile management
  - Environment management
  - MCP server control
  - Service startup / lifecycle (admin)
  - Hooks / native-hooks
  - Runtime configuration
  - Admin / safe / debug helpers
  - Drift inspection (read-only)
- The row's `safe_ui_exposure` is `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, or `CONFIRM_REQUIRED` (admin tier).
- The row's `activation_status` is `ACTIVE` (otherwise the row routes to Unknown/Drift Queue or `ShowBlockedReason`).
- The operator selected the primary outcome `OpenSettingsAdminRuntime`.

If any of these is false, route per `PALETTE_ROUTING_RULES.md`.

## 2. Handoff Payload (Required Fields)

The palette delivers a payload to the Settings/Admin/Runtime surface. The surface uses this payload to land the operator on the correct flow group and to pre-populate the gate inputs the surface will hand off to the Safe Action Gate.

| Field | Source | Notes |
| --- | --- | --- |
| `flow_group` | derived from `parent_group` and `command_path` | One of the nine flow groups in `SETTINGS_ADMIN_RUNTIME_SPEC.md` §2. |
| `command_path` | `command_path` | Verbatim. |
| `proposed_resolved_params` | `parameter_schema` resolved per preview | Surfaces preview values into the surface; surface re-displays them for the operator. |
| `cwd` | `parameter_schema.cwd_target` resolved | Required, never `/tmp` substitute. |
| `authority_domain` | `authority_domain` | Verbatim. |
| `canonical_writer` | `canonical_writer` | Comma-joined writers. |
| `safety_class` | `safe_ui_exposure` | One of allowed admin classes. |
| `proposed_gate_tier` | `gate_tier` | The surface validates the tier before invoking the gate. |
| `side_effects` | `parameter_schema.side_effects` | Required for any non-display/inspect class. |
| `expected_proof` | `proof_requirement` | Surface must show the proof category in its admin confirm UI. |
| `source_provenance` | `source_file:source_symbol`, `evidence_path_or_command` | Preserved end-to-end. |
| `palette_request_id` | UUID generated at handoff | Correlation id. |
| `palette_index_row_hash` | SHA-256 of normalized row | Drift detection. |

## 3. Surface Lands The Operator, Then Invokes The Gate

The handoff opens Settings/Admin/Runtime at the correct flow group with the row's preview pre-populated. From that surface, the operator confirms the action; the surface then invokes the Safe Action Gate with the same payload structure described in `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`. The palette is out of the loop after the surface opens.

| Flow group | Allowed safety classes (per `SETTINGS_ADMIN_RUNTIME_SPEC.md` §4) | Likely tier |
| --- | --- | --- |
| Routing / Model Provider | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` (admin) | `T2` |
| Profile / Env | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` (admin) | `T2` |
| MCP server control | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (admin) | `T2` / `T5` |
| Service startup / lifecycle (admin) | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (start/stop) | `T5` |
| Hooks / native-hooks | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` | `T2` |
| Runtime / admin / debug helpers | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY` | `T0i` / `T2` / `T5` |
| Drift inspection | `DISPLAY_ONLY`, `INSPECT_ACTION` | `T0` / `T0i` (read-only) |

## 4. Refusal Rules

The palette refuses to route to Settings/Admin/Runtime and re-routes to Unknown/Drift Queue when:

| Refusal trigger | Reason |
| --- | --- |
| `flow_group` cannot be derived from `parent_group` / `command_path`. | `FLOW_GROUP_UNKNOWN` |
| `safe_ui_exposure == BLOCKED_IN_COCKPIT`. | route to `ShowBlockedReason` instead. |
| `safe_ui_exposure == UNKNOWN`. | `UNKNOWN_CLASS`. |
| `authority_domain == 'unknown / conflicting'`. | `AUTHORITY_CONFLICT`. |
| Required parameters resolve to `UNKNOWN`. | `PARAM_UNRESOLVED`. |
| `cwd` resolves to `UNKNOWN`. | `CWD_UNRESOLVED`. |
| `gate_tier` is `UNKNOWN` or non-executable for an executable selection. | `GATE_TIER_UNKNOWN`. |
| `activation_status` is non-`ACTIVE`. | `NOT_ACTIVE`. |

## 5. Surface Boundaries Preserved

The palette does not change the surface contracts. Settings/Admin/Runtime:

- Is a major secondary surface, not a sixth top-level mode (`SETTINGS_ADMIN_RUNTIME_SPEC.md` §1, §5).
- Does not own state, truth, or PM workflow.
- Does not provide an alternative path around the Safe Action Gate.
- Does not subsume Services or Overview.

The palette must not collapse Settings/Admin/Runtime into the palette itself.

## 6. Audit / Event Receipt

The palette records a routing receipt to the evidence stream:

- `palette_request_id`
- `palette_index_row_hash`
- timestamp (UTC)
- target `flow_group`
- target `gate_tier`
- handoff outcome (`accepted`, `refused`, `rerouted`)
- refusal reason (if any)

The Settings/Admin/Runtime surface is responsible for the post-action proof receipt when its gate confirms.

## 7. Forbidden In This Handoff

- Skipping Settings/Admin/Runtime and routing directly to the Safe Action Gate for `Settings/Admin` rows.
- Auto-confirming inside Settings/Admin/Runtime from a palette selection.
- Bypassing the surface for runtime/admin rows by treating them as ordinary palette rows.
- Permitting `BLOCKED_IN_COCKPIT` rows to enter Settings/Admin/Runtime.
- Permitting `UNKNOWN` rows to enter Settings/Admin/Runtime.
- Sending parameters with `UNKNOWN` required fields.

## 8. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
