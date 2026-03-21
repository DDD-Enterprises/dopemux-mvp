---
name: plan-reviewer
description: Review an implementation plan for scope, evidence alignment, and verification quality before coding starts.
---

# Plan Reviewer

Use this skill for the `plan_review` gate.

## Contract

- Confirm the plan follows approved research and does not skip evidence.
- Reject plans with vague or missing verification commands.
- Reject plans that introduce scope creep or cross-task spillover.
- No code is allowed until this review is approved.

## Required Output

- `plan-review.md`
- Approval, rejection, or blocker rationale
- Any required plan changes

## Completion Rule

Emit one of:

```xml
<workflow-checkpoint phase="plan_review" status="approved" task="task-001" summary="Plan approved" artifact="/abs/path/plan-review.md" />
```

```xml
<workflow-checkpoint phase="plan_review" status="rejected" task="task-001" summary="Plan needs revision" artifact="/abs/path/plan-review.md" />
```
