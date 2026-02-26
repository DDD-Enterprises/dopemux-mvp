# PROMPT_C2

## Goal
Produce `C2` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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

## Extraction Procedure
1. Scan `src/**` and `services/**` for event bus implementations and adapters: classes or modules that provide `publish`, `emit`, `send`, `subscribe`, `on`, `listen`, or `register_handler` methods. For each bus component, record the class/module name, transport mechanism (Redis Pub/Sub, in-process, HTTP webhook, etc.), and file path with line range evidence.
2. Extract all literal event names and topic strings by scanning for string constants passed to publish/emit/subscribe calls, topic configuration in YAML/JSON files, and enum definitions of event types. Record each event name with the declaring file path and line range.
3. Identify all producer call sites: locations where events are published or emitted. For each producer, record the caller function/method, the event name or topic, the payload shape (if inferable from arguments), and the file path with line range evidence. Emit these as `EVENT_PRODUCERS.json` items.
4. Identify all consumer registrations: locations where event handlers are registered via decorators (`@on_event`, `@subscribe`), method calls (`bus.subscribe(topic, handler)`), or configuration entries. For each consumer, record the handler function, the subscribed event name, and the file path with line range evidence. Emit these as `EVENT_CONSUMERS.json` items.
5. Cross-reference producers against consumers to identify orphaned events (produced but never consumed) and unproduced subscriptions (consumed but never produced). Flag these with `status: orphaned_producer` or `status: unmatched_consumer` respectively.
6. Cross-reference discovered bus components and event wiring against upstream `SERVICE_ENTRYPOINTS.json` and `CODE_PARTITIONS.json` to tag each item with its owning service and partition.
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
- Event name used in a publish call is a dynamic expression (variable, f-string, or concatenation) rather than a literal string: emit with `event_name: UNKNOWN` and `status: dynamic_topic` with evidence citing the expression.
- Consumer handler registered for a wildcard or pattern topic (e.g., `events.*`): emit with the pattern as `event_name` and `status: wildcard_subscription` with evidence.

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
