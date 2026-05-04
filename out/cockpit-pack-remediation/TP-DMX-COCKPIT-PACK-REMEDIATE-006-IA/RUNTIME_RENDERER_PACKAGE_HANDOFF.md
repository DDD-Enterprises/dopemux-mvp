# Runtime Renderer Package Handoff

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This file specifies what the runtime renderer packet (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) may consume from this packet and what it must satisfy. **This packet does not authorize runtime execution.** It documents the contract the runtime renderer must satisfy and the boundaries it must not cross.

## 1. What The Runtime Renderer May Consume (Inputs)

The runtime renderer packet may treat the following as authoritative inputs (no rewriting; no re-interpretation):

### 1.1 IA & screen contracts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/RECONCILED_COCKPIT_IA.md` (five top-level modes; four secondary surfaces)
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md` and `.json` (per-screen owner, allowed/forbidden classes, gates, data sources, coverage)
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json` (seven safety classes; carried counts; allowed/forbidden UI forms)

### 1.2 Command Palette contract & schemas

- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_CONTRACT.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json` (16 fields; 11 row-validation rules)
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md` (R-1..R-9 routing algorithm)
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`

### 1.3 Safe Action Gate contract & schemas

- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_CONTRACT.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json` (ten tiers; required preflight; required proof; refusal conditions)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.json` (17 fields; tier-specific extensions)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_CONFIRMATION_FLOWS.md` (tier-specific flows; typed confirmation for T4/T5/T6)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md` (30+ enumerated refusal triggers)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PROOF_REQUIREMENTS.md` (per-tier proof artifacts)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md` (8 event types; receipt schema)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md` (13 primitives)
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TEST_MATRIX.md`

### 1.4 Settings/Admin/Runtime & Unknown/Drift Queue specs

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-pack-remediation/TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA/SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md`
- `out/cockpit-pack-remediation/TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA/UNKNOWN_DRIFT_PACKAGE_HANDOFF.md`

### 1.5 This packet's integration matrices

- `INTEGRATED_COCKPIT_IA_CONTRACT.md`
- `TOP_LEVEL_MODE_PACKAGE_MATRIX.md`
- `GLOBAL_SURFACE_PACKAGE_MATRIX.md`
- `COMMAND_TO_GATE_TO_SCREEN_MATRIX.md`
- `SAFE_ACTION_GATE_INTEGRATION_MATRIX.md`
- `PACKAGE_REMEDIATION_TEST_MATRIX.md`

## 2. What The Runtime Renderer Must Satisfy

### 2.1 IA Invariants

- Render exactly five top-level modes (PM, Implementer, Overview, Services, Events). No sixth top-level mode.
- Render the four secondary surfaces (Command Palette, Settings/Admin/Runtime, Safe Actions/Proof Gate, Unknown/Drift Queue) as global/secondary, never as top-level modes.
- Preserve authority boundaries per `RECONCILED_COCKPIT_IA.md` §9 and `COMMAND_PALETTE_CONTRACT.md` §8.
- Honor `SCREEN_CONTRACT_MATRIX.md` per-screen contracts (allowed/forbidden classes, gates, data sources).

### 2.2 Command Palette Invariants

- Implement R-1..R-9 routing in order; first rule that fires terminates.
- Index every row with the 16 fields in `COMMAND_PALETTE_INDEX_SCHEMA.json`.
- Enforce RV-1..RV-11 row validation.
- Render `UNKNOWN` literally for missing fields; never blank.
- Never execute; only route.
- Never bypass Settings/Admin/Runtime for `cockpit_placement == Settings/Admin`.

### 2.3 Safe Action Gate Invariants

- Carry the tier from the upstream surface; never reclassify.
- Render the preflight panel for every executable tier with all required fields per `SAFE_ACTION_PREFLIGHT_SCHEMA.json`.
- Disable confirm affordance when any required field is `UNKNOWN`.
- Require typed confirmation for T4/T5/T6 (matching `remote_target_endpoint`/`service_id`/`tp_or_task_id` exactly).
- Refuse per `SAFE_ACTION_REFUSAL_RULES.md`; emit `gate_refuse` event/receipt.
- Capture proof per `SAFE_ACTION_PROOF_REQUIREMENTS.md`; tag stale proof; route stale proof to Unknown/Drift Queue.
- Emit `gate_open`/`gate_refuse`/`gate_abort`/`gate_timeout`/`gate_confirmed`/`gate_proof_captured`/`gate_proof_incomplete`/`gate_proof_stale` events per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md`.
- Append-only receipts; UTC timestamps; secrets redacted.
- Block T4 by default until remote-mutation policy is in scope and approves.

### 2.4 Settings/Admin/Runtime Invariants

- Implement the nine flow groups per `SETTINGS_ADMIN_RUNTIME_SPEC.md` §2.
- Land the operator on the correct flow group from the Palette payload.
- Invoke the Safe Action Gate from within the surface; never bypass.
- Display drift inspection as read-only.

### 2.5 Unknown/Drift Queue Invariants

- Display every row with the per-row fields in `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4.
- Accept `palette_request_id` and `gate_request_id` correlation.
- Never offer execution.
- Never reclassify in place.
- Reachable from Overview, Palette filters, Settings/Admin/Runtime.

## 3. What The Runtime Renderer Must Decide / Configure (UNKNOWNs)

The runtime renderer packet owns these decisions because they require runtime context this packet cannot provide:

| UNKNOWN | Why this packet defers it |
| --- | --- |
| Stale-proof window duration. | Depends on per-class evidence retention policy and operator-tolerance signals; not specified by the carried IA. |
| Confirm-flow operator timeout duration. | Depends on accessibility and ADHD-tolerance settings; not specified by the carried IA. |
| Operator authentication / `operator_id` capture. | Depends on Cockpit auth wiring; not yet present (`CLAUDE_DESIGN_BLOCKERS.md` §3 condition 6). |
| Final visual treatment for tier badges, refusal panels, completed-with-proof states, stale-proof states. | Final visuals are blocked at the Claude Design boundary. |
| Per-row tier mapping for the 62 Settings/Admin rows. | Owned by `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`. |
| Remote-mutation policy reference (referenced by T4 preflight). | Owned by a separate policy artifact. |
| Per-keystroke shortcuts. | Owned by the Cockpit shell remediation packet. |
| Inventory regeneration counts. | Owned by a separate inventory-regeneration packet. |

## 4. What The Runtime Renderer Must Not Do

- Execute commands without the Safe Action Gate.
- Bypass Settings/Admin/Runtime for `cockpit_placement == Settings/Admin` rows.
- Reclassify any UNKNOWN row.
- Promote any BLOCKED row to executable.
- Auto-confirm any tier.
- Allow T4 execution without an approved remote-mutation policy.
- Substitute confirmation receipts for execution proof.
- Substitute preflight render evidence for execution proof.
- Persist typed confirmation values across gate openings.
- Hide the authority owner, canonical writer, safety class, side effects, or proof requirement.
- Render a sixth top-level mode.
- Promote any global surface to a top-level mode.
- Upload final screens to Claude Design without all eight unblock conditions in `CLAUDE_DESIGN_BLOCKERS.md` §3.

## 5. Test Inputs The Runtime Renderer Must Pass

The runtime renderer must pass the test matrices in:

- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TEST_MATRIX.md`
- `out/cockpit-pack-remediation/TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA/PACKAGE_REMEDIATION_TEST_MATRIX.md`

These test matrices are normative; the runtime renderer is responsible for runtime validation.

## 6. Runtime Authority Owner Per Tier (Reference)

The gate hands off to the runtime authority owner identified by `canonical_writer` after a successful confirm. The runtime authority owner emits the proof event the gate captures. The mapping from `canonical_writer` (or comma-joined writers) to actual runtime calls is **owned by the runtime renderer packet**, not by this packet.

| Likely runtime authority owner | Likely tier(s) |
| --- | --- |
| Dopemux operator control (CLI / runtime / admin) | T2, T5 (admin), T0i |
| Dopetask execution handoff (TP runner) | T6, T1 (artifact emission) |
| Task-orchestrator workflow | T2/T6 for workflow transitions |
| ConPort | T2/T1 for decision/progress writes |
| Dope-memory chronicle | T1 chronicle artifact emission |
| Per-service authority (MCP server start/stop, Cockpit service start/stop) | T5 |
| External (e.g., GitHub, Slack) under remote-mutation policy | T4 (BLOCKED until policy approves) |

## 7. Source Artifacts

(See [PACKAGE_REMEDIATION_INDEX.md](PACKAGE_REMEDIATION_INDEX.md) §"Source Artifacts" for the full list.)
