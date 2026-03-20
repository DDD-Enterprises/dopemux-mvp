---
id: POLICY_TUNING_RULES
title: Policy Tuning Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Policy Tuning Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Policy Tuning Rules

## Recommendation Logic

### Thread Resolution
- **IF** `THREAD_REOPENED` rate > 10% for an intent class **THEN** recommend tightening the `ThreadResolutionGuard`.
- **IF** `MUST_FIX_CODE` is resolved without issues across 50+ runs **THEN** increase confidence level.

### Escalation
- **IF** `ESCALATED_UNNECESSARILY` rate > 20% **THEN** recommend expanding the `FeedbackClassifier` regex or intent mapping.
- **IF** `UNDER_BLOCKED` occurs even once **THEN** trigger immediate high-confidence block on affected patterns.

### Queue Admission
- **IF** `QUEUE_REMOVED` correlates with specific `CITriageCategory` **THEN** mark that category as non-retryable for admission.

## Confidence Levels
- **HIGH**: Supported by 10+ identical outcomes or any `UNDER_BLOCKED` event.
- **MEDIUM**: Supported by 5+ outcomes with consistent patterns.
- **LOW**: Initial observation; requires further monitoring or shadow-mode simulation.
