# Opus Remediation Plan

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT

This plan proposes the next packets to remediate the gaps identified in `UPDATED_COVERAGE_DECISION.md` and unblock the conditions in `CLAUDE_DESIGN_BLOCKERS.md`. None of these packets execute work inside the present packet.

## 1. Proposed Next Packets

The following packets are proposed in dependency order. Each packet has a defined input/output boundary; none of them edit runtime code or Cockpit packages outside their explicit scope.

### TP-DMX-COCKPIT-COMMAND-PALETTE-001
- **Goal:** Wire the Command Palette as a broker per `COMMAND_PALETTE_SPEC.md`.
- **Inputs:** `COMMAND_PALETTE_SPEC.md`, `COMMAND_EXPOSURE_POLICY.json`, carried `COMMAND_INVENTORY.json`.
- **Outputs:** Palette index schema, palette routing rules, primitive-level visual contract, palette-to-gate handoff contract.
- **Out of scope:** Final palette screen design upload to Claude Design; runtime execution; remote-mutation flows.
- **Unblocks:** Condition 1 in `CLAUDE_DESIGN_BLOCKERS.md`.

### TP-DMX-COCKPIT-SAFE-ACTIONS-001
- **Goal:** Wire the Safe Action Gate per `SAFE_ACTION_GATE_SPEC.md`.
- **Inputs:** `SAFE_ACTION_GATE_SPEC.md`, `COMMAND_EXPOSURE_POLICY.json`, `SCREEN_CONTRACT_MATRIX.md`.
- **Outputs:** Tier-by-tier confirmation contract, preflight schema, post-action proof schema, fail-closed behavior matrix.
- **Out of scope:** Final gate visuals at Claude Design fidelity; remote-mutation policy (handled in a separate governance packet).
- **Unblocks:** Condition 2 in `CLAUDE_DESIGN_BLOCKERS.md`.

### TP-DMX-COCKPIT-SETTINGS-RUNTIME-001
- **Goal:** Establish Settings/Admin/Runtime as a major secondary surface per `SETTINGS_ADMIN_RUNTIME_SPEC.md`.
- **Inputs:** `SETTINGS_ADMIN_RUNTIME_SPEC.md`, `SCREEN_CONTRACT_MATRIX.md`, carried inventory rows with placement = `Settings/Admin`.
- **Outputs:** Surface routing, per-flow contracts, gate-driven action contracts.
- **Out of scope:** New authority claims; mode-bar changes; final screen designs.
- **Unblocks:** Condition 3 in `CLAUDE_DESIGN_BLOCKERS.md`.

### TP-DMX-COCKPIT-UNKNOWN-DRIFT-001
- **Goal:** Establish the Unknown/Drift Queue per `UNKNOWN_DRIFT_QUEUE_SPEC.md`.
- **Inputs:** `UNKNOWN_DRIFT_QUEUE_SPEC.md`, `COMMAND_EXPOSURE_POLICY.json`, `EVIDENCE_LEDGER.md`.
- **Outputs:** Queue schema, surface routing, no-execute enforcement, promotion-evidence contract.
- **Out of scope:** Reclassifying inventory rows inside the queue (must be done in dedicated packets).
- **Unblocks:** Condition 4 in `CLAUDE_DESIGN_BLOCKERS.md`.

### TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
- **Goal:** Reconcile the Cockpit package IA against `REVISED_COCKPIT_IA.md` so the package matches the five top-level modes + four secondary surfaces.
- **Inputs:** `REVISED_COCKPIT_IA.md`, current Cockpit package files (`docs/03-reference/Dopemux Cockpit TUI Design System/ui_kits/cockpit/*`), `SCREEN_CONTRACT_MATRIX.md`.
- **Outputs:** Package IA reconciliation diff (proposal only), per-screen contract verification table, regression list.
- **Out of scope:** Final visual changes inside the design system; Claude Design upload; runtime code edits.
- **Unblocks:** Condition 5 in `CLAUDE_DESIGN_BLOCKERS.md`.

### TP-DMX-COCKPIT-RUNTIME-RENDER-001
- **Goal:** Validate the Cockpit runtime renderer against the screen contracts and gate primitives.
- **Inputs:** `SCREEN_CONTRACT_MATRIX.md`, output of the four packets above, runtime renderer code.
- **Outputs:** Renderer conformance report, proof JSON validation results, screenshot/visual approval evidence (in a non-Claude-Design surface).
- **Out of scope:** Authoring final Claude Design screens; uploading to Claude Design; any destructive runtime tests.
- **Unblocks:** Condition 6 in `CLAUDE_DESIGN_BLOCKERS.md`.

## 2. Cross-Cutting Workstreams

These workstreams complement the packet sequence and should be opened in parallel as preconditions:

- **Inventory refresh.** Regenerate `COMMAND_INVENTORY.json` against current HEAD; resolve runtime `dopemux help` UNKNOWN by ensuring `litellm` is available; reconcile counts. Unblocks Condition 7.
- **Open UNKNOWNs reduction.** Decision subcommands, optional `genetic`, defined-but-not-registered `worktree`/`vault` surfaces; root `RULES.md` and `TRUTH_*.md` absences. Unblocks Condition 8.

## 3. Dependencies

```
COMMAND-PALETTE-001 ──┐
SAFE-ACTIONS-001 ─────┼──► PACK-REMEDIATE-006-IA ──► RUNTIME-RENDER-001 ──► (Claude Design unblock)
SETTINGS-RUNTIME-001 ─┤
UNKNOWN-DRIFT-001 ────┘
```

Inventory refresh and UNKNOWN reduction can run in parallel; both must be at least partially complete before `RUNTIME-RENDER-001` is meaningful.

## 4. Forbidden In These Packets

Each downstream packet inherits the same forbidden list this packet observes:

- Do not modify runtime code outside the packet's explicit scope.
- Do not modify Cockpit package HTML/CSS/React outside the explicit packet that owns that change.
- Do not edit ZIP packages.
- Do not generate final PM or Implementer screens.
- Do not upload to Claude Design.
- Do not stage, commit, push, or open PRs unless explicitly instructed by the supervisor.
- Do not claim READY_FOR_CLAUDE_DESIGN.

## 5. Source Artifacts Referenced

- `REVISED_COCKPIT_IA.md`
- `COMMAND_PALETTE_SPEC.md`
- `SAFE_ACTION_GATE_SPEC.md`
- `SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `COMMAND_MAPPING_DECISIONS.md`
- `UPDATED_COVERAGE_DECISION.md`
- `CLAUDE_DESIGN_BLOCKERS.md`
- `SCREEN_CONTRACT_MATRIX.md`
- `COMMAND_EXPOSURE_POLICY.md` / `.json`
- `EVIDENCE_LEDGER.md`
