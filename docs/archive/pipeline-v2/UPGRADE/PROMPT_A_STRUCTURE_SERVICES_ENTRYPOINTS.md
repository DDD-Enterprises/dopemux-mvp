---
id: PROMPT_A_STRUCTURE_SERVICES_ENTRYPOINTS
title: Prompt A Structure Services Entrypoints
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt A Structure Services Entrypoints (explanation) for dopemux documentation
  and developer workflows.
---
# Prompt A (v2): Structure + Services + Entrypoints

**Outputs:** `STRUCTURE_MAP.json`, `SERVICE_MAP.json`, `ENTRYPOINTS.json`

---

## TASK

Produce THREE JSON files: `STRUCTURE_MAP.json`, `SERVICE_MAP.json`, `ENTRYPOINTS.json`.

## TARGET INPUTS

- **WORKING TREE:** `/Users/hue/code/dopemux-mvp` (primary truth)
- **BASELINE:** `dopemux-mvp-llm-20260206-074421.zip` (drift comparator only - if present)

## STRUCTURE_MAP.json

- Enumerate files under: `services/**`, `src/**`, `config/**`, `scripts/**`, `docs/**`, `compose*.yml`, `Dockerfile*`
- For each file emit an item:
  - `domain=code_service` if under `services/`, else `code_entrypoint` if looks like entrypoint, else `doc_meta` if `docs/`
  - `kind=file`
  - `name=basename`
  - `strings=[language, extension, top_level_dir]`
  - `excerpt=first 2 non-empty lines (if text)`

## SERVICE_MAP.json

- Identify each service under `services/**` and any compose-defined services.
- For each service emit an item:
  - `domain=code_service`
  - `kind=service`
  - `name=<service name>`
  - Include references to:
    - dockerfile path (if any)
    - compose service name and ports (if any)
    - entry command module/file (if any)
  - `strings` should include: `["compose:<name>", "port:<n>", "dockerfile:<path>"]` when present

## ENTRYPOINTS.json

- Find:
  - console scripts in `pyproject.toml` / `setup.cfg` / `setup.py`
  - `__main__` blocks
  - Typer/Click app instantiations
  - FastAPI app objects
- For each emit an item:
  - `domain=code_entrypoint`
  - `kind=entrypoint`
  - `name=<entrypoint name>`
  - `symbol=<function or app var name if present>`

## OUTPUT RULES

- JSON only.
- Universal item schema for every record.
- Deterministic sorting.
