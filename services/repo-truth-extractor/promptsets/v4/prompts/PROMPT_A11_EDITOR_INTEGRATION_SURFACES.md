# PROMPT_A11

## Goal
Extract editor and IDE integration points.

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

- `.claude/**`
- `.vibe/**`
- `mcp-proxy-config*.yaml`
- `mcp-proxy-config.json`
- `src/dopemux/claude/**`

## Outputs
- `EDITOR_INTEGRATION_SURFACE.json`

## Schema
- Output contracts:
  - `EDITOR_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`

## Extraction Procedure
1. Scan for editor configs
2. Output JSON.
