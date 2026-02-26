# PROMPT_R5

## Goal
Produce `R5` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOWS_TRUTH_GRAPH.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOWS_TRUTH_GRAPH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R5`
    - `id_rule`: `WORKFLOWS_TRUTH_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`

## Extraction Procedure
1. Load all required upstream normalized artifacts as specified in the inputs section. Validate each artifact's schema compliance before processing. Synthesize workflow truth graph from Phase C workflow runners, Phase E execution surfaces, and Phase A compose/startup artifacts. Build a complete DAG of workflow execution with evidence at each node and edge.
2. For each synthesized fact or truth claim, require evidence from at least one normalized artifact. Chain evidence through multiple artifacts when the truth spans phases (e.g., doc claim → code implementation → runtime state).
3. Identify gaps: areas where evidence is incomplete, artifacts are missing, or cross-phase consistency cannot be verified. Record each gap with `status: UNKNOWN` and `missing_evidence_reason`.
4. Format the output as the declared artifact type (markdown for `.md` outputs, JSON for `.json` outputs). For markdown outputs, structure with clear sections, evidence citations, and an explicit UNKNOWN/gaps section at the end.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

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
- Required upstream artifact missing: emit output with available data and add `missing_inputs` section listing unavailable artifacts with their expected phase/step.
- Cross-phase evidence contradicts (e.g., docs say X, code does Y): emit both with `status: contradiction` and evidence from each source; do not resolve the contradiction, only document it.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: WORKFLOWS_TRUTH_GRAPH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce workflow truth graph.

MUST INCLUDE:
- Bootstrap flows (tmux, compose, scripts)
- Multi-service workflows with order/dependencies
- Inputs/outputs/artifacts where explicit
- Instruction-file-driven workflow steps

OUTPUT:
- Workflow list (W1..Wn) with literal steps + citations
- Services involved per workflow
- UNKNOWN markers where evidence is missing

RULES:
- No inferred steps.
- Use WORKFLOW_RUNNER_SURFACE + HOME_TMUX_WORKFLOW_SURFACE + compose graph evidence.
```
