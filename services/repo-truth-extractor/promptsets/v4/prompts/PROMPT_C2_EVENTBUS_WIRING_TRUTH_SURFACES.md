# PROMPT_C2

## Goal
Produce `C2` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EVENTBUS_SURFACE.json`
- `EVENT_PRODUCERS.json`
- `EVENT_CONSUMERS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
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

### Item Schema — EVENTBUS_SURFACE
```json
{
  "id": "EVENTBUS_SURFACE:<hash>",
  "event_name": "<literal event/topic name string>",
  "channel": "<bus/adapter name, e.g. 'event_bus', 'redis_pubsub', 'celery'>",
  "transport": "in_process|redis|rabbitmq|kafka|http_webhook|unknown",
  "is_async": true,
  "retry_policy": "none|fixed_delay|exponential_backoff|custom",
  "max_retries": "<integer or null if unlimited/unset>",
  "dlq_target": "<dead-letter queue/topic name, or null if none>",
  "ordering_guarantee": "none|fifo|key_based|partition_ordered",
  "payload_schema_ref": "<path to Pydantic model or TypedDict defining payload, or null>",
  "path": "<repo-relative path to bus/adapter definition>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Transport Type Definitions
- **in_process**: Events dispatched via function calls within a single process (e.g., `EventBus.emit()`)
- **redis**: Events published/subscribed via Redis Pub/Sub or Streams
- **rabbitmq**: Events routed via RabbitMQ exchanges/queues
- **kafka**: Events produced/consumed via Kafka topics
- **http_webhook**: Events delivered via HTTP POST callbacks
- **unknown**: Transport mechanism cannot be determined from code evidence

### Retry Policy Definitions
- **none**: No retry on delivery failure; fire-and-forget
- **fixed_delay**: Retry after a constant interval (e.g., 5s between retries)
- **exponential_backoff**: Retry with increasing delay (e.g., 1s, 2s, 4s, 8s...)
- **custom**: Application-defined retry logic (document in description)

### Ordering Guarantee Definitions
- **none**: No ordering; events may arrive in any order
- **fifo**: Strict first-in-first-out ordering for all events on this channel
- **key_based**: Ordering guaranteed within a partition key (e.g., by entity ID)
- **partition_ordered**: Ordering within partitions but not across them

### Item Schema — EVENT_PRODUCERS
```json
{
  "id": "EVENT_PRODUCERS:<hash>",
  "event_name": "<event/topic name emitted>",
  "producer_symbol": "<function or method that emits>",
  "producer_service": "<service name from registry.yaml, or module path>",
  "call_pattern": "emit|publish|send|dispatch|fire|custom",
  "path": "<repo-relative path to call site>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Item Schema — EVENT_CONSUMERS
```json
{
  "id": "EVENT_CONSUMERS:<hash>",
  "event_name": "<event/topic name consumed>",
  "consumer_symbol": "<handler function or method>",
  "consumer_service": "<service name from registry.yaml, or module path>",
  "registration_pattern": "decorator|subscribe_call|handler_class|config_binding",
  "is_blocking": true,
  "path": "<repo-relative path to handler registration>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Worked Example
```json
{
  "id": "EVENTBUS_SURFACE:a3f1b2c4",
  "event_name": "task.completed",
  "channel": "event_bus",
  "transport": "in_process",
  "is_async": false,
  "retry_policy": "none",
  "max_retries": null,
  "dlq_target": null,
  "ordering_guarantee": "none",
  "payload_schema_ref": "src/dopemux/events/types.py::TaskCompletedEvent",
  "path": "services/dopecon-bridge/dopecon_bridge/event_bus.py",
  "line_range": [15, 42],
  "status": "ok",
  "evidence": [{"path": "services/dopecon-bridge/dopecon_bridge/event_bus.py", "line_range": [15, 20], "excerpt": "class EventBus:\n    def emit(self, event_name: str, payload: dict):"}]
}
```

## Extraction Procedure
1. Load upstream inventory and partitions; use the eventbus wiring partition as primary scan surface
2. Extract eventbus wiring facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted eventbus wiring elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each EVENTBUS_SURFACES item, populate `id`, required fields, and `evidence`
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
Goals: EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json

Prompt:
- Extract:
  - event bus implementations/adapters
  - literal event names/topics (string constants)
  - producer call sites
  - consumer registration/handlers
```
