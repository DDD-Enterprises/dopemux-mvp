---
id: OPERATOR_REVIEW_FORM
title: Operator Review Form
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Structured form for capturing human feedback during the live pilot.
---
# Operator Review Form

Operators must fill out this form (or its programmatic equivalent) for every branch processed in the Live Pilot.

## 1. Domain Accuracy (Pass/Fail)
- **Branch Truth Accurate?**: [Y/N]
- **Adjacent-Work Detection Useful?**: [Y/N]
- **Docs/Changelog Obligations Correct?**: [Y/N]

## 2. Draft Quality
- **Title Quality**: (Excellent / Good / Usable / Poor)
- **Body Usefulness**: (Highly Useful / Useful / Misleading)

## 3. Handoff & Decision
- **Final Decision Correct?**: [Y/N]
- **Handoff Bundle Sufficient?**: [Y/N]

## 4. Overall Acceptance
- **Acceptance Status**: `ACCEPTED` | `PARTIALLY_ACCEPTED` | `REJECTED` | `DEFERRED_FOR_REVIEW`

## 5. Overrides
If the skill's decision was overridden:
- **What was overridden?**: (e.g., Blocked on missing docs, but docs weren't actually needed)
- **Severity of Override**: `INFO` | `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
- **Reason Category**: (Missing context / Overblocking / Underblocking / Repo-convention mismatch / Preference)
