---
name: task-breakdown
description: Breaks a validated workflow brief into task slices while treating the PM plane as canonical and local workflow files as mirrors only.
---

# Task Breakdown

Use after a brief is frozen.

## Rules

- PM plane authority wins over local markdown or JSON mirrors.
- Local workflow task files may mirror PM data but must not become the canonical source.
- Each task must include required artifacts and exact verification commands.
- Do not assign implementation until the research phase is complete.

## Output

Return:

1. `task_list`
2. `pm_authority_status`
3. `required_artifacts`
4. `verification_commands`
5. `local_mirror_notes`
