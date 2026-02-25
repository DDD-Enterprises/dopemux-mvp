# PROMPT_T0

## Goal
Produce `T0` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PROJECT_INSTRUCTIONS.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T0`
    - `id_rule`: `PROJECT_INSTRUCTIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load R-phase norm artifacts (R0-R8) and X-phase feature/risk catalogs as specified in the inputs section. Produce a task packet factory by scanning `PROJECT_INSTRUCTIONS.md`, governance constraints from `AGENTS.md`, and upstream truth artifacts to build an implementation-ready top-10 TP backlog ranked by severity, blast radius, and dependency order.
2. For each candidate task packet, require at least one R-phase evidence chain linking the problem statement to a specific risk ID, conflict entry, or truth-map gap. Do not fabricate problem statements unsupported by upstream artifacts.
3. Validate that every packet includes: `tp_id`, `title`, `priority`, `problem_statement`, `authority_inputs` (paths to R/X norm artifacts), `invariants`, `scope_in`, `scope_out`, `acceptance_criteria`, `rollback`, and `stop_conditions`. Set `implementer_target` to the declared target from Legacy Context.
4. Cross-reference the backlog against `PIPELINE_DOCTOR_REPORT.json` (if available) to exclude packets that depend on artifacts flagged as incomplete or corrupted.
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
- R-phase norm artifacts missing or incomplete: emit partial backlog with reduced confidence scores and add `missing_authority_inputs` section listing unavailable R/X artifacts.
- Packet field validation fails against TP schema: retain packet with `status: schema_violation` and list specific failing fields with reasons.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: Produce an implementation-ready top-10 TP backlog from R/X norm artifacts.

Role:
- Arbitration planner only. Do not implement code.
- Truth authority is R norm artifacts.

Inputs:
- R norm artifacts (R0-R8 outputs) from extraction/runs/<run_id>/R_arbitration/norm/
- X feature/risk catalogs from extraction/runs/<run_id>/X_feature_index/norm/
- Repo governance constraints from AGENTS.md and .claude/PROJECT_INSTRUCTIONS.md

Outputs:
- TP_BACKLOG_TOPN.json
- TP_INDEX.json

Required schema keys for TP_BACKLOG_TOPN.json:
- run_id
- generated_at
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].priority
- packets[].problem_statement
- packets[].authority_inputs (array of repo paths to R artifacts)
- packets[].invariants (array)
- packets[].scope_in
- packets[].scope_out
- packets[].acceptance_criteria (array)
- packets[].rollback
- packets[].stop_conditions (array)
- packets[].implementer_target

Hard rules:
- implementer_target must equal "Codex Desktop (GPT-5.3-Codex)" for every packet.
- authority_inputs must reference only R/X norm artifacts by path.
- No packet may require repo re-scan or truth reinterpretation.
- No packet may omit deterministic verification commands.

Stop conditions:
- Any TP missing scope, invariants, commands, acceptance criteria, rollback, or stop conditions.
- Any TP proposes a refactor without evidence-driven necessity.
```
