# EXECUTABLE PROMPT: W1 - Ops Workflow Surface

---

## YOUR ROLE

You are a **mechanical extractor**. You follow instructions exactly. You do not reason, interpret, or decide. You output JSON only.

---

## TASK

Extract operational workflows from Docker Compose files, scripts, and task runners.

Produce ONE JSON file: `WORKFLOW_SURFACE_OPS.json`

---

## TARGET

Working tree at: `/Users/hue/code/dopemux-mvp`

---

## SCOPE: Files to Extract From

### Docker Compose
- `docker-compose*.yml`
- `compose.yml`
- `compose/**/*.yml`

### Scripts
- `scripts/**/*.sh`
- `scripts/**/*.py`
- `ops/**/*`
- `tools/**/*`
- `start-mcp-servers.sh`

### Task Runners
- `Makefile`
- `justfile`
- `package.json` (scripts section)
- `pyproject.toml` (scripts section)

---

## EXTRACTION RULES

### From Docker Compose Files

For each service definition, extract:
- `service_name`
- `depends_on` (list of dependencies)
- `ports` (exposed ports)
- `volumes` (mount paths - just the paths, not full syntax)
- `command` (startup command - first 100 chars)
- `image` or `build` context

Emit as workflow items with:
- `workflow_id`: `"workflow_ops:compose:" + service_name`
- `domain`: `code_service`
- `kind`: `workflow_step`
- `name`: service name
- `path`: compose file path
- `strings`: array of extracted facts:
  - `"compose_service:<name>"`
  - `"depends_on:<dep>"` (for each dependency)
  - `"port:<number>"` (for each port)
  - `"cmd:<command>"` (first 100 chars)

### From Scripts

For scripts that orchestrate services:
- Look for: `docker compose`, `uv run`, `taskx`, `dopemux`, service start/stop commands
- Extract service/tool names mentioned
- Extract commands run

Emit as:
- `workflow_id`: `"workflow_ops:script:" + basename`
- `domain`: `code_hook` or `code_entrypoint`
- `kind`: `workflow_step`
- `name`: script basename
- `path`: script path
- `strings`: 
  - `"cmd:<command>"` (for each command found)
  - `"service:<name>"` (for each service mentioned)

### From Task Runners

Extract targets/tasks from:
- Makefile targets
- package.json scripts
- pyproject.toml scripts

Emit as:
- `workflow_id`: `"workflow_ops:task:" + task_name`
- `domain`: `code_entrypoint`
- `kind`: `workflow_step`
- `name`: task/target name
- `path`: file path
- `strings`:
  - `"runner:make|npm|uv"`
  - `"cmd:<command>"` (first 100 chars)

---

## OUTPUT: WORKFLOW_SURFACE_OPS.json

```json
{
  "artifact_type": "WORKFLOW_SURFACE_OPS",
  "generated_at_utc": "2026-02-15T21:20:00Z",
  "source_artifact": "WORKING_TREE",
  "workflows": [
    {
      "workflow_id": "workflow_ops:compose:chronicle",
      "domain": "code_service",
      "kind": "workflow_step",
      "name": "chronicle",
      "path": "compose.yml",
      "line_range": [45, 67],
      "strings": [
        "compose_service:chronicle",
        "depends_on:postgres",
        "port:8080",
        "cmd:uv run python -m services.chronicle.main"
      ]
    },
    {
      "workflow_id": "workflow_ops:script:start-mcp-servers",
      "domain": "code_hook",
      "kind": "workflow_step",
      "name": "start-mcp-servers.sh",
      "path": "start-mcp-servers.sh",
      "line_range": [1, 50],
      "strings": [
        "cmd:cd docker/mcp-servers && docker compose up -d",
        "service:dope-context",
        "service:dope-brainz"
      ]
    },
    {
      "workflow_id": "workflow_ops:task:dev",
      "domain": "code_entrypoint",
      "kind": "workflow_step",
      "name": "dev",
      "path": "package.json",
      "line_range": [12, 12],
      "strings": [
        "runner:npm",
        "cmd:docker compose up -d && npm run watch"
      ]
    }
  ]
}
```

---

## HARD RULES

1. **No inference about purpose** - just extract literal facts
2. **Extract exact values only**
3. **JSON only** - no markdown, no prose
4. **ASCII only**
5. **Deterministic sorting** - sort workflows by (domain, path, name)
6. **Cap strings** - max 10 strings per workflow item

---

## BEGIN EXTRACTION

Scan the target directory and produce the JSON output now.
