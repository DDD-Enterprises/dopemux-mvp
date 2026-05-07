# Palette Routing Rules

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the rules the Command Palette uses to route a selected row to exactly one of six allowed outcomes. Routing is deterministic. The palette never silently chooses an outcome the row does not allow. Every routing decision is grounded in carried inputs and is fail-closed.

## 1. Outcomes (Exactly One Per Click)

| Outcome | Target surface | Executes? |
| --- | --- | --- |
| Inspect | Inspect drawer in current mode (PM/Implementer/Overview/Services/Events/Settings/Admin/Runtime). | No mutation. |
| CopyCommand | Clipboard (with evidence-stream log of clipboard event). | No mutation. |
| OpenSafeActionGate | Safe Action Gate primitive. | Gate handles execution per its own contract; palette never executes. |
| OpenSettingsAdminRuntime | Settings/Admin/Runtime surface. | The surface invokes the Safe Action Gate; palette never executes. |
| ShowBlockedReason | Blocked-row inspector inside palette. | Never executes. |
| ShowUnknownDriftReason | Unknown/Drift Queue. | Never executes. |

The palette never collapses two outcomes into one click (`COMMAND_PALETTE_SPEC.md` §3).

## 2. Routing By `safe_ui_exposure`

This is the primary routing axis. The class is enumerated in `COMMAND_EXPOSURE_POLICY.json:classes`.

| `safe_ui_exposure` | Allowed outcomes | Forbidden outcomes | Default outcome |
| --- | --- | --- | --- |
| `DISPLAY_ONLY` | `Inspect` | `OpenSafeActionGate`, `OpenSettingsAdminRuntime`, `ShowBlockedReason`, `ShowUnknownDriftReason` (unless field-driven) | `Inspect` |
| `INSPECT_ACTION` | `Inspect` | `OpenSafeActionGate`, `OpenSettingsAdminRuntime` | `Inspect` |
| `CONFIRM_REQUIRED` | `Inspect` (preview only), `OpenSafeActionGate`, `OpenSettingsAdminRuntime` (admin/runtime rows) | `ShowBlockedReason`, `ShowUnknownDriftReason` (unless other field is unknown) | `OpenSafeActionGate` (or `OpenSettingsAdminRuntime` per placement) |
| `COMMAND_PALETTE_ONLY` | `Inspect` (preview only), `OpenSafeActionGate`, `OpenSettingsAdminRuntime` | mode-home placement | `Inspect` then `OpenSafeActionGate` (or `OpenSettingsAdminRuntime` per placement) |
| `BLOCKED_IN_COCKPIT` | `ShowBlockedReason` | All execution outcomes | `ShowBlockedReason` |
| `EXTERNAL_ONLY` | `Inspect`, `CopyCommand` | `OpenSafeActionGate`, `OpenSettingsAdminRuntime`, `ShowBlockedReason` (it is not blocked, it is external) | `CopyCommand` |
| `UNKNOWN` | `ShowUnknownDriftReason` | All execution outcomes | `ShowUnknownDriftReason` |

Counts of rows in each class (carried, not regenerated):

- `DISPLAY_ONLY` 178
- `CONFIRM_REQUIRED` 111
- `BLOCKED_IN_COCKPIT` 48
- `COMMAND_PALETTE_ONLY` 40
- `INSPECT_ACTION` 23
- `EXTERNAL_ONLY` 37 (`metadata.external_only_count`)
- `UNKNOWN` 5

## 3. Routing By `cockpit_placement`

This is the secondary routing axis. It applies only to rows that have already been determined to be executable by `safe_ui_exposure`. It does not override class rules; it disambiguates when `OpenSafeActionGate` and `OpenSettingsAdminRuntime` are both candidates.

| `cockpit_placement` | Effect |
| --- | --- |
| `PM` | Palette opens contextual Inspect drawer in PM mode. Executable rows handed off to Safe Action Gate. |
| `Implementer` | Palette opens contextual Inspect drawer in Implementer mode. Executable rows handed off to Safe Action Gate (T6 if execution handoff). |
| `Overview` | Palette opens contextual Inspect drawer in Overview. No mutation in Overview; executable rows handed off to Safe Action Gate. |
| `Services` | Palette opens contextual Inspect drawer in Services. Service start/stop handed off to Safe Action Gate (T5). |
| `Events` | Palette opens contextual Inspect drawer in Events. Capture/emit handed off to Safe Action Gate. |
| `Command Palette` | Palette is the home; Inspect/Preview occurs inline; executable rows handed off to Safe Action Gate or Settings/Admin/Runtime per side-effect class. |
| `Settings/Admin` | Palette routes to Settings/Admin/Runtime surface (`OpenSettingsAdminRuntime`); the surface invokes the Safe Action Gate. The palette must not bypass Settings/Admin/Runtime. |
| `External/Not Cockpit` | Palette permits `Inspect` and `CopyCommand` only. No execution path. |
| `UNKNOWN` | Palette routes to Unknown/Drift Queue (`ShowUnknownDriftReason`). |

Counts of rows by placement (carried):

- `Command Palette` 139
- `Implementer` 73
- `Settings/Admin` 62
- `Services` 54
- `External/Not Cockpit` 37
- `Events` 15
- `PM` 15
- `Overview` 9
- `UNKNOWN` 1

## 4. Routing By `activation_status`

This axis overrides class-based execution routes. A non-`ACTIVE` row never reaches the Safe Action Gate, even if the class is `CONFIRM_REQUIRED`.

| `activation_status` | Effect |
| --- | --- |
| `ACTIVE` | No override; class-based and placement-based routing applies. |
| `DEFINED_NOT_REGISTERED` | Force-route to Unknown/Drift Queue with reason `DEFINED_NOT_REGISTERED`. `Inspect` and `CopyCommand` may still be allowed for documentation. |
| `OPTIONAL_IMPORT_UNKNOWN` | Force-route to Unknown/Drift Queue with reason `OPTIONAL_IMPORT_UNKNOWN`. |
| `DEPRECATED_BLOCKED` | Force-route to `ShowBlockedReason`. The row remains visible as a blocked row. |

Counts (carried):

- `ACTIVE` 366
- `DEFINED_NOT_REGISTERED` 30
- `OPTIONAL_IMPORT_UNKNOWN` 2
- `DEPRECATED_BLOCKED` 7

## 5. Routing By `authority_domain`

The palette never routes to Safe Action Gate or Settings/Admin/Runtime when the authority is unknown or conflicting.

| `authority_domain` | Effect |
| --- | --- |
| Any of the nine resolved authorities | No override; routing proceeds by class/placement/activation. |
| `unknown / conflicting` | Force-route to Unknown/Drift Queue with reason `AUTHORITY_CONFLICT`. |

Resolved authorities (10 enumerated, one of which is `unknown / conflicting`).

## 6. Routing By `current_cockpit_coverage`

Coverage is informational by default but combines with other gaps to force fail-closed routing.

| `current_cockpit_coverage` | Effect |
| --- | --- |
| `PARTIAL` | No override; class-based routing applies. Display a `coverage:PARTIAL` badge. |
| `OUT_OF_SCOPE` | Force-route to `ShowBlockedReason` or `Inspect` (whichever the class allows). The row is documented but not in scope. |
| `MISSING` | Display a `coverage:MISSING` badge. If combined with `safe_ui_exposure == UNKNOWN` or `activation_status` non-`ACTIVE`, route to Unknown/Drift Queue. |
| `UNKNOWN` | Display a `coverage:UNKNOWN` badge. If any other field is also unknown, route to Unknown/Drift Queue. |

Counts (carried):

- `MISSING` 284
- `PARTIAL` 82
- `UNKNOWN` 32
- `OUT_OF_SCOPE` 7

## 7. Routing Decision Algorithm (Normative)

The palette must apply rules in this exact order. The first rule that fires terminates the decision.

1. **R-1 (Index integrity).** If the row fails index validation rules `RV-1 .. RV-11` from `COMMAND_PALETTE_INDEX_SCHEMA.json`, route to Unknown/Drift Queue. Reason = the failing rule id.
2. **R-2 (Activation override).** If `activation_status` is `DEPRECATED_BLOCKED`, route to `ShowBlockedReason`. If `activation_status` is `DEFINED_NOT_REGISTERED` or `OPTIONAL_IMPORT_UNKNOWN`, route to Unknown/Drift Queue.
3. **R-3 (Authority override).** If `authority_domain == 'unknown / conflicting'` or `canonical_writer == UNKNOWN`, route to Unknown/Drift Queue with reason `AUTHORITY_CONFLICT`.
4. **R-4 (Class override - blocked/unknown/external).** If `safe_ui_exposure == BLOCKED_IN_COCKPIT`, route to `ShowBlockedReason`. If `safe_ui_exposure == UNKNOWN`, route to Unknown/Drift Queue. If `safe_ui_exposure == EXTERNAL_ONLY`, restrict outcomes to `Inspect` and `CopyCommand`.
5. **R-5 (Display/Inspect classes).** If `safe_ui_exposure` is `DISPLAY_ONLY` or `INSPECT_ACTION`, default outcome is `Inspect`.
6. **R-6 (Parameter resolution).** If `safe_ui_exposure` is `CONFIRM_REQUIRED` or `COMMAND_PALETTE_ONLY` and any required parameter resolves to `UNKNOWN`, route to Unknown/Drift Queue with reason `PARAM_UNRESOLVED`.
7. **R-7 (Placement disambiguation).** If `safe_ui_exposure` is `CONFIRM_REQUIRED` or `COMMAND_PALETTE_ONLY` and parameters resolve, route by `cockpit_placement`:
   - `Settings/Admin` ⇒ `OpenSettingsAdminRuntime`.
   - `External/Not Cockpit` ⇒ `Inspect` or `CopyCommand` only.
   - Any other placement ⇒ `OpenSafeActionGate`.
8. **R-8 (Coverage check).** If `current_cockpit_coverage == OUT_OF_SCOPE`, restrict outcomes to `Inspect`. If `current_cockpit_coverage == MISSING` and the row is otherwise eligible for execution, allow execution but display a `coverage:MISSING` badge prominently.
9. **R-9 (Final candidate set).** The resulting outcome must be in the row's `allowed_palette_outcomes` set. If not, route to Unknown/Drift Queue with reason `OUTCOME_DENIED`.

## 8. Worked Examples

These examples are illustrative; they use representative inventory rows from `COMMAND_EXPOSURE_POLICY.json:classes.examples_from_inventory`. No new classification is asserted.

| Example row | Class | Activation | Placement | Routing |
| --- | --- | --- | --- | --- |
| `./scripts/dopetask` | `DISPLAY_ONLY` | `ACTIVE` | (not Cockpit primary) | R-5 ⇒ `Inspect` |
| `./scripts/dopetask doctor` | `INSPECT_ACTION` | `ACTIVE` | Implementer/Palette | R-5 ⇒ `Inspect` |
| `./scripts/dopetask collect-evidence` | `CONFIRM_REQUIRED` | `ACTIVE` | Implementer/Palette | R-7 ⇒ `OpenSafeActionGate` (T1 generated artifact) |
| `./scripts/dopetask project init` | `COMMAND_PALETTE_ONLY` | `ACTIVE` | Settings/Admin or Palette | R-7 ⇒ `OpenSettingsAdminRuntime` (admin) or `OpenSafeActionGate` (palette home) |
| `./scripts/dopetask commit-run` | `BLOCKED_IN_COCKPIT` | n/a | (not executable in Cockpit) | R-4 ⇒ `ShowBlockedReason` |
| `dopemux decisions list` | `EXTERNAL_ONLY` | `ACTIVE` | External/Not Cockpit | R-4 ⇒ `Inspect`/`CopyCommand` only |
| `dopemux worktree` (defined-but-not-registered example) | n/a | `DEFINED_NOT_REGISTERED` | n/a | R-2 ⇒ Unknown/Drift Queue |
| `python -m dopemux` (UNKNOWN example) | `UNKNOWN` | n/a | n/a | R-4 ⇒ Unknown/Drift Queue |

## 9. Forbidden Routing Behaviors

- Reclassifying a row inside the palette to change its outcome.
- Routing a `BLOCKED_IN_COCKPIT` row to `OpenSafeActionGate` or `OpenSettingsAdminRuntime`.
- Routing an `UNKNOWN` row to any executing outcome.
- Substituting `Inspect` for `OpenSafeActionGate` for a `CONFIRM_REQUIRED` row when the operator chose to run.
- Picking a default outcome that is not in `allowed_palette_outcomes`.
- Background or hidden routing changes.

## 10. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_MAPPING_DECISIONS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
