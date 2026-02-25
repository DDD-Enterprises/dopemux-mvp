# PROMPT_A6

## Goal
Produce `A6` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `.claude/**`
- `.github/**`
- `.taskx/**`
- `config/**`
- `scripts/**`
- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `README.md`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`
- `REPO_MCP_SERVER_DEFS.json`
- `REPO_MCP_PROXY_SURFACE.json`
- `REPO_ROUTER_SURFACE.json`
- `REPO_HOOKS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_COMPOSE_SERVICE_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_COMPOSE_SERVICE_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_COMPOSE_SERVICE_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Locate all compose files (`compose.yml`, `docker-compose*.yml`) within in-scope source roots and extract the top-level `services` mapping from each.
2. For each declared service, extract explicit properties: `image`, `build`, `environment`/`env_file`, `ports`, `volumes`, `depends_on`, `networks`, `command`, `entrypoint`, and `healthcheck`. Record the source file path and line range as evidence for every property.
3. Extract top-level `networks` and `volumes` definitions as separate graph nodes; link each service node to the networks and volumes it references via graph edges.
4. Build the service dependency DAG from `depends_on` declarations; create a directed edge for each dependency with the condition (e.g., `service_healthy`, `service_started`) attached as edge metadata.
5. Cross-reference extracted service names against `services/registry.yaml` (when present) and upstream `REPOCTRL_INVENTORY.json` to validate service identity and detect compose files not covered by the scan scope.
6. Resolve environment variable references (`${VAR}`, `${VAR:-default}`) to variable names only; do not resolve values. Record each variable name with evidence from the compose file line where it appears.
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
- Circular `depends_on` references: detect cycles in the service DAG and emit all cycle-participant services with `status: circular_dependency` and evidence citing each `depends_on` declaration in the cycle.
- Multiple compose files with conflicting service definitions: when the same service name appears in more than one compose file, emit both with distinct IDs incorporating the source path and mark `status: needs_review`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A6 - Compose Service Graph

Phase: A
Step: A6

Outputs:
- REPO_COMPOSE_SERVICE_GRAPH.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_COMPOSE_SERVICE_GRAPH.json",
  "phase": "A",
  "step": "A6",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "service:<name>",
      "service_name": "...",
      "image": "...",
      "build": "...",
      "env": ["..."],
      "ports": ["..."],
      "volumes": ["..."],
      "depends_on": ["..."],
      "networks": ["..."],
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Compose services: image/build, env names, volumes, ports, depends_on
- Networks and volumes
- Do not infer service meaning unless explicitly named
```
