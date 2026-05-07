# Safe Action Gate Integration Matrix

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This matrix integrates the Safe Action Gate per-tier behavior across the IA: which surfaces originate which tier, what preflight is required, what confirmation is required, what refusal triggers apply, what proof is captured, and what event/receipt is emitted. The matrix is normative for runtime renderer planning.

## 1. Per-Tier Integration

### 1.1 T0 — DISPLAY_ONLY

| Aspect | Value |
| --- | --- |
| Allowed origins | Read-only contextual surfaces (PM/Implementer/Overview/Services/Events display rows); Overview drift summary; Inspect drawer. |
| Preflight required | `command`, `authority_domain`, `safety_class`, `gate_tier`, `source_provenance`, `surface_origin`, `created_at_utc`. |
| Confirmation strength | None. |
| Refusal triggers | command resolves to UNKNOWN; authority unknown/conflicting; provenance missing. |
| Proof captured | `INSPECT_RESULT_AND_TIMESTAMP` at view time; source authority. |
| Event/receipt | `gate_open` (atypical for T0 reaching gate) ⇒ refuse with `NON_EXECUTABLE_TIER` if reached on confirm path. |
| Routing on refusal | Back to inspect/display surface. |

### 1.2 T0i — INSPECT_ACTION

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `Inspect` outcome; Settings/Admin/Runtime drift inspector; contextual inspect drawer. |
| Preflight required | `command`, `resolved_params`, `cwd`, `worktree_metadata`, `authority_domain`, `canonical_writer`, `safety_class`, `gate_tier`, `source_provenance`, `surface_origin`, `created_at_utc`, `palette_request_id` (when from palette), `operator_intent`. |
| Confirmation strength | Explicit invoke (operator clicks `Run inspection`). No defaults-on. |
| Refusal triggers | Required params UNKNOWN; cwd UNKNOWN/outside worktree; authority/writer UNKNOWN/conflicting; activation non-ACTIVE; stale palette index hash. |
| Proof captured | command path + exit/result summary + source authority. |
| Event/receipt | `gate_open` ⇒ `gate_confirmed: invoke` ⇒ `gate_proof_captured`. |
| Routing on refusal | Unknown/Drift Queue with the missing-field reason. |

### 1.3 T1 — Generated artifact

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `OpenSafeActionGate`; Implementer or Palette contextual surface action that produces an artifact. |
| Preflight required | All common executable preflight + `output_target_path`, `overwrite_behavior`. |
| Confirmation strength | Explicit confirm button. |
| Refusal triggers | Common executable + `output_target_path` UNKNOWN; `overwrite_behavior` UNKNOWN when output exists. |
| Proof captured | `ARTIFACT_AND_CHECKSUM` (artifact path, checksum/summary, exit code if runner-invoked). |
| Event/receipt | `gate_open` ⇒ `gate_confirmed` ⇒ `gate_proof_captured` (or `gate_proof_incomplete` if artifact missing). |
| Routing on refusal | Unknown/Drift Queue. |

### 1.4 T2 — Config mutation

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `OpenSafeActionGate`; Settings/Admin/Runtime flow groups (Routing, Profile, Env, MCP-config, Hooks/native-hooks, Runtime, Admin/safe/debug). |
| Preflight required | All common executable preflight + `config_target_file_or_service`, `effective_config_diff_or_unknown_flag`. |
| Confirmation strength | Explicit button + diff acknowledgment (`diff` or `unknown_diff_accepted`). |
| Refusal triggers | Common executable + config target UNKNOWN; UNKNOWN diff without explicit `unknown_diff_accepted`; rollback path UNKNOWN; rollback insufficient. |
| Proof captured | `CONFIG_DIFF_OR_STATUS` (config diff or before/after status; command exit code). |
| Event/receipt | `gate_open` ⇒ `gate_confirmed` (with `diff_acknowledged`) ⇒ `gate_proof_captured`. |
| Routing on refusal | Unknown/Drift Queue. |

### 1.5 T3 — Write local

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `OpenSafeActionGate`; contextual surface action that writes locally. |
| Preflight required | All common executable preflight + `write_target_path`, `side_effect_classification`. |
| Confirmation strength | Explicit confirm button. |
| Refusal triggers | Common executable + `write_target_path` UNKNOWN/outside worktree; `side_effect_classification` UNKNOWN; rollback UNKNOWN for destructive write; dirty worktree if tier requires clean. |
| Proof captured | `FILESYSTEM_DIFF_OR_EXIT_CODE` (filesystem path, action verb, result, exit code). |
| Event/receipt | `gate_open` ⇒ `gate_confirmed` ⇒ `gate_proof_captured`. |
| Routing on refusal | Unknown/Drift Queue. |

### 1.6 T4 — Write remote

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `OpenSafeActionGate` only when remote-mutation policy is in scope; Settings/Admin/Runtime only flows whose policy approves T4. |
| Preflight required | All common executable preflight + `remote_target_endpoint`, `remote_account_or_context`, `idempotency_key`, `remote_mutation_policy_reference`, `typed_confirmation`. |
| Confirmation strength | Explicit button + typed confirmation matching the endpoint identifier (or policy-specified token). |
| Refusal triggers | Common executable + `remote_mutation_policy_reference` missing or not approved; `remote_target_endpoint` UNKNOWN; `remote_account_or_context` UNKNOWN; `idempotency_key` UNKNOWN; typed confirmation mismatch. |
| Proof captured | `REMOTE_RECEIPT` (endpoint, actor, status, idempotency key echoed, response excerpt where governance allows). |
| Event/receipt | `gate_open` ⇒ `gate_confirmed` (with `typed_confirmation_match: true`) ⇒ `gate_proof_captured`. |
| Routing on refusal | Unknown/Drift Queue. |
| **Status** | **BLOCKED BY DEFAULT** until remote-mutation policy approves and runtime renderer wires it. **No T4 execution in this packet.** |

### 1.7 T5 — Start/stop service

| Aspect | Value |
| --- | --- |
| Allowed origins | Settings/Admin/Runtime Service startup/lifecycle (admin); Command Palette when placement is Services and confirmation flow allows. |
| Preflight required | All common executable preflight + `service_id`, `service_scope`, `expected_state_transition`, `pre_state_snapshot`, `typed_confirmation`. |
| Confirmation strength | Explicit button + typed service-id confirmation. |
| Refusal triggers | Common executable + `service_id` UNKNOWN; `pre_state_snapshot` missing; `expected_state_transition` UNKNOWN; revert path UNKNOWN; typed confirmation mismatch. |
| Proof captured | `SERVICE_STATUS_AND_LOG` (post-state status, log excerpt, exit code; pre-state echoed for delta). |
| Event/receipt | `gate_open` ⇒ `gate_confirmed` (with `typed_confirmation_match: true` and `service_id`) ⇒ `gate_proof_captured`. |
| Routing on refusal | Unknown/Drift Queue. |

### 1.8 T6 — Execution handoff

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `OpenSafeActionGate` for execution-handoff rows (Implementer/Palette); Implementer contextual surface that originates a TP run. |
| Preflight required | All common executable preflight + `tp_or_task_id`, `runner_id`, `branch`, `output_or_proof_target`, `tp_gate_present`, `typed_confirmation`. |
| Confirmation strength | Explicit button + typed TP-id confirmation. |
| Refusal triggers | Common executable + `tp_gate_present == false` (`TP_GATE_ABSENT`); `tp_or_task_id` UNKNOWN; `runner_id` UNKNOWN; `branch` UNKNOWN; `output_or_proof_target` UNKNOWN; typed confirmation mismatch. |
| Proof captured | `TP_RUNNER_PROOF` (exit code, proof path, validation summary; TP id, runner id, branch echoed). |
| Event/receipt | `gate_open` ⇒ `gate_confirmed` (with `typed_confirmation_match: true` and `tp_or_task_id`) ⇒ `gate_proof_captured` (or `gate_proof_incomplete`/`gate_proof_stale` later). |
| Routing on refusal | Unknown/Drift Queue. |

### 1.9 TX — Blocked

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `ShowBlockedReason`; Unknown/Drift Queue blocked-row visibility. |
| Preflight required | `command`, `authority_domain`, `safety_class`, `gate_tier`, `block_reason`, `replacement_command_or_NOT_APPLICABLE`, `required_external_workflow_or_NOT_APPLICABLE`, `source_provenance`, `surface_origin`, `created_at_utc`. |
| Confirmation strength | None. **Never executable.** |
| Refusal triggers | Reaching the gate with `safety_class == BLOCKED_IN_COCKPIT` ⇒ refuse with `BLOCKED_IN_COCKPIT`; route to `ShowBlockedReason` at originating surface. |
| Proof captured | `BLOCK_REASON_RECORD` (block reason; replacement; evidence of attempted selection). |
| Event/receipt | `gate_refuse` (no confirm; no proof for execution). |
| Routing on refusal | `ShowBlockedReason` at originating surface. |

### 1.10 TU — Unknown

| Aspect | Value |
| --- | --- |
| Allowed origins | Command Palette `ShowUnknownDriftReason`; Unknown/Drift Queue visibility. |
| Preflight required | `command_or_UNKNOWN`, `authority_domain_or_UNKNOWN`, `safety_class`, `gate_tier`, `unknown_reason`, `required_investigation_packet_or_UNKNOWN`, `source_provenance`, `surface_origin`, `created_at_utc`, `palette_request_id`. |
| Confirmation strength | None. **Never executable.** |
| Refusal triggers | Reaching the gate with `safety_class == UNKNOWN` ⇒ refuse with `UNKNOWN_CLASS`; in-gate reclassification attempt ⇒ refuse. |
| Proof captured | `INVESTIGATION_PACKET_REFERENCE` (unknown reason; required investigation packet). |
| Event/receipt | `gate_refuse`. |
| Routing on refusal | Unknown/Drift Queue. |

## 2. Cross-Cutting Refusal Triggers (Apply To All Tiers)

The following triggers cause refusal regardless of tier (verbatim from `SAFE_ACTION_REFUSAL_RULES.md`):

| Category | Examples |
| --- | --- |
| Identity & resolution | `COMMAND_UNRESOLVED`, `PARAM_UNRESOLVED`, `DEFAULT_UNKNOWN`, `CWD_UNRESOLVED`, `CWD_OUT_OF_WORKTREE`, `WORKTREE_METADATA_UNRESOLVED`, `WORKTREE_DIRTY` |
| Authority & writer | `AUTHORITY_UNKNOWN`, `AUTHORITY_CONFLICT`, `WRITER_UNKNOWN` |
| Class & tier | `BLOCKED_IN_COCKPIT`, `UNKNOWN_CLASS`, `EXTERNAL_ONLY`, `NON_EXECUTABLE_TIER`, `GATE_TIER_UNKNOWN` |
| Activation | `DEPRECATED_BLOCKED`, `NOT_ACTIVE` |
| Side-effect & proof | `SIDE_EFFECTS_UNKNOWN`, `SIDE_EFFECTS_EMPTY`, `PROOF_REQUIREMENT_UNKNOWN`, `PROOF_TARGET_UNKNOWN` |
| Rollback & abort | `ROLLBACK_UNKNOWN`, `ROLLBACK_INSUFFICIENT` |
| Provenance & correlation | `PROVENANCE_UNKNOWN`, `REQUEST_ID_MISSING`, `INDEX_HASH_MISSING`, `INDEX_DRIFT` |
| Stale & origin | `STALE_HANDOFF`, `STALE_PROOF_GATE`, `SURFACE_ORIGIN_UNKNOWN`, `UNSAFE_SOURCE_SURFACE`, `INTENT_UNKNOWN` |
| Confirmation flow | `TYPED_CONFIRMATION_MISMATCH`, `DIFF_NOT_ACKNOWLEDGED`, `OPERATOR_ABORTED`, `OPERATOR_TIMEOUT` |
| Authority/class drift mid-flow | `AUTHORITY_DRIFT_MID_FLOW`, `CLASS_DRIFT_MID_FLOW` |

Every refusal emits a gate event/receipt; the gate never silently dismisses a refusal.

## 3. Cross-Cutting Receipts

Every gate invocation emits at least one event/receipt (`gate_open`); refusal/abort/timeout/confirmation/proof-capture emit additional events. Receipts:

- Are append-only.
- Carry UTC timestamps.
- Include `gate_request_id` (unique per invocation).
- Include `palette_request_id` when origin is `COMMAND_PALETTE`.
- Include `action_row_hash` (SHA-256 of preflight object).
- Redact secrets.
- Persist regardless of operator interaction (abort, timeout, dismiss).

(Source: `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` §3, §5, §6, §8.)

## 4. Cross-Cutting Forbidden Behaviors

- Auto-confirm in any tier.
- Confirm affordance enabled while any required field is `UNKNOWN`.
- Confirm affordance enabled before typed confirmation matches (T4/T5/T6).
- Confirm affordance rendered for `safety_class in {BLOCKED_IN_COCKPIT, UNKNOWN, EXTERNAL_ONLY}` or `gate_tier in {T0, TX, TU}`.
- Treating handoff as confirmation; treating confirmation as proof; treating preflight green as readiness proof.
- In-gate reclassification.
- Hidden retries; success chips before proof.
- Bypassing Settings/Admin/Runtime for `cockpit_placement == Settings/Admin`.
- Bypassing the gate for any non-read action.
- Persisting typed confirmation values across gate openings.
- Storing secrets in proof artifacts.
- Reusing a stale `palette_index_row_hash`.

(Source: `SAFE_ACTION_GATE_CONTRACT.md` §9; `SAFE_ACTION_CONFIRMATION_FLOWS.md` §6; `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` §9; `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §5; `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §7.)

## 5. Source Artifacts

- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_CONTRACT.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_CONFIRMATION_FLOWS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TEST_MATRIX.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
