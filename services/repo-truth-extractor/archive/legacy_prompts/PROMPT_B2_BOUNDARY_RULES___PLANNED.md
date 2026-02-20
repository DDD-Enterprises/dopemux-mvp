# PROMPT_B2 — Bypass paths + missing guards (evidence-only)

ROLE: Boundary plane auditor.
GOAL: Identify bypass paths backed by explicit evidence (alternate code paths, missing checks noted in docs/TODOs).

OUTPUTS:
  • BOUNDARY_BYPASS_RISKS.json
    - risks[]: {kind(missing_check/alternate_path/config_override/manual_escape), description, evidence_refs[], severity_hint(low/med/high)}

RULES:
  • No inference. Omit anything without explicit evidence.
  • severity_hint should be conservative unless clearly stated otherwise.
