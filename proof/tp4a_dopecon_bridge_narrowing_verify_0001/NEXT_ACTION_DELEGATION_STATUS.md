# Next-Action Delegation Status: dopecon-bridge

**Date:** 2026-03-12
**Status:** **FULLY DELEGATED**

## Findings
The bridge no longer calculates or determines the "next action" for any project or user.

### 1. Legacy Removal
The legacy `GET /tasks/next/{project_id}` route remains defined but is **administratively disabled** with a fail-closed policy. 

### 2. Policy-Enforced Redirection
The `PMRouteRequest` logic explicitly includes `next_action` and `get_next_action` in the `WORKFLOW_SIGNIFICANT_OPERATIONS` list. This ensures that even through the generic `/route/pm` adapter, "next-action" requests are blocked at the bridge layer.

### 3. Authority Target
The bridge expects the `Task Orchestrator` to be the sole authority for next-action resolution.

## Final Verdict
Delegation is **Proven**. The bridge performs no local next-action logic.
