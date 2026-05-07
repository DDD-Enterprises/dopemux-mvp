# Safe Action Gate Contract

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)
**Upstream packets:**
- TP-DMX-COCKPIT-IA-RECONCILE-001 (`SAFE_ACTION_GATE_SPEC.md`, `COMMAND_EXPOSURE_POLICY.json`, `SCREEN_CONTRACT_MATRIX.json`, `CLAUDE_DESIGN_BLOCKERS.md`, `UNKNOWN_DRIFT_QUEUE_SPEC.md`, `SETTINGS_ADMIN_RUNTIME_SPEC.md`)
- TP-DMX-COCKPIT-COMMAND-PALETTE-001 (`COMMAND_PALETTE_CONTRACT.md`, `COMMAND_PALETTE_INDEX_SCHEMA.json`, `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`, `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`, `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`, `PALETTE_PROOF_REQUIREMENTS.md`)

**ia_verdict:** CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION
**safe_for_claude_design:** NO
**READY_FOR_CLAUDE_DESIGN:** not approved

This document defines the canonical contract for the Cockpit Safe Action Gate. It is normative for the downstream Cockpit shell remediation packets (`TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA`, `TP-DMX-COCKPIT-RUNTIME-RENDER-001`). It produces no runtime code, no Cockpit package edits, no final screens, and no Claude Design uploads.

## 1. Role Statement

The Safe Action Gate is a **cross-cutting confirmation, preflight, proof, refusal, and evidence-capture contract layer**. It is **not** a destination mode. The operator never opens the gate as a goal; the gate is invoked from another surface that has already produced a resolved action request.

The gate's job is, for every non-read action:

- Receive the resolved action request from the upstream surface (Command Palette via `OpenSafeActionGate`, Settings/Admin/Runtime via its admin confirm step, contextual surfaces in PM/Implementer/Overview/Services/Events that originate an action request).
- Validate that all required preflight fields are present and resolved.
- Render the safety tier badge, every required input, side effects, expected proof, and rollback/abort plan.
- Demand an explicit confirmation affordance (typed confirmation for high-risk tiers).
- Refuse unsafe, unresolved, blocked, unknown, stale, or authority-conflicting actions and route them to the Unknown/Drift Queue (or `ShowBlockedReason` for blocked) per the routing rules in this contract.
- Capture post-action proof requirements aligned with the carried tier and emit a gate event/receipt regardless of outcome.

The gate **does not implement runtime execution** in this packet. This packet defines the contract; runtime wiring is the scope of `TP-DMX-COCKPIT-RUNTIME-RENDER-001`.

## 2. The Gate Is Cross-Cutting, Not A Mode

The reconciled IA has exactly five top-level modes (PM, Implementer, Overview, Services, Events) and four secondary surfaces (Command Palette, Settings/Admin/Runtime, Safe Actions / Proof Gate, Unknown / Drift Queue) per `REVISED_COCKPIT_IA.md` §2–§3. The Safe Action Gate is one of those secondary surfaces in IA terms, but in operator terms it is a contract layer interposed between any non-read action and its execution.

The gate:

- Does not appear in the primary mode bar.
- Does not own state, truth, decisions, or PM workflow.
- Does not subsume PM, Implementer, Overview, Services, or Events.
- Does not replace the Command Palette, Settings/Admin/Runtime, or the Unknown/Drift Queue.
- Does not invent new authority. Every action it gates is owned by the authority domain the inventory and policy assigns.
- Does not collapse multiple authority domains into a single control brain.
- Is invoked **only** from an upstream surface that has already produced a resolved action request.
- Is the **only** path from a `CONFIRM_REQUIRED` selection (T1–T6) to an execution.

## 3. Sources Of Action Requests (Allowed Origins)

The gate accepts action requests from exactly these origins. Every other origin is refused.

| Origin | Path | Notes |
| --- | --- | --- |
| Command Palette | `OpenSafeActionGate` outcome per `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`. | Direct handoff, palette is out of the loop after handoff. |
| Settings/Admin/Runtime | Admin confirm step of an admin/runtime flow per `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §3 and `SETTINGS_ADMIN_RUNTIME_SPEC.md` §3. | The surface invokes the gate; the palette never bypasses Settings/Admin/Runtime for `Settings/Admin` rows. |
| Contextual surface in PM, Implementer, Overview, Services, Events | A row, badge, or affordance on a primary mode that originates an action request and routes through the gate. | The mode displays the row; the gate confirms and proves. The mode is **not** the executor. |

A direct keyboard shortcut, deep-link, URL parameter, or background trigger is not an allowed origin and is refused.

## 4. The Gate Confirms; The Gate Does Not Execute (In This Packet)

This contract defines:

- The preflight schema the gate must collect before offering a confirm affordance.
- The tier the gate must assign and badge.
- The confirmation flow per tier (typed confirmation rules for T4/T5/T6).
- The refusal rules and routing into the Unknown/Drift Queue or blocked reason display.
- The post-action proof requirements the gate must record once execution returns from the runtime.
- The event/receipt the gate emits to the evidence stream.
- The UI primitive states the gate must render.

This contract does **not** define:

- Runtime execution code, runner wiring, or any patch to the Cockpit package HTML/CSS/React.
- Final screen designs.
- Production proof emission.
- Final operator-facing copy or color systems.

## 5. The Gate Never Auto-Confirms

The gate must **never**:

- Auto-confirm based on prior selection, prior gate confirmation, "remember my choice", or session state.
- Replace a typed confirmation field with a pre-typed default value.
- Treat a single click as both a parameter resolution and an execution confirmation.
- Treat receipt of a Palette handoff as the operator's confirmation; the handoff is just a candidate.
- Skip preflight rendering when fields are present (the operator must still see the preflight).
- Treat a green preflight state as proof of execution. Confirmation is not execution proof.

## 6. The Gate Never Lets Blocked Or Unknown Through

The gate must never:

- Execute or confirm a row whose `safety_class` is `BLOCKED_IN_COCKPIT` (`TX`).
- Execute or confirm a row whose `safety_class` is `UNKNOWN` (`TU`).
- Execute or confirm a row whose `activation_status` is `DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`, or `DEPRECATED_BLOCKED`.
- Execute or confirm a row whose `authority_domain` is `unknown / conflicting` or whose `canonical_writer` is `UNKNOWN`.
- Render a confirm affordance on a `BLOCKED_IN_COCKPIT` row, ever.
- Render a confirm affordance on an `UNKNOWN` row, ever.
- Replace a blocked row with a confirmable one (no in-gate reclassification).
- Reuse a stale `palette_index_row_hash` to confirm an action.

A blocked, unknown, or non-active row that reaches the gate is refused and routed:

- `BLOCKED_IN_COCKPIT` and `DEPRECATED_BLOCKED` ⇒ `ShowBlockedReason` (the gate hands back to the originating surface for blocked display).
- All other refusals ⇒ Unknown/Drift Queue with the enumerated reason (see `SAFE_ACTION_REFUSAL_RULES.md`).

## 7. Authority Boundaries Preserved

The gate does not move authority. The boundaries documented in `REVISED_COCKPIT_IA.md` §5 and `COMMAND_PALETTE_CONTRACT.md` §8 remain canonical:

- Dopemux — Operator control, CLI coordination, shell/runtime framing.
- Dopetask — Execution handoff runtime; only via explicit handoff and proof gates.
- Task-orchestrator — Workflow coordination only.
- ConPort — Structured decision/progress/context/custom-data slices only.
- Dope-memory — Chronicle and historical receipt authority only.
- Dope-context — Code/docs retrieval/indexing only.
- Dopecon-bridge — Adapter/proxy/event transport only.
- ADHD Engine — Advisory operator-support / cognitive-state surface only.
- Repo Truth Extractor — Audit/extraction runtime only.
- Routing/model-provider support — LiteLLM/CCR routing only.

The gate displays each row's `authority_domain` and `canonical_writer`. It never substitutes its own ownership and never collapses authority domains into a single control brain.

## 8. Capabilities (Allowed)

The gate must support all of the following simultaneously. These capabilities exist together; they cannot be disabled or short-circuited.

| Capability | Definition |
| --- | --- |
| Preflight rendering | Display every required preflight field per `SAFE_ACTION_PREFLIGHT_SCHEMA.json`. Missing fields render `UNKNOWN`, never blank. |
| Tier classification | Assign the carried `gate_tier` (T0/T0i/T1–T6/TX/TU) per `SAFE_ACTION_GATE_TIER_SCHEMA.json`. Never reclassify; the tier is carried from upstream. |
| Confirmation flow | Demand explicit confirm affordance per `SAFE_ACTION_CONFIRMATION_FLOWS.md`. T4/T5/T6 require typed confirmation. |
| Refusal | Refuse unsafe, unresolved, stale, or authority-conflicting actions per `SAFE_ACTION_REFUSAL_RULES.md` and route to the next destination (Unknown/Drift Queue or blocked display). |
| Proof capture | Record post-action proof per `SAFE_ACTION_PROOF_REQUIREMENTS.md`. Stale proof routes back to the Unknown/Drift Queue. |
| Event receipts | Emit a gate event/receipt per `SAFE_ACTION_GATE_EVENT_RECEIPTS.md` for every gate invocation, regardless of outcome. |
| Provenance preservation | Carry `source_file:source_symbol`, `evidence_path_or_command`, `palette_request_id`, `palette_index_row_hash`, `authority_domain`, `canonical_writer`, `proof_requirement` end-to-end. |
| UI primitives | Render the primitive UI states defined in `SAFE_ACTION_GATE_UI_PRIMITIVES.md`. |
| Fail-closed behavior | When any required field is unresolved, refuse to confirm. Route to Unknown/Drift Queue with the missing-field reason. |

## 9. Forbidden Behaviors (Hard No)

The gate **must never** do any of the following.

| Forbidden | Rationale / source rule |
| --- | --- |
| Execute commands itself in this packet. | This packet is contract-only. Runtime wiring is `TP-DMX-COCKPIT-RUNTIME-RENDER-001`. |
| Auto-confirm any action. | `SAFE_ACTION_GATE_SPEC.md` §5; `COMMAND_EXPOSURE_POLICY.json:classes.CONFIRM_REQUIRED.forbidden_ui_form`. |
| Run a `BLOCKED_IN_COCKPIT` row through any path. | `COMMAND_EXPOSURE_POLICY.json:classes.BLOCKED_IN_COCKPIT.forbidden_ui_form`. |
| Promote an `UNKNOWN` row into execution. | `COMMAND_EXPOSURE_POLICY.json:classes.UNKNOWN.forbidden_ui_form`; `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3. |
| Reclassify a row inside the gate. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3, §5; reclassification requires a packet. |
| Hide authority owner, canonical writer, safety class, side effects, or proof requirement from the operator. | `SAFE_ACTION_GATE_SPEC.md` §5. |
| Render a confirm affordance with a missing required field. | Fail-closed rule. |
| Treat confirmation as execution proof. | Proof must be captured post-execution (`SAFE_ACTION_PROOF_REQUIREMENTS.md`). |
| Substitute the worktree path with `/tmp` or another non-worktree path. | `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §7. |
| Reuse a stale `palette_index_row_hash`. | Drift detection rule. |
| Allow a remote-mutating (T4) action without a remote-mutation policy in scope. | `SAFE_ACTION_GATE_SPEC.md` §1 row T4; `CLAUDE_DESIGN_BLOCKERS.md` §4. |
| Bypass the Command Palette routing rules to confirm a row. | `PALETTE_ROUTING_RULES.md` §9. |
| Bypass Settings/Admin/Runtime for rows whose `cockpit_placement == Settings/Admin`. | `PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md` §1, §7. |
| Collapse authority domains into one control brain. | `COMMAND_PALETTE_CONTRACT.md` §8; `REVISED_COCKPIT_IA.md` §5. |
| Background or hidden retries; success chips before proof. | `SAFE_ACTION_GATE_SPEC.md` §5; `PALETTE_PROOF_REQUIREMENTS.md` §8. |
| Auto-retry a stale-proof action. | `UNKNOWN_DRIFT_QUEUE_SPEC.md` §3. |

## 10. Invariants The Gate Must Preserve

Every gate invocation carries the following invariants from preflight to proof. Loss of any invariant is a fail-closed condition; the gate refuses and routes to the Unknown/Drift Queue.

- **Authority domain.** From the upstream payload; one of the ten enumerated values in `COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.authority_domain`.
- **Canonical writer.** All writers comma-joined; never `UNKNOWN` for executable tiers (T1–T6).
- **Source provenance.** `source_file:source_symbol`, `evidence_path_or_command` carried verbatim.
- **Safety class.** One of `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED`, `COMMAND_PALETTE_ONLY`, `BLOCKED_IN_COCKPIT`, `EXTERNAL_ONLY`, `UNKNOWN`. Only `CONFIRM_REQUIRED` and `COMMAND_PALETTE_ONLY` (with executable tier) reach a confirm affordance.
- **Gate tier.** One of T0/T0i/T1/T2/T3/T4/T5/T6/TX/TU; only T1–T6 reach a confirm affordance.
- **Cwd / worktree.** Resolved against the current worktree, never `/tmp` substitute.
- **Side effects.** Enumerated; non-empty for any executable tier.
- **Expected proof.** One of the proof categories in `COMMAND_PALETTE_INDEX_SCHEMA.json:fields.proof_requirement.enum`; never `UNKNOWN` for executable tiers.
- **Rollback / abort.** Explicit rollback path, abort token, or `NOT_APPLICABLE` with documented reason.
- **Palette correlation.** `palette_request_id` and `palette_index_row_hash` preserved end-to-end.

## 11. The Gate Owns Confirm; Downstream Owns Execution

After a successful confirm, the gate hands off to the runtime authority owner identified by `canonical_writer`. The gate does not execute the command; the runtime authority does. The gate captures the proof emitted by the runtime authority and records it on the gate event/receipt.

The runtime wiring (the actual execution and proof emission) is the scope of `TP-DMX-COCKPIT-RUNTIME-RENDER-001`. This packet defines the contract that runtime must satisfy.

## 12. What This Contract Does Not Approve

- No final Safe Action Gate screens. Primitive-level only.
- No runtime code edits.
- No Cockpit package HTML/CSS/React edits.
- No ZIP edits.
- No Claude Design uploads.
- No execution capability inside the gate in this packet.
- No reclassification of `UNKNOWN` rows.
- No promotion of `BLOCKED_IN_COCKPIT` rows to executable.
- No remote-mutation flow without a remote-mutation policy and a wired T4 gate.
- No staging, commits, pushes, or PRs.

## 13. Source Artifacts (Authoritative Inputs)

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_MAPPING_DECISIONS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UPDATED_COVERAGE_DECISION.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SETTINGS_ADMIN_RUNTIME_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/PROOF.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_CONTRACT.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_ROUTING_RULES.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PROOF.json`
