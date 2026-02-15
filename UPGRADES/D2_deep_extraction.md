## D2: Deep extraction (interfaces + workflows + decisions) (run per partition chunk)

Output files
	•	DOC_INTERFACES.<partition_id>.json
	•	DOC_WORKFLOWS.<partition_id>.json
	•	DOC_DECISIONS.<partition_id>.json
	•	DOC_GLOSSARY.<partition_id>.json

ROLE: Mechanical deep extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- PARTITION_PLAN.json
- CAP_NOTICES.<partition_id>.json (if present)
PARAM: partition_id = <ONE_PARTITION_CHUNK_ID>

SCOPE:
Only docs listed in PARTITION_PLAN[partition_id].
Prioritize docs with cap_notice first, then the rest.

EXTRACT:

A) DOC_INTERFACES.<partition_id>.json
From fenced code blocks ```...``` extract:
- language_hint from fence (or "unknown")
- interface_type inferred ONLY from language_hint and first non-empty line:
  json_envelope|yaml_config|toml_config|sql|bash|python|other
- block_text capped to 120 lines
- path, line_range, heading_path

B) DOC_WORKFLOWS.<partition_id>.json
Extract step sequences under headings or paragraphs containing:
workflow, pipeline, lifecycle, runbook, procedure, steps, how to, operation, integration
Capture:
- name (heading or first line)
- steps[] exact strings (cap 40 steps)
- path, line_range

C) DOC_DECISIONS.<partition_id>.json
Extract decision snippets near markers:
Decision:, Rationale, Tradeoff, Consequences, Alternatives, Chose, We chose
Emit:
- path, line_range, excerpt <= 12 lines, heading_path

D) DOC_GLOSSARY.<partition_id>.json
If doc defines terms (patterns like "X:", "X -", "Definition"):
Emit term + definition excerpt <= 3 lines, path, line_range.

RULES:
- exact text only
- no summarization
- JSON only
- deterministic ordering
