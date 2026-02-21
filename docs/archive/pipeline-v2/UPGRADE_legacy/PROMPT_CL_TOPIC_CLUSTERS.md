---
id: PROMPT_CL_TOPIC_CLUSTERS
title: Prompt Cl Topic Clusters
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt Cl Topic Clusters (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt CL (v2): Topic Clustering

**Outputs:** `DOC_TOPIC_CLUSTERS.json`

---

## TASK

Produce ONE JSON file: `DOC_TOPIC_CLUSTERS.json`.

## INPUTS

All merged doc artifacts from M1:
- `DOC_INDEX.json`
- `DOC_CLAIMS.json`
- `DOC_WORKFLOWS.json`
- `DOC_BOUNDARIES.json`
- `DOC_INTERFACES.json`
- `DOC_DECISIONS.json`
- `DOC_CITATION_GRAPH.json`

## GOAL

Create mechanical topic clustering using token overlap so later models can:
- Quickly find "all docs about memory plane"
- Avoid re-reading 200+ files
- Navigate authority chains faster

**No semantic labeling required.** Just clusters + top tokens + member docs.

## TOKENIZATION RULES

For each doc, build a token multiset from these fields:
- `title`
- `headings` (H1-H3 text)
- `claim normalized_text`
- `workflow names` + step verbs
- `boundary original_quote` (first 50 words)
- `interface language_hint` (json, sql, python, yaml, mcp, etc.)
- `decision_snippet` (first 2 lines only)

**Token transform:**
1. Lowercase
2. Split on non-alphanumeric
3. Keep tokens length ≥ 4
4. Drop stopwords: `the, and, that, with, this, from, into, when, then, only, also, over, under, about, after, before, each, some, such, than, very, will, would, could, should`
5. Cap to top 500 tokens by frequency per doc (ties broken lexicographically)

**No stemming. No synonyms. No semantic mapping.**

## SIMILARITY CALCULATION

```
sim(A, B) = |tokensA ∩ tokensB| / |tokensA ∪ tokensB|
```

Jaccard overlap on token sets.

## CLUSTERING METHOD (Deterministic Greedy)

1. Sort docs by:
   - Citation in-degree (from DOC_CITATION_GRAPH) descending
   - Then by path lexicographically

2. For each unassigned doc:
   - Start new cluster with this doc as seed
   - Add any remaining doc with `sim ≥ 0.18`
   - After initial adds, do one additional pass

3. Clusters of size 1:
   - Go to `unclustered` unless `sim ≥ 0.25` to any existing cluster

## CLUSTER OUTPUT

For each cluster:
```json
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
```

**Fields:**
- `cluster_id`: `"c001"`, `"c002"`, ... (sequential by seed order)
- `doc_ids`, `doc_paths`: sorted lexicographically
- `top_tokens`: top 25 tokens by document frequency within cluster, include `df` counts
- `anchor_docs`: top 3 docs by average similarity to others in cluster (score 0..1)
- Citation degrees: sum of member docs

## OUTPUT FORMAT

```json
{
  "artifact_type": "DOC_TOPIC_CLUSTERS",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "inputs": {
    "doc_index": "DOC_INDEX.json",
    "doc_claims": "DOC_CLAIMS.json",
    "doc_workflows": "DOC_WORKFLOWS.json",
    "doc_boundaries": "DOC_BOUNDARIES.json",
    "doc_interfaces": "DOC_INTERFACES.json",
    "doc_decisions": "DOC_DECISIONS.json",
    "doc_citation_graph": "DOC_CITATION_GRAPH.json"
  },
  "token_rules": {
    "lowercase": true,
    "min_len": 4,
    "stopwords": "builtin_small",
    "max_tokens_per_doc": 500
  },
  "similarity_threshold": 0.18,
  "clusters": [...],
  "unclustered": ["doc:...", "..."],
  "qa": {
    "doc_count": 903,
    "cluster_count": 12,
    "avg_docs_per_cluster": 75.25,
    "max_docs_in_cluster": 120,
    "min_docs_in_cluster": 8
  }
}
```

## RULES

- **Do not label clusters** (no "Architecture" or "Memory" labels)
- **JSON only**, ASCII only
- **Deterministic ordering** everywhere
- **Stable clustering** (same inputs → same outputs)

## ID RULE

```
doc_id = "doc:" + path
cluster_id = "c" + zero-padded-number (c001, c002, ...)
```
