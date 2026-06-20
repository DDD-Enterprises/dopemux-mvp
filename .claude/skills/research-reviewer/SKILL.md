---
name: research-reviewer
description: Approve, reject, or block workflow research before planning is allowed to proceed.
---

# Research Reviewer

Use this skill for the `research_review` gate.

## Contract

- Review for completeness, evidence quality, and risk coverage.
- Reject research that relies on assumptions without repo evidence.
- Approve only when the next planner can act without guessing.
- Do not write the plan in this phase.

## Required Output

- `research-review.md`
- Approval, rejection, or blocker rationale
- Specific follow-up gaps when not approved

## Completion Rule

Emit one of:

```xml
<workflow-checkpoint phase="research_review" status="approved" task="task-001" summary="Research approved" artifact="/abs/path/research-review.md" />
```

```xml
<workflow-checkpoint phase="research_review" status="rejected" task="task-001" summary="Research needs more evidence" artifact="/abs/path/research-review.md" />
```
