# PROMPT_A99

## Goal
Produce `A99` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `.vibe/**`
- `.claude/**`
- `.dopemux/**`
- `.github/**`
- `.githooks/**`
- `.taskx/**`
- `mcp-proxy-config.copilot.yaml`
- `compose/**`
- `config/**`
- `configs/**`
- `docker/**`
- `scripts/**`
- `tools/**`

- `installers/**`
- `ops/**`





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
- `REPO_COMPOSE_SERVICE_GRAPH.json`
- `REPO_LITELLM_SURFACE.json`
- `REPO_TASKX_SURFACE.json`
- `REPO_IMPLICIT_BEHAVIOR_HINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`
- `REPO_MCP_SERVER_DEFS.json`
- `REPO_MCP_PROXY_SURFACE.json`
- `REPO_ROUTER_SURFACE.json`
- `REPO_HOOKS_SURFACE.json`
- `REPO_IMPLICIT_BEHAVIOR_HINTS.json`
- `REPO_COMPOSE_SERVICE_GRAPH.json`
- `REPO_LITELLM_SURFACE.json`
- `REPO_LEANTIME_SURFACE.json`
- `REPO_TASKX_SURFACE.json`
- `REPOCTRL_NORM_MANIFEST.json`
- `REPOCTRL_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_INSTRUCTION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_INSTRUCTION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_INSTRUCTION_REFERENCES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_INSTRUCTION_REFERENCES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_MCP_SERVER_DEFS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_MCP_SERVER_DEFS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_MCP_PROXY_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_MCP_PROXY_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_ROUTER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_ROUTER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_HOOKS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_HOOKS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_IMPLICIT_BEHAVIOR_HINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_IMPLICIT_BEHAVIOR_HINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_COMPOSE_SERVICE_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_COMPOSE_SERVICE_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_LITELLM_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_LITELLM_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_LEANTIME_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_LEANTIME_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_TASKX_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_TASKX_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPOCTRL_NORM_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPOCTRL_NORM_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPOCTRL_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPOCTRL_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream A-phase artifacts (A1-A13) and verify `ItemList` schema compliance and ID uniqueness.
2. Perform deterministic merge for each target output:
   - `REPO_INSTRUCTION_SURFACE.json`: merge all items from A1, sorting by `(path, line_range, id)`.
   - `REPO_MCP_SERVER_DEFS.json`: merge all items from A2.
   - `REPO_MCP_PROXY_SURFACE.json`: merge all items from A3.
   - `REPO_ROUTER_SURFACE.json`: merge all items from A4.
   - `REPO_HOOKS_SURFACE.json`: merge all items from A5.
   - `REPO_COMPOSE_SERVICE_GRAPH.json`: merge all items from A6.
   - `REPO_LITELLM_SURFACE.json`: merge all items from A7.
   - `REPO_TASKX_SURFACE.json`: merge all items from A8.
   - `REPO_IMPLICIT_BEHAVIOR_HINTS.json`: merge all items from A9.
   - `REPO_LEANTIME_SURFACE.json`: merge all items from A10.
3. Generate `REPOCTRL_NORM_MANIFEST.json`:
   - Enumerate all merged artifacts.
   - Record `artifact_name`, `sha256` hash of content, `item_count`, and `writer_step_id: A99`.
4. Generate `REPOCTRL_QA.json`:
   - Perform "missing-artifact" checks: flag any expected output names not successfully merged.
   - Perform "shadow/collision" checks: identify items with identical IDs but conflicting fields.
   - Perform "evidence-gap" checks: identify items with `UNKNOWN` fields or missing evidence anchors.
   - Record `status`, `checks` (list of pass/fail), and `issues` (list of specific gaps).
5. Ensure absolute determinism: no timestamps, no `run_id`, stable sort by ID then path, reproducible byte-for-byte output.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path|symbol|name).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID.
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A99 - Merge + QA (Repo Control Plane)

Phase: A
Step: A99

Intent summary:
- Merge upstream A-phase artifacts into the exact declared output artifact names for this step.
- Produce a deterministic manifest artifact (`REPOCTRL_NORM_MANIFEST.json`).
- Produce a deterministic QA artifact (`REPOCTRL_QA.json`) summarizing presence, gaps, and merge quality.

Hard rules:
1) Do NOT invent. If not present, write `UNKNOWN`.
2) Every non-trivial field must include evidence with exact source anchors.
3) Emit ONLY the declared artifact names and keep them deterministic.
4) Legacy examples must never override the schema, outputs, or determinism rules above.
```
