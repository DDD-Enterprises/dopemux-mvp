# Safe Action Gate Confirmation Flows

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the confirmation flow per tier. The flows are normative. The Safe Action Gate never auto-confirms, never collapses confirmation into selection, and never lets a `BLOCKED_IN_COCKPIT` or `UNKNOWN` row reach a confirm affordance. High-risk tiers (T4, T5, T6) require a typed confirmation token in addition to the explicit confirm button.

## 1. Common Confirmation Invariants (All Tiers)

- **Explicit invocation.** A confirm action requires an explicit affordance (button click, and for high-risk tiers a typed token). Hover, focus, double-click, drag, or keyboard shortcuts that bypass the surface are refused.
- **No auto-confirm.** The gate never auto-confirms based on prior selection, prior gate confirmation, "remember my choice", session state, or arrival via deep-link.
- **No silent default.** Optional parameters carry the explicit `was_default: true` flag. The gate displays each default value and the operator may change it before confirming.
- **No empty preflight.** Missing required fields render `UNKNOWN` and disable the confirm affordance.
- **No confirmation as proof.** Confirmation is the operator's intent to run, not proof that the action ran. Post-action proof is captured separately per `SAFE_ACTION_PROOF_REQUIREMENTS.md`.
- **Abort always available.** Until the runtime authority owner has accepted the handoff, the gate offers an explicit `Abort` affordance with no penalty.

## 2. Per-Tier Confirmation Flow

### 2.1 T0 — DISPLAY_ONLY (no confirmation; no execution)

- **Render:** Source authority + view timestamp.
- **Affordances:** None (no confirm, no inspect, no run).
- **End state:** Display captured by the originating surface; no gate event/receipt for execution.

### 2.2 T0i — INSPECT_ACTION (explicit invoke; no typed confirmation)

1. Operator selects `Inspect` outcome at the upstream surface (Palette `Inspect`, Settings/Admin/Runtime drift inspector, contextual inspect drawer).
2. Gate receives preflight payload; renders preflight panel:
   - Command path (resolved).
   - Resolved params (required + explicit defaults).
   - Cwd / worktree.
   - Authority domain + canonical writer.
   - Tier badge: `T0i INSPECT_ACTION`.
   - Side effects: `none` (or empty list for inspect).
   - Expected proof: `INSPECT_RESULT_AND_TIMESTAMP` or class-specific.
   - Source provenance.
3. Operator clicks `Run inspection` (explicit invoke).
4. Gate emits gate event/receipt with status `confirmed=invoke`.
5. Runtime authority returns inspect result (out of scope for this packet — `TP-DMX-COCKPIT-RUNTIME-RENDER-001`).
6. Gate captures proof: command path + exit/result summary + source authority. Updates gate event/receipt.

### 2.3 T1 — Generated artifact (explicit button confirmation)

1. Operator selects `OpenSafeActionGate` at upstream surface.
2. Gate renders preflight panel with all common fields plus T1-specific:
   - `output_target_path`.
   - `overwrite_behavior` (preserve, fail, overwrite-with-prompt).
3. Operator may edit optional parameter defaults.
4. Operator clicks `Confirm and generate`. (No typed confirmation required at T1.)
5. Gate emits gate event/receipt with status `confirmed`.
6. Runtime authority generates the artifact.
7. Gate captures proof: artifact path + checksum/summary, exit code if runner-invoked.

### 2.4 T2 — Config mutation (explicit button + diff acknowledgment)

1. Operator selects `OpenSafeActionGate` (palette) or admin confirm step (Settings/Admin/Runtime).
2. Gate renders preflight panel with T2-specific fields:
   - `config_target_file_or_service` (e.g., `~/.claude.json`, MCP server config).
   - `effective_config_diff_or_unknown_flag`.
3. Diff handling:
   - If diff is derivable: gate displays before/after diff. Operator must scroll through or expand the diff before the confirm button enables.
   - If diff is `UNKNOWN`: gate displays `UNKNOWN diff` warning. Operator must explicitly toggle `Accept UNKNOWN diff` before the confirm button enables. (No silent acceptance.)
4. Operator clicks `Confirm and apply`. (No typed confirmation required at T2 unless the underlying flow demands one.)
5. Gate emits gate event/receipt with status `confirmed` and a `diff_acknowledged` flag (`diff` or `unknown_diff_accepted`).
6. Runtime authority applies the config change.
7. Gate captures proof: config diff (or post-action status) + command exit code.

### 2.5 T3 — Write local (explicit button)

1. Operator selects `OpenSafeActionGate`.
2. Gate renders preflight panel with T3-specific fields:
   - `write_target_path`.
   - `side_effect_classification` (e.g., `create file`, `append file`, `delete file`, `replace file`).
   - Worktree dirty flag (if tier requires clean state, dirty fails closed).
3. If destructive (`delete file`, `replace file`): gate enforces presence of `rollback_or_abort` with a non-`UNKNOWN` value before enabling confirm.
4. Operator clicks `Confirm and write`. (No typed confirmation at T3 unless the underlying flow demands one.)
5. Gate emits gate event/receipt with status `confirmed`.
6. Runtime authority performs the write.
7. Gate captures proof: filesystem path + action verb + result + exit code.

### 2.6 T4 — Write remote (explicit button + typed confirmation; remote-mutation policy required)

1. Operator selects `OpenSafeActionGate`.
2. Gate validates `remote_mutation_policy_reference` is present and approved. If missing or not approved: refuse with reason `REMOTE_MUTATION_POLICY_MISSING`; route to Unknown/Drift Queue.
3. Gate renders preflight panel with T4-specific fields:
   - `remote_target_endpoint` (e.g., a fully resolved URL or service identifier).
   - `remote_account_or_context` (e.g., GitHub org, ConPort workspace, Slack workspace).
   - `idempotency_key` (or `NOT_APPLICABLE` with documented reason).
   - `remote_mutation_policy_reference` (e.g., `RFC-DMX-REMOTE-MUTATION-001`).
4. Gate displays the typed confirmation field. The operator must type the **endpoint identifier** (or a confirmation token specified by the policy) exactly. The confirm button stays disabled until the typed value matches.
5. Operator clicks `Confirm and call remote`.
6. Gate emits gate event/receipt with status `confirmed` and `typed_confirmation_match: true`.
7. Runtime authority issues the remote call.
8. Gate captures proof: remote endpoint + actor + status + response excerpt where governance allows.

**Note:** This packet does not implement T4 execution. T4 remains blocked by default in Cockpit until `TP-DMX-COCKPIT-RUNTIME-RENDER-001` and a remote-mutation policy approve it (`CLAUDE_DESIGN_BLOCKERS.md` §4).

### 2.7 T5 — Start/stop service (explicit button + typed service-id confirmation)

1. Operator selects `OpenSafeActionGate` (palette for service status), or `OpenSettingsAdminRuntime` (Settings/Admin/Runtime Service startup/lifecycle), and the surface invokes the gate.
2. Gate renders preflight panel with T5-specific fields:
   - `service_id`.
   - `service_scope` (e.g., local, container, host).
   - `expected_state_transition` (e.g., `stopped → running`, `running → stopped`).
   - `pre_state_snapshot` (current status before the action).
   - `rollback_or_abort` (revert path).
3. Gate displays the typed confirmation field. The operator must type the **service id** exactly. The confirm button stays disabled until the typed value matches.
4. Operator clicks `Confirm and start` or `Confirm and stop`.
5. Gate emits gate event/receipt with status `confirmed` and `typed_confirmation_match: true`.
6. Runtime authority transitions the service state.
7. Gate captures proof: post-state status + log excerpt + exit code.

### 2.8 T6 — Execution handoff (explicit button + typed TP id confirmation)

1. Operator selects `OpenSafeActionGate` for an execution-handoff row (Implementer/Palette).
2. Gate validates `tp_gate_present == true`. If missing: refuse with reason `TP_GATE_ABSENT`.
3. Gate renders preflight panel with T6-specific fields:
   - `tp_or_task_id`.
   - `runner_id`.
   - `branch`.
   - `cwd` (resolved against worktree).
   - `output_or_proof_target`.
   - `rollback_or_abort` (typically: abort allowed before runner starts; in-flight cancellation through runner authority).
4. Gate displays the typed confirmation field. The operator must type the **TP id** exactly. The confirm button stays disabled until the typed value matches.
5. Operator clicks `Confirm and run TP`.
6. Gate emits gate event/receipt with status `confirmed` and `typed_confirmation_match: true`.
7. Runtime authority hands off to runner.
8. Gate captures proof: exit code + proof path + validation summary.

### 2.9 TX — Blocked (no confirmation; never executes)

1. Operator selects a `BLOCKED_IN_COCKPIT` row at the upstream surface.
2. Upstream surface routes to `ShowBlockedReason`. The gate is **not** invoked for `TX`; the surface displays the blocked reason inline.
3. If the gate is somehow reached with `safety_class == BLOCKED_IN_COCKPIT` (e.g., misrouting): the gate refuses with reason `BLOCKED_IN_COCKPIT`, emits a refusal event/receipt, and routes back to the originating surface for blocked display.
4. **No confirm affordance is ever rendered for TX.** The gate's UI primitive set explicitly forbids this (`SAFE_ACTION_GATE_UI_PRIMITIVES.md`).

### 2.10 TU — Unknown (no confirmation; never executes)

1. Operator selects an `UNKNOWN` row at the upstream surface.
2. Upstream surface routes to `ShowUnknownDriftReason` (Unknown/Drift Queue).
3. If the gate is somehow reached with `safety_class == UNKNOWN`: the gate refuses with reason `UNKNOWN_CLASS`, emits a refusal event/receipt, and routes to the Unknown/Drift Queue.
4. **No confirm affordance is ever rendered for TU.**
5. **No reclassification inside the gate.** Reclassification requires a packet (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5).

## 3. Typed Confirmation Tokens (T4/T5/T6 Detail)

| Tier | Required typed value | Match rule | Refusal trigger |
| --- | --- | --- | --- |
| T4 | The remote endpoint identifier or the policy's confirmation token (whichever is more specific). | Case-sensitive exact match. | Mismatch ⇒ refuse with reason `TYPED_CONFIRMATION_MISMATCH`. |
| T5 | The `service_id` exactly. | Case-sensitive exact match. | Mismatch ⇒ refuse with reason `TYPED_CONFIRMATION_MISMATCH`. |
| T6 | The `tp_or_task_id` exactly. | Case-sensitive exact match. | Mismatch ⇒ refuse with reason `TYPED_CONFIRMATION_MISMATCH`. |

The gate displays the required token in the preflight panel as the source of truth. The operator types it; the gate compares; the confirm button enables only on match. The typed confirmation field is reset on every gate-open (no persisted state).

## 4. Confirmation Flow State Machine

```
[gate opened with payload]
        │
        ▼
[preflight rendered]
        │  any field UNKNOWN?
        ├──── yes ──► [refuse, route per SAFE_ACTION_REFUSAL_RULES.md]
        │
        no
        ▼
[tier-specific affordance set]
        │  blocked or unknown class?
        ├──── yes ──► [refuse, route per SAFE_ACTION_REFUSAL_RULES.md]
        │
        no
        ▼
[operator interacts]
        │  abort?
        ├──── yes ──► [emit abort event/receipt; return]
        │
        no
        ▼
[typed confirmation required (T4/T5/T6)?]
        │  yes
        ├──► [wait for typed match] ──► [enable confirm button]
        │
        no
        ▼
[operator clicks confirm]
        │
        ▼
[emit confirmed event/receipt; hand off to runtime authority]
        │
        ▼
[runtime authority executes (out of scope this packet)]
        │
        ▼
[gate captures post-action proof per SAFE_ACTION_PROOF_REQUIREMENTS.md]
        │
        ▼
[update gate event/receipt with proof status]
```

## 5. Refusal Behavior Inside Confirmation Flow

If at any point during the confirmation flow a previously-resolved field becomes `UNKNOWN` (e.g., index drift detected via stale `palette_index_row_hash`, worktree becomes dirty mid-flow, authority resolution lost), the gate refuses:

- The confirm affordance is disabled.
- The gate displays the refusal reason.
- The gate emits a refusal event/receipt.
- The action routes per `SAFE_ACTION_REFUSAL_RULES.md` (Unknown/Drift Queue or blocked display).

The operator never confirms an action that has lost a required field mid-flow.

## 6. Forbidden In Confirmation Flows

- Auto-confirm based on prior gate confirmation or session state.
- Confirm affordance enabled while any required field is `UNKNOWN`.
- Confirm affordance enabled before the typed confirmation field matches (T4/T5/T6).
- Confirm affordance rendered for `safety_class` in {`BLOCKED_IN_COCKPIT`, `UNKNOWN`, `EXTERNAL_ONLY`} or `gate_tier` in {`T0`, `TX`, `TU`}.
- Treating the upstream handoff as confirmation. The handoff is the candidate action; the operator confirms.
- Treating confirmation as proof of execution. Proof is captured post-execution.
- Skipping the diff acknowledgment in T2 with `UNKNOWN diff`.
- Persisting typed confirmation values across gate openings.
- Reusing a stale `palette_index_row_hash` to keep the confirm enabled.
- Routing a refused action silently (every refusal emits an event/receipt).

## 7. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §1, §5
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:classes`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md` §3, §4
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §3
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §4, §5
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
