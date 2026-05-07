# Claude Design Blockers

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT
**Supersedes (as canonical name):** `CLAUDE_DESIGN_GATE.md`

## 1. Header State

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- `ia_verdict: CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`

This document **does not** approve any final Cockpit screens, runtime flows, destructive affordances, or completeness claims. The carried `CLAUDE_DESIGN_GATE.md` allowed conditional primitives; this normalized output tightens that to **not approved** at the Claude Design boundary, in line with the supervisor thread's required PROOF.json shape.

## 2. Why Claude Design Is Blocked

Claude Design is blocked because the Cockpit IA cannot honor the carried inventory without secondary surfaces and a cross-cutting safety contract that do not yet exist as wired primitives in the Cockpit shell. Approving final screens now would commit the system to:

- An IA that ignores 139 Palette rows and 62 Settings/Admin rows.
- Visual affordances (buttons, shortcuts) that contradict the 48 BLOCKED_IN_COCKPIT rows.
- One-click flows that contradict the 111 CONFIRM_REQUIRED rows.
- A surface that hides 284 MISSING and 32 UNKNOWN coverage rows.
- An execution model that contradicts the authority boundaries documented in the carried artifacts.

## 3. Exact Unblock Conditions

All of the following must be true for Claude Design to be approved for final screens:

| # | Condition | Evidence required to satisfy |
| --- | --- | --- |
| 1 | Command Palette broker is wired and conformant. | Packet `TP-DMX-COCKPIT-COMMAND-PALETTE-001` complete; palette never executes; routes to Safe Action Gate / Settings/Admin/Runtime / Unknown/Drift Queue per row class; index covers all axes in `COMMAND_PALETTE_SPEC.md` §2. |
| 2 | Safe Action Gate is wired across all non-read affordances. | Packet `TP-DMX-COCKPIT-SAFE-ACTIONS-001` complete; tiers T0i–T6 implemented; `BLOCKED_IN_COCKPIT` and `UNKNOWN` rows fail closed. |
| 3 | Settings/Admin/Runtime exists as a secondary surface. | Packet `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001` complete; routing/profile/env/MCP/service-startup/hooks/runtime/admin/debug grouped; per-flow gates wired. |
| 4 | Unknown/Drift Queue is wired and visible. | Packet `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001` complete; surface non-executable; covers UNKNOWN, MISSING, BLOCKED, DEFINED_NOT_REGISTERED, OPTIONAL_IMPORT_UNKNOWN, conflicting authority, stale proof. |
| 5 | Cockpit package IA reconciled against this revision. | Packet `TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA` complete; package IA matches `REVISED_COCKPIT_IA.md` (five top-level modes + four secondary surfaces); no sixth-mode regressions. |
| 6 | Runtime renderer validated. | Packet `TP-DMX-COCKPIT-RUNTIME-RENDER-001` complete; runtime renders contracts in `SCREEN_CONTRACT_MATRIX.md`; proof JSON validation passes; no destructive affordances rendered for blocked rows. |
| 7 | Inventory regenerated against current HEAD. | Inventory regenerated against worktree HEAD; counts match or are diffed and reconciled; runtime `dopemux help` resolved (or explicit UNKNOWN preserved with reason). |
| 8 | Open UNKNOWNs from `EVIDENCE_LEDGER.md` reduced. | Decision subcommands, optional `genetic`, defined-but-not-registered `worktree`/`vault` surfaces resolved or explicitly rejected; root `RULES.md` and `TRUTH_*.md` absences resolved. |

Until all eight conditions hold, Claude Design must not be told that the Cockpit is ready. Conditional primitive approval (the prior carried gate behavior) is **not** equivalent to "ready for final screens" and is no longer sufficient under the supervisor thread's tightened gate.

## 4. Blocked Design Scope

Even with the conditional primitives carried in `CLAUDE_DESIGN_GATE.md`, the following remain blocked under this normalized gate:

- Final screens implying complete command coverage.
- Direct high-risk action buttons.
- Runtime execution flows.
- Destructive action affordances.
- Complete Cockpit readiness claims.
- Unified PM or unified brain screens.
- Any remote-mutating flow without a remote-mutation policy and a wired T4 gate.

## 5. Allowed Pre-Design Work (Outside Claude Design)

The following can proceed in non-Claude-Design contexts (these are not Claude Design approvals; they are inputs to the named remediation packets):

- Drafting Cockpit shell primitives (palette, gate, settings shell, drift queue) inside the named packets.
- Authoring screen contracts and validating them against `SCREEN_CONTRACT_MATRIX.md`.
- Regenerating the command inventory and reconciling counts.

These work items must not produce final Cockpit screens or upload to Claude Design.

## 6. Source Artifact

`CLAUDE_DESIGN_GATE.md` (carried) is preserved as the historical conditional gate. This file is the canonical Claude Design blocker statement for this packet.
