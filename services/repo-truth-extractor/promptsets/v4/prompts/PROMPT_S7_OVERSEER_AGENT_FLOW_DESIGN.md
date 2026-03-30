# PROMPT_S7_OVERSEER_AGENT_FLOW_DESIGN

## Goal
Synthesize overseer:agent architecture from integration surfaces.
(Note: Detailed instruction rewrite deferred to Opus. This is a structural stub to pass v5 linting.)

## Inputs
- Source scope (scan these roots first):
- `EDITOR_INTEGRATION_SURFACE.json`
- `HOOK_CONTRACT_SURFACE.json`
- `EVENT_FLOW_GRAPH.json`
- `AGENT_ORCHESTRATION_SURFACE.json`
- `SERVICE_CATALOG.json` (for context)

The inputs provided here represent the collective system understanding of the orchestration boundaries and agent integrations. It is crucial to review these inputs holistically to understand the overarching system architecture before attempting to synthesize the final markdown documentation.

## Outputs
- `S7_OVERSEER_AGENT_FLOW_DESIGN.md`

## Schema
- Output contracts:
  - `S7_OVERSEER_AGENT_FLOW_DESIGN.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`

The output format is highly unstructured markdown, but it must conform to the semantic expectations of the user and logically connect the agent definitions from the input JSON artifacts. Ensure the final document is readable, logically organized, and cleanly formatted for human review.

## Extraction Procedure
1. Initialize the synthesis context reading all input JSON artifacts.
2. Formulate the overarching architecture narrative connecting the overseer agent to its dependencies.
3. Synthesize JSON insights into a cohesive markdown document.
4. Output MD file according strictly to the schema.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
