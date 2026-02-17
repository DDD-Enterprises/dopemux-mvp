# PROMPT_B0 — BOUNDARY inventory + partition plan

ROLE: Boundary plane recon.
GOAL: Find all boundary declarations/enforcements across code, docs, and control plane surfaces.

SCOPE TARGETS:
  • src/, services/, tools/
  • docs/ (architecture, ADRs, invariants)
  • repo control plane outputs (instructions, hooks, router configs)

OUTPUTS:
  • BOUNDARY_INVENTORY.json
    - items[]: {path, kind(code/doc/config), boundary_terms_found[], enforcement_terms_found[], referenced_planes[], symbols_if_any[], evidence_refs[]}
  • BOUNDARY_PARTITIONS.json
    - partitions[]: {id, label, include_globs[], exclude_globs[], max_files_hint, rationale}

RULES:
  • boundary_terms_found must be literal matches ("Trinity", "plane", "boundary", "refusal", "guardrail").
  • Do not interpret semantics in B0; simply inventory.
