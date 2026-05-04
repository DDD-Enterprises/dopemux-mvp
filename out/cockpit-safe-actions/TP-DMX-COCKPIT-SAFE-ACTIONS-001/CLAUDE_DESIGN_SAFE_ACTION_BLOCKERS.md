# Claude Design Safe Action Blockers

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

## 1. Header State (Preserved)

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- `ia_verdict: CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`
- Carried from: `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md` and `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/CLAUDE_DESIGN_PALETTE_BLOCKERS.md`.

This document **does not** approve any final Cockpit screens, Safe Action Gate final visual designs, runtime execution flows, destructive affordances, completeness claims, or Claude Design uploads. It tightens — does not relax — the upstream blockers.

## 2. What This Packet Approves

This packet approves only:

- The Safe Action Gate **contract** (`SAFE_ACTION_GATE_CONTRACT.md`).
- The tier schema (`SAFE_ACTION_GATE_TIER_SCHEMA.json` + `.md`).
- The preflight schema (`SAFE_ACTION_PREFLIGHT_SCHEMA.json` + `.md`).
- The confirmation flows (`SAFE_ACTION_CONFIRMATION_FLOWS.md`).
- The refusal rules (`SAFE_ACTION_REFUSAL_RULES.md`).
- The proof requirements (`SAFE_ACTION_PROOF_REQUIREMENTS.md`).
- The event/receipt schema (`SAFE_ACTION_GATE_EVENT_RECEIPTS.md`).
- The UI primitive component inventory (`SAFE_ACTION_GATE_UI_PRIMITIVES.md`).
- The handoff to Unknown/Drift Queue (`SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`).
- The contract test matrix (`SAFE_ACTION_GATE_TEST_MATRIX.md`).
- This blocker statement.

This packet **does not** approve:

- Final Safe Action Gate screens.
- Runtime execution code or wiring.
- Cockpit package HTML/CSS/React edits.
- ZIP package edits.
- Claude Design uploads.
- T4 (write remote) execution. T4 remains blocked by default until `TP-DMX-COCKPIT-RUNTIME-RENDER-001` and an approved remote-mutation policy ship together.
- TX (blocked) execution. Permanently blocked in Cockpit.
- TU (unknown) execution. Permanently blocked until reclassified through a packet.

## 3. Why Final Safe Action Gate Screens Remain Blocked

Approving final Safe Action Gate screens now would commit the system to:

- A confirmation surface that has not yet been wired to any runtime authority owner.
- A proof-display surface that has no runtime proof emission to render (`TP-DMX-COCKPIT-RUNTIME-RENDER-001` not yet complete).
- A typed-confirmation pattern that has not yet been validated against actual T4/T5/T6 flows.
- A blocked-state and unknown-state visual treatment that may shift after the Cockpit IA reconciliation propagates through the Cockpit package and the Unknown/Drift Queue surface.
- A receipt schema that, while normative here, has not been validated end-to-end against the evidence stream the runtime renderer will implement.

Final-screen approval is therefore deferred to the conditions enumerated in §4.

## 4. Exact Unblock Conditions (Carried + Tightened)

The eight upstream conditions from `CLAUDE_DESIGN_BLOCKERS.md` §3 remain in force. This packet **tightens** them with respect to the Safe Action Gate:

| # | Condition | This packet's contribution |
| --- | --- | --- |
| 1 | Command Palette broker is wired and conformant. | The palette → gate handoff (`PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`) is mirrored by the gate's preflight schema. |
| 2 | **Safe Action Gate is wired across all non-read affordances.** | This packet defines the contract; runtime wiring is `TP-DMX-COCKPIT-RUNTIME-RENDER-001`. Tiers T0i–T6 are specified; TX and TU are specified as never-executable. |
| 3 | Settings/Admin/Runtime exists as a secondary surface. | The handoff from Settings/Admin/Runtime to the gate is constrained per `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`. |
| 4 | Unknown/Drift Queue is wired and visible. | The gate's handoff to the queue (`SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`) is specified, including stale-proof routing. |
| 5 | Cockpit package IA reconciled against this revision. | The gate must be one of the four secondary surfaces in the reconciled IA; this packet preserves that. |
| 6 | Runtime renderer validated. | This packet specifies the contract the runtime renderer must satisfy. The renderer is **not** yet validated. |
| 7 | Inventory regenerated against current HEAD. | Tier mapping in this packet uses carried counts; regeneration is needed before final approval. |
| 8 | Open UNKNOWNs reduced. | Per `EVIDENCE_LEDGER.md`; not addressed by this packet. |

Until all eight conditions hold, Claude Design must not be told the Safe Action Gate is ready for final screens.

## 5. Allowed Pre-Design Work (Outside Claude Design)

The following may proceed in non-Claude-Design contexts, contributing to the named remediation packets:

- **Safe Action Gate primitive sketches.** After this packet is accepted, primitive sketches of the gate's UI (preflight panel, confirmation control, refused state, completed-with-proof state, blocked state, unknown state) may be drafted as inputs to `TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA` and `TP-DMX-COCKPIT-RUNTIME-RENDER-001`. These are **inputs**, not approved Claude Design uploads.
- Wiring contracts in the Cockpit shell (palette ⇄ gate ⇄ Settings/Admin/Runtime ⇄ Unknown/Drift Queue) inside the named packets.
- Authoring contract tests against the test matrix in `SAFE_ACTION_GATE_TEST_MATRIX.md`.
- Drafting the remote-mutation policy that T4 requires.
- Drafting the proof-event emission contract for the runtime renderer.

These work items must not produce final Cockpit screens or upload to Claude Design.

## 6. Forbidden Until Unblocked

- Final Safe Action Gate screens of any tier.
- Final final-state visuals (e.g., color/typography/iconography for tier badges, refusal panels, proof-captured states).
- Direct destructive action affordances anywhere in Cockpit.
- One-click flows for `CONFIRM_REQUIRED` rows.
- Buttons or shortcuts that contradict the 48 `BLOCKED_IN_COCKPIT` rows.
- Affordances that confirm or execute `UNKNOWN` rows.
- Final operator copy/microcopy on the gate.
- Any remote-mutating flow without a remote-mutation policy and a wired T4 gate.
- Unified PM or unified-brain screens.
- Claude Design uploads representing final Safe Action Gate screens.
- Stagings, commits, pushes, or PRs from this packet.

## 7. What Claude Design May Receive After Acceptance

After this packet is accepted (validation passes; verdict reaches `SAFE_ACTION_GATE_SPEC_READY_FOR_PACKAGE_REMEDIATION`), Claude Design may receive:

- **Primitive-level sketches** of the gate's UI components: preflight panel, missing-field row, badges, confirmation control, typed confirmation field, refused state, completed-with-proof state, stale-proof state, blocked state, unknown state.
- These sketches are **primitive-level**, not final screens.
- These sketches do **not** approve runtime execution.
- These sketches do **not** approve final visual design or final operator copy.

Final screens for the Safe Action Gate remain blocked until conditions §4 #1–#8 all hold.

## 8. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/CLAUDE_DESIGN_PALETTE_BLOCKERS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_CONTRACT.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_CONTRACT.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TEST_MATRIX.md`
