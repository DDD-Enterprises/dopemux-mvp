MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase G0: Governance Inventory + Policy Sources & Partitions

Outputs:
- GOVERNANCE_SOURCE_INDEX.json
- GOVERNANCE_PARTITIONS.json

Prompt:
Index:
- CI workflows, pre-commit, repo hygiene policies, redaction rules, output allowlists
- instruction precedence mentions
- any "authority hierarchy" statements

Partition:
- G_CI, G_PRECOMMIT, G_REPO_HYGIENE, G_REDACTION, G_INSTRUCTION_AUTHORITY, G_RELEASES
