# OPEN_PR_DESIGN_IMPACT

Packet: `TP-DMX-COCKPIT-DESIGN-PICKUP-001`

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

## Provider State

OBSERVED through `gh` and the GitHub pulls API on 2026-05-07:

- PR #587 is merged; pack remediation is on `main`.
- PR #573 is merged; runtime-contract fidelity repair is on `main`.
- PR #585 is merged, but its design pickup plan is stale after PR #587.
- PR #595 is merged; Gemini review workflow hardening is on `main` and does not change Cockpit design readiness.
- PR #572 is open against `main`; GitHub currently reports `mergeable=false`, `mergeable_state=dirty`, matching local pack-to-main proof's stale/conflicting risk.
- There are 8 open PRs excluding this packet's PR, or 9 including this packet's PR after publication.

## Impact Matrix

| PR | Classification | Blocks Discussion | Blocks Final Screens | Reason |
| --- | --- | --- | --- | --- |
| #596 | NON_BLOCKING | No | No | UI dashboard palette changes, no Cockpit artifact contract paths. |
| #589 | NON_BLOCKING | No | No | PR queue template security changes. |
| #588 | NON_BLOCKING | No | No | Security instruction docs. |
| #586 | BLOCKS_FINAL_SCREENS | No | Yes | Removes genetic-agent/taskmaster surfaces that may change inventory and Unknown/Drift counts. |
| #584 | NON_BLOCKING | No | No | MCP follow-up paths. |
| #583 | NON_BLOCKING | No | No | Dependency updates. |
| #582 | NON_BLOCKING | No | No | Dependency updates. |
| #572 | NEEDS_HUMAN_DECISION | No | Yes | Stale Cockpit merge-stack evidence remains open with dirty current mergeability. |

Design discussion can continue, but final screens cannot be recommended while #572 is unresolved, #586 may alter inventory, and merged PR #585 remains stale historical evidence.
