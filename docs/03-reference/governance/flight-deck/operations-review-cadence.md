---
id: OPERATIONS_REVIEW_CADENCE
title: Operations Review Cadence
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operations Review Cadence (explanation) for dopemux documentation and developer
  workflows.
---
# Operations Review Cadence

## Overview

This document defines the formal cadence for reviewing flight-deck operations metrics.
All reviews are operator-driven.  No automated process may change posture without a review.

---

## Review Schedule

### After Every 10 Cases

**Trigger**: When `actual_cases` in the rolling window reaches a multiple of 10.

**Scope**:
- Run `scripts/generate_ops_monitoring_report.py`
- Review `OPS_HEALTH_REPORT.json`
- Review `SIGNOFF_COMPLIANCE_REPORT.json`
- Review `POSTURE_DRIFT_REPORT.json`
- Review `SCALE_GATE_DECISION.json`
- Log review outcome in ConPort or ops journal

**Duration**: Target 15 minutes.

---

### After Any Incident (Immediate)

**Trigger**: Any `safety_log.jsonl` entry where `risk != "LOW"` AND `status != "FAILED"`, OR
any `DRIFT_DETECTED` status in `POSTURE_DRIFT_REPORT.json`.

**Scope**:
- Halt autonomous operations immediately (operator judgment)
- Review all safety log entries in the current window
- Identify root cause
- Determine whether the incident requires escalation
- Log incident decision in ConPort
- Re-run monitoring report after remediation

**Duration**: No fixed target.  Incident is not closed until root cause is documented.

---

### Weekly Signoff Compliance Check

**Trigger**: Every 7 calendar days.

**Scope**:
- Run `compute_signoff_compliance(window_size=10)`
- If `compliance_rate < 1.0`, investigate immediately (treat as post-incident)
- Log compliance check outcome

**Duration**: Target 10 minutes.

---

### Formal 30-Day Review

**Trigger**: Every 30 calendar days.

**Scope**:
- Review all monitoring artifacts from the past 30 days
- Evaluate scale-gate decision history
- Review posture drift history
- Assess whether the current posture is appropriate
- Propose any posture changes for the next review cycle
- Document findings in a formal review report

**Duration**: Target 60 minutes.  Requires at least one senior operator.

---

## Review Artifacts

All review outputs should be stored in `proof_bundle/` with a dated tranche directory.
The `generate_ops_monitoring_report.py` script produces the standard artifact set for each review.

---

## Escalation Path

| Condition                          | Escalation                              |
|------------------------------------|-----------------------------------------|
| `DISABLE_AUTO_APPLY` decision      | Immediate operator notification         |
| `ROLLBACK_TO_EVALUATION_ONLY`      | Emergency review within 2 hours        |
| 2+ drift signals active            | Review within 4 hours                  |
| Compliance rate < 0.8              | Review within 24 hours                 |
