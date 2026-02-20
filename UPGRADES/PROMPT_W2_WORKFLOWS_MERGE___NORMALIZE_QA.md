MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase W2: Workflows Merge + Normalize + QA

Outputs:
- WORKFLOWS_EXTRACTED.json
- WORKFLOW_TOUCHES.json
- WORKFLOW_QA.json

Prompt:
Merge part files
Normalize IDs and stable ordering

QA:
- orphan steps without evidence
- workflows with missing triggers
- duplicate workflow_ids
