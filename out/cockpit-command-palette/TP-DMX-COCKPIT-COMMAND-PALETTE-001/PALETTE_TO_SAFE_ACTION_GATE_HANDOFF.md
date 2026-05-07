# Palette → Safe Action Gate Handoff

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the exact handoff payload, refusal rules, and post-handoff behavior between the Command Palette and the Safe Action Gate (`SAFE_ACTION_GATE_SPEC.md`). The palette never executes; the gate confirms and proves. This handoff is the only path from a palette `CONFIRM_REQUIRED` selection to a gate confirmation.

## 1. When This Handoff Fires

The handoff fires when, and only when, all of the following are true:

- The selected row's `safe_ui_exposure` is `CONFIRM_REQUIRED` or `COMMAND_PALETTE_ONLY` with an executable `gate_tier`.
- The row's `cockpit_placement` is **not** `Settings/Admin` (admin rows go through `OpenSettingsAdminRuntime` first; that surface invokes the gate).
- The row's `activation_status` is `ACTIVE`.
- The row's `authority_domain` is one of the resolved authorities (not `unknown / conflicting`).
- The row's `parameter_schema` resolves with no `UNKNOWN` required fields (per `PALETTE_PARAMETER_PREVIEW_SPEC.md` §6).
- The operator explicitly clicked the primary outcome `OpenSafeActionGate`.

If any of these is false, the handoff is **refused**. The row is routed instead to Unknown/Drift Queue or Settings/Admin/Runtime per `PALETTE_ROUTING_RULES.md`.

## 2. Handoff Payload (Required Fields)

The palette delivers the following payload to the Safe Action Gate. Every field is required. If any field is `UNKNOWN`, the handoff is refused.

| Field | Source | Notes |
| --- | --- | --- |
| `command` | `command_path` + resolved subcommands | Fully resolved invocation, no shell-escape ambiguity. |
| `resolved_params.required` | `parameter_schema.required_parameters` (resolved values) | Map of name → value; no value may be `UNKNOWN`. |
| `resolved_params.optional` | `parameter_schema.optional_parameters` with explicit defaults | Map of name → {value, was_default: bool}. Defaults are explicit. |
| `cwd` | `parameter_schema.cwd_target` (resolved against current worktree) | Absolute path; never `/tmp` or non-worktree path. |
| `worktree_metadata` | runtime worktree info | Includes branch, detached-state, dirty flag when knowable. |
| `authority_domain` | `authority_domain` | Verbatim. |
| `canonical_writer` | `canonical_writer` | All writers, comma-joined. |
| `safety_class` | `safe_ui_exposure` | One of `CONFIRM_REQUIRED`, `COMMAND_PALETTE_ONLY`. Never `BLOCKED_IN_COCKPIT` or `UNKNOWN`. |
| `gate_tier` | `gate_tier` | One of `T1`–`T6`. Never `T0`/`T0i`/`TX`/`TU`. |
| `side_effects` | `parameter_schema.side_effects` | Enumerated set; must not be empty for `CONFIRM_REQUIRED`. |
| `expected_proof` | `proof_requirement` | Proof category the gate must capture. |
| `rollback_or_abort` | row metadata or class default | Explicit rollback path, abort token, or `NOT_APPLICABLE` with reason. |
| `source_provenance` | `source_file:source_symbol`, `evidence_path_or_command` | Provenance preserved end-to-end. |
| `palette_request_id` | UUID generated at handoff | Correlation id for evidence/audit logs. |
| `palette_index_row_hash` | SHA-256 of normalized row | Lets the gate verify the row hasn't drifted in flight. |

## 3. Field-By-Field Refusal Rules

The palette must refuse the handoff and re-route the row when:

| Refusal trigger | Re-route target | Reason |
| --- | --- | --- |
| `command` resolves to `UNKNOWN` | Unknown/Drift Queue | `COMMAND_UNRESOLVED` |
| Any `resolved_params.required` is `UNKNOWN` | Unknown/Drift Queue | `PARAM_UNRESOLVED` |
| Any `resolved_params.optional` default is `UNKNOWN` | Unknown/Drift Queue | `DEFAULT_UNKNOWN` |
| `cwd` is `UNKNOWN` or outside the current worktree | Unknown/Drift Queue | `CWD_UNRESOLVED` |
| `authority_domain == 'unknown / conflicting'` or `canonical_writer == UNKNOWN` | Unknown/Drift Queue | `AUTHORITY_CONFLICT` / `WRITER_UNKNOWN` |
| `safety_class == BLOCKED_IN_COCKPIT` | `ShowBlockedReason` | `BLOCKED_IN_COCKPIT` |
| `safety_class == UNKNOWN` | Unknown/Drift Queue | `UNKNOWN_CLASS` |
| `gate_tier` is `UNKNOWN`, `T0`, `T0i`, `TX`, or `TU` | route per state | non-executable tier |
| `side_effects == UNKNOWN` or empty for `CONFIRM_REQUIRED` | Unknown/Drift Queue | `SIDE_EFFECTS_UNKNOWN` |
| `expected_proof == UNKNOWN` | Unknown/Drift Queue | `PROOF_REQUIREMENT_UNKNOWN` |
| `rollback_or_abort` required by tier (T3, T4, T5, T6) and resolves to `UNKNOWN` | Unknown/Drift Queue | `ROLLBACK_UNKNOWN` |
| `cockpit_placement == Settings/Admin` | re-route via `OpenSettingsAdminRuntime` | placement override |
| `activation_status` is non-`ACTIVE` | per state (Drift Queue or `ShowBlockedReason`) | `NOT_ACTIVE` |
| `palette_index_row_hash` does not match the live index | re-render preview | `INDEX_DRIFT` |

## 4. Tier-Specific Handoff Notes

| Tier | Class meaning | Handoff specifics |
| --- | --- | --- |
| `T1` | Generated artifact | Output target required; preflight summary required. |
| `T2` | Config mutation | Effective-config diff or `UNKNOWN` flag. If diff cannot be derived, gate displays `UNKNOWN` and operator must explicitly accept (`SAFE_ACTION_GATE_SPEC.md` §1). |
| `T3` | Write local | Path and side-effect class required. Rollback path explicit or block. |
| `T4` | Write remote | Remote target, account/context, idempotency required. Block by default until remote-mutation policy approves (`SAFE_ACTION_GATE_SPEC.md` §1 row T4). |
| `T5` | Start/stop service | Pre-state snapshot required; revert path explicit. |
| `T6` | Execution handoff | TP id, runner, cwd, branch, output/proof target required. TP gate must be present. |

## 5. The Gate Owns Execution

After a successful handoff, the palette is **out of the loop**. The Safe Action Gate:

- Displays the safety tier badge.
- Displays every required input or `UNKNOWN`.
- Demands an explicit confirm action (button + optional typed confirmation for T4/T6).
- Captures post-action proof per `proof_requirement`.
- Records evidence with `palette_request_id` for end-to-end audit.

The palette does not show a success state. The palette does not run any callback that mutates state.

## 6. Audit / Event Receipt

The handoff produces a receipt the evidence stream captures:

- `palette_request_id`
- `palette_index_row_hash`
- timestamp (UTC)
- selected row `command_path`, `authority_domain`, `gate_tier`
- handoff outcome (`accepted`, `refused`, `rerouted`)
- refusal reason (if any)
- target gate tier
- target proof requirement

The receipt is recorded regardless of whether the gate later confirms or aborts.

## 7. Forbidden In This Handoff

- Bypassing the gate by issuing the command directly.
- Sending an `UNKNOWN` field instead of refusing.
- Auto-confirming on behalf of the operator.
- Sending a `BLOCKED_IN_COCKPIT` row.
- Sending a row with non-`ACTIVE` activation.
- Sending a row whose `cockpit_placement` is `Settings/Admin` (must go through Settings/Admin/Runtime first).
- Substituting the worktree path with `/tmp` or any other authoritative path.
- Reusing a stale `palette_index_row_hash`.

## 8. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
