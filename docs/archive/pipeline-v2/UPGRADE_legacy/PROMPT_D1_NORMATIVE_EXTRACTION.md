---
id: PROMPT_D1_NORMATIVE_EXTRACTION
title: Prompt D1 Normative Extraction
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Prompt D1 Normative Extraction (explanation) for dopemux documentation and
  developer workflows.
---
# Prompt D1 (v2): Normative Extraction (Per Partition)

**Outputs:** `DOC_INDEX.partNN.json`, `DOC_CLAIMS.partNN.json`, `DOC_BOUNDARIES.partNN.json`, `DOC_SUPERSESSION.partNN.json`, `CAP_NOTICES.partNN.json`

---

## TASK

Produce FIVE JSON files per partition.

## INPUT

- `DOC_PARTITIONS.json` from D0
- **Partition ID**: `<PARTITION_ID>` (e.g., "P001", "P002", etc.)

## SCOPE

**Only process docs listed in the specified partition_id.**

Ignore all other docs.

## 1) DOC_INDEX.partNN.json

For each doc in partition:
- `doc_id`: `"doc:" + path`
- `path`: repo-relative path
- `title`: first H1 (exact text)
- `headings`: H1-H3 with line ranges
- `dates`: any date strings found (exact)
- `status_markers`: ACTIVE|DEPRECATED|DRAFT|SUPERSEDED if literal keywords present
- `anchor_quotes`: 5 representative quotes (≤12 words each) with line ranges

## 2) DOC_CLAIMS.partNN.json

Extract atomic sentences containing **any** of:
- `MUST`, `MUST NOT`, `SHOULD`, `REQUIRED`, `INVARIANT`, `DEFAULT`, `DETERMINISTIC`, `FAIL-CLOSED`, `APPEND-ONLY`, `SINGLE SOURCE OF TRUTH`

For each claim:
- `claim_id`: `"claim:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `claim_type`: literal keyword matched (e.g., "MUST", "INVARIANT")
- `normalized_text`: lowercase, collapse whitespace only
- `original_quote`: exact quote (cap 200 characters)

## 3) DOC_BOUNDARIES.partNN.json

Extract explicit authority/boundary statements with patterns:
- `authoritative`, `source of truth`, `only X may`, `must not`, `forbidden`, `responsible for`, `owns`, `boundary`

For each boundary:
- `boundary_id`: `"boundary:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `boundary_type`: `authority|forbidden|ownership|responsibility|interface`
- `original_quote`: exact quote (cap 200 characters)
- `actors`: literal service/plane/tool names if present (as list)

## 4) DOC_SUPERSESSION.partNN.json

Extract version/deprecation markers:
- `supersedes`, `deprecated`, `replaces`, version chains (`v0`/`v1`/`v2`), `status:`

For each:
- `supersession_id`: `"supersession:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `relation`: `supersedes|deprecated|replaces|version|status`
- `subject`: exact phrase
- `object`: exact phrase if present

## 5) CAP_NOTICES.partNN.json

**CAP RULE:**

If a doc meets **any** of these criteria:
- `line_count_estimate > 800`
- `code fences > 12`
- `headings > 80`
- Extract length would exceed reasonable limits

**Do NOT attempt deep parse**. Instead, emit a cap_notice:

```json
{
  "doc_id": "doc:...",
  "path": "...",
  "reason": "line_count:950",
  "recommended_pass": "D2",
  "next_action": "extract_code_blocks|extract_workflows|extract_decisions"
}
```

## RULES

- **No inference about behavior**
- **No forbidden words**: "means", "likely", "should" (unless literal quote), "correct", "wrong", "best", "problem", "bug"
- **Deterministic sorting**: by (doc_id, line_range[0])
- **JSON only**, ASCII only
- **Exact quotes only** - no paraphrasing

## OUTPUT FORMAT

All five JSON files follow this structure:
```json
{
  "artifact_type": "DOC_CLAIMS",
  "partition_id": "P001",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```
