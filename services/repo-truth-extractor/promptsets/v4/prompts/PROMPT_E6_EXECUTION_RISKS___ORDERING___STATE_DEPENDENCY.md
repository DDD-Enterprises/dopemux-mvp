# PROMPT_E6

## Goal
Produce `E6` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- `EXEC_STARTUP_GRAPH.json`
- `EXEC_RUNTIME_MODES.json`
- `EXEC_MODE_DELTA_REPORT.json`
- `EXEC_ARTIFACT_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_RISK_FACTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_RISK_FACTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E6`
    - `id_rule`: `EXEC_RISK_FACTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`, `SERVICE_STARTUP_GRAPH.json`, and `ENV_LOADING_CONFIG_CHAIN.json`.
2.  **Scan for Port Conflicts**:
    *   Identify hardcoded ports in code and config: `port=8000`, `EXPOSE 8080`, `bind: "0.0.0.0:5000"`.
    *   Cross-reference with `docker-compose.yml` to find overlapping host port mappings.
3.  **Identify Startup Race Conditions**:
    *   Detect services that share a common state file or DB but lack `depends_on` or health-check guards.
    *   Find non-atomic file writes (`open('w').write()`) used for shared state.
4.  **Detect Order-of-Execution Risks**:
    *   Identify circular dependencies in `docker-compose.yml`.
    *   Find shell scripts that execute background tasks (`&`) without `wait` or status checking.
5.  **Analyze Resource Exhaustion Risks**:
    *   Scan for unbounded loops or recursions in execution entrypoints.
    *   Identify missing `memory` or `cpu` limits in `docker-compose.yml`.
6.  **Build Risk Items**: For each risk, record:
    *   `risk_type`: e.g., `port_conflict`, `race_condition`, `circular_dependency`.
    *   `severity`: `critical`, `high`, `medium`, `low`.
    *   `mitigation_evidence`: Any existing code meant to prevent this risk (e.g., a `try/except` around bind).
7.  **Evidence Anchoring**: Attach exact excerpts for the risk source and any mitigation logic.
8.  **Validate**: Sort by severity then path. Emit `EXECUTION_RISKS_REGISTER.json`.
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
# PROMPT_E6 — EXECUTION RISKS / ORDERING / STATE DEPENDENCY

TASK: Extract ordering hazards and state coupling points.

OUTPUTS:
	•	EXEC_RISK_FACTS.json
```
