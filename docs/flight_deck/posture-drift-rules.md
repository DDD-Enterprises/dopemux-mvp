---
id: POSTURE_DRIFT_RULES
title: Posture Drift Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Posture Drift Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Posture Drift Rules

## Overview

Posture drift occurs when the system's actual behavior diverges from its sanctioned operating posture.
Three drift signals are defined.  Detection is performed by `FlightDeckOpsEngine.detect_posture_drift()`.

---

## Drift Signal 1: Missing Signoff

**Condition**: A case with a mutation-class action class (`MERGE`, `APPLY_FIX`, `CLOSE`) exists in
the rolling window without a matching signoff record in `signoffs.jsonl`.

**Matching**: By `pr_id` field.

**Severity**: HIGH

**Signal name**: `MISSING_SIGNOFF`

**Interpretation**: A mutation-class action was logged without the required operator approval.
This may indicate a process gap, a logging failure, or an unauthorized action.

**Required response**: Immediately review the unsigned cases.  Log retroactive signoffs if the
action was legitimately approved but not captured.  If the action was not approved, treat as an incident.

---

## Drift Signal 2: High-Risk Safety Event

**Condition**: A `safety_log.jsonl` entry exists where `risk != "LOW"` AND `status != "FAILED"`.

**Interpretation**: A non-LOW-risk action succeeded (was not stopped by a safety gate).
This is a drift signal because non-LOW-risk successful actions require operator oversight.

**Severity**: HIGH

**Signal name**: `HIGH_RISK_EVENT`

**Required response**: Review the safety log entry.  Verify the action was operator-approved.
If not, treat as an incident and trigger `PAUSE_AND_REVIEW` governance.

---

## Drift Signal 3: Low Compliance Rate

**Condition**: `signoff_compliance_rate < 1.0` in the rolling window of mutation cases.

**Interpretation**: Less than 100% of mutation-class cases have matching signoffs.
This is a weaker signal than Signal 1 (it covers the rate, not individual gaps).

**Severity**: MEDIUM

**Signal name**: `LOW_COMPLIANCE_RATE`

**Reported fields**: `rate` (float, the computed compliance rate).

**Required response**: Investigate which cases are unsigned.  Review the signoff process.
Trigger `PAUSE_AND_REVIEW` if the gap cannot be explained.

---

## Drift Detection Output Schema

```json
{
  "status": "STABLE | DRIFT_DETECTED | INSUFFICIENT_DATA",
  "thin_sample": true,
  "drift_signals": [
    {
      "signal": "MISSING_SIGNOFF | HIGH_RISK_EVENT | LOW_COMPLIANCE_RATE",
      "count": 2,
      "severity": "HIGH | MEDIUM",
      "rate": 0.67
    }
  ],
  "window_size": 10,
  "computed_at": 1710000000.0
}
```

---

## Integration with Scale Gate

Drift signals feed into `generate_scale_gate_decision()` indirectly via the compliance and
incident metrics they expose.  `DRIFT_DETECTED` status should prompt a `PAUSE_AND_REVIEW`
or stronger scale-gate decision.
