# Prompt Bundle: Active Extraction Bundle 1

## Prompt
- prompt_id: rte_a_a0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A0
- short_name: Repo Control Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A0_REPO_CONTROL_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPOCTRL_INVENTORY.json, REPOCTRL_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A0

## Goal
Produce `A0` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `components/**`
- `contracts/**`
- `dashboard/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`




- `compose.yml`
- `docker-compose*.yml`
- `README.md`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPOCTRL_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A0`
    - `id_rule`: `REPOCTRL_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPOCTRL_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A0`
    - `id_rule`: `REPOCTRL_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan repo control-plane (`*.yaml`, `*.toml`, `*.json`, `docker-compose*`, `.claude/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the repo control-plane (`*.yaml`, `*.toml`, `*.json`, `docker-compose*`, `.claude/`) domain
3. Build REPO_CTRL_PARTITIONS by grouping files into logical categories with rationale
4. For each REPO_CTRL_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each REPO_CTRL_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
MODE: Mechanical extractor, zero interpretation.
INPUT: repo working tree (top-level), include hidden dirs shown in ls -la (not .git contents).
OUTPUT:
- REPOCTRL_INVENTORY.json: list files (path, ext, size, mtime, sha256 if available), plus first 30 non-empty lines for text.
- REPOCTRL_PARTITIONS.json: partitions by type:
  - instructions/prompts (CLAUDE.md, AGENTS.md, .claude/**, docs/** instruction files)
  - mcp/proxy configs (mcp-proxy-config*, start-mcp-servers.sh, compose/**)
  - hooks (.githooks/**, scripts called by hooks)
  - routers/provider ladders (litellm.config*, any router yaml/toml/json)
  - compose/service graphs (compose.yml, docker-compose*.yml, compose/**)
  - CI/gates (.github/**, pre-commit, ruff/mypy/pytest configs)
  - taskx surfaces (.taskx/**, .taskx-pin, task packets in repo)
RULES: JSON only. Every item must include path + line_range (or null if binary).
```

---

## Prompt
- prompt_id: rte_a_a1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A1
- short_name: Instruction Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A1_INSTRUCTION_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
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

---

## Prompt
- prompt_id: rte_a_a10
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A10
- short_name: Leantime Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A10_LEANTIME_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_LEANTIME_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A10 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A10

## Goal
Produce `A10` outputs for phase `A` by extracting the repository control-plane surfaces that configure or route Leantime integration behavior.
Capture only implementation facts that are directly evidenced in source and configuration files.

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

- `services/leantime-bridge/**`
- `compose.yml`
- `docker-compose*.yml`
- `src/dopemux/**`
- `.claude.json`
- `README.md`
- `installers/**`
- `ops/**`





- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_INSTRUCTION_SURFACE.json`
  - `REPO_MCP_SERVER_DEFS.json`
  - `REPO_MCP_PROXY_SURFACE.json`
  - `REPO_ROUTER_SURFACE.json`
  - `REPO_TASKX_SURFACE.json`
  - `REPO_COMPOSE_SERVICE_GRAPH.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
  - `services/registry.yaml`

## Outputs
- `REPO_LEANTIME_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contract:
  - `REPO_LEANTIME_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_LEANTIME_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, line_range, evidence`
- Capture these surfaces when evidenced:
  - Leantime service definitions and runtime ports
  - MCP transport wiring and endpoint URLs
  - Environment variable contracts
  - CLI command entrypoints that enable Leantime integration

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on Leantime integration surfaces.
2. Scan `services/leantime-bridge/**`, `compose.yml`, and `config/leantime/*.yaml` for service and network facts:
   - `leantime_service`: identify container name, image, and explicit `ports` (e.g., 80, 443, 8061).
   - `mcp_transport`: scan for "leantime" tools in `mcp-proxy-config.yaml` or `src/dopemux/mcp/leantime.py`.
   - `endpoint_urls`: identify literal Leantime API or webhook URLs (e.g., `LEANTIME_API_URL`).
3. Extract environment variable contracts: search for `LEANTIME_API_KEY`, `LEANTIME_DB_*`, `LEANTIME_URL`, or `LEANTIME_TOKEN`.
4. Identify CLI and workflow integration points:
   - Search for literal commands: `dopemux leantime sync`, `taskx --leantime`, or `leantime-bridge import`.
5. Build relationship graph: link the Leantime bridge service to the core Dopemux router, MCP proxy, and TaskX surfaces.
6. For each REPO_LEANTIME_SURFACE item, populate `id` (stable-hash of path|name), required fields, and `evidence`.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path|symbol|name).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A10 - Leantime Surface
Phase: A
Step: A10
Outputs:
- REPO_LEANTIME_SURFACE.json
Mode: extraction
Strict: evidence_only
```

---

## Prompt
- prompt_id: rte_a_a11
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A11
- short_name: Editor Integration Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A11_EDITOR_INTEGRATION_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: EDITOR_INTEGRATION_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A11 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A11

## Goal
Produce `A11` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Extract editor and IDE integration surfaces: configuration files, settings, extensions, and workspace definitions that control how code editors (VS Code, Cursor, Claude Code, Copilot) interact with the repository.

## Inputs
- Source scope (scan these roots first):
  - `.vibe/**`
  - `.claude/**`
  - `.dopemux/**`
  - `.github/**`
  - `.githooks/**`
  - `.taskx/**`
  - `mcp-proxy-config.copilot.yaml`
  - `mcp-proxy-config*.yaml`
  - `mcp-proxy-config.json`
  - `compose/**`
  - `config/**`
  - `configs/**`
  - `docker/**`
  - `installers/**`
  - `ops/**`
  - `scripts/**`
  - `tools/**`
  - `src/dopemux/claude/**`
  - `.vscode/**`
  - `.cursor/**`
  - `.editorconfig`
  - `*.code-workspace`
- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_INSTRUCTION_SURFACE.json`
  - `REPO_MCP_SERVER_DEFS.json`
  - `REPO_MCP_PROXY_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `EDITOR_INTEGRATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `EDITOR_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A11`
    - `id_rule`: `EDITOR_INTEGRATION_SURFACE:<stable-hash(path|editor_type|config_key)>`
    - `required_item_fields`: `id, editor_type, config_key, config_value, scope, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `editor_type` enum: `vscode | cursor | claude_code | copilot | editorconfig | workspace | other`
- `scope` enum: `workspace | user | project | global`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on editor and IDE integration surfaces.
2. Scan `.vscode/settings.json`, `.vscode/extensions.json`, and `.cursor/rules/` for editor-specific behaviors and constraints.
3. Scan `mcp-proxy-config*.yaml` and `mcp-proxy-config.json` for editor-facing MCP proxy configurations and tool bindings.
4. Extract Claude Code configuration facts: scan `.claude/config.json` and `claude_desktop_config.json` for tool registrations and agent profiles.
5. Identify Copilot instruction sets: scan `.github/copilot-instructions.md` and related YAML metadata for repository-wide AI guidance.
6. Parse `.editorconfig` for formatting contracts and `*.code-workspace` files for multi-root project definitions.
7. For each integration point, extract mandatory fields:
   - `editor_type`: categorize as `vscode`, `cursor`, `claude_code`, `copilot`, or `editorconfig`.
   - `config_key` and `config_value`: capture literal setting pairs (e.g., `"editor.formatOnSave": true`).
   - `scope`: classify as `workspace` (in-repo) or `project`.
8. Cross-reference with `REPO_MCP_SERVER_DEFS.json` to identify which MCP tools are explicitly bound to which editor interface.
9. For each EDITOR_INTEGRATION_SURFACE item, populate `id`, required fields, and `evidence`.
10. Build deterministic IDs using stable content keys (path|editor_type|config_key).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID.
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_a_a12
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A12
- short_name: Cli Command Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A12_CLI_COMMAND_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: CLI_COMMAND_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A12 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A12

## Goal
Produce `A12` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Extract the CLI command tree: all command-line interfaces, subcommands, argument signatures, and entry points defined in the repository.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/cli.py`
  - `src/dopemux/commands/**`
  - `src/dopemux/cli/**`
  - `scripts/**`
  - `tools/**`
  - `installers/**`
  - `.vibe/**`
  - `.claude/**`
  - `.dopemux/**`
  - `.github/**`
  - `.taskx/**`
  - `mcp-proxy-config.copilot.yaml`
  - `compose/**`
  - `config/**`
  - `configs/**`
  - `docker/**`
  - `ops/**`
  - `setup.py`
  - `setup.cfg`
  - `pyproject.toml`
- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_INSTRUCTION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `CLI_COMMAND_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `CLI_COMMAND_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A12`
    - `id_rule`: `CLI_COMMAND_SURFACE:<stable-hash(path|command_name|parent_command)>`
    - `required_item_fields`: `id, command_name, module_path, parent_command, arguments, subcommands, description, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `arguments` shape: `[{"name": "...", "type": "...", "required": bool, "default": "...", "help": "..."}]`
- `subcommands` shape: `["sub1", "sub2"]` referencing other item IDs

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the CLI command partition.
2. Scan `src/dopemux/cli.py` and `src/dopemux/commands/**/*.py` for framework-specific command definitions:
   - Identify Click decorators: `@click.command`, `@click.group`, `@click.option`, `@click.argument`.
   - Identify Typer decorators: `@app.command`, `@app.callback`.
   - Identify argparse patterns: `argparse.ArgumentParser()` and `.add_argument()` calls.
3. Extract mandatory command metadata:
   - `command_name`: the literal string name (e.g., "run", "sync", "audit").
   - `parent_command`: identify the group or parent parser ID.
   - `arguments`: extract name, type, required status, and default values for every option/argument.
   - `description`: extract from docstrings or the `help` parameter in the decorator.
4. Scan `pyproject.toml`, `setup.py`, and `setup.cfg` for `console_scripts` or `[project.scripts]` entry points.
5. Scan `scripts/` and `tools/` for executable standalone scripts containing `#!/usr/bin/env` and argument parsing logic.
6. Build command tree: map parent-child relationships between groups and subcommands to represent the full hierarchy.
7. For each CLI_COMMAND_SURFACE item, populate `id` (stable-hash of path|command_name|parent_command), required fields, and `evidence`.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path|symbol|name).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID.
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_a_a13
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A13
- short_name: Hook Contract Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A13_HOOK_CONTRACT_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: HOOK_CONTRACT_SURFACE.json, EVENT_FLOW_GRAPH.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A13 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A13

## Goal
Produce `A13` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Extract hook contracts and event flow graphs: map every hook trigger to its handler, event types, transport mechanism, and lifecycle phase to produce a complete event envelope model.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/hooks/**`
  - `src/dopemux/mcp/hooks.py`
  - `src/dopemux/events/**`
  - `src/dopemux/event_bus.py`
  - `.claude/hooks/**`
  - `.githooks/**`
  - `.vibe/**`
  - `.claude/**`
  - `.dopemux/**`
  - `.github/**`
  - `.taskx/**`
  - `mcp-proxy-config.copilot.yaml`
  - `compose/**`
  - `config/**`
  - `configs/**`
  - `docker/**`
  - `installers/**`
  - `ops/**`
  - `scripts/**`
  - `tools/**`
- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_HOOKS_SURFACE.json`
  - `REPO_MCP_SERVER_DEFS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `HOOK_CONTRACT_SURFACE.json`
- `EVENT_FLOW_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `HOOK_CONTRACT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A13`
    - `id_rule`: `HOOK_CONTRACT_SURFACE:<stable-hash(path|trigger_source|handler_path)>`
    - `required_item_fields`: `id, trigger_source, handler_path, event_types, transport_mechanism, lifecycle_phase, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENT_FLOW_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A13`
    - `id_rule`: `EVENT_FLOW_GRAPH:<stable-hash(source|target|event_type)>`
    - `required_item_fields`: `id, source, target, event_type, transport, direction, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `lifecycle_phase` enum: `pre_launch | post_launch | on_message | on_complete | on_error`
- `transport_mechanism` enum: `eventbus | direct_call | webhook | mcp_tool | file_watch | signal | other`
- `direction` enum: `producer_to_consumer | request_response | broadcast | pub_sub`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json`, `REPOCTRL_PARTITIONS.json`, and `REPO_HOOKS_SURFACE.json`.
2. Scan `src/dopemux/hooks/**/*.py` and `src/dopemux/mcp/hooks.py` for registration and handler patterns:
   - Search for decorators: `@hook`, `@on_event`, `@register_handler`.
   - Search for registration calls: `event_bus.subscribe()`, `hooks.add()`, `callback_manager.register()`.
3. Map every hook trigger to its operational contract:
   - `trigger_source`: identify the event ID or condition that fires the hook.
   - `handler_path`: locate the function or script that executes on trigger.
   - `event_types`: identify the literal event names (e.g., `TASK_CREATED`, `GIT_PRE_COMMIT`).
   - `transport_mechanism`: categorize as `eventbus`, `direct_call`, `webhook`, `mcp_tool`, or `signal`.
   - `lifecycle_phase`: identify phase (e.g., `pre_launch`, `post_launch`, `on_message`, `on_error`).
4. Scan `src/dopemux/event_bus.py` and `src/dopemux/events/*.py` to build the `EVENT_FLOW_GRAPH`:
   - Identify `producers`: where `event_bus.publish()` or `emit()` is called.
   - Identify `consumers`: where handlers are registered via subscription.
   - Trace flow from `source` component to `target` component per `event_type`.
5. Build deterministic IDs using stable content keys (path|trigger_source|handler_path).
6. Attach evidence to every non-derived field, anchoring to both the trigger registration AND the handler definition.
7. Normalize arrays by stable sort keys; deduplicate by ID.
8. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
9. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_a_a2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A2
- short_name: Mcp Server Defs
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A2_MCP_SERVER_DEFS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_MCP_SERVER_DEFS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A2

## Goal
Produce `A2` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_MCP_SERVER_DEFS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_MCP_SERVER_DEFS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_MCP_SERVER_DEFS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the MCP server definition partition.
2. Scan `mcp-proxy-config.copilot.yaml`, `config/*.yaml`, and `.claude/*.json` for MCP server configurations:
   - Search for top-level keys: `mcpServers`, `mcp_servers`, or `servers`.
3. For each server entry found, extract mandatory fields:
   - `server_name`: the key or explicit `name` field.
   - `command`: the executable string (e.g., `node`, `python3`, `bash`).
   - `args`: the list of command-line arguments.
   - `env`: the list of environment variable names (record keys, omit values if they look like secrets).
   - `enabled`: boolean status if explicitly defined; assume `true` if undefined but present.
4. Scan `docker-compose.yml` and `compose/*.yml` for sidecar containers with labels containing "mcp" or "tool-server".
5. Extract per-server metadata:
   - `cwd` or `root`: allowed execution paths.
   - `capabilities`: any explicit mentions of "resources", "prompts", or "tools" offered.
6. Build relationship graph: link MCP servers to the configuration files where they are defined.
7. For each REPO_MCP_SERVER_DEFS item, populate `id` (mcp:<name>), required fields, and `evidence`.
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
# PROMPT: A2 - MCP Server Definitions

Phase: A
Step: A2

Outputs:
- REPO_MCP_SERVER_DEFS.json

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
  "artifact": "REPO_MCP_SERVER_DEFS.json",
  "phase": "A",
  "step": "A2",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp:<name>",
      "server_name": "...",
      "command": "...",
      "args": ["..."],
      "env": ["..."],
      "enabled": true,
      "source_path": "...",
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
- MCP server definitions: name, command, args, env var names, enabled/disabled, cwd/root/allowed paths if present
- Any explicit per-server capabilities/notes
- Source locations and config keys
```

---

## Prompt
- prompt_id: rte_a_a3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A3
- short_name: Mcp Proxy Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A3_MCP_PROXY_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_MCP_PROXY_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A3

## Goal
Produce `A3` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_MCP_PROXY_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_MCP_PROXY_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_MCP_PROXY_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the MCP proxy partition.
2. Scan `mcp-proxy-config.yaml`, `mcp-proxy-config.copilot.yaml`, and `configs/proxy/*.json` for proxy definitions.
3. Identify proxy endpoints: scan for `endpoint`, `url`, `listen`, `port`, or `host` fields.
4. Extract upstream targets and routing rules:
   - `upstream_targets`: search for `upstreams`, `targets`, `backends`, or `proxy_pass` blocks.
   - `routes`: identify path-to-server mappings (e.g., `/mcp/google-search` -> `google-search-server`).
5. Identify authentication and security handling:
   - `auth_method`: scan for `auth`, `api_key`, `bearer`, `token`, or `headers` keys.
6. Record routing logic: scan for explicit "search order", "fallback", or "retry" logic in the proxy config.
7. Build relationship graph: trace the flow from proxy endpoint to upstream MCP server targets.
8. For each REPO_MCP_PROXY_SURFACE item, populate `id` (mcp-proxy:<name_or_path>), required fields, and `evidence`.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path|symbol|name).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID.
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A3 - MCP Proxy Surface

Phase: A
Step: A3

Outputs:
- REPO_MCP_PROXY_SURFACE.json

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
  "artifact": "REPO_MCP_PROXY_SURFACE.json",
  "phase": "A",
  "step": "A3",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp-proxy:<name_or_path>",
      "proxy_name": "...",
      "endpoint": "...",
      "upstream_targets": ["..."],
      "routes": ["..."],
      "auth_method": "...",
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
- Proxy config between clients/Dopemux and MCP servers
- Endpoints, routing rules, upstream targets, auth handling (only if explicit)
- Config search order hints only if explicit
```

---

## Prompt
- prompt_id: rte_a_a4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A4
- short_name: Router Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A4_ROUTER_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_ROUTER_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A4

## Goal
Produce `A4` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_ROUTER_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_ROUTER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_ROUTER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the router partition.
2. Scan `litellm.config`, `config/router/*.yaml`, and `src/dopemux/router/**/*.py` for routing tables and model definitions.
3. Extract provider and model mappings:
   - Identify `model_list`, `routers`, or explicit model-to-provider mappings.
4. Identify routing triggers and logic:
   - `trigger`: scan for `if`, `when`, `tag`, `filter`, or `metadata` rules used for route selection.
   - `fallback_ladder`: identify `fallbacks`, `retry_models`, or sequential provider lists.
5. Extract operational policies:
   - `retry_policy`: scan for `retries`, `backoff`, or `retry_on` configuration.
   - `rate_limit_policy`: scan for `rpm`, `tpm`, `rate_limit`, or `quota` keys.
6. Identify named `profiles` (e.g., "fast-low-cost", "high-reasoning") and their associated model sets.
7. Build relationship graph: trace connections between triggers, providers, and fallback models.
8. For each ROUTER_SURFACE item, populate `id` (route:<stable_id>), required fields, and `evidence`.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path|symbol|name).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID.
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A4 - Repo Router Surface

Phase: A
Step: A4

Outputs:
- REPO_ROUTER_SURFACE.json

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
  "artifact": "REPO_ROUTER_SURFACE.json",
  "phase": "A",
  "step": "A4",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "route:<stable_id>",
      "provider": "...",
      "model": "...",
      "trigger": "...",
      "fallback_ladder": ["..."],
      "retry_policy": "...",
      "rate_limit_policy": "...",
      "profile": "...",
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
- Provider/model routing tables, fallback ladders, profiles, routing rules
- Any retry/backoff/rate-limit knobs if present
- Routing policy files if present
```

---

## Prompt
- prompt_id: rte_a_a5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A5
- short_name: Hooks Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A5_HOOKS_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_HOOKS_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A5

## Goal
Produce `A5` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `src/dopemux/hooks/**`
- `src/dopemux/mcp/hooks.py`

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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_HOOKS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_HOOKS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_HOOKS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, hook_name, hook_type, trigger, handler_path, is_blocking, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "REPO_HOOKS_SURFACE:<hash>",
  "hook_name": "<human-readable hook identifier>",
  "hook_type": "git_hook|claude_hook|github_action|fastapi_event|signal_handler|pre_commit|taskx_hook|launchd_trigger",
  "trigger": "<event or condition that fires the hook>",
  "handler_path": "<repo-relative path to handler script or function>",
  "handler_symbol": "<function name or script entrypoint, or null for whole-file scripts>",
  "command": "<literal command string executed, or null if code-based>",
  "is_blocking": true,
  "timeout_seconds": "<configured timeout, or null if none>",
  "invoked_paths": ["<repo-relative paths called by this hook>"],
  "path": "<repo-relative path to hook definition/registration>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Hook Type Definitions
- **git_hook**: Git hooks in `.githooks/` or `.git/hooks/` (pre-commit, pre-push, post-merge, etc.)
- **claude_hook**: Claude Code hooks defined in `.claude/settings.json` under `hooks` key with trigger/glob/command
- **github_action**: GitHub Actions workflows in `.github/workflows/` triggered by `on:` events
- **fastapi_event**: FastAPI lifecycle events registered via `@app.on_event()` or `app.add_event_handler()`
- **signal_handler**: OS signal handlers registered via `signal.signal()` or framework equivalents
- **pre_commit**: Pre-commit framework hooks in `.pre-commit-config.yaml`
- **taskx_hook**: TaskX/Dopemux hooks in `.taskx/` configuration or `src/dopemux/hooks/`
- **launchd_trigger**: macOS launchd-triggered scripts defined in plist files

### Worked Example
```json
{
  "id": "REPO_HOOKS_SURFACE:c4a8e2f1",
  "hook_name": "PrePush lint check",
  "hook_type": "claude_hook",
  "trigger": "PrePush",
  "handler_path": ".claude/settings.json",
  "handler_symbol": null,
  "command": "scripts/lint-docs.sh",
  "is_blocking": true,
  "timeout_seconds": null,
  "invoked_paths": ["scripts/lint-docs.sh"],
  "path": ".claude/settings.json",
  "line_range": [12, 18],
  "status": "ok",
  "evidence": [{"path": ".claude/settings.json", "line_range": [12, 18], "excerpt": "\"hooks\": {\"PrePush\": [{\"command\": \"scripts/lint-docs.sh\"}]}"}]
}
```

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the hooks partition.
2. Scan `.githooks/`, `.github/workflows/`, and `.pre-commit-config.yaml` for external hook triggers.
3. Scan `src/dopemux/hooks/**` and `src/dopemux/mcp/hooks.py` for internal hook registrations and decorators.
4. For each hook identified, extract mandatory fields:
   - `hook_type`: categorize as "git-hook", "pre-commit", "ci-pipeline", "task-hook", or "mcp-hook".
   - `trigger`: identify the triggering event (e.g., `git commit`, `cron`, `workflow_dispatch`, `on_task_start`).
   - `command`: extract the literal shell command string or python function name invoked.
   - `invoked_paths`: list file patterns the hook watches or modifies (e.g., `*.py`, `docs/**`).
5. Build relationship graph: link hooks to the files they monitor and the commands they execute.
6. For each HOOKS_SURFACE item, populate `id` (hook:<type>:<name>), required fields, and `evidence`.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path|symbol|name).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A5 - Repo Hooks Surface

Phase: A
Step: A5

Outputs:
- REPO_HOOKS_SURFACE.json

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
  "artifact": "REPO_HOOKS_SURFACE.json",
  "phase": "A",
  "step": "A5",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hook:<type>:<name>",
      "hook_type": "...",
      "trigger": "...",
      "command": "...",
      "invoked_paths": ["..."],
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
- Git hooks, pre-commit hooks, CI hooks, taskx/dopemux hooks
- Literal commands invoked, source file locations, triggering conditions if defined
```

---

## Prompt
- prompt_id: rte_a_a6
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A6
- short_name: Compose Service Graph
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A6_COMPOSE_SERVICE_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_COMPOSE_SERVICE_GRAPH.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A6 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A6

## Goal
Produce `A6` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the compose service graph partition.
2. Scan `compose.yml`, `docker-compose*.yml`, and `compose/*.yml` for service definitions and architecture maps.
3. For each service block found under `services:`, extract mandatory implementation facts:
   - `service_name`: the top-level service key.
   - `image` or `build`: extract the literal image tag or the local Dockerfile/context path.
   - `env`: list environment variable keys defined in `environment` or referenced in `env_file`.
   - `ports`: extract literal port mappings (e.g., "8080:80").
   - `volumes`: list source/target mount points and named volume references.
   - `depends_on`: capture explicit service dependencies and healthcheck requirements.
   - `networks`: list network aliases and driver types.
4. Identify top-level infrastructure definitions:
   - `networks`: scan for global network configurations and external flags.
   - `volumes`: scan for global volume drivers and local paths.
5. Build relationship graph: map services as `nodes` and `depends_on` or `network` links as `edges`.
6. For each COMPOSE_SERVICE_GRAPH item, populate `id` (service:<name>), required fields, and `evidence`.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path|symbol|name).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

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

---

## Prompt
- prompt_id: rte_a_a7
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A7
- short_name: Litellm Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A7_LITELLM_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_LITELLM_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A7 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A7

## Goal
Produce `A7` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_LITELLM_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_LITELLM_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_LITELLM_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on LiteLLM configuration surfaces.
2. Scan `litellm.config`, `config/litellm/*.yaml`, and `src/dopemux/router/litellm_proxy.py` for model and provider declarations.
3. For each LiteLLM configuration entry, extract mandatory facts:
   - `provider`: identify the target LLM provider (e.g., "openai", "anthropic", "vertex_ai").
   - `model`: extract the literal model string or alias (e.g., "gpt-4-turbo", "claude-3-opus").
   - `env_var_requirements`: list specific environment variable names (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
   - `budgets` and `rate_limits`: identify `max_budget`, `max_parallel_requests`, `rpm`, or `tpm` constraints.
   - `cache_settings`: identify cache type (redis, in-memory) and TTL if defined.
   - `logging_or_db`: identify `success_callback`, `failure_callback`, or `database_url` for telemetry.
4. Identify any explicit "proxy" or "server" endpoints defined in the LiteLLM config or compose files.
5. Build relationship graph: link models to their respective providers and environment variable requirements.
6. For each LITELLM_SURFACE item, populate `id` (litellm:<stable_id>), required fields, and `evidence`.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path|symbol|name).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A7 - Repo LiteLLM Surface

Phase: A
Step: A7

Outputs:
- REPO_LITELLM_SURFACE.json

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
  "artifact": "REPO_LITELLM_SURFACE.json",
  "phase": "A",
  "step": "A7",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "litellm:<stable_id>",
      "config_file": "...",
      "provider": "...",
      "model": "...",
      "env_var_requirements": ["..."],
      "budgets": ["..."],
      "rate_limits": ["..."],
      "cache_settings": ["..."],
      "logging_or_db": ["..."],
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
- LiteLLM config files/references, model/provider declarations
- Expected env var names only, budgets/rate limits/cache/logging/db settings if present
```

---

## Prompt
- prompt_id: rte_a_a8
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A8
- short_name: Taskx Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A8_TASKX_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_TASKX_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A8 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A8

## Goal
Produce `A8` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_TASKX_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_TASKX_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_TASKX_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on TaskX configuration and invocation surfaces.
2. Scan `.taskx/`, `task-packets/`, and `config/taskx/*.yaml` for TaskX metadata and packet definitions.
3. Identify TaskX invocations in scripts and workflows:
   - Search for literal command strings: `taskx run`, `taskx-cli`, or `python -m taskx`.
4. Extract concrete implementation facts:
   - `packet_path`: locate where task packets (CSV, JSON, YAML) are stored or generated.
   - `instruction_surfaces`: identify files or directories used for task-specific "custom instructions" or "prompts".
   - `operator_surface`: identify "operator profiles" or "agent definitions" used during execution.
5. Trace connections between task packets, the instructions they reference, and the operators invoked to process them.
6. Build relationship graph: map the flow from a task trigger to the final packet output.
7. For each TASKX_SURFACE item, populate `id` (taskx:<stable_id>), required fields, and `evidence`.
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
# PROMPT: A8 - Repo TaskX Surface

Phase: A
Step: A8

Outputs:
- REPO_TASKX_SURFACE.json

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
  "artifact": "REPO_TASKX_SURFACE.json",
  "phase": "A",
  "step": "A8",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "taskx:<stable_id>",
      "invocation": "...",
      "config_file": "...",
      "packet_path": "...",
      "operator_surface": "...",
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
- .taskx files, taskx config, scripts/workflows invoking taskx
- Packet paths, instruction compilation/injection surfaces, operator profile surfaces
```

---

## Prompt
- prompt_id: rte_a_a9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A9
- short_name: Implicit Behavior Hints
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A9_IMPLICIT_BEHAVIOR_HINTS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_IMPLICIT_BEHAVIOR_HINTS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_A9

## Goal
Produce `A9` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_IMPLICIT_BEHAVIOR_HINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_IMPLICIT_BEHAVIOR_HINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_IMPLICIT_BEHAVIOR_HINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream A-Phase artifacts (A0-A8); focus on "convention over configuration" and undocumented defaults.
2. Scan configuration loaders and "defaults" modules (e.g., `src/dopemux/config/defaults.py`, `config/settings.yaml`) for:
   - `config search order`: identify the sequence of paths checked for environment or config files (e.g., `./.env`, `~/.dopemux/env`).
   - `default paths`: identify hardcoded fallbacks for log files, databases, or cache directories.
3. Scan for "if-file-exists" behaviors: identify logic that triggers automatically based on the presence of marker files like `.dopetask-pin`, `.git`, or `.mcp-proxy-config.local`.
4. Identify "silent" operational behaviors:
   - `fallback_chains`: identify models or servers swapped automatically without explicit user configuration.
   - `auto_migrations`: search for scripts or decorators that run schema updates on service startup.
5. Extract environment variable toggles: identify `env` keys that enable hidden or implicit modes (e.g., `DEBUG_MODE`, `SKIP_VALIDATION`, `OFFLINE_ONLY`).
6. Build relationship graph: link implicit behaviors to the files or environment conditions that trigger them.
7. For each IMPLICIT_BEHAVIOR_HINTS item, populate `id` (hint:<stable_id>), description, risk, and `evidence`.
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
# PROMPT: A9 - Repo Implicit Behavior Hints

Phase: A
Step: A9

Outputs:
- REPO_IMPLICIT_BEHAVIOR_HINTS.json

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
  "artifact": "REPO_IMPLICIT_BEHAVIOR_HINTS.json",
  "phase": "A",
  "step": "A9",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hint:<stable_id>",
      "hint_type": "...",
      "description": "...",
      "toggle_or_path": "...",
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
- Explicitly documented implicit behavior: config search order, default paths, if-file-exists toggles, env-var toggles, hidden coupling points when directly stated
```

---

## Prompt
- prompt_id: rte_a_a99
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: A
- step: A99
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A99_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("A")
- invokes: REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json, REPO_MCP_SERVER_DEFS.json, REPO_MCP_PROXY_SURFACE.json, REPO_ROUTER_SURFACE.json, REPO_HOOKS_SURFACE.json, REPO_IMPLICIT_BEHAVIOR_HINTS.json, REPO_COMPOSE_SERVICE_GRAPH.json, REPO_LITELLM_SURFACE.json, REPO_LEANTIME_SURFACE.json, REPO_TASKX_SURFACE.json, REPOCTRL_NORM_MANIFEST.json, REPOCTRL_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: A phase step A99 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
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

---

## Prompt
- prompt_id: rte_h_h0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H0
- short_name: Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H0_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_INVENTORY.json, HOME_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H0

## Goal
Produce `H0` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H0`
    - `id_rule`: `HOME_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H0`
    - `id_rule`: `HOME_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles) domain
3. Build HOME_PARTITIONS by grouping files into logical categories with rationale
4. For each HOME_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each HOME_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
# Phase H0: Home Control Plane Inventory + Partition Plan

You are running inside the Dopemux extraction pipeline.

Goal:
- Inventory only the HOME control-plane relevant files found in the provided context.
- Produce a deterministic partition plan for subsequent Phase H steps.

Hard rules:
- Do NOT invent paths or contents not present in the provided context.
- If something is commonly expected (~/.config/mcp, ~/.dopemux) but not present in context, record it as MISSING (not guessed).
- Output valid JSON only, no markdown fences.

Inputs:
- The runner provides a set of home-control-plane candidate files (safe mode filtering may already have excluded sensitive areas).

Outputs:
- HOME_INVENTORY.json
- HOME_PARTITIONS.json

HOME_INVENTORY.json format:
{
  "inventory_version": "H0.v1",
  "generated_at": "<iso8601>",
  "root_hint": "<string or empty>",
  "items": [
    {
      "path": "<string>",
      "ext": "<string>",
      "bytes": <int>,
      "mtime_epoch": <int>,
      "category_hint": "<one of: mcp|router|litellm|profiles|tmux|sqlite|shell|other|unknown>",
      "notes": "<string>"
    }
  ],
  "missing_expected_roots": [
    {"path": "<string>", "reason": "<string>"}
  ]
}

HOME_PARTITIONS.json format:
{
  "partition_version": "H0.v1",
  "generated_at": "<iso8601>",
  "max_files_per_partition": <int>,
  "partitions": [
    {
      "partition_id": "H_P0001",
      "focus": "<mcp|router|litellm|profiles|tmux|sqlite|mixed>",
      "paths": ["<path1>", "<path2>"],
      "notes": "<string>"
    }
  ],
  "determinism_notes": [
    "Paths sorted ascending before partitioning
```

---

## Prompt
- prompt_id: rte_h_h1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H1
- short_name: Keys / References
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H1_KEYS___REFERENCES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_KEYS_SURFACE.json, HOME_REFERENCES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H1

## Goal
Produce `H1` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_KEYS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_KEYS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_REFERENCES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_REFERENCES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the keys and credential references partition as primary scan surface
2. Extract keys and credential references facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted keys and credential references elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_KEYS_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H1: Home Keys + References Surface (Safe)

Goal:
- Extract references to environment variables, API keys, token paths, credential file paths, and configuration include-chains that appear in the provided home control-plane files.
- Do NOT output secrets. Only output key NAMES, referenced FILE PATHS, and reference locations.

Hard rules:
- Never print actual secret values.
- Prefer explicit evidence: show (path, line_range, snippet_redacted) for each reference.
- Output valid JSON only.

Outputs:
- HOME_KEYS_SURFACE.json
- HOME_REFERENCES.json

HOME_KEYS_SURFACE.json:
{
  "surface_version": "H1.v1",
  "generated_at": "<iso8601>",
  "env_vars_referenced": [
    {
      "name": "<ENV_VAR_NAME>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "credential_paths_referenced": [
    {
      "path": "<string>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "notes": []
}

HOME_REFERENCES.json:
{
  "refs_version": "H1.v1",
  "generated_at": "<iso8601>",
  "includes_and_imports": [
    {
      "source_path": "<path>",
      "kind": "<include|import|source|extends|loads>",
      "target": "<string>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ]
}
```

---

## Prompt
- prompt_id: rte_h_h2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H2
- short_name: Mcp Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H2_MCP_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_MCP_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H2

## Goal
Produce `H2` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_MCP_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_MCP_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_MCP_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the MCP server definitions partition as primary scan surface
2. Extract MCP server definitions facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted MCP server definitions elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_MCP_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H2: Home MCP Surface

Goal:
- Extract MCP server definitions, client configs, and any local MCP wiring present in home control-plane files.

Hard rules:
- Evidence-only.
- If MCP appears only as a hint (string mention) but no structured config is present, record as "hint_only".

Outputs:
- HOME_MCP_SURFACE.json

HOME_MCP_SURFACE.json:
{
  "surface_version": "H2.v1",
  "generated_at": "<iso8601>",
  "servers": [
    {
      "name": "<string>",
      "command": "<string or empty>",
      "args": ["<string>"],
      "env_keys": ["<ENV_VAR_NAME>"],
      "config_path": "<path>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "confidence": "<high|medium|low|hint_only>"
    }
  ],
  "clients": [
    {
      "name": "<string>",
      "config_path": "<path>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes": []
}
```

---

## Prompt
- prompt_id: rte_h_h3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H3
- short_name: Router / Provider Ladders
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H3_ROUTER___PROVIDER_LADDERS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_ROUTER_SURFACE.json, HOME_PROVIDER_LADDER_HINTS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H3

## Goal
Produce `H3` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_ROUTER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_ROUTER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_PROVIDER_LADDER_HINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_PROVIDER_LADDER_HINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the router and provider ladder partition as primary scan surface
2. Extract router and provider ladder facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted router and provider ladder elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_ROUTER_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H3: Home Router + Provider Ladder Hints

Goal:
- Extract any router configuration, model/provider selection ladders, fallback chains, or policy-like directives found in home control plane configs.

Outputs:
- HOME_ROUTER_SURFACE.json
- HOME_PROVIDER_LADDER_HINTS.json

HOME_ROUTER_SURFACE.json:
{
  "surface_version": "H3.v1",
  "generated_at": "<iso8601>",
  "router_configs": [
    {
      "path": "<path>",
      "router_type_hint": "<string>",
      "model_selection_rules": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}

HOME_PROVIDER_LADDER_HINTS.json:
{
  "hints_version": "H3.v1",
  "generated_at": "<iso8601>",
  "ladders": [
    {
      "name": "<string>",
      "providers_or_models": ["<string>"],
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "confidence": "<high|medium|low|hint_only>"
    }
  ]
}
```

---

## Prompt
- prompt_id: rte_h_h4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H4
- short_name: Litellm Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H4_LITELLM_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_LITELLM_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H4

## Goal
Produce `H4` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_LITELLM_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_LITELLM_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_LITELLM_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the LiteLLM config partition as primary scan surface
2. Extract LiteLLM config facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted LiteLLM config elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_LITELLM_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H4: Home LiteLLM Surface

Goal:
- Extract LiteLLM config references, proxy configs, spend/log DB hints, and provider entries from home control-plane.

Outputs:
- HOME_LITELLM_SURFACE.json

HOME_LITELLM_SURFACE.json:
{
  "surface_version": "H4.v1",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<path>",
      "providers": ["<string>"],
      "models": ["<string>"],
      "db_or_logs": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
```

---

## Prompt
- prompt_id: rte_h_h5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H5
- short_name: Profiles / Sessions
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H5_PROFILES___SESSIONS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_PROFILES_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H5

## Goal
Produce `H5` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_PROFILES_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_PROFILES_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_PROFILES_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the profiles and sessions partition as primary scan surface
2. Extract profiles and sessions facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted profiles and sessions elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_PROFILES_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H5: Home Profiles + Sessions Surface

Goal:
- Extract any operator profiles, session presets, persona configs, or “profile selection” hints from home control-plane.

Outputs:
- HOME_PROFILES_SURFACE.json

HOME_PROFILES_SURFACE.json:
{
  "surface_version": "H5.v1",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "name": "<string>",
      "path": "<path>",
      "fields": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes":[]
}
```

---

## Prompt
- prompt_id: rte_h_h6
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H6
- short_name: Tmux / Workflow Helpers
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H6_TMUX___WORKFLOW_HELPERS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_TMUX_WORKFLOW_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H6 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H6

## Goal
Produce `H6` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- `HOME_PROFILES_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_TMUX_WORKFLOW_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_TMUX_WORKFLOW_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_TMUX_WORKFLOW_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the tmux and workflow helpers partition as primary scan surface
2. Extract tmux and workflow helpers facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted tmux and workflow helpers elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_TMUX_WORKFLOW_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H6: Home TMUX + Workflow Helpers Surface

Goal:
- Extract tmux session definitions, scripts, aliases, and helper commands that appear to bootstrap Dopemux/TaskX workflows.

Outputs:
- HOME_TMUX_WORKFLOW_SURFACE.json

HOME_TMUX_WORKFLOW_SURFACE.json:
{
  "surface_version": "H6.v1",
  "generated_at": "<iso8601>",
  "workflows": [
    {
      "name": "<string>",
      "kind": "<tmux|shell|alias|script>",
      "entrypoint": "<string>",
      "paths_involved": ["<path>"],
      "commands": ["<command string>"],
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
```

---

## Prompt
- prompt_id: rte_h_h7
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H7
- short_name: Sqlite / State Db Metadata
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H7_SQLITE___STATE_DB_METADATA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOME_SQLITE_SCHEMA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H7 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H7

## Goal
Produce `H7` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- `HOME_PROFILES_SURFACE.json`
- `HOME_TMUX_WORKFLOW_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_SQLITE_SCHEMA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_SQLITE_SCHEMA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_SQLITE_SCHEMA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the SQLite and state DB metadata partition as primary scan surface
2. Extract SQLite and state DB metadata facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted SQLite and state DB metadata elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_SQLITE_SCHEMA item, populate `id`, required fields, and `evidence`
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
# Phase H7: Home SQLite + State DB Metadata

Goal:
- Detect references to sqlite DB files, schema files, migrations, or state directories in home control plane configs.
- If you have actual sqlite schema text in context, extract table/index names as metadata only (no secret contents).

Outputs:
- HOME_SQLITE_SCHEMA.json

HOME_SQLITE_SCHEMA.json:
{
  "surface_version": "H7.v1",
  "generated_at": "<iso8601>",
  "db_files": [
    {
      "path": "<path>",
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes":"<string>"
    }
  ],
  "schema_hints": [
    {
      "source_path": "<path>",
      "tables": ["<string>"],
      "indexes": ["<string>"],
      "triggers": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
```

---

## Prompt
- prompt_id: rte_h_h9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: H
- step: H9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_H9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("H")
- invokes: HOMECTRL_NORM_MANIFEST.json, HOMECTRL_QA.json, HOME_KEYS_SURFACE.json, HOME_REFERENCES.json, HOME_MCP_SURFACE.json, HOME_ROUTER_SURFACE.json, HOME_PROVIDER_LADDER_HINTS.json, HOME_LITELLM_SURFACE.json, HOME_PROFILES_SURFACE.json, HOME_TMUX_WORKFLOW_SURFACE.json, HOME_SQLITE_SCHEMA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: routing/classification
- purpose: H phase step H9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_H9

## Goal
Produce `H9` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- `HOME_PROFILES_SURFACE.json`
- `HOME_TMUX_WORKFLOW_SURFACE.json`
- `HOME_SQLITE_SCHEMA.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOMECTRL_NORM_MANIFEST.json`
- `HOMECTRL_QA.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- `HOME_PROFILES_SURFACE.json`
- `HOME_TMUX_WORKFLOW_SURFACE.json`
- `HOME_SQLITE_SCHEMA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOMECTRL_NORM_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOMECTRL_NORM_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOMECTRL_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOMECTRL_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_KEYS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_KEYS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_REFERENCES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_REFERENCES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_MCP_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_MCP_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_ROUTER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_ROUTER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_PROVIDER_LADDER_HINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_PROVIDER_LADDER_HINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_LITELLM_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_LITELLM_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_PROFILES_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_PROFILES_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_TMUX_WORKFLOW_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_TMUX_WORKFLOW_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_SQLITE_SCHEMA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_SQLITE_SCHEMA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all H-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all HOME_* artifacts into HOMECTRL_NORM_MANIFEST using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all H-Phase artifacts present, coverage complete, sort order deterministic; emit HOMECTRL_QA
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
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
# Phase H9: Merge + QA (Home Control Plane)

Goal:
- Merge all Phase H raw outputs into deterministic normalized artifacts.
- Emit a QA report: missing expected artifacts, empty artifacts, and evidence quality warnings.

Hard rules:
- Deterministic ordering: sort keys where applicable; sort arrays by stable keys (path/name) when possible.
- No invention.

Outputs:
- HOMECTRL_NORM_MANIFEST.json
- HOMECTRL_QA.json

HOMECTRL_NORM_MANIFEST.json:
{
  "manifest_version": "H9.v1",
  "generated_at": "<iso8601>",
  "inputs": ["<raw json file names>"],
  "outputs": [
    "HOME_KEYS_SURFACE.json",
    "HOME_REFERENCES.json",
    "HOME_MCP_SURFACE.json",
    "HOME_ROUTER_SURFACE.json",
    "HOME_PROVIDER_LADDER_HINTS.json",
    "HOME_LITELLM_SURFACE.json",
    "HOME_PROFILES_SURFACE.json",
    "HOME_TMUX_WORKFLOW_SURFACE.json",
    "HOME_SQLITE_SCHEMA.json"
  ],
  "notes":[]
}

HOMECTRL_QA.json:
{
  "qa_version": "H9.v1",
  "generated_at": "<iso8601>",
  "missing_expected_raw_steps": ["<string>"],
  "empty_outputs": ["<string>"],
  "evidence_warnings": ["<string>"],
  "safe_mode_observations": ["<string>"]
}
```

---

## Prompt
- prompt_id: rte_d_d0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: D
- step: D0
- short_name: Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_D0_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("D")
- invokes: DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: D phase step D0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_D0

## Goal
Produce `D0` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Hard Requirements
- Every `payload.items[]` row MUST include:
  - `id` as a string
  - `path` as a repo-relative string
  - `line_range` as `[start, end]` with exactly two integers where `start > 0` and `end >= start`
- For every emitted row, `evidence[0].path` and `evidence[0].line_range` MUST match the row's `path` and `line_range`.
- Treat the provided excerpts as line-numbered evidence. Cite only those excerpt-local line numbers.
- If you cannot determine a real `line_range` from the provided evidence, do not guess.
- Instead, emit a valid artifact envelope with `"items": []` for that artifact.
- Output exactly one JSON object. No markdown, no prose, no code fences.

## Minimal Example
```json
{
  "artifacts": [
    {
      "artifact_name": "DOC_INVENTORY.json",
      "payload": {
        "schema": "DOC_INVENTORY@v1",
        "items": [
          {
            "id": "DOC_INVENTORY:example",
            "path": "docs/example.md",
            "line_range": [4, 6],
            "kind": "guide",
            "summary": "Example inventory row.",
            "evidence": [
              {
                "path": "docs/example.md",
                "line_range": [4, 6],
                "excerpt": "0004: Example heading"
              }
            ]
          }
        ]
      }
    }
  ]
}
```

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D0`
    - `id_rule`: `DOC_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D0`
    - `id_rule`: `DOC_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_TODO_QUEUE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D0`
    - `id_rule`: `DOC_TODO_QUEUE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan documentation (`docs/**`, archive dirs) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the documentation (`docs/**`, archive dirs) domain
3. Build DOC_PARTITIONS by grouping files into logical categories with rationale
4. For each DOC_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each DOC_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
Goal: DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json

Prompt:
- Scan docs/** (include archive dirs but tag them as archive).
- For each doc:
  - path, size, mtime, top headings, first 40 non-empty lines, token count estimate.
  - tag: ACTIVE vs ARCHIVE vs QUARANTINE based on path + in-doc markers.
- Create partitions:
  - core architecture
  - planes (pm/memory/orchestrator/mcp/hooks)
  - services (dope-memory, eventbus, dashboards, etc.)
  - task-packets + governance
  - research/audits
  - archives (split into manageable buckets)
- Output a queue of partitions with recommended run order.
```

---

## Prompt
- prompt_id: rte_d_d1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: D
- step: D1
- short_name: Claims / Boundaries / Supersession
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_D1_CLAIMS___BOUNDARIES___SUPERSESSION.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("D")
- invokes: DOC_INDEX.partX.json, DOC_CONTRACT_CLAIMS.partX.json, DOC_BOUNDARIES.partX.json, DOC_SUPERSESSION.partX.json, CAP_NOTICES.partX.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: D phase step D1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_D1

## Goal
Produce `D1` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Hard Requirements
- Every `payload.items[]` row MUST include:
  - `id` as a string
  - `path` as a repo-relative string
  - `line_range` as `[start, end]` with exactly two integers where `start > 0` and `end >= start`
- For every emitted row, `evidence[0].path` and `evidence[0].line_range` MUST match the row's `path` and `line_range`.
- Treat the provided excerpts as line-numbered evidence. Cite only those excerpt-local line numbers.
- If you cannot determine a real `line_range` from the provided evidence, do not guess.
- Instead, emit a valid artifact envelope with `"items": []` for that artifact.
- Output exactly one JSON object. No markdown, no prose, no code fences.

## Minimal Example
```json
{
  "artifacts": [
    {
      "artifact_name": "DOC_INDEX.partX.json",
      "payload": {
        "schema": "DOC_INDEX@v1",
        "items": [
          {
            "id": "DOC_INDEX:example",
            "path": "docs/example.md",
            "line_range": [7, 9],
            "name": "Example doc",
            "kind": "contract",
            "evidence": [
              {
                "path": "docs/example.md",
                "line_range": [7, 9],
                "excerpt": "0007: Example contract statement"
              }
            ]
          }
        ]
      }
    }
  ]
}
```

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INDEX.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
  - `DOC_CONTRACT_CLAIMS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_CONTRACT_CLAIMS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_BOUNDARIES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_BOUNDARIES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_SUPERSESSION.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_SUPERSESSION:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `CAP_NOTICES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `CAP_NOTICES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load upstream inventory and partitions; use the doc claims, boundaries, and supersession partition as primary scan surface
2. Extract doc claims, boundaries, and supersession facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted doc claims, boundaries, and supersession elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_INDEX item, populate `id`, required fields, and `evidence`
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
Goal (per partition):
- DOC_INDEX.partX.json
- DOC_CONTRACT_CLAIMS.partX.json
- DOC_BOUNDARIES.partX.json
- DOC_SUPERSESSION.partX.json
- CAP_NOTICES.partX.json (what didn't fit, what needs D2)

Prompt:
- Extract only "normative" and "boundary" statements:
  - MUST/SHALL/DO NOT, invariants, failure modes, interfaces, "authority" language
  - plane boundaries and what enforces them (even if just planned)
  - supersession markers: ACTIVE/DEPRECATED, version headers, timestamps, "supersedes"
- Cite everything: file + line_range + short quote.
```

---

## Prompt
- prompt_id: rte_d_d2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: D
- step: D2
- short_name: Deep Extraction
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_D2_DEEP_EXTRACTION.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("D")
- invokes: DOC_INTERFACES.partX.json, DOC_WORKFLOWS.partX.json, DOC_DECISIONS.partX.json, DOC_GLOSSARY.partX.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: D phase step D2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_D2

## Goal
Produce `D2` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INTERFACES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_INTERFACES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_WORKFLOWS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_WORKFLOWS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_DECISIONS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_DECISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_GLOSSARY.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_GLOSSARY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load upstream inventory and partitions; use the deep doc extraction (interfaces, workflows, decisions) partition as primary scan surface
2. Extract deep doc extraction (interfaces, workflows, decisions) facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted deep doc extraction (interfaces, workflows, decisions) elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_DEEP item, populate `id`, required fields, and `evidence`
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
Goal (per partition):
- DOC_INTERFACES.partX.json
- DOC_WORKFLOWS.partX.json
- DOC_DECISIONS.partX.json
- DOC_GLOSSARY.partX.json

Prompt:
- Extract structured interface/workflow details:
  - service responsibilities
  - dataflow steps
  - event names mentioned
  - state DBs and schema references
  - operational workflows, multi-service pipelines
  - instruction-file-driven workflows
- Again: cite everything.
```

---

## Prompt
- prompt_id: rte_d_d3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: D
- step: D3
- short_name: Citation / Reference Graph
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_D3_CITATION___REFERENCE_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("D")
- invokes: DOC_CITATION_GRAPH.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: D phase step D3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_D3

## Goal
Produce `D3` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_CITATION_GRAPH.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- When emitting `items[]`, every entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_CITATION_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D3`
    - `id_rule`: `DOC_CITATION_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the citation and reference graph partition as primary scan surface
2. Extract citation and reference graph facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted citation and reference graph elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_CITATIONS item, populate `id`, required fields, and `evidence`
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
Goal: DOC_CITATION_GRAPH.json

Prompt:
- Build graph edges:
  - doc A references doc B (links, filenames, "see also", explicit citations)
  - doc A references code path
  - doc A references service name/config name
- Output top referenced docs, hub docs, cross-plane edges.
```

---

## Prompt
- prompt_id: rte_d_d4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: D
- step: D4
- short_name: Merge / Normalize / Coverage Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_D4_MERGE___NORMALIZE___COVERAGE_QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("D")
- invokes: DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json, DOC_RECENCY_DUPLICATE_REPORT.json, DOC_COVERAGE_REPORT.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: D phase step D4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_D4

## Goal
Produce `D4` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`
- `DOC_CITATION_GRAPH.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INDEX.json`
- `DOC_CONTRACT_CLAIMS.json`
- `DOC_SUPERSESSION.json`
- `DOC_TOPIC_CLUSTERS.json`
- `DUPLICATE_DRIFT_REPORT.json`
- `DOC_RECENCY_DUPLICATE_REPORT.json`
- `DOC_COVERAGE_REPORT.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_CONTRACT_CLAIMS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_CONTRACT_CLAIMS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_SUPERSESSION.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_SUPERSESSION:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_TOPIC_CLUSTERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D5`
    - `id_rule`: `DOC_TOPIC_CLUSTERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DUPLICATE_DRIFT_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DUPLICATE_DRIFT_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_RECENCY_DUPLICATE_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_RECENCY_DUPLICATE_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_COVERAGE_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_COVERAGE_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, missing, extra, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all D-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all DOC_* artifacts into DOC_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all D-Phase artifacts present, coverage complete, sort order deterministic; emit DOC_QA
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
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
Goal:
- merged: DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json
- optional alternate duplicate artifact: DOC_RECENCY_DUPLICATE_REPORT.json
- QA: DOC_COVERAGE_REPORT.json

Prompt:
- Merge all part files.
- Dedup rules:
  - prefer newer timestamps when same doc appears in multiple buckets
  - preserve both if content differs materially
- Coverage gates:
  - all docs indexed
  - no pending partitions
  - all CAP_NOTICES resolved or explicitly waived
  - citation graph present
```

---

## Prompt
- prompt_id: rte_d_d5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: D
- step: D5
- short_name: Doc Topic Clusters Json
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_D5_DOC_TOPIC_CLUSTERS_JSON.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("D")
- invokes: DOC_TOPIC_CLUSTERS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: D phase step D5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_D5

## Goal
Produce `D5` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`
- `DOC_CITATION_GRAPH.json`
- `DOC_INDEX.json`
- `DOC_CONTRACT_CLAIMS.json`
- `DOC_SUPERSESSION.json`
- `DOC_TOPIC_CLUSTERS.json`
- `DUPLICATE_DRIFT_REPORT.json`
- `DOC_RECENCY_DUPLICATE_REPORT.json`
- `DOC_COVERAGE_REPORT.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_TOPIC_CLUSTERS.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_TOPIC_CLUSTERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D5`
    - `id_rule`: `DOC_TOPIC_CLUSTERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the doc topic clustering partition as primary scan surface
2. Extract doc topic clustering facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted doc topic clustering elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_TOPIC_CLUSTERS item, populate `id`, required fields, and `evidence`
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
Goal: DOC_TOPIC_CLUSTERS.json

Prompt:
- Input: merged docs index (plus optionally raw text samples).
- Cluster by token overlap (no semantic labeling).
- Output:
  - cluster_id
  - doc_paths
  - top_tokens (weighted)
  - doc_count
  - newest_mtime + oldest_mtime (for recency awareness)
- No "this cluster is architecture" labeling.
```

---

## Prompt
- prompt_id: rte_c_c0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C0
- short_name: Code Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C0_CODE_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: CODE_INVENTORY.json, CODE_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C0

## Goal
Produce `C0` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `shared/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `UPGRADES/**`
- `vendor/**`


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`
- `extraction/**`
- `reports/**`




- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CODE_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CODE_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`) domain
3. Build CODE_PARTITIONS by grouping files into logical categories with rationale
4. For each CODE_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each CODE_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
Goal: CODE_INVENTORY.json, CODE_PARTITIONS.json

Prompt:
- Build partitions by subsystem:
  - services/** entrypoints
  - shared/**
  - src/**
  - workflow scripts
  - eventbus modules
  - dope-memory modules
  - boundary/guardrail modules
  - taskx bridges
```

---

## Prompt
- prompt_id: rte_c_c1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C1
- short_name: Service Entrypoints
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C1_SERVICE_ENTRYPOINTS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: SERVICE_ENTRYPOINTS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C1

## Goal
Produce `C1` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SERVICE_ENTRYPOINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `SERVICE_ENTRYPOINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENTRYPOINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, entrypoint_type, invocation, module_path, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "SERVICE_ENTRYPOINTS:<hash>",
  "service_id": "<service name from registry.yaml or module path>",
  "entrypoint_type": "uvicorn|gunicorn|cli_click|cli_typer|cli_argparse|script_direct|docker_cmd|docker_entrypoint|console_script|makefile_target|compose_command",
  "invocation": "<exact command or symbol used to start, e.g. 'uvicorn app:app --port 8000'>",
  "module_path": "<Python module path, e.g. 'services.task_orchestrator.app:app'>",
  "port": "<integer port number, or null if not network-facing>",
  "bind_host": "<bind address, e.g. '0.0.0.0', '127.0.0.1', or null>",
  "startup_args": ["<CLI flags or env-controlled startup parameters>"],
  "health_check_path": "<HTTP health check endpoint path, or null>",
  "restart_policy": "always|on_failure|no|unless_stopped|null",
  "depends_on": ["<other service names this entrypoint depends on>"],
  "is_production": true,
  "path": "<repo-relative path to entrypoint definition>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Entrypoint Type Definitions
- **uvicorn**: ASGI server invocation via `uvicorn module:app` (directly or via Python `-m`)
- **gunicorn**: WSGI/ASGI server invocation via `gunicorn` with worker configuration
- **cli_click**: Click-based CLI entrypoint using `@click.command()` or `@click.group()`
- **cli_typer**: Typer-based CLI entrypoint using `typer.Typer()` app
- **cli_argparse**: Standard library `argparse.ArgumentParser` CLI entrypoint
- **script_direct**: Direct Python script execution (`python script.py` or `#!/usr/bin/env python`)
- **docker_cmd**: `CMD` instruction in Dockerfile defining container startup command
- **docker_entrypoint**: `ENTRYPOINT` instruction in Dockerfile
- **console_script**: Entry defined in `pyproject.toml` `[project.scripts]` or `setup.py` `console_scripts`
- **makefile_target**: Make target that starts a service (e.g., `make run`, `make serve`)
- **compose_command**: Docker Compose `command:` override in compose.yml

### Worked Example
```json
{
  "id": "SERVICE_ENTRYPOINTS:d5f3a9b2",
  "service_id": "task-orchestrator",
  "entrypoint_type": "uvicorn",
  "invocation": "uvicorn task_orchestrator.app:app --host 0.0.0.0 --port 8100",
  "module_path": "task_orchestrator.app:app",
  "port": 8100,
  "bind_host": "0.0.0.0",
  "startup_args": ["--host", "0.0.0.0", "--port", "8100"],
  "health_check_path": "/health",
  "restart_policy": "on_failure",
  "depends_on": ["redis", "postgres"],
  "is_production": true,
  "path": "services/task-orchestrator/Dockerfile",
  "line_range": [22, 22],
  "status": "ok",
  "evidence": [{"path": "services/task-orchestrator/Dockerfile", "line_range": [22, 22], "excerpt": "CMD [\"uvicorn\", \"task_orchestrator.app:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8100\"]"}]
}
```

## Extraction Procedure
1. Load upstream inventory and partitions; use the service entrypoint partition as primary scan surface.
2. Scan `src/**` and `services/**` for `if __name__ == "__main__":` blocks and `main()` functions to identify direct execution entrypoints.
3. Scan `compose.yml` and `docker-compose*.yml` for `command:` and `entrypoint:` fields to identify canonical service start strings and runtime parameters.
4. Search for FastAPI/Flask app definitions (e.g., `app = FastAPI()`, `app = Flask(__name__)`) and decorators like `@app.get`, `@app.post`, `@app.route` to map API entrypoints.
5. Identify CLI entrypoints in `pyproject.toml` (under `[project.scripts]`), `setup.py` (under `entry_points`), or `Makefile` targets.
6. Locate uvicorn, gunicorn, or celery invocation patterns in shell scripts (`*.sh`) and service definition files.
7. Build relationship graph: trace connections between extracted service entrypoint elements and their underlying module symbols.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts between code-level entrypoints and orchestration-level commands.
9. For each SERVICE_ENTRYPOINTS item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: SERVICE_ENTRYPOINTS.json

Prompt:
- Find how services start:
  - main modules, cli entrypoints, compose commands, uvicorn/gunicorn, scripts.
- Extract exact invocation strings + module symbols.
```

---

## Prompt
- prompt_id: rte_c_c10
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C10
- short_name: Service Catalog Deep
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C10_SERVICE_CATALOG_DEEP.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: SERVICE_CATALOG.partX.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C10 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C10

## Goal
Produce `C10` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `services/agents/**`
  - `components/**`
  - `dashboard/**`
  - `plugins/**`
  - `ui-dashboard/**`
  - `ui-dashboard-backend/**`
  - `src/dopemux/agent_orchestrator.py`
  - `src/dopemux/hooks/**`
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
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `SECRETS_RISK_LOCATIONS.json`
- `CODE_SURFACES_QA.json`
- `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SERVICE_CATALOG.partX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `SERVICE_CATALOG.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_service_id`
    - `canonical_writer_step_id`: `C10`
    - `id_rule`: `SERVICE_CATALOG:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config, evidence`
    - `required_registry_fields`: `service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config`

## Extraction Procedure
1. Load upstream inventory and partitions; use the deep service catalog partition as primary scan surface.
2. Aggregate service identity: extract names and IDs from `services/registry.yaml`, `package.json`, or `pyproject.toml` files within service directories.
3. Identify network exposure: scan `compose.yml`, `Dockerfile`, and code for `EXPOSE` instructions, port assignments, and bind addresses.
4. Locate health check logic: search for dedicated health check functions, `/health` routes, or `HEALTHCHECK` instructions in Dockerfiles.
5. Map repository locations: identify the primary source directories and owners for each service listed in the registry.
6. Synthesize deep facts: combine entrypoint data (from C1), interface data (from C2, C7), and dependency data (from C5, C16) into a unified service profile.
7. Identify configuration surfaces: search for `os.getenv`, `pydantic.BaseSettings`, or `.env` file loading that defines the service's runtime configuration.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in service catalog metadata.
9. For each SERVICE_CATALOG_DEEP item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c11
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C11
- short_name: Leantime Integration Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C11_LEANTIME_INTEGRATION_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: LEANTIME_INTEGRATION_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C11 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C11

## Goal
Produce `C11` outputs for phase `C` by extracting deep Leantime integration surfaces across code paths, service boundaries, and event/HTTP interfaces.
This step maps implementation truth, not intended architecture.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`

- `services/leantime-bridge/**`
- `src/dopemux/**`
- `config/**`
- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




- Upstream normalized artifacts:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `API_DASHBOARD_SURFACE.json`
  - `SERVICE_CATALOG.partX.json`
  - `SERVICE_CATALOG.json`
  - `REPO_LEANTIME_SURFACE.json`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `LEANTIME_INTEGRATION_SURFACE.json`

## Schema
- Deterministic container:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contract:
  - `LEANTIME_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C11`
    - `id_rule`: `LEANTIME_INTEGRATION_SURFACE:<stable-hash(path|symbol|interface)>`
    - `required_item_fields`: `id, path, line_range, evidence`
- Each item should capture one of:
  - service entrypoint integration point
  - HTTP/API boundary call
  - event producer/consumer flow
  - config/env dependency for Leantime behavior

## Extraction Procedure
1. Locate Leantime bridge modules: scan `services/leantime-bridge/**` and identify its exported APIs, models, and service classes.
2. Search for Leantime API call sites: identify code using `leantime_client`, direct `requests` calls to Leantime URLs, or equivalent bridge methods.
3. Identify Leantime-related events: search for event topics (cross-reference with C2) like `leantime.*` or `ticket.*` that signify integration flows.
4. Locate configuration dependencies: search for environment variables like `LEANTIME_API_KEY`, `LEANTIME_URL`, or `LEANTIME_PROJECT_ID` in config modules.
5. Map cross-service flows: trace how dashboard actions or TaskX completions trigger updates in Leantime via the bridge service.
6. Build deterministic IDs and normalized item payloads for each identified integration point.
7. Attach evidence per field and per relationship using direct code excerpts.
8. Deduplicate and sort items by `(path, line_start, id)` to ensure reproducible output.
9. Emit exactly one output file: `LEANTIME_INTEGRATION_SURFACE.json`.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: C11 - Leantime Integration Surfaces
Phase: C
Step: C11
Outputs:
- LEANTIME_INTEGRATION_SURFACE.json
Mode: extraction
Strict: evidence_only
```

---

## Prompt
- prompt_id: rte_c_c12
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C12
- short_name: Agent Orchestration Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C12_AGENT_ORCHESTRATION_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: AGENT_ORCHESTRATION_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C12 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C12

## Goal
Produce `C12` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract agent orchestration surfaces: the `AgentType` enum, `AgentManager` class patterns, agent launch/spawn mechanisms, inter-agent communication protocols, and lifecycle state machines.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/agent_orchestrator.py`
  - `services/agents/**`
  - `src/dopemux/hooks/**`
  - `src/dopemux/agents/**`
  - `src/dopemux/mcp/**`
  - `src/**`
  - `services/**`
  - `components/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `AGENT_ORCHESTRATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `AGENT_ORCHESTRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C12`
    - `id_rule`: `AGENT_ORCHESTRATION_SURFACE:<stable-hash(path|agent_type|symbol)>`
    - `required_item_fields`: `id, item_type, agent_type, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `item_type` enum: `agent_type_enum_value | manager_method | comm_protocol | lifecycle_state | launch_pattern | spawn_pattern`
- `agent_type` values: extracted directly from the `AgentType` enum definition with code evidence
- For `manager_method` items, include: `method_name`, `parameters`, `return_type`, `description`
- For `comm_protocol` items, include: `protocol_type`, `producer`, `consumer`, `payload_shape`
- For `lifecycle_state` items, include: `state_name`, `transitions_to`, `trigger`

## Extraction Procedure
1. Load upstream inventory and partitions; use the agent orchestration partition as primary scan surface.
2. Locate the `AgentType` enum (or equivalent type union) — extract every enum value with its string representation and evidence.
3. Locate the `AgentManager` class (or equivalent orchestrator) — extract all public methods with signatures, parameters, and return types.
4. Scan for agent launch patterns: factory methods (e.g., `AgentFactory.get_agent`), `spawn()`, `create_agent()`, `run_in_background=True`, subprocess invocations, or MCP tool registrations that instantiate agents.
5. Scan for inter-agent communication protocols: search for eventbus subscriptions, direct method calls between agent instances, and usage of `AgentMessage` or equivalent payload types.
6. Extract lifecycle state machines: trace transitions through `READY`, `BUSY`, `IDLE`, `DONE`, and `ERROR` states in agent logic.
7. Cross-reference with `EVENTBUS_SURFACE.json` to identify agent-eventbus bindings and specific message topics.
8. Build deterministic IDs using stable content keys (path/agent_type/symbol).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c13
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C13
- short_name: Adhd Engine Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C13_ADHD_ENGINE_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: ADHD_ENGINE_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C13 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C13

## Goal
Produce `C13` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract the ADHD engine subsystem: focus timer mechanics, dopamine reward loop patterns, task switching logic, cognitive load estimation, and accommodation surfaces.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/adhd/**`
  - `services/adhd_engine/**`
  - `src/dopemux/cognitive/**`
  - `src/dopemux/focus/**`
  - `src/dopemux/hooks/**`
  - `src/dopemux/agent_orchestrator.py`
  - `services/agents/**`
  - `src/**`
  - `services/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `ADHD_ENGINE_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `ADHD_ENGINE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C13`
    - `id_rule`: `ADHD_ENGINE_SURFACE:<stable-hash(path|component|symbol)>`
    - `required_item_fields`: `id, component, subsystem, symbol, description, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `subsystem` enum: `focus_timer | dopamine_reward | task_switching | cognitive_load | accommodation | session_management | other`
- For `focus_timer` items, include: `timer_duration`, `break_logic`, `session_tracking`
- For `dopamine_reward` items, include: `reward_trigger`, `reward_mechanism`, `feedback_loop`
- For `cognitive_load` items, include: `load_metric`, `threshold`, `estimation_method`

## Extraction Procedure
1. Load upstream inventory and partitions; use the ADHD engine partition as primary scan surface
2. Scan `src/dopemux/adhd/**` and `services/adhd_engine/**` for ADHD accommodation implementations
3. Extract focus timer mechanics: Pomodoro-style timers, session duration configs, break logic
4. Extract dopamine reward loop patterns: completion rewards, streak tracking, progress visualization triggers
5. Extract task switching logic: context preservation, task queue management, interruption handling
6. Extract cognitive load estimation: complexity scoring, energy estimation, load-aware routing
7. Scan for accommodation surfaces: how the ADHD engine modifies behavior of other subsystems (task orchestrator, agents)
8. Cross-reference with `AGENT_ORCHESTRATION_SURFACE.json` to identify ADHD-agent integration points
9. Cross-reference with `EVENTBUS_SURFACE.json` for ADHD-related events (focus_start, focus_end, break_taken, etc.)
10. Build deterministic IDs using stable content keys (path/component/symbol)
11. Attach evidence to every non-derived field and every relationship edge
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
14. Emit exactly the declared outputs and no additional files

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c14
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C14
- short_name: Code Health Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C14_CODE_HEALTH_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: CODE_HEALTH_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C14 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C14

## Goal
Produce `C14` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Identify code quality issues, complexity hotspots, and technical debt indicators across all source code: functions exceeding length thresholds, deep nesting, god classes, duplicate logic patterns, missing error handling, and inconsistent coding patterns.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `shared/**`
- `plugins/**`
- `tools/**`
- `scripts/**`
- Upstream normalized artifacts available to this step:
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- `SERVICE_ENTRYPOINTS.json`
- `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CODE_HEALTH_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"CODE_HEALTH_SURFACE@v1","items":[...]}`
- Output contracts:
  - `CODE_HEALTH_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C14`
    - `id_rule`: `CODE_HEALTH_SURFACE:<stable-hash(file_path|function_name|issue_type)>`
    - `required_item_fields`: `id, file_path, function_name, issue_type, severity, description, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "CODE_HEALTH_SURFACE:<hash>",
  "file_path": "<repo-relative path>",
  "function_name": "<function or class name, or null for file-level issues>",
  "issue_type": "high_complexity|long_function|deep_nesting|god_class|duplicate_logic|missing_error_handling|inconsistent_patterns|excessive_parameters|tight_coupling",
  "severity": "critical|high|medium|low",
  "description": "<specific description of the issue>",
  "line_range": [<start>, <end>],
  "metric_value": "<numeric value if applicable, e.g., line count, nesting depth>",
  "metric_threshold": "<threshold that was exceeded>",
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Issue Type Definitions
- **high_complexity**: Cyclomatic complexity indicators (many branches, nested conditions)
- **long_function**: Functions exceeding 100 lines of code
- **deep_nesting**: Nesting depth exceeding 4 levels (if/for/while/try nested inside each other)
- **god_class**: Classes with more than 10 methods or mixing unrelated responsibilities
- **duplicate_logic**: Near-identical code blocks appearing in multiple locations
- **missing_error_handling**: Functions performing I/O, network, or subprocess calls without try/except or error checking
- **inconsistent_patterns**: Same operation done differently in different parts of the codebase (e.g., mixed error handling styles)
- **excessive_parameters**: Functions with more than 5 parameters
- **tight_coupling**: Direct imports crossing architectural boundaries (e.g., service A importing service B internals)

### Severity Classification
- **critical**: Issues that may cause runtime failures or data corruption
- **high**: Issues that significantly impair maintainability or reliability
- **medium**: Issues that moderately affect code quality
- **low**: Style issues or minor improvements

## Extraction Procedure
1. Load upstream CODE_INVENTORY and CODE_PARTITIONS; use the code partition as primary scan surface.
2. Scan for **long functions**: identify functions exceeding 100 lines; record function name, file path, line count.
3. Scan for **deep nesting**: identify code blocks with nesting depth > 4 levels; trace the nesting chain (if > for > if > try > ...).
4. Scan for **god classes**: identify classes with > 10 methods; list method count and method names.
5. Scan for **missing error handling**: identify functions that call `subprocess`, `open()`, `requests.*`, `httpx.*`, database operations, or file I/O without surrounding try/except or explicit error checking.
6. Scan for **excessive parameters**: identify functions with > 5 positional/keyword parameters.
7. Scan for **inconsistent patterns**: compare error handling approaches across modules (e.g., some use exceptions, others return error codes; some log, others swallow).
8. Scan for **duplicate logic**: identify near-identical code blocks (>10 lines) appearing in multiple files.
9. Classify severity for each issue based on impact assessment.
10. Build deterministic IDs using stable content keys `(file_path|function_name|issue_type)`.
11. Attach evidence to every issue with exact excerpts showing the problematic code.
12. Emit exactly `CODE_HEALTH_SURFACE.json` and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c15
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C15
- short_name: Dead Code Inventory
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C15_DEAD_CODE_INVENTORY.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: DEAD_CODE_INVENTORY.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C15 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C15

## Goal
Produce `C15` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Identify unreachable, unused, and deprecated code: functions/classes never imported or called from other modules, stub implementations, deprecated markers, commented-out code blocks, and unused imports.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `shared/**`
- `plugins/**`
- `tools/**`
- `scripts/**`
- Upstream normalized artifacts available to this step:
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- `SERVICE_ENTRYPOINTS.json`
- `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DEAD_CODE_INVENTORY.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"DEAD_CODE_INVENTORY@v1","items":[...]}`
- Output contracts:
  - `DEAD_CODE_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C15`
    - `id_rule`: `DEAD_CODE_INVENTORY:<stable-hash(file_path|symbol_name|dead_code_type)>`
    - `required_item_fields`: `id, file_path, symbol_name, symbol_type, dead_code_type, confidence, evidence, referenced_by`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "DEAD_CODE_INVENTORY:<hash>",
  "file_path": "<repo-relative path>",
  "symbol_name": "<function, class, variable, or import name>",
  "symbol_type": "function|class|method|variable|import|module",
  "dead_code_type": "unreferenced|unreachable|deprecated_marker|empty_implementation|commented_out|stub_only|unused_import",
  "confidence": "high|medium|low",
  "line_range": [<start>, <end>],
  "referenced_by": ["<list of files/modules that reference this symbol, empty if truly dead>"],
  "deprecation_marker": "<text of @deprecated decorator or comment, if applicable>",
  "description": "<why this is considered dead code>",
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Dead Code Type Definitions
- **unreferenced**: Functions/classes defined but never imported or called from any other module in the scanned scope.
- **unreachable**: Code after unconditional return/raise/break/continue, or inside branches that can never execute (e.g., `if False:`).
- **deprecated_marker**: Symbols marked with `@deprecated`, `# DEPRECATED`, `DeprecationWarning`, or similar markers.
- **empty_implementation**: Functions/methods whose body is only `pass`, `...`, or `raise NotImplementedError`.
- **commented_out**: Code blocks that are commented out (multi-line `#` blocks or triple-quote disabled code).
- **stub_only**: Functions that exist only as stubs with `# TODO` or placeholder logic.
- **unused_import**: Import statements where the imported name is never used in the module.

### Confidence Levels
- **high**: Symbol is demonstrably unreferenced across all scanned files, or has explicit deprecation marker.
- **medium**: Symbol appears unreferenced but could be used via dynamic dispatch, reflection, or entry points not in scan scope.
- **low**: Symbol might be dead but evidence is ambiguous (e.g., used only in tests, or referenced via string-based lookup).

## Extraction Procedure
1. Load upstream CODE_INVENTORY and CODE_PARTITIONS; use the code partition as primary scan surface.
2. Scan for **unreferenced symbols**: for each public function/class definition, search for import statements and call sites across all modules in scope. If no references found outside the defining module, flag as unreferenced.
3. Scan for **unreachable code**: identify code after unconditional `return`, `raise`, `sys.exit()`, `break`, `continue`; also identify `if False:` or `if 0:` blocks.
4. Scan for **deprecated markers**: search for `@deprecated`, `# DEPRECATED`, `warnings.warn(.*DeprecationWarning)`, `# TODO: remove`, `# LEGACY`.
5. Scan for **empty implementations**: find functions/methods whose body is exactly `pass`, `...`, `raise NotImplementedError()`, or `raise NotImplementedError`.
6. Scan for **commented-out code**: identify blocks of 5+ consecutive commented lines that appear to be code (contain `=`, `def `, `class `, `import `, `if `, `for `, `return `).
7. Scan for **stub implementations**: find functions with `# TODO` in body or with placeholder return values and no real logic.
8. Scan for **unused imports**: for each import statement, check if the imported name appears anywhere else in the module.
9. For unreferenced symbols, populate `referenced_by` with any partial references found (e.g., test files, dynamic usage).
10. Assign confidence based on reference analysis completeness and dynamic dispatch possibility.
11. Build deterministic IDs using stable content keys `(file_path|symbol_name|dead_code_type)`.
12. Emit exactly `DEAD_CODE_INVENTORY.json` and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c16
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C16
- short_name: Dependency Graphs
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C16_DEPENDENCY_GRAPHS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: MODULE_DEPENDENCY_GRAPH.json, SERVICE_DEPENDENCY_GRAPH.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C16 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C16

## Goal
Produce `C16` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Build module-level and service-level dependency graphs using edges-as-items representation. Map import chains, service-to-service calls, and cross-boundary dependencies.

## Inputs
- Source scope (scan these roots first):
  - `src/**/*.py`
  - `services/**/*.py`
  - `components/**/*.py`
  - `compose.yml`
  - `docker-compose*.yml`
  - `services/registry.yaml`
  - `pyproject.toml`
  - `requirements*.txt`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_CATALOG.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `PYTHON_API_SURFACE.json`
  - `SERVICE_ENDPOINT_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
  - `WORKFLOW_RUNNER_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `MODULE_DEPENDENCY_GRAPH.json`
- `SERVICE_DEPENDENCY_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts (edges-as-items — no `json_graph` kind in runner):
  - `MODULE_DEPENDENCY_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C16`
    - `id_rule`: `MODULE_DEP_EDGE:<stable-hash(source|target|edge_type)>`
    - `required_item_fields`: `id, source, target, edge_type, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
  - `SERVICE_DEPENDENCY_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C16`
    - `id_rule`: `SERVICE_DEP_EDGE:<stable-hash(source|target|edge_type)>`
    - `required_item_fields`: `id, source, target, edge_type, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `edge_type` enum for module graph: `import | from_import | dynamic_import | type_reference | inheritance | composition`
- `edge_type` enum for service graph: `http_call | mcp_invocation | eventbus_pub_sub | shared_db | file_dependency | compose_depends_on | direct_import`
- Each item represents ONE directed edge: `source` → `target` with `edge_type`
- `source` and `target` are module paths (for MODULE) or service_ids (for SERVICE)

## Extraction Procedure
1. Load upstream inventory and partitions; use the full code partition as scan surface
2. **Module dependency graph**: scan all Python files for `import` and `from ... import` statements
3. Classify each import: `import` (full module), `from_import` (selective), `dynamic_import` (`importlib` calls)
4. Trace inheritance chains: extract class bases to build `inheritance` edges
5. Identify composition patterns: class attributes typed as other project classes → `composition` edges
6. **Service dependency graph**: cross-reference upstream artifacts to build service-level edges
7. From `EVENTBUS_SURFACE.json`: map producer service → consumer service as `eventbus_pub_sub` edges
8. From `SERVICE_ENDPOINT_SURFACE.json`: identify cross-service HTTP calls and MCP invocations
9. From `compose.yml` / `docker-compose*.yml`: extract `depends_on` relationships as `compose_depends_on` edges
10. From `SERVICE_CATALOG.json`: extract declared dependencies
11. Build deterministic IDs: `MODULE_DEP_EDGE:<hash(source|target|edge_type)>` and `SERVICE_DEP_EDGE:<hash(source|target|edge_type)>`
12. Attach evidence to every edge (the import statement, the compose config line, the API call site)
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
15. Emit exactly the declared outputs and no additional files

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c17
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C17
- short_name: Cognitive Features Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C17_COGNITIVE_FEATURES_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: COGNITIVE_FEATURES_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C17 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C17

## Goal
Produce `C17` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract all cognitive accommodation features across the codebase: ADHD accommodations, energy-aware routing, attention management, focus optimization, dopamine reward loops, and self-learning/adaptation mechanisms.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/**`
  - `services/**`
  - `src/dopemux/adhd/**`
  - `services/adhd_engine/**`
  - `src/dopemux/cognitive/**`
  - `src/dopemux/focus/**`
  - `src/dopemux/energy/**`
  - `src/dopemux/attention/**`
  - `src/dopemux/learning/**`
  - `src/dopemux/agent_orchestrator.py`
  - `src/dopemux/routing/**`
  - `src/dopemux/routing_config.py`
  - `src/dopemux/hooks/**`
  - `config/**`
  - `configs/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `ADHD_ENGINE_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
  - `EVENTBUS_SURFACE.json`
  - `TASKX_INTEGRATION_SURFACE.json`
  - `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `COGNITIVE_FEATURES_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `COGNITIVE_FEATURES_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C17`
    - `id_rule`: `COGNITIVE_FEATURES_SURFACE:<stable-hash(path|feature_domain|symbol)>`
    - `required_item_fields`: `id, feature_domain, feature_name, subsystem, symbol, description, implementation_status, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `feature_domain` enum:
  - `adhd_accommodation` — focus timers, Pomodoro, break scheduling, interruption shielding
  - `energy_awareness` — energy-level estimation, energy-tagged routing, fatigue detection, low-energy fallbacks
  - `attention_management` — cognitive load scoring, context switching cost, attention budgets, distraction guards
  - `dopamine_reward` — streak tracking, completion celebrations, progress visualization, gamification hooks
  - `self_learning` — user preference adaptation, pattern recognition, model selection learning, feedback loops, drift detection
  - `task_accommodation` — task decomposition heuristics, complexity-aware scheduling, priority rewriting
- `implementation_status` enum: `implemented | stub | planned | partial | deprecated`
- For `adhd_accommodation` items, include: `timer_config`, `break_policy`, `session_tracking_method`
- For `energy_awareness` items, include: `energy_source`, `routing_impact`, `fallback_behavior`
- For `attention_management` items, include: `load_metric`, `threshold_config`, `mitigation_action`
- For `dopamine_reward` items, include: `reward_trigger`, `reward_mechanism`, `feedback_channel`
- For `self_learning` items, include: `learning_signal`, `adaptation_target`, `persistence_mechanism`, `drift_detection_method`
- For `task_accommodation` items, include: `decomposition_strategy`, `complexity_scorer`, `scheduling_rule`

## Extraction Procedure
1. Load upstream inventory and partitions; use the full code partition as scan surface.
2. Scan for ADHD accommodation features: locate code implementing focus timers, Pomodoro sessions (e.g., 25-minute intervals), break logic, and interruption shielding decorators.
3. Scan for energy-aware routing: functions/classes that assess user energy level, route tasks based on energy, implement low-energy fallbacks, tag tasks with energy requirements
4. Scan for attention management: cognitive load estimation functions, context-switch cost calculations, attention budget allocators, distraction guards
5. Scan for dopamine reward loops: streak counters, completion rewards, progress bars/visualizations, gamification elements, achievement systems
6. Scan for self-learning mechanisms: user preference stores, adaptive model selection, feedback ingestion, pattern recognition, recommendation adjustment, drift detection between expected and actual behavior
7. Scan for task accommodation: automatic task decomposition, complexity scoring (0.0-1.0 scale per workspace config), energy-aware scheduling, priority rewriting rules
8. Cross-reference with `ADHD_ENGINE_SURFACE.json` to ensure complete coverage and identify features outside the core engine
9. Cross-reference with `AGENT_ORCHESTRATION_SURFACE.json` to find cognitive features embedded in agent routing
10. Cross-reference with `TASKX_INTEGRATION_SURFACE.json` to find task-level accommodations
11. For each feature, classify `feature_domain`, extract `implementation_status` (implemented|stub|planned).
12. Build deterministic IDs using stable content keys (path/feature_domain/symbol).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID.
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_c_c2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C2
- short_name: Eventbus Wiring Truth Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
1. Load upstream inventory and partitions; use the eventbus wiring partition as primary scan surface.
2. Identify event bus classes and adapters: search for classes inheriting from base event bus types or using Redis/Nats/RabbitMQ client libraries.
3. Search for literal event names and topics defined as string constants (e.g., `TOPIC_USER_CREATED = "user.created"`) to map the event vocabulary.
4. Locate producer call sites: search for `.publish(`, `.emit(`, `.send_event(`, or equivalent method calls that push data to the bus.
5. Locate consumer registration and handlers: search for decorators like `@bus.subscribe(`, `@event_handler(`, or explicit registration calls like `bus.add_listener(`.
6. Build relationship graph: trace connections between producers, topics, and consumers by matching event identifiers.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in event routing or schema enforcement.
8. For each EVENTBUS_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

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

---

## Prompt
- prompt_id: rte_c_c3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C3
- short_name: Dope Memory Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C3_DOPE_MEMORY_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: DOPE_MEMORY_CODE_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C3

## Goal
Produce `C3` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOPE_MEMORY_CODE_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOPE_MEMORY_CODE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_CODE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the dope memory storage partition as primary scan surface.
2. Identify storage backend configurations: search for Redis, SQLite, Postgres, or ChromaDB connection strings and initialization code in `config/` or `services/**`.
3. Locate schema definitions and migration files: scan `*.sql` files and Python migration scripts (e.g., Alembic `env.py` or `versions/*.py`) to map data structures.
4. Find all database write locations: search for raw `INSERT`, `UPDATE`, `DELETE` SQL statements or ORM equivalent calls like `.add(`, `.save(`, `.update(`.
5. Identify TTL and retention enforcement: search for `expire`, `ttl`, `cleanup_stale`, or `retention` keywords in storage-related modules.
6. Build relationship graph: map the connections between code symbols (functions/classes) and the specific database tables or collections they manipulate.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in storage settings across environments.
8. For each DOPE_MEMORY_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goals: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json

Prompt:
- Extract:
  - storage backends
  - schema sources (SQL, migrations)
  - all DB write locations (insert/update/delete) with context
  - TTL/retention enforcement points
```

---

## Prompt
- prompt_id: rte_c_c4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C4
- short_name: Trinity Boundary Enforcement Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C4_TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C4

## Goal
Produce `C4` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
1. Load upstream inventory and partitions; use the trinity boundary enforcement partition as primary scan surface.
2. Identify boundary enforcement points: search for decorators like `@boundary_check`, `@gatekeeper`, or `@authorize` that wrap sensitive functions.
3. Locate refusal logic and guardrails: search for keywords like "refusal", "forbidden", "unauthorized", "block", or "rail" in error handling, middleware, and validation modules.
4. Trace gating chains: identify sequences of checks in FastAPI/Flask middleware, base class methods, or decorator stacks.
5. Scan CLI paths and routers for explicit permission or boundary validation calls (e.g., `check_access(user, resource)`).
6. Build relationship graph: map which boundaries and guardrails protect which service entrypoints and data access paths.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in security policy enforcement.
8. For each TRINITY_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goals: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json

Prompt:
- Extract:
  - boundary checks, refusal artifacts, gating chains
  - where it's invoked (middleware, validators, routers, CLI paths)
```

---

## Prompt
- prompt_id: rte_c_c5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C5
- short_name: Taskx Integration Surfaces
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C5_TASKX_INTEGRATION_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: TASKX_INTEGRATION_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C5

## Goal
Produce `C5` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TASKX_INTEGRATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TASKX_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `TASKX_INTEGRATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the TaskX integration partition as primary scan surface.
2. Locate all calls to TaskX APIs: search for imports of `taskx` and calls to methods like `taskx.create_task`, `taskx.submit`, or `taskx.get_status`.
3. Identify packet read/write paths: search for code handling `TaskPacket` objects, `.to_json()`, or `.from_json()` calls related to task serialization.
4. Find operator instruction compilation: search for logic that generates templates, prompts, or instruction sets specifically for TaskX execution.
5. Identify result processing: search for callback handlers, polling loops, or event listeners that ingest TaskX completion data.
6. Build relationship graph: trace the lifecycle of a task from creation in code to its representation in a TaskPacket and eventual result handling.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in task orchestration logic.
8. For each TASKX_INTEGRATION_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: TASKX_INTEGRATION_SURFACE.json

Prompt:
- Extract:
  - any calls to taskx
  - packet read/write paths
  - operator instruction compilation/injection in code
```

---

## Prompt
- prompt_id: rte_c_c6
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C6
- short_name: Workflow Runners / Multi Service Coordination
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C6_WORKFLOW_RUNNERS___MULTI_SERVICE_COORDINATION.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: WORKFLOW_RUNNER_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C6 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C6

## Goal
Produce `C6` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_RUNNER_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_RUNNER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `WORKFLOW_RUNNER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the workflow runner and multi-service coordination partition as primary scan surface.
2. Identify workflow scripts: scan `scripts/**` and `tools/**` for `*.sh`, `*.py`, or `*.rb` files that orchestrate or start multiple services.
3. Scan `tmux.conf`, `tmux-*.yaml`, or `*.tmux` files to identify session/window/pane layouts and multi-service startup sequences.
4. Search for orchestrator configurations: scan `orchestrator.yaml`, `workflow.yaml`, or equivalent files that define multi-step execution graphs or service dependencies.
5. Identify `Makefile` and `Taskfile` targets that wrap multiple service commands (e.g., `start-all`, `deploy-stack`, `setup-env`).
6. Trace execution ordering: identify `sleep` commands, `wait-for-it` patterns, or explicit health-check polling loops in startup scripts.
7. Build relationship graph: map the coordination flow from the runner script/target to the individual services and their specific startup order.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in service coordination logic.
9. For each WORKFLOW_RUNNER_SURFACES item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: WORKFLOW_RUNNER_SURFACE.json

Prompt:
- Extract:
  - scripts, tmux configs, orchestrator yaml, make targets
  - what starts what, and in what order
```

---

## Prompt
- prompt_id: rte_c_c7
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C7
- short_name: Api / Dashboards
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C7_API___DASHBOARDS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: API_DASHBOARD_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C7 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C7

## Goal
Produce `C7` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `API_DASHBOARD_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `API_DASHBOARD_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C7`
    - `id_rule`: `API_DASHBOARD_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, http_method, path_template, handler_symbol, auth_required, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "API_DASHBOARD_SURFACE:<hash>",
  "http_method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|WEBSOCKET",
  "path_template": "<route path, e.g. '/api/v1/tasks/{task_id}'>",
  "handler_symbol": "<function or method name handling the route>",
  "service_name": "<service name from registry.yaml>",
  "request_body_schema": "<Pydantic model name or null for no body>",
  "response_model": "<Pydantic model name or null if untyped>",
  "response_codes": ["200", "404", "422"],
  "auth_required": true,
  "auth_mechanism": "depends_injection|bearer_token|api_key|none|unknown",
  "rate_limited": false,
  "rate_limit_spec": "<e.g. '100/minute' or null>",
  "tags": ["<FastAPI tags if declared>"],
  "is_deprecated": false,
  "path": "<repo-relative path to route definition>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### HTTP Method Definitions
- **GET**: Read-only retrieval of resources
- **POST**: Create new resources or trigger actions
- **PUT**: Full replacement of a resource
- **PATCH**: Partial update of a resource
- **DELETE**: Remove a resource
- **OPTIONS**: CORS preflight or capability discovery
- **HEAD**: Headers-only GET (no body)
- **WEBSOCKET**: WebSocket upgrade endpoint

### Auth Mechanism Definitions
- **depends_injection**: Auth enforced via FastAPI `Depends()` (e.g., `Depends(get_current_user)`)
- **bearer_token**: JWT or OAuth2 Bearer token in Authorization header
- **api_key**: API key in header, query parameter, or cookie
- **none**: No authentication required (public endpoint)
- **unknown**: Auth presence unclear from code evidence

### Severity Classification (for dashboard items)
- **critical**: Endpoint has no auth but handles sensitive data
- **high**: Endpoint missing error handling or has unvalidated inputs
- **medium**: Endpoint lacks rate limiting or response schema
- **low**: Documentation or deprecation annotation missing

### Worked Example
```json
{
  "id": "API_DASHBOARD_SURFACE:b7e2d1f8",
  "http_method": "POST",
  "path_template": "/api/v1/tasks/{task_id}/decompose",
  "handler_symbol": "decompose_task",
  "service_name": "task-orchestrator",
  "request_body_schema": "DecomposeRequest",
  "response_model": "DecomposeResponse",
  "response_codes": ["200", "404", "422"],
  "auth_required": false,
  "auth_mechanism": "none",
  "rate_limited": false,
  "rate_limit_spec": null,
  "tags": ["tasks"],
  "is_deprecated": false,
  "path": "services/task-orchestrator/app/api/pm_tools.py",
  "line_range": [45, 78],
  "status": "ok",
  "evidence": [{"path": "services/task-orchestrator/app/api/pm_tools.py", "line_range": [45, 47], "excerpt": "@router.post('/api/v1/tasks/{task_id}/decompose', response_model=DecomposeResponse)"}]
}
```

## Extraction Procedure
1. Load upstream inventory and partitions; use the API endpoint and dashboard partition as primary scan surface.
2. Extract API routes: scan `src/**` and `services/**` for router definitions (e.g., `APIRouter()`, `Blueprint()`) and route decorators (e.g., `@app.get`, `@router.post`).
3. Identify dashboard definitions: search for UI components in `dashboard/**`, `ui-dashboard/**`, or `components/**` that render system state or metrics.
4. Locate monitoring and health endpoints: search for routes like `/health`, `/metrics`, `/status`, or Prometheus-style exporter configurations.
5. Identify frontend-to-backend mappings: search for `fetch(`, `axios.`, or `api.get(` calls in JavaScript/TypeScript files to identify backend dependencies.
6. Build relationship graph: trace connections between API endpoints and the dashboard components that display their data.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in API surface definitions.
8. For each API_DASHBOARD_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: API_DASHBOARD_SURFACE.json

Prompt:
- Extract API routes, dashboard definitions, and monitoring endpoints.
- Cite file and line ranges.
```

---

## Prompt
- prompt_id: rte_c_c8
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C8
- short_name: Determinism / Idempotency / Concurrency Location Scans
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C8 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
1. Load upstream inventory and partitions; use the determinism, idempotency, and concurrency partition as primary scan surface.
2. Scan for non-deterministic functions: search for usage of `random.*`, `datetime.now()`, `time.time()`, and `uuid.uuid4()` in critical business logic paths.
3. Identify concurrency risks: search for `global` keyword, shared mutable state, and usage of `threading.Thread` or `asyncio.gather` without visible locking mechanisms.
4. Locate idempotency risks: identify database write operations (cross-reference with C3) that lack unique constraints, upsert logic, or idempotency keys.
5. Scan for secrets patterns: search for hardcoded strings matching regex patterns for API keys, tokens, or `SECRETS = "..."` assignments in non-config files.
6. Build risk registry: map each identified risk to its specific file location and classify severity based on the surrounding code context.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in risk assessment logic.
8. For each DETERMINISM_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

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

---

## Prompt
- prompt_id: rte_c_c9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: C
- step: C9
- short_name: Merge / Normalize / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_C9_MERGE___NORMALIZE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("C")
- invokes: CODE_SURFACES_QA.json, SERVICE_CATALOG.json, PYTHON_API_SURFACE.json, SERVICE_ENDPOINT_SURFACE.json, COGNITIVE_FEATURES_SURFACE.json, SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json, DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json, TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json, TASKX_INTEGRATION_SURFACE.json, WORKFLOW_RUNNER_SURFACE.json, DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: C phase step C9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_C9

## Goal
Produce `C9` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `SECRETS_RISK_LOCATIONS.json`
- `AGENT_ORCHESTRATION_SURFACE.json`
- `ADHD_ENGINE_SURFACE.json`
- `PYTHON_API_SURFACE.json`
- `SERVICE_ENDPOINT_SURFACE.json`
- `MODULE_DEPENDENCY_GRAPH.json`
- `SERVICE_DEPENDENCY_GRAPH.json`
- `COGNITIVE_FEATURES_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CODE_SURFACES_QA.json`
- `SERVICE_CATALOG.json`
- `PYTHON_API_SURFACE.json`
- `SERVICE_ENDPOINT_SURFACE.json`
- `COGNITIVE_FEATURES_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `SERVICE_ENTRYPOINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENTRYPOINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, type, value, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
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
  - `DOPE_MEMORY_CODE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_CODE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_SCHEMAS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_SCHEMAS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_DB_WRITES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_DB_WRITES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
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
  - `TASKX_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `TASKX_INTEGRATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `WORKFLOW_RUNNER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `WORKFLOW_RUNNER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `LEANTIME_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C11`
    - `id_rule`: `LEANTIME_INTEGRATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
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
  - `CODE_SURFACES_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `CODE_SURFACES_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `AGENT_ORCHESTRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `AGENT_ORCHESTRATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `ADHD_ENGINE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `ADHD_ENGINE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `PYTHON_API_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `PYTHON_API_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `SERVICE_ENDPOINT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENDPOINT_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `MODULE_DEPENDENCY_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `MODULE_DEPENDENCY_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `SERVICE_DEPENDENCY_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_DEPENDENCY_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `COGNITIVE_FEATURES_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `COGNITIVE_FEATURES_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `SERVICE_CATALOG.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_service_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_CATALOG:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config, evidence`
    - `required_registry_fields`: `service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config`

## Extraction Procedure
1. Load all C-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all CODE_* artifacts into CODE_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all C-Phase artifacts present, coverage complete, sort order deterministic; emit CODE_QA
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
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
Goal:
- merged: SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json
- merged: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- merged: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json, TASKX_INTEGRATION_SURFACE.json
- merged: WORKFLOW_RUNNER_SURFACE.json
- merged: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json
- QA: CODE_SURFACES_QA.json

Prompt:
- Merge all C1-C8 outputs.
- QA: Ensure all artifacts present, no secrets, coverage complete.
```

---
