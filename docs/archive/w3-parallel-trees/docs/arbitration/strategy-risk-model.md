---
id: STRATEGY_RISK_MODEL
title: Strategy Risk Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Strategy Risk Model (explanation) for dopemux documentation and developer
  workflows.
---
# Strategy Risk Model

## Overview
This model defines how the arbitration lane assesses the inherent risk of a chosen merge strategy.

## Risk Factors
1. **Blast Radius**: The number of subsystems affected by the integration.
2. **Complexity**: The cyclomatic and semantic complexity of the synthesized code.
3. **Confidence**: The model's self-reported certainty in the proposed path.
4. **Historical Override Rate**: Frequency of human intervention for this strategy.

## Strategy Risk Matrix

| Strategy ID | Risk Profile | Default Posture |
| :--- | :---: | :--- |
| **PATCH_ISOLATION** | LOW | Supervised Auto-Apply |
| **OURS_THEN_PORT** | MEDIUM | Human Approval Required |
| **INTERFACE_FIRST** | HIGH | Human Gated |
| **MIGRATION_FIRST** | HIGH | Human Gated |
| **HUMAN_DEFER** | CRITICAL | Manual Execution |

## Enforcement
Strategies tagged as **HIGH** or **CRITICAL** risk automatically trigger an `AutonomyGate` of `DEFER_TO_HUMAN` or `PATCH_PLAN_ALLOWED_HUMAN_REVIEW_REQUIRED`.
