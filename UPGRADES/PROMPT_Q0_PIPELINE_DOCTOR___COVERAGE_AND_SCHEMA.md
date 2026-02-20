MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase Q0: Pipeline Doctor + Coverage & Schema

Outputs:
- PIPELINE_DOCTOR_REPORT.json

Prompt:
Input: all phase outputs in extraction/latest/**

Checks:
- required artifacts exist per phase
- each JSON item has required keys (path, line_range, stable id)
- no duplicate prompt collisions (same prefix)
- no CAP_NOTICES unresolved
- no secrets leakage (match only; do not print secret values)
- stable sorting verified

Emit PASS/WARN/FAIL with reasons and file lists.
