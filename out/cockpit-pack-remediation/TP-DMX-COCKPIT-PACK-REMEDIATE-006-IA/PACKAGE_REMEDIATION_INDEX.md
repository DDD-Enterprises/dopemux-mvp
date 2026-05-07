# Cockpit IA Package Remediation Index

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)
**Series:** DMX-COCKPIT-IA-REMEDIATION
**Branch:** pack/cockpit-pack-remediate-006-ia
**Base branch:** audit/cockpit-ia-reconcile-001
**Worktree:** /Users/hue/code/dopemux-worktrees/dopemux-cockpit-ia-reconcile-001
**HEAD at packet creation:** 88c188d551719b60e6a560a04b6da2939b27d34b

## Header State (Preserved)

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- `ia_verdict: CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`

The carried `RECONCILED_COCKPIT_IA.md` still contains the older "CONDITIONAL" verdict slot. The normalized `CLAUDE_DESIGN_BLOCKERS.md` (and downstream Command Palette + Safe Action Gate packets) tightened the gate to **NO / not approved**. This package remediation honors the tightened state. The older "CONDITIONAL" wording is preserved as historical evidence in the upstream artifact; this package does not regenerate or rewrite it.

## Purpose

Integrate the three accepted upstream contracts into a single self-contained package-remediation handoff that downstream packets (`TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA` runtime renderer wiring, `TP-DMX-COCKPIT-RUNTIME-RENDER-001`, `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`, `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001`) can consume without runtime implementation, final screen approval, or Claude Design upload.

## Upstream Verdicts (Accepted)

| Packet | Verdict | safe_for_claude_design |
| --- | --- | --- |
| TP-DMX-COCKPIT-IA-RECONCILE-001 | IA_RECONCILED_FOR_PACKAGE_REMEDIATION | NO |
| TP-DMX-COCKPIT-COMMAND-PALETTE-001 | COMMAND_PALETTE_SPEC_READY_FOR_PACKAGE_REMEDIATION | NO |
| TP-DMX-COCKPIT-SAFE-ACTIONS-001 | SAFE_ACTION_GATE_SPEC_READY_FOR_PACKAGE_REMEDIATION | NO |

All three upstream packets are accepted. None of them approve final screens, runtime execution, T4 (write remote) execution, TX (BLOCKED_IN_COCKPIT) execution, TU (UNKNOWN) execution, or Claude Design upload. This packet preserves those constraints.

## Artifact Catalog (This Packet)

| Artifact | Purpose |
| --- | --- |
| [PACKAGE_REMEDIATION_INDEX.md](PACKAGE_REMEDIATION_INDEX.md) | This index. Entry point for downstream consumers. |
| [PACKAGE_REMEDIATION_INDEX.json](PACKAGE_REMEDIATION_INDEX.json) | Machine-readable catalog with every artifact path, hash, upstream packet reference, and residual blocker. |
| [INTEGRATED_COCKPIT_IA_CONTRACT.md](INTEGRATED_COCKPIT_IA_CONTRACT.md) | Single integrated contract: five top-level modes + four secondary surfaces + Safe Action Gate cross-cutting layer + Unknown/Drift Queue. |
| [TOP_LEVEL_MODE_PACKAGE_MATRIX.md](TOP_LEVEL_MODE_PACKAGE_MATRIX.md) | Per-mode (PM, Implementer, Overview, Services, Events) package-level expectations. |
| [GLOBAL_SURFACE_PACKAGE_MATRIX.md](GLOBAL_SURFACE_PACKAGE_MATRIX.md) | Per-surface (Command Palette, Settings/Admin/Runtime, Safe Actions/Proof Gate, Unknown/Drift Queue) package-level expectations. |
| [COMMAND_TO_GATE_TO_SCREEN_MATRIX.md](COMMAND_TO_GATE_TO_SCREEN_MATRIX.md) | Cross-walk: command exposure class → gate tier → screen contract → proof requirement. |
| [SAFE_ACTION_GATE_INTEGRATION_MATRIX.md](SAFE_ACTION_GATE_INTEGRATION_MATRIX.md) | Per-tier integration of preflight, confirmation, refusal, proof, and event/receipt across the IA. |
| [SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md](SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md) | Per-flow-group package-level handoff for the 62 Settings/Admin rows. |
| [UNKNOWN_DRIFT_PACKAGE_HANDOFF.md](UNKNOWN_DRIFT_PACKAGE_HANDOFF.md) | Package-level routing of UNKNOWN/MISSING/BLOCKED/STALE-PROOF rows into the queue. |
| [RUNTIME_RENDERER_PACKAGE_HANDOFF.md](RUNTIME_RENDERER_PACKAGE_HANDOFF.md) | Inputs the runtime renderer packet may consume; explicitly does not authorize runtime execution. |
| [CLAUDE_DESIGN_PRIMITIVE_BOUNDARY.md](CLAUDE_DESIGN_PRIMITIVE_BOUNDARY.md) | Primitive vs final-screen boundary; explicit Claude Design blocker preservation. |
| [PACKAGE_REMEDIATION_TEST_MATRIX.md](PACKAGE_REMEDIATION_TEST_MATRIX.md) | Contract test catalog spanning IA, Palette, Gate, Settings, Drift Queue. |
| [PROOF.json](PROOF.json) | Single supervisor PROOF for this TP. |
| [sha256sums.txt](sha256sums.txt) | SHA-256 checksums of generated artifacts. |

## Evidence Classification

Every claim in this packet is labeled one of:

- **OBSERVED** — directly present in an upstream artifact (`RECONCILED_COCKPIT_IA.md`, `COMMAND_EXPOSURE_POLICY.json`, `SCREEN_CONTRACT_MATRIX.md`, `SAFE_ACTION_GATE_SPEC.md`, `COMMAND_PALETTE_INDEX_SCHEMA.json`, etc.).
- **INFERRED** — derived from carried evidence by combining axes (e.g., joining `safe_ui_exposure` + `cockpit_placement` + `gate_tier`).
- **UNKNOWN** — not resolved by any upstream artifact; preserved as `UNKNOWN` and never imputed.
- **BLOCKED** — explicitly forbidden in upstream artifacts (final screens, runtime execution, T4 mutation, Claude Design upload).

## Residual UNKNOWNs (Preserved From Upstream)

- Command inventory regenerated against current HEAD — pending (`CLAUDE_DESIGN_BLOCKERS.md` §3 condition 7).
- Decision subcommands, optional `genetic`, defined-but-not-registered `worktree`/`vault` — unresolved (`CLAUDE_DESIGN_BLOCKERS.md` §3 condition 8).
- Root `RULES.md`, `TRUTH_*.md` absences — unresolved.
- Runtime `dopemux help` resolution — unresolved (env without `litellm`).
- Stale-proof window duration — owner: runtime renderer.
- Confirm-flow operator timeout — owner: runtime renderer.
- Remote-mutation policy reference — pending separate policy artifact.
- Operator authentication wiring (`operator_id` capture) — pending runtime renderer.
- Per-flow tier mapping for Settings/Admin rows beyond seven flow groups — pending Settings/Runtime packet.

## Residual Blockers (Preserved From Upstream)

- **Final screens of any kind** remain blocked at the Claude Design boundary.
- **Runtime execution** remains blocked in this packet; runtime wiring is `TP-DMX-COCKPIT-RUNTIME-RENDER-001`.
- **T4 (write remote)** remains blocked until the remote-mutation policy approves and runtime renderer wires it.
- **TX (BLOCKED_IN_COCKPIT)** remains permanently blocked in Cockpit.
- **TU (UNKNOWN)** remains never-executable; reclassification requires a packet.
- **Auto-confirm** is forbidden across all tiers.
- **In-gate reclassification** is forbidden.

## What This Packet Does Not Approve

- No final Cockpit screens (PM, Implementer, Overview, Services, Events, Command Palette, Settings/Admin/Runtime, Safe Action Gate, Unknown/Drift Queue).
- No Cockpit package HTML/CSS/React edits.
- No ZIP package edits.
- No runtime code or service wiring.
- No T4 remote mutation.
- No Claude Design upload.
- No `READY_FOR_CLAUDE_DESIGN` claim.
- No staging or commits outside the `commit.allowlist` of this TP.

## Recommended Downstream Packets

After this packet is accepted (validation passes; no forbidden tracked files modified):

1. `TP-DMX-COCKPIT-RUNTIME-RENDER-001` — wire the runtime renderer per the contracts in this packet; emit per-tier proof; capture operator identity; configure stale-proof window and confirm-flow timeout.
2. `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001` — finalize per-flow-group tier mapping for the 62 Settings/Admin rows.
3. `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001` — wire the Unknown/Drift Queue surface; promote/demote rows only via packet evidence.
4. Inventory regeneration packet — regenerate `COMMAND_INVENTORY.json` against current HEAD; reconcile counts.
5. Remote-mutation policy packet — author the policy that T4 requires; until approved, T4 remains blocked.

Claude Design final-screen approval requires all eight conditions in `CLAUDE_DESIGN_BLOCKERS.md` §3.

## Source Artifacts (Authoritative Inputs)

### IA Reconcile (TP-DMX-COCKPIT-IA-RECONCILE-001)

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/RECONCILED_COCKPIT_IA.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/RECONCILED_COCKPIT_IA.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/REVISED_COCKPIT_IA.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_MAPPING_DECISIONS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UPDATED_COVERAGE_DECISION.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_GATE.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/OPUS_REMEDIATION_PLAN.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/PROOF.json`

### Command Palette (TP-DMX-COCKPIT-COMMAND-PALETTE-001)

- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_CONTRACT.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_BLOCKED_UNKNOWN_STATES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_RESULT_ROW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/CLAUDE_DESIGN_PALETTE_BLOCKERS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PROOF.json`

### Safe Actions (TP-DMX-COCKPIT-SAFE-ACTIONS-001)

- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_CONTRACT.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TIER_SCHEMA.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.json`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PREFLIGHT_SCHEMA.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_CONFIRMATION_FLOWS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_REFUSAL_RULES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_PROOF_REQUIREMENTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_EVENT_RECEIPTS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_UI_PRIMITIVES.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/SAFE_ACTION_GATE_TEST_MATRIX.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`
- `out/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001/PROOF.json`
