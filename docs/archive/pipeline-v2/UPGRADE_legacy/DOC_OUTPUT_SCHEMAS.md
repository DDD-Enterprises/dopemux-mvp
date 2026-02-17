---
id: DOC_OUTPUT_SCHEMAS
title: Doc Output Schemas
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Doc Output Schemas (explanation) for dopemux documentation and developer
  workflows.
---
# Documentation Output Schemas

All JSON outputs from the phased documentation extraction pipeline conform to these schemas.

---

## Universal Item Fields

Every extracted item includes:
- `doc_id`: `"doc:" + path`
- `path`: repo-relative path
- `line_range`: `[start_line, end_line]` (1-indexed, inclusive)
- `heading_path`: breadcrumb to containing section (e.g., `"Architecture > Memory Plane > Design"`)

---

## D0 Outputs

### DOC_INVENTORY.json
```json
{
  "artifact_type": "DOC_INVENTORY",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "docs": [
    {
      "doc_id": "doc:docs/architecture/MEMORY.md",
      "path": "docs/architecture/MEMORY.md",
      "size_bytes": 12345,
      "line_count_estimate": 320,
      "has_headings": true,
      "has_code_fences": true,
      "last_modified": "2026-02-01T10:30:00Z",
      "sha256": "abc123...",
      "title": "Memory Plane Architecture",
      "headings": [
        {"level": 1, "text": "Memory Plane Architecture", "line_range": [1, 1]},
        {"level": 2, "text": "Overview", "line_range": [3, 3]}
      ]
    }
  ]
}
```

### DOC_PARTITIONS.json
```json
{
  "artifact_type": "DOC_PARTITIONS",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "partitions": [
    {
      "partition_id": "P001",
      "doc_count": 25,
      "doc_ids": ["doc:...", "doc:..."],
      "doc_paths": ["docs/...", "docs/..."],
      "buckets": ["A", "C"],
      "scope_description": "Core architecture docs"
    }
  ]
}
```

### DOC_TODO_QUEUE.json
```json
{
  "artifact_type": "DOC_TODO_QUEUE",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "queue": [
    {
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "status": "pending",
      "partition_id": "P001",
      "buckets": ["A"]
    }
  ]
}
```

---

## D1 Outputs

### DOC_INDEX.partNN.json
```json
{
  "artifact_type": "DOC_INDEX",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "title": "...",
      "headings": [...],
      "dates": ["2026-02-01"],
      "status_markers": ["ACTIVE"],
      "anchor_quotes": [
        {"quote": "...", "line_range": [10, 10]}
      ]
    }
  ]
}
```

### DOC_CLAIMS.partNN.json
```json
{
  "artifact_type": "DOC_CLAIMS",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "claim_id": "claim:doc:docs/...:45",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [45, 47],
      "heading_path": "Architecture > Memory Plane",
      "claim_type": "MUST",
      "normalized_text": "the memory plane must persist all events",
      "original_quote": "The Memory Plane MUST persist all events to SQLite."
    }
  ]
}
```

### DOC_BOUNDARIES.partNN.json
```json
{
  "artifact_type": "DOC_BOUNDARIES",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "boundary_id": "boundary:doc:docs/...:78",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [78, 80],
      "heading_path": "Architecture > Boundaries",
      "boundary_type": "authority",
      "original_quote": "Chronicle is the authoritative source of truth for event history.",
      "actors": ["Chronicle", "Memory Plane"]
    }
  ]
}
```

### DOC_SUPERSESSION.partNN.json
```json
{
  "artifact_type": "DOC_SUPERSESSION",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "supersession_id": "supersession:doc:docs/...:12",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [12, 12],
      "heading_path": "Status",
      "relation": "supersedes",
      "subject": "Memory Plane v2",
      "object": "Memory Plane v1"
    }
  ]
}
```

### CAP_NOTICES.partNN.json
```json
{
  "artifact_type": "CAP_NOTICES",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "notices": [
    {
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "reason": "line_count:950",
      "recommended_pass": "D2",
      "next_action": "extract_code_blocks"
    }
  ]
}
```

---

## D2 Outputs

### DOC_INTERFACES.partNN.json
```json
{
  "artifact_type": "DOC_INTERFACES",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "interface_id": "interface:doc:docs/...:120",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [120, 145],
      "heading_path": "API Reference",
      "interface_type": "json_envelope",
      "language_hint": "json",
      "block_text": "{\n  \"event_id\": \"...\",\n  \"ts\": \"...\"\n}"
    }
  ]
}
```

### DOC_WORKFLOWS.partNN.json
```json
{
  "artifact_type": "DOC_WORKFLOWS",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "workflow_id": "workflow:doc:docs/...:67",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [67, 85],
      "heading_path": "Event Processing Workflow",
      "workflow_name": "Event Processing Workflow",
      "steps": [
        "Receive event from producer",
        "Validate schema",
        "Persist to Chronicle"
      ],
      "actors": ["Producer", "Chronicle"],
      "artifacts": ["event.json", "chronicle.db"]
    }
  ]
}
```

### DOC_DECISIONS.partNN.json
```json
{
  "artifact_type": "DOC_DECISIONS",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "decision_id": "decision:doc:docs/...:200",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [200, 212],
      "heading_path": "Architecture Decisions",
      "decision_snippet": "Decision: Use SQLite for Chronicle storage.\nRationale: Simplicity, determinism, no network dependencies."
    }
  ]
}
```

### DOC_GLOSSARY.partNN.json
```json
{
  "artifact_type": "DOC_GLOSSARY",
  "partition_id": "P001",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [
    {
      "term_id": "term:doc:docs/...:34",
      "doc_id": "doc:docs/...",
      "path": "docs/...",
      "line_range": [34, 36],
      "heading_path": "Glossary",
      "term": "Chronicle",
      "definition": "The append-only event store that serves as the authoritative source of truth."
    }
  ]
}
```

---

## D3 Output

### DOC_CITATION_GRAPH.json
```json
{
  "artifact_type": "DOC_CITATION_GRAPH",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "edges": [
    {
      "edge_id": "edge:docs/a.md:45:b.md",
      "from_doc": "docs/a.md",
      "to_target": "b.md",
      "context_quote": "see b.md for details",
      "line_range": [45, 45],
      "link_type": "see_reference"
    }
  ],
  "metrics": {
    "total_edges": 567,
    "total_docs": 903,
    "docs_with_outbound_refs": 234,
    "top_referenced_docs": [
      {"doc": "docs/...", "in_degree": 23}
    ]
  }
}
```

---

## M1 Outputs (Merged)

All merged files follow the same schema as their partNN counterparts, with added `merge_metadata`:

```json
{
  "artifact_type": "DOC_CLAIMS",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "merge_metadata": {
    "partition_count": 12,
    "source_files": ["DOC_CLAIMS.part001.json", "..."],
    "total_items_before_dedup": 1234,
    "total_items_after_dedup": 1200,
    "duplicates_removed": 34
  },
  "items": [...]
}
```

---

## QA Output

### DOC_COVERAGE_REPORT.json
```json
{
  "artifact_type": "DOC_COVERAGE_REPORT",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "coverage": {
    "doc_count_total": 903,
    "doc_count_indexed": 903,
    "doc_count_processed_d1": 903,
    "doc_count_processed_d2": 47,
    "doc_count_pending": 0,
    "docs_missing_from_index": []
  },
  "cap_notices": {
    "cap_notices_total": 47,
    "cap_notices_resolved": 47,
    "cap_notices_unresolved": 0,
    "unresolved_docs": []
  },
  "artifact_counts": {
    "DOC_INDEX": 903,
    "DOC_CLAIMS": 1234,
    "DOC_BOUNDARIES": 456,
    "DOC_SUPERSESSION": 89,
    "DOC_INTERFACES": 234,
    "DOC_WORKFLOWS": 123,
    "DOC_DECISIONS": 67,
    "DOC_GLOSSARY": 145
  },
  "per_doc_coverage": {
    "docs_with_zero_claims": [],
    "docs_with_zero_interfaces": [],
    "docs_with_any_extraction": 890,
    "docs_with_no_extraction": []
  },
  "citation_graph": {
    "total_edges": 567,
    "docs_with_outbound_refs": 234,
    "isolated_docs": 120
  },
  "quality_gates": {
    "gate_all_docs_indexed": true,
    "gate_no_pending_docs": true,
    "gate_no_unresolved_caps": true,
    "gate_claims_coverage_pct": 78.5,
    "gate_citation_graph_exists": true,
    "overall_pass": true
  }
}
```

---

## CL Output

### DOC_TOPIC_CLUSTERS.json
```json
{
  "artifact_type": "DOC_TOPIC_CLUSTERS",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "inputs": {
    "doc_index": "DOC_INDEX.json",
    "doc_claims": "DOC_CLAIMS.json",
    "doc_citation_graph": "DOC_CITATION_GRAPH.json"
  },
  "token_rules": {
    "lowercase": true,
    "min_len": 4,
    "stopwords": "builtin_small",
    "max_tokens_per_doc": 500
  },
  "similarity_threshold": 0.18,
  "clusters": [
    {
      "cluster_id": "c001",
      "doc_ids": ["doc:...", "doc:..."],
      "doc_paths": ["docs/...", "docs/..."],
      "top_tokens": [
        {"token": "memory", "df": 18},
        {"token": "sqlite", "df": 12}
      ],
      "anchor_docs": [
        {"doc_id": "doc:...", "path": "...", "score": 0.91}
      ],
      "citation_out_degree": 12,
      "citation_in_degree": 7
    }
  ],
  "unclustered": ["doc:..."],
  "qa": {
    "doc_count": 903,
    "cluster_count": 12,
    "avg_docs_per_cluster": 75.25,
    "max_docs_in_cluster": 120,
    "min_docs_in_cluster": 8
  }
}
```
