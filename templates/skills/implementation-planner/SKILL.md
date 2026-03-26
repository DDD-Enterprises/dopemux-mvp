---
name: implementation-planner
description: Produces a minimal implementation plan after research_review approval, including files, invariants, and validation commands.
---

# Implementation Planner

Use only after `research_review` is approved.

## Rules

- No code before plan approval.
- Keep the diff minimal and tied to verified contracts.
- Enumerate exact validation commands and expected success signals.
- Include rollback or containment notes when contract-sensitive files are touched.

## Output

Return:

1. `change_plan`
2. `files_likely_touched`
3. `invariants`
4. `validation_commands`
5. `rollback_notes`
