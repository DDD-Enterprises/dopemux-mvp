# Unknown / Drift Queue Specification

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT

The Unknown / Drift Queue is a non-executable visible queue. It surfaces items that the operator and the system need to see, but that Cockpit must not execute. This surface preserves operator awareness of the gap between the inventory and the IA without ever providing an execution affordance.

## 1. What Goes In The Queue

A row enters the queue if any of the following is true:

| Trigger | Source signal | Why it goes here |
| --- | --- | --- |
| Unknown command | `safe_UI_exposure = UNKNOWN` or `activation_status = OPTIONAL_IMPORT_UNKNOWN` | Authority, side effects, or runtime ownership unresolved. |
| Defined-but-not-registered | `activation_status = DEFINED_NOT_REGISTERED` | Source defines the command but runtime does not register it. |
| Conflicting evidence | `authority_domain = unknown / conflicting` | Multiple authority claims; cannot be safely placed. |
| Blocked command | `safe_UI_exposure = BLOCKED_IN_COCKPIT` | Visible block surface for drift management; never executable. |
| Missing coverage | `current_Cockpit_coverage = MISSING` | The IA has no canonical home yet. |
| Stale proof gate | post-action proof missing or expired | A previously gated action has no current proof. |
| Drifted classification | row's classification disagrees with current authority docs | Cannot be reconciled inside the queue; needs a packet. |

Counts from the carried inventory (see `RECONCILED_COCKPIT_IA.json:counts_used`):

- `coverage.MISSING = 284`
- `coverage.UNKNOWN = 32`
- `safe_ui_exposure.UNKNOWN = 5`
- `safe_ui_exposure.BLOCKED_IN_COCKPIT = 48`
- `activation_status.DEFINED_NOT_REGISTERED = 30`
- `activation_status.OPTIONAL_IMPORT_UNKNOWN = 2`
- `activation_status.DEPRECATED_BLOCKED = 7`
- `authority_domain.unknown / conflicting = 14`

## 2. What Does Not Go In The Queue

- Rows that have a confident placement, valid authority owner, and resolved class. Those go to their canonical home (PM, Implementer, Overview, Services, Events, Palette, or Settings/Admin/Runtime).
- Rows that are simply waiting on a parameter; those remain in the Palette with `UNKNOWN` parameter fields and fail-closed gate behavior, not in the drift queue.
- Successful, recent actions; they go to the evidence stream / Events surface.

## 3. Forbidden Behaviors

- **No execution from the Unknown/Drift Queue under any condition.** This is the strongest rule. Even if a row appears safe, the queue cannot promote it.
- No copy-as-run shortcut that bypasses Palette + Safe Action Gate.
- No silent reclassification inside the queue.
- No "promote" affordance that changes the row's class without a packet's approval.
- No automatic retry of stale-proof actions.
- No suppression of `BLOCKED_IN_COCKPIT` rows; they remain visible as blocked.

## 4. Required Per-Row Fields

Every queued row must show:

- Trigger reason (one of the categories in §1).
- Command path (when known) or symbol/source location (when defined-but-not-registered).
- Authority domain (or `unknown / conflicting`).
- Last seen activation status.
- Current Cockpit coverage value.
- Block reason or required external workflow (if blocked).
- Required investigation packet id (if proposed).
- Last evidence timestamp / proof reference (if any).

Missing fields render as `UNKNOWN`; they never render blank.

## 5. Required Evidence To Promote A Row Out Of The Queue

A row may only leave the queue when **all** of the following are produced through a packet (not inside the queue itself):

| Promotion category | Required evidence |
| --- | --- |
| Unknown → known | Authority owner identified in system docs; classification assigned; placement assigned; Safe Action Gate tier determined. |
| Defined-but-not-registered → registered | Runtime registration repaired or row explicitly rejected; updated inventory; activation status flipped. |
| Conflicting authority → resolved | Decision in ConPort linking to system-docs change; updated authority domain. |
| Missing coverage → covered | Screen contract added (`SCREEN_CONTRACT_MATRIX.md`); placement field updated; Safe Action Gate tier set. |
| Blocked → external-only or display | Replacement command (if any); external workflow documented; reclassification through packet. |
| Stale proof → fresh | Re-execute the gated action and capture proof, or mark the action `EXTERNAL_ONLY` if proof cannot be captured in Cockpit. |

Promotion always requires a packet artifact reference. The queue is **not** an admin tool; it is a visibility surface.

## 6. Surface Reachability

- Reachable from Overview as part of the drift summary.
- Reachable from Command Palette as a filter (`status:UNKNOWN`, `status:BLOCKED`, `coverage:MISSING`, `proof:STALE`).
- Reachable from Settings/Admin/Runtime as a read-only drift inspector.
- Not reachable from PM/Implementer/Services/Events directly; those surfaces link to it via Overview when relevant.

## 7. Source Artifact

This spec is new in this packet. It is derived from the `UNKNOWN`, `BLOCKED_IN_COCKPIT`, `DEFINED_NOT_REGISTERED`, `OPTIONAL_IMPORT_UNKNOWN`, `MISSING`, and `unknown / conflicting` axes in the carried inventory and from the residual unknowns in `EVIDENCE_LEDGER.md`.
