---
id: EXEC_A_STRUCTURE_SERVICES_ENTRYPOINTS
title: Exec A Structure Services Entrypoints
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Exec A Structure Services Entrypoints (explanation) for dopemux documentation
  and developer workflows.
---
# EXECUTABLE PROMPT: A - Structure + Services + Entrypoints

---

## YOUR ROLE

You are a **mechanical extractor**. You enumerate files, services, and entrypoints. Extract literal text only — no inference about behavior.

---

## TASK

Scan the provided codebase files and produce THREE JSON files:
1. `STRUCTURE_MAP.json`
2. `SERVICE_MAP.json`
3. `ENTRYPOINTS.json`

---

## OUTPUT 1: STRUCTURE_MAP.json

For each file under `services/**`, `src/**`, `config/**`, `scripts/**`, `compose*.yml`, `Dockerfile*`:

```json
{
  "path": "services/chronicle/main.py",
  "line_range": [1, 1],
  "domain": "code_service",
  "kind": "file",
  "name": "main.py",
  "language": "python",
  "extension": ".py",
  "top_level_dir": "services",
  "excerpt": "from fastapi import FastAPI\napp = FastAPI(title=\"chronicle\")"
}
```

### domain Classification

- `code_service` — files under `services/`
- `code_entrypoint` — files containing `if __name__`, `app =`, or `cli =`
- `code_script` — files under `scripts/`
- `code_config` — files under `config/` or `compose*.yml` or `Dockerfile*`
- `doc_meta` — files under `docs/` (index path only, do not read content)

### excerpt

First 2 non-empty, non-comment lines. Truncate at 120 chars per line.

---

## OUTPUT 2: SERVICE_MAP.json

For each service directory under `services/` AND each compose-defined service:

```json
{
  "path": "services/chronicle",
  "line_range": [1, 1],
  "domain": "code_service",
  "kind": "service",
  "name": "chronicle",
  "dockerfile": "services/chronicle/Dockerfile",
  "compose_service": "chronicle",
  "compose_ports": ["8001:8001"],
  "entry_module": "services/chronicle/main.py",
  "entry_command": "uvicorn main:app --host 0.0.0.0 --port 8001",
  "dependencies": ["postgres", "redis"]
}
```

### Extract From

- `services/*/` directory names → service name
- `compose.yml` / `docker-compose*.yml` → service blocks (ports, depends_on, command)
- `Dockerfile*` → if present in service dir
- `pyproject.toml` → scripts section if pointing to a service

---

## OUTPUT 3: ENTRYPOINTS.json

```json
{
  "path": "src/dopemux/cli.py",
  "line_range": [45, 45],
  "domain": "code_entrypoint",
  "kind": "entrypoint",
  "name": "dopemux",
  "entry_type": "console_script",
  "symbol": "cli",
  "source": "pyproject.toml [project.scripts]"
}
```

### Find

| Pattern                                 | entry_type       |
| --------------------------------------- | ---------------- |
| `[project.scripts]` in pyproject.toml   | `console_script` |
| `console_scripts` in setup.cfg/setup.py | `console_script` |
| `if __name__ == "__main__"` blocks      | `main_block`     |
| `app = FastAPI(...)`                    | `fastapi_app`    |
| `app = Typer(...)` or `@click.command`  | `cli_app`        |

---

## HARD RULES

1. **No inference** — extract literal text only
2. **JSON only** — no markdown, no prose, no explanation
3. **ASCII only** — no unicode in output
4. **Deterministic sorting** — sort by path (alphabetical), then line_range
5. **path + line_range required** — every item must include both fields
6. **excerpt ≤ 120 chars per line** — truncate, do not summarize

---

## OUTPUT FORMAT

Each file must have this wrapper:

```json
{
  "artifact_type": "STRUCTURE_MAP",
  "generated_at_utc": "2026-02-15T22:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```

---

## BEGIN EXTRACTION

Process the provided context files and produce the three JSON outputs now.
