# PROMPT_S1

## Goal
Produce phase `S1` migration planning artifacts that transform arbitration truths into a conservative MCP-to-hooks plan. The output must remain evidence-bounded, reversible, and suitable for task packet generation without introducing refactors or speculative behavior claims.

## Inputs
- Source scope:
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/X_feature_index/norm/**`
  - `extraction/**/T_task_packets/norm/**`
  - `extraction/**/Z_handoff_freeze/norm/**`
- Required artifacts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
  - `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
  - `CONFLICT_LEDGER.md`
  - `RISK_REGISTER_TOP20.md`
- Optional supporting artifacts:
  - `REPO_MCP_SERVER_DEFS.json`
  - `REPO_HOOKS_SURFACE.json`
  - `REPO_MCP_PROXY_SURFACE.json`
  - `REPO_ROUTER_SURFACE.json`
  - `FEATURE_INDEX_MERGED.json`
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
- Constraint:
  - Operate only on supplied phase artifacts; no direct repository scans.

## Outputs
- `MCP_TO_HOOKS_MIGRATION_OPUS.md`
- `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`

## Schema
- Artifact kind: markdown planning documents with deterministic section order.
- Canonical writer: `S1` for both declared outputs.
- Output contracts:
  - `MCP_TO_HOOKS_MIGRATION_OPUS.md`: compatibility migration report for existing consumers.
  - `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`: step-scoped migration plan alias for new consumers.
- Mandatory content blocks in each output:
  - Scope and constraints
  - Candidate inventory with eligibility gate status
  - Staged migration plan with entry criteria, steps, verification suggestions, and rollback
  - No-go triggers table with `risk_id` and optional `conflict_id`
  - Unknown/missing evidence register
- Candidate eligibility rule:
  - Include a candidate only when evidence exists for both current MCP surface and target hooks surface.

## Extraction Procedure
1. Build a migration evidence map from required arbitration artifacts and optional control-surface artifacts.
2. Enumerate candidate surfaces and evaluate eligibility using the dual-evidence gate.
3. Reject ineligible candidates into `UNKNOWN` with explicit missing evidence references.
4. Create staged plan entries that remain mechanical and rollback-capable.
5. Derive no-go triggers from `R8` risk IDs and `R7` conflicts where relevant.
6. Write identical semantic content to both outputs to maintain compatibility and alias determinism.

## Evidence Rules
- Every non-trivial plan claim must terminate with:
  - `EVIDENCE: <artifact_filename>#<section_heading_or_anchor>`
- Risk and no-go entries must cite `R8` and include `R7` when conflict-driven.
- Candidate inclusion must reference at least one MCP-side and one hook-side evidence anchor.
- Unsupported candidates must be listed in unknowns with explicit missing artifacts.
- If evidence objects are emitted, include `path`, `line_range`, and `excerpt` keys.
- Never present migration readiness without cited evidence.
- Do not cite non-input artifacts.

## Determinism Rules
- Do not include `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Keep section order fixed and candidate ordering deterministic.
- Use fixed status tokens: `ELIGIBLE`, `INELIGIBLE`, `UNKNOWN`, `NO_GO`, `READY`.
- Keep `MCP_TO_HOOKS_MIGRATION_OPUS.md` and `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md` semantically identical.
- Avoid speculative terms unless coupled with `UNKNOWN` and missing evidence details.
- Normalize table columns and heading names for reproducible output.

## Anti-Fabrication Rules
- Do not invent migration targets, hooks, proxies, or service boundaries.
- Do not infer target mechanisms without direct evidence.
- Do not claim execution or validation was performed.
- Do not recommend refactors or broad architecture rewrites.
- Do not hide uncertainty; unresolved issues must stay explicit.
- Do not modify risk severity labels without evidence anchors.

## Failure Modes
- Required artifacts missing: output conservative plan with `UNKNOWN` sections and missing input list.
- Candidate evidence asymmetric (MCP present, hook absent or vice versa): mark candidate `INELIGIBLE` and exclude from execution steps.
- Conflict cannot be resolved from available evidence: tie candidate to `NO_GO` and flag for PRO escalation.
- Risk mapping incomplete: include explicit no-go placeholder and missing-risk evidence request.
- Alias output drift between two files: regenerate both from the same deterministic content template.
- Excessive optional-input dependence: downgrade confidence and keep stage progression conservative.
