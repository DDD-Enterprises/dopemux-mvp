# Claude Design Primitive Boundary

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

## 1. Header State (Preserved)

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- `ia_verdict: CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`
- Carried from: `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`, `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/CLAUDE_DESIGN_PALETTE_BLOCKERS.md`, and `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`.

## 2. The Boundary

This packet preserves and **tightens** the Claude Design boundary. Three things are explicitly distinguished:

| Category | Status | Examples |
| --- | --- | --- |
| **Primitive sketches (text-only, low-fidelity, non-final)** | ALLOWED in this packet as inputs to downstream packets. | Text descriptions of preflight panels, missing-field rows, badges, confirmation control, refused state, blocked state. Tables describing layouts. Lists of slot inputs. ASCII routing diagrams. |
| **Primitive components (the conceptual UI primitives)** | DEFINED in `SAFE_ACTION_GATE_UI_PRIMITIVES.md`; **conceptual only**, not visual. | Preflight panel; tier badge; typed confirmation field; etc. |
| **Final screens (visual designs, color/typography/iconography, layout, copy)** | **BLOCKED** at the Claude Design boundary. | High-fidelity mockups, prototypes, color/font specifications, layout grids, motion specs, final operator copy. |

## 3. What Is Allowed Here

Within this packet (and the upstream three packets), the following are allowed:

- Authoring contracts, schemas, matrices, refusal rules, proof requirements, event/receipt shapes, UI primitive component lists.
- Documenting routing topologies as ASCII diagrams.
- Describing per-tier preflight requirements and confirmation flows in text.
- Describing per-row state transitions in text or simple tables.
- Listing forbidden behaviors and refusal triggers.
- Cross-referencing upstream artifacts.

## 4. What Is Allowed After This Packet Is Accepted (Outside Claude Design)

After this packet is accepted (validation passes; no forbidden tracked files modified), the downstream packet authors may produce:

- **Primitive-level sketches** of Cockpit components: navigation skeleton, command palette primitive (search input, result row, filter chips), safe-action confirmation primitive (preflight panel, confirm button, typed confirmation field), proof requirement badge, blocked action row, admin/runtime shell skeleton, drift queue row, screen shell placeholders.
- **Wiring contracts** in the Cockpit shell (palette ⇄ gate ⇄ Settings/Admin/Runtime ⇄ Unknown/Drift Queue).
- **Contract test implementations** against the test matrices in `SAFE_ACTION_GATE_TEST_MATRIX.md` and `PACKAGE_REMEDIATION_TEST_MATRIX.md`.
- **Drafts** of the remote-mutation policy that T4 requires.
- **Drafts** of the proof-event emission contract for the runtime renderer.

These are **inputs** to `TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA` (this packet's downstream wiring counterpart) and `TP-DMX-COCKPIT-RUNTIME-RENDER-001`, **not** approved Claude Design uploads.

## 5. What Remains Blocked (Final-Screen Boundary)

Even after this packet is accepted, the following remain blocked at the Claude Design boundary until **all eight** unblock conditions in `CLAUDE_DESIGN_BLOCKERS.md` §3 hold:

| # | Condition | Owner |
| --- | --- | --- |
| 1 | Command Palette broker is wired and conformant. | TP-DMX-COCKPIT-COMMAND-PALETTE-001 (contract: complete; runtime wiring: pending) |
| 2 | Safe Action Gate is wired across all non-read affordances. | TP-DMX-COCKPIT-SAFE-ACTIONS-001 (contract: complete; runtime wiring: pending) |
| 3 | Settings/Admin/Runtime exists as a secondary surface. | TP-DMX-COCKPIT-SETTINGS-RUNTIME-001 (pending) |
| 4 | Unknown/Drift Queue is wired and visible. | TP-DMX-COCKPIT-UNKNOWN-DRIFT-001 (pending) |
| 5 | Cockpit package IA reconciled against this revision. | This packet contributes to that condition; final wiring still pending. |
| 6 | Runtime renderer validated. | TP-DMX-COCKPIT-RUNTIME-RENDER-001 (pending) |
| 7 | Inventory regenerated against current HEAD. | Separate inventory-regeneration packet (pending) |
| 8 | Open UNKNOWNs from `EVIDENCE_LEDGER.md` reduced. | Separate reclassification packets (pending) |

Approving final screens before all eight conditions hold would commit the system to:

- An IA that ignores 139 Palette rows and 62 Settings/Admin rows.
- Visual affordances (buttons, shortcuts) that contradict the 48 `BLOCKED_IN_COCKPIT` rows.
- One-click flows that contradict the 111 `CONFIRM_REQUIRED` rows.
- A surface that hides 284 `MISSING` and 32 `UNKNOWN` coverage rows.
- An execution model that contradicts authority boundaries.

## 6. Specific Final-Screen Items That Remain Blocked

- Final screens implying complete command coverage.
- Direct high-risk action buttons.
- Runtime execution flows.
- Destructive action affordances.
- Complete Cockpit readiness claims.
- Unified PM screens or unified-brain screens.
- Any remote-mutating flow without a remote-mutation policy and a wired T4 gate.
- Final visual treatment for tier badges (color, type, iconography).
- Final visual treatment for refusal panels.
- Final visual treatment for completed-with-proof states.
- Final visual treatment for stale-proof states.
- Final visual treatment for blocked / unknown states.
- Final operator copy / microcopy on the gate.
- Final layout / responsive breakpoints / animation specs.

## 7. The Two-Level Promotion Path

```
Level 1 (this packet & predecessors):
  • Author contracts, schemas, matrices, refusal rules, proof requirements,
    event/receipt shapes, UI primitive component lists.
  • Author primitive sketches as text-only, low-fidelity, non-final inputs.
  • Validate against test matrices.
  • Produce PROOF.json + sha256sums.txt.

Level 2 (after this packet is accepted):
  • Downstream packets (Settings/Runtime, Unknown/Drift, Runtime Renderer)
    produce wiring contracts, primitive UI sketches, contract tests.
  • Inventory regeneration packet refreshes counts.
  • Remote-mutation policy packet authors T4 policy.
  • Open UNKNOWN reclassifications complete via packet evidence.

Level 3 (only after all 8 conditions hold):
  • Claude Design final-screen review may proceed.
  • Final visual design produced.
  • Final operator copy produced.
  • READY_FOR_CLAUDE_DESIGN may be evaluated.
```

This packet is **Level 1 only**. It does not approve Level 2 outputs and does not approve Level 3 outputs.

## 8. What Claude Design May Receive After This Packet Is Accepted

Only **primitive-level sketches** described in §4. These sketches are **not** final screens, **not** Claude Design upload material, and **not** equivalent to "ready for final screens".

If Claude Design is presented with anything that looks like a final screen, the boundary has been violated. The reviewer must reject and route the violation to the appropriate reclassification packet.

## 9. Forbidden Claims In This Packet

This packet must never claim, implicitly or explicitly, any of the following (sanitized references; literal claim strings are intentionally not reproduced verbatim so that automated grep checks remain valid):

- Setting `READY_FOR_CLAUDE_DESIGN` to the [APPROVED-CLAIM] value (i.e. flipping the gate to approved).
- Setting `safe_for_claude_design` to the [YES-CLAIM] value.
- Stating that Claude Design upload is [PERMITTED-CLAIM].
- Stating that T4 has been [AUTHORIZED-CLAIM].
- Claiming that runtime execution has been [IMPLEMENTED-CLAIM].
- Stating that final screens are approved.
- Stating that the Cockpit is ready (in the readiness/release sense).
- Stating that all UNKNOWNs are resolved.

The sentinel tokens above ([APPROVED-CLAIM], [YES-CLAIM], [PERMITTED-CLAIM], [AUTHORIZED-CLAIM], [IMPLEMENTED-CLAIM]) are sanitized stand-ins. The validation grep in this packet's verify step searches for the **literal** forbidden claim strings; finding any literal string would indicate a real claim slipped into the artifacts. The sentinel form preserves the prohibition without producing a false positive.

## 10. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_GATE.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/RECONCILED_COCKPIT_IA.md` §10
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/CLAUDE_DESIGN_PALETTE_BLOCKERS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md` (primitive component list)
