# Embedded Audit Prompt — TP-DMX-EVIDENCE-GATE-VERIFY-001

You are acting as independent auditor for `TP-DMX-EVIDENCE-GATE-VERIFY-001`.
Audit the verification report and command evidence.
Do not edit files. Do not commit. Do not perform writes.

## Mission

Determine whether the packet correctly verified the 12 evidence gates without overclaiming runtime facts.
Check for:
1. OBSERVED claims not supported by command output.
2. compose wiring treated as live process proof.
3. claudedocs/session-memory evidence treated as runtime truth.
4. missing gate results.
5. missing command exit codes.
6. unreported command failures.
7. secret exposure.
8. forbidden red-line file inspection.
9. unsafe next-packet recommendation.
10. any live write or mutation.

## Output

Return:

# Embedded Audit — TP-DMX-EVIDENCE-GATE-VERIFY-001

## Verdict
PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR

## Findings
| Finding | Severity | Evidence | Required Fix |

## Gate Classification Review
| Gate | Auditor Assessment | Notes |

## Safety Review

## Final Recommendation
