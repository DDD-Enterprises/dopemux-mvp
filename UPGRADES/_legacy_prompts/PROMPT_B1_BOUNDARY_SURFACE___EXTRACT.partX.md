MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase B1: Boundary Surface Extract (Part X)

Outputs:
- BOUNDARY_SURFACE.partX.json
- CAP_NOTICES.B1.partX.json (optional)

Prompt:
Extract boundary objects:
- boundary_id
- declared_in (doc/instruction/code)
- enforced_by[] (functions/hooks/middleware/scripts) with citations
- scope (what it applies to, if explicitly stated)
- config_toggles[] (env var names, config keys, flags) if explicitly present
- failure_modes[] if stated

No bypass claims here.
