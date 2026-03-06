# PROMPT_C0

## Goal
Produce `C0` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CODE_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CODE_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `src/**`, `services/**`, `docker/**`, `compose.yml`, `docker-compose*.yml`, and `services/registry.yaml` for all code modules, service definitions, Dockerfiles, and compose service declarations.
2. For each discovered module, classify by `kind`: service-entrypoint, shared-library, workflow-script, eventbus-module, dope-memory-module, boundary-module, taskx-bridge, or utility; record the owning subsystem.
3. Build the code partition plan by grouping modules into cohesive partitions aligned with subsystems listed in Legacy Context (services entrypoints, shared, src, workflow scripts, eventbus, dope-memory, boundary/guardrail, taskx bridges); assign `partition_id` derived from `SHA256(sorted(file_paths))`.
4. Cross-reference each module against `services/registry.yaml` to assign `service_id`; for modules in `shared/**` or `src/**` assign to all consuming services or mark `service_id: shared`.
5. For each CODE_INVENTORY item, populate `id` using `CODE_INVENTORY:<stable-hash(path|symbol|name)>`, `path`, `kind`, `summary`, and `evidence`.
6. For each CODE_PARTITIONS item, populate `id` using `CODE_PARTITIONS:<stable-hash(path|symbol|name)>`, `partition_id`, `files` (sorted), `reason`, and `evidence`.
7. Legacy Context is intent guidance only and is never evidence.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

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
- Module with ambiguous subsystem ownership: if a module straddles multiple subsystem categories (e.g. a workflow script that also contains eventbus logic), assign to the primary subsystem and note the secondary in `coverage_notes`.
- Compose service without matching code: if a compose service declaration has no matching code module in `src/**` or `services/**`, emit with `kind: compose_only` and `missing_evidence_reason`.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: CODE_INVENTORY.json, CODE_PARTITIONS.json

Prompt:
- Build partitions by subsystem:
  - services/** entrypoints
  - shared/**
  - src/**
  - workflow scripts
  - eventbus modules
  - dope-memory modules
  - boundary/guardrail modules
  - taskx bridges
```
