# PROMPT_A13

## Goal
Extract hook contracts and event flows.

## Inputs
- Source scope (scan these roots first):
- `.vibe/**`
- `.claude/**`
- `.dopemux/**`
- `.github/**`
- `.githooks/**`
- `.taskx/**`
- `mcp-proxy-config.copilot.yaml`
- `compose/**`
- `config/**`
- `configs/**`
- `docker/**`
- `scripts/**`
- `tools/**`

- `.vibe/**`
- `.claude/**`
- `.dopemux/**`
- `.github/**`
- `.githooks/**`
- `.taskx/**`
- `mcp-proxy-config.copilot.yaml`
- `compose/**`
- `config/**`
- `configs/**`
- `docker/**`
- `installers/**`
- `ops/**`
- `scripts/**`
- `tools/**`

- `.vibe/**`
- `.claude/**`
- `.dopemux/**`
- `.github/**`
- `.githooks/**`
- `.taskx/**`
- `mcp-proxy-config.copilot.yaml`
- `compose/**`
- `config/**`
- `configs/**`
- `docker/**`
- `installers/**`
- `ops/**`
- `scripts/**`
- `tools/**`

- `.vibe/**`
- `.claude/**`
- `mcp-proxy-config.copilot.yaml`

- `.vibe/**`
- `.claude/**`
- `mcp-proxy-config.copilot.yaml`

- `src/dopemux/hooks/**`
- `src/dopemux/mcp/hooks.py`
- `.claude/hooks/**`
- `src/dopemux/events/**`
- `src/dopemux/event_bus.py`

## Outputs
- `HOOK_CONTRACT_SURFACE.json`
- `EVENT_FLOW_GRAPH.json`

## Schema
- Output contracts:
  - `HOOK_CONTRACT_SURFACE.json`
    - `kind`: `json_item_list`
  - `EVENT_FLOW_GRAPH.json`
    - `kind`: `json_item_list`

## Extraction Procedure
1. Scan hooks and events.
2. Output JSON.
