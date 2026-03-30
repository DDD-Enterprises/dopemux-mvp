# PROMPT_A1

## Goal
Produce `A1` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`

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

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the instruction partition as primary scan surface.
2. Scan `.claude/`, `.vibe/`, `.dopemux/`, and `.github/` for instruction-bearing files:
   - Identify `.md`, `.json`, `.yaml`, and `.txt` files containing keywords: "system instructions", "persona", "prompt template", "workflow playbook", "agent rules".
   - Categorize each source by `kind`: `claude_system`, `agent_profile`, `tooling_instructions`, `prompt_template`, or `workflow_playbook`.
3. Extract literal tool references: scan instruction text for mentions of "conport", "serena", "mcp", "litellm", "taskx", and "dope-context".
4. Identify service references: scan for "dashboard", "orchestrator", "proxy", "brainz", or "supervisor".
5. Extract specific behavior and boundary claims:
   - `declared_behaviors`: capture literal "Should..." or "Always..." statements.
   - `declared_boundaries`: capture "Must NOT...", "Never...", or "Forbidden" constraints.
   - `declared_dataflows`: capture descriptions of data movement between components.
6. Build relationship graph: map instruction files to the tools and services they explicitly mention or claim to control.
7. For each REPO_INSTRUCTION_SURFACE item, populate `id`, `kind`, `scope`, and mandatory `evidence` (path, line_range, excerpt).
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path|symbol|name).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID.
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PHASE A1 — INSTRUCTION SURFACES (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_INSTRUCTION_SURFACE.json + REPO_INSTRUCTION_REFERENCES.json

Hard rules:
- Extract ONLY what is explicitly present in files.
- Every extracted item MUST include evidence: {path, anchor_excerpt<=200 chars}.
- No guessing. If unclear, record UNKNOWN with evidence showing ambiguity.

Inputs:
- Partition content from A0 P0 partitions: instruction docs, agent files, custom instructions directories.

Task:
1) Build REPO_INSTRUCTION_SURFACE.json:
   Identify all instruction-bearing files and normalize into:
   - instruction_sources[] items:
     - id (stable, e.g., INSTR_0001)
     - path
     - kind (one of: "claude_system", "agent_profile", "tooling_instructions", "prompt_template", "workflow_playbook", "other")
     - scope (repo-wide / project-specific / tool-specific)
     - referenced_tools (list of strings found literally: e.g., "conport", "serena", "mcp", "litellm", "taskx")
     - declared_behaviors (list of short literal statements, each with anchor_excerpt)
     - declared_boundaries (list, each with anchor_excerpt)
     - declared_dataflows (list, each with anchor_excerpt)
   Determinism: sort by path, then by first appearance.

2) Build REPO_INSTRUCTION_REFERENCES.json:
   A cross-reference map of “instruction mentions -> targets”.
   Extract literal references to:
   - services (conport, serena, dope-context, dashboard, orchestrator, proxy)
   - MCP servers/tools
   - router/provider ladders
   - scripts/commands
   Output:
   - references[]:
     - ref_type ("service"|"command"|"file_p
```
