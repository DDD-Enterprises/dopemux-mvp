---
id: PROMPT_D2_DEEP_EXTRACTION
title: Prompt D2 Deep Extraction
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt D2 Deep Extraction (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt D2 (v2): Deep Extraction (CAP_NOTICES Only)

**Outputs:** `DOC_INTERFACES.partNN.json`, `DOC_WORKFLOWS.partNN.json`, `DOC_DECISIONS.partNN.json`, `DOC_GLOSSARY.partNN.json`

---

## TASK

Produce FOUR JSON files for heavy docs requiring deep extraction.

## INPUT

- `CAP_NOTICES.partNN.json` from D1
- **Partition ID**: `<PARTITION_ID>`

## SCOPE

**Only process docs listed in CAP_NOTICES for this partition.**

Ignore all other docs.

## 1) DOC_INTERFACES.partNN.json

Extract code blocks and structured interface examples:
- Fenced code blocks: ` ``` ... ``` `
- JSON examples (objects/arrays)
- CLI usage blocks (lines starting with `$` or `dopemux`)
- SQL blocks (CREATE TABLE, INSERT, SELECT)

For each:
- `interface_id`: `"interface:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `interface_type`: `json_envelope|mcp_tool|cli|sql|pseudocode|other`
- `language_hint`: from fence if present (e.g., "python", "json")
- `block_text`: exact text (cap at 120 lines per block)

## 2) DOC_WORKFLOWS.partNN.json

Extract workflows and step sequences:
- Headings containing: `workflow`, `pipeline`, `flow`, `lifecycle`, `process`
- Numbered lists or bulleted step lists underneath

For each:
- `workflow_id`: `"workflow:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `workflow_name`: from heading (exact)
- `steps`: array of exact step strings
- `actors`: literal service/plane/tool names if present
- `artifacts`: literal filenames or data artifacts if present

## 3) DOC_DECISIONS.partNN.json

Extract decision records when patterns appear:
- `Decision:`, `We chose`, `Tradeoff`, `Rationale`, `Consequences`, `Alternatives`

For each:
- `decision_id`: `"decision:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `decision_snippet`: exact paragraph (cap 12 lines)

## 4) DOC_GLOSSARY.partNN.json

Extract term definitions:
- Pattern: `<TERM> is ...` or `Definition:` or `Glossary:` headings

For each:
- `term_id`: `"term:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `term`: exact term
- `definition`: exact definition text

## RULES

- **No inference, no summarization**
- **Exact extraction only**
- **Deterministic sorting**: by (doc_id, line_range[0])
- **JSON only**, ASCII only
- **Block caps**: 120 lines max per code block

## OUTPUT FORMAT

All four JSON files follow this structure:
```json
{
  "artifact_type": "DOC_INTERFACES",
  "partition_id": "P001",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```
