# PROMPT_C13

## Goal
Extract ADHD engine subsystem details.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `src/dopemux/adhd/**`
- `services/adhd_engine/**`

## Outputs
- `ADHD_ENGINE_SURFACE.json`

## Schema
- Output contracts:
  - `ADHD_ENGINE_SURFACE.json`
    - `kind`: `json_item_list`

## Extraction Procedure
1. Scan adhd engine files.
2. Output JSON.
