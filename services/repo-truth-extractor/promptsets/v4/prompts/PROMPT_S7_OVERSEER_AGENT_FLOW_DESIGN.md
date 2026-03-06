# PROMPT_S7

## Goal
Synthesize overseer:agent architecture from integration surfaces.

## Inputs
- Source scope (scan these roots first):
- `EDITOR_INTEGRATION_SURFACE.json`
- `HOOK_CONTRACT_SURFACE.json`
- `EVENT_FLOW_GRAPH.json`
- `AGENT_ORCHESTRATION_SURFACE.json`

## Outputs
- `S7_OVERSEER_AGENT_FLOW_DESIGN.md`

## Schema
- Output contracts:
  - `S7_OVERSEER_AGENT_FLOW_DESIGN.md`
    - `kind`: `markdown`

## Extraction Procedure
1. Synthesize JSONs into markdown.
2. Output MD.
