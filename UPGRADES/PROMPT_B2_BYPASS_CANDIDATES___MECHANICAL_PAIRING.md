MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase B2: Bypass Candidates (Mechanical Pairing)

Outputs:
- BOUNDARY_BYPASS_CANDIDATES.json

Prompt:
Using:
- boundary enforcement list
- execution graph
- alternate entrypoints/commands

Emit candidate patterns only when you can cite a "paired" situation:
- Path A calls enforcement, Path B does not
- Config disables enforcement
- Different instruction precedence could suppress enforcement

Output each candidate with:
- candidate_id, boundary_id, evidence_pairs[], why_candidate
