MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase B0: Boundary Inventory + Sources & Partitions

Outputs:
- BOUNDARY_SOURCE_INDEX.json
- BOUNDARY_PARTITIONS.json

Prompt:
Inputs:
- code boundary surfaces (Trinity/guardrails/refusals)
- docs boundaries
- instruction surfaces
- execution graph (where boundaries might be bypassed)

Index boundary definitions and enforcement callsites

Partition by boundary family:
- B_TRINITY, B_VALIDATION, B_REDACTION, B_ROUTING, B_PRIVACY, B_AUTH, B_MISC
