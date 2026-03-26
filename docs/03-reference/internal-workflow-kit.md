---
id: internal-workflow-kit-reference
title: Internal Workflow Kit Reference
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-19'
prelude: Technical reference for workflow phases, state schema, checkpoint tokens, roles, and skill-pack assets.
---
# Internal Workflow Kit Reference

## Purpose

The internal workflow kit gives Dopemux a stateful, review-gated execution loop for complex implementation work.

## CLI Surface

| Command | Purpose |
| --- | --- |
| `dopemux workflow init [prompt]` | Create or resume a workflow for the current workspace |
| `dopemux workflow status` | Show current workflow summary and gate failures |
| `dopemux workflow resume` | Rebind the current workspace or instance to an existing workflow |
| `dopemux workflow cancel` | Mark a workflow inactive without deleting artifacts |
| `dopemux workflow inspect` | Show state, history, checkpoints, and executor launch preview |

## Workflow Phases

1. `brief`
2. `breakdown`
3. `research`
4. `research_review`
5. `plan`
6. `plan_review`
7. `implement`
8. `refactor`
9. `complete`

## Phase Gates

| Target phase | Required proof |
| --- | --- |
| `research_review` | `research.md` or a `research` completion checkpoint |
| `plan` | approved `research_review` checkpoint |
| `plan_review` | `plan.md` or a `plan` completion checkpoint |
| `implement` | approved `plan_review` checkpoint |
| `refactor` | completed `implement` checkpoint |
| `complete` | all tasks done, required artifacts present, verification passed |

## State Location

- State file: `.dopemux/workflows/<workflow_id>/state.json`
- Per-task artifacts: `.dopemux/workflows/<workflow_id>/tasks/<task_id>/`

## Required Persisted State Fields

- `workflow_id`
- `workspace_root`
- `instance_id`
- `mode`
- `phase`
- `current_task_id`
- `iteration`
- `max_iterations`
- `max_minutes`
- `completion_token`
- `started_at`
- `updated_at`
- `status`
- `history`

## Checkpoint Token

```xml
<workflow-checkpoint phase="implement" status="complete" task="task-001" summary="Implementation complete" artifact="/abs/path/implementation-notes.md" verification="pytest -q;;ruff check src" />
```

Rules:

- `phase` must match a Dopemux workflow phase
- `status` must be one of `complete`, `approved`, `rejected`, `blocked`
- `verification` commands are separated with `;;`
- `artifact` should point to the phase artifact when available

## Completion Token

```xml
<promise>WORKFLOW_COMPLETE</promise>
```

## Roles, Personas, and Profiles

| Asset | Path |
| --- | --- |
| Manager role | `workflow-manager` |
| Executor role | `workflow-executor` |
| Manager persona | `.claude/personas/workflow-manager.agent.md` |
| Executor persona | `.claude/personas/workflow-executor.agent.md` |
| Manager profile seed | `config/profiles/workflow-manager.yaml` |
| Executor profile seed | `config/profiles/workflow-executor.yaml` |

## Workflow Skill Pack

- `templates/skills/brief-drafter/`
- `templates/skills/task-breakdown/`
- `templates/skills/code-researcher/`
- `templates/skills/research-reviewer/`
- `templates/skills/implementation-planner/`
- `templates/skills/plan-reviewer/`
- `templates/skills/code-implementer/`
- `templates/skills/quality-refactorer/`

## Claude Hook Responsibilities

- Inject workflow context during `SessionStart` and `UserPromptSubmit`
- Enforce iteration and time limits before tool use
- Record tool attempts and results around tool execution
- Block `Stop` while the workflow is active unless a valid checkpoint or completion token was emitted

## Related Docs

- [Run the Internal Workflow Kit](../02-how-to/internal-workflow-kit.md)
- [Workflow Kit Architecture](../04-explanation/workflow-kit-architecture.md)
- [Workflow Kit Transfer RFC](../91-rfc/workflow-kit-pickle-mechanics-transfer.md)
