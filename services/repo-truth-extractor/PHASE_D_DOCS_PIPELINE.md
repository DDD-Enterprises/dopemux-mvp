# Phase D: Docs Pipeline Prompts (P0–P5)

This document contains the prompts for the Phase D documentation pipeline.

## D0: Inventory + Partition Plan

**Output files**
* `DOC_INVENTORY.json`
* `PARTITION_PLAN.json`

**ROLE**: Mechanical indexer. No reasoning. JSON only. ASCII only.

**TARGET ROOT**: dopemux-mvp repo working tree.

**SCOPE**:
- `docs/**/*.md`
- `docs/**/*.txt`

**OUTPUT 1: DOC_INVENTORY.json**
For each doc:
- `path`
- `size_bytes`
- `last_modified` (if available)
- `sha256` (if available)
- `line_count_estimate` (if available)
- `is_archive=true` if path starts with `docs/archive/` OR `docs/04-explanation/archive/`
- `is_evidence=true` if path contains `/_evidence/` OR `/_handoff/` OR `/_opus_inputs/`
- `title`: first H1 if present (scan first 120 lines only)
- `has_code_fences=true` if "```" appears (scan first 300 lines only)

**OUTPUT 2: PARTITION_PLAN.json**
Create deterministic partitions by folder groups:
```
P2_CORE_ARCH =
  docs/spec/** +
  docs/architecture/** +
  docs/90-adr/** +
  docs/91-rfc/** +
  docs/systems/**

P3_PLANES_ACTIVE =
  docs/planes/** excluding any "/_evidence/" "/_handoff/" "/_opus_inputs/"

P4_PLANES_EVIDENCE =
  docs/planes/**/_evidence/** +
  docs/planes/**/_handoff/** +
  docs/planes/**/_opus_inputs/**

P5_TASK_PACKETS_PM_INV =
  docs/task-packets/** +
  docs/pm/** +
  docs/investigations/**

P6_DIATAXIS =
  docs/01-tutorials/** +
  docs/02-how-to/** +
  docs/03-reference/** +
  docs/04-explanation/** excluding docs/04-explanation/archive/**

P7_MISC =
  docs/api/** +
  docs/projects/** +
  docs/best-practices/** +
  docs/troubleshooting/** +
  docs/05-audit-reports/** +
  docs/06-research/**

P8_ARCHIVE =
  docs/archive/** +
  docs/04-explanation/archive/**
```

**RULE**:
If any partition has > 30 docs, split into subpartitions of 20 docs each, named like `P2_CORE_ARCH__01`, `P2_CORE_ARCH__02`, etc.
Order docs within each partition by path ascending.

**RULES**:
- Do not read full docs here.
- JSON only.
- Deterministic ordering.

---

## D1: Claims + Boundaries + Supersession (run per partition chunk)

**Output files**
* `DOC_INDEX.<partition_id>.json`
* `DOC_CLAIMS.<partition_id>.json`
* `DOC_BOUNDARIES.<partition_id>.json`
* `DOC_SUPERSESSION.<partition_id>.json`
* `CAP_NOTICES.<partition_id>.json`

**ROLE**: Mechanical extractor. No reasoning. JSON only. ASCII only.

**INPUTS**:
- `DOC_INVENTORY.json`
- `PARTITION_PLAN.json`
**PARAM**: `partition_id = <ONE_PARTITION_CHUNK_ID>`

**SCOPE**:
Only docs listed in `PARTITION_PLAN[partition_id]`.

For each doc, extract:

**A) DOC_INDEX.<partition_id>.json**
- headings H1-H3 with line ranges (cap 120 headings per doc)
- `anchor_quotes`: 5 short quotes (<= 12 words) with line ranges, chosen deterministically:
  pick the first 5 non-empty lines that are not headings, skipping code fences

**B) DOC_CLAIMS.<partition_id>.json**
Extract atomic sentences containing any of these tokens (case-insensitive):
`MUST`, `MUST NOT`, `SHALL`, `REQUIRED`, `FORBIDDEN`, `INVARIANT`, `DEFAULT`, `DETERMINISTIC`,
`FAIL-CLOSED`, `APPEND-ONLY`, `SINGLE SOURCE OF TRUTH`, `AUTHORITY`, `TRINITY`,
`EVENTBUS`, `PRODUCER`, `CONSUMER`, `TASKX`, `MCP`, `HOOK`, `WORKFLOW`, `PIPELINE`

For each claim item:
- `path`, `line_range`, `heading_path`
- `original_quote` (exact sentence)
- `trigger_tokens[]` (which words matched)

**C) DOC_BOUNDARIES.<partition_id>.json**
Extract atomic sentences that define:
- ownership/responsibility separation
- module/service boundaries
- interface contracts between subsystems
Use same structure as claims, but kind="boundary".

**D) DOC_SUPERSESSION.<partition_id>.json**
Extract lines that indicate:
- "supersedes", "replaces", "deprecated", "obsolete", "archived", "active", "status",
  version numbers, dates in headings
Emit items with `path`, `line_range`, `excerpt` <= 2 lines.

**E) CAP_NOTICES.<partition_id>.json**
If doc `line_count_estimate` > 900 OR `size_bytes` > 250000 OR `has_code_fences=true`:
- emit `cap_notice` with `reason`, and `recommended_next="D2_DEEP"`

**RULES**:
- exact text only
- no summarization
- stable ordering by path then line_range
- JSON only

---

## D2: Deep extraction (interfaces + workflows + decisions) (run per partition chunk)

**Output files**
* `DOC_INTERFACES.<partition_id>.json`
* `DOC_WORKFLOWS.<partition_id>.json`
* `DOC_DECISIONS.<partition_id>.json`
* `DOC_GLOSSARY.<partition_id>.json`

**ROLE**: Mechanical deep extractor. No reasoning. JSON only. ASCII only.

**INPUTS**:
- `PARTITION_PLAN.json`
- `CAP_NOTICES.<partition_id>.json` (if present)
**PARAM**: `partition_id = <ONE_PARTITION_CHUNK_ID>`

**SCOPE**:
Only docs listed in `PARTITION_PLAN[partition_id]`.
Prioritize docs with cap_notice first, then the rest.

**EXTRACT**:

**A) DOC_INTERFACES.<partition_id>.json**
From fenced code blocks ```...``` extract:
- `language_hint` from fence (or "unknown")
- `interface_type` inferred ONLY from language_hint and first non-empty line:
  `json_envelope|yaml_config|toml_config|sql|bash|python|other`
- `block_text` capped to 120 lines
- `path`, `line_range`, `heading_path`

**B) DOC_WORKFLOWS.<partition_id>.json**
Extract step sequences under headings or paragraphs containing:
`workflow`, `pipeline`, `lifecycle`, `runbook`, `procedure`, `steps`, `how to`, `operation`, `integration`
Capture:
- `name` (heading or first line)
- `steps[]` exact strings (cap 40 steps)
- `path`, `line_range`

**C) DOC_DECISIONS.<partition_id>.json**
Extract decision snippets near markers:
`Decision:`, `Rationale`, `Tradeoff`, `Consequences`, `Alternatives`, `Chose`, `We chose`
Emit:
- `path`, `line_range`, `excerpt` <= 12 lines, `heading_path`

**D) DOC_GLOSSARY.<partition_id>.json**
If doc defines terms (patterns like "X:", "X -", "Definition"):
Emit `term` + `definition` excerpt <= 3 lines, `path`, `line_range`.

**RULES**:
- exact text only
- no summarization
- JSON only
- deterministic ordering

---

## D3: Citation / Reference Graph (global)

**Output file**
* `DOC_CITATION_GRAPH.json`

**ROLE**: Mechanical reference extractor. No reasoning. JSON only. ASCII only.

**TARGET**: `docs/**/*.md` and `docs/**/*.txt`

**Extract**:
- markdown links `[text](target)`
- plain references to other docs (paths containing "docs/" or ending in ".md")
- phrases: "see", "refer to", "linked", "as described in"

For each edge:
- `from_path`
- `to_target` (exact string)
- `context_quote` <= 12 words
- `line_range`

Output `DOC_CITATION_GRAPH.json` with stable ordering by `from_path` then `line_range`.

---

## D4: Merge + Normalize + Coverage QA (global)

**Output files**
* `DOC_INDEX.json`
* `DOC_CLAIMS.json`
* `DOC_BOUNDARIES.json`
* `DOC_SUPERSESSION.json`
* `DOC_INTERFACES.json`
* `DOC_WORKFLOWS.json`
* `DOC_DECISIONS.json`
* `DOC_GLOSSARY.json`
* `DOC_COVERAGE_REPORT.json`

**ROLE**: Mechanical normalizer. No reasoning. JSON only. ASCII only.

**INPUTS**:
- all `DOC_INDEX.*.json`
- all `DOC_CLAIMS.*.json`
- all `DOC_BOUNDARIES.*.json`
- all `DOC_SUPERSESSION.*.json`
- all `DOC_INTERFACES.*.json`
- all `DOC_WORKFLOWS.*.json`
- all `DOC_DECISIONS.*.json`
- all `DOC_GLOSSARY.*.json`
- `DOC_INVENTORY.json`
- `DOC_CITATION_GRAPH.json`

**MERGE RULES**:
- concatenate items per artifact type
- dedupe items by (`path`, `line_range`, hash(`original_quote` or `block_text` or `excerpt`))
- stable sort by `path` asc then `line_range` start asc

**OUTPUT** unified JSON artifacts listed above.

**QA OUTPUT: DOC_COVERAGE_REPORT.json**
Must include:
- `total_docs` (from DOC_INVENTORY)
- `docs_processed` (count docs appearing in any merged artifact)
- `docs_with_claims`
- `docs_with_interfaces`
- `docs_with_workflows`
- `docs_with_decisions`
- `docs_missing_all` (docs that appear in DOC_INVENTORY but not in any merged artifact)
- `archive_counts` and `evidence_counts`

**RULES**:
- no interpretation
- JSON only

---

## D5: DOC_TOPIC_CLUSTERS.json (mechanical clustering, instruction-weight aware)

**Output file**
* `DOC_TOPIC_CLUSTERS.json`

**ROLE**: Mechanical clustering engine. No reasoning. JSON only. ASCII only.

**INPUTS**:
- `DOC_INVENTORY.json`
- `DOC_INDEX.json`
- `DOC_CLAIMS.json`
- `DOC_BOUNDARIES.json`
- `DOC_WORKFLOWS.json`
- `DOC_INTERFACES.json`
- `DOC_DECISIONS.json`
- `DOC_CITATION_GRAPH.json`

**TOKEN SOURCES per doc**:
- title + headings
- claims `original_quote` tokens
- workflows `step` tokens
- boundary tokens
- interfaces: `interface_type` + `language_hint` only (not full blocks)
- decisions: first 2 lines tokens
- citation targets tokens (weak)

**TOKENIZATION**:
- lowercase
- split on non-alphanumeric
- keep tokens len >= 4
- remove stopwords
- cap 500 tokens per doc

**WEIGHTING**:
- if `is_archive=true`: drop lowest 30% frequency tokens in that doc
- if path contains `/custom-instructions/` or `/_opus_inputs/` or `/_handoff/`:
  duplicate the token set once (multiset doubling)

**SIMILARITY**:
- Jaccard overlap on token sets

**CLUSTERING**:
- deterministic greedy:
  sort docs by `citation_in_degree` desc, then `path` asc
  seed cluster with first unassigned doc
  add docs with sim >= 0.18
  do one extra expansion pass, then finalize cluster

**OUTPUT DOC_TOPIC_CLUSTERS.json**:
- `cluster_id` c001...
- `doc_paths[]`
- `top_tokens` (top 25 by document frequency within cluster)
- `anchor_docs` (top 3 docs by average similarity inside cluster)
- `cluster_stats`: `doc_count`, `avg_similarity_estimate`, `total_citation_in`, `total_citation_out`

**RULES**:
- no semantic labels
- JSON only
- deterministic ordering

---

## Model choice for Phase D
* **Gemini Flash 3**: D0–D5 (best default)
* **Grok-code-fast-1**: only if Flash fails to keep strict JSON-only, or if you want faster extraction of large code-fenced docs, but still riskier for “helpful” drift

## Minimal “today” run set (if time is tight)

Do these in order:
1. D0
2. D1 on `P2_CORE_ARCH__*`, `P3_PLANES_ACTIVE__*`, `P5_TASK_PACKETS_PM_INV__*`
3. D2 on those same partitions
4. D4
5. D5

That gives you architecture, planes, workflows, and decision spine without archive bloat.
