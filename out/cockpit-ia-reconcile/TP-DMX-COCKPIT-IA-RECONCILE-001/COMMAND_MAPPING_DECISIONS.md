# Command Mapping Decisions

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT

This file summarizes the placement decisions used by this packet across the carried command inventory. Counts are taken **only** from carried-forward artifacts. Where a row could not be placed with carried evidence, it is preserved as `UNKNOWN`.

## 1. Source Counts (From Carried Artifacts)

Source: `RECONCILED_COCKPIT_IA.json:counts_used.placement`, `safe_ui_exposure`, `coverage`, `activation_status`, `authority_domain`. Cross-confirmed in `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`.

| Axis | Value | Count |
| --- | --- | --- |
| Total inventory rows | total_inventory_rows | 405 |
| Active rows | activation_status.ACTIVE | 366 |
| Defined but not registered | activation_status.DEFINED_NOT_REGISTERED | 30 |
| Deprecated / blocked | activation_status.DEPRECATED_BLOCKED | 7 |
| Optional import unknown | activation_status.OPTIONAL_IMPORT_UNKNOWN | 2 |
| High-risk rows | high_risk_rows | 199 |

### Placement (carried)

| Placement | Count |
| --- | --- |
| Command Palette | 139 |
| Implementer | 73 |
| Settings/Admin | 62 |
| Services | 54 |
| External/Not Cockpit | 37 |
| Events | 15 |
| PM | 15 |
| Overview | 9 |
| UNKNOWN | 1 |

### Safe UI Exposure (carried)

| Class | Count |
| --- | --- |
| DISPLAY_ONLY | 178 |
| CONFIRM_REQUIRED | 111 |
| BLOCKED_IN_COCKPIT | 48 |
| COMMAND_PALETTE_ONLY | 40 |
| INSPECT_ACTION | 23 |
| UNKNOWN | 5 |

### Coverage (carried)

| Coverage | Count |
| --- | --- |
| MISSING | 284 |
| PARTIAL | 82 |
| UNKNOWN | 32 |
| OUT_OF_SCOPE | 7 |

### Authority Domain (carried)

| Authority | Count |
| --- | --- |
| dopemux operator control | 145 |
| dopetask execution handoff | 109 |
| Repo Truth Extractor audit/extraction | 44 |
| ADHD/operator support | 21 |
| routing/model-provider support | 20 |
| ConPort structured context/decision/progress | 15 |
| dope-memory chronicle | 15 |
| unknown / conflicting | 14 |
| task-orchestrator workflow | 11 |
| dopecon-bridge adapter/proxy/event transport | 11 |

## 2. Mapping Decisions By Surface

These decisions are about **placement of inventory rows** in the reconciled IA. They are not about authority ownership, which remains fixed in the carried authority boundary table.

### PM
- Source count: placement.PM = 15.
- Decision: PM stays a top-level mode. PM rows shown are read/inspect/handoff readiness across split PM authorities. PM does not absorb workflow-mutating rows that belong to task-orchestrator workflow or Implementer execution handoff.
- Rationale: PM is workflow triage; ownership is split across Leantime, task-orchestrator, ConPort, dope-memory.

### Implementer
- Source count: placement.Implementer = 73.
- Decision: Implementer stays a top-level mode. Implementer rows are task focus, evidence, validation, and explicit execution handoff readiness. Execution itself is Safe Action Gate T6.
- Rationale: Implementer must not own execution truth after dopetask handoff.

### Overview
- Source count: placement.Overview = 9.
- Decision: Overview stays a top-level mode. Overview rows are status, health, drift, and safe launches into secondary surfaces. Overview also routes operators to Unknown/Drift Queue.
- Rationale: Operator-level overview lens; no mutation.

### Services
- Source count: placement.Services = 54.
- Decision: Services stays a top-level mode. Services rows are status and child workload inspection. Service start/stop is Safe Action Gate T5; admin lifecycle moves to Settings/Admin/Runtime.
- Rationale: Authority preservation; Services is not the admin/runtime surface.

### Events
- Source count: placement.Events = 15.
- Decision: Events stays a top-level mode. Events rows are chronicle/capture/trigger inspection. Events is not a PM truth replacement.
- Rationale: dope-memory authority boundary preserved.

### Command Palette
- Source count: placement."Command Palette" = 139.
- Decision: Palette is the canonical home for these rows. Palette is a broker. Routing into Safe Action Gate, Settings/Admin/Runtime, or Unknown/Drift Queue per row class.
- Rationale: Rare/parameter-heavy/admin/specialist commands cannot occupy primary mode chrome.

### Settings/Admin/Runtime
- Source count: placement."Settings/Admin" = 62.
- Decision: New canonical secondary surface. Routing/profile/env/MCP/service-startup/hooks/runtime/admin/debug grouping; gate-driven.
- Rationale: Admin/runtime cannot live inside Services or Overview without breaking authority boundaries.

### External / Not Cockpit
- Source count: placement."External/Not Cockpit" = 37.
- Decision: Visible only via Palette `EXTERNAL_ONLY` rows; never executed. Copyable command text and runbook link only.
- Rationale: Authority lives outside Cockpit; we preserve discoverability without claiming ownership.

### Blocked
- Source count: safe_ui_exposure.BLOCKED_IN_COCKPIT = 48.
- Decision: Visible in Palette and Unknown/Drift Queue as blocked rows; no execute affordance under any path.
- Rationale: Fail-closed; Cockpit cannot become a destructive surface.

### Unknown
- Source count: placement.UNKNOWN = 1; coverage.UNKNOWN = 32; safe_ui_exposure.UNKNOWN = 5; activation_status.OPTIONAL_IMPORT_UNKNOWN = 2; activation_status.DEFINED_NOT_REGISTERED = 30; authority_domain."unknown / conflicting" = 14.
- Decision: All flow into Unknown/Drift Queue. Promotion requires a packet (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5).
- Rationale: Unknown rows must never execute; classification cannot happen inside the queue.

## 3. Cross-Surface Notes

- Safe Action Gate is interposed; it is not a placement target. Rows are placed in the surface that is appropriate for the operator's intent and reach the gate from there.
- The IA does not introduce new authority. Every placement preserves the carried authority domain.
- Counts above are reproduced verbatim from carried artifacts. New counts are not invented in this packet.

## 4. Source Artifacts Referenced

- `RECONCILED_COCKPIT_IA.json` (counts_used)
- `COMMAND_EXPOSURE_POLICY.json` (metadata.source_counts)
- `COMMAND_EXPOSURE_POLICY.md`
- `SCREEN_CONTRACT_MATRIX.md`
- `EVIDENCE_LEDGER.md`
- `RECONCILED_COCKPIT_IA.md` §3, §4, §6, §7, §8, §9
