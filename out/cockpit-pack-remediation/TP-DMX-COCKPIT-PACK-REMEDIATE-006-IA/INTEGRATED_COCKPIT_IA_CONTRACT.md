# Integrated Cockpit IA Contract

**Packet:** TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA
**Status:** ARTIFACT-ONLY HANDOFF (NO RUNTIME, NO FINAL SCREENS, NO CLAUDE DESIGN UPLOAD)

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

This contract integrates the three accepted upstream packets into a single statement of the Cockpit IA at the package level. It is normative for the downstream package-remediation work and the runtime renderer, but it does not approve runtime execution, final screens, or Claude Design uploads.

## 1. Five Top-Level Modes (OBSERVED — Preserved)

The reconciled IA has exactly **five** top-level operator modes. No sixth top-level mode is introduced.

| # | Mode | Purpose | Allowed action classes | Forbidden action classes |
| --- | --- | --- | --- | --- |
| 1 | PM | Workflow triage and PM handoff readiness without claiming unified PM truth. | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (governance gate) | `BLOCKED_IN_COCKPIT`, `UNKNOWN`, `EXTERNAL_ONLY` |
| 2 | Implementer | Current task, acceptance, evidence, validation, bounded execution handoff. | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (TP/proof gate) | `BLOCKED_IN_COCKPIT`, `UNKNOWN` |
| 3 | Overview | Operator status, health, drift summaries, safe launch points into secondary surfaces. | `DISPLAY_ONLY`, `INSPECT_ACTION` | `BLOCKED_IN_COCKPIT`, `UNKNOWN` |
| 4 | Services | Service status, logs, health, child workload inspection. Start/stop via gate. | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (start/stop through gate) | `BLOCKED_IN_COCKPIT`, `UNKNOWN` |
| 5 | Events | Chronicle, capture, trigger, event-inspection. Capture/emit via gate. | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (capture/emit) | `BLOCKED_IN_COCKPIT`, `UNKNOWN` |

(Source: `RECONCILED_COCKPIT_IA.md` §3, §4; `SCREEN_CONTRACT_MATRIX.md`.)

**Forbidden:** Adding a sixth top-level mode. Subsuming any mode into another. Promoting a secondary surface into a top-level mode. Collapsing authority domains across modes.

## 2. Four Secondary / Global Surfaces (OBSERVED — Preserved)

| # | Surface | Role | Authority owner | Executes? |
| --- | --- | --- | --- | --- |
| 1 | Command Palette | Global broker — discovery, classification, parameter preview, routing. Never executes. | dopemux operator control (broker) | No (broker only) |
| 2 | Settings/Admin/Runtime | Major secondary surface for admin/governance flows. Invokes the Safe Action Gate; never bypasses it. | dopemux operator control + per-flow authority | No (admin gate then Safe Action Gate) |
| 3 | Safe Actions / Proof Gate | Cross-cutting confirmation/preflight/proof/refusal/evidence layer for any non-read action. | cross-cutting safety contract | Confirm, not execute (in this packet) |
| 4 | Unknown / Drift Queue | Non-executable visibility surface for UNKNOWN, MISSING, BLOCKED, DEFINED_NOT_REGISTERED, OPTIONAL_IMPORT_UNKNOWN, conflicting authority, and stale-proof rows. | drift evidence (no execution) | No |

(Source: `REVISED_COCKPIT_IA.md` §3; `COMMAND_PALETTE_CONTRACT.md` §1, §2; `SETTINGS_ADMIN_RUNTIME_SPEC.md` §1, §3, §5; `SAFE_ACTION_GATE_CONTRACT.md` §1, §2; `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §3.)

## 3. Authority Boundary Map (OBSERVED — Preserved)

The package preserves authority boundaries verbatim. No collapsing, no substitution.

| Authority | Cockpit treatment | Inventory rows |
| --- | --- | --- |
| Dopemux | Operator control, CLI coordination, shell/runtime framing. | 145 |
| Dopetask | Execution handoff runtime; only via explicit handoff and proof gates. | 109 |
| Repo Truth Extractor | Audit/extraction runtime and evidence artifact generator only. | 44 |
| ADHD Engine | Advisory operator-support / cognitive-state surface only. | 21 |
| Routing/model-provider | LiteLLM/CCR routing only. | 20 |
| ConPort | Structured decision/progress/context/custom-data slices only. | 15 |
| Dope-memory | Chronicle and historical receipt authority only. | 15 |
| Task-orchestrator | Workflow coordination and workflow-significant transitions. | 11 |
| Dopecon-bridge | Adapter/proxy/event transport only. | 11 |
| unknown / conflicting | (not allowed for executable rows) | 14 |

(Source: `RECONCILED_COCKPIT_IA.md` §2, §9; `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.authority_domain`. Dope-context appears in carried authority docs but not as a separate inventory authority count.)

## 4. Inventory Counts (OBSERVED — Preserved)

| Axis | Count | Notes |
| --- | --- | --- |
| Total rows | 405 | from `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.total_inventory_rows` |
| Active rows | 366 | `activation_status.ACTIVE` |
| High-risk rows | 199 | `metadata.source_counts.high_risk_rows` |
| `safe_ui_exposure.DISPLAY_ONLY` | 178 | T0 |
| `safe_ui_exposure.CONFIRM_REQUIRED` | 111 | T1–T6 by side-effect class |
| `safe_ui_exposure.BLOCKED_IN_COCKPIT` | 48 | TX |
| `safe_ui_exposure.COMMAND_PALETTE_ONLY` | 40 | T1–T6 (executable) or T0i (inspect) |
| `safe_ui_exposure.INSPECT_ACTION` | 23 | T0i |
| `safe_ui_exposure.UNKNOWN` | 5 | TU |
| `external_only_count` | 37 | T0i or TX |
| `cockpit_placement.Command Palette` | 139 | Palette home |
| `cockpit_placement.Implementer` | 73 |  |
| `cockpit_placement.Settings/Admin` | 62 | Settings/Admin/Runtime home |
| `cockpit_placement.Services` | 54 |  |
| `cockpit_placement.External/Not Cockpit` | 37 |  |
| `cockpit_placement.Events` | 15 |  |
| `cockpit_placement.PM` | 15 |  |
| `cockpit_placement.Overview` | 9 |  |
| `cockpit_placement.UNKNOWN` | 1 |  |
| `current_cockpit_coverage.MISSING` | 284 | needs canonical home |
| `current_cockpit_coverage.PARTIAL` | 82 |  |
| `current_cockpit_coverage.UNKNOWN` | 32 |  |
| `current_cockpit_coverage.OUT_OF_SCOPE` | 7 |  |
| `activation_status.DEFINED_NOT_REGISTERED` | 30 | TU routing |
| `activation_status.DEPRECATED_BLOCKED` | 7 | TX routing |
| `activation_status.OPTIONAL_IMPORT_UNKNOWN` | 2 | TU routing |

The package does not regenerate or change these counts. Inventory regeneration is `CLAUDE_DESIGN_BLOCKERS.md` §3 condition 7 and is owned by a separate packet.

## 5. Safety Class → Gate Tier Mapping (OBSERVED — Preserved)

| Safety class | Gate tier | Confirms? | Executes (in this packet)? |
| --- | --- | --- | --- |
| `DISPLAY_ONLY` | T0 | No | No |
| `INSPECT_ACTION` | T0i | Explicit invoke | Yes (read-only) |
| `CONFIRM_REQUIRED` (generated artifact) | T1 | Explicit button | Yes |
| `CONFIRM_REQUIRED` (config mutation) | T2 | Explicit button + diff acknowledgment | Yes |
| `CONFIRM_REQUIRED` (write local) | T3 | Explicit button | Yes |
| `CONFIRM_REQUIRED` (write remote) | T4 | Explicit button + typed confirmation | **No** (blocked until policy approves; this packet is contract-only) |
| `CONFIRM_REQUIRED` (start/stop service) | T5 | Explicit button + typed service id | Yes |
| `CONFIRM_REQUIRED` (execution handoff) | T6 | Explicit button + typed TP id | Yes |
| `BLOCKED_IN_COCKPIT` | TX | No | Never |
| `EXTERNAL_ONLY` | T0i or TX | Inspect/CopyCommand only | No (in Cockpit) |
| `UNKNOWN` | TU | No | Never |

(Source: `SAFE_ACTION_GATE_TIER_SCHEMA.json`; `SAFE_ACTION_GATE_TIER_SCHEMA.md`; `COMMAND_EXPOSURE_POLICY.json:classes`.)

## 6. Cross-Cutting Safety Invariants (OBSERVED — Preserved)

The Safe Action Gate is **cross-cutting**. Invocations from any of the three allowed origins (Command Palette, Settings/Admin/Runtime, contextual surface in PM/Implementer/Overview/Services/Events) flow through the **same** preflight schema, tier schema, refusal rules, confirmation flow, proof requirements, event/receipt schema, and UI primitives. Origin-specific behaviors (e.g., palette `palette_request_id` correlation) are tagged on the gate event/receipt; they do not change the gate's cross-cutting behavior.

| Invariant | Source |
| --- | --- |
| Gate is cross-cutting, not a destination mode. | `SAFE_ACTION_GATE_CONTRACT.md` §1, §2 |
| Auto-confirm forbidden across all tiers. | `SAFE_ACTION_GATE_CONTRACT.md` §5; `COMMAND_EXPOSURE_POLICY.json:classes.CONFIRM_REQUIRED.forbidden_ui_form` |
| `BLOCKED_IN_COCKPIT` never executes through any path. | `COMMAND_EXPOSURE_POLICY.json:classes.BLOCKED_IN_COCKPIT.forbidden_ui_form`; `SAFE_ACTION_GATE_CONTRACT.md` §6 |
| `UNKNOWN` never executes through any path. | `COMMAND_EXPOSURE_POLICY.json:classes.UNKNOWN.forbidden_ui_form`; `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3 |
| In-gate reclassification forbidden. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5; `SAFE_ACTION_GATE_CONTRACT.md` §6 |
| Confirmation is not execution proof. | `SAFE_ACTION_PROOF_REQUIREMENTS.md` §1 |
| Proof required for any completion claim. | `SAFE_ACTION_PROOF_REQUIREMENTS.md` §1 |
| Stale proof routes to Unknown/Drift Queue. | `SAFE_ACTION_GATE_SPEC.md` §4; `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1 |
| Typed confirmation required for T4/T5/T6. | `SAFE_ACTION_CONFIRMATION_FLOWS.md` §3 |
| Remote-mutation policy required for T4. | `SAFE_ACTION_GATE_SPEC.md` §1 row T4; `CLAUDE_DESIGN_BLOCKERS.md` §4 |
| Settings/Admin rows must invoke the gate via Settings/Admin/Runtime, not bypass it. | `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §1, §7 |
| Palette never executes. | `COMMAND_PALETTE_CONTRACT.md` §1, §4 |
| Authority domains preserved per inventory. | `COMMAND_PALETTE_CONTRACT.md` §8; `REVISED_COCKPIT_IA.md` §5 |
| Cwd resolved against worktree, never `/tmp`. | `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §2 |
| `palette_index_row_hash` drift fails closed. | `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §3, §7 |
| Receipts append-only, no secrets, UTC. | `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` §5, §6 |

## 7. Routing Topology (INFERRED From Upstream Rules)

```
   ┌─────────────────────────────────────────────────────────────┐
   │  Operator (anywhere in Cockpit)                             │
   └───────────────────────────┬─────────────────────────────────┘
                               │
       ┌──────────────────┬────┴─────┬────────────────────┐
       │                  │          │                    │
   PM/Imp/Ovw/Svc/Evt  Command   Settings/Admin/Runtime  Unknown/Drift Queue
   contextual            Palette   surface (admin gate)   (visibility only)
   surface               broker    │                       │
       │                  │        │                       │
       │                  │        │                       │
       ▼                  ▼        ▼                       ▼
   ┌─────────────────────────────────────────────────────┐ │
   │ Safe Action Gate (cross-cutting contract)           │ │
   │ - preflight                                         │ │
   │ - tier classification (carried, not reclassified)   │ │
   │ - confirmation (typed for T4/T5/T6)                 │ │
   │ - refusal (fail-closed)                             │ │
   │ - proof capture                                     │ │
   │ - event/receipt emission                            │ │
   └────────────┬────────────────────────────────────────┘ │
                │                                          │
        confirm │           refuse / stale / drift         │
                ▼                                          ▼
        Runtime authority owner          ──────────► Unknown/Drift Queue
        (canonical_writer)                            (route, no execute)
        ──── proof emitted (out of scope this packet)
```

(All execution flows route **through** the Safe Action Gate. The gate is cross-cutting; the operator never opens the gate as a goal.)

## 8. Cross-Cutting Stops And Approvals (Apex Boundaries)

- Final screens: BLOCKED at Claude Design boundary (`CLAUDE_DESIGN_BLOCKERS.md` §3, §4).
- Runtime execution: BLOCKED in this packet (owner: `TP-DMX-COCKPIT-RUNTIME-RENDER-001`).
- T4 execution: BLOCKED until remote-mutation policy approves and runtime renderer wires it.
- TX execution: BLOCKED permanently in Cockpit.
- TU execution: BLOCKED permanently; reclassification requires a packet.
- Claude Design upload: BLOCKED.
- Sixth top-level mode: BLOCKED.
- Authority collapse: BLOCKED.
- Auto-confirm: BLOCKED across all tiers.
- In-gate reclassification: BLOCKED.

## 9. UNKNOWNs (Preserved)

- Inventory regeneration against current HEAD — owner: separate packet.
- Decision subcommands, optional `genetic`, defined-but-not-registered `worktree`/`vault` — owner: separate packets.
- Stale-proof window duration — owner: runtime renderer.
- Confirm-flow operator timeout — owner: runtime renderer.
- Operator authentication wiring — owner: runtime renderer.
- Remote-mutation policy reference document — owner: separate policy artifact.
- Per-flow tier mapping for the 62 Settings/Admin rows beyond seven flow groups — owner: `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`.

## 10. What This Contract Does Not Approve

- No final screens.
- No runtime execution.
- No T4 execution.
- No Cockpit package edits.
- No Claude Design upload.
- No `READY_FOR_CLAUDE_DESIGN` claim.
- No reclassification of any UNKNOWN row.
- No promotion of any BLOCKED row to executable.

## 11. Source Artifacts

(See [PACKAGE_REMEDIATION_INDEX.md](PACKAGE_REMEDIATION_INDEX.md) §"Source Artifacts" for the full list.)
