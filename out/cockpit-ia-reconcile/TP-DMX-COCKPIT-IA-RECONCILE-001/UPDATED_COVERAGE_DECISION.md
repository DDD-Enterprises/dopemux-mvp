# Updated Coverage Decision

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT
**Verdict:** CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION

## 1. Is The Current Five-Mode IA Sufficient?

**No.** The five-mode IA (PM, Implementer, Overview, Services, Events) is necessary as the operator's primary lens but is **insufficient** as the entire Cockpit IA. Carried evidence demonstrates this concretely:

- 139 inventory rows route to a Command Palette that has no formal screen contract.
- 62 inventory rows route to Settings/Admin without a canonical secondary surface.
- 48 BLOCKED_IN_COCKPIT rows have no canonical visible-but-non-executable home.
- 40 COMMAND_PALETTE_ONLY rows must not occupy primary mode chrome.
- 111 CONFIRM_REQUIRED rows have no cross-cutting Safe Action gate contract.
- 284 MISSING + 32 UNKNOWN coverage rows need a non-executable Unknown/Drift Queue.
- 30 DEFINED_NOT_REGISTERED + 2 OPTIONAL_IMPORT_UNKNOWN + 14 conflicting authority rows need queue tracking.

Source: `RECONCILED_COCKPIT_IA.json:counts_used`, `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts`.

The reconciled IA keeps all five modes and **adds** four secondary structures: Command Palette, Settings/Admin/Runtime, Safe Actions / Proof Gate, Unknown / Drift Queue. None of these are new top-level authority modes; all of them are required to honor the inventory.

## 2. Final Claude Design Screens — Status

**Final Claude Design screens remain blocked.**

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- The Cockpit's final per-screen designs cannot be approved until: (a) the Command Palette spec is implemented as a broker; (b) Settings/Admin/Runtime exists with gate-driven flows; (c) Safe Action Gate is wired across all non-read affordances; (d) Unknown/Drift Queue is wired to surface unresolved coverage.

This packet preserves the carried `CLAUDE_DESIGN_GATE.md` for historical reference but supersedes it with the stricter `CLAUDE_DESIGN_BLOCKERS.md` per the supervisor thread's required outputs.

## 3. Package Updates Required Next

The current Cockpit packages (HTML/CSS/React in the design-system review pack and the `ui_kits/cockpit/*` artifacts) cannot be modified inside this packet. The required package updates are queued for downstream packets:

| Required update | Target | Tracking packet |
| --- | --- | --- |
| Add Command Palette broker primitive | Cockpit shell | TP-DMX-COCKPIT-COMMAND-PALETTE-001 |
| Add Safe Action Gate primitive across all classes | Cockpit shell | TP-DMX-COCKPIT-SAFE-ACTIONS-001 |
| Add Settings/Admin/Runtime shell | Cockpit shell | TP-DMX-COCKPIT-SETTINGS-RUNTIME-001 |
| Add Unknown/Drift Queue surface | Cockpit shell | TP-DMX-COCKPIT-UNKNOWN-DRIFT-001 |
| Reconcile package IA against this revision | Cockpit package | TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA |
| Validate runtime renderer against contracts | Cockpit runtime | TP-DMX-COCKPIT-RUNTIME-RENDER-001 |

Within this packet **no package edits, runtime edits, or screen approvals** are produced. Per supervisor instructions: do not modify runtime code, do not modify Cockpit package HTML/CSS/React, do not edit ZIP packages, do not generate final PM or Implementer screens, do not upload to Claude Design.

## 4. Unresolved Proof Gates / Open Items

These items remain unresolved until the appropriate packet runs:

- Runtime `dopemux help` was an UNKNOWN input in the inventory packet because the environment lacked `litellm`. No new inventory was generated here.
- Decision subcommands, optional `genetic`, and defined-but-not-registered `worktree`/`vault` surfaces remain unresolved until runtime registration is repaired or rejected.
- Final runtime renderer, browser visual approval, screenshot approval, and proof JSON validation for Cockpit remain outside this packet.
- Root `RULES.md` is absent in the fresh worktree; `docs/03-reference` and `AGENTS.md` were used.
- Root `TRUTH_*.md` files are absent; `docs/03-reference/truth/*` equivalents were used.
- The carried inventory was generated at HEAD `af5c4627`; this worktree is at `4959a089f` / origin/main `4959a089f`. Inventory was not regenerated.
- Stale-proof gate detection is defined in `SAFE_ACTION_GATE_SPEC.md` §4 but no scan was executed in this packet.

## 5. Verdict

`CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`. The reconciliation deliverables in this packet are sufficient to begin the named remediation packets in §3. They are not sufficient to resume final Claude Design screen approval.

## 6. Source Artifacts Referenced

- `RECONCILED_COCKPIT_IA.json`
- `COMMAND_EXPOSURE_POLICY.json` / `.md`
- `SCREEN_CONTRACT_MATRIX.json` / `.md`
- `EVIDENCE_LEDGER.md`
- `CLAUDE_DESIGN_GATE.md` (superseded by `CLAUDE_DESIGN_BLOCKERS.md` here)
- `RECONCILED_COCKPIT_IA.md`
