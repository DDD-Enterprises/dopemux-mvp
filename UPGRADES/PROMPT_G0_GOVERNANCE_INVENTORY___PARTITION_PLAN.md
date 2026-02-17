# PROMPT_G0 — GOVERNANCE inventory + partition plan

ROLE: Governance recon.
GOAL: Identify repo governance surfaces (CI, lint/test gates, hygiene policies, release rules, branch protections).

SCOPE TARGETS:
  • .github/, config/, docs/, Makefile, scripts/
  • any "policy" JSON/YAML, root hygiene, formatting, pre-commit, CI workflows

OUTPUTS:
  • GOVERNANCE_INVENTORY.json
    - items[]: {path, kind(ci/policy/doc/script), controls[], triggers[], evidence_refs[]}
  • GOVERNANCE_PARTITIONS.json
    - partitions[]: {id, label, include_globs[], exclude_globs[], max_files_hint, rationale}

RULES:
  • controls[] must contain literal strings ("ruff", "pre-commit", "root hygiene", etc.) found in configs.
