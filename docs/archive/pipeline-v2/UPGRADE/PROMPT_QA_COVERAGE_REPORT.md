---
id: PROMPT_QA_COVERAGE_REPORT
title: Prompt Qa Coverage Report
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt Qa Coverage Report (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt QA (v2): Coverage Report

**Outputs:** `DOC_COVERAGE_REPORT.json`

---

## TASK

Produce ONE JSON file: `DOC_COVERAGE_REPORT.json`.

## INPUTS

- `DOC_INVENTORY.json` (from D0)
- `DOC_TODO_QUEUE.json` (from D0)
- `CAP_NOTICES.part*.json` (from D1, all partitions)
- Merged artifacts from M1:
  - `DOC_INDEX.json`
  - `DOC_CLAIMS.json`
  - `DOC_BOUNDARIES.json`
  - `DOC_SUPERSESSION.json`
  - `DOC_INTERFACES.json`
  - `DOC_WORKFLOWS.json`
  - `DOC_DECISIONS.json`
  - `DOC_GLOSSARY.json`
- `DOC_CITATION_GRAPH.json` (from D3)

## DOC_COVERAGE_REPORT.json

Calculate and report:

### 1. Document Coverage
```json
{
  "doc_count_total": 903,
  "doc_count_indexed": 903,
  "doc_count_processed_d1": 903,
  "doc_count_processed_d2": 47,
  "doc_count_pending": 0,
  "docs_missing_from_index": []
}
```

### 2. CAP_NOTICES Analysis
```json
{
  "cap_notices_total": 47,
  "cap_notices_resolved": 47,
  "cap_notices_unresolved": 0,
  "unresolved_docs": []
}
```

### 3. Artifact Item Counts
```json
{
  "DOC_INDEX": 903,
  "DOC_CLAIMS": 1234,
  "DOC_BOUNDARIES": 456,
  "DOC_SUPERSESSION": 89,
  "DOC_INTERFACES": 234,
  "DOC_WORKFLOWS": 123,
  "DOC_DECISIONS": 67,
  "DOC_GLOSSARY": 145
}
```

### 4. Per-Doc Coverage
```json
{
  "docs_with_zero_claims": ["doc:...", "..."],
  "docs_with_zero_interfaces": ["doc:...", "..."],
  "docs_with_zero_workflows": ["doc:...", "..."],
  "docs_with_any_extraction": 890,
  "docs_with_no_extraction": ["doc:...", "..."]
}
```

### 5. Citation Graph Metrics
```json
{
  "total_edges": 567,
  "docs_with_outbound_refs": 234,
  "docs_with_inbound_refs": 189,
  "isolated_docs": 120,
  "top_referenced_docs": [
    {"doc": "docs/...", "in_degree": 23},
    ...
  ]
}
```

### 6. Quality Gates
```json
{
  "gate_all_docs_indexed": true,
  "gate_no_pending_docs": true,
  "gate_no_unresolved_caps": true,
  "gate_claims_coverage_pct": 78.5,
  "gate_interfaces_coverage_pct": 23.4,
  "gate_citation_graph_exists": true,
  "overall_pass": true
}
```

## PASS/FAIL CRITERIA

The report must answer:
- ✅ All docs from inventory are indexed
- ✅ No pending docs in todo queue
- ✅ All CAP_NOTICES have been resolved by D2
- ✅ Claims coverage > 50% (at least half of docs have claims)
- ✅ Citation graph is non-trivial (>100 edges)

If any criterion fails, set `overall_pass: false` and list failures.

## RULES

- **Mechanical calculation only** - no judgment
- **JSON only**, ASCII only
- **Deterministic ordering**

## OUTPUT FORMAT

```json
{
  "artifact_type": "DOC_COVERAGE_REPORT",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "source_artifact": "WORKING_TREE",
  "coverage": {...},
  "cap_notices": {...},
  "artifact_counts": {...},
  "per_doc_coverage": {...},
  "citation_graph": {...},
  "quality_gates": {...}
}
```
