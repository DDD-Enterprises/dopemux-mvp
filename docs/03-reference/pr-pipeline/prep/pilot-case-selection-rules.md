---
id: PILOT_CASE_SELECTION_RULES
title: Pilot Case Selection Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Rules for selecting branches to run in the live pilot.
---
# Pilot Case Selection Rules

Branch candidates must be triaged into one of three buckets before the pilot runs.

## 1. PILOT_READY
The branch is suitable for standard pilot execution.
- Base branch is clearly detectable.
- No severe corruption in the local Git state.
- An operator is available to review the output.
- The case naturally fits the approved governance posture.

## 2. PILOT_READY_HIGH_RISK
The branch is suitable, but contains high-risk elements requiring maximum caution.
- Adjacent-work ambiguity is non-trivial (e.g., dirty stashes exist).
- Contains DB migrations, infrastructure configs, or public API changes.
- Will likely fall back to `PACKAGE_ONLY` or `BLOCKED_NO_CREATE` during the run.

## 3. DEFER_FOR_REVIEW
Do not run the pilot on this branch yet.
- Branch truth is hopelessly ambiguous (e.g., detached HEAD with no upstream).
- Critical context is missing.
- The blast radius exceeds pilot safety parameters.
- Operator is unavailable.
