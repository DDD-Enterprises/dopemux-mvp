---
id: AUTONOMY_POLICY
title: Autonomy Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Autonomy Policy (explanation) for dopemux documentation and developer workflows.
---
# Autonomy Policy

## Overview
Autonomy Gates ensure that model consensus does not bypass human authority in high-risk scenarios.

## Gate Levels

| Level | Confidence Required | Risk Constraints | Outcome |
| :--- | :---: | :--- | :--- |
| **RECOMMENDATION_ONLY** | Any | Any | Advisory output only. |
| **PATCH_PLAN_ALLOWED** | HIGH/MEDIUM | No `HIGH_RISK` conflicts. | Generate patch, human review required. |
| **NO_AUTONOMOUS_PROGRESS** | LOW/INSUFFICIENT | Any | Block all automation. |
| **DEFER_TO_HUMAN** | Any | High Challenger objection severity. | Explicitly stop and hand off. |

## Rules
1. **Low Confidence Blocks**: Any decision with `LOW` confidence must result in `NO_AUTONOMOUS_PROGRESS`.
2. **Objections Tighten**: material Challenger objections automatically downgrade the autonomy level.
3. **Synthesis Requires Verification**: Any `SYNTHESIZE_BOTH` strategy must include a `RequiredVerificationPlan`.
