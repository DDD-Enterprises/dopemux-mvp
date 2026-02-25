# PROMPT_C4

## Goal
Produce `C4` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
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

## Extraction Procedure
1. Scan `src/**` and `services/**` for trinity boundary enforcement components: classes, decorators, or middleware that implement access control checks, role-based gating, permission validation, or trust-zone boundary assertions. For each component, record the enforcement mechanism (decorator, middleware, inline check), the protected resource, and file path with line range evidence.
2. Identify refusal artifacts: functions or handlers that return denial responses (HTTP 403/401, error objects, refusal messages). Extract the refusal condition, the response payload pattern, and the triggering check. Record file path and line range for each.
3. Trace gating chains: follow the call path from request entry (router/endpoint) through middleware, validators, and enforcement points to the final authorization decision. For each chain, record the ordered sequence of checks, the enforcement point names, and evidence from each link in the chain.
4. Extract guardrail configurations: rate limiters, input size validators, content filters, prompt injection detectors, and output sanitizers. For each guardrail, record the configuration parameters (limits, thresholds), the enforcement location, and file path with line range evidence.
5. Cross-reference discovered enforcement surfaces against upstream `SERVICE_ENTRYPOINTS.json` to map which endpoints are protected by which enforcement points, and against `EVENTBUS_SURFACE.json` to identify event-driven enforcement triggers.
6. Validate coverage: check that every public endpoint discovered in upstream artifacts has at least one enforcement point in its call chain. Flag unprotected endpoints with `status: no_enforcement_detected`.
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
- Enforcement logic embedded in dynamically loaded plugins or middleware registered at runtime: emit with `enforcement_type: dynamic` and `status: needs_review` with evidence citing the registration pattern.
- Guardrail configuration loaded from external source (environment variable, remote config) with no default visible in code: emit with configuration values set to `UNKNOWN` and `missing_evidence_reason: external_config`.

## Legacy Context (for intent only; never as evidence)
```markdown
Goals: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json

Prompt:
- Extract:
  - boundary checks, refusal artifacts, gating chains
  - where it's invoked (middleware, validators, routers, CLI paths)
```
