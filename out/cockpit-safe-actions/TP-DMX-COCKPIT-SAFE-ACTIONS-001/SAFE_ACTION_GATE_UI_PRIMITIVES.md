# Safe Action Gate UI Primitives

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the primitive UI states the Safe Action Gate must render. These are **not** final screens. They are the conceptual primitive components and state shapes that downstream packets (`TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA`, `TP-DMX-COCKPIT-RUNTIME-RENDER-001`) will wire and render. No final visual design, no Claude Design upload, no Cockpit package edits.

## 1. Primitive Component Inventory

The gate is composed of the following primitive components. Each primitive has well-defined state inputs, refusal/error states, and forbidden behaviors.

| Primitive | Purpose | Required state inputs |
| --- | --- | --- |
| Preflight panel | Displays every required preflight field. | All fields from `SAFE_ACTION_PREFLIGHT_SCHEMA.json` for the row's tier. |
| Missing-field row | Displays a single field whose value is `UNKNOWN`. | Field name; `UNKNOWN` value; refusal reason. |
| Authority badge | Displays the row's authority domain. | `authority_domain`; visual treatment per the ten enumerated authorities (no color picks here, just the slot). |
| Canonical writer badge | Displays the canonical writer (or comma-joined writers). | `canonical_writer`. |
| Tier badge | Displays the row's gate tier. | `gate_tier` (T0/T0i/T1/T2/T3/T4/T5/T6/TX/TU). |
| Side-effect summary | Enumerates the row's side effects. | `side_effects` array; per-side-effect notes. |
| Proof requirement badge | Displays the expected proof category. | `expected_proof`. |
| Confirmation control | The explicit confirm button and (when required) the typed confirmation field. | `gate_tier`, `typed_confirmation_required`, `typed_confirmation_token_value`. |
| Typed confirmation field | Operator types the required token (T4/T5/T6). | Required token value; current input value; match state. |
| Refused state | Displays refusal reason and routing destination. | `refusal_reason`; `routing_destination`; missing-field list when applicable. |
| Completed-with-proof state | Displays that the action ran and proof was captured. | `proof_status: captured`; `proof_artifacts`; UTC timestamps. |
| Stale-proof state | Displays that proof has gone stale and routes to the queue. | `stale_proof_tag: true`; routing destination. |
| Blocked state | Displays a blocked row's reason and forbids confirm. | `block_reason`; replacement command (if any); required external workflow (if any). |
| Unknown state | Displays an unknown row's reason and required investigation packet. | `unknown_reason`; required investigation packet reference. |

## 2. Primitive State Catalog

### 2.1 Preflight panel

**Purpose:** Show every required field for the row's tier with explicit values, defaults made explicit, side effects enumerated, expected proof, and rollback plan.

**Required slots:**

- `command` (resolved invocation).
- `resolved_params.required` (each required parameter with its value).
- `resolved_params.optional` (each optional parameter with `value` and `was_default` flag).
- `cwd` (absolute path within worktree).
- `worktree_metadata` (branch, dirty flag, detached state).
- `authority_domain` (badge).
- `canonical_writer` (badge).
- `safety_class` (badge).
- `gate_tier` (badge).
- `side_effects` (summary).
- `expected_proof` (badge).
- `rollback_or_abort` (rollback path / abort token / `NOT_APPLICABLE` with reason).
- `source_provenance` (`source_file:source_symbol`, `evidence_path_or_command`).

**Refusal/UNKNOWN behavior:** Any field with value `UNKNOWN` is rendered as a `Missing-field row`. The confirm control is disabled. The refusal reason and routing destination are displayed.

**Forbidden:** Hiding a field; rendering blank for `UNKNOWN`; auto-filling `UNKNOWN` from session state.

### 2.2 Missing-field row

**Purpose:** Show a single required field that resolved to `UNKNOWN` and explain why it blocks the confirm path.

**Required slots:**

- Field name.
- Field value: `UNKNOWN`.
- Reason: one of the enumerated refusal reasons (e.g., `PARAM_UNRESOLVED`, `CWD_OUT_OF_WORKTREE`, `AUTHORITY_CONFLICT`).
- Recommended next action: e.g., "Re-render preview at upstream surface", "Resolve parameter at originating surface", "Open Unknown/Drift Queue".

**Forbidden:** Suggesting a default value; offering an "ignore and proceed" affordance.

### 2.3 Authority and writer badges

**Purpose:** Display the authority domain and canonical writer so the operator always knows who owns the action.

**Required slots:**

- `authority_domain` value (one of the ten enumerated, including `unknown / conflicting`).
- `canonical_writer` value (single or comma-joined; or `UNKNOWN`).

**Forbidden:** Hiding the badges; substituting "Cockpit" for the authority owner.

### 2.4 Tier badge

**Purpose:** Display the gate tier prominently so the operator understands the confirmation strength required.

**Required slots:**

- `gate_tier` value (T0/T0i/T1/T2/T3/T4/T5/T6/TX/TU).
- Tier human label (e.g., "T2 Config Mutation", "T6 Execution Handoff", "TX Blocked", "TU Unknown").

**Forbidden:** Showing an executable tier badge for a row that is `BLOCKED_IN_COCKPIT` or `UNKNOWN`; showing a T0 badge on a confirm flow.

### 2.5 Side-effect summary

**Purpose:** Enumerate the row's side effects so the operator sees the consequences before confirming.

**Required slots:**

- `side_effects` array (e.g., `config mutation`, `write local`, `start service`, `execution handoff`).
- Per-side-effect notes (path, scope, magnitude where derivable).

**Forbidden:** Empty side-effect summary on an executable tier; collapsing multiple side effects into a single label.

### 2.6 Proof requirement badge

**Purpose:** Tell the operator what proof will be required to claim completion.

**Required slots:**

- `expected_proof` value (one of the ten enumerated proof categories).
- Brief human label (e.g., "Artifact + checksum", "Config diff or status", "Service status + log", "TP runner proof").

**Forbidden:** Hiding the proof requirement; substituting "no proof needed" for a tier that requires proof.

### 2.7 Confirmation control

**Purpose:** Operator's explicit affordance to confirm. Required for T0i (invoke) and T1–T6 (confirm-and-run).

**Required slots:**

- Confirm button (label varies per tier: `Run inspection`, `Confirm and generate`, `Confirm and apply`, `Confirm and write`, `Confirm and call remote`, `Confirm and start`/`Confirm and stop`, `Confirm and run TP`).
- Abort button (always present; no penalty).
- `typed_confirmation_required` flag (true for T4/T5/T6).

**Disabled-state rules:**

- Disabled when any required preflight field is `UNKNOWN`.
- Disabled when `typed_confirmation_required == true` and the typed value does not match.
- Disabled when `safety_class in {BLOCKED_IN_COCKPIT, UNKNOWN, EXTERNAL_ONLY}` (these never reach a confirm control).
- Disabled when `gate_tier in {T0, TX, TU}` (these never reach a confirm control).
- Disabled when authority drift or class drift is detected mid-flow.

**Forbidden:** Auto-clicking; showing the confirm button while preflight has `UNKNOWN`; persisting the confirm-state across gate openings; double-confirming with a single click.

### 2.8 Typed confirmation field

**Purpose:** Force the operator to type a specific token before confirming a high-risk action.

**Required slots:**

- Required token value (displayed in the preflight panel as the source of truth).
- Current input value (operator-typed).
- Match state: `not_started` | `partial_match` | `exact_match` | `mismatch`.

**Behaviors:**

- Displays the required token next to the input field so the operator can read and type it.
- Confirm button enables only on `exact_match`.
- Reset on every gate-open (no persisted state).
- Mismatch on confirm attempt emits `TYPED_CONFIRMATION_MISMATCH` refusal event/receipt and re-prompts.

**Forbidden:** Auto-fill; copy-as-token shortcut from clipboard; persisting across gate openings; pre-typing the token in a hidden input.

### 2.9 Refused state

**Purpose:** Display the gate's refusal explicitly so the operator never wonders why the action did not run.

**Required slots:**

- Refusal reason (enumerated value from `SAFE_ACTION_REFUSAL_RULES.md`).
- Missing-field list when applicable.
- Routing destination (`Unknown/Drift Queue`, `Show blocked reason`, `Re-render`, `Originating surface`).
- Continue affordance (e.g., `Continue to Drift Queue`, `Re-render preview`).

**Forbidden:** Silent dismissal; substituting a generic "error" message for the enumerated reason; offering an "ignore and confirm anyway" affordance.

### 2.10 Completed-with-proof state

**Purpose:** Display that the action ran and proof was captured.

**Required slots:**

- `proof_status: captured`.
- Proof artifacts (path, checksum, exit code, status, log excerpt — per tier).
- UTC timestamps (`gate_open_timestamp_utc`, `confirm_timestamp_utc`, `proof_timestamp_utc`).
- Correlation: `gate_request_id`, `palette_request_id` (when applicable).

**Forbidden:** Showing this state before proof is captured; substituting confirmation receipts for execution proof; showing this state with `proof_status: incomplete` or `proof_status: stale`.

### 2.11 Stale-proof state

**Purpose:** Display that proof has gone stale and direct the operator to the Unknown/Drift Queue.

**Required slots:**

- `stale_proof_tag: true`.
- Reason: missing or expired proof.
- Routing: `Unknown/Drift Queue`.
- Required next action: re-execute and capture proof, or mark `EXTERNAL_ONLY`.

**Forbidden:** Auto-retrying the action; treating a stale-proof row as fresh; allowing the operator to re-confirm without re-execution and re-proof.

### 2.12 Blocked state

**Purpose:** Display a `BLOCKED_IN_COCKPIT` or `DEPRECATED_BLOCKED` row with its reason and (if any) replacement.

**Required slots:**

- `block_reason`.
- Replacement command (if any) or `NOT_APPLICABLE`.
- Required external workflow (if any) or `NOT_APPLICABLE`.
- Source provenance.

**Forbidden:** Showing a confirm affordance; offering a copy-as-run shortcut that bypasses the gate; suppressing the block reason; reclassifying the row inside this state.

### 2.13 Unknown state

**Purpose:** Display a `safety_class == UNKNOWN`, `activation_status` non-`ACTIVE`, or `authority_domain == 'unknown / conflicting'` row with its reason.

**Required slots:**

- `unknown_reason`.
- Required investigation packet reference (or `INVESTIGATION_PACKET_REQUIRED`).
- Last activation status (when known).
- Last evidence reference (when known).

**Forbidden:** Showing a confirm affordance; reclassifying the row inside this state; auto-routing to a confirm path.

## 3. Primitive State Transitions

```
[gate_open]
  → render(Preflight panel)
  → if any required field UNKNOWN:
      → render(Missing-field row(s)) inside Preflight panel
      → render(Refused state) with refusal reason and routing destination
      → emit gate_refuse receipt
  → else if safety_class == BLOCKED_IN_COCKPIT:
      → render(Blocked state)
      → emit gate_refuse receipt
  → else if safety_class == UNKNOWN:
      → render(Unknown state)
      → emit gate_refuse receipt
  → else if gate_tier in {T1..T6}:
      → render(Confirmation control)
      → if typed_confirmation_required:
          → render(Typed confirmation field) with required token
      → operator interacts:
          → on Abort:
              → emit gate_abort receipt; close
          → on Timeout:
              → emit gate_timeout receipt; close
          → on Confirm (with token match where required):
              → emit gate_confirmed receipt
              → hand off to runtime authority owner (out of scope this packet)
              → on proof received:
                  → if all required proof artifacts present:
                      → render(Completed-with-proof state)
                      → emit gate_proof_captured receipt
                  → else:
                      → render(Refused state) with reason: incomplete proof
                      → emit gate_proof_incomplete receipt
              → on stale proof tagged later:
                  → render(Stale-proof state)
                  → emit gate_proof_stale receipt
```

## 4. No Final Screens In This Packet

This packet defines the **primitive components** and their state shapes. It does not specify:

- Final visual design (color, type, spacing).
- Final layout (responsive breakpoints, container chrome, navigation).
- Final animation, motion, or transition specifics.
- Final operator copy/microcopy.
- Final iconography or color tokens for badges.

Final screens are blocked at the Claude Design boundary (`CLAUDE_DESIGN_BLOCKERS.md`, `CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`). Claude Design may receive Safe Action Gate primitive sketches **after** this packet is accepted; final screens remain blocked.

## 5. Forbidden Across All Primitives

- Hiding any required field (render `UNKNOWN`, never blank).
- Rendering a confirm affordance when any required field is `UNKNOWN`.
- Rendering a confirm affordance for `safety_class in {BLOCKED_IN_COCKPIT, UNKNOWN, EXTERNAL_ONLY}` or `gate_tier in {T0, TX, TU}`.
- Substituting a generic "error" or "warning" for the enumerated refusal reason.
- Auto-dismissing the gate without an event/receipt.
- Persisting typed confirmation values across gate openings.
- Suggesting an "ignore and proceed" path on any refusal.
- Promoting an `UNKNOWN` row inside the gate (reclassification requires a packet).
- Reclassifying a `BLOCKED_IN_COCKPIT` row inside the gate.
- Showing the Completed-with-proof state before proof is captured.

## 6. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §5
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:classes`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SCREEN_CONTRACT_MATRIX.json`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §4
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PARAMETER_PREVIEW_SPEC.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §5
