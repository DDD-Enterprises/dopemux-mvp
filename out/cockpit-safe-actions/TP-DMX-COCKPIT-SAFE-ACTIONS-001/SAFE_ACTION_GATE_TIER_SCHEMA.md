# Safe Action Gate Tier Schema (Human-Readable)

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)
**Companion file:** `SAFE_ACTION_GATE_TIER_SCHEMA.json`

This document explains the ten Safe Action Gate tiers in human-readable form. Tiers determine confirmation, preflight, proof, and refusal behavior. The gate carries the tier from the upstream surface; it never reclassifies. Tier semantics are normative and aligned with `SAFE_ACTION_GATE_SPEC.md` §1, `COMMAND_EXPOSURE_POLICY.json`, and `COMMAND_PALETTE_INDEX_SCHEMA.json:fields.gate_tier`.

## 1. Tier Family Overview

| Tier | Class | Executes? | When this tier applies | Operator interaction |
| --- | --- | --- | --- | --- |
| T0 | `DISPLAY_ONLY` | No (no execution path) | Read-only state/status data. No execution affordance. | Operator views; gate captures view-time provenance. |
| T0i | `INSPECT_ACTION` | Yes (read-only invocation) | Diagnostic, doctor, preflight commands invoked intentionally for inspection. | Operator clicks `Inspect` (no confirm step needed beyond explicit invoke). |
| T1 | `CONFIRM_REQUIRED` (generated artifact) | Yes | Action produces a generated artifact (file, report, evidence). | Operator confirms output path and overwrite behavior. |
| T2 | `CONFIRM_REQUIRED` (config mutation) | Yes | Action mutates configuration (routing, profile, env, MCP, hooks, runtime config). | Operator confirms target file/service and the before/after diff. |
| T3 | `CONFIRM_REQUIRED` (write local) | Yes | Action writes locally to filesystem outside a generated-artifact path. | Operator confirms path and side-effect class. |
| T4 | `CONFIRM_REQUIRED` (write remote) | Blocked by default until policy approves | Action mutates a remote endpoint (API call with side effects). | Operator confirms target, account/context, idempotency, and **types** the confirmation token. |
| T5 | `CONFIRM_REQUIRED` (start/stop service) | Yes | Action starts or stops a service. | Operator confirms service id and **types** the service id confirmation. |
| T6 | `CONFIRM_REQUIRED` (execution handoff) | Yes | Action hands a TP/task off to a runner. | Operator confirms TP id, runner, cwd, branch, output target, and **types** the TP id confirmation. |
| TX | `BLOCKED_IN_COCKPIT` | No (never) | Destructive, high-trust, legacy-blocked, or unsafe-without-external-governance rows. | Operator views block reason and any replacement; no confirm affordance. |
| TU | `UNKNOWN` | No (never) | Activation, authority, side effects, or runtime ownership unresolved. | Operator views unknown reason and required investigation packet; no confirm affordance. |

## 2. When To Apply Each Tier

The tier is determined at the upstream surface (Palette / Settings/Admin/Runtime) using `safe_ui_exposure` plus `parameter_schema.side_effects`, per `COMMAND_PALETTE_INDEX_SCHEMA.json:fields.gate_tier` and `SAFE_ACTION_GATE_SPEC.md` §1.

### T0 — DISPLAY_ONLY

- **When:** Read-only data is rendered without an action affordance. Examples (carried, illustrative): `./scripts/dopetask` (the bare command path showing help), status badges, last observed timestamps.
- **Gate behavior:** No confirm affordance. The gate (or upstream surface) captures source authority and view timestamp at display time.
- **Why a tier:** Even read-only display must preserve provenance and not imply Cockpit owns the underlying authority.

### T0i — INSPECT_ACTION

- **When:** A diagnostic command is intentionally invoked. Examples (carried): `./scripts/dopetask doctor`, `./scripts/dopetask manifest check`, `./scripts/dopetask ops doctor`, `./scripts/dopetask project doctor`, `./scripts/dopetask tp git doctor`.
- **Gate behavior:** Explicit invoke required (no defaults-on inspection with side effects). The gate displays the command and captures result + source authority + timestamp as proof.
- **Why a tier:** Diagnostics can be expensive or environment-sensitive; require explicit invocation.

### T1 — Generated artifact

- **When:** Action produces a generated artifact. Examples (carried): `./scripts/dopetask collect-evidence`, `./scripts/dopetask compile-tasks`, `./scripts/dopetask bundle export`.
- **Gate behavior:** Confirm output path and overwrite behavior. Capture artifact path + checksum/summary as proof. Abort allowed before write; rollback if writer supports.

### T2 — Config mutation

- **When:** Action mutates routing/profile/env/MCP/hooks/runtime config. Examples (carried, by placement Settings/Admin): `dopemux routing` family, `dopemux profile` rows, `dopemux env` rows, `dopemux mcp` rows, hooks/native-hooks rows, runtime configuration rows.
- **Gate behavior:** Confirm target file/service and effective-config diff. If diff cannot be derived, the gate displays `UNKNOWN` and the operator must explicitly accept the `UNKNOWN` diff (no auto-accept). Capture config diff or post-action status as proof.

### T3 — Write local

- **When:** Action writes locally to filesystem outside a generated-artifact path (e.g., create directory, scaffold files, append to a managed file). Side effects include `write local` per `parameter_schema.side_effects`.
- **Gate behavior:** Confirm path and side-effect class. Block destructive writes if rollback path is absent. Capture filesystem diff, artifact path, or exit code as proof.

### T4 — Write remote

- **When:** Action mutates a remote endpoint with side effects. **Blocked by default** until the remote-mutation policy is in scope and approves the row. Examples (carried, illustrative): API calls that change remote state.
- **Gate behavior:** Confirm remote target, account/context, idempotency. **Typed confirmation** required (operator types the remote endpoint or a confirmation token). Capture remote receipt as proof.
- **Status:** This packet defines the contract; no T4 execution occurs in this packet (`CLAUDE_DESIGN_BLOCKERS.md` §4).

### T5 — Start/stop service

- **When:** Action starts or stops a service (Services flow group, MCP server start/stop, etc.).
- **Gate behavior:** Confirm service id, scope, expected state transition. Pre-state snapshot required. **Typed confirmation** required (operator types the service id). Capture post-state status + log excerpt + exit code as proof.

### T6 — Execution handoff

- **When:** Action hands a TP/task off to a runner. Examples (carried, illustrative): TP runs, dopetask runs that hand off to a runner.
- **Gate behavior:** Confirm TP id, runner, cwd, branch, output/proof target. TP gate must be present (`SAFE_ACTION_GATE_SPEC.md` §1 row T6). **Typed confirmation** required (operator types the TP id). Capture exit code + proof path + validation summary as proof.

### TX — Blocked

- **When:** `safe_ui_exposure == BLOCKED_IN_COCKPIT` (48 rows in carried inventory). Examples (carried): `./scripts/dopetask commit-run`, `./scripts/dopetask commit-sequence`, `./scripts/dopetask finish`, `./scripts/dopetask metrics reset`, `./scripts/dopetask tmux kill`. Also `activation_status == DEPRECATED_BLOCKED`.
- **Gate behavior:** Never executable. The gate displays block reason + replacement command (if any) + required external workflow. No confirm affordance under any condition.

### TU — Unknown

- **When:** `safe_ui_exposure == UNKNOWN` (5 rows in carried inventory), `activation_status` in `{DEFINED_NOT_REGISTERED, OPTIONAL_IMPORT_UNKNOWN}`, `authority_domain == 'unknown / conflicting'`, or other unresolved-axis combinations. Examples (carried): `dopemux genetic`, `dopemux vault`, `dopemux worktree`, `dopemux worktrees`, `python -m dopemux`.
- **Gate behavior:** Never executable. The gate displays unknown reason + required investigation packet. No confirm affordance under any condition. No reclassification inside the gate.

## 3. Tier Determines Required Preflight

Each tier defines its own `required_preflight_fields` set in `SAFE_ACTION_GATE_TIER_SCHEMA.json`. Common fields apply to T0i–T6 (resolved command, params, cwd, authority, writer, side effects, expected proof, rollback). Tier-specific fields add:

- T1: `output_target_path`, `overwrite_behavior`.
- T2: `config_target_file_or_service`, `effective_config_diff_or_unknown_flag`.
- T3: `write_target_path`, `side_effect_classification`.
- T4: `remote_target_endpoint`, `remote_account_or_context`, `idempotency_key`, `remote_mutation_policy_reference`.
- T5: `service_id`, `service_scope`, `expected_state_transition`, `pre_state_snapshot`.
- T6: `tp_or_task_id`, `runner_id`, `branch`, `output_or_proof_target`, `tp_gate_present`.
- TX: `block_reason`, `replacement_command_or_NOT_APPLICABLE`, `required_external_workflow_or_NOT_APPLICABLE`.
- TU: `unknown_reason`, `required_investigation_packet_or_UNKNOWN`.

Missing required fields ⇒ refuse confirmation ⇒ route to Unknown/Drift Queue with the missing-field reason.

## 4. Tier Determines Required Post-Action Proof

| Tier | Proof captured |
| --- | --- |
| T0 | `INSPECT_RESULT_AND_TIMESTAMP` at view time + source authority. |
| T0i | Command path + exit/result summary + source authority. |
| T1 | `ARTIFACT_AND_CHECKSUM` (artifact path + checksum/summary; exit code if runner-invoked). |
| T2 | `CONFIG_DIFF_OR_STATUS` (config diff or before/after status; command exit code). |
| T3 | `FILESYSTEM_DIFF_OR_EXIT_CODE` (filesystem path, action verb, result, exit code). |
| T4 | `REMOTE_RECEIPT` (endpoint, actor, status, response excerpt where governance allows). |
| T5 | `SERVICE_STATUS_AND_LOG` (post-state status, log excerpt, exit code). |
| T6 | `TP_RUNNER_PROOF` (exit code, proof path, validation summary). |
| TX | `BLOCK_REASON_RECORD` + replacement command (if any) + evidence of attempted selection. |
| TU | `INVESTIGATION_PACKET_REFERENCE` + unknown reason record. |

Missing proof after execution succeeded ⇒ row tagged `STALE_PROOF` and routed to Unknown/Drift Queue.

## 5. Tier Determines Confirmation Strength

- T0 / TX / TU: no confirmation; never executes.
- T0i: explicit invoke (operator clicks Inspect intentionally).
- T1 / T2 / T3: explicit confirm button (no auto-confirm).
- T4 / T5 / T6: explicit confirm button **plus typed confirmation** (operator types the relevant identifier — remote endpoint, service id, or TP id).

The typed confirmation token requirement is normative (`SAFE_ACTION_GATE_SPEC.md` §5; this contract §5 in `SAFE_ACTION_GATE_CONTRACT.md`).

## 6. Tier Determines Allowed Sources

| Tier | Allowed origin surfaces |
| --- | --- |
| T0 | Read-only contextual surfaces; Overview drift summary; Inspect drawer. |
| T0i | Command Palette `Inspect` outcome; Settings/Admin/Runtime drift inspector; contextual inspect drawer. |
| T1 | Command Palette `OpenSafeActionGate`; contextual surface action originating an artifact. |
| T2 | Command Palette `OpenSafeActionGate`; Settings/Admin/Runtime Routing/Profile/Env/Hooks/Runtime/MCP-config flows (admin gate then Safe Action Gate). |
| T3 | Command Palette `OpenSafeActionGate`; contextual surface action that writes locally. |
| T4 | Command Palette `OpenSafeActionGate` only when remote-mutation policy is in scope; Settings/Admin/Runtime only flows whose policy approves T4. |
| T5 | Settings/Admin/Runtime Service startup/lifecycle (admin); Command Palette when placement is Services and confirmation flow allows. |
| T6 | Command Palette `OpenSafeActionGate` for execution handoff rows (Implementer/Palette); Implementer contextual surface that originates a TP run. |
| TX | Command Palette `ShowBlockedReason`; Unknown/Drift Queue blocked-row visibility. |
| TU | Command Palette `ShowUnknownDriftReason`; Unknown/Drift Queue visibility surface. |

Other origins (deep-link, URL parameter, keyboard shortcut bypassing the surface) are refused.

## 7. Tier Refusals Are Fail-Closed

If any required preflight field for the row's tier resolves to `UNKNOWN`, the gate refuses confirmation. Tier-specific refusal triggers are enumerated in `SAFE_ACTION_REFUSAL_RULES.md`. Refused actions never reach a confirm affordance and never invoke the runtime.

## 8. Tier Counts From Carried Inventory

The tier mapping respects the carried counts in `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`:

- `safe_ui_exposure.DISPLAY_ONLY = 178` ⇒ T0.
- `safe_ui_exposure.INSPECT_ACTION = 23` ⇒ T0i.
- `safe_ui_exposure.CONFIRM_REQUIRED = 111` ⇒ T1–T6 by side-effect class.
- `safe_ui_exposure.COMMAND_PALETTE_ONLY = 40` ⇒ T1–T6 by side-effect class (executable variant) or T0i (inspect variant).
- `safe_ui_exposure.BLOCKED_IN_COCKPIT = 48` ⇒ TX.
- `safe_ui_exposure.UNKNOWN = 5` ⇒ TU.
- `external_only_count = 37` ⇒ T0i or TX (external-only rows do not execute via Cockpit).

## 9. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §1, §3, §5
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json:fields.gate_tier`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §4
