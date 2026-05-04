# Settings / Admin / Runtime Package Handoff

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This file specifies the package-level handoff for the 62 Settings/Admin rows. Settings/Admin/Runtime is a **major secondary surface**, not a sixth top-level mode. The Palette routes admin/runtime rows here, the surface lands the operator on the correct flow group, and the surface invokes the Safe Action Gate. The Palette never bypasses Settings/Admin/Runtime for `cockpit_placement == Settings/Admin`.

## 1. Surface Role Recap

- **Major secondary surface**, not a sixth top-level mode (`SETTINGS_ADMIN_RUNTIME_SPEC.md` §1, §5).
- Hosts admin/governance flows that cannot be safely mixed into PM/Implementer/Services/Events home screens.
- Reachable from Overview, Services, and the Command Palette; never from PM, Implementer, or Events directly.
- Every action in this surface invokes the Safe Action Gate; no inline execution.

## 2. Flow Groups (Carried From Upstream)

Nine flow groups are normative (`SETTINGS_ADMIN_RUNTIME_SPEC.md` §2; `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §3):

| Flow group | Authority owner | Primary tier(s) | Confirmation strength | Typical proof |
| --- | --- | --- | --- | --- |
| Routing / Model Provider | routing/model-provider support (LiteLLM/CCR) | T2 | Explicit button + diff acknowledgment | `CONFIG_DIFF_OR_STATUS` |
| Profile management | dopemux operator control | T2 | Explicit button + diff acknowledgment | `CONFIG_DIFF_OR_STATUS` |
| Environment management | dopemux operator control | T2 | Explicit button + diff acknowledgment | `CONFIG_DIFF_OR_STATUS` |
| MCP server control | dopemux operator control + per-MCP authority | T2 (config) / T5 (start/stop) | Explicit button (T2) or typed service-id (T5) | `CONFIG_DIFF_OR_STATUS` / `SERVICE_STATUS_AND_LOG` |
| Service startup / lifecycle (admin) | per-service authority (Cockpit shows status only) | T5 | Explicit button + typed service-id | `SERVICE_STATUS_AND_LOG` |
| Hooks / native-hooks | dopemux operator control | T2 | Explicit button + diff acknowledgment | `CONFIG_DIFF_OR_STATUS` |
| Runtime configuration | dopemux operator control | T2 | Explicit button + diff acknowledgment | `CONFIG_DIFF_OR_STATUS` |
| Admin / safe / debug helpers | dopemux operator control | T0i / T2 / T5 (varies by row) | per tier | per tier |
| Drift inspection (read-only) | drift evidence (no execution) | T0 / T0i | None / explicit invoke | `INSPECT_RESULT_AND_TIMESTAMP` |

## 3. Handoff Sequence (Carried From Upstream)

1. Palette receives operator selection of a row whose `cockpit_placement == Settings/Admin` (or whose `parent_group` matches a flow group).
2. Palette validates the row per `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §1, §4.
3. Palette routes to `OpenSettingsAdminRuntime` per `PALETTE_ROUTING_RULES.md` §7 (R-7 Placement disambiguation).
4. Settings/Admin/Runtime opens at the correct flow group with the row's preview pre-populated (`PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §2 payload).
5. Operator confirms in Settings/Admin/Runtime.
6. Settings/Admin/Runtime invokes the Safe Action Gate with the same payload structure as `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 (the gate sees `surface_origin: SETTINGS_ADMIN_RUNTIME`).
7. Gate enforces preflight, confirmation, refusal, proof, event/receipt per its contract.
8. Runtime authority owner executes (out of scope this packet).
9. Gate captures proof and emits `gate_proof_captured` (or `gate_proof_incomplete` / `gate_proof_stale`).
10. Settings/Admin/Runtime displays the post-action evidence per its admin shell contract; final visual is **not** approved here.

## 4. Required Payload (Carried From Upstream)

The Palette → Settings/Admin/Runtime payload is normative (`PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §2):

- `flow_group` (one of the nine flow groups above).
- `command_path`.
- `proposed_resolved_params`.
- `cwd` (resolved against current worktree, never `/tmp`).
- `authority_domain`.
- `canonical_writer`.
- `safety_class`.
- `proposed_gate_tier`.
- `side_effects`.
- `expected_proof`.
- `source_provenance`.
- `palette_request_id`.
- `palette_index_row_hash`.

## 5. Refusal Rules At This Surface (Carried From Upstream)

The Palette refuses to route to Settings/Admin/Runtime and re-routes to Unknown/Drift Queue when (`PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §4):

- `flow_group` cannot be derived ⇒ `FLOW_GROUP_UNKNOWN`.
- `safety_class == BLOCKED_IN_COCKPIT` ⇒ route to `ShowBlockedReason` instead.
- `safety_class == UNKNOWN` ⇒ `UNKNOWN_CLASS`.
- `authority_domain == 'unknown / conflicting'` ⇒ `AUTHORITY_CONFLICT`.
- Required parameters resolve to UNKNOWN ⇒ `PARAM_UNRESOLVED`.
- `cwd` resolves to UNKNOWN ⇒ `CWD_UNRESOLVED`.
- `gate_tier` UNKNOWN or non-executable for an executable selection ⇒ `GATE_TIER_UNKNOWN`.
- `activation_status` non-`ACTIVE` ⇒ `NOT_ACTIVE`.

Settings/Admin/Runtime then enforces the Safe Action Gate's own refusal rules per `SAFE_ACTION_REFUSAL_RULES.md` once the gate is invoked from this surface.

## 6. Per-Flow-Group Tier Mapping (Package-Level)

The default mapping below is **INFERRED** from `SETTINGS_ADMIN_RUNTIME_SPEC.md` §4 + `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §3. **Per-row** mapping for the 62 rows is **UNKNOWN** at this packet's level and is owned by `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`.

| Flow group | Default executable tier | Inspect tier | Notes |
| --- | --- | --- | --- |
| Routing / Model Provider | T2 | T0i | Effective config preview required. |
| Profile management | T2 | T0i |  |
| Environment management | T2 | T0i |  |
| MCP server control (config) | T2 | T0i |  |
| MCP server control (start/stop) | T5 | T0i | Typed service-id required. |
| Service startup / lifecycle (admin) | T5 | T0i | Typed service-id required. |
| Hooks / native-hooks | T2 | T0i |  |
| Runtime configuration | T2 | T0i |  |
| Admin / safe / debug helpers | T0i / T2 / T5 (varies) | T0i | Per row. |
| Drift inspection (read-only) | n/a | T0 / T0i | Read-only inspector. |

**UNKNOWN at this packet level:** Per-row tier mapping for all 62 Settings/Admin rows beyond the seven executable flow groups. Owner: `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`.

## 7. UI Primitive Requirements (Package-Level)

Settings/Admin/Runtime must, at the primitive level (no final visuals approved here), render:

- A flow-group navigation primitive listing the nine flow groups.
- A row list primitive showing the rows belonging to the active flow group, with `authority_domain`, `canonical_writer`, `safety_class`, `gate_tier`, `coverage` badges, and `last_evidence_timestamp` when known.
- An admin confirmation primitive that wraps the gate's `Confirmation control` per `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §2.7.
- A read-only drift inspector primitive linking to the Unknown/Drift Queue.
- A blocked-row primitive that defers to the Safe Action Gate's `Blocked state` UI primitive (`SAFE_ACTION_GATE_UI_PRIMITIVES.md` §2.12).

These primitives are inputs to the Cockpit package remediation and the runtime renderer. **No final screens are approved here.**

## 8. Forbidden In This Surface (Carried From Upstream)

- Adding admin rows to the primary mode bar (`SETTINGS_ADMIN_RUNTIME_SPEC.md` §6).
- Mutating routing or environment without going through the Safe Action Gate.
- Implicit defaults that change runtime configuration on selection.
- Treating the surface as a PM or Implementer destination.
- Hiding `BLOCKED_IN_COCKPIT` admin rows; they remain visible as blocked rows.
- Bypassing Settings/Admin/Runtime by routing `cockpit_placement == Settings/Admin` rows directly to the Safe Action Gate.
- Auto-confirming inside Settings/Admin/Runtime from a palette selection.
- Sending parameters with `UNKNOWN` required fields.

## 9. Audit / Event Receipt

The Palette emits a routing receipt per `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §6 when it routes here. Settings/Admin/Runtime invokes the gate, which emits its own event/receipt per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md`. Both receipts share `palette_request_id` for end-to-end audit correlation.

## 10. Recommended Downstream Packet

`TP-DMX-COCKPIT-SETTINGS-RUNTIME-001` finalizes per-flow-group and per-row tier mapping for the 62 Settings/Admin rows, defines flow-group-specific UI primitives, and wires the surface against the runtime renderer. This packet does not authorize the runtime wiring; it documents the contract that the Settings/Runtime packet must satisfy.

## 11. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Settings/Admin`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md` §3, §7
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_CONTRACT.md` §3
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T2`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T5`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
