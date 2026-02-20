# PROMPT_T2 — PACKET SCHEMA / AUTHORITY RULES

TASK: Define the canonical Task Packet schema and authority hierarchy used by Phase T.

OUTPUTS:
- TP_SCHEMA.json
- TP_AUTHORITY_RULES.json

Rules:
- implementer_target must be exactly `Codex Desktop (GPT-5.3-Codex)`.
- Authority hierarchy is strict: R norm artifacts > X norm artifacts > policy docs.
- Every packet must include evidence-backed `authority_inputs` paths.
- No packet may require re-scan, truth reinterpretation, or undocumented assumptions.
- Define required fields, validation constraints, and failure reasons for schema noncompliance.
