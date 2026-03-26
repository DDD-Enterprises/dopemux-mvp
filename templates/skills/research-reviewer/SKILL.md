---
name: research-reviewer
description: Reviews research evidence and either approves the research_review checkpoint or fails it closed with explicit gaps.
---

# Research Reviewer

Use after research output exists and before planning.

## Rules

- Fail closed if key authority files or runtime surfaces were skipped.
- Approve only when research supports a minimal implementation plan.
- Call out drift between docs, tests, and code.
- No code changes and no planning prose beyond approval rationale.

## Output

Return:

1. `checkpoint`
2. `decision`
3. `evidence_sufficiency`
4. `blocking_gaps`
