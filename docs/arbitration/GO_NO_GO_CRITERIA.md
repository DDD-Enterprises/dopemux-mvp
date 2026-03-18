---
id: GO_NO_GO_CRITERIA
title: Go No Go Criteria
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Go No Go Criteria (explanation) for dopemux documentation and developer workflows.
---
# Go/No-Go Criteria

## Decision Framework
The final governance decision is based on specific performance and safety thresholds.

## Posture Criteria

### 1. GO_SUPERVISED_ONLY
- **Utility**: > 70% of operators find defer packets or merge plans useful.
- **Incidents**: Zero MAJOR or CRITICAL incidents during live trial.
- **Stability**: > 95% runtime success rate.
- **Adherence**: 100% compliance with fail-closed guardrails.

### 2. EXPAND_CAUTIOUSLY
- **Utility**: > 85% of guidance is accepted or partially accepted.
- **Overrides**: < 10% override rate on non-human-required decisions.
- **Confidence**: Consistency in HIGH confidence ratings across roles.
- **Prerequisite**: GO_SUPERVISED_ONLY criteria must also be met.

### 3. GO_ADVISORY_ONLY
- **Utility**: < 70% but > 40% usefulness.
- **Incidents**: MINOR incidents present, but no safety breaches.
- **Stability**: < 95% success rate or high provider variance.

### 4. NO_GO_REMAIN_SHADOW
- **Utility**: < 40% usefulness or results are consistently ignored.
- **Incidents**: Material unsafe recommendations (MAJOR).
- **Evidence**: Frequent "INSUFFICIENT_EVIDENCE" defers indicating weak extraction.

### 5. ROLLBACK_TO_SHADOW_ONLY
- **Safety**: Any unauthorized mutation or policy breach.
- **Reliability**: Critical failures in fail-closed logic.
- **Incidents**: Any CRITICAL incident.
