# Command Palette Index Schema (Human-Readable)

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Companion artifact:** `COMMAND_PALETTE_INDEX_SCHEMA.json`
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)
**safe_for_claude_design:** NO
**READY_FOR_CLAUDE_DESIGN:** not approved

This file explains every field in `COMMAND_PALETTE_INDEX_SCHEMA.json`, where the field comes from, what it means, and how the palette behaves when the field is missing or `UNKNOWN`. The index is a **view** over the carried command inventory and exposure policy. It does not introduce new authority, new counts, or new classifications.

## 1. Per-Row Fields

### 1.1 `command_path`
- **Source.** `COMMAND_INVENTORY.json:rows[*].command_path`.
- **Meaning.** Fully qualified invocation path including subcommands (`./scripts/dopetask doctor`, `dopemux routing status`).
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** Yes. A row without a resolvable `command_path` cannot be routed to the Safe Action Gate or Settings/Admin/Runtime; it routes to Unknown/Drift Queue.

### 1.2 `parent_group`
- **Source.** `COMMAND_INVENTORY.json:rows[*].parent_group`.
- **Meaning.** Top-level command family (`dopetask`, `dopemux routing`, `mcp/servers`).
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** No on its own; missing here does not prevent routing.

### 1.3 `authority_domain`
- **Source.** `COMMAND_INVENTORY.json:rows[*].authority_domain`. Enumerated in `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.authority_domain`.
- **Meaning.** The owning authority for the row. The palette never substitutes its own authority.
- **Missing or `unknown / conflicting`.** Routes to Unknown/Drift Queue. The palette must not invoke the Safe Action Gate when authority is unknown or conflicting.
- **Fail-closed.** Yes.

### 1.4 `canonical_writer`
- **Source.** Derived from `authority_domain` plus the system docs in `docs/03-reference/systems/*` (e.g. `system-dopemux.md`, `system-dopetask.md`, `system-conport.md`).
- **Meaning.** The system or service that owns the write/state mutation. If multiple writers apply, all are listed.
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** Yes. Required for T2–T6 gate tiers in `SAFE_ACTION_GATE_SPEC.md` §2.

### 1.5 `safe_ui_exposure`
- **Source.** `COMMAND_INVENTORY.json:rows[*].safe_UI_exposure` and `COMMAND_EXPOSURE_POLICY.json:classes`.
- **Meaning.** The safety class governing allowed UI form. Values: `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED`, `COMMAND_PALETTE_ONLY`, `BLOCKED_IN_COCKPIT`, `EXTERNAL_ONLY`, `UNKNOWN`.
- **Missing or `UNKNOWN`.** Routes to Unknown/Drift Queue. Forbidden to upgrade to executable inside the palette.
- **Fail-closed.** Yes.

### 1.6 `cockpit_placement`
- **Source.** `COMMAND_INVENTORY.json:rows[*].likely_cockpit_placement`.
- **Meaning.** The IA placement assigned by the inventory: `PM`, `Implementer`, `Overview`, `Services`, `Events`, `Command Palette`, `Settings/Admin`, `External/Not Cockpit`, `UNKNOWN`.
- **Missing or `UNKNOWN`.** Routes to Unknown/Drift Queue with placement reason.
- **Fail-closed.** Yes.

### 1.7 `current_cockpit_coverage`
- **Source.** `COMMAND_INVENTORY.json:rows[*].current_Cockpit_coverage`.
- **Meaning.** Whether Cockpit currently has coverage for this row: `PARTIAL`, `MISSING`, `UNKNOWN`, `OUT_OF_SCOPE`.
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** No on its own; `MISSING` and `UNKNOWN` show as filterable badges and feed Unknown/Drift Queue when combined with other gaps.

### 1.8 `activation_status`
- **Source.** `COMMAND_INVENTORY.json:rows[*].activation_status`.
- **Meaning.** Whether the runtime registered the row: `ACTIVE`, `DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`, `DEPRECATED_BLOCKED`.
- **Missing or non-`ACTIVE`.** Routes to Unknown/Drift Queue. Per `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1.
- **Fail-closed.** Yes when not `ACTIVE`.

### 1.9 `source_file`
- **Source.** `COMMAND_INVENTORY.json:rows[*].source_file`.
- **Meaning.** Repo-relative path to the file that defines the row.
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** No on its own.

### 1.10 `source_symbol`
- **Source.** `COMMAND_INVENTORY.json:rows[*].source_symbol`.
- **Meaning.** Function, class, or registration symbol within `source_file`.
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** No on its own.

### 1.11 `help_text_or_summary`
- **Source.** `COMMAND_INVENTORY.json:rows[*].help_text` or docstring.
- **Meaning.** Short human-readable description for display only.
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** No.

### 1.12 `evidence_path_or_command`
- **Source.** `COMMAND_INVENTORY.json:rows[*].evidence_path_or_command`.
- **Meaning.** Path or command that proves the row exists (manifest entry, inspect command).
- **Missing.** Renders as `UNKNOWN`.
- **Fail-closed.** No on its own; required for the Inspect outcome's evidence display.

### 1.13 `parameter_schema`
- **Source.** Derived from parsing `source_file` / `source_symbol` plus carried inventory parameters.
- **Meaning.** Structured description of:
  - `required_parameters` — must be provided; preview refuses to invoke gate if any value is `UNKNOWN`.
  - `optional_parameters` — defaults made explicit; never implicit.
  - `cwd_target` — must be the current worktree, never `/tmp` as authoritative.
  - `output_target` — file path, log target, dry-run output, or `NOT_APPLICABLE`.
  - `side_effects` — enumerated set (config mutation, write local, write remote, start service, stop service, execution handoff, none).
- **Missing.** `UNKNOWN`.
- **Fail-closed.** Yes. A row whose required parameters are unresolved cannot reach the Safe Action Gate; it routes to Unknown/Drift Queue with reason `PARAM_UNRESOLVED`.

### 1.14 `proof_requirement`
- **Source.** Derived from `safe_ui_exposure` and `SAFE_ACTION_GATE_SPEC.md` §1.
- **Meaning.** Required post-action proof category. Values: `NONE`, `INSPECT_RESULT_AND_TIMESTAMP`, `ARTIFACT_AND_CHECKSUM`, `CONFIG_DIFF_OR_STATUS`, `FILESYSTEM_DIFF_OR_EXIT_CODE`, `REMOTE_RECEIPT`, `SERVICE_STATUS_AND_LOG`, `TP_RUNNER_PROOF`, `BLOCK_REASON_RECORD`, `INVESTIGATION_PACKET_REFERENCE`.
- **Missing.** `UNKNOWN`.
- **Fail-closed.** Yes.

### 1.15 `gate_tier`
- **Source.** Derived from `safe_ui_exposure` plus `parameter_schema.side_effects`. Tiered per `SAFE_ACTION_GATE_SPEC.md` §1.
- **Meaning.** Confirmation tier: `T0` (display only), `T0i` (inspect), `T1` (generated artifact), `T2` (config mutation), `T3` (write local), `T4` (write remote), `T5` (start/stop service), `T6` (execution handoff), `TX` (blocked), `TU` (unknown).
- **Missing.** `UNKNOWN`.
- **Fail-closed.** Yes.

### 1.16 `allowed_palette_outcomes`
- **Source.** Derived per row from `safe_ui_exposure`, `cockpit_placement`, `activation_status`, `current_cockpit_coverage`.
- **Meaning.** The candidate set of outcomes for this row: `Inspect`, `CopyCommand`, `OpenSafeActionGate`, `OpenSettingsAdminRuntime`, `ShowBlockedReason`, `ShowUnknownDriftReason`. Exactly one resolves at click; the list is the candidate set.
- **Missing or empty.** Fail-closed; routes to Unknown/Drift Queue.
- **Fail-closed.** Yes when empty.

### 1.17 `blocked_reason`
- **Source.** `COMMAND_INVENTORY.json:rows[*].blocked_reason`, or derived from `safe_ui_exposure == 'BLOCKED_IN_COCKPIT'` or `activation_status == 'DEPRECATED_BLOCKED'`.
- **Meaning.** Human-readable block reason, replacement command (if any), required external workflow.
- **Missing.** `UNKNOWN`.
- **Fail-closed.** Yes for blocked rows. A blocked row whose `blocked_reason` is `UNKNOWN` routes to the Unknown/Drift Queue with both `BLOCKED` and `UNKNOWN_REASON` flags.

### 1.18 `unknown_reason`
- **Source.** Derived when any of: `authority_domain == 'unknown / conflicting'`, `activation_status in {'DEFINED_NOT_REGISTERED','OPTIONAL_IMPORT_UNKNOWN'}`, `safe_ui_exposure == 'UNKNOWN'`, `current_cockpit_coverage in {'UNKNOWN','MISSING'}`.
- **Meaning.** Why the row is unknown or has drift. Used by the Unknown/Drift Queue.
- **Missing.** `UNKNOWN`.
- **Fail-closed.** Yes for unknown rows.

### 1.19 `updated_at_or_source_timestamp`
- **Source.** `COMMAND_INVENTORY.json` metadata or filesystem `mtime` of `source_file`.
- **Meaning.** ISO-8601 UTC timestamp the row was last sourced. Stale entries (beyond a configured window in the runtime packet) route to Unknown/Drift Queue with reason `STALE_INDEX`.
- **Missing.** `UNKNOWN`.
- **Fail-closed.** No on its own; staleness is enforced by the runtime, not by this packet.

## 2. Row Validation Rules (RV-1 .. RV-11)

These are enumerated normatively in `COMMAND_PALETTE_INDEX_SCHEMA.json:row_validation_rules`. Summary:

- **RV-1.** `safe_ui_exposure == UNKNOWN` ⇒ outcomes are exactly `[ShowUnknownDriftReason]`, tier `TU`.
- **RV-2.** `safe_ui_exposure == BLOCKED_IN_COCKPIT` ⇒ outcomes exactly `[ShowBlockedReason]`, tier `TX`, `blocked_reason` must not be `UNKNOWN`.
- **RV-3.** `safe_ui_exposure == EXTERNAL_ONLY` ⇒ outcomes are subset of `[CopyCommand, Inspect]`, tier `T0i` or `TX`.
- **RV-4.** `safe_ui_exposure == DISPLAY_ONLY` ⇒ outcomes include `Inspect`; no executing outcome; tier `T0`.
- **RV-5.** `safe_ui_exposure == INSPECT_ACTION` ⇒ outcomes include `Inspect`; no executing outcome; tier `T0i`.
- **RV-6.** `safe_ui_exposure == CONFIRM_REQUIRED` ⇒ resolves to `OpenSafeActionGate` (or `OpenSettingsAdminRuntime` which itself invokes the gate); tier `T1–T6`; no auto-confirm.
- **RV-7.** `safe_ui_exposure == COMMAND_PALETTE_ONLY` ⇒ reachable via palette only; never a mode home button.
- **RV-8.** `activation_status` non-`ACTIVE` ⇒ outcomes restricted to `{Inspect, ShowBlockedReason, ShowUnknownDriftReason, CopyCommand}`; no gate handoff.
- **RV-9.** `authority_domain == 'unknown / conflicting'` OR `canonical_writer == UNKNOWN` ⇒ Unknown/Drift Queue route only.
- **RV-10.** Any required parameter unresolved ⇒ Unknown/Drift Queue with `PARAM_UNRESOLVED`.
- **RV-11.** `cockpit_placement == External/Not Cockpit` ⇒ outcomes subset of `[Inspect, CopyCommand]`; tier `T0i` or `TX`.

## 3. Index Invariants

The index, as a whole, must satisfy:

1. **Every row has every required field.** Missing fields are stored as the literal string `UNKNOWN`, never `null`, never absent.
2. **Counts match carried inputs.** Row counts grouped by `safe_ui_exposure`, `cockpit_placement`, `activation_status`, `current_cockpit_coverage`, and `authority_domain` must match `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`. The palette is a view, not a source of new counts.
3. **No new authority.** No row may be assigned an `authority_domain` or `canonical_writer` outside the carried set.
4. **No reclassification inside the palette.** Reclassification requires a packet (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5).
5. **Provenance preserved end-to-end.** `source_file`, `source_symbol`, and `evidence_path_or_command` follow the row from index to gate handoff.

## 4. Forbidden Index Behaviors

- Inferring a `safe_ui_exposure` not present in the carried policy.
- Inventing an `authority_domain` not in the carried set.
- Defaulting required parameters to silently change side effects.
- Caching a stale `safe_ui_exposure` that disagrees with the carried policy.
- Hiding `BLOCKED_IN_COCKPIT` rows from search.
- Removing `UNKNOWN` rows from the index.

## 5. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_MAPPING_DECISIONS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
