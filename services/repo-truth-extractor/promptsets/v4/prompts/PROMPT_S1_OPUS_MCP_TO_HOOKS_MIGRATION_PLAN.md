# PROMPT_S1

## Goal
Produce `S1` outputs for phase `S` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- `WORKFLOWS_TRUTH_GRAPH.md`
- `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
- `CONFLICT_LEDGER.md`
- `RISK_REGISTER_TOP20.md`
- `ARCHITECTURE_SYNTHESIS_OPUS.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `MCP_TO_HOOKS_MIGRATION_OPUS.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `MCP_TO_HOOKS_MIGRATION_OPUS.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S1`
    - `id_rule`: `MCP_TO_HOOKS_MIGRATION_OPUS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
2. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
3. Attach evidence to every non-derived field and every relationship edge.
4. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
5. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
6. Emit exactly the declared outputs and no additional files.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_S1 — OPUS MCP -> HOOKS MIGRATION IMPACT + PLAN (from Truth Pack)

ROLE: Opus Reviewer/Synthesist.
MODE: Migration planner under evidence constraints.

GOAL:
Design a safe, incremental MCP -> hooks migration plan (or a no-go recommendation),
grounded ONLY in Phase R truth artifacts and portability risks.

HARD RULES:
1) No repo rescans, no invented components.
2) Every migration claim MUST cite Phase R evidence:
   EVIDENCE: <filename>#<section>
3) Separate:
   - What is feasible now (IMPLEMENTED surfaces)
   - What requires new work (PLANNED or UNKNOWN)
4) No large refactors: propose minimal, mechanical steps.

INPUTS (required):
- R0 CONTROL_PLANE_TRUTH_MAP.md
- R5 WORKFLOWS_TRUTH_GRAPH.md
- R6 PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7 CONFLICT_LEDGER.md
- R8 RISK_REGISTER_TOP20.md
Optional:
- R3 TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md (to avoid bypassing guardrails)

DELIVERABLE:
Write MCP_TO_HOOKS_MIGRATION_OPUS.md with:

1) Current-State Control Surfaces
- What MCP is currently responsible for (by evidence)
- What hooks/scripts/compose already do (by evidence)
EVIDENCE per bullet.

2) Migration Candidates Table
Surface | Current mechanism | Proposed mechanism | Preconditions | Risks | Evidence
Only include candidates supported by evidence.

3) "Portability First" Plan (staged)
Stage 0: Observability + proof pack hardening
Stage 1: Low-risk moves (no behavior change)
Stage 2: Behavioral moves behind flags
Stage 3: Decommission candidates
Each stage must include:
- Entry criteria
- Steps
- Rollback
- Evidence links
- Risks mapped to R8

4) No-Go Triggers
List c
```
