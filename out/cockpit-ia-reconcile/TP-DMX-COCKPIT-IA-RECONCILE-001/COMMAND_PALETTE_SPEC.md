# Command Palette Specification

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT
**Supersedes (as canonical name):** `COMMAND_PALETTE_POLICY.md`

The Command Palette is a **broker**, not an executor. It provides discovery, classification, parameter preview, and routing into the appropriate execution gate. It never executes commands directly. It never silently routes around a gate. It never claims ownership of any authority slice.

## 1. Role Statement

The palette is the only allowed home for the 139 placement rows the inventory routes to "Command Palette" (see `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Command Palette`). It is also the global discovery surface for any command that the operator addresses by path or by intent rather than by mode home.

The palette **must not**:

- Execute any command itself.
- Auto-confirm a `CONFIRM_REQUIRED` action.
- Run a `BLOCKED_IN_COCKPIT` row through any path.
- Promote an `UNKNOWN` row into execution; it can only show why it is unknown.
- Hide the authority owner, safety class, or required gate state from the operator.
- Default destructive parameters or apply implicit defaults that change side effects.

The palette **must**:

- Show every match with command path, authority owner, safety class, current cockpit placement, canonical writer, and proof requirement.
- Route every action through the Safe Action Gate (`SAFE_ACTION_GATE_SPEC.md`) when execution is allowed.
- Route every admin/runtime row through Settings/Admin/Runtime (`SETTINGS_ADMIN_RUNTIME_SPEC.md`) when it is an admin flow.
- Route every unknown or blocked row to the Unknown/Drift Queue (`UNKNOWN_DRIFT_QUEUE_SPEC.md`) when execution is not allowed.

## 2. Search Axes

The palette must support search and filter across these axes simultaneously. A row may match on any axis; the palette must surface the axis that matched so the operator does not get a false-positive hit.

| Axis | Field source | Example query |
| --- | --- | --- |
| Command path | `command_path`, `parent_group`, `source_symbol` | `dopetask doctor` |
| Authority domain | `authority_domain` | `authority:dopetask` |
| Safety class | `safe_UI_exposure` | `class:CONFIRM_REQUIRED` |
| Cockpit placement | `likely_cockpit_placement` | `place:Settings/Admin` |
| Canonical writer | derived from authority domain + system docs | `writer:ConPort` |
| Proof requirement | derived from class + governance gate | `proof:required` |
| Source provenance | `source_file`, `source_symbol`, `evidence_path_or_command` | `source:routing_cli.py` |
| Activation status | `activation_status` | `status:DEFINED_NOT_REGISTERED` |

## 3. Outcomes (Allowed Result Actions)

Every palette result must resolve into exactly one of these outcomes. The palette must never collapse multiple outcomes into a single click.

| Outcome | When to use | What happens |
| --- | --- | --- |
| Inspect | The row is `DISPLAY_ONLY` or `INSPECT_ACTION`. | Open inspector with command path, authority owner, last result, evidence path; no mutation. |
| Copy command | Operator wants to run externally, or row is `EXTERNAL_ONLY`. | Copy fully resolved invocation to clipboard, log clipboard event in evidence stream. |
| Open Safe Action Gate | Row is `CONFIRM_REQUIRED` or class-specific (config mutation, write local, write remote, start/stop service, execution handoff). | Hand the resolved command and parameters to the Safe Action Gate; do not run anything yet. |
| Open Settings/Admin/Runtime | Row is admin/runtime (routing/profile/env/hooks/MCP/service-startup/debug). | Navigate to the Settings surface where the row is grouped; the gate is invoked from there. |
| Show blocked reason | Row is `BLOCKED_IN_COCKPIT`. | Show block class, reason, replacement command (if any), required external workflow; no execute affordance. |
| Show unknown / drift reason | Row is `UNKNOWN`, `OPTIONAL_IMPORT_UNKNOWN`, `DEFINED_NOT_REGISTERED`, or has missing authority/proof. | Show why the row is unknown; show the required investigation packet; route to the Unknown/Drift Queue. |

## 4. Parameter Preview Contract

For any row that takes parameters, the palette must display the fully resolved invocation **before** any handoff to a gate. It must show:

- Command path including subcommands.
- Required parameters with current values.
- Optional parameters with defaults made explicit (no implicit defaults).
- `cwd` / worktree target (resolved against the current worktree).
- Output target (file path, log target, dry-run output) when applicable.
- Whether the row requires TP/governance, proof, or external approval.
- Side-effect summary derived from authority + class.

If any field cannot be resolved, the palette must show the field as `UNKNOWN` and refuse to invoke a Safe Action Gate confirmation. This is a fail-closed behavior; no defaults are guessed.

## 5. Index Fields (Required)

These fields must be loaded from the command inventory and made visible per row. Missing fields must render as `UNKNOWN` not as blank.

- `command_path`
- `parent_group`
- `authority_domain`
- `classification` / `safe_UI_exposure`
- `likely_cockpit_placement`
- `current_Cockpit_coverage`
- `activation_status`
- `source_file`
- `source_symbol`
- `help_text_or_summary`
- `evidence_path_or_command`
- `canonical_writer` (derived)
- `proof_requirement` (derived)

## 6. Forbidden Behaviors

- Silent execution from any palette match.
- Auto-confirmation of any `CONFIRM_REQUIRED` row.
- Toolbar shortcut on `BLOCKED_IN_COCKPIT` rows.
- Mode home-screen placement of `COMMAND_PALETTE_ONLY` rows.
- Implicit default parameters that change side effects.
- Promotion of `UNKNOWN` rows to execution.
- Hidden retries or background reroutes.

## 7. Source Artifact

The original `COMMAND_PALETTE_POLICY.md` carried into this packet remains as an evidence artifact. This spec replaces it as the canonical name and tightens the broker-not-executor contract. Counts and class definitions are inherited unchanged from `COMMAND_EXPOSURE_POLICY.md` / `COMMAND_EXPOSURE_POLICY.json`.
