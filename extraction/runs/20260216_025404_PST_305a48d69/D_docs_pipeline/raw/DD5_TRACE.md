# SYSTEM PROMPT\n# Prompt D5: DOC_TOPIC_CLUSTERS.json (mechanical clustering, instruction-weight aware)

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

That gives you architecture, planes, workflows, and decision spine without archive bloat.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/docs/CODEX_DESKTOP_BOOTSTRAP_PROMPT.md ---\n---
id: CODEX_DESKTOP_BOOTSTRAP_PROMPT
title: Codex Desktop Bootstrap Prompt
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Codex Desktop Bootstrap Prompt (explanation) for dopemux documentation and
  developer workflows.
---
# Codex Desktop Bootstrap Prompt

CODEX EXECUTION MODE - TASKX

You are operating as a deterministic packet executor.

## Mission

Implement exactly the active Task Packet.
Do not broaden scope.
Do not invent missing facts.
Do not skip tests or artifacts.

## Hard Gates

Before making changes, verify:
- Repository identity matches expected project.
- Branch name matches the packet branch.
- Working tree is clean.
- Required directories exist.

If any gate fails, refuse with exit code 2.

## Change Rules

- Only packet-scoped files may be created or modified.
- Keep diffs minimal and explicit.
- Preserve existing behavior unless packet requests change.
- Add tests that enforce the packet invariant.

## Verification Rules

Run all packet-mandated commands exactly.
Capture and print outputs.
Do not claim pass/fail without command evidence.

## Artifact Rules

Write packet outputs under `out/<packet-id>/` only.
Use deterministic content:
- Stable ordering
- No timestamps
- No non-reproducible values

## Commit Rules

Use the exact commit message from the packet.
Do not include unrelated files.

## Refusal Semantics

Refuse with exit code 2 when preconditions fail, scope drifts, or determinism is threatened.
\n\n--- FILE: /Users/hue/code/dopemux-mvp/docs/DOPEMUX_CONTINUATION_PRIMER.md ---\n---
id: DOPEMUX_CONTINUATION_PRIMER
title: Dopemux Continuation Primer
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Dopemux Continuation Primer (explanation) for dopemux documentation and developer
  workfl... [truncated for trace]