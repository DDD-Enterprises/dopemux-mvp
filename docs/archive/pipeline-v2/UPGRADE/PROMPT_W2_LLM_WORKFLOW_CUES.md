---
id: PROMPT_W2_LLM_WORKFLOW_CUES
title: Prompt W2 Llm Workflow Cues
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Prompt W2 Llm Workflow Cues (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt W2 (v2): LLM Workflow Cues

**Outputs:** `WORKFLOW_SURFACE_LLM.json`

---

## TASK

Produce ONE JSON file: `WORKFLOW_SURFACE_LLM.json`.

## INPUTS

- `LLM_INSTRUCTION_INDEX.json` from I1
- `LLM_TOOLING_REFERENCES.json` from I2
- `LLM_SERVER_CALL_SURFACE.json` from I2

## SCOPE

**Only files listed in LLM_INSTRUCTION_INDEX.json**

## WORKFLOW_SURFACE_LLM.json

Extract step sequences from instruction files where patterns match:

### Numbered/Bulleted Lists with Action Verbs
- Lists with verbs: `run`, `start`, `call`, `route`, `write`, `store`, `emit`, `redact`, `promote`, `rank`, `invoke`, `use`, `load`, `check`
- Under workflow-ish headings: `workflow`, `pipeline`, `process`, `procedure`, `steps`, `how to`

### Command Blocks
- Bash command blocks: ` ```bash ... ``` `
- Shell examples starting with `$` or prompt
- Python command examples

For each workflow:
- `workflow_id`: `"workflow_llm:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `domain=doc_workflow`
- `kind=doc_workflow`
- `workflow_name`: from heading or first verb phrase
- `steps`: array of exact step strings (cap 30 steps)
- `actors`: literal service/plane/tool names if mentioned (e.g., "Chronicle", "MCP server", "TaskX")
- `artifacts`: literal filenames or data artifacts if mentioned

**Example:**
```json
{
  "workflow_id": "workflow_llm:doc:.claude/PRIMER.md:120",
  "doc_id": "doc:.claude/PRIMER.md",
  "path": ".claude/PRIMER.md",
  "line_range": [120, 145],
  "heading_path": "Memory Workflow",
  "domain": "doc_workflow",
  "kind": "doc_workflow",
  "workflow_name": "Memory Workflow",
  "steps": [
    "Receive event from producer",
    "Call dope_context MCP tool",
    "Store in Chronicle",
    "Update memory index"
  ],
  "actors": ["dope_context", "Chronicle"],
  "artifacts": ["chronicle.db", "memory_index"]
}
```

## RULES

- **Exact text only** - no paraphrasing
- **Max 30 steps per workflow**
- **JSON only**, ASCII only
- **Deterministic sorting** by (doc_id, line_range[0])

## OUTPUT FORMAT

```json
{
  "artifact_type": "WORKFLOW_SURFACE_LLM",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "workflows": [...]
}
```
