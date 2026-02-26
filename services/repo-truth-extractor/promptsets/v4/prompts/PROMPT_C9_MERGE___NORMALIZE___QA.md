# PROMPT_C9

## Goal
Produce `C9` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- `SERVICE_ENTRYPOINTS.json`
- `EVENTBUS_SURFACE.json`
- `EVENT_PRODUCERS.json`
- `EVENT_CONSUMERS.json`
- `DOPE_MEMORY_CODE_SURFACE.json`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`
- `TASKX_INTEGRATION_SURFACE.json`
- `WORKFLOW_RUNNER_SURFACE.json`
- `API_DASHBOARD_SURFACE.json`
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `SECRETS_RISK_LOCATIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SERVICE_ENTRYPOINTS.json`
- `EVENTBUS_SURFACE.json`
- `EVENT_PRODUCERS.json`
- `EVENT_CONSUMERS.json`
- `DOPE_MEMORY_CODE_SURFACE.json`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`
- `TASKX_INTEGRATION_SURFACE.json`
- `WORKFLOW_RUNNER_SURFACE.json`
- `LEANTIME_INTEGRATION_SURFACE.json`
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `CODE_SURFACES_QA.json`
- `SERVICE_CATALOG.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `SERVICE_ENTRYPOINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENTRYPOINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, type, value, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENTBUS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `EVENTBUS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENT_PRODUCERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `EVENT_PRODUCERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENT_CONSUMERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `EVENT_CONSUMERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_CODE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_CODE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_SCHEMAS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_SCHEMAS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_DB_WRITES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_DB_WRITES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TRINITY_ENFORCEMENT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `TRINITY_ENFORCEMENT_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REFUSAL_AND_GUARDRAILS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `REFUSAL_AND_GUARDRAILS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TASKX_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `TASKX_INTEGRATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `WORKFLOW_RUNNER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `WORKFLOW_RUNNER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `LEANTIME_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C11`
    - `id_rule`: `LEANTIME_INTEGRATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DETERMINISM_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DETERMINISM_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `IDEMPOTENCY_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `IDEMPOTENCY_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CONCURRENCY_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `CONCURRENCY_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CODE_SURFACES_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `CODE_SURFACES_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `SERVICE_CATALOG.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_service_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_CATALOG:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config, evidence`
    - `required_registry_fields`: `service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config`

## Extraction Procedure
1. Load all upstream C-phase artifacts (`SERVICE_ENTRYPOINTS.json`, `EVENTBUS_SURFACE.json`, `EVENT_PRODUCERS.json`, `EVENT_CONSUMERS.json`, `DOPE_MEMORY_CODE_SURFACE.json`, `DOPE_MEMORY_SCHEMAS.json`, `DOPE_MEMORY_DB_WRITES.json`, `TRINITY_ENFORCEMENT_SURFACE.json`, `REFUSAL_AND_GUARDRAILS_SURFACE.json`, `TASKX_INTEGRATION_SURFACE.json`, `WORKFLOW_RUNNER_SURFACE.json`, `API_DASHBOARD_SURFACE.json`, `DETERMINISM_RISK_LOCATIONS.json`, `IDEMPOTENCY_RISK_LOCATIONS.json`, `CONCURRENCY_RISK_LOCATIONS.json`, `SECRETS_RISK_LOCATIONS.json`). Validate each against its declared schema contract; record any schema violations as QA issues.
2. Merge artifacts that share the same `merge_strategy`: for `itemlist_by_id`, union items by `id` and merge evidence arrays. For `itemlist_by_service_id`, merge by `service_id`. Resolve field conflicts deterministically (non-empty wins, then lexicographically smallest).
3. Build the merged `SERVICE_CATALOG.json` by joining service-level data from all upstream artifacts keyed by `service_id`. For each service, assemble: entrypoints, event subscriptions, memory surfaces, enforcement points, TaskX integrations, workflow runners, API surfaces, and risk locations.
4. Run cross-artifact consistency checks: verify that every `service_id` referenced in entrypoints, events, and risk locations exists in `services/registry.yaml`; verify that every event producer has at least one consumer (flag orphans); verify that every API endpoint has enforcement coverage.
5. Emit `CODE_SURFACES_QA.json` with per-artifact validation results: schema compliance status, item count, duplicate detection results, cross-reference integrity checks, and any `needs_review` items aggregated from upstream.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

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
- Upstream artifact missing entirely (file not found): emit merged output without that artifact's data and add `missing_inputs` entry with the artifact name and expected path.
- Duplicate IDs across different upstream artifacts with conflicting field values: merge deterministically (non-empty wins, then lexicographic) and emit `status: merged_conflict` with evidence from both sources.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal:
- merged: SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json
- merged: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- merged: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json, TASKX_INTEGRATION_SURFACE.json
- merged: WORKFLOW_RUNNER_SURFACE.json
- merged: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json
- QA: CODE_SURFACES_QA.json

Prompt:
- Merge all C1-C8 outputs.
- QA: Ensure all artifacts present, no secrets, coverage complete.
```
