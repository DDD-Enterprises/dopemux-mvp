# PROMPT_C8

## Goal
Produce `C8` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

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
  - `SECRETS_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C8`
    - `id_rule`: `SECRETS_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk_type, severity, affected_symbol, secret_category, exposure_vector, mitigation_present, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema — DETERMINISM_RISK_LOCATIONS
```json
{
  "id": "DETERMINISM_RISK_LOCATIONS:<hash>",
  "risk_type": "random_call|uuid_generation|timestamp_dependency|dict_iteration|set_iteration|floating_point|os_dependent|locale_dependent",
  "severity": "critical|high|medium|low",
  "affected_symbol": "<function or method containing the non-deterministic call>",
  "non_deterministic_call": "<exact function call, e.g. 'random.choice(items)'>",
  "in_critical_path": true,
  "mitigation_present": false,
  "mitigation_description": "<description of seed/mock/override if present, or null>",
  "path": "<repo-relative path>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

#### Determinism Risk Type Definitions
- **random_call**: Use of `random.*`, `secrets.*`, `numpy.random.*` without seed control
- **uuid_generation**: Use of `uuid.uuid4()` or `uuid.uuid1()` producing non-reproducible IDs
- **timestamp_dependency**: Use of `datetime.now()`, `time.time()`, `time.monotonic()` in output-affecting logic
- **dict_iteration**: Reliance on dictionary ordering in Python < 3.7 patterns or cross-process serialization
- **set_iteration**: Iteration over sets where order affects output
- **floating_point**: Floating-point arithmetic in equality checks or hash computation
- **os_dependent**: Path separators, line endings, or locale-dependent string operations
- **locale_dependent**: String comparison, sorting, or formatting affected by locale settings

### Item Schema — IDEMPOTENCY_RISK_LOCATIONS
```json
{
  "id": "IDEMPOTENCY_RISK_LOCATIONS:<hash>",
  "risk_type": "db_write_no_upsert|file_append_no_dedup|counter_increment|side_effect_on_retry|missing_idempotency_key|duplicate_event_emission",
  "severity": "critical|high|medium|low",
  "affected_symbol": "<function or method with idempotency risk>",
  "operation": "<description of the non-idempotent operation>",
  "mitigation_present": false,
  "mitigation_description": "<idempotency key, upsert, dedup logic, or null>",
  "path": "<repo-relative path>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

#### Idempotency Risk Type Definitions
- **db_write_no_upsert**: INSERT/UPDATE without ON CONFLICT or unique constraint guard
- **file_append_no_dedup**: File writes using append mode without deduplication checks
- **counter_increment**: Atomic counter increments that double-count on retry
- **side_effect_on_retry**: External API calls or notifications that fire again on retry
- **missing_idempotency_key**: Endpoint or handler that accepts retries without idempotency token
- **duplicate_event_emission**: Event bus publish that emits duplicates on handler retry

### Item Schema — CONCURRENCY_RISK_LOCATIONS
```json
{
  "id": "CONCURRENCY_RISK_LOCATIONS:<hash>",
  "risk_type": "shared_mutable_state|race_condition|deadlock_potential|thread_unsafe_call|async_blocking|missing_lock|global_state_mutation",
  "severity": "critical|high|medium|low",
  "affected_symbol": "<function or method with concurrency risk>",
  "shared_resource": "<name of shared state, global variable, or file>",
  "access_pattern": "read_write|write_write|read_only",
  "mitigation_present": false,
  "mitigation_description": "<lock, queue, atomic op, or null>",
  "path": "<repo-relative path>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

#### Concurrency Risk Type Definitions
- **shared_mutable_state**: Module-level or class-level mutable variables accessed from multiple threads/tasks
- **race_condition**: Check-then-act patterns without synchronization (TOCTOU)
- **deadlock_potential**: Multiple locks acquired in inconsistent order
- **thread_unsafe_call**: Calling non-thread-safe functions (e.g., `sqlite3` from multiple threads)
- **async_blocking**: Synchronous blocking calls inside `async def` (e.g., `time.sleep`, `requests.get`)
- **missing_lock**: Concurrent writes to shared resource without mutex/semaphore
- **global_state_mutation**: Mutation of module-level dictionaries, lists, or objects during request handling

### Item Schema — SECRETS_RISK_LOCATIONS
```json
{
  "id": "SECRETS_RISK_LOCATIONS:<hash>",
  "risk_type": "hardcoded_secret|env_var_no_default|secret_in_log|secret_in_url|unencrypted_storage|weak_credential|exposed_in_error",
  "severity": "critical|high|medium|low",
  "affected_symbol": "<function or location containing the risk>",
  "secret_category": "api_key|oauth_token|db_password|jwt_secret|encryption_key|webhook_secret|generic_credential",
  "exposure_vector": "<how the secret could leak: log, error message, URL parameter, git history, etc.>",
  "mitigation_present": false,
  "mitigation_description": "<vault, env var, .gitignore rule, or null>",
  "path": "<repo-relative path>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

#### Secrets Risk Type Definitions
- **hardcoded_secret**: Literal secret value in source code (API keys, passwords, tokens)
- **env_var_no_default**: `os.environ["KEY"]` without fallback — crashes on missing secret
- **secret_in_log**: Secret values passed to `logger.*()` or `print()` calls
- **secret_in_url**: Secrets embedded in URL query parameters or path segments
- **unencrypted_storage**: Secrets written to disk/database without encryption
- **weak_credential**: Default passwords, empty strings, or well-known test credentials
- **exposed_in_error**: Secrets leaked in exception messages or HTTP error responses

#### Severity Thresholds (all risk types)
- **critical**: Secret exposed in production-reachable code path or data corruption risk from concurrency bug
- **high**: Risk in code that runs on every request/event, or secret with broad access scope
- **medium**: Risk in periodic/background code, or secret with narrow scope
- **low**: Risk in test/dev-only code, or theoretical risk with existing partial mitigation

### Worked Example (DETERMINISM_RISK_LOCATIONS)
```json
{
  "id": "DETERMINISM_RISK_LOCATIONS:e8c4f2a1",
  "risk_type": "random_call",
  "severity": "high",
  "affected_symbol": "_select_phase_sample",
  "non_deterministic_call": "random.sample(files, sample_size)",
  "in_critical_path": true,
  "mitigation_present": true,
  "mitigation_description": "Replaced with hash-based _deterministic_phase_sample in bundle branch",
  "path": "services/repo-truth-extractor/run_extraction_v5.py",
  "line_range": [13690, 13698],
  "status": "ok",
  "evidence": [{"path": "services/repo-truth-extractor/run_extraction_v5.py", "line_range": [13690, 13694], "excerpt": "def _deterministic_phase_sample(files, n, seed_salt):\n    scored = sorted(files, key=lambda f: hashlib.sha256("}]
}
```

## Extraction Procedure
1. Load upstream inventory and partitions; use the determinism, idempotency, and concurrency partition as primary scan surface
2. Extract determinism, idempotency, and concurrency facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted determinism, idempotency, and concurrency elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DETERMINISM_SURFACES item, populate `id`, required fields, and `evidence`
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
- Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`
- Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`

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
