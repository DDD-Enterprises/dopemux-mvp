# OPEN_PR_DESIGN_IMPACT

Packet: `TP-DMX-COCKPIT-DESIGN-PICKUP-001`

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

## Provider State

OBSERVED through `gh` and the GitHub pulls API on 2026-05-07:

- PR #587 is merged; pack remediation is on `main`.
- PR #573 is merged; runtime-contract fidelity repair is on `main`.
- PR #572 is open against `main`, `mergeable=false`, `mergeable_state=dirty`.
- There are 10 open PRs.

## Impact Matrix

| PR | Classification | Blocks Discussion | Blocks Final Screens | Reason |
| --- | --- | --- | --- | --- |
| #596 | NON_BLOCKING | No | No | UI dashboard palette changes, no Cockpit artifact contract paths. |
| #595 | NON_BLOCKING | No | No | CI review workflow hardening, no current Cockpit contract change. |
| #589 | NON_BLOCKING | No | No | PR queue template security changes. |
| #588 | NON_BLOCKING | No | No | Security instruction docs. |
| #586 | BLOCKS_FINAL_SCREENS | No | Yes | Removes genetic-agent/taskmaster surfaces that may change inventory and Unknown/Drift counts. |
| #585 | SUPERSEDED | No | Yes | Stale Cockpit recon artifact conflicts with post-PR #587 main. |
| #584 | NON_BLOCKING | No | No | MCP follow-up paths. |
| #583 | NON_BLOCKING | No | No | Dependency updates. |
| #582 | NON_BLOCKING | No | No | Dependency updates. |
| #572 | NEEDS_HUMAN_DECISION | No | Yes | Stale/conflicting Cockpit merge-stack evidence remains open. |

Design discussion can continue, but final screens cannot be recommended while #572 is unresolved and #586/#585 remain relevant to final-screen readiness.
