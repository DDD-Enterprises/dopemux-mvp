---
id: PROMPT_I1_INSTRUCTION_INDEX
title: Prompt I1 Instruction Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt I1 Instruction Index (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt I1 (v2): LLM Instruction Plane Index

**Outputs:** `LLM_INSTRUCTION_INDEX.json`

---

## TASK

Produce ONE JSON file: `LLM_INSTRUCTION_INDEX.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE - Control plane instruction files only.

## SCOPE (Instruction/Control Plane Files)

Include files matching these patterns:

### Repo Root Control Plane
- `.claude/**`
- `.dopemux/**`
- `.taskx/**` 
- `.githooks/**`
- `AGENTS.md`
- `mcp-proxy-config*`
- `start-mcp-servers.sh`
- `compose.yml`, `compose/**`, `docker-compose*.yml`

### Docs Instruction Files
- `docs/**/custom-instructions/**`
- `docs/llm/**`
- `docs/prompts/**`
- Any file matching: `*prompt*`, `*primer*`, `*router*`, `*operator*`, `*instruction*`

## LLM_INSTRUCTION_INDEX.json

For each instruction file:
- `doc_id`: `"doc:" + path`
- `path`: repo-relative path
- `size_bytes`: file size
- `line_count_estimate`: line count if available
- `file_role_hint`: based on filename tokens only
  - `instruction` (has prompt/primer/instruction in name)
  - `config` (json/yaml/toml config)
  - `compose` (docker compose)
  - `script` (shell/python script)
  - `other`
- `is_control_plane`: `true`
- `title`: first H1 if markdown, else basename
- `headings`: H1-H3 with line ranges (cap 60 headings)
- `markers_found`: list of literal keywords found
  - Scan for: `TOOLS`, `MCP`, `SERVER`, `ROUTER`, `AUTHORITY`, `BOUNDARY`, `REFUSAL`, `GATE`, `DETERMINISM`, `AUDIT`


**Example:**
```json
{
  "doc_id": "doc:.claude/PRIMER.md",
  "path": ".claude/PRIMER.md",
  "size_bytes": 7200,
  "line_count_estimate": 180,
  "file_role_hint": "instruction",
  "is_control_plane": true,
  "title": "Dopemux Agent Primer",
  "headings": [
    {"level": 1, "text": "Dopemux Agent Primer", "line_range": [1, 1]},
    {"level": 2, "text": "MCP Tools", "line_range": [15, 15]}
  ],
  "markers_found": ["MCP", "TOOLS", "AUTHORITY"]
}
```

## Per-Marker Items

Additionally, when a marker appears in a normative sentence (contains MUST/SHOULD/REQUIRED), emit separate items:
- `domain=doc_claim` or `domain=doc_boundary`
- `kind=doc_claim` or `kind=doc_boundary`
- `marker`: which keyword triggered
- `original_quote`: exact sentence (cap 200 characters)
- `path`, `line_range`, `heading_path`

## RULES

- **No summarization** - exact text only
- **Scan first 200 lines only** for markers (not full file)
- **JSON only**, ASCII only
- **Deterministic sorting** by path

## OUTPUT FORMAT

```json
{
  "artifact_type": "LLM_INSTRUCTION_INDEX",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "instruction_files": [...],
  "marker_claims": [...]
}
```
