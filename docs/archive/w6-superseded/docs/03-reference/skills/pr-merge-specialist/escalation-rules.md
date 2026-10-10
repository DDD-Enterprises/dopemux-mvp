---
id: ESCALATION_RULES
title: Escalation Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Escalation Rules (explanation) for dopemux documentation and developer workflows.
---
# PR Merge Specialist: Escalation Rules

## Escalation Triggers
A human operator must be engaged immediately if any of the following conditions are met:

1. **Ambiguous Feedback**: Reviewer comments that are vague ("this looks weird") or lack clear actionable intent.
2. **Conflicting Intent**: Two or more reviewers provide contradictory instructions for the same area of code.
3. **High-Risk Conflict**: The PR enters a `HIGH_RISK` conflict state (e.g., changes to security logic or core contracts) that the automated `rerere` path refuses.
4. **Design Disagreements**: Discussions regarding architecture, performance trade-offs, or product requirements.
5. **Governance Blocks**: Manual approvals required by policy that cannot be automated (e.g., legal or compliance review).
6. **Repeated Failure**: A verification task fails multiple times after automated retry attempts.

## Escalation Output
When an escalation is triggered, the engine must produce an **Escalation Packet** containing:
- **Source**: The specific comment, thread, or state that triggered the escalation.
- **Context**: The relevant file, line, and implementation history.
- **Reason**: A clear explanation of why automated remediation was refused.
- **Suggested Action**: A draft reply or specific question for the human operator to resolve.
