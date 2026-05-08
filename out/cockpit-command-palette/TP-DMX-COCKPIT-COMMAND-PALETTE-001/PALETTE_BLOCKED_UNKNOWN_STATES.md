# Palette Blocked / Unknown States Specification

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file enumerates the states a palette row can be in when execution is not allowed, and how the palette must render each state. The palette must keep these rows visible (so the operator and the system can see them) without offering any execution affordance.

## 1. State Catalog (Read-Only Per Row)

### 1.1 Blocked Row (`safe_ui_exposure == BLOCKED_IN_COCKPIT`)

Counts (carried): 48 rows.

**Display.**
- Safety badge: `BLOCKED_IN_COCKPIT`.
- Activation badge: as carried (often `ACTIVE` or `DEPRECATED_BLOCKED`).
- Authority badge: as carried.
- Placement badge: as carried (often `External/Not Cockpit` or `Settings/Admin`).
- Block reason text (`blocked_reason`).
- Replacement command text (when present in `blocked_reason`).
- External workflow link (when present).
- No primary outcome button. The affordance region renders a non-clickable blocked chip.

**Required evidence to display.**
- Block reason.
- Replacement command (if any).
- Required external workflow (if any).

**Forbidden affordances.**
- Run button.
- Confirm modal that still executes.
- Keyboard shortcut.

### 1.2 Unknown Row (`safe_ui_exposure == UNKNOWN`)

Counts (carried): 5 rows.

**Display.**
- Safety badge: `UNKNOWN`.
- Activation badge: as carried.
- Authority badge: as carried (often `unknown / conflicting`).
- Placement badge: as carried (often `UNKNOWN`).
- Unknown reason text (`unknown_reason`).
- Required investigation packet reference (when known).
- No primary outcome button.

**Required evidence to display.**
- Missing-authority note.
- Required investigation packet id (when proposed) or `INVESTIGATION_PACKET_REQUIRED` text.

**Forbidden affordances.**
- Execution affordance.
- Success or readiness claim.

### 1.3 Defined-But-Not-Registered Row (`activation_status == DEFINED_NOT_REGISTERED`)

Counts (carried): 30 rows.

**Display.**
- Activation badge: `DEFINED_NOT_REGISTERED` (overrides safety color).
- Source badge: `source_file:source_symbol` (the source defines the row).
- Reason text: "Defined in source but not registered with the runtime."
- Coverage badge: as carried.
- Required investigation packet reference (when known).
- No primary outcome button. `Inspect` and `CopyCommand` may be available for documentation.

**Required evidence to display.**
- Source file and symbol.
- Statement that the runtime has not registered the row.

**Forbidden affordances.**
- `OpenSafeActionGate`.
- `OpenSettingsAdminRuntime`.

### 1.4 Optional Import Unknown Row (`activation_status == OPTIONAL_IMPORT_UNKNOWN`)

Counts (carried): 2 rows.

**Display.**
- Activation badge: `OPTIONAL_IMPORT_UNKNOWN`.
- Reason text: "Optional dependency not present in the inventory environment."
- The original cause (e.g. `litellm` missing) is shown when known.
- No primary outcome button.

**Required evidence to display.**
- Optional dependency name (e.g. `litellm`).
- Required investigation packet reference (when known).

### 1.5 Deprecated Blocked Row (`activation_status == DEPRECATED_BLOCKED`)

Counts (carried): 7 rows.

**Display.**
- Activation badge: `DEPRECATED_BLOCKED`.
- Behaves like `BLOCKED_IN_COCKPIT` for affordances (shows block reason, no run button).
- Replacement command shown when known.
- Authority badge as carried.

### 1.6 External-Only Row (`safe_ui_exposure == EXTERNAL_ONLY`)

Counts (carried): 37 rows.

**Display.**
- Safety badge: `EXTERNAL_ONLY`.
- Activation badge: as carried (often `ACTIVE`).
- Reason text: "Authority lives outside Cockpit."
- Affordances: `Inspect` (informational), `CopyCommand` (clipboard).
- External authority owner shown explicitly.
- External runbook link when present.

**Forbidden affordances.**
- Cockpit execution path.
- State mutation from UI.

### 1.7 Conflicting Authority Row (`authority_domain == 'unknown / conflicting'`)

Counts (carried): 14 rows.

**Display.**
- Authority badge: `UNKNOWN AUTHORITY` (rendered explicitly so it cannot be confused with a resolved authority).
- Reason text: "Multiple authority claims; cannot be safely placed."
- Required investigation packet reference (when known).
- No primary outcome button.

### 1.8 Missing Coverage Row (`current_cockpit_coverage == MISSING`)

Counts (carried): 284 rows.

**Display rule.** Coverage is informational by default. Render the `coverage:MISSING` badge prominently. The row remains executable if `safe_ui_exposure`, `activation_status`, and `authority_domain` are all valid for execution. If any of those are also missing or unknown, route to Unknown/Drift Queue.

### 1.9 Unknown Coverage Row (`current_cockpit_coverage == UNKNOWN`)

Counts (carried): 32 rows.

**Display rule.** Coverage badge `UNKNOWN`. If combined with any other unknown axis, route to Unknown/Drift Queue.

### 1.10 Out-Of-Scope Row (`current_cockpit_coverage == OUT_OF_SCOPE`)

Counts (carried): 7 rows.

**Display rule.** Coverage badge `OUT_OF_SCOPE`. Allowed outcomes restricted to `Inspect` (and `CopyCommand` if class permits).

### 1.11 Stale Proof Row (post-action)

**Display rule.** Stale proof is detected by the runtime, not by this packet. When detected and surfaced via the Unknown/Drift Queue, the palette displays:

- Reason text: "Proof gate stale; row needs re-evidence."
- Last successful proof timestamp (when known).
- Required action: re-execute the gated action (subject to gate rules) or mark `EXTERNAL_ONLY`.

## 2. Affordance Truth Table

| State | Inspect | CopyCommand | Open Safe Action Gate | Open Settings/Admin/Runtime | Show Blocked Reason | Show Unknown/Drift Reason |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Blocked Row | optional | optional (read-only) | NEVER | NEVER | YES | NEVER |
| Unknown Row | optional | NEVER | NEVER | NEVER | NEVER | YES |
| Defined-but-not-registered | YES | YES | NEVER | NEVER | NEVER | YES |
| Optional Import Unknown | YES | NEVER | NEVER | NEVER | NEVER | YES |
| Deprecated Blocked | optional | optional (replacement) | NEVER | NEVER | YES | YES |
| External-Only | YES | YES | NEVER | NEVER | NEVER | NEVER |
| Conflicting Authority | optional | NEVER | NEVER | NEVER | NEVER | YES |
| Missing Coverage (alone) | YES | per class | per class | per placement | NEVER | NEVER |
| Unknown Coverage (alone) | YES | per class | NEVER | NEVER | NEVER | YES |
| Out-Of-Scope | YES | per class | NEVER | NEVER | NEVER | NEVER |
| Stale Proof | YES | NEVER | per class (re-evidence path only) | per placement (re-evidence path only) | NEVER | YES |

## 3. Required Investigation / External Workflow Reference

For every blocked or unknown state above, the palette must surface the path forward without permitting execution:

- **Blocked.** Replacement command (if any) and required external workflow.
- **Unknown.** Required investigation packet id (when known) or `INVESTIGATION_PACKET_REQUIRED`.
- **Defined-but-not-registered.** Source file/symbol and a hint that runtime registration must be repaired or rejected (`OPUS_REMEDIATION_PLAN.md` §2 inventory refresh).
- **Optional import unknown.** Optional dependency name and remediation hint (e.g. install `litellm`).
- **Deprecated blocked.** Replacement command and deprecation note.
- **Conflicting authority.** Note that resolution requires a packet (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5 promotion rules).

## 4. No Execution Path — Reiteration

For all states above, the palette **never** offers execution. The only outcomes available are:

- `Inspect` (for documentation and provenance).
- `CopyCommand` (for external execution outside Cockpit).
- `ShowBlockedReason` (blocked).
- `ShowUnknownDriftReason` (unknown / drift / defined-but-not-registered / optional import unknown / conflicting authority / stale proof).

## 5. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_MAPPING_DECISIONS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`
