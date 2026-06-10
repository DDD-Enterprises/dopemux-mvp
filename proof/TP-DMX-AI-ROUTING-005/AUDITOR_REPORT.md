# Auditor Report — TP-DMX-AI-ROUTING-005

**Auditor:** claude-sonnet-4.6 (self-audit, Claude Code CLI)  
**Verdict:** PASS_WITH_RISKS (BLOCKED — stop condition triggered)

## Stop Condition

"enforcement path differs from expected design"

routing-consistency CI job fails during test collection on every PR due to
`ModuleNotFoundError: No module named 'rich'` in `tests/conftest.py:82`.
No routing consistency test ran in CI. Drift test could not be executed.

## What Was Verified

- Enforcement chain structure: routing-consistency → CI Pipeline Summary → branch protection
- CI Pipeline Summary is a required check; routing-consistency is in its `needs:` list
- PR #841 confirms: routing-consistency=fail → CI Summary=fail → merge blocked
- Local 7/7 tests pass (with full deps and with --noconftest)

## What Was Not Verified

- Baseline CI pass (blocked by conftest dep failure)
- Drift failure test (blocked — precondition unmet)
- Governance docs reference to routing-consistency CI gate (gap found)

## Findings

- F1 (HIGH, OPEN): routing-consistency CI job fails at baseline — conftest dep issue
- F2 (LOW, OPEN): model-routing.md does not reference the CI enforcement gate
- F3 (INFO, RESOLVED): indirect enforcement chain is functionally sound

## Remediation

TP-DMX-AI-ROUTING-004A: add `--noconftest` to ci-complete.yml routing-consistency step.
After fix, re-run TP-005 to complete validation.
