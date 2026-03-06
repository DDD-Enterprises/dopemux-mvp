# PROMPT_C12

## Goal
Extract agent orchestration and launch patterns.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `services/agents/**`
- `src/dopemux/agent_orchestrator.py`

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `services/agents/**`
- `src/dopemux/agent_orchestrator.py`

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

- `services/agents/**`
- `src/dopemux/agent_orchestrator.py`

## Outputs
- `AGENT_ORCHESTRATION_SURFACE.json`

## Schema
- Output contracts:
  - `AGENT_ORCHESTRATION_SURFACE.json`
    - `kind`: `json_item_list`

## Extraction Procedure
1. Scan agents and orchestrators.
2. Output JSON.
