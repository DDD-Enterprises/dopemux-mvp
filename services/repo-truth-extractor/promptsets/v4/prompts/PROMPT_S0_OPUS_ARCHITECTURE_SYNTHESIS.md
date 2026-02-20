# PROMPT_S0

## Goal
Produce `S0` outputs for phase `S` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
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

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `CONTROL_PLANE_TRUTH_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `DOPE_MEMORY_IMPLEMENTATION_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `EVENTBUS_WIRING_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `EVENTBUS_WIRING_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `TRINITY_BOUNDARY_ENFORCEMENT_TRA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TASKX_INTEGRATION_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `TASKX_INTEGRATION_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `WORKFLOWS_TRUTH_GRAPH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `WORKFLOWS_TRUTH_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
  - `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `PORTABILITY_AND_MIGRATION_RISK_L:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
  - `CONFLICT_LEDGER.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `CONFLICT_LEDGER:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `RISK_REGISTER_TOP20.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `RISK_REGISTER_TOP20:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
  - `ARCHITECTURE_SYNTHESIS_OPUS.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `S0`
    - `id_rule`: `ARCHITECTURE_SYNTHESIS_OPUS:<stable-hash(path|symbol|name)>`
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
# PROMPT_S0 — OPUS ARCHITECTURE + SUBSYSTEM SYNTHESIS (from Truth Pack)

ROLE: Opus Reviewer/Synthesist.
MODE: Evidence-bounded synthesis. No excavation.

GOAL:
Produce a coherent, decision-grade architecture map for Dopemux and how TaskX fits into it,
using ONLY the Truth Pack outputs from Phase R (+ supporting indices from X, and doc clusters from D).

HARD RULES:
1) Do NOT rescan repo. Do NOT infer undocumented mechanisms.
2) Every non-trivial claim MUST cite one of the Phase R truth artifacts, using:
   EVIDENCE: <filename>#<section or anchor>
3) If evidence is missing or ambiguous: write UNKNOWN and specify exactly what artifact is missing.
4) Prefer "implemented reality" over "planned intent":
   - IMPLEMENTED comes from Phase R's CODE-based sections
   - PLANNED comes from Phase R's DOC-based sections
5) No refactors. No rewriting. Only architecture decisions + bounded recommendations.

INPUTS (required):
- R0 CONTROL_PLANE_TRUTH_MAP.md
- R1 DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- R2 EVENTBUS_WIRING_TRUTH.md
- R3 TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- R4 TASKX_INTEGRATION_TRUTH.md
- R5 WORKFLOWS_TRUTH_GRAPH.md
- R6 PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7 CONFLICT_LEDGER.md
- R8 RISK_REGISTER_TOP20.md
Optional but helpful:
- X feature index outputs (X* merged/norm)
- D doc clusters + supersession outputs

DELIVERABLE:
Write ARCHITECTURE_SYNTHESIS_OPUS.md with:

1) Executive Architecture Snapshot (1 page)
- What exists today (implemented)
- What is planned but not implemented
- Key boundaries and planes
EVIDENCE required per bullet.

2) Subsystem Boundary Map
For
```
