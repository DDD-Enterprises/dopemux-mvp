# PROMPT_E6 — Execution risks + ordering/state dependencies

ROLE: Execution plane extractor.
GOAL: record determinism/portability risks related to ordering, state files, env, time, or non-determinism.

OUTPUTS:
  • EXEC_RISK_LOCATIONS.json (risks[]: {kind(ordering/state/env/time/non-determinism), evidence_refs[], severity, mitigation_hint})

RULES:
  • Only note risks supported by textual evidence (no guessing).
  • Mitigation hints must be actionable and evident in sources.
