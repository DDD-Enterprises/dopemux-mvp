---
id: EXEC_I1_INSTRUCTION_INDEX
title: Exec I1 Instruction Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Exec I1 Instruction Index (explanation) for dopemux documentation and developer
  workflows.
---
# EXECUTABLE PROMPT: I1 - LLM Instruction Plane Index

---

## YOUR ROLE

You are a **mechanical extractor**. You follow instructions exactly. You do not reason, interpret, or decide. You output JSON only.

---

## TASK

Index all LLM instruction and control plane files in the dopemux-mvp repository.

Produce ONE JSON file: `LLM_INSTRUCTION_INDEX.json`

---

## TARGET

Working tree at: `/Users/hue/code/dopemux-mvp`

---

## SCOPE: Control Plane Files to Index

### Repo Root Control Plane
- `.claude/**/*.md`, `.claude/**/*.json`
- `.dopemux/**`
- `.taskx/**`
- `.githooks/**`
- `AGENTS.md` (repo root)
- `mcp-proxy-config*`
- `start-mcp-servers.sh`
- `compose.yml`, `compose/**`, `docker-compose*.yml`

### Docs Instruction Files
- `docs/**/custom-instructions/**`
- `docs/llm/**`
- `docs/prompts/**`
- Any file matching patterns: `*prompt*`, `*primer*`, `*router*`, `*operator*`, `*instruction*`

---

## OUTPUT: LLM_INSTRUCTION_INDEX.json

```json
{
  "artifact_type": "LLM_INSTRUCTION_INDEX",
  "generated_at_utc": "<ISO timestamp>",
  "source_artifact": "WORKING_TREE",
  "instruction_files": [
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
        {"level": 2, "text": "MCP Tools", "line_range": [15, 15]},
        {"level": 2, "text": "Authority Boundaries", "line_range": [42, 42]}
      ],
      "markers_found": ["MCP", "TOOLS", "AUTHORITY", "BOUNDARY"]
    }
  ],
  "marker_claims": [
    {
      "claim_id": "claim:doc:.claude/PRIMER.md:78",
      "doc_id": "doc:.claude/PRIMER.md",
      "path": ".claude/PRIMER.md",
      "line_range": [78, 80],
      "heading_path": "MCP Tools > Authority",
      "domain": "doc_boundary",
      "kind": "doc_boundary",
      "marker": "AUTHORITY",
      "original_quote": "MCP servers MUST be the authoritative source for their data domains.",
      "normalized_text": "mcp servers must be the authoritative source for their data domains"
    }
  ]
}
```

---

## EXTRACTION RULES

### For Each File

1. **doc_id**: `"doc:" + path` (repo-relative path)
2. **path**: repo-relative (e.g., `.claude/PRIMER.md`)
3. **size_bytes**: file size in bytes
4. **line_count_estimate**: number of lines (approximate)
5. **file_role_hint**: classify based on filename/extension:
   - `instruction` - has prompt/primer/instruction in name
   - `config` - .json/.yaml/.toml config file
   - `compose` - docker-compose or compose file
   - `script` - .sh/.py/.js script
   - `other` - doesn't match above
6. **is_control_plane**: always `true` for this pass
7. **title**: 
   - For markdown: first H1 text
   - Otherwise: basename without extension
8. **headings**: H1-H3 headings with line ranges
   - Cap at 60 headings per file
   - Format: `{"level": 1, "text": "...", "line_range": [n, n]}`
9. **markers_found**: List of keywords found in file (scan first 200 lines only)
   - Keywords: `TOOLS`, `MCP`, `SERVER`, `ROUTER`, `AUTHORITY`, `BOUNDARY`, `REFUSAL`, `GATE`, `DETERMINISM`, `AUDIT`
   - Only include if keyword appears (case-insensitive match)

### Marker Claims (separate array)

When a marker keyword appears in a **normative sentence** (contains MUST/SHOULD/REQUIRED/SHALL):

1. **claim_id**: `"claim:" + doc_id + ":" + line_range[0]`
2. **domain**: `doc_claim` or `doc_boundary`
   - Use `doc_boundary` if sentence mentions: authority, ownership, responsibility, source of truth
   - Otherwise use `doc_claim`
3. **kind**: same as domain
4. **marker**: which keyword triggered extraction
5. **original_quote**: exact sentence (cap 200 chars)
6. **normalized_text**: lowercase, collapse whitespace

---

## HARD RULES

1. **No summarization** - extract exact text only
2. **No interpretation** - don't decide what things mean
3. **JSON only** - no markdown, no prose
4. **ASCII only** - no emoji, no special unicode
5. **Deterministic sorting** - sort files by path (alphabetical)
6. **Scan limit** - only scan first 200 lines per file for markers (performance)

---

## EXAMPLE OUTPUT STRUCTURE

```json
{
  "artifact_type": "LLM_INSTRUCTION_INDEX",
  "generated_at_utc": "2026-02-15T21:13:00Z",
  "source_artifact": "WORKING_TREE",
  "instruction_files": [
    {
      "doc_id": "doc:.claude/AGENT_ARCHITECTURE.md",
      "path": ".claude/AGENT_ARCHITECTURE.md",
      "size_bytes": 21000,
      "line_count_estimate": 450,
      "file_role_hint": "instruction",
      "is_control_plane": true,
      "title": "Agent Architecture",
      "headings": [
        {"level": 1, "text": "Agent Architecture", "line_range": [1, 1]},
        {"level": 2, "text": "Trinity Design", "line_range": [12, 12]}
      ],
      "markers_found": ["MCP", "AUTHORITY", "BOUNDARY"]
    },
    {
      "doc_id": "doc:.claude/claude_config.json",
      "path": ".claude/claude_config.json",
      "size_bytes": 3500,
      "line_count_estimate": 98,
      "file_role_hint": "config",
      "is_control_plane": true,
      "title": "claude_config",
      "headings": [],
      "markers_found": ["MCP", "SERVER"]
    }
  ],
  "marker_claims": [
    {
      "claim_id": "claim:doc:.claude/AGENT_ARCHITECTURE.md:45",
      "doc_id": "doc:.claude/AGENT_ARCHITECTURE.md",
      "path": ".claude/AGENT_ARCHITECTURE.md",
      "line_range": [45, 45],
      "heading_path": "Trinity Design > Authority",
      "domain": "doc_boundary",
      "kind": "doc_boundary",
      "marker": "AUTHORITY",
      "original_quote": "Chronicle is the authoritative source of truth for all events.",
      "normalized_text": "chronicle is the authoritative source of truth for all events"
    }
  ]
}
```

---

## BEGIN EXTRACTION

Scan the target directory and produce the JSON output now.
