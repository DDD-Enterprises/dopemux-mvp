# Auditor A Prompt — 0001

You are independent Auditor A.

Do not edit files.

Audit DMX-DCP-MODEL-ROUTING-MVP-0001.

**Focus**:
- schema correctness
- fixture strength
- test strength
- forbidden file compliance
- OpenCode backend-only posture
- no runtime routing
- no unsafe selectors
- proof extension additive
- auditor_verdict distinct from validation_state

**Return**:
- auditor_tool
- auditor_model
- verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR
- blocking_findings
- non_blocking_findings
- required_fixes
- carried_risks
