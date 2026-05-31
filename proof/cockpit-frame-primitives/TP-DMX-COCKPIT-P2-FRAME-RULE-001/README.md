# TP-DMX-COCKPIT-P2-FRAME-RULE-001 Proof Bundle

## Scope

This bundle records Phase 2 P2-01 Frame + Rule primitives. The implementation adds primitive geometry only:

- `FrameLayout` coordinate contracts for 120x40, 100x32, and 80x24.
- `FrameBuffer` protected border, divider, body rule, status rule, and bottom rule cells.
- A frame-shell renderer that returns the canonical blocker string below 80x24.

## Boundary Statement

This packet does not replace `render_pm`, does not add mode dispatch, does not wire live data, and does not add runtime action execution or Claude Design upload behavior.
