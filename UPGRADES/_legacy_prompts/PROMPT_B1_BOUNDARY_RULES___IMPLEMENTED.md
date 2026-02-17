# PROMPT_B1 — Trinity boundary enforcement surfaces

ROLE: Boundary plane extractor.
GOAL: Extract concrete enforcement points: checks, validators, refusals, and how they propagate.

OUTPUTS:
  • TRINITY_ENFORCEMENT_SURFACE.json
    - enforcement_points[]: {file, symbol, boundary_kind, check_description, failure_behavior, evidence_refs[]}
  • REFUSAL_AND_GUARDRAILS_SURFACE.json
    - rails[]: {file, symbol, creates_refusal, propagates_refusal, evidence_refs[]}

RULES:
  • evidence_refs must be precise: file + line range when available, else file + quoted phrase.
  • If enforcement cannot be proven, label it "suspected" and include why with its evidence.
