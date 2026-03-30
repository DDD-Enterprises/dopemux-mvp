---
id: EVALUATION_MODEL
title: Evaluation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Evaluation Model (explanation) for dopemux documentation and developer workflows.
---
# Arbitration Lane Evaluation Model

## Overview
This model defines the dimensions and methodology for the formal whole-subsystem evaluation of the High-Risk Integration Arbitration Lane.

## Evaluation Dimensions

### 1. Structural Completeness
- **Evidence Pack**: Does the canonical bundle capture sufficient context for high-risk cases?
- **Role Separation**: Are Analyzer, Challenger, and Arbiter roles distinct and effective?
- **Consensus & Gating**: Are merge plans and autonomy gates policy-aligned and conservative?
- **Human Surface**: Is the defer packet concise and actionable for human integrators?

### 2. Runtime & Provider Quality
- **Stability**: Success rate of LLM invocations, handling of timeouts and refusals.
- **Validation**: Adherence to strict output schemas.
- **Fail-Closed**: Correctness of automatic deferrals upon runtime failure.

### 3. Operator Utility & Governance
- **Usefulness**: Did the lane's output reduce human integration effort?
- **Acceptance Rate**: Frequency of operator adoption vs. rejection of guidance.
- **Override Analysis**: Reasons for human intervention in automated decisions.
- **Safety**: Did the lane remain within its assigned blast-radius and mode constraints?

## Methodology
- **Evidence Aggregation**: Systematic rollup of artifacts from Tranches 029 through 035.
- **Incident Review**: Deep dive into all recorded live trial incidents.
- **Tradeoff Analysis**: Assessment of defer-rate vs. decision-utility.
