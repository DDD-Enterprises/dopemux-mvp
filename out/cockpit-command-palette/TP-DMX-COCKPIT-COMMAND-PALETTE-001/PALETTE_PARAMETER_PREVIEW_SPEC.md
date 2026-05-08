# Palette Parameter Preview Specification

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines what the Command Palette must show before invoking any execution gate. Parameter preview is the contract that prevents the palette from silently changing side effects via implicit defaults. This spec is fail-closed: any field that cannot be resolved renders as `UNKNOWN` and refuses gate handoff (`COMMAND_PALETTE_SPEC.md` §4).

## 1. When Preview Is Required

Preview is required for any palette result whose `safe_ui_exposure` is `CONFIRM_REQUIRED` or `COMMAND_PALETTE_ONLY`, or any row whose selected outcome is `OpenSafeActionGate` or `OpenSettingsAdminRuntime`. Preview is also offered on `INSPECT_ACTION` rows so the operator can see the exact diagnostic invocation before it runs.

Preview is **not** required for `DISPLAY_ONLY`, `BLOCKED_IN_COCKPIT`, `EXTERNAL_ONLY` (copy-only), or `UNKNOWN` rows; those rows have no execution path from the palette.

## 2. Preview Fields (Required, Visible Before Confirm)

| Field | Source | Display rule |
| --- | --- | --- |
| Command path with subcommands | `command_path` | Always shown verbatim; never abbreviated. |
| Required parameters | `parameter_schema.required_parameters` | Each shown with name, type, current value, and example. Any unresolved value shows `UNKNOWN`. |
| Optional parameters | `parameter_schema.optional_parameters` | Each shown with name, type, **explicit default**, and the side effect that default produces. No implicit defaults. |
| `cwd` / worktree target | `parameter_schema.cwd_target` | Resolved against the current worktree (this packet's worktree). Never `/tmp` or any other authoritative substitute. |
| Output target | `parameter_schema.output_target` | File path, log target, dry-run output, or `NOT_APPLICABLE`. |
| Side-effect summary | `parameter_schema.side_effects` | Enumerated set: config mutation, write local, write remote, start service, stop service, execution handoff, none. |
| Authority owner | `authority_domain` | Authority badge displayed inside preview. |
| Canonical writer | `canonical_writer` | Writer system(s) shown explicitly. |
| Safety class | `safe_ui_exposure` | Class shown in preview header. |
| Gate tier | `gate_tier` | Confirmation tier the row will use (`T0i`–`T6`, `TX`, `TU`). |
| Required gate state | governance gate hint (e.g. TP/proof) | Whether a TP/proof gate must be present. |
| Expected proof | `proof_requirement` | Proof category that will be required after execution. |
| Rollback / abort path | from carried row metadata or class | Explicit rollback path, abort token, or `NOT_APPLICABLE` with reason. |

## 3. Defaults Display Rule

Optional parameters must show defaults **explicitly**. Implicit defaults are forbidden. The display rule:

```
optional_parameter_name (type)
  default = <explicit literal value>
  effect when default is used = <enumerated side effect>
```

If a default cannot be derived from the source, the preview shows `default = UNKNOWN` and the row is fail-closed for execution. The palette must not invent a default.

## 4. `cwd` / Worktree Resolution Rule

`cwd_target` must resolve to the **current worktree** the operator is in. The palette must:

- Display the absolute path of the worktree.
- Display whether the worktree branch is detached.
- Display whether the worktree is dirty (uncommitted changes), if knowable from the carried inputs.

The palette must not silently substitute `/tmp`, `~`, or any non-worktree path as authoritative. If the worktree cannot be resolved, the preview shows `cwd_target = UNKNOWN` and the row is fail-closed.

## 5. Side-Effect Summary Rule

Side-effect rendering is enumerated. The palette must show every applicable side effect:

| Side effect token | Rendered language |
| --- | --- |
| `config_mutation` | "Will modify configuration in `<target>`." |
| `write_local` | "Will write file(s) to `<output_target>`." |
| `write_remote` | "Will call remote endpoint `<endpoint>`. Remote-mutation policy required." |
| `start_service` | "Will start service `<service>`. Service-lifecycle gate required." |
| `stop_service` | "Will stop service `<service>`. Service-lifecycle gate required." |
| `execution_handoff` | "Will hand off execution to `<runner>` with TP id `<tp_id>`." |
| `none` | "No side effects expected." |

If the side effect is not enumerated above, the preview shows `side_effects = UNKNOWN` and the row is fail-closed.

## 6. Fail-Closed Behavior (Normative)

The palette refuses to invoke a Safe Action Gate or Settings/Admin/Runtime confirm if **any** of these conditions hold:

| Condition | Reason rendered |
| --- | --- |
| Any required parameter resolves to `UNKNOWN`. | `PARAM_UNRESOLVED` |
| `cwd_target` resolves to `UNKNOWN`. | `CWD_UNRESOLVED` |
| `output_target` is required by class but resolves to `UNKNOWN`. | `OUTPUT_UNRESOLVED` |
| `side_effects` resolves to `UNKNOWN`. | `SIDE_EFFECTS_UNKNOWN` |
| `canonical_writer` resolves to `UNKNOWN`. | `WRITER_UNKNOWN` |
| `gate_tier` resolves to `UNKNOWN`. | `GATE_TIER_UNKNOWN` |
| `proof_requirement` resolves to `UNKNOWN` for an executing class. | `PROOF_REQUIREMENT_UNKNOWN` |
| Optional parameter default resolves to `UNKNOWN`. | `DEFAULT_UNKNOWN` |
| `authority_domain == 'unknown / conflicting'`. | `AUTHORITY_CONFLICT` |
| `activation_status` is non-`ACTIVE`. | `NOT_ACTIVE` |

In all cases, the row routes to the Unknown/Drift Queue with the reason. The palette never auto-resolves these by guessing.

## 7. Preview Update Rules

- Preview must update synchronously when the operator edits a parameter.
- Preview must show a re-derived `gate_tier` and `proof_requirement` if the side-effect set changes.
- Preview must not auto-fire a confirmation when a parameter is filled.
- Preview must not start the gate handoff until the operator explicitly clicks the primary outcome (`OpenSafeActionGate` or `OpenSettingsAdminRuntime`).

## 8. Forbidden Preview Behaviors

- Hiding any required preview field.
- Showing a default in plain text without labeling it as the explicit default.
- Substituting an inferred path or value for an `UNKNOWN`.
- Auto-confirming on selection.
- Replacing a `BLOCKED_IN_COCKPIT` preview with an executable preview.
- Showing a confirm affordance on rows whose preview has any fail-closed condition active.

## 9. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md` §4
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §2
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
