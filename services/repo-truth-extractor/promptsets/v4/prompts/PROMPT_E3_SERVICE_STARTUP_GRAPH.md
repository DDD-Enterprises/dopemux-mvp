# PROMPT_E3

## Goal
Produce `E3` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `compose.yml`
- `docker-compose*.yml`
- `Makefile`
- `src/**`
- Upstream normalized artifacts available to this step:
- `EXEC_INVENTORY.json`
- `EXEC_PARTITIONS.json`
- `EXEC_BOOTSTRAP_COMMANDS.json`
- `EXEC_ENV_CHAIN.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_STARTUP_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_STARTUP_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E3`
    - `id_rule`: `EXEC_STARTUP_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`. Focus on `docker-compose.yml`, `Dockerfile`, and systemd/init scripts.
2.  **Extract Service Dependencies**:
    *   Parse `docker-compose.yml` for `depends_on`, `links`, and `networks`.
    *   Identify dependency types: `service_started`, `service_healthy`, `service_completed_successfully`.
3.  **Identify Wait-for Patterns**:
    *   Scan entrypoint scripts (`*.sh`) for `wait-for-it.sh`, `nc -z`, or `while ! curl ...; do sleep 1; done`.
    *   Extract timeout and retry logic associated with these waits.
4.  **Extract Health Checks**:
    *   Record `test`, `interval`, `timeout`, and `retries` from `docker-compose.yml` or `Dockerfile`.
5.  **Build Graph Nodes**: For each service, record:
    *   `service_id`: The canonical name from the registry or compose file.
    *   `startup_command`: The literal `command:` or `ENTRYPOINT`.
    *   `dependencies`: List of parent service IDs and condition types.
6.  **Evidence Anchoring**: Attach exact line ranges for every dependency and health check definition.
7.  **Validate**: Ensure graph is a DAG (note circulars in `coverage_notes`). Emit `SERVICE_STARTUP_GRAPH.json`.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_E3 — SERVICE STARTUP GRAPH

TASK: Produce a service start graph from compose/scripts.

OUTPUTS:
	•	EXEC_STARTUP_GRAPH.json
```
