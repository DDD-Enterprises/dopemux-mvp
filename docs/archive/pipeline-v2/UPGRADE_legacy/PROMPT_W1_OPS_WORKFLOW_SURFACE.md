---
id: PROMPT_W1_OPS_WORKFLOW_SURFACE
title: Prompt W1 Ops Workflow Surface
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt W1 Ops Workflow Surface (explanation) for dopemux documentation and
  developer workflows.
---
# Prompt W1 (v2): Ops Workflow Surface (Compose + Scripts)

**Outputs:** `WORKFLOW_SURFACE_OPS.json`

---

## TASK

Produce ONE JSON file: `WORKFLOW_SURFACE_OPS.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE.

## SCOPE

Extract from:
- `docker-compose*.yml`, `compose.yml`, `compose/**`
- Scripts under: `scripts/**`, `ops/**`, `tools/**`
- Task runners: `Makefile`, `justfile`, `package.json` (npm scripts), `pyproject.toml` (uv scripts)

## WORKFLOW_SURFACE_OPS.json

### From Docker Compose Files

Extract service definitions:
- `service_name`
- `depends_on` (dependencies)
- `ports` (exposed ports)
- `volumes` (mount paths)
- `command` (startup command - first 100 characters)
- `image` or `build` path

Emit items:
- `workflow_id`: `"workflow_ops:compose:" + service_name`
- `domain=code_service`
- `kind=workflow_step`
- `name=<service_name>`
- `path`: compose file path
- `strings`: `["compose_service:<name>", "depends_on:<dep>", "port:<n>", "cmd:<...>"]`

### From Scripts

Extract scripts that orchestrate multi-service flows:
- Bash/Zsh/Python scripts under `scripts/`, `ops/`, `tools/`
- Look for patterns: `docker compose`, `uv run`, `taskx`, `dopemux`, service start/stop

Emit items:
- `workflow_id`: `"workflow_ops:script:" + script_basename`
- `domain=code_hook` or `code_entrypoint`
- `kind=workflow_step`
- `name=<script_name>`
- `path`: script path
- `strings`: `["cmd:<command>", "service:<name>", "file:<...>"]` (extracted from script)

### From Task Runners

Extract targets/tasks:
- Makefile targets
- package.json scripts
- pyproject.toml script sections

Emit items:
- `workflow_id`: `"workflow_ops:task:" + task_name`
- `domain=code_entrypoint`
- `kind=workflow_step`
- `name=<task/target name>`
- `strings`: `["runner:make|npm|uv", "cmd:<...>"]`

## RULES

- **No inference about purpose**
- **Extract literal values only**
- **JSON only**, ASCII only
- **Deterministic sorting** by (domain, path, name)

## OUTPUT FORMAT

```json
{
  "artifact_type": "WORKFLOW_SURFACE_OPS",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "workflows": [...]
}
```
