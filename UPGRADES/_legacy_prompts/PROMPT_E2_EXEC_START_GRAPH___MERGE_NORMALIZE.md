MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase E2: Exec Start Graph + Merge & Normalize

Outputs:
- EXEC_COMMAND_INDEX.json
- EXEC_SERVICE_START_GRAPH.json
- EXEC_QA.json

Prompt:
Merge all EXEC_COMMAND_INDEX.part*.json
Build EXEC_SERVICE_START_GRAPH.json:
- nodes: services/scripts/commands
- edges: "invokes", "depends_on", "writes_to", "reads_from"

QA:
- missing partitions
- commands without citations
- duplicate IDs
- unstable ordering
