# Palette Result Row Specification

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the visible fields and badges of a single result row in the Command Palette. It is normative for the downstream Cockpit shell remediation packets. It does not describe pixel-level visuals; it describes the data and badges that must be present and the affordances that must or must not be available per row class.

## 1. Visible Fields (Required, Per Row)

Every result row must show all of the following. None of these may be hidden behind a hover, tooltip, or expansion-only state. Missing values render as the literal string `UNKNOWN`, never blank (`COMMAND_PALETTE_SPEC.md` §5).

| Field | Source field | Display purpose |
| --- | --- | --- |
| Command path | `command_path` | The fully qualified path operator typed or matched. |
| Display label | `command_path` short form, or `parent_group + last segment of command_path` | Human-readable label. The display label must include the full `command_path` somewhere on the row (path is never hidden). |
| Authority badge | `authority_domain` | Authority owner badge. |
| Safety badge | `safe_ui_exposure` | Safety class badge. |
| Placement badge | `cockpit_placement` | Where this row's home is in the IA. |
| Proof requirement badge | `proof_requirement` (derived) | What proof is required after execution. |
| Activation/coverage status | `activation_status` + `current_cockpit_coverage` | Two badges: activation and coverage. |
| Source / provenance | `source_file:source_symbol` | Provenance pointer. |
| Primary outcome | first member of `allowed_palette_outcomes` resolved by `PALETTE_ROUTING_RULES.md` §7 | The button or affordance the operator can click. |
| Blocked reason (when applicable) | `blocked_reason` | Required when `safe_ui_exposure == BLOCKED_IN_COCKPIT` or `activation_status == DEPRECATED_BLOCKED`. |
| Unknown reason (when applicable) | `unknown_reason` | Required when row is in any unknown/drift state. |

## 2. Badge Definitions

Badges are short, color-coded labels used to make safety and authority legible at a glance. The palette must surface every badge per row.

### 2.1 Authority Badge (`authority_domain`)
- One of the ten enumerated authorities; `unknown / conflicting` is rendered explicitly as `UNKNOWN AUTHORITY`.
- The badge must show the authority text; the authority is never abbreviated to invented short names.

### 2.2 Safety Badge (`safe_ui_exposure`)
- `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED`, `COMMAND_PALETTE_ONLY`, `BLOCKED_IN_COCKPIT`, `EXTERNAL_ONLY`, `UNKNOWN`.
- Must be visually distinct so a `BLOCKED_IN_COCKPIT` row never looks like a `CONFIRM_REQUIRED` row.

### 2.3 Placement Badge (`cockpit_placement`)
- One of `PM`, `Implementer`, `Overview`, `Services`, `Events`, `Command Palette`, `Settings/Admin`, `External/Not Cockpit`, `UNKNOWN`.
- The badge informs the operator that selecting the row will route into that surface (see `PALETTE_ROUTING_RULES.md` §3).

### 2.4 Proof Requirement Badge (`proof_requirement`)
- `NONE`, `INSPECT_RESULT_AND_TIMESTAMP`, `ARTIFACT_AND_CHECKSUM`, `CONFIG_DIFF_OR_STATUS`, `FILESYSTEM_DIFF_OR_EXIT_CODE`, `REMOTE_RECEIPT`, `SERVICE_STATUS_AND_LOG`, `TP_RUNNER_PROOF`, `BLOCK_REASON_RECORD`, `INVESTIGATION_PACKET_REFERENCE`.
- Drives operator expectations of what evidence will be produced if the row is run.

### 2.5 Activation Badge (`activation_status`)
- `ACTIVE`, `DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`, `DEPRECATED_BLOCKED`.
- Non-`ACTIVE` activation visually overrides the safety badge color (e.g. blocked styling for `DEPRECATED_BLOCKED`).

### 2.6 Coverage Badge (`current_cockpit_coverage`)
- `PARTIAL`, `MISSING`, `UNKNOWN`, `OUT_OF_SCOPE`.
- `MISSING` and `UNKNOWN` are rendered prominently so the operator can see drift even on a row that is otherwise executable.

## 3. Affordances By Class (Allowed / Forbidden)

| `safe_ui_exposure` | Allowed affordances | Forbidden affordances |
| --- | --- | --- |
| `DISPLAY_ONLY` | Inspect button, copy-command (informational). | Run button, primary CTA button. |
| `INSPECT_ACTION` | Inspect button (preflight/diagnostic), copy-command. | Run button, defaults-on polling. |
| `CONFIRM_REQUIRED` | Preview button, "Open Safe Action Gate" button (or "Open Settings/Admin/Runtime" for admin rows). | One-click run, auto-confirm, success chip before result. |
| `COMMAND_PALETTE_ONLY` | Preview, "Open Safe Action Gate" or "Open Settings/Admin/Runtime". | Mode-bar shortcut, toolbar shortcut. |
| `BLOCKED_IN_COCKPIT` | Display blocked reason, copy-command (read-only), link to external workflow. | Run button, confirm modal that still executes, keyboard shortcut. |
| `EXTERNAL_ONLY` | Copy-command, link to external runbook, inspect (informational). | Cockpit execution path, state mutation from UI. |
| `UNKNOWN` | Display unknown reason, link to investigation packet (when known). | Any execution affordance. |

## 4. Per-Row Layout (Logical, Not Pixel)

The row consists of three logical regions. The palette designer may arrange them but must include all three.

1. **Identification region.** Display label + command path + provenance pointer (`source_file:source_symbol`).
2. **Classification region.** Authority badge, safety badge, placement badge, proof requirement badge, activation badge, coverage badge.
3. **Affordance region.** Primary outcome button or read-only badge (e.g. blocked-row chip). For blocked/unknown rows, no run button is rendered.

## 5. Multi-State Visualization (Required)

Rows may simultaneously carry several state signals. The visualization must remain honest: a `CONFIRM_REQUIRED` row that is `DEFINED_NOT_REGISTERED` is **not** executable from the palette and must show its activation override.

| State combination | Visual rule |
| --- | --- |
| `CONFIRM_REQUIRED` + `ACTIVE` + `MISSING` coverage | Executable. Display `coverage:MISSING` badge prominently. Operator can proceed to gate. |
| `CONFIRM_REQUIRED` + `DEFINED_NOT_REGISTERED` | Activation override; show `Inspect` and `Drift` outcome only. Run button hidden. |
| `BLOCKED_IN_COCKPIT` + `MISSING` coverage | Display blocked reason; coverage badge informational only; no run button. |
| `EXTERNAL_ONLY` + `ACTIVE` | Display `CopyCommand` outcome; no Cockpit execution path. |
| `UNKNOWN` (class) + any | Show unknown reason; route to Unknown/Drift Queue. |

## 6. Result Row Forbidden Behaviors

- Hide the safety badge.
- Hide the placement badge.
- Hide the activation/coverage badges.
- Render the primary outcome button when the row is `BLOCKED_IN_COCKPIT` or `UNKNOWN`.
- Render a "run" button on a `DISPLAY_ONLY` row.
- Render a success chip before any result has been observed.
- Show a row without authority (i.e. omit the authority badge).
- Show a row whose `safe_ui_exposure` was reclassified inside the palette.

## 7. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
