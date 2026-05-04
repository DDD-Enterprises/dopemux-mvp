# Global Surface Package Matrix

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This matrix specifies, per global / secondary surface, the package-level expectations the runtime renderer and Cockpit package remediation must satisfy. The four surfaces are preserved verbatim. None of them is promoted to a top-level mode. None of them owns authority that the carried inventory does not already place there.

## 1. Per-Surface Package Matrix

### 1.1 Command Palette

| Field | Value | Source |
| --- | --- | --- |
| Surface kind | Global broker — discovery, classification, parameter preview, routing | `COMMAND_PALETTE_CONTRACT.md` §1 |
| Authority owner | dopemux operator control (broker only) | `COMMAND_PALETTE_CONTRACT.md` §8 |
| Inventory rows whose home is here | 139 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Command Palette` |
| Inventory rows that may pass through here from any home | All 405 | by definition (palette is global) |
| Allowed outcomes | `Inspect`, `CopyCommand`, `OpenSafeActionGate`, `OpenSettingsAdminRuntime`, `ShowBlockedReason`, `ShowUnknownDriftReason` | `PALETTE_ROUTING_RULES.md` §1 |
| Executes? | No | `COMMAND_PALETTE_CONTRACT.md` §1 |
| Forbidden outcomes | Any execution; bypassing Settings/Admin/Runtime for `Settings/Admin` rows; bypassing the Safe Action Gate. | `COMMAND_PALETTE_CONTRACT.md` §4; `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §1, §7 |
| Routing axes | `safe_ui_exposure`, `cockpit_placement`, `activation_status`, `authority_domain`, `current_cockpit_coverage` | `PALETTE_ROUTING_RULES.md` §2–§6 |
| Routing decision algorithm | R-1 .. R-9 in order; first rule that fires terminates | `PALETTE_ROUTING_RULES.md` §7 |
| Index schema | `COMMAND_PALETTE_INDEX_SCHEMA.json` (16 fields; UNKNOWN renders literally; 11 row-validation rules RV-1..RV-11) | `COMMAND_PALETTE_INDEX_SCHEMA.json` |
| Proof obligation | Routing receipt per `PALETTE_PROOF_REQUIREMENTS.md`; downstream proof per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md`. | `PALETTE_PROOF_REQUIREMENTS.md` §1; `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` §1 |
| UNKNOWN handling | Any required field UNKNOWN ⇒ refuse; route to Unknown/Drift Queue with the missing-field reason. | `COMMAND_PALETTE_INDEX_SCHEMA.json:fail_closed_rule`; `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1 |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_PALETTE_BLOCKERS.md` |

### 1.2 Settings/Admin/Runtime

| Field | Value | Source |
| --- | --- | --- |
| Surface kind | Major secondary admin/runtime shell | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §1 |
| Authority owner | dopemux operator control + per-flow authority | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §2 |
| Inventory rows placed here | 62 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Settings/Admin` |
| Coverage | MISSING (needs canonical home) | `SCREEN_CONTRACT_MATRIX.md` |
| Flow groups | (1) Routing/Model Provider; (2) Profile management; (3) Environment management; (4) MCP server control; (5) Service startup/lifecycle; (6) Hooks/native-hooks; (7) Runtime configuration; (8) Admin/safe/debug helpers; (9) Drift inspection (read-only). | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §2 |
| Allowed safety classes | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` (admin tier) | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §4 |
| Forbidden safety classes | `BLOCKED_IN_COCKPIT`, `UNKNOWN` execution | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §4, §6 |
| Tier emphasis | T2 config mutation; T5 service start/stop; T0i inspect for diagnostics. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §4 |
| Executes? | No (admin gate then Safe Action Gate) | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3; `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §3 |
| Bypass rule | Palette never bypasses Settings/Admin/Runtime when `cockpit_placement == Settings/Admin`. | `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §1, §7 |
| Drift inspector | Reachable from this surface as read-only. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §2 |
| Forbidden | Adding admin rows to the primary mode bar; mutating routing/env without going through the Safe Action Gate; implicit defaults that change config on selection; treating the surface as a PM or Implementer destination; hiding `BLOCKED_IN_COCKPIT` admin rows. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §6 |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_BLOCKERS.md` §4 |

### 1.3 Safe Actions / Proof Gate

| Field | Value | Source |
| --- | --- | --- |
| Surface kind | Cross-cutting confirmation/preflight/proof/refusal/evidence layer | `SAFE_ACTION_GATE_CONTRACT.md` §1, §2 |
| Authority owner | cross-cutting safety contract; preserves per-row `authority_domain` and `canonical_writer`. | `SAFE_ACTION_GATE_CONTRACT.md` §7 |
| Tier set | T0, T0i, T1, T2, T3, T4, T5, T6, TX, TU | `SAFE_ACTION_GATE_TIER_SCHEMA.json` |
| Allowed origins | Command Palette, Settings/Admin/Runtime, contextual surface in PM/Implementer/Overview/Services/Events. | `SAFE_ACTION_GATE_CONTRACT.md` §3; `SAFE_ACTION_PREFLIGHT_SCHEMA.json:fields.surface_origin` |
| Forbidden origins | Deep-link, URL parameter, keyboard shortcut bypassing the surface. | `SAFE_ACTION_REFUSAL_RULES.md` §2.11 |
| Confirmation strength by tier | T0: none; T0i: explicit invoke; T1/T2/T3: explicit confirm; T2 also requires diff acknowledgment; T4/T5/T6: explicit confirm + typed confirmation. | `SAFE_ACTION_CONFIRMATION_FLOWS.md` §2 |
| Refusal | 30+ enumerated triggers across identity, authority, class/tier, activation, side-effect, proof, rollback, remote-mutation, service/handoff, provenance, drift, stale, origin/intent, confirmation-flow, and authority-drift. | `SAFE_ACTION_REFUSAL_RULES.md` §2 |
| Proof | Per-tier `proof_artifacts`; required for any completion claim; missing proof ⇒ stale-proof routing to queue. | `SAFE_ACTION_PROOF_REQUIREMENTS.md` §1, §2, §4 |
| Event receipts | 8 event types (`gate_open`, `gate_refuse`, `gate_abort`, `gate_timeout`, `gate_confirmed`, `gate_proof_captured`, `gate_proof_incomplete`, `gate_proof_stale`); append-only; UTC; secrets redacted. | `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` §1, §2, §5, §6 |
| UI primitives | 13 primitives: preflight panel, missing-field row, authority/writer/tier/proof-requirement badges, side-effect summary, confirmation control, typed confirmation field, refused state, completed-with-proof state, stale-proof state, blocked state, unknown state. | `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §1 |
| Executes (in this packet)? | No (contract-only) | `SAFE_ACTION_GATE_CONTRACT.md` §4 |
| T4 status | Blocked by default until remote-mutation policy approves and runtime renderer wires it. | `SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T4` |
| Forbidden | Auto-confirm; in-gate reclassification; `BLOCKED_IN_COCKPIT`/`UNKNOWN` execution; final screens. | `SAFE_ACTION_GATE_CONTRACT.md` §5, §6, §9 |
| Final screens | BLOCKED. Primitive sketches only after acceptance. | `CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md` §3, §6 |

### 1.4 Unknown / Drift Queue

| Field | Value | Source |
| --- | --- | --- |
| Surface kind | Non-executable visibility queue | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1 |
| Authority owner | drift evidence (no execution) | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1 |
| What goes in | `safe_ui_exposure == UNKNOWN`; `activation_status` non-`ACTIVE`; `authority_domain == 'unknown / conflicting'`; `safe_ui_exposure == BLOCKED_IN_COCKPIT` (visibility only); `current_cockpit_coverage == MISSING` combined with another unknown axis; stale-proof tag; drifted classification. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1 |
| Inventory counts triggering this surface | `coverage.MISSING = 284`; `coverage.UNKNOWN = 32`; `safe_ui_exposure.UNKNOWN = 5`; `safe_ui_exposure.BLOCKED_IN_COCKPIT = 48`; `activation_status.DEFINED_NOT_REGISTERED = 30`; `activation_status.OPTIONAL_IMPORT_UNKNOWN = 2`; `activation_status.DEPRECATED_BLOCKED = 7`; `authority_domain.unknown / conflicting = 14`. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1 |
| What does NOT go in | Rows with confident placement, valid authority, resolved class; rows waiting only on a parameter (those stay in Palette with UNKNOWN parameter); successful recent actions (those go to Events / evidence stream). | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §2 |
| Per-row required fields | trigger reason; command path or symbol/source; authority domain; last activation status; coverage; block reason or external workflow; required investigation packet; last evidence timestamp / proof reference. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §4 |
| Promotion rule | Rows leave the queue only via packet evidence (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5). No in-queue reclassification. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5 |
| Reachability | From Overview drift summary; from Palette filters (`status:UNKNOWN`, `status:BLOCKED`, `coverage:MISSING`, `proof:STALE`); from Settings/Admin/Runtime as read-only inspector. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §6 |
| Executes? | Never. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3 |
| Forbidden | Execution affordance; copy-as-run shortcut bypassing Palette + Gate; silent reclassification; "promote" affordance; auto-retry of stale-proof actions; suppression of `BLOCKED_IN_COCKPIT` rows. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3 |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_BLOCKERS.md` §4 |

## 2. Cross-Surface Routing Topology

```
Palette ─────► Gate ─────► Runtime authority
   │  (executes through)
   │
   ├────► Settings/Admin/Runtime ───► Gate ───► Runtime authority
   │
   ├────► ShowBlockedReason (TX, DEPRECATED_BLOCKED)
   │
   └────► Unknown / Drift Queue (UNKNOWN, NOT_ACTIVE, AUTHORITY_CONFLICT, MISSING+UNKNOWN-axes,
                                  stale proof, drifted classification)

PM/Implementer/Overview/Services/Events contextual surface
   │
   └────► Gate ─────► Runtime authority   (same gate; surface_origin tagged)

Gate refusal ─────► Unknown / Drift Queue (or ShowBlockedReason for blocked)
Gate stale proof ──► Unknown / Drift Queue with stale_proof tag
Gate index drift ──► Re-render at upstream surface; require new handoff
```

## 3. Cross-Surface Forbidden Behaviors

- Promoting any global surface to a top-level mode.
- Executing from any global surface (Palette, Settings/Admin/Runtime, Unknown/Drift Queue).
- Bypassing Settings/Admin/Runtime for `Settings/Admin` rows.
- Bypassing the Safe Action Gate for any non-read action.
- Reclassifying inside any surface (requires a packet).
- Hiding the authority owner, canonical writer, safety class, or proof requirement.
- Final screens.

## 4. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/RECONCILED_COCKPIT_IA.md` §3, §4, §6, §7, §8
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_CONTRACT.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/CLAUDE_DESIGN_PALETTE_BLOCKERS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_CONTRACT.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`
