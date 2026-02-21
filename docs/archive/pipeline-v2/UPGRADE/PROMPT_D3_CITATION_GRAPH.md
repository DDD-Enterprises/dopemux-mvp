---
id: PROMPT_D3_CITATION_GRAPH
title: Prompt D3 Citation Graph
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt D3 Citation Graph (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt D3 (v2): Citation Graph Extraction

**Outputs:** `DOC_CITATION_GRAPH.json`

---

## TASK

Produce ONE JSON file: `DOC_CITATION_GRAPH.json`.

## TARGET

All docs in `/Users/hue/code/dopemux-mvp` documentation corpus.

## SCOPE

Extract cross-references between docs to build authority chains.

## DOC_CITATION_GRAPH.json

Extract all cross-document references:
- Explicit filenames mentioned in text
- `see <...>` patterns
- Markdown links: `[text](target)`
- `as defined in <...>`
- `per <doc>`, `ref:`, `→` arrows

For each reference:
- `edge_id`: `"edge:" + from_doc + ":" + line_range[0] + ":" + to_target`
- `from_doc`: source doc path
- `to_target`: exact string (do NOT resolve paths)
- `context_quote`: surrounding text (≤12 words)
- `line_range`: where reference appears
- `link_type`: `filename|see_reference|markdown_link|defined_in|other`

**Example:**
```json
{
  "edge_id": "edge:docs/architecture/MEMORY.md:45:CHRONICLE_SPEC.md",
  "from_doc": "docs/architecture/MEMORY.md",
  "to_target": "CHRONICLE_SPEC.md",
  "context_quote": "see CHRONICLE_SPEC.md for details",
  "line_range": [45, 45],
  "link_type": "see_reference"
}
```

## RULES

- **Do NOT resolve targets** (keep exact strings as written)
- **Extract all references**, even if target doesn't exist
- **Deterministic sorting**: by (from_doc, line_range[0], to_target)
- **JSON only**, ASCII only

## OUTPUT FORMAT

```json
{
  "artifact_type": "DOC_CITATION_GRAPH",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "source_artifact": "WORKING_TREE",
  "edges": [...]
}
```

## GRAPH METRICS (include in output)

Calculate and include:
- `total_edges`: count
- `total_docs`: unique doc count
- `docs_with_outbound_refs`: count
- `docs_with_inbound_refs`: count (requires 2-pass, optional)
- `top_referenced_docs`: top 10 by in-degree (doc path + count)
