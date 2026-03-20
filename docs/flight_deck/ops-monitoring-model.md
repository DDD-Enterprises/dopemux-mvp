---
id: OPS_MONITORING_MODEL
title: Ops Monitoring Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Ops Monitoring Model (explanation) for dopemux documentation and developer
  workflows.
---
# Ops Monitoring Model

## Overview

Rolling-window health monitoring for the PR Merge Specialist flight deck.
All metrics are **READ-ONLY advisory**.  No metric automatically changes posture.
Operator action is required for any governance decision.

---

## Rolling Window Definition

| Metric Class          | Window Size (N) | Thin-Sample Threshold |
|-----------------------|-----------------|-----------------------|
| Case-level metrics    | N = 10 cases    | < 5 cases             |
| Signoff metrics       | N = 10 signoffs | < 5 signoffs          |
| Safety event metrics  | N = 20 events   | < 5 events            |

A window is considered **THIN_SAMPLE** when actual data points fall below the threshold.
Thin-sample metrics are reported but flagged as unreliable.

---

## Metrics Inventory

### Case-Level Metrics (`cases.jsonl`)

| Metric               | Field          | Description                                      |
|----------------------|----------------|--------------------------------------------------|
| `actual_cases`       | computed       | Number of cases in rolling window                |
| `thin_sample`        | computed       | True when actual_cases < thin_sample_threshold   |
| `acceptance_rate`    | computed       | Fraction of cases with outcome=ACCEPTED          |
| `override_rate`      | computed       | Fraction with operator_override=True (see note)  |

**Note**: `operator_override_rate` requires future log additions for full accuracy.
Currently computed as `operator_override=True` field on case records.

### Signoff Metrics (`signoffs.jsonl`)

| Metric                    | Field          | Description                                          |
|---------------------------|----------------|------------------------------------------------------|
| `signoff_compliance_rate` | computed       | Fraction of mutation cases with matching signoff     |
| `mutation_cases`          | computed       | Cases with action_class in MERGE/APPLY_FIX/CLOSE     |
| `matched_signoffs`        | computed       | Signoff records matching a mutation case by pr_id    |

**Note**: `gating_refresh_success_rate` requires future log additions.
Currently returns `THIN_SAMPLE` status.  See `compute_gating_refresh_stability()`.

### Safety Event Metrics (`safety_log.jsonl`)

| Metric                | Field          | Description                                          |
|-----------------------|----------------|------------------------------------------------------|
| `incident_rate`       | computed       | Fraction of entries with risk≠LOW and status≠FAILED  |
| `severity`            | computed       | NONE / LOW / MEDIUM / HIGH (thresholds: 0, 5%, 10%) |
| `auto_apply_count`    | computed       | Entries with action_type=auto_apply                  |
| `high_risk_failures`  | computed       | Auto-apply entries with status=FAILED and risk=HIGH  |

---

## Data Sources

All logs are append-only JSONL files in the ops directory
(`proof/pr_merge/flight_deck/ops/` by default):

| File                | Written by                            |
|---------------------|---------------------------------------|
| `cases.jsonl`       | `OperationalizationEngine.log_case_usage()` |
| `signoffs.jsonl`    | `OperationalizationEngine.log_signoff()` |
| `safety_log.jsonl`  | `OperationalizationEngine.log_safety_event()` |

---

## Thin-Sample Warning

When a metric is THIN_SAMPLE:

1. The metric value is still computed and reported
2. `thin_sample: true` is set in the output dict
3. The `monitoring_health_panel` component shows a `THIN_SAMPLE` badge
4. The scale-gate decision may still reference the value but should be treated with caution

Thin-sample warnings do **not** block operations.
