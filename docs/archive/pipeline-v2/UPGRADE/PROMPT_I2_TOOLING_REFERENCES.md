---
id: PROMPT_I2_TOOLING_REFERENCES
title: Prompt I2 Tooling References
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt I2 Tooling References (explanation) for dopemux documentation and
  developer workflows.
---
# Prompt I2 (v2): LLM Tooling & Server References

**Outputs:** `LLM_TOOLING_REFERENCES.json`, `LLM_SERVER_CALL_SURFACE.json`

---

## TASK

Produce TWO JSON files: `LLM_TOOLING_REFERENCES.json`, `LLM_SERVER_CALL_SURFACE.json`.

## INPUT

- `LLM_INSTRUCTION_INDEX.json` from I1

## SCOPE

**Only files listed in LLM_INSTRUCTION_INDEX.json**

## 1) LLM_TOOLING_REFERENCES.json

Extract literal references to:
- **Tool names** (in lists, code blocks, "use tool X")
- **MCP server names** (server identifiers, package names)
- **Commands** to run: `uv`, `docker compose`, `taskx`, `dopemux`, `python -m`
- **File paths** used as authorities or references
- **Environment variable names** (e.g., `ANTHROPIC_API_KEY`, `DOPEMUX_HOME`)

For each reference:
- `ref_id`: `"ref:" + doc_id + ":" + line_range[0] + ":" + ref_name`
- `doc_id`, `path`, `line_range`, `heading_path`
- `ref_type`: `mcp_tool|mcp_server|command|file_ref|env_var`
- `ref_name`: exact literal string
- `context_excerpt`: <=3 lines around reference

**Example:**
```json
{
  "ref_id": "ref:doc:.claude/PRIMER.md:45:dope_context",
  "doc_id": "doc:.claude/PRIMER.md",
  "path": ".claude/PRIMER.md",
  "line_range": [45, 45],
  "heading_path": "MCP Tools > Available Tools",
  "ref_type": "mcp_server",
  "ref_name": "dope_context",
  "context_excerpt": "Use dope_context server for memory retrieval"
}
```

## 2) LLM_SERVER_CALL_SURFACE.json

Extract patterns where code/instructions invoke servers/tools:
- `"call <tool>"`
- `"use <server>"`
- `"invoke MCP"`
- `"route to"`
- `"run command:"`
- YAML/JSON blocks listing `mcp_servers` or tool registries

For each invocation:
- `call_id`: `"call:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `call_pattern`: `call_tool|use_server|invoke_mcp|route_to|run_command|config_block`
- `target_name`: server/tool name if literal, else section name
- `block_excerpt`: up to 4 lines around invocation

## RULES

- **Exact string extraction only**
- **No inference** about what tools do
- **JSON only**, ASCII only
- **Deterministic sorting** by (doc_id, line_range[0])

## OUTPUT FORMAT

Both files follow this structure:
```json
{
  "artifact_type": "LLM_TOOLING_REFERENCES",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "refs": [...]
}
```
