## D1: Claims + Boundaries + Supersession (run per partition chunk)

Output files
	•	DOC_INDEX.<partition_id>.json
	•	DOC_CLAIMS.<partition_id>.json
	•	DOC_BOUNDARIES.<partition_id>.json
	•	DOC_SUPERSESSION.<partition_id>.json
	•	CAP_NOTICES.<partition_id>.json

ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- DOC_INVENTORY.json
- PARTITION_PLAN.json
PARAM: partition_id = <ONE_PARTITION_CHUNK_ID>

SCOPE:
Only docs listed in PARTITION_PLAN[partition_id].

For each doc, extract:

A) DOC_INDEX.<partition_id>.json
- headings H1-H3 with line ranges (cap 120 headings per doc)
- anchor_quotes: 5 short quotes (<= 12 words) with line ranges, chosen deterministically:
  pick the first 5 non-empty lines that are not headings, skipping code fences

B) DOC_CLAIMS.<partition_id>.json
Extract atomic sentences containing any of these tokens (case-insensitive):
MUST, MUST NOT, SHALL, REQUIRED, FORBIDDEN, INVARIANT, DEFAULT, DETERMINISTIC,
FAIL-CLOSED, APPEND-ONLY, SINGLE SOURCE OF TRUTH, AUTHORITY, TRINITY,
EVENTBUS, PRODUCER, CONSUMER, TASKX, MCP, HOOK, WORKFLOW, PIPELINE

For each claim item:
- path, line_range, heading_path
- original_quote (exact sentence)
- trigger_tokens[] (which words matched)

C) DOC_BOUNDARIES.<partition_id>.json
Extract atomic sentences that define:
- ownership/responsibility separation
- module/service boundaries
- interface contracts between subsystems
Use same structure as claims, but kind="boundary".

D) DOC_SUPERSESSION.<partition_id>.json
Extract lines that indicate:
- "supersedes", "replaces", "deprecated", "obsolete", "archived", "active", "status",
  version numbers, dates in headings
Emit items with path, line_range, excerpt <= 2 lines.

E) CAP_NOTICES.<partition_id>.json
If doc line_count_estimate > 900 OR size_bytes > 250000 OR has_code_fences=true:
- emit cap_notice with reason, and recommended_next="D2_DEEP"

RULES:
- exact text only
- no summarization
- stable ordering by path then line_range
- JSON only
