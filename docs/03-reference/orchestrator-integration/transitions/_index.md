---
id: orchestrator-transitions-index
title: Transition Preview & Gating Reference
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference detailing transition previews, safety tier classifications, and advance_item rules.
related_packets:
  - TP-DMX-ORCH-012
  - TP-DMX-ORCH-012-LIVE
---

# Workflow Transition Preview & Gating

Task state transitions map directly to safety policies. All mutating transitions require explicit approval.

## Transition Lifecycle
1.  **Preview**: Runs `get_next_status` to evaluate required notes.
2.  **Approval Adjudication**: Compares capabilities and safety tiers.
3.  **Apply**: Invokes `advance_item` with verified actor attribution.
