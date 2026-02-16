# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase Z0: Handoff Bundle + Freeze Run

Outputs:
- HANDOFF_BUNDLE.md
- HANDOFF_BUNDLE.json

Prompt:
ROLE: GPT-5.2.
Inputs: pipeline doctor + R + catalogs + TP backlog.
Output:
- frozen invariants
- authoritative artifacts list (hashes if available)
- what may change vs must not
- next-run instructions
\n\n# USER CONTEXT\n... [truncated for trace]