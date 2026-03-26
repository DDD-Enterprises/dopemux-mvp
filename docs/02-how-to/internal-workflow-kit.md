---
id: internal-workflow-kit
title: Run the Internal Workflow Kit
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-19'
prelude: Goal-oriented guide for starting, inspecting, and closing Dopemux internal workflow runs.
---
# Run the Internal Workflow Kit

Use this guide when you want Dopemux to manage a bounded implementation workflow with explicit phases, review gates, and isolated executor work.

## Prerequisites

- A Dopemux workspace with `.dopemux/`
- Claude native hooks registered if you want stop-hook continuity
- A task packet, PM artifact, or a prompt strong enough to seed a local fallback brief

## 1. Initialize or Reattach a Workflow

Create a workflow for the current workspace:

```bash
dopemux workflow init "Harden the workflow kit"
```

Behavior:

- Reuses the active workflow when one is already bound to the workspace or instance
- Prefers an existing task packet or PM artifact for the brief
- Falls back to a local `brief.md` beside the workflow state when no canonical brief exists

## 2. Inspect the Current Phase and Launch Preview

Check the active workflow:

```bash
dopemux workflow status
dopemux workflow inspect --json-output
```

Use `inspect` when you need:

- phase, task, and checkpoint history
- current gate failures
- the next executor launch preview

## 3. Start the Manager and Executor Lanes

Manager lane:

```bash
dopemux start --role workflow-manager
```

Executor lane for isolated task delivery:

```bash
dopemux start --role workflow-executor
```

The manager lane validates artifacts and verification before advancing phases. The executor lane stays scoped to one task at a time.

## 4. Emit Review-Safe Checkpoints

Workers should end bounded phases with a checkpoint token:

```xml
<workflow-checkpoint phase="plan_review" status="approved" task="task-001" summary="Plan approved" artifact="/abs/path/plan-review.md" verification="pytest -q;;ruff check src" />
```

Use the completion token only when the whole workflow is ready to close:

```xml
<promise>WORKFLOW_COMPLETE</promise>
```

## 5. Reattach from Another Worktree or Instance

When you switch directories or instances, rebind to the matching workflow:

```bash
dopemux workflow resume
```

Resolution favors:

1. active workspace ancestry
2. family root ancestry
3. matching instance id
4. active status and recent activity

## 6. Cancel Without Deleting Artifacts

If you need to stop the run but keep the trail:

```bash
dopemux workflow cancel
```

This marks the workflow inactive and leaves state plus artifacts in place for later inspection.

## Verification

- `dopemux workflow status --json-output`
- `dopemux workflow inspect --json-output`
- `python -m compileall src/dopemux/workflow src/dopemux/claude/native_hooks.py src/dopemux/commands/workflow_group_commands.py`

## Related Docs

- [Internal Workflow Kit Reference](../03-reference/internal-workflow-kit.md)
- [Workflow Kit Architecture](../04-explanation/workflow-kit-architecture.md)
- [Workflow Kit Transfer RFC](../91-rfc/workflow-kit-pickle-mechanics-transfer.md)
