safe_for_claude_design: CONDITIONAL
READY_FOR_CLAUDE_DESIGN: conditional
allowed_design_scope:
  - navigation skeleton
  - command palette primitive
  - safe-action confirmation primitive
  - proof gate primitive
  - blocked action row
  - proof requirement badge
  - admin/runtime shell
  - screen shell placeholders
blocked_design_scope:
  - final screens implying complete command coverage
  - direct high-risk action buttons
  - runtime execution flows
  - destructive action affordances
  - complete cockpit readiness claims
  - unified PM or unified brain screens
required_inputs_for_design:
  - RECONCILED_COCKPIT_IA.json
  - COMMAND_EXPOSURE_POLICY.json
  - SCREEN_CONTRACT_MATRIX.json
  - COMMAND_PALETTE_POLICY.md
  - SAFE_ACTION_GATES.md
  - prior COMMAND_INVENTORY.json
