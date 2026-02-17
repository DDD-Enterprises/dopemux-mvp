---
id: PROMPT_M1_MERGE_NORMALIZE
title: Prompt M1 Merge Normalize
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt M1 Merge Normalize (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt M1 (v2): Merge & Normalize

**Outputs:** Merged `DOC_INDEX.json`, `DOC_CLAIMS.json`, `DOC_BOUNDARIES.json`, `DOC_SUPERSESSION.json`, `DOC_INTERFACES.json`, `DOC_WORKFLOWS.json`, `DOC_DECISIONS.json`, `DOC_GLOSSARY.json`

---

## TASK

Merge all `.partNN.json` files into unified artifacts.

## INPUTS

From D1 (per partition):
- `DOC_INDEX.part*.json`
- `DOC_CLAIMS.part*.json`
- `DOC_BOUNDARIES.part*.json`
- `DOC_SUPERSESSION.part*.json`

From D2 (per partition with CAP_NOTICES):
- `DOC_INTERFACES.part*.json`
- `DOC_WORKFLOWS.part*.json`
- `DOC_DECISIONS.part*.json`
- `DOC_GLOSSARY.part*.json`

## MERGE RULES

### 1. Append-Only Union
- Collect all items from all partNN.json files
- No filtering, no selection

### 2. Deduplication
Deduplicate by composite key:
- For INDEX: `(doc_id)`
- For CLAIMS: `(doc_id, line_range, normalized_text)`
- For BOUNDARIES: `(doc_id, line_range, original_quote)`
- For SUPERSESSION: `(doc_id, line_range, relation, subject)`
- For INTERFACES: `(doc_id, line_range, block_text_hash)`
- For WORKFLOWS: `(doc_id, line_range, workflow_name)`
- For DECISIONS: `(doc_id, line_range, decision_snippet)`
- For GLOSSARY: `(doc_id, term)`

**Collision resolution:** Keep first occurrence by partition_id order.

### 3. Deterministic Sorting
Sort all items by:
1. `doc_id` (lexicographic)
2. `line_range[0]` (numeric)
3. `id` field (lexicographic)

### 4. Metadata
Include in merged outputs:
```json
{
  "artifact_type": "DOC_CLAIMS",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "source_artifact": "WORKING_TREE",
  "merge_metadata": {
    "partition_count": 8,
    "source_files": ["DOC_CLAIMS.part001.json", "..."],
    "total_items_before_dedup": 1234,
    "total_items_after_dedup": 1200,
    "duplicates_removed": 34
  },
  "items": [...]
}
```

## OUTPUT FILES

1. `DOC_INDEX.json` - All docs indexed
2. `DOC_CLAIMS.json` - All normative claims
3. `DOC_BOUNDARIES.json` - All boundary statements
4. `DOC_SUPERSESSION.json` - All deprecation/version markers
5. `DOC_INTERFACES.json` - All code blocks/schemas
6. `DOC_WORKFLOWS.json` - All workflow step sequences
7. `DOC_DECISIONS.json` - All ADR-style decisions
8. `DOC_GLOSSARY.json` - All term definitions

## RULES

- **No arbitration** - all items pass through
- **No judgment** - keep duplicates with different line_range
- **Stable sorting** - deterministic output
- **JSON only**, ASCII only

## OPTIONAL: GLOBAL_MERGE_INDEX.json

Create a unified index showing which partitions contributed to each artifact:
```json
{
  "artifact": "DOC_CLAIMS.json",
  "partitions_merged": ["P001", "P002", "..."],
  "item_count": 1200,
  "duplicates_removed": 34
}
```
