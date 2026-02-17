---
id: PROMPT_D0_INDEX_PARTITION
title: Prompt D0 Index Partition
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt D0 Index Partition (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt D0 (v2): Index & Partition

**Outputs:** `DOC_INVENTORY.json`, `DOC_PARTITIONS.json`, `DOC_TODO_QUEUE.json`

---

## TASK

Produce THREE JSON files: `DOC_INVENTORY.json`, `DOC_PARTITIONS.json`, `DOC_TODO_QUEUE.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` - All documentation sources:
- `docs/**/*.md`
- `.claude/docs/**/*.md`
- `services/*/docs/**/*.md`
- `docker/mcp-servers/docs/**/*.md`
- `_audit_out/**/*.md`
- `quarantine/2026-02-04/**/*.md`
- `scripts/docs_audit/**/*.md`

**Exclude:**
- `node_modules/**`
- `.venv/**`, `.taskx_venv/**`
- `.git/**`
- `SYSTEM_ARCHIVE/**`

## DOC_INVENTORY.json

For each doc file, extract:
- `doc_id`: `"doc:" + path` (exact path string)
- `path`: repo-relative path
- `size_bytes`: file size
- `line_count_estimate`: line count (if available)
- `has_headings`: true/false (presence of `#` lines)
- `has_code_fences`: true/false (presence of ` ``` ` blocks)
- `last_modified`: timestamp if available
- `sha256`: file hash if available
- `title`: first H1 heading if present (exact text)
- `headings`: list of H1-H3 headings with line ranges (cap 60 headings)

**Example:**
```json
{
  "doc_id": "doc:docs/architecture/MEMORY_PLANE.md",
  "path": "docs/architecture/MEMORY_PLANE.md",
  "size_bytes": 12543,
  "line_count_estimate": 320,
  "has_headings": true,
  "has_code_fences": true,
  "title": "Memory Plane Architecture",
  "headings": [
    {"level": 1, "text": "Memory Plane Architecture", "line_range": [1, 1]},
    {"level": 2, "text": "Overview", "line_range": [3, 3]}
  ]
}
```

## DOC_PARTITIONS.json

Create partitions of **≤25 docs each**, sorted by path.

Additionally create 6 **priority buckets** based on token presence in headings/title:
- **Bucket A** tokens: `memory`, `chronicle`, `sqlite`, `postgres`, `mirror`
- **Bucket B** tokens: `event`, `taxonomy`, `envelope`, `bus`, `producer`, `consumer`
- **Bucket C** tokens: `trinity`, `boundary`, `authority`, `plane`
- **Bucket D** tokens: `taskx`, `orchestrator`, `packet`, `router`
- **Bucket E** tokens: `mcp`, `tool`, `server`, `contract`
- **Bucket F** tokens: `ranking`, `retrieval`, `redaction`, `promotion`

Bucket membership is literal case-insensitive token match in title or headings.

**Example:**
```json
{
  "partition_id": "P001",
  "doc_count": 25,
  "doc_ids": ["doc:...", "doc:..."],
  "buckets": ["A", "C"],
  "scope_description": "Core architecture docs (docs/architecture/, docs/90-adr/)"
}
```

## DOC_TODO_QUEUE.json

List all docs with processing status:
```json
{
  "doc_id": "doc:docs/...",
  "path": "docs/...",
  "status": "pending",
  "partition_id": "P001",
  "buckets": ["A"]
}
```

## RULES

- **Do NOT read full doc content in D0** - only parse for headings and metadata
- **JSON only**, ASCII only
- **Deterministic sorting** by path
- **Partition balance**: aim for 20-25 docs per partition
- If `docs/archive/` has >200 files, create sub-partitions (P-ARCHIVE-001, P-ARCHIVE-002, etc.)

## ID RULE

```
doc_id = "doc:" + path
partition_id = "P" + zero-padded-number (P001, P002, ...)
```

## OUTPUT FORMAT

All three JSON files must follow this structure:
- Top-level object with metadata
- `generated_at_utc`: timestamp
- `source_artifact`: "WORKING_TREE"
- Deterministic ordering
