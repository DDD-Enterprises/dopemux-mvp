# CLAUDE_DESIGN_BOUNDARY

Packet: `TP-DMX-COCKPIT-DESIGN-PICKUP-001`

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

## Allowed

- Architecture and design discussion.
- Primitive-level sketches as non-final discussion artifacts.
- IA critique against current `main` evidence.
- Component inventory review.
- Flow descriptions that preserve blocked states.
- State diagrams that keep T4, TX, TU, Unknown/Drift, and proof-durability blockers visible.
- Design input briefs for a human continuation thread.

## Forbidden

- Claude Design upload.
- Final Claude Design screens.
- Production UI screen generation.
- T4 remote mutation design as approved behavior.
- Runtime action execution claims.
- Positive READY_FOR_CLAUDE_DESIGN readiness claims.
- Live service adapters.
- Canonical writes.
- Runtime reclassification of Unknown/Drift rows.
- PR, branch, merge, or proof governance mutation.

## Boundary

Claude Design may not proceed to final screens until PR #572 disposition, proof durability, T4 policy, Settings/Admin per-row tiers, Unknown/Drift gaps, and relevant open PR impact are all resolved or explicitly waived with durable evidence.
