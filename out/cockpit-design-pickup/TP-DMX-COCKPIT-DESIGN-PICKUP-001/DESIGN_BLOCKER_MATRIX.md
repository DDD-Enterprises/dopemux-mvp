# DESIGN_BLOCKER_MATRIX

Packet: `TP-DMX-COCKPIT-DESIGN-PICKUP-001`

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

## Summary

Design discussion is open. Final Claude Design screens remain blocked.

| Blocker | Status | Blocks Discussion | Blocks Primitive Sketches | Blocks Final Screens | Evidence Class |
| --- | --- | --- | --- | --- | --- |
| Claude Design final-screen gate | BLOCKED | No | No | Yes | OBSERVED |
| T4 remote-mutation policy | BLOCKED | No | No | Yes | OBSERVED |
| Runtime action execution | NOT_AUTHORIZED | No | No | Yes | OBSERVED |
| PR #572 stale dirty state | OPEN_STALE_DIRTY | No | No | Yes | OBSERVED |
| Pack-to-main proof durability | LOCAL_ONLY_PROOF | No | No | Yes | OBSERVED |
| Runtime-contract fidelity | CLEARED_ON_MAIN_WITH_RESIDUAL_RISKS | No | No | Yes | OBSERVED |
| Unknown/Drift queue gaps | BLOCKED_FOR_FINAL_SCREENS | No | No | Yes | OBSERVED |
| Settings/Admin per-row tiers | BLOCKED_FOR_FINAL_SCREENS | No | No | Yes | OBSERVED |
| Root authority/schema gaps | PARTIALLY_CLEARED | No | No | No | CONFLICTING |
| PR #586 surface removal | OPEN_RELEVANT_TO_INVENTORY | No | No | Yes | INFERRED |
| PR #585 stale recon artifact | MERGED_STALE_RECON_ARTIFACT | No | No | Yes | CONFLICTING |

## Required Next Actions

- Decide the disposition of PR #572.
- Do not treat local-only pack-to-main proof as durable unless Ledger accepts it or a durable proof packet lands.
- Resolve or waive Unknown/Drift and Settings/Admin per-row gaps with packet evidence.
- Author and accept a T4 remote-mutation policy before final design depicts that behavior.
- If PR #586 lands, regenerate Cockpit inventory before any final-screen gate review.
- Treat merged PR #585 artifacts as stale historical evidence and use this packet as the current pickup.
