# Top-Level Mode Package Matrix

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This matrix specifies, per top-level Cockpit mode, the package-level expectations the runtime renderer and Cockpit package remediation must satisfy. The five top-level modes are preserved verbatim; **no sixth top-level mode** is introduced. Authority owners are preserved per the carried IA. No final screens are approved.

## 1. Per-Mode Package Matrix

### 1.1 PM

| Field | Value | Source |
| --- | --- | --- |
| Mode index | 1 | `RECONCILED_COCKPIT_IA.md` §4 |
| Authority owner (split) | Leantime, task-orchestrator workflow, ConPort decision/progress, dope-memory receipts | `SCREEN_CONTRACT_MATRIX.md`; `RECONCILED_COCKPIT_IA.md` §9 |
| Allowed safety classes | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (governance gate) | `SCREEN_CONTRACT_MATRIX.md` |
| Forbidden safety classes | `BLOCKED_IN_COCKPIT`, `UNKNOWN`, `EXTERNAL_ONLY` | `SCREEN_CONTRACT_MATRIX.md` |
| Inventory rows placed here | 15 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.PM` |
| Coverage | PARTIAL | `SCREEN_CONTRACT_MATRIX.md` |
| Gate origin | `surface_origin: PM` | `SAFE_ACTION_PREFLIGHT_SCHEMA.json:fields.surface_origin` |
| Settings/Admin route | PM does NOT link directly to admin actions; admin flows must open Palette and route via Settings/Admin/Runtime. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3 |
| Drift route | Drift summary surfaces in Overview; PM links to Overview when drift relevant. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §6 |
| Forbidden | Claiming unified PM truth; subsuming task-orchestrator, ConPort, or dope-memory authority; collapsing authorities into one control brain. | `RECONCILED_COCKPIT_IA.md` §3, §9; `COMMAND_PALETTE_CONTRACT.md` §8 |
| Final screens | BLOCKED. Primitive sketches only after this packet is accepted. | `CLAUDE_DESIGN_BLOCKERS.md` |

### 1.2 Implementer

| Field | Value | Source |
| --- | --- | --- |
| Mode index | 2 | `RECONCILED_COCKPIT_IA.md` §4 |
| Authority owner | dopetask execution handoff + task evidence systems | `SCREEN_CONTRACT_MATRIX.md` |
| Allowed safety classes | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (TP/proof gate) | `SCREEN_CONTRACT_MATRIX.md` |
| Forbidden safety classes | `BLOCKED_IN_COCKPIT`, `UNKNOWN` | `SCREEN_CONTRACT_MATRIX.md` |
| Inventory rows placed here | 73 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Implementer` |
| Coverage | PARTIAL | `SCREEN_CONTRACT_MATRIX.md` |
| Gate origin | `surface_origin: IMPLEMENTER` | `SAFE_ACTION_PREFLIGHT_SCHEMA.json:fields.surface_origin` |
| Tier emphasis | T6 execution handoff (TP id + runner + branch + output target; typed TP-id confirmation). T1 generated artifact also common (e.g., `./scripts/dopetask collect-evidence`). | `SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T6`, `T1` |
| TP gate requirement | TP gate must be present (`tp_gate_present: true`); else refusal `TP_GATE_ABSENT`. | `SAFE_ACTION_REFUSAL_RULES.md` §2.8 |
| Settings/Admin route | Implementer does NOT link directly to admin actions; admin via Palette. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3 |
| Forbidden | Bypassing the TP gate; treating handoff as proof of completion; auto-cancel without runner authority. | `SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T6.forbidden_behaviors` |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_BLOCKERS.md` |

### 1.3 Overview

| Field | Value | Source |
| --- | --- | --- |
| Mode index | 3 | `RECONCILED_COCKPIT_IA.md` §4 |
| Authority owner | dopemux operator control | `SCREEN_CONTRACT_MATRIX.md` |
| Allowed safety classes | `DISPLAY_ONLY`, `INSPECT_ACTION` | `SCREEN_CONTRACT_MATRIX.md` |
| Forbidden safety classes | `BLOCKED_IN_COCKPIT`, `UNKNOWN` | `SCREEN_CONTRACT_MATRIX.md` |
| Inventory rows placed here | 9 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Overview` |
| Coverage | PARTIAL | `SCREEN_CONTRACT_MATRIX.md` |
| Gate origin | `surface_origin: OVERVIEW` | `SAFE_ACTION_PREFLIGHT_SCHEMA.json:fields.surface_origin` |
| Mutation policy | No direct mutation; diagnostics require inspect result evidence (T0i). | `SCREEN_CONTRACT_MATRIX.md` |
| Drift summary | Overview is the canonical drift summary surface; links to Unknown/Drift Queue. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §6 |
| Settings/Admin route | Overview links to Settings/Admin/Runtime from drift / health summaries. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3 |
| Forbidden | Mutation in Overview; presenting drift as resolved without packet evidence. | `SCREEN_CONTRACT_MATRIX.md` |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_BLOCKERS.md` |

### 1.4 Services

| Field | Value | Source |
| --- | --- | --- |
| Mode index | 4 | `RECONCILED_COCKPIT_IA.md` §4 |
| Authority owner | per-service authority; dopemux only as operator control | `SCREEN_CONTRACT_MATRIX.md` |
| Allowed safety classes | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (start/stop through gate) | `SCREEN_CONTRACT_MATRIX.md` |
| Forbidden safety classes | `BLOCKED_IN_COCKPIT`, `UNKNOWN` | `SCREEN_CONTRACT_MATRIX.md` |
| Inventory rows placed here | 54 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Services` |
| Coverage | PARTIAL | `SCREEN_CONTRACT_MATRIX.md` |
| Gate origin | `surface_origin: SERVICES` | `SAFE_ACTION_PREFLIGHT_SCHEMA.json:fields.surface_origin` |
| Tier emphasis | T5 start/stop service (typed service-id confirmation; pre-state snapshot; revert path). | `SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T5` |
| Admin scope | Services covers status and child workload inspection only; admin/runtime mutation flows go through Settings/Admin/Runtime. | `SCREEN_CONTRACT_MATRIX.md`; `SETTINGS_ADMIN_RUNTIME_SPEC.md` §1 |
| Settings/Admin route | Services links to Settings/Admin/Runtime only for admin-level actions. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3 |
| Forbidden | Service start/stop without typed service-id confirmation; treating start as proof of running state without log evidence. | `SAFE_ACTION_GATE_TIER_SCHEMA.json:tiers.T5.forbidden_behaviors` |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_BLOCKERS.md` |

### 1.5 Events

| Field | Value | Source |
| --- | --- | --- |
| Mode index | 5 | `RECONCILED_COCKPIT_IA.md` §4 |
| Authority owner | dope-memory chronicle + upstream event producers | `SCREEN_CONTRACT_MATRIX.md` |
| Allowed safety classes | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (capture/emit) | `SCREEN_CONTRACT_MATRIX.md` |
| Forbidden safety classes | `BLOCKED_IN_COCKPIT`, `UNKNOWN` | `SCREEN_CONTRACT_MATRIX.md` |
| Inventory rows placed here | 15 | `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Events` |
| Coverage | PARTIAL | `SCREEN_CONTRACT_MATRIX.md` |
| Gate origin | `surface_origin: EVENTS` | `SAFE_ACTION_PREFLIGHT_SCHEMA.json:fields.surface_origin` |
| Tier emphasis | T1 generated artifact (capture); T2 config-like for event/trigger config. | INFERRED from `SCREEN_CONTRACT_MATRIX.md` Events row |
| PM authority preserved | Events is chronicle/event/capture, not current PM truth. | `RECONCILED_COCKPIT_IA.md` §3 |
| Settings/Admin route | Events does not link directly to admin actions; admin via Palette → Settings/Admin/Runtime. | `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3 |
| Forbidden | Asserting Events is PM truth; collapsing dope-memory chronicle authority into PM. | `RECONCILED_COCKPIT_IA.md` §3, §9 |
| Final screens | BLOCKED. | `CLAUDE_DESIGN_BLOCKERS.md` |

## 2. Common Per-Mode Package Requirements

Every mode must satisfy:

- **Authority badge** displayed on every action row (per `SAFE_ACTION_GATE_UI_PRIMITIVES.md` §1).
- **Safety class badge** on every row.
- **Tier badge** on every executable row.
- **Coverage badge** when `current_cockpit_coverage in {PARTIAL, MISSING, UNKNOWN, OUT_OF_SCOPE}`.
- **Last evidence timestamp** when available.
- Only allowed safety classes (per the matrix above) reach the row's primary affordance; everything else routes per `PALETTE_ROUTING_RULES.md` (when accessed via the Palette) or per the contextual surface's routing (when originated locally).

## 3. Mode-Level Forbidden Behaviors (Cross-Cutting)

- Adding a sixth top-level mode.
- Subsuming any mode into another.
- Promoting Command Palette, Settings/Admin/Runtime, Safe Action Gate, or Unknown/Drift Queue into a top-level mode.
- Collapsing authority domains across modes (e.g., having PM claim ConPort decision authority).
- Showing direct destructive action buttons.
- Showing one-click flows for `CONFIRM_REQUIRED` rows.
- Hiding `BLOCKED_IN_COCKPIT` rows from the surfaces that should display them as blocked.
- Hiding `UNKNOWN` rows or auto-confirming them.
- Hiding the authority owner, canonical writer, safety class, or proof requirement.

## 4. Per-Mode Operator Affordances (Primitive-Level Only)

The downstream runtime renderer and package remediation are responsible for the actual UI. The package matrix specifies the **affordance shape** at the primitive level. No final visual treatment is approved here.

| Mode | Primary primitive affordances |
| --- | --- |
| PM | Read-only badges; inspect drawer; governance-gated confirm action with tier-specific preflight. |
| Implementer | Read-only badges; inspect drawer; TP-gated confirm with typed TP-id confirmation. |
| Overview | Read-only summaries; inspect drawer; safe launch links into Palette / Settings/Admin/Runtime / Unknown/Drift Queue. |
| Services | Read-only status; inspect drawer; service start/stop via T5 (typed service-id confirmation). |
| Events | Read-only chronicle/event view; inspect drawer; capture/emit via gate. |

## 5. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/RECONCILED_COCKPIT_IA.md` §3, §4, §9
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md` §1, §3
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §6
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_CONTRACT.md` §8
