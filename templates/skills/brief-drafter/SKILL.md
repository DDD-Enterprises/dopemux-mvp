---
name: brief-drafter
description: Draft or normalize a Dopemux workflow brief from task packets, PM artifacts, or a local fallback brief before breakdown begins.
---

# Brief Drafter

Use this skill when a workflow needs a source-of-truth brief.

## Contract

- Prefer existing `dopeTask`, task packet, or task-orchestrator artifacts over creating local markdown.
- If no canonical brief exists, create a local `brief.md` that clearly marks itself as a fallback mirror.
- Explain the next move before editing or generating artifacts.
- Keep claims evidence-backed and scope-limited to the current workflow.

## Required Output

- Goal summary
- Constraints and non-goals
- Success criteria
- Stop conditions
- Source provenance

## Completion Rule

Emit:

```xml
<workflow-checkpoint phase="brief" status="complete" summary="Brief ready" artifact="/abs/path/brief.md" />
```
