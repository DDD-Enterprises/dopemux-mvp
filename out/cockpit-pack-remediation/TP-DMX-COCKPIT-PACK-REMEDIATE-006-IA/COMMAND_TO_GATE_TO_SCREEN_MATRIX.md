# Command → Gate → Screen Matrix

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This matrix cross-walks every command-exposure axis to its assigned gate tier, screen contract, proof requirement, allowed palette outcome, and routing destination. The matrix is **derived** from the carried inventory; this packet does not regenerate or change the underlying counts. UNKNOWN axes remain UNKNOWN.

## 1. Master Cross-Walk

| Safety class | Default gate tier | Confirmation strength | Allowed palette outcomes | Default screen contract | Proof requirement category | Inventory rows |
| --- | --- | --- | --- | --- | --- | --- |
| `DISPLAY_ONLY` | T0 | None | `Inspect` | Per-screen contract for the display location (Overview status row, mode row, badge). | `INSPECT_RESULT_AND_TIMESTAMP` (at view time) | 178 |
| `INSPECT_ACTION` | T0i | Explicit invoke (no defaults-on) | `Inspect` | Inspect drawer in current mode | command path + exit/result + source authority | 23 |
| `CONFIRM_REQUIRED` (generated artifact) | T1 | Explicit button | `Inspect`, `OpenSafeActionGate` | Per-mode confirm flow (Implementer/Palette common) | `ARTIFACT_AND_CHECKSUM` | (subset of 111) |
| `CONFIRM_REQUIRED` (config mutation) | T2 | Explicit button + diff acknowledgment | `Inspect`, `OpenSafeActionGate` (Palette) or `OpenSettingsAdminRuntime` | Settings/Admin/Runtime flow group (Routing/Profile/Env/MCP/Hooks/Runtime/Admin) | `CONFIG_DIFF_OR_STATUS` | (subset of 111) |
| `CONFIRM_REQUIRED` (write local) | T3 | Explicit button | `Inspect`, `OpenSafeActionGate` | Per-mode confirm flow | `FILESYSTEM_DIFF_OR_EXIT_CODE` | (subset of 111) |
| `CONFIRM_REQUIRED` (write remote) | T4 | Explicit button + typed confirmation | `Inspect`, `OpenSafeActionGate` (only if remote-mutation policy in scope) | Per-mode confirm flow gated by remote-mutation policy | `REMOTE_RECEIPT` | (subset of 111; **blocked by default**) |
| `CONFIRM_REQUIRED` (start/stop service) | T5 | Explicit button + typed service-id | `Inspect`, `OpenSafeActionGate` (Palette) or `OpenSettingsAdminRuntime` (admin) | Services or Settings/Admin/Runtime Service startup/lifecycle | `SERVICE_STATUS_AND_LOG` | (subset of 111) |
| `CONFIRM_REQUIRED` (execution handoff) | T6 | Explicit button + typed TP-id | `Inspect`, `OpenSafeActionGate` | Implementer / Execution Handoff | `TP_RUNNER_PROOF` | (subset of 111) |
| `COMMAND_PALETTE_ONLY` | T0i if inspect; T1–T6 by side effect | Explicit invoke (T0i) or per-tier (T1–T6) | `Inspect`, `OpenSafeActionGate`, `OpenSettingsAdminRuntime` | Palette home; admin via Settings/Admin/Runtime | per tier | 40 |
| `BLOCKED_IN_COCKPIT` | TX | None (never executable) | `ShowBlockedReason` | Blocked-row inspector inside palette / originating surface | `BLOCK_REASON_RECORD` | 48 |
| `EXTERNAL_ONLY` | T0i or TX (no execution path in Cockpit) | None for execution | `Inspect`, `CopyCommand` | External-only row; copy-to-clipboard | (none — externally executed) | 37 |
| `UNKNOWN` | TU | None (never executable) | `ShowUnknownDriftReason` | Unknown/Drift Queue | `INVESTIGATION_PACKET_REFERENCE` | 5 |

(Sources: `COMMAND_EXPOSURE_POLICY.json:classes` + `COMMAND_PALETTE_INDEX_SCHEMA.json:fields.proof_requirement.enum` + `SAFE_ACTION_GATE_TIER_SCHEMA.json` + `SCREEN_CONTRACT_MATRIX.md` + `PALETTE_ROUTING_RULES.md` §2 + `SETTINGS_ADMIN_RUNTIME_SPEC.md` §4.)

## 2. Placement → Default Routing

| `cockpit_placement` | Inventory rows | Default routing | Notes |
| --- | --- | --- | --- |
| `Command Palette` | 139 | Inspect/Preview inline; executable rows handed off to Safe Action Gate or Settings/Admin/Runtime per side-effect class. | Palette is the home. |
| `Implementer` | 73 | Contextual Inspect drawer in Implementer; executable rows handed off to Safe Action Gate (T6 if execution handoff). | TP gate emphasis. |
| `Settings/Admin` | 62 | Palette routes to `OpenSettingsAdminRuntime`; surface invokes Safe Action Gate. **Never bypass the surface.** | Admin emphasis. |
| `Services` | 54 | Contextual Inspect drawer in Services; service start/stop handed off to Safe Action Gate (T5). | Per-service authority preserved. |
| `External/Not Cockpit` | 37 | Palette permits `Inspect` and `CopyCommand` only. No execution path. | Documentation only. |
| `Events` | 15 | Contextual Inspect drawer in Events; capture/emit handed off to Safe Action Gate. | dope-memory chronicle authority preserved. |
| `PM` | 15 | Contextual Inspect drawer in PM; executable rows handed off to Safe Action Gate. | No claim of unified PM truth. |
| `Overview` | 9 | Contextual Inspect drawer in Overview; no mutation in Overview. | Drift summary surface. |
| `UNKNOWN` | 1 | Force-route to Unknown/Drift Queue (`ShowUnknownDriftReason`). | Never executes. |

(Source: `PALETTE_ROUTING_RULES.md` §3.)

## 3. Activation → Routing Override

| `activation_status` | Inventory rows | Override behavior |
| --- | --- | --- |
| `ACTIVE` | 366 | No override; class/placement routing applies. |
| `DEFINED_NOT_REGISTERED` | 30 | Force-route to Unknown/Drift Queue (`Inspect`/`CopyCommand` allowed for documentation). |
| `OPTIONAL_IMPORT_UNKNOWN` | 2 | Force-route to Unknown/Drift Queue. |
| `DEPRECATED_BLOCKED` | 7 | Force-route to `ShowBlockedReason`. |

(Source: `PALETTE_ROUTING_RULES.md` §4.)

## 4. Authority → Routing Override

| `authority_domain` | Inventory rows | Override behavior |
| --- | --- | --- |
| Resolved (9 enumerated) | 391 | No override; class/placement/activation routing applies. |
| `unknown / conflicting` | 14 | Force-route to Unknown/Drift Queue with reason `AUTHORITY_CONFLICT`. |

(Source: `PALETTE_ROUTING_RULES.md` §5.)

## 5. Coverage → Routing Modifier

| `current_cockpit_coverage` | Inventory rows | Modifier |
| --- | --- | --- |
| `PARTIAL` | 82 | No override. Display `coverage:PARTIAL` badge. |
| `OUT_OF_SCOPE` | 7 | Force-route to `ShowBlockedReason` or `Inspect` (whichever class allows). |
| `MISSING` | 284 | Display `coverage:MISSING` badge. If combined with another unknown axis, route to Unknown/Drift Queue. |
| `UNKNOWN` | 32 | Display `coverage:UNKNOWN` badge. If combined with another unknown axis, route to Unknown/Drift Queue. |

(Source: `PALETTE_ROUTING_RULES.md` §6.)

## 6. Cross-Walk Examples (From Carried Inventory; Illustrative Only)

These rows are taken verbatim from `COMMAND_EXPOSURE_POLICY.json:classes.examples_from_inventory`. No new classification is asserted.

| Example row | Class | Activation | Placement | Default tier | Default outcome | Proof requirement |
| --- | --- | --- | --- | --- | --- | --- |
| `./scripts/dopetask` | `DISPLAY_ONLY` | `ACTIVE` | (n/a — display) | T0 | `Inspect` | `INSPECT_RESULT_AND_TIMESTAMP` |
| `./scripts/dopetask doctor` | `INSPECT_ACTION` | `ACTIVE` | Implementer/Palette | T0i | `Inspect` (executable inspect) | command path + exit/result |
| `./scripts/dopetask collect-evidence` | `CONFIRM_REQUIRED` | `ACTIVE` | Implementer/Palette | T1 | `OpenSafeActionGate` | `ARTIFACT_AND_CHECKSUM` |
| `./scripts/dopetask compile-tasks` | `CONFIRM_REQUIRED` | `ACTIVE` | Implementer/Palette | T1 | `OpenSafeActionGate` | `ARTIFACT_AND_CHECKSUM` |
| `./scripts/dopetask bundle export` | `CONFIRM_REQUIRED` | `ACTIVE` | Implementer/Palette | T1 | `OpenSafeActionGate` | `ARTIFACT_AND_CHECKSUM` |
| `./scripts/dopetask project init` | `COMMAND_PALETTE_ONLY` | `ACTIVE` | Settings/Admin or Palette | T2 (config) | `OpenSettingsAdminRuntime` (admin) or `OpenSafeActionGate` (palette home) | `CONFIG_DIFF_OR_STATUS` |
| `./scripts/dopetask project mode set` | `COMMAND_PALETTE_ONLY` | `ACTIVE` | Settings/Admin or Palette | T2 (config) | `OpenSettingsAdminRuntime` | `CONFIG_DIFF_OR_STATUS` |
| `./scripts/dopetask commit-run` | `BLOCKED_IN_COCKPIT` | n/a | (not executable) | TX | `ShowBlockedReason` | `BLOCK_REASON_RECORD` |
| `./scripts/dopetask commit-sequence` | `BLOCKED_IN_COCKPIT` | n/a | (not executable) | TX | `ShowBlockedReason` | `BLOCK_REASON_RECORD` |
| `./scripts/dopetask finish` | `BLOCKED_IN_COCKPIT` | n/a | (not executable) | TX | `ShowBlockedReason` | `BLOCK_REASON_RECORD` |
| `./scripts/dopetask metrics reset` | `BLOCKED_IN_COCKPIT` | n/a | (not executable) | TX | `ShowBlockedReason` | `BLOCK_REASON_RECORD` |
| `./scripts/dopetask tmux kill` | `BLOCKED_IN_COCKPIT` | n/a | (not executable) | TX | `ShowBlockedReason` | `BLOCK_REASON_RECORD` |
| `./scripts/dopetask manifest check` | `INSPECT_ACTION` | `ACTIVE` | Implementer/Palette | T0i | `Inspect` | command path + exit/result |
| `./scripts/dopetask ops doctor` | `INSPECT_ACTION` | `ACTIVE` | Implementer/Palette | T0i | `Inspect` | command path + exit/result |
| `./scripts/dopetask project doctor` | `INSPECT_ACTION` | `ACTIVE` | Implementer/Palette | T0i | `Inspect` | command path + exit/result |
| `./scripts/dopetask tp git doctor` | `INSPECT_ACTION` | `ACTIVE` | Implementer/Palette | T0i | `Inspect` | command path + exit/result |
| `dopemux decisions energy analytics` | `EXTERNAL_ONLY` | `ACTIVE` | External/Not Cockpit | T0i (read-only inspect) | `Inspect`/`CopyCommand` | (none — externally executed) |
| `dopemux decisions energy log` | `EXTERNAL_ONLY` | `ACTIVE` | External/Not Cockpit | T0i | `Inspect`/`CopyCommand` | (none) |
| `dopemux decisions energy status` | `EXTERNAL_ONLY` | `ACTIVE` | External/Not Cockpit | T0i | `Inspect`/`CopyCommand` | (none) |
| `dopemux decisions graph` | `EXTERNAL_ONLY` | `ACTIVE` | External/Not Cockpit | T0i | `Inspect`/`CopyCommand` | (none) |
| `dopemux decisions list` | `EXTERNAL_ONLY` | `ACTIVE` | External/Not Cockpit | T0i | `Inspect`/`CopyCommand` | (none) |
| `dopemux genetic` | `UNKNOWN` | n/a | UNKNOWN | TU | `ShowUnknownDriftReason` | `INVESTIGATION_PACKET_REFERENCE` |
| `dopemux vault` | `UNKNOWN` | n/a | UNKNOWN | TU | `ShowUnknownDriftReason` | `INVESTIGATION_PACKET_REFERENCE` |
| `dopemux worktree` | `UNKNOWN` | `DEFINED_NOT_REGISTERED` | UNKNOWN | TU | `ShowUnknownDriftReason` | `INVESTIGATION_PACKET_REFERENCE` |
| `dopemux worktrees` | `UNKNOWN` | `DEFINED_NOT_REGISTERED` | UNKNOWN | TU | `ShowUnknownDriftReason` | `INVESTIGATION_PACKET_REFERENCE` |
| `python -m dopemux` | `UNKNOWN` | n/a | UNKNOWN | TU | `ShowUnknownDriftReason` | `INVESTIGATION_PACKET_REFERENCE` |

## 7. Routing Decision Algorithm Reference

The Palette applies routing rules in this exact order; the first rule that fires terminates (verbatim from `PALETTE_ROUTING_RULES.md` §7):

1. **R-1 Index integrity** — fail RV-1..RV-11 ⇒ Unknown/Drift Queue.
2. **R-2 Activation override** — `DEPRECATED_BLOCKED` ⇒ `ShowBlockedReason`; `DEFINED_NOT_REGISTERED` or `OPTIONAL_IMPORT_UNKNOWN` ⇒ Unknown/Drift Queue.
3. **R-3 Authority override** — `unknown / conflicting` or `canonical_writer == UNKNOWN` ⇒ Unknown/Drift Queue with `AUTHORITY_CONFLICT`.
4. **R-4 Class override** — `BLOCKED_IN_COCKPIT` ⇒ `ShowBlockedReason`; `UNKNOWN` ⇒ Unknown/Drift Queue; `EXTERNAL_ONLY` ⇒ `Inspect`/`CopyCommand` only.
5. **R-5 Display/Inspect** — `DISPLAY_ONLY`/`INSPECT_ACTION` ⇒ `Inspect`.
6. **R-6 Parameter resolution** — `CONFIRM_REQUIRED`/`COMMAND_PALETTE_ONLY` with any required param `UNKNOWN` ⇒ Unknown/Drift Queue with `PARAM_UNRESOLVED`.
7. **R-7 Placement disambiguation** — `Settings/Admin` ⇒ `OpenSettingsAdminRuntime`; `External/Not Cockpit` ⇒ `Inspect`/`CopyCommand`; otherwise ⇒ `OpenSafeActionGate`.
8. **R-8 Coverage check** — `OUT_OF_SCOPE` ⇒ restrict to `Inspect`; `MISSING` allows execution but displays `coverage:MISSING` badge.
9. **R-9 Final candidate set** — outcome must be in row's `allowed_palette_outcomes`; otherwise ⇒ Unknown/Drift Queue with `OUTCOME_DENIED`.

## 8. Forbidden Mappings

- Mapping a `BLOCKED_IN_COCKPIT` row to any executable tier.
- Mapping an `UNKNOWN` row to any executable tier.
- Mapping a `Settings/Admin` placement directly to `OpenSafeActionGate` (must go through `OpenSettingsAdminRuntime`).
- Mapping an `External/Not Cockpit` row to any execution path.
- Mapping a `T4` tier without a `remote_mutation_policy_reference` to executable.
- Reclassifying a row inside this matrix.

## 9. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PROOF_REQUIREMENTS.md`
