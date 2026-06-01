# Auditor Report

## TP-DMX-BRIDGE-SYMMETRY-016

- **Status**: PASS
- **Findings**: None
- **Fixes Applied**: Modified `tools/pr_action_bridge/compiler.py` so that unknown blockers (such as `EMBEDDED_AUDIT_UNKNOWN`) correctly emit a fail-closed `unknown-blocker` action assigned to the `supervisor` role, instead of being silently skipped. Updated tests to assert this new behavior.
- **Remaining Risks**: None
