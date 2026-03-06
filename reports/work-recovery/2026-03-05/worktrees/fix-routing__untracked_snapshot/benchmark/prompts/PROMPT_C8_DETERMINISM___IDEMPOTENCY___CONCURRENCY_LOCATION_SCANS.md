# PROMPT_C8

## Goal
Produce `C8` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `SECRETS_RISK_LOCATIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
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
  - `SECRETS_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C8`
    - `id_rule`: `SECRETS_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream artifacts through `API_DASHBOARD_SURFACE.json`; use the full code inventory as the scan surface for risk location discovery.
2. Scan for determinism risks: search for calls to `random`, `time.time()`, `uuid4()`, `datetime.now()`, `os.getpid()` in critical code paths (not test/debug); for each, assess whether the non-determinism affects output reproducibility and record `severity`.
3. Scan for concurrency risks: identify global mutable state, shared variables without synchronization, race condition patterns (check-then-act without locks), and thread-unsafe singleton access; record the risk description and `location`.
4. Scan for idempotency risks: locate DB writes without idempotency keys (INSERT without ON CONFLICT), retry logic with side effects, and state mutations that lack guard conditions; record the risk and affected operation.
5. Scan for secrets patterns: search for hardcoded API keys, tokens, passwords, and connection strings using regex patterns (`[A-Za-z0-9]{32,}`, `sk-`, `Bearer `, `password=`); exclude false positives in test fixtures and documentation.
6. For each risk item across all four outputs, populate `id` using the appropriate id_rule, `risk` (description), `severity` (critical|high|medium|low), `location` (path + line_range), and `evidence`.
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
- False positive secrets: if a pattern match triggers on a test fixture, example value, or hash constant, include with `severity: low` and `status: likely_false_positive` with evidence showing the non-sensitive context.
- Intentional non-determinism: if a non-deterministic call is used by design (e.g., `uuid4()` for generating unique IDs), emit with `severity: low` and `status: by_design` noting the intentional usage.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json

Prompt:
- Scan for:
  - Non-deterministic functions (random, time, uuid) in critical paths.
  - Concurrency risks (global state mutation, race conditions).
  - Idempotency risks (DB writes without keys, retries with side effects).
  - Secrets patterns (APi keys, tokens).
```
