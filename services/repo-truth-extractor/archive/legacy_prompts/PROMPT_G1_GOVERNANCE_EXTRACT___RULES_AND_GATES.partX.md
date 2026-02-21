MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase G1: Governance Extract Rules + Gates (Part X)

Outputs:
- GOVERNANCE_RULES.partX.json
- CAP_NOTICES.G1.partX.json (optional)

Prompt:
Extract rules:
- gate name, trigger, exact command(s), files affected
- forbidden paths/patterns
- allowlist exceptions
- redaction constraints
- instruction authority/precedence statements (as candidates only)

Every rule must cite source lines.
