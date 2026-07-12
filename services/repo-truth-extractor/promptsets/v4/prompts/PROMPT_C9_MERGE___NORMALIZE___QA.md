# PROMPT_C9

## Goal
Merge and normalize the C0-C8 code-truth artifacts without weakening their producer contracts.
Emit only artifacts that can be constructed from inputs available when C9 runs, with deterministic
conflict handling, explicit evidence, and a fail-closed QA result.

## Inputs
- Source scope (use only to resolve conflicts and construct the C9-only derived surfaces):
  - `src/**`
  - `services/**`
  - `components/**`
  - `dashboard/**`
  - `plugins/**`
  - `ui-dashboard/**`
  - `ui-dashboard-backend/**`
  - `docker/**`
  - `compose.yml`
  - `docker-compose*.yml`
  - `services/registry.yaml`
- Upstream normalized artifacts available before C9:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `DOPE_MEMORY_CODE_SURFACE.json`
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
- Use `services/registry.yaml` as the canonical service identity list when it is present.

## Outputs
- `SERVICE_ENTRYPOINTS.json`
- `EVENTBUS_SURFACE.json`
- `EVENT_PRODUCERS.json`
- `EVENT_CONSUMERS.json`
- `DOPE_MEMORY_CODE_SURFACE.json`
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`
- `TASKX_INTEGRATION_SURFACE.json`
- `WORKFLOW_RUNNER_SURFACE.json`
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `PYTHON_API_SURFACE.json`
- `SERVICE_ENDPOINT_SURFACE.json`
- `SERVICE_CATALOG.json`
- `CODE_SURFACES_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `SERVICE_ENTRYPOINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENTRYPOINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, entrypoint_type, invocation, module_path, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENTBUS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `EVENTBUS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, event_name, channel, transport, retry_policy, ordering_guarantee, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENT_PRODUCERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `EVENT_PRODUCERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, event_name, producer_symbol, call_pattern, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENT_CONSUMERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `EVENT_CONSUMERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, event_name, consumer_symbol, registration_pattern, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_CODE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_CODE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
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
  - `DETERMINISM_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DETERMINISM_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk_type, severity, affected_symbol, non_deterministic_call, mitigation_present, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `IDEMPOTENCY_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `IDEMPOTENCY_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk_type, severity, affected_symbol, operation, mitigation_present, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CONCURRENCY_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `CONCURRENCY_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk_type, severity, affected_symbol, shared_resource, access_pattern, mitigation_present, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `PYTHON_API_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `PYTHON_API_SURFACE:<stable-hash(module_path|symbol|symbol_kind)>`
    - `required_item_fields`: `id, module_path, symbol, symbol_kind, signature, visibility, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
  - `SERVICE_ENDPOINT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENDPOINT_SURFACE:<stable-hash(service_id|endpoint_type|endpoint_name)>`
    - `required_item_fields`: `id, service_id, endpoint_type, endpoint_name, http_method, path_template, handler_symbol, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
  - `SERVICE_CATALOG.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_service_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_CATALOG:<stable-hash(service_id)>`
    - `required_item_fields`: `id, service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config, evidence`
    - `required_registry_fields`: `service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config`
  - `CODE_SURFACES_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `CODE_SURFACES_QA:<stable-hash(check|artifact_name)>`
    - `required_item_fields`: `id, status, checks, issues, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`

## Extraction Procedure
1. Load C0-C8 artifacts only. Reject missing required inputs or contracts instead of inferring later-step data.
2. Validate every producer item against its producer contract before merge. Do not rename, remove, or replace producer fields; merge results must retain the complete producer field set plus any non-conflicting additional fields.
3. Canonicalize `SERVICE_ENTRYPOINTS.json`, `EVENTBUS_SURFACE.json`, `EVENT_PRODUCERS.json`, `EVENT_CONSUMERS.json`, `DOPE_MEMORY_CODE_SURFACE.json`, `TRINITY_ENFORCEMENT_SURFACE.json`, `REFUSAL_AND_GUARDRAILS_SURFACE.json`, `TASKX_INTEGRATION_SURFACE.json`, `WORKFLOW_RUNNER_SURFACE.json`, `DETERMINISM_RISK_LOCATIONS.json`, `IDEMPOTENCY_RISK_LOCATIONS.json`, and `CONCURRENCY_RISK_LOCATIONS.json` by stable ID. Union evidence arrays, preserve every producer field, and record scalar conflicts in deterministic `merge_conflicts` entries without overwriting either observed value.
4. Build `PYTHON_API_SURFACE.json` by opening source paths from `CODE_INVENTORY.json` and extracting public module functions, classes, constants, and re-exports. Cross-check `SERVICE_ENTRYPOINTS.json`; preserve exact module paths and signatures when evidenced, otherwise emit `UNKNOWN` with an evidence gap.
5. Build `SERVICE_ENDPOINT_SURFACE.json` from `EVENTBUS_SURFACE.json`, `EVENT_PRODUCERS.json`, `EVENT_CONSUMERS.json`, and the read-only `API_DASHBOARD_SURFACE.json` input. Use explicit endpoint types (`http`, `websocket`, `eventbus`, `mcp`, or `unknown`) and retain source artifact evidence.
6. Build `SERVICE_CATALOG.json` from `services/registry.yaml`, `SERVICE_ENTRYPOINTS.json`, `EVENTBUS_SURFACE.json`, `API_DASHBOARD_SURFACE.json`, `TASKX_INTEGRATION_SURFACE.json`, and `WORKFLOW_RUNNER_SURFACE.json`. Aggregate entrypoints, interfaces, dependencies, and configuration by `service_id`; do not consume C10 or later-step artifacts.
7. `API_DASHBOARD_SURFACE.json remains C7-owned` and `SECRETS_RISK_LOCATIONS.json remains C8-owned`; validate and consume them as read-only inputs without re-emitting or redefining their contracts.
8. Emit `CODE_SURFACES_QA.json` with one deterministic item per output contract. Report presence, schema validation, duplicate IDs, field-preservation checks, evidence completeness, and unresolved merge conflicts.
9. Attach evidence to every non-derived field and relationship. Legacy context and model assumptions are never evidence.
10. Sort items by `id`, evidence by `(path, line_range, excerpt)`, and conflict records by `(field, source_artifact, value_hash)`; serialize with stable key ordering.
11. Fail closed when a required producer field is absent. Use `UNKNOWN` only for a declared field whose value cannot be established, and include the evidence gap in `CODE_SURFACES_QA.json`.
12. Emit exactly the 16 declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
