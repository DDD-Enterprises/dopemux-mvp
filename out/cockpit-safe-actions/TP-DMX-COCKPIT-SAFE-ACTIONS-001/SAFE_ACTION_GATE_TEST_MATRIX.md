# Safe Action Gate Test Matrix

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file enumerates the test cases the Safe Action Gate contract must satisfy. The matrix is normative; the runtime renderer packet (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) implements the runtime behavior these tests will validate. **No runtime tests are run inside this packet** — this is a contract test catalog.

## 1. Test Identity Conventions

- Test IDs follow the form `SAGT-<TIER>-<CATEGORY>-<NN>` (e.g., `SAGT-T6-CONFIRM-01`).
- Categories: `OPEN`, `PREFLIGHT`, `CONFIRM`, `REFUSE`, `PROOF`, `RECEIPT`, `UI`, `ROUTING`, `DRIFT`, `STALE`, `TYPED`, `INTEGRATION`.
- Each test specifies inputs, expected gate behavior, and expected receipt event(s).

## 2. T0 — DISPLAY_ONLY

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T0-OPEN-01` | T0 row reaches gate (atypical; T0 normally does not invoke gate). | Gate refuses with reason `NON_EXECUTABLE_TIER`; routes back to inspect/display surface. | `gate_refuse` |
| `SAGT-T0-UI-01` | T0 displayed contextually with source authority. | Source authority + view timestamp captured at view time. No confirm affordance rendered. | n/a (display-time provenance only) |

## 3. T0i — INSPECT_ACTION

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T0i-OPEN-01` | T0i row arrives with all required fields. | Preflight panel renders; `Run inspection` affordance enabled. | `gate_open` |
| `SAGT-T0i-OPEN-02` | T0i row arrives with `command == UNKNOWN`. | Preflight panel renders with missing-field row; affordance disabled. | `gate_open`, `gate_refuse` (`COMMAND_UNRESOLVED`) |
| `SAGT-T0i-CONFIRM-01` | Operator clicks `Run inspection`. | Gate emits invoke event/receipt; runtime returns inspect result; gate captures proof (command path + result + source authority). | `gate_open`, `gate_confirmed`, `gate_proof_captured` |
| `SAGT-T0i-REFUSE-01` | Activation status `DEFINED_NOT_REGISTERED`. | Gate refuses with `NOT_ACTIVE`; routes to Unknown/Drift Queue. | `gate_open`, `gate_refuse` (`NOT_ACTIVE`) |

## 4. T1 — Generated artifact

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T1-OPEN-01` | T1 row arrives with `output_target_path` resolved. | Preflight renders with output path and overwrite behavior. | `gate_open` |
| `SAGT-T1-PREFLIGHT-01` | `output_target_path == UNKNOWN`. | Confirm disabled; refusal `PROOF_TARGET_UNKNOWN` (or T1-specific output target reason); route to Unknown/Drift Queue. | `gate_open`, `gate_refuse` |
| `SAGT-T1-PREFLIGHT-02` | `overwrite_behavior == UNKNOWN` and output exists. | Confirm disabled; refusal at preflight. | `gate_open`, `gate_refuse` |
| `SAGT-T1-CONFIRM-01` | Operator confirms; runtime generates artifact. | Gate captures `ARTIFACT_AND_CHECKSUM` proof. | `gate_open`, `gate_confirmed`, `gate_proof_captured` |
| `SAGT-T1-PROOF-01` | Runtime returns without artifact path. | Proof incomplete; row tagged `STALE_PROOF`; routes to queue. | `gate_open`, `gate_confirmed`, `gate_proof_incomplete` |

## 5. T2 — Config mutation

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T2-OPEN-01` | T2 row arrives with derivable diff. | Preflight renders before/after diff; confirm disabled until diff scrolled/expanded. | `gate_open` |
| `SAGT-T2-OPEN-02` | T2 row arrives with `effective_config_diff == UNKNOWN`. | Preflight renders `UNKNOWN diff` warning; operator must explicitly toggle `Accept UNKNOWN diff` before confirm enables. | `gate_open` |
| `SAGT-T2-PREFLIGHT-01` | `config_target_file_or_service == UNKNOWN`. | Confirm disabled; refusal at preflight. | `gate_open`, `gate_refuse` |
| `SAGT-T2-CONFIRM-01` | Operator scrolls diff and confirms. | Gate emits `gate_confirmed` with `diff_acknowledged: diff`. | `gate_open`, `gate_confirmed` |
| `SAGT-T2-CONFIRM-02` | Operator accepts `UNKNOWN diff` and confirms. | Gate emits `gate_confirmed` with `diff_acknowledged: unknown_diff_accepted`. | `gate_open`, `gate_confirmed` |
| `SAGT-T2-PROOF-01` | Runtime returns config diff and exit code. | Gate captures `CONFIG_DIFF_OR_STATUS` proof. | `gate_open`, `gate_confirmed`, `gate_proof_captured` |

## 6. T3 — Write local

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T3-OPEN-01` | T3 row arrives with `write_target_path` inside worktree. | Preflight renders; confirm enabled. | `gate_open` |
| `SAGT-T3-PREFLIGHT-01` | `write_target_path` outside worktree. | Refusal `CWD_OUT_OF_WORKTREE`. | `gate_open`, `gate_refuse` |
| `SAGT-T3-PREFLIGHT-02` | Destructive write (`replace file`) with `rollback_or_abort == UNKNOWN`. | Confirm disabled; refusal `ROLLBACK_UNKNOWN`. | `gate_open`, `gate_refuse` |
| `SAGT-T3-PREFLIGHT-03` | `worktree_metadata.dirty == true` and tier requires clean. | Refusal `WORKTREE_DIRTY`. | `gate_open`, `gate_refuse` |
| `SAGT-T3-CONFIRM-01` | Operator confirms; runtime writes file. | Gate captures filesystem path + verb + result + exit code. | `gate_open`, `gate_confirmed`, `gate_proof_captured` |

## 7. T4 — Write remote

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T4-OPEN-01` | T4 row arrives without `remote_mutation_policy_reference`. | Refusal `REMOTE_MUTATION_POLICY_MISSING`; route to queue. | `gate_open`, `gate_refuse` |
| `SAGT-T4-OPEN-02` | T4 row arrives with policy reference but row not approved. | Refusal `REMOTE_MUTATION_POLICY_NOT_APPROVED`. | `gate_open`, `gate_refuse` |
| `SAGT-T4-OPEN-03` | T4 row arrives with all fields and approved policy. | Preflight renders; typed confirmation field shown; confirm disabled. | `gate_open` |
| `SAGT-T4-TYPED-01` | Operator types incorrect endpoint identifier. | Confirm stays disabled; mismatch state shown; on attempt, refusal `TYPED_CONFIRMATION_MISMATCH`. | `gate_open`, `gate_refuse` |
| `SAGT-T4-TYPED-02` | Operator types correct identifier. | Confirm enables; click confirms; gate emits `gate_confirmed` with `typed_confirmation_match: true`. | `gate_open`, `gate_confirmed` |
| `SAGT-T4-PROOF-01` | Runtime returns remote receipt. | Gate captures `REMOTE_RECEIPT` proof. | `gate_open`, `gate_confirmed`, `gate_proof_captured` |
| `SAGT-T4-PROOF-02` | Remote call fails; receipt absent. | Proof incomplete; route to queue. | `gate_open`, `gate_confirmed`, `gate_proof_incomplete` |
| `SAGT-T4-INTEGRATION-01` | T4 attempted in this packet (contract-only). | Gate refuses with reason: T4 execution out of scope this packet. | `gate_open`, `gate_refuse` |

## 8. T5 — Start/stop service

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T5-OPEN-01` | T5 row arrives with `service_id`, `pre_state_snapshot`, `expected_state_transition`, revert path. | Preflight renders; typed confirmation field shown. | `gate_open` |
| `SAGT-T5-PREFLIGHT-01` | `service_id == UNKNOWN`. | Refusal `SERVICE_ID_UNKNOWN`. | `gate_open`, `gate_refuse` |
| `SAGT-T5-PREFLIGHT-02` | `pre_state_snapshot == UNKNOWN`. | Refusal `PRE_STATE_SNAPSHOT_MISSING`. | `gate_open`, `gate_refuse` |
| `SAGT-T5-TYPED-01` | Operator types incorrect service id. | Confirm stays disabled; mismatch state. | n/a |
| `SAGT-T5-TYPED-02` | Operator types correct service id. | Confirm enables. | `gate_open` |
| `SAGT-T5-CONFIRM-01` | Operator confirms; runtime transitions state. | Gate captures `SERVICE_STATUS_AND_LOG` proof. | `gate_open`, `gate_confirmed`, `gate_proof_captured` |

## 9. T6 — Execution handoff

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-T6-OPEN-01` | T6 row arrives with `tp_or_task_id`, `runner_id`, `branch`, `output_or_proof_target`, `tp_gate_present == true`. | Preflight renders; typed confirmation field shown. | `gate_open` |
| `SAGT-T6-PREFLIGHT-01` | `tp_gate_present == false`. | Refusal `TP_GATE_ABSENT`. | `gate_open`, `gate_refuse` |
| `SAGT-T6-PREFLIGHT-02` | `runner_id == UNKNOWN`. | Refusal `RUNNER_ID_UNKNOWN`. | `gate_open`, `gate_refuse` |
| `SAGT-T6-TYPED-01` | Operator types incorrect TP id. | Confirm stays disabled. | n/a |
| `SAGT-T6-TYPED-02` | Operator types correct TP id. | Confirm enables. | `gate_open` |
| `SAGT-T6-CONFIRM-01` | Operator confirms; runner accepts handoff. | Gate emits `gate_confirmed`; awaits proof. | `gate_open`, `gate_confirmed` |
| `SAGT-T6-PROOF-01` | Runner emits exit code + proof path + validation summary. | Gate captures `TP_RUNNER_PROOF`. | `gate_open`, `gate_confirmed`, `gate_proof_captured` |
| `SAGT-T6-PROOF-02` | Runner does not emit proof. | Proof incomplete; row tagged `STALE_PROOF`. | `gate_open`, `gate_confirmed`, `gate_proof_incomplete` |
| `SAGT-T6-PROOF-03` | Proof expires (stale window passes). | Row tagged `STALE_PROOF`; routes to queue. | `gate_proof_stale` |

## 10. TX — Blocked

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-TX-OPEN-01` | TX row reaches gate (misroute scenario). | Refusal `BLOCKED_IN_COCKPIT`; routes to `ShowBlockedReason` at originating surface. | `gate_open`, `gate_refuse` |
| `SAGT-TX-UI-01` | Originating surface displays blocked state with reason + replacement. | No confirm affordance ever rendered. | n/a |
| `SAGT-TX-REFUSE-01` | Operator attempts to copy-as-run a TX row. | Forbidden; refused; logged in originating surface as `CLIPBOARD_BLOCKED`. | n/a (handled at surface) |

## 11. TU — Unknown

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-TU-OPEN-01` | TU row reaches gate (misroute scenario). | Refusal `UNKNOWN_CLASS`; routes to Unknown/Drift Queue. | `gate_open`, `gate_refuse` |
| `SAGT-TU-UI-01` | Unknown/Drift Queue displays unknown_reason + required_investigation_packet. | No confirm affordance. | n/a |
| `SAGT-TU-REFUSE-01` | Operator attempts in-gate reclassification. | Forbidden; gate refuses with reason: reclassification requires a packet. | n/a |

## 12. Drift, Stale, And Origin Tests

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-DRIFT-01` | `palette_index_row_hash` mismatch with current index. | Refusal `INDEX_DRIFT`; route back to upstream surface for re-render. | `gate_open`, `gate_refuse` |
| `SAGT-DRIFT-02` | Authority resolution lost mid-flow. | Refusal `AUTHORITY_DRIFT_MID_FLOW`; route to queue. | `gate_open`, `gate_refuse` |
| `SAGT-DRIFT-03` | Class drift between handoff and confirm. | Refusal `CLASS_DRIFT_MID_FLOW`; block until reclassified by packet. | `gate_open`, `gate_refuse` |
| `SAGT-STALE-01` | `created_at_utc` older than configured stale window. | Refusal `STALE_HANDOFF`; route to upstream surface for re-issue. | `gate_open`, `gate_refuse` |
| `SAGT-STALE-02` | Runtime reports stale proof on a previously confirmed row. | `gate_proof_stale` event; route to queue with `stale_proof` badge. | `gate_proof_stale` |
| `SAGT-ORIGIN-01` | Gate invoked via deep-link bypassing surface. | Refusal `UNSAFE_SOURCE_SURFACE`; route to queue. | `gate_open`, `gate_refuse` |
| `SAGT-ORIGIN-02` | Gate invoked from `COMMAND_PALETTE` with valid handoff payload. | Preflight renders; confirm flow proceeds per tier. | `gate_open` |

## 13. Receipt And Audit Tests

| Test ID | Scenario | Expected behavior | Receipt(s) |
| --- | --- | --- | --- |
| `SAGT-RECEIPT-01` | Every gate invocation emits a `gate_open` event. | One `gate_open` per `gate_request_id`. | `gate_open` |
| `SAGT-RECEIPT-02` | Refusal emits a `gate_refuse` event. | Refusal reason and routing destination present. | `gate_refuse` |
| `SAGT-RECEIPT-03` | Confirm emits `gate_confirmed`; proof emits `gate_proof_captured`. | Two events for a successful run. | `gate_confirmed`, `gate_proof_captured` |
| `SAGT-RECEIPT-04` | Abort emits `gate_abort`. | Abort kind = `operator_aborted`. | `gate_abort` |
| `SAGT-RECEIPT-05` | Timeout emits `gate_timeout`. | Abort kind = `operator_timeout`. | `gate_timeout` |
| `SAGT-RECEIPT-06` | Receipts contain no secrets. | Tokens, passwords, PII redacted. | All event types |
| `SAGT-RECEIPT-07` | `gate_request_id` unique per invocation. | No reuse across distinct invocations. | All event types |
| `SAGT-RECEIPT-08` | Receipts append-only. | No edit or delete observed. | All event types |

## 14. UI Primitive Tests

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `SAGT-UI-01` | Preflight panel renders all required slots for the tier. | Every slot present; `UNKNOWN` rendered, never blank. |
| `SAGT-UI-02` | Authority and writer badges shown for every executable tier. | Visible and explicit. |
| `SAGT-UI-03` | Tier badge shown prominently. | Visible. |
| `SAGT-UI-04` | Confirm control disabled when any required field is `UNKNOWN`. | Disabled state visible. |
| `SAGT-UI-05` | Typed confirmation field reset on every gate-open. | No persisted state. |
| `SAGT-UI-06` | Refused state displays enumerated reason and routing destination. | Reason + routing visible. |
| `SAGT-UI-07` | Completed-with-proof state displays after proof captured. | All proof artifacts shown; UTC timestamps shown. |
| `SAGT-UI-08` | Stale-proof state displays after runtime tags stale. | Stale-proof badge + routing visible. |
| `SAGT-UI-09` | Blocked state never shows a confirm affordance. | Confirm absent. |
| `SAGT-UI-10` | Unknown state never shows a reclassification affordance. | Reclassify absent. |

## 15. Routing Tests

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `SAGT-ROUTING-01` | `BLOCKED_IN_COCKPIT` arriving at gate routes to `ShowBlockedReason` at originating surface. | Routing destination correct. |
| `SAGT-ROUTING-02` | `UNKNOWN` class routes to Unknown/Drift Queue. | Routing destination correct. |
| `SAGT-ROUTING-03` | `EXTERNAL_ONLY` routes to `Inspect`/`CopyCommand` only at originating surface. | No confirm affordance. |
| `SAGT-ROUTING-04` | T0 / T0i never reaches confirm flow. | Inspect-only. |
| `SAGT-ROUTING-05` | T4 with missing remote-mutation policy routes to queue. | Routing destination correct. |
| `SAGT-ROUTING-06` | Settings/Admin/Runtime row never bypasses Settings/Admin/Runtime to reach gate directly. | Surface origin = `SETTINGS_ADMIN_RUNTIME`. |
| `SAGT-ROUTING-07` | Stale proof routes to queue with `stale_proof` tag. | Routing destination correct. |

## 16. Integration Tests (Cross-Packet)

| Test ID | Scenario | Expected behavior |
| --- | --- | --- |
| `SAGT-INTEGRATION-01` | Palette `OpenSafeActionGate` ⇒ gate ⇒ runtime authority. | End-to-end correlation: `palette_request_id` ⇒ `gate_request_id` ⇒ proof `gate_proof_captured`. |
| `SAGT-INTEGRATION-02` | Palette `OpenSettingsAdminRuntime` ⇒ Settings/Admin/Runtime ⇒ gate ⇒ runtime authority. | Surface origin = `SETTINGS_ADMIN_RUNTIME`; correlation preserved. |
| `SAGT-INTEGRATION-03` | Palette `ShowBlockedReason` for TX row. | Gate not invoked; originating surface displays blocked state. |
| `SAGT-INTEGRATION-04` | Palette `ShowUnknownDriftReason` for TU row. | Gate not invoked; Unknown/Drift Queue displays unknown state. |
| `SAGT-INTEGRATION-05` | Carried inventory invariants honored. | Counts of T0/T0i/T1–T6/TX/TU consistent with `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`. |

## 17. No Runtime Tests Run In This Packet

This file is a contract test catalog. The runtime renderer packet (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) implements the runtime behaviors and runs the test matrix as part of its validation.

## 18. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
