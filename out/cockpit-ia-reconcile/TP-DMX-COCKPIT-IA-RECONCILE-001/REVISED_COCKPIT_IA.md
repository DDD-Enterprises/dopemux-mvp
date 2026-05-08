# Revised Cockpit Information Architecture

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT
**Verdict:** CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION
**safe_for_claude_design:** NO
**READY_FOR_CLAUDE_DESIGN:** not approved

This document supersedes the working draft `RECONCILED_COCKPIT_IA.md` and `RECONCILED_COCKPIT_IA.json` carried into this packet, while reusing their evidence base and authority boundary tables. References to those source artifacts are kept inline.

## 1. Why The Previous IA Is Under-Scoped

The previous Cockpit IA presented the cockpit as five top-level modes (PM, Implementer, Overview, Services, Events) with no canonical home for a large class of authoritative behaviors that the command inventory has now made measurable. Carried evidence (see `RECONCILED_COCKPIT_IA.json`, `COMMAND_EXPOSURE_POLICY.json`, `SCREEN_CONTRACT_MATRIX.json`) shows:

- **139 placement rows** route to a Command Palette that has no formal screen contract, no broker semantics, and no proof-gate integration.
- **62 placement rows** belong to a Settings/Admin/Runtime family (routing, profile, hooks, env, debug, runtime configuration) for which the five-mode IA gives no canonical home.
- **48 BLOCKED_IN_COCKPIT** rows have no canonical surface that can show them as visible-but-non-executable; that visibility is required for drift management and operator trust.
- **40 COMMAND_PALETTE_ONLY** rows must never appear as primary mode chrome but currently have no formal palette contract.
- **111 CONFIRM_REQUIRED** rows have no cross-cutting Safe Action gate contract attached to the five-mode IA.
- **284 MISSING coverage rows** and **32 UNKNOWN coverage rows** have no formal Unknown/Drift Queue surface where they can be tracked without execution.
- **Repo Truth / Audit, Execution Handoff, Mobile/Tmux, System Data, PR Merge** are first-class authority interaction surfaces that the five-mode taxonomy hides inside Services or Implementer where they cannot enforce their own gates.

The five-mode model is therefore **necessary but insufficient**. It is correct as the operator's primary lens. It is incorrect as the entire IA. The reconciliation in this packet keeps the five top-level modes and adds the missing surfaces as **non-authority secondary structures** rather than as a sixth mode or a hidden silo.

## 2. Retained Top-Level Modes

The reconciled IA retains exactly five top-level modes. None of them are removed, renamed, or merged.

| Mode | Scope | Authority boundary |
| --- | --- | --- |
| PM | Workflow triage, PM handoff readiness across split PM authorities. | Does not claim unified PM truth; PM is split between Leantime, task-orchestrator, ConPort, and dope-memory receipts. |
| Implementer | Bounded task focus, evidence framing, validation, and explicit execution handoff readiness. | Does not own execution truth after dopetask handoff; Implementer is read/inspect/preview, never silent execution. |
| Overview | Operator status, health, drift summaries, safe launch context. | No mutation; routes the operator into secondary surfaces under their own gates. |
| Services | Service status and child workload inspection. | Does not own admin/runtime mutation by default; admin behavior moves to Settings/Admin/Runtime. |
| Events | Chronicle, capture, trigger, and event-inspection views with dope-memory authority boundaries. | Does not become a PM truth surface; events are receipts and history. |

Source: `RECONCILED_COCKPIT_IA.md` §3, §4 and `RECONCILED_COCKPIT_IA.json:top_level_modes`.

## 3. Added Global / Secondary Surfaces

These are **secondary surfaces**, not new authority modes. They exist because the inventory cannot be honored without them. They do not appear in the primary mode bar. They are reachable from Overview, Services, the Command Palette, and (where appropriate) from PM/Implementer/Events row affordances.

| Surface | Purpose | Why it is not a new top-level authority |
| --- | --- | --- |
| Command Palette | Global broker for rare, parameter-heavy, admin-heavy, and specialist commands; never an executor. | The palette is a broker over the same authority graph; it does not own any authority slice. |
| Settings/Admin/Runtime | Major secondary surface for routing, profile, hooks, env, MCP, service startup, runtime/admin/debug actions. | These flows belong to existing authority owners (dopemux operator control, routing/model-provider support); the surface is a reachable shell, not a new owner. |
| Safe Actions / Proof Gate | Cross-cutting confirmation, proof, TP/governance, and blocked-action gate before any non-read action. | This is a contract layer interposed between intent and execution; it does not own any state by itself. |
| Unknown / Drift Queue | Visible, non-executable queue for unknown, blocked, deprecated, drift, or missing-coverage rows. | The queue tracks items that lack ownership; nothing executes from this surface. |

Source: `RECONCILED_COCKPIT_IA.md` §4, §6, §7, §8 and `RECONCILED_COCKPIT_IA.json:secondary_surfaces`.

## 4. Reconciled Navigation Model

```
Primary mode bar (top level, exactly five):
  [PM] [Implementer] [Overview] [Services] [Events]

Always-available global surfaces (not in mode bar):
  - Command Palette (global hotkey + persistent invocation)
  - Settings/Admin/Runtime (admin shell reachable from Overview/Services/Palette)
  - Safe Actions / Proof Gate (interposed; never the destination)
  - Unknown / Drift Queue (reachable from Overview drift summary, Palette filter)
```

Detail screens reachable from primary modes or from the Palette retain the original sub-surfaces (Routing/Model Provider, Execution Handoff, Repo Truth / Audit, PR Merge, System Data, Mobile/Tmux, Hooks/Profile/Env). They are not authority modes; they are typed detail screens governed by the same Safe Action gate rules. See `SCREEN_CONTRACT_MATRIX.md` for per-screen contracts.

## 5. Authority Boundaries Preserved

The reconciliation does not move authority. The boundaries documented in the working draft remain canonical:

| Boundary | Treatment |
| --- | --- |
| Dopemux | Operator control, CLI coordination, shell/runtime framing. |
| Dopetask | Execution handoff runtime; only via explicit handoff and proof gates. |
| Task-orchestrator | Workflow coordination and workflow-significant transitions. |
| ConPort | Structured decision/progress/context/custom-data slices. |
| Dope-memory | Chronicle and historical receipt authority only. |
| Dope-context | Code/docs retrieval/indexing only. |
| Dopecon-bridge | Adapter/proxy/event transport only; never canonical PM/decision/progress authority. |
| ADHD Engine | Advisory operator-support / cognitive-state surface only. |
| Repo Truth Extractor | Audit/extraction runtime and evidence artifact generator only. |

Source: `RECONCILED_COCKPIT_IA.md` §9.

## 6. What This Revision Does Not Do

- Does not add a sixth top-level mode.
- Does not collapse Settings/Admin/Runtime, Palette, Safe Actions, or Drift Queue into a single mode.
- Does not approve final Cockpit screens for Claude Design.
- Does not approve runtime execution flows or destructive affordances.
- Does not regenerate the command inventory; it consumes the inventory carried into this packet.
- Does not modify Cockpit package HTML/CSS/React, runtime code, or ZIP packages.

## 7. Required Reading For Downstream Packets

- `COMMAND_PALETTE_SPEC.md` — palette is a broker, not an executor.
- `SAFE_ACTION_GATE_SPEC.md` — confirmation tiers and post-action proof expectations.
- `SETTINGS_ADMIN_RUNTIME_SPEC.md` — admin/runtime placement rules.
- `UNKNOWN_DRIFT_QUEUE_SPEC.md` — unknown/drift visibility without execution.
- `COMMAND_MAPPING_DECISIONS.md` — placement decisions across the inventory.
- `UPDATED_COVERAGE_DECISION.md` — coverage verdict and remaining gaps.
- `CLAUDE_DESIGN_BLOCKERS.md` — explicit unblock conditions.
- `OPUS_REMEDIATION_PLAN.md` — proposed next packets.

## 8. Source Artifacts Referenced

- `RECONCILED_COCKPIT_IA.md` — working-draft IA narrative.
- `RECONCILED_COCKPIT_IA.json` — working-draft structured IA.
- `COMMAND_EXPOSURE_POLICY.md` / `.json` — exposure class definitions.
- `SCREEN_CONTRACT_MATRIX.md` / `.json` — per-screen contract matrix.
- `COMMAND_PALETTE_POLICY.md` — original palette policy (superseded by `COMMAND_PALETTE_SPEC.md`).
- `SAFE_ACTION_GATES.md` — original safe-action gate table (superseded by `SAFE_ACTION_GATE_SPEC.md`).
- `CLAUDE_DESIGN_GATE.md` — original gate document (superseded by `CLAUDE_DESIGN_BLOCKERS.md`).
- `EVIDENCE_LEDGER.md` — evidence trail.
