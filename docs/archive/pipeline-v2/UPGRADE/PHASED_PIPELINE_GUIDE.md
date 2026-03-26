---
id: PHASED_PIPELINE_GUIDE
title: Phased Pipeline Guide
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Phased Pipeline Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Phased Documentation Extraction Pipeline Guide

**Run this pipeline to extract all documentation with zero silent loss.**

---

## Pipeline Overview

```
D0 (Index) → D1 (Normative) → D2 (Deep) → D3 (Citation) → M1 (Merge) → QA (Coverage) → CL (Clustering)
```

### 7 Phases

1. **D0** - Inventory & Partition (1 run)
2. **D1** - Normative Extraction (17 runs, one per partition)
3. **D2** - Deep Extraction (runs only where CAP_NOTICES exist)
4. **D3** - Citation Graph (1 run)
5. **M1** - Merge & Normalize (1 run)
6. **QA** - Coverage Report (1 run)
7. **CL** - Topic Clustering (1 run)

---

## Phase D0: Index & Partition

**Run once:**
```bash
flash run PROMPT_D0_INDEX_PARTITION.md \
  --output-dir ./extraction/d0/
```

**Outputs:**
- `DOC_INVENTORY.json` - All docs indexed with metadata
- `DOC_PARTITIONS.json` - 17 partitions defined
- `DOC_TODO_QUEUE.json` - Processing queue

**Validation:**
- Verify `doc_count_total` matches expected (~903 in docs/)
- Check partition balance (should be ~20-35 docs per partition, except archives)

---

## Phase D1: Normative Extraction

**Run per partition (17 times):**

See `DOC_PARTITION_PLAN.md` for recommended execution order.

```bash
# Core architecture first (high priority)
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P003 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P007 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P008 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P002 --output-dir ./extraction/d1/

# Then systems & implementation
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P004 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P005 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P010 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P-SERVICES --output-dir ./extraction/d1/

# Audit & research
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P006 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P001 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P009 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P011 --output-dir ./extraction/d1/

# Archive (optional - see DOC_PARTITION_PLAN.md for strategy)
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P-ARCHIVE-001 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P-ARCHIVE-002 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P-ARCHIVE-003 --output-dir ./extraction/d1/
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P-ARCHIVE-004 --output-dir ./extraction/d1/

# Quarantine (defer or skip entirely)
# flash run PROMPT_D1_NORMATIVE_EXTRACTION.md --var PARTITION_ID=P-QUARANTINE --output-dir ./extraction/d1/
```

**Outputs per partition:**
- `DOC_INDEX.partNN.json`
- `DOC_CLAIMS.partNN.json`
- `DOC_BOUNDARIES.partNN.json`
- `DOC_SUPERSESSION.partNN.json`
- `CAP_NOTICES.partNN.json`

**Validation:**
- Check that each partition produced 5 output files
- Collect all `CAP_NOTICES.part*.json` for D2

---

## Phase D2: Deep Extraction

**Run only for partitions with CAP_NOTICES:**

```bash
# First, merge all CAP_NOTICES to see which partitions need D2
cat ./extraction/d1/CAP_NOTICES.part*.json | jq '.items[].partition_id' | sort -u

# Then run D2 for each
flash run PROMPT_D2_DEEP_EXTRACTION.md --var PARTITION_ID=P003 --output-dir ./extraction/d2/
flash run PROMPT_D2_DEEP_EXTRACTION.md --var PARTITION_ID=P005 --output-dir ./extraction/d2/
# ... (repeat for all partitions with CAP_NOTICES)
```

**Outputs per partition:**
- `DOC_INTERFACES.partNN.json`
- `DOC_WORKFLOWS.partNN.json`
- `DOC_DECISIONS.partNN.json`
- `DOC_GLOSSARY.partNN.json`

**Expected:** ~6-10 partitions will have CAP_NOTICES requiring D2.

---

## Phase D3: Citation Graph

**Run once:**
```bash
flash run PROMPT_D3_CITATION_GRAPH.md \
  --output-dir ./extraction/d3/
```

**Outputs:**
- `DOC_CITATION_GRAPH.json`

**Validation:**
- Check `total_edges > 100` (non-trivial graph)
- Review `top_referenced_docs` for sanity

---

## Phase M1: Merge & Normalize

**Run once:**
```bash
flash run PROMPT_M1_MERGE_NORMALIZE.md \
  --input-dir ./extraction/d1/ \
  --input-dir ./extraction/d2/ \
  --output-dir ./extraction/merged/
```

**Outputs:**
- `DOC_INDEX.json`
- `DOC_CLAIMS.json`
- `DOC_BOUNDARIES.json`
- `DOC_SUPERSESSION.json`
- `DOC_INTERFACES.json`
- `DOC_WORKFLOWS.json`
- `DOC_DECISIONS.json`
- `DOC_GLOSSARY.json`

**Validation:**
- Check `merge_metadata.duplicates_removed` is reasonable
- Verify `total_items_after_dedup` counts make sense

---

## Phase QA: Coverage Report

**Run once:**
```bash
flash run PROMPT_QA_COVERAGE_REPORT.md \
  --input ./extraction/d0/DOC_INVENTORY.json \
  --input ./extraction/d0/DOC_TODO_QUEUE.json \
  --input ./extraction/merged/*.json \
  --input ./extraction/d3/DOC_CITATION_GRAPH.json \
  --output-dir ./extraction/qa/
```

**Outputs:**
- `DOC_COVERAGE_REPORT.json`

**Quality Gates:**
- ✅ `gate_all_docs_indexed: true`
- ✅ `gate_no_pending_docs: true`
- ✅ `gate_no_unresolved_caps: true`
- ✅ `gate_claims_coverage_pct > 50`
- ✅ `gate_citation_graph_exists: true`
- ✅ `overall_pass: true`

**If any gate fails:**
1. Check `docs_missing_from_index` and investigate
2. Check `unresolved_docs` and run D2 on them
3. Check `docs_with_no_extraction` and verify they're truly empty/irrelevant

---

## Phase CL: Topic Clustering

**Run once:**
```bash
flash run PROMPT_CL_TOPIC_CLUSTERS.md \
  --input ./extraction/merged/*.json \
  --output-dir ./extraction/clusters/
```

**Outputs:**
- `DOC_TOPIC_CLUSTERS.json`

**Validation:**
- Check `cluster_count` (expect 8-15 clusters)
- Review `top_tokens` for each cluster (should be coherent)
- Check `unclustered` count (should be small, <50)

---

## Final Output Directory Structure

```
extraction/
├── d0/
│   ├── DOC_INVENTORY.json
│   ├── DOC_PARTITIONS.json
│   └── DOC_TODO_QUEUE.json
├── d1/
│   ├── DOC_INDEX.part001.json
│   ├── DOC_CLAIMS.part001.json
│   ├── ... (5 files × 17 partitions = 85 files)
│   └── CAP_NOTICES.part017.json
├── d2/
│   ├── DOC_INTERFACES.part003.json
│   ├── ... (4 files × ~8 partitions = 32 files)
│   └── DOC_GLOSSARY.part010.json
├── d3/
│   └── DOC_CITATION_GRAPH.json
├── merged/
│   ├── DOC_INDEX.json
│   ├── DOC_CLAIMS.json
│   ├── ... (8 merged artifacts)
│   └── DOC_GLOSSARY.json
├── qa/
│   └── DOC_COVERAGE_REPORT.json
└── clusters/
    └── DOC_TOPIC_CLUSTERS.json
```

**Total artifacts:** ~120 intermediate + 11 final

---

## Estimated Execution Time

| Phase | Runs | Est. Time per Run | Total   |
| ----- | ---- | ----------------- | ------- |
| D0    | 1    | 5 min             | 5 min   |
| D1    | 17   | 3-8 min           | ~90 min |
| D2    | ~8   | 5-10 min          | ~60 min |
| D3    | 1    | 10 min            | 10 min  |
| M1    | 1    | 5 min             | 5 min   |
| QA    | 1    | 3 min             | 3 min   |
| CL    | 1    | 8 min             | 8 min   |

**Total:** ~3 hours (can parallelize D1 partitions for 45 min total)

---

## Next Steps After Extraction

1. **Normalize** (if needed): Run additional normalization prompts (N1-N4)
2. **Arbitration**: Hand merged artifacts to GPT-5.2 for conflict resolution
3. **Synthesis**: Hand to Opus for high-level boundary map creation
