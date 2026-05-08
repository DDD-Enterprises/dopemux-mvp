# Dopemux Cockpit Design Pickup Brief

Packet: `TP-DMX-COCKPIT-DESIGN-PICKUP-001`

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

## Operator Summary

Verdict: `READY_FOR_DESIGN_DISCUSSION`.

Resume design discussion from `origin/main` at `e4f01cb176fe0d9f6a1dac410598b04985b92b2c`. The pack-to-main merge has landed, and the runtime primitive model is now inspectable on main. Do not proceed to final Claude Design screens, upload to Claude Design, claim final readiness, authorize runtime action execution, approve T4 remote mutation, add live adapters, add canonical writes, or runtime-reclassify Unknown/Drift rows.

## Read First

1. `out/cockpit-design-pickup/TP-DMX-COCKPIT-DESIGN-PICKUP-001/DESIGN_PICKUP_STATE.md`
2. `out/cockpit-design-pickup/TP-DMX-COCKPIT-DESIGN-PICKUP-001/DESIGN_BLOCKER_MATRIX.md`
3. `out/cockpit-design-pickup/TP-DMX-COCKPIT-DESIGN-PICKUP-001/CLAUDE_DESIGN_BOUNDARY.md`
4. `out/cockpit-design-pickup/TP-DMX-COCKPIT-DESIGN-PICKUP-001/OPEN_PR_DESIGN_IMPACT.md`
5. `src/dopemux/ui/cockpit/runtime_contract.py`
6. `tests/unit/dopemux/ui/cockpit/test_runtime_contract.py`

## What Can Resume

- Architecture and design discussion.
- Primitive-level sketches as non-final discussion artifacts.
- IA critique and component inventory review.
- Flow descriptions and state diagrams.
- A design input brief that keeps blockers visible.

## What Remains Blocked

- Claude Design upload.
- Final Claude Design screens.
- Production UI screen generation.
- Runtime action execution claims.
- T4 remote mutation as approved behavior.
- Live service adapters.
- Canonical writes.
- Runtime reclassification of Unknown/Drift rows.
- PR, branch, merge, or proof governance mutation.

## Evidence

- OBSERVED: PR #587 merged pack remediation to `main` at merge commit `0ca8fae9dee59bc410cf013cc9af741aa28b88e7`.
- OBSERVED: PR #573 merged runtime-contract fidelity repairs at merge commit `c0c32c1639e675d3415257f2444437ae1fa2ea3c`.
- OBSERVED: runtime snapshot reports `safe_for_claude_design=NO`, `READY_FOR_CLAUDE_DESIGN=not approved`, five top-level modes, four global surfaces, 62 Settings/Admin unknown tier rows, and 487 lower-bound Unknown/Drift queue items.
- OBSERVED: PR #572 is still open, based on `main`, and GitHub pulls API reports `mergeable=false`, `mergeable_state=dirty`.
- OBSERVED: pack-to-main proof exists only in the retained local worktree and is not present on `main`.
- CONFLICTING: PR #585's design pickup plan says pack work is not on main; this is stale after PR #587.

## Questions To Preserve

- What is the intended disposition of PR #572 now that the pack branch disappeared and the PR is dirty against `main`?
- Will Ledger accept the local-only pack-to-main proof bundle, or should durable proof be landed separately?
- Which packet will resolve Settings/Admin per-row tiers for the 62 rows?
- Which packet will resolve or explicitly waive the remaining Unknown/Drift queue gaps?
- Will PR #586 land, and if so, who regenerates the Cockpit inventory afterward?
- Is a T4 remote-mutation policy desired for Cockpit, or should T4 remain a permanently blocked tier in the design language?

## Next Packet If Implementation Is Needed

Use a narrow follow-up packet only after the operator chooses scope:

- `TP-DMX-COCKPIT-PR572-DISPOSITION-001` for the stale/conflicting PR #572 decision.
- `TP-DMX-COCKPIT-PROOF-DURABILITY-001` for durable pack-to-main proof.
- `TP-DMX-COCKPIT-INVENTORY-REFRESH-AFTER-PR586-001` if PR #586 lands.
- `TP-DMX-COCKPIT-SETTINGS-TIER-RESOLUTION-001` for per-row Settings/Admin gate tiers.

Until those blockers are handled, continue only with design discussion and primitive-level exploration.
