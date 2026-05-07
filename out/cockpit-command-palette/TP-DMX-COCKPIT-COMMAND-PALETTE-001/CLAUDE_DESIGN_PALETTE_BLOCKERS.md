# Claude Design Palette Blockers

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)
**Inherits from:** `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`

## 1. Header State (Preserved)

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- `ia_verdict: CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`

This packet does **not** approve final Cockpit screens, runtime flows, destructive affordances, or completeness claims. The upstream `CLAUDE_DESIGN_BLOCKERS.md` is the canonical Claude Design blocker statement; this file restates and extends it for the palette specifically.

## 2. Why The Palette Is Blocked At Claude Design

Even though this packet defines a complete primitive-level palette contract, the palette cannot be drawn at Claude Design fidelity yet. The remaining Claude Design dependencies are:

| # | Dependency | Source |
| --- | --- | --- |
| 1 | Safe Action Gate primitive must be wired (T0i–T6 with proof). | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 2; `OPUS_REMEDIATION_PLAN.md` §1 `TP-DMX-COCKPIT-SAFE-ACTIONS-001`. |
| 2 | Settings/Admin/Runtime surface must exist with gate-driven flows. | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 3; `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`. |
| 3 | Unknown/Drift Queue surface must exist and be visible. | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 4; `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001`. |
| 4 | Cockpit package IA must be reconciled against `REVISED_COCKPIT_IA.md`. | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 5; `TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA`. |
| 5 | Runtime renderer must validate against the screen contracts. | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 6; `TP-DMX-COCKPIT-RUNTIME-RENDER-001`. |
| 6 | Inventory must be regenerated against current HEAD; runtime `dopemux help` resolved. | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 7. |
| 7 | Open UNKNOWNs from `EVIDENCE_LEDGER.md` must be reduced. | `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 8. |

This packet contributes Condition 1 of the eight upstream conditions (`Command Palette broker is wired and conformant`) but the remaining seven still hold.

## 3. What This Packet Approves

This packet approves only:

- A primitive-level Command Palette contract (broker, not executor).
- A row-level index schema and routing rules.
- Handoff payload contracts to the Safe Action Gate, Settings/Admin/Runtime, and Unknown/Drift Queue.
- Proof-receipt schemas at routing time.
- Blocked/unknown state display rules.

These are inputs to downstream packets. They are **not** Claude Design uploads, screens, runtime code, or package edits.

## 4. What This Packet Does Not Approve (Explicit)

- No final palette screens at Claude Design fidelity.
- No upload to Claude Design.
- No primary CTA buttons on `BLOCKED_IN_COCKPIT` rows.
- No primary CTA buttons on `UNKNOWN` rows.
- No mode-bar shortcuts for `COMMAND_PALETTE_ONLY` rows.
- No reclassification of any inventory row.
- No runtime execution flows.
- No remote-mutation flows (T4) approved without a remote-mutation policy and a wired gate.
- No PR Merge execution flows.
- No completeness claim for the Cockpit IA.
- No staging, commits, pushes, or PRs.

## 5. Palette-Specific Unblock Conditions (To Reach Claude Design)

Claude Design can receive **palette primitive sketches only** when:

| # | Condition | Evidence |
| --- | --- | --- |
| P-1 | This packet is accepted by the supervisor. | Supervisor verdict on `TP-DMX-COCKPIT-COMMAND-PALETTE-001`. |
| P-2 | Safe Action Gate contract is available as a sibling primitive. | `TP-DMX-COCKPIT-SAFE-ACTIONS-001` complete. |
| P-3 | Settings/Admin/Runtime contract is available as a sibling primitive. | `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001` complete. |
| P-4 | Unknown/Drift Queue contract is available as a sibling primitive. | `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001` complete. |
| P-5 | Inventory regenerated against current HEAD. | Inventory refresh workstream complete. |
| P-6 | Open UNKNOWNs reduced (root `RULES.md`, `TRUTH_*.md`, `worktree`/`vault` registration, optional `genetic`, `litellm` import). | UNKNOWN reduction workstream complete. |

**Even with P-1 through P-6 satisfied, Claude Design receives palette _primitive sketches only_, not final palette screens.** Final palette screens require the full eight-condition unblock from `CLAUDE_DESIGN_BLOCKERS.md` §3.

## 6. Forbidden Claims In This Packet

- Claiming `READY_FOR_CLAUDE_DESIGN`.
- Claiming `safe_for_claude_design: YES`.
- Claiming Cockpit completeness or readiness for final screens.
- Claiming the palette executes commands.
- Claiming a sixth top-level mode.
- Claiming reclassification of `UNKNOWN` rows.
- Claiming the palette has authority over any system.

## 7. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/REVISED_COCKPIT_IA.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/OPUS_REMEDIATION_PLAN.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UPDATED_COVERAGE_DECISION.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/PROOF.json`
