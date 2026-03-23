---
title: PM Plane Output Boundaries
description: Authority boundaries and write classification policies for PM plane operations
status: stable
last_updated: 2026-03-23
id: write-boundaries
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-23'
last_review: '2026-03-23'
next_review: '2026-06-21'
prelude: PM Plane Output Boundaries (explanation) for dopemux documentation and developer
  workflows.
---
# PM Plane Output Boundaries

## Objective
Establish the strict separation between **PM metadata writes** and **workflow-significant writes** to ensure Dopemux systems maintain distinct authority boundaries.

## Authority Boundaries

1. **Leantime** is the canonical PM record/reflection authority. It manages projects, goals, tasks, and sprint planning. It is **not** the workflow-law authority.
2. **Task Orchestrator** is the canonical workflow authority. It adjudicates workflow-significant changes such as task state transitions, phase changes, and blocker clearance.
3. **ConPort / Dope-Memory** handle chronicle logging and task progress context.

## Write Classification Policy

All payloads entering the PM plane must be classified.

### Direct PM Metadata Writes (Allowed)
These updates are allowed to proceed through the generic PM update path (\`pm_update_work_item\`). They represent record updates and reflection states, such as:
- \`title\`, \`headline\`
- \`description\`, \`details\`
- \`assignee\`, \`assigned_to\`, \`owner\`
- \`tags\`, \`priority\`

### Workflow-Significant Writes (Filtered)
These updates represent state machine transitions and **must** be routed through the Task Orchestrator (\`pm_transition_task\`). Direct writes to these fields via the PM bridge are **prohibited**:
- \`status\`, \`state\`
- \`blocker_status\`, \`is_blocked\`
- \`completion_date\`, \`actual_hours\`

## Implementation Directives

### 1. The Bridge Filter
The PM Bridge (\`dopecon-bridge\`) must implement a schema-aware filter. If a PATCH request contains workflow-significant fields, it must:
1. Reject the request if no orchestrator transition is linked.
2. OR, transparently trigger the Task Orchestrator transition before allowing the PM record update.

### 2. The Taskmaster Constraint
Taskmaster adapters must never update a task's \`status\` field directly in Leantime. They must call \`pm_transition_task\` which will update the status in the Orchestrator first, then sync to Leantime.
