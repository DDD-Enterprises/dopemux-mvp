# Embedded Audit Report

- Packet: `TP-DMX-CI-CONTAINERS-1118-001` PR 1260
- Audited content head: `873b8471004e8a2027b72ea7edaa363848225cd9`
- Auditor: agy gemini-3.1-pro-high / session `6110b9e6-c3cf-485e-9c85-748886a87fc3`
- Verdict: **PASS_WITH_RISKS**

## Summary
The matrix definition for adhd-dashboard is correctly implemented and the target Dockerfile exists. The diff is clean with no scope creep or secret leaks. However, there is a mismatch between the risk lane specified in the Task Packet invariants (L0) and the actual evaluated lane of the changed files (L3).

## Findings
- **Task Packet Risk Lane Mismatch** (`RISK_LANE_MISMATCH`, MEDIUM, OPEN): The task packet invariants section claims 'Risk lane is L0 deterministic CI configuration', but modifying .github/workflows/containers.yml is evaluated as an L3 change by validate_change_contract.py. The invariant should be updated to L3.

## Remaining risks
- Task packet invariant specifies L0 but the change is evaluated as L3.
