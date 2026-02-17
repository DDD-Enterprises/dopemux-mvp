---
id: EXEC_I2_TOOLING_REFERENCES
title: Exec I2 Tooling References
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Exec I2 Tooling References (explanation) for dopemux documentation and developer
  workflows.
---
# EXECUTABLE PROMPT: I2 - LLM Tooling & Server References

---

## YOUR ROLE

You are a **mechanical extractor**. You follow instructions exactly. You do not reason, interpret, or decide. You output JSON only.

---

## TASK

Extract all references to MCP servers, tools, commands, file paths, and environment variables from instruction files.

Produce TWO JSON files:
1. `LLM_TOOLING_REFERENCES.json`
2. `LLM_SERVER_CALL_SURFACE.json`

---

## INPUT

Read this file from the previous I1 pass:
- `LLM_INSTRUCTION_INDEX.json`

---

## SCOPE

**Process only the files listed in `LLM_INSTRUCTION_INDEX.json`**

Do not scan any other files.

---

## OUTPUT 1: LLM_TOOLING_REFERENCES.json

Extract literal references to:
- **Tool names** (e.g., `dope_context`, `filesystem`, `brave_search`)
- **MCP server names** (e.g., `@modelcontextprotocol/server-filesystem`)
- **Commands** to run: `uv`, `docker compose`, `taskx`, `dopemux`, `python -m`
- **File paths** mentioned as authorities or references
- **Environment variable names** (e.g., `ANTHROPIC_API_KEY`, `DOPEMUX_HOME`)

### Item Format

```json
{
  "ref_id": "ref:doc:.claude/PRIMER.md:45:dope_context",
  "doc_id": "doc:.claude/PRIMER.md",
  "path": ".claude/PRIMER.md",
  "line_range": [45, 47],
  "heading_path": "MCP Tools > Available Tools",
  "ref_type": "mcp_server",
  "ref_name": "dope_context",
  "context_excerpt": "Use the dope_context server to retrieve memory from Chronicle.\nIt provides read-only access to event history."
}
```

### ref_type Values

- `mcp_tool` - individual tool name
- `mcp_server` - server name/package
- `command` - shell command or program invocation
- `file_ref` - file path mentioned
- `env_var` - environment variable name

---

## OUTPUT 2: LLM_SERVER_CALL_SURFACE.json

Extract patterns where instructions invoke servers/tools:
- `"call <tool>"`
- `"use <server>"`
- `"invoke MCP"`
- `"route to <service>"`
- `"run command:"`
- YAML/JSON blocks listing `mcp_servers` or tool registries

### Item Format

```json
{
  "call_id": "call:doc:.claude/PRIMER.md:120",
  "doc_id": "doc:.claude/PRIMER.md",
  "path": ".claude/PRIMER.md",
  "line_range": [120, 124],
  "heading_path": "Workflows > Memory Retrieval",
  "call_pattern": "use_server",
  "target_name": "dope_context",
  "block_excerpt": "To retrieve memories:\n1. Use dope_context server\n2. Query by topic or recency\n3. Store results in context"
}
```

### call_pattern Values

- `call_tool` - explicit "call X" or "use tool X"
- `use_server` - "use X server"
- `invoke_mcp` - generic MCP invocation
- `route_to` - routing instruction
- `run_command` - command execution instruction
- `config_block` - YAML/JSON config listing servers/tools

---

## EXTRACTION RULES

1. **Exact strings only** - extract literal text, no paraphrasing
2. **Context excerpt** - include 2-4 lines around reference (cap 200 chars)
3. **heading_path** - breadcrumb to containing section (e.g., `"Tools > MCP Servers > Available"`)
4. **No inference** - don't guess what tools do or how they work
5. **Deterministic sorting** - sort by (doc_id, line_range[0])

---

## HARD RULES

1. **No summarization**
2. **No interpretation**
3. **JSON only** - no markdown, no prose
4. **ASCII only**
5. **Extract from instruction files only** (from LLM_INSTRUCTION_INDEX.json)

---

## OUTPUT FORMAT

### LLM_TOOLING_REFERENCES.json

```json
{
  "artifact_type": "LLM_TOOLING_REFERENCES",
  "generated_at_utc": "2026-02-15T21:15:00Z",
  "source_artifact": "WORKING_TREE",
  "input_files": ["LLM_INSTRUCTION_INDEX.json"],
  "refs": [
    {
      "ref_id": "ref:doc:.claude/claude_config.json:12:dope_context",
      "doc_id": "doc:.claude/claude_config.json",
      "path": ".claude/claude_config.json",
      "line_range": [12, 18],
      "heading_path": "mcpServers",
      "ref_type": "mcp_server",
      "ref_name": "dope_context",
      "context_excerpt": "\"dope_context\": {\n  \"command\": \"uv\",\n  \"args\": [\"--directory\", \"/path/to/mcp-servers/dope-context\", \"run\", \"dope-context\"]\n}"
    }
  ]
}
```

### LLM_SERVER_CALL_SURFACE.json

```json
{
  "artifact_type": "LLM_SERVER_CALL_SURFACE",
  "generated_at_utc": "2026-02-15T21:15:00Z",
  "source_artifact": "WORKING_TREE",
  "input_files": ["LLM_INSTRUCTION_INDEX.json"],
  "calls": [
    {
      "call_id": "call:doc:.claude/PRIMER.md:67",
      "doc_id": "doc:.claude/PRIMER.md",
      "path": ".claude/PRIMER.md",
      "line_range": [67, 70],
      "heading_path": "Memory Workflow",
      "call_pattern": "use_server",
      "target_name": "dope_context",
      "block_excerpt": "Use dope_context to:\n- Query event history\n- Retrieve patterns\n- Build context"
    }
  ]
}
```

---

## BEGIN EXTRACTION

Read `LLM_INSTRUCTION_INDEX.json` and produce the two JSON outputs now.
