MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase Q1: Doc Recency + Duplicate Groups

Outputs:
- DOC_RECENCY_DUPLICATE_REPORT.json

Prompt:
Inputs: DOC_INVENTORY.json, DOC_DUPLICATES.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json

For each duplicate group:
- list docs with mtime, any explicit supersession markers, cluster membership
- emit needs_arbitration=true/false (mechanical criteria only)
