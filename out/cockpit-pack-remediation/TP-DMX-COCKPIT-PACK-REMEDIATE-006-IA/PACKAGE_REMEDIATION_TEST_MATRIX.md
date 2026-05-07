# Package Remediation Test Matrix

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)
**safe_for_claude_design:** NO
**READY_FOR_CLAUDE_DESIGN:** not approved

This file enumerates the contract-level test cases the package remediation must satisfy. Tests span the IA, Command Palette, Safe Action Gate, Settings/Admin/Runtime, and Unknown/Drift Queue. The test catalog is normative; the runtime renderer (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) implements and runs them. **No runtime tests are run inside this packet.**

## 1. Test Identity Conventions

- Test IDs follow `PRMR-<DOMAIN>-<NN>` where DOMAIN ∈ {IA, PAL, GATE, SETT, DRFT, INTG, BLOK}.
- Each test specifies inputs, expected behavior, and observable outcome.

## 2. IA Tests (PRMR-IA-*)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-IA-01` | Render exactly five top-level modes (PM, Implementer, Overview, Services, Events). | No sixth top-level mode rendered. |
| `PRMR-IA-02` | Render the four secondary surfaces. | Command Palette, Settings/Admin/Runtime, Safe Actions/Proof Gate, Unknown/Drift Queue all reachable; none promoted to top-level. |
| `PRMR-IA-03` | Honor `SCREEN_CONTRACT_MATRIX.md` per-screen allowed/forbidden classes. | A `BLOCKED_IN_COCKPIT` row never appears in PM/Implementer/Services/Events as executable. |
| `PRMR-IA-04` | Preserve authority boundaries. | No mode collapses ConPort, dope-memory, dope-context, or dopecon-bridge into a single control brain. |
| `PRMR-IA-05` | Inventory counts match carried `metadata.source_counts`. | Counts of safety classes, placements, activations, coverage, authority match upstream. |
| `PRMR-IA-06` | `safe_for_claude_design: NO` and `READY_FOR_CLAUDE_DESIGN: not approved` preserved everywhere. | Header state preserved across all packet artifacts. |

## 3. Command Palette Tests (PRMR-PAL-*)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-PAL-01` | Index every row with the 16 fields per `COMMAND_PALETTE_INDEX_SCHEMA.json`. | All rows complete; missing fields render `UNKNOWN` literally. |
| `PRMR-PAL-02` | Apply RV-1..RV-11 row validation. | Invalid rows fail validation and route to Unknown/Drift Queue. |
| `PRMR-PAL-03` | Apply R-1..R-9 routing in order. | First firing rule terminates; outcomes match expected per row class/placement/activation. |
| `PRMR-PAL-04` | `BLOCKED_IN_COCKPIT` row selected. | Routes to `ShowBlockedReason`; never reaches gate. |
| `PRMR-PAL-05` | `UNKNOWN` row selected. | Routes to Unknown/Drift Queue (`ShowUnknownDriftReason`); never reaches gate. |
| `PRMR-PAL-06` | `EXTERNAL_ONLY` row selected. | Allowed outcomes restricted to `Inspect`/`CopyCommand`; no execution path. |
| `PRMR-PAL-07` | `Settings/Admin` placement row selected. | Routes to `OpenSettingsAdminRuntime`; never bypasses Settings/Admin/Runtime. |
| `PRMR-PAL-08` | Required parameter unresolved. | Routes to Unknown/Drift Queue with `PARAM_UNRESOLVED`. |
| `PRMR-PAL-09` | `palette_index_row_hash` mismatch with current index. | `INDEX_DRIFT`; re-render preview before allowing handoff. |
| `PRMR-PAL-10` | Routing receipt emitted for every outcome. | Receipt schema per `PALETTE_PROOF_REQUIREMENTS.md` §3. |
| `PRMR-PAL-11` | Palette never executes. | All routes go through gate / surface / queue / inspect / copy; no inline execution. |

## 4. Safe Action Gate Tests (PRMR-GATE-*)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-GATE-01` | Tier carried verbatim from upstream surface. | No reclassification inside the gate. |
| `PRMR-GATE-02` | `gate_open` event/receipt emitted for every invocation. | Append-only; UTC; with `gate_request_id` and `palette_request_id` (when applicable). |
| `PRMR-GATE-03` | T0 row reaches gate. | Refused with `NON_EXECUTABLE_TIER`. |
| `PRMR-GATE-04` | T0i row with all preflight fields. | Confirm affordance enabled (explicit invoke); proof captured = command path + exit/result + source authority. |
| `PRMR-GATE-05` | T1 row with `output_target_path` UNKNOWN. | Confirm disabled; refusal `PROOF_TARGET_UNKNOWN`. |
| `PRMR-GATE-06` | T2 row with derivable diff. | Diff displayed; confirm disabled until acknowledged. |
| `PRMR-GATE-07` | T2 row with UNKNOWN diff and operator accepts. | `gate_confirmed` with `diff_acknowledged: unknown_diff_accepted`. |
| `PRMR-GATE-08` | T3 destructive write with no rollback. | Refusal `ROLLBACK_UNKNOWN`. |
| `PRMR-GATE-09` | T4 row without remote-mutation policy. | Refusal `REMOTE_MUTATION_POLICY_MISSING`. |
| `PRMR-GATE-10` | T4 row with policy and correct typed confirmation. | `gate_confirmed` with `typed_confirmation_match: true`. **No T4 execution in this packet.** |
| `PRMR-GATE-11` | T5 row with typed service-id mismatch. | Confirm stays disabled; mismatch state. |
| `PRMR-GATE-12` | T5 row confirms; runtime emits status + log. | `gate_proof_captured` with `SERVICE_STATUS_AND_LOG`. |
| `PRMR-GATE-13` | T6 row without TP gate. | Refusal `TP_GATE_ABSENT`. |
| `PRMR-GATE-14` | T6 row with typed TP-id and runner. | `gate_confirmed`; `gate_proof_captured` with `TP_RUNNER_PROOF`. |
| `PRMR-GATE-15` | TX row reaches gate (misroute). | Refusal `BLOCKED_IN_COCKPIT`; route to `ShowBlockedReason`. |
| `PRMR-GATE-16` | TU row reaches gate. | Refusal `UNKNOWN_CLASS`; route to Unknown/Drift Queue. |
| `PRMR-GATE-17` | Operator aborts mid-flow. | `gate_abort` emitted; no execution. |
| `PRMR-GATE-18` | Confirm flow exceeds timeout. | `gate_timeout` emitted; no execution. |
| `PRMR-GATE-19` | Stale proof tagged after confirmation. | `gate_proof_stale`; route to Unknown/Drift Queue. |
| `PRMR-GATE-20` | Gate invoked via deep-link bypassing surface. | Refusal `UNSAFE_SOURCE_SURFACE`. |
| `PRMR-GATE-21` | Auto-confirm attempt. | Refusal; gate never auto-confirms. |
| `PRMR-GATE-22` | Receipts contain no secrets. | Tokens, passwords, PII redacted. |
| `PRMR-GATE-23` | `gate_request_id` unique per invocation. | No reuse across distinct invocations. |
| `PRMR-GATE-24` | Receipts append-only. | No edit/delete observed. |
| `PRMR-GATE-25` | Authority drift mid-flow. | Refusal `AUTHORITY_DRIFT_MID_FLOW`. |
| `PRMR-GATE-26` | Class drift mid-flow. | Refusal `CLASS_DRIFT_MID_FLOW`; block until reclassified by packet. |

## 5. Settings/Admin/Runtime Tests (PRMR-SETT-*)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-SETT-01` | Palette routes a `Settings/Admin` placement row. | Routes to `OpenSettingsAdminRuntime`; never bypasses surface. |
| `PRMR-SETT-02` | Settings surface lands operator on correct flow group. | `flow_group` derived from `parent_group`/`command_path`. |
| `PRMR-SETT-03` | Surface invokes the gate from admin confirm step. | `surface_origin: SETTINGS_ADMIN_RUNTIME` recorded on gate event/receipt. |
| `PRMR-SETT-04` | T2 config mutation in Routing flow group. | Effective config diff displayed; confirm disabled until acknowledged. |
| `PRMR-SETT-05` | T5 service start in Service Startup flow group. | Pre-state snapshot captured; typed service-id confirmation required. |
| `PRMR-SETT-06` | `BLOCKED_IN_COCKPIT` row at admin surface. | Cannot execute; remains visible as blocked. |
| `PRMR-SETT-07` | `UNKNOWN` row at admin surface. | Cannot execute; routes to Unknown/Drift Queue. |
| `PRMR-SETT-08` | `flow_group` cannot be derived. | Refusal `FLOW_GROUP_UNKNOWN`; route to Unknown/Drift Queue. |
| `PRMR-SETT-09` | Admin row added to primary mode bar. | Forbidden by spec; package remediation must reject. |

## 6. Unknown/Drift Queue Tests (PRMR-DRFT-*)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-DRFT-01` | UNKNOWN row routed from Palette. | Appears in queue with all required per-row fields per `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4. |
| `PRMR-DRFT-02` | DEFINED_NOT_REGISTERED row. | Appears in queue; `Inspect`/`CopyCommand` may be allowed for documentation; no execute. |
| `PRMR-DRFT-03` | OPTIONAL_IMPORT_UNKNOWN row. | Appears in queue; no execute. |
| `PRMR-DRFT-04` | Conflicting authority row. | Appears in queue with `AUTHORITY_CONFLICT`; no execute. |
| `PRMR-DRFT-05` | Stale proof row. | Appears in queue with `stale_proof` badge; auto-retry forbidden. |
| `PRMR-DRFT-06` | Operator attempts in-queue reclassification. | Forbidden; reclassification requires a packet. |
| `PRMR-DRFT-07` | Operator attempts copy-as-run from queue. | Forbidden. |
| `PRMR-DRFT-08` | Queue reachable from Overview drift summary. | Visible. |
| `PRMR-DRFT-09` | Queue reachable from Palette filter `status:UNKNOWN`. | Visible. |
| `PRMR-DRFT-10` | Queue reachable from Settings/Admin/Runtime as read-only inspector. | Visible. |
| `PRMR-DRFT-11` | `BLOCKED_IN_COCKPIT` row visible in queue. | Visible (visibility-only); also routed to `ShowBlockedReason`. |

## 7. Integration Tests (PRMR-INTG-*)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-INTG-01` | Palette `OpenSafeActionGate` ⇒ gate ⇒ runtime authority. | End-to-end correlation: `palette_request_id` ⇒ `gate_request_id` ⇒ proof `gate_proof_captured`. |
| `PRMR-INTG-02` | Palette `OpenSettingsAdminRuntime` ⇒ Settings/Admin/Runtime ⇒ gate ⇒ runtime authority. | `surface_origin: SETTINGS_ADMIN_RUNTIME`; correlation preserved. |
| `PRMR-INTG-03` | Palette `ShowBlockedReason` for TX row. | Gate not invoked; originating surface displays blocked state. |
| `PRMR-INTG-04` | Palette `ShowUnknownDriftReason` for TU row. | Gate not invoked; Unknown/Drift Queue displays unknown state. |
| `PRMR-INTG-05` | Carried inventory invariants honored. | Counts of T0/T0i/T1–T6/TX/TU consistent with `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`. |
| `PRMR-INTG-06` | Refusal correlation. | Refusal events from gate carry `palette_request_id` when applicable; receipts in same evidence stream. |
| `PRMR-INTG-07` | Stale proof correlation. | `gate_proof_stale` references prior `gate_request_id`; routed to Unknown/Drift Queue. |

## 8. Blocked / Forbidden Tests (PRMR-BLOK-*)

These tests verify that the package never claims forbidden states. They run as grep checks over the package artifacts and as runtime validation. The literal forbidden claim strings are intentionally **not** reproduced in this matrix; the verify-step grep in this packet's PROOF/commit verification searches for the literal strings, and reproducing them here would create false positives.

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `PRMR-BLOK-01` | Verify grep finds no positive claim that flips `READY_FOR_CLAUDE_DESIGN` to the [APPROVED-CLAIM] value. | Not found. |
| `PRMR-BLOK-02` | Verify grep finds no positive claim that flips `safe_for_claude_design` to the [YES-CLAIM] value. | Not found. |
| `PRMR-BLOK-03` | Verify grep finds no positive claim that Claude Design upload is [PERMITTED-CLAIM]. | Not found. |
| `PRMR-BLOK-04` | Verify grep finds no positive claim that T4 is [AUTHORIZED-CLAIM]. | Not found. |
| `PRMR-BLOK-05` | Verify grep finds no positive claim that runtime execution is [IMPLEMENTED-CLAIM]. | Not found. |
| `PRMR-BLOK-06` | Final screens approved anywhere in this packet. | Not approved; explicit forbiddance preserved. |
| `PRMR-BLOK-07` | Sixth top-level mode introduced. | Not introduced. |
| `PRMR-BLOK-08` | T4 execution attempted in this packet. | Not attempted. |
| `PRMR-BLOK-09` | TX or TU row promoted to executable inside any artifact. | Not promoted. |
| `PRMR-BLOK-10` | Authority domains collapsed into a single control brain. | Not collapsed. |

The sentinel tokens above ([APPROVED-CLAIM], [YES-CLAIM], [PERMITTED-CLAIM], [AUTHORIZED-CLAIM], [IMPLEMENTED-CLAIM]) are stand-ins for the literal forbidden claim strings the verify-step grep looks for. Any artifact in this packet that contains the literal forbidden strings would fail the verify step.

## 9. No Runtime Tests Run In This Packet

This file is a contract test catalog. The runtime renderer packet (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) implements the runtime behaviors and runs the test matrix as part of its validation. The Palette and Safe Action Gate packets contain their own contract test matrices; this matrix sits at the **package** level and integrates them.

## 10. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TEST_MATRIX.md`
