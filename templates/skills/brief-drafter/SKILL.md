---
name: brief-drafter
description: Drafts workflow briefs from existing dopeTask, task-packet, or task-orchestrator authority before any decomposition work begins.
---

# Brief Drafter

Use this skill when starting a Dopemux internal workflow run.

## Rules

- Prefer existing authority in this order: dopeTask artifact, task packet, task-orchestrator output, then local mirror notes.
- Do not invent scope, tasks, or acceptance criteria that are not present in authority.
- Mark unknown fields explicitly.
- Stop if no trustworthy authority exists.

## Output

Return:

1. `brief_summary`
2. `authority_sources`
3. `scope_in`
4. `scope_out`
5. `acceptance_signals`
6. `unknowns`
