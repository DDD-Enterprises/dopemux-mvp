---
id: HIGH_RISK_HANDOFF_RULES
title: High Risk Handoff Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Rules for handling high-risk branches during PR handoff.
---
# High Risk Handoff Rules

When a branch triggers a `HIGH_RISK_HANDOFF_REQUIRED` decision, or carries a `HIGH` risk hint (e.g., migrations, schema changes, massive refactoring), the handoff bundle must explicitly alert the downstream merge specialist.

## Rules
1. **Creation Posture**: High-risk branches must default to `CREATE_DRAFT_PR` or `PACKAGE_ONLY`. They must NEVER be created as `CREATE_FINAL_PR` autonomously.
2. **Context Preservation**: The specific risk flags and ambiguity warnings must be preserved verbatim in the `warnings` array of the handoff bundle.
3. **Next Step Routing**: The `recommended_next_step` must be explicitly set to `MERGE_SPECIALIST_HIGH_RISK_AWARE_FLOW`.
4. **Integration Notes**: The drafted PR body MUST include the "High-Risk Integration Notes" section, forcing human reviewers to acknowledge the complexity.
