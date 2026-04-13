# Prompt Bundle: Active Extraction Bundle 2

## Prompt
- prompt_id: rte_e_e0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E0
- short_name: Execution Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E0_EXECUTION_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_INVENTORY.json, EXEC_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_E0

## Goal
Produce `E0` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `compose.yml`
- `docker-compose*.yml`
- `Makefile`
- `src/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_INVENTORY.json`
- `EXEC_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E0`
    - `id_rule`: `EXEC_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E0`
    - `id_rule`: `EXEC_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan execution-plane targets (`Makefile`, `scripts/`, `*.sh`, `.github/`, `docker*/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the execution-plane targets (`Makefile`, `scripts/`, `*.sh`, `.github/`, `docker*/`) domain
3. Build EXEC_PARTITIONS by grouping files into logical categories with rationale
4. For each EXEC_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each EXEC_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
# PROMPT_E0 — EXECUTION INVENTORY + PARTITION PLAN

TASK: Build inventory + partitions for execution plane.
SCAN TARGETS: Makefile, package.json, pyproject.toml, scripts/, tools/, compose/, .github/, docker*/, *.sh, *.zsh, justfile*, *.mk.

OUTPUTS:
	•	EXEC_INVENTORY.json
	•	EXEC_PARTITIONS.json

RULES:
	•	Identify every file in the scan targets.
	•	Chunk sources into tractable partitions for the following prompts.
	•	Ensure partitions are deterministic.
```

---

## Prompt
- prompt_id: rte_e_e1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E1
- short_name: Bootstrap Commands Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E1_BOOTSTRAP_COMMANDS_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_BOOTSTRAP_COMMANDS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_E1

## Goal
Produce `E1` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_BOOTSTRAP_COMMANDS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_BOOTSTRAP_COMMANDS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E1`
    - `id_rule`: `EXEC_BOOTSTRAP_COMMANDS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json` and `EXECUTION_PARTITIONS.json`. Target scripts (`*.sh`, `*.ps1`), `Makefile`, `Dockerfile`, and `setup.py`/`pyproject.toml`.
2.  **Extract Install & Init Commands**:
    *   In `Makefile`: Identify targets like `install`, `setup`, `init`, `deps`, and `build`. Record the literal recipe lines.
    *   In `install.sh`/`bootstrap.sh`: Extract key command sequences (e.g., `pip install`, `npm install`, `apt-get`).
    *   In `Dockerfile`: Extract `RUN` commands specifically performing setup or dependency installation.
3.  **Map Command Metadata**: For each command, identify:
    *   `command_string`: The literal shell/executable string.
    *   `interpreter`: `bash`, `python`, `make`, etc.
    *   `is_idempotent`: Identify guards like `if [ ! -f ... ]` or `|| true`.
4.  **Populate Items**: Construct `BOOTSTRAP_COMMANDS` items with deterministic IDs based on `path|command_string`.
5.  **Evidence Anchoring**: Attach exact excerpts and line ranges for every command and guard identified.
6.  **Validate**: Apply deterministic sorting by path and line number. Emit `BOOTSTRAP_COMMANDS_SURFACE.json`.
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
# PROMPT_E1 — BOOTSTRAP COMMANDS SURFACE

TASK: Enumerate canonical “what starts what” commands.

MUST EXTRACT (literal strings):
	•	make targets and recipes
	•	npm scripts
	•	python entrypoints / CLI invocations
	•	compose up/down targets
	•	tmux wrappers invoked from repo side

OUTPUTS:
	•	EXEC_BOOTSTRAP_COMMANDS.json
```

---

## Prompt
- prompt_id: rte_e_e2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E2
- short_name: Env Loading / Config Chain
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E2_ENV_LOADING___CONFIG_CHAIN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_ENV_CHAIN.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_E2

## Goal
Produce `E2` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_ENV_CHAIN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_ENV_CHAIN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E2`
    - `id_rule`: `EXEC_ENV_CHAIN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`. Focus on source code (`*.py`, `*.ts`), `.env.example`, and `config/*.yaml`.
2.  **Scan for Environment Access**:
    *   In Python: Identify `os.getenv`, `os.environ`, `dotenv.load_dotenv`, and Pydantic `BaseSettings`.
    *   In TypeScript/JS: Identify `process.env`.
    *   In Docker/Compose: Identify `environment:` and `env_file:` sections.
3.  **Identify Configuration Cascades**:
    *   Find functions like `load_config()`, `get_settings()`, or `init_app()`.
    *   Trace how variables are merged (e.g., CLI args > Env Vars > Default Config).
4.  **Extract Variable Metadata**: For each variable, record:
    *   `name`: The literal env var name.
    *   `default`: The hardcoded fallback value.
    *   `is_required`: Boolean based on `raise` if missing or Pydantic validation.
    *   `source`: File and line where it is first defined or accessed.
5.  **Evidence Anchoring**: Attach exact excerpts for every access point and default value.
6.  **Validate**: Deduplicate by variable name and file path. Emit `ENV_LOADING_CONFIG_CHAIN.json`.
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
# PROMPT_E2 — ENV LOADING / CONFIG CHAIN

TASK: Map env var sources and config precedence chain.

MUST EXTRACT:
	•	.env loading behavior and where it occurs
	•	config file resolution order
	•	env var names and their consumers (by reference only, no guessing)

OUTPUTS:
	•	EXEC_ENV_CHAIN.json
```

---

## Prompt
- prompt_id: rte_e_e3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E3
- short_name: Service Startup Graph
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E3_SERVICE_STARTUP_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_STARTUP_GRAPH.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
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

---

## Prompt
- prompt_id: rte_e_e4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E4
- short_name: Runtime Modes / Delta Report
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E4_RUNTIME_MODES___DELTA_REPORT.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_RUNTIME_MODES.json, EXEC_MODE_DELTA_REPORT.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_E4

## Goal
Produce `E4` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_RUNTIME_MODES.json`
- `EXEC_MODE_DELTA_REPORT.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_RUNTIME_MODES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E4`
    - `id_rule`: `EXEC_RUNTIME_MODES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_MODE_DELTA_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E4`
    - `id_rule`: `EXEC_MODE_DELTA_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`. Focus on configuration loaders, CLI entrypoints, and feature toggle files.
2.  **Identify Mode Triggers**:
    *   Scan for environment variables that switch modes: `APP_ENV`, `NODE_ENV`, `STAGE`, `DEBUG`.
    *   Scan for CLI flags: `--dev`, `--prod`, `--test`, `--dry-run`.
3.  **Map Mode-Specific Behavior**:
    *   Identify conditional logic in code: `if settings.is_dev:`, `if os.environ.get("DEBUG") == "1":`.
    *   Extract differences in: logging levels, database connection strings, security enforcements, and available API endpoints.
4.  **Detect Feature Toggles**:
    *   Scan for toggle definitions: `features.json`, `unleash` configs, or hardcoded boolean flags.
5.  **Build Mode Items**: For each identified mode, record:
    *   `mode_name`: e.g., "production", "development", "maintenance".
    *   `trigger_condition`: The literal env var or flag that activates it.
    *   `affected_behavior`: A concise description of what changes in this mode.
6.  **Evidence Anchoring**: Attach exact excerpts showing the conditional checks and mode definitions.
7.  **Validate**: Apply stable sorting by mode name. Emit `RUNTIME_MODES_DELTA.json`.
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
# PROMPT_E4 — RUNTIME MODES / DELTA REPORT

TASK: Identify runtime “modes” (dev/prod/smoke/local) + deltas.

OUTPUTS:
	•	EXEC_RUNTIME_MODES.json
	•	EXEC_MODE_DELTA_REPORT.json
```

---

## Prompt
- prompt_id: rte_e_e5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E5
- short_name: Artifact Outputs / Logs / State
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E5_ARTIFACT_OUTPUTS___LOGS___STATE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_ARTIFACT_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_E5

## Goal
Produce `E5` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_ARTIFACT_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_ARTIFACT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E5`
    - `id_rule`: `EXEC_ARTIFACT_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`. Target logging configurations, database initialization code, and Docker volume mounts.
2.  **Identify Log Destinations**:
    *   Scan code for `logging.FileHandler`, `RotatingFileHandler`, `Sentry`, or custom log writers.
    *   Identify log file patterns: `/var/log/*.log`, `logs/app.log`.
    *   Extract log format and rotation policies if present.
3.  **Map Persistent State**:
    *   Scan for database connection strings: `sqlite3.connect`, `PostgreSQL` DSNs.
    *   Identify local file-based state: `Path("data/state.json")`, `.dopemux/sessions/*.json`.
    *   Extract Docker volume mappings from `docker-compose.yml` that point to local folders.
4.  **Detect Artifact Generators**:
    *   Identify code paths that write files: `open(..., 'w')`, `df.to_csv()`, `json.dump()`.
    *   Record the type of artifact: `log`, `state`, `cache`, `report`, `export`.
5.  **Build Output Items**: For each destination, record:
    *   `artifact_path`: The literal path or pattern.
    *   `persistence_type`: `volatile` (memory/stdout) or `durable` (disk/DB).
    *   `component_owner`: The service or module that writes to this location.
6.  **Evidence Anchoring**: Attach exact excerpts showing the file path hardcoding or volume mount definition.
7.  **Validate**: Deduplicate by artifact path. Emit `EXEC_ARTIFACT_IO_MAP.json`.
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
# PROMPT_E5 — ARTIFACT OUTPUTS / LOGS / STATE

TASK: List artifact outputs: logs, db files, cache dirs, out dirs.

OUTPUTS:
	•	EXEC_ARTIFACT_SURFACE.json
```

---

## Prompt
- prompt_id: rte_e_e6
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E6
- short_name: Execution Risks / Ordering / State Dependency
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E6_EXECUTION_RISKS___ORDERING___STATE_DEPENDENCY.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_RISK_FACTS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E6 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
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

---

## Prompt
- prompt_id: rte_e_e9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: E
- step: E9
- short_name: Merge / Normalize / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_E9_MERGE___NORMALIZE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("E")
- invokes: EXEC_MERGED.json, EXEC_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: tool_orchestration
- purpose: E phase step E9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_E9

## Goal
Produce `E9` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- `EXEC_RISK_FACTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_MERGED.json`
- `EXEC_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E9`
    - `id_rule`: `EXEC_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E9`
    - `id_rule`: `EXEC_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all E-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all EXEC_* artifacts into EXEC_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all E-Phase artifacts present, coverage complete, sort order deterministic; emit EXEC_QA
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
# PROMPT_E9 — Execution merge + normalize + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge all EXEC_* outputs, report coverage and suspicious gaps.

OUTPUTS:
  • EXEC_MERGED.json
  • EXEC_QA.json (counts_by_filekind, partitions_covered, missing_expected_outputs[], suspicious_empty[])

RULES:
  • Normalize arrays by stable sort, remove duplicate rows.
  • Preserve exact field names from upstream prompts.
```

---

## Prompt
- prompt_id: rte_w_w0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W0
- short_name: Workflow Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W0_WORKFLOW_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_INVENTORY.json, WORKFLOW_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W0

## Goal
Produce `W0` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W0`
    - `id_rule`: `WORKFLOW_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `WORKFLOW_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W0`
    - `id_rule`: `WORKFLOW_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan workflow sources (orchestration scripts, runbooks, CI workflows, compose, tmux sessions) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the workflow sources (orchestration scripts, runbooks, CI workflows, compose, tmux sessions) domain
3. Build WORKFLOW_PARTITIONS by grouping files into logical categories with rationale
4. For each WORKFLOW_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each WORKFLOW_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
# PROMPT_W0 — WORKFLOW INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for workflows.

OUTPUTS:
	•	WORKFLOW_INVENTORY.json
	•	WORKFLOW_PARTITIONS.json
```

---

## Prompt
- prompt_id: rte_w_w1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W1
- short_name: Workflow Catalog / Runbook Facts
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W1_WORKFLOW_CATALOG___RUNBOOK_FACTS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_CATALOG.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W1

## Goal
Produce `W1` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_CATALOG.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_CATALOG.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W1`
    - `id_rule`: `WORKFLOW_CATALOG:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the workflow catalog and runbook partition as primary scan surface.
2. Identify executable workflows in `scripts/**`: scan for `main()` entrypoints in Python/Ruby scripts and `set -e` blocks in Shell scripts that define multi-step sequences.
3. Locate runbook facts in `docs/02-how-to/**` and `docs/03-reference/**`: search for step-by-step instructions and command blocks (marked with ` ``` `).
4. Extract literal steps: for each identified workflow, list the specific commands or function calls executed in sequence, along with their prerequisites.
5. Scan `compose.yml` for multi-service `command:` overrides that define specific runtime workflows (e.g., `seed-db`, `run-tests`).
6. Build relationship graph: link documentation runbooks to their corresponding executable script files and service entrypoints.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in workflow definitions.
8. For each WORKFLOW_CATALOG item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID.
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W1 — WORKFLOW CATALOG / RUNBOOK FACTS

TASK: Enumerate workflows W1..Wn with literal steps.

OUTPUTS:
	•	WORKFLOW_CATALOG.json
```

---

## Prompt
- prompt_id: rte_w_w2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W2
- short_name: Workflow Inputs Outputs / Artifacts
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W2_WORKFLOW_INPUTS_OUTPUTS___ARTIFACTS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_IO_MAP.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W2

## Goal
Produce `W2` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_IO_MAP.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_IO_MAP.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W2`
    - `id_rule`: `WORKFLOW_IO_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the workflow inputs/outputs/artifacts partition as primary scan surface.
2. Identify workflow inputs: search for `argparse`, `sys.argv`, `os.getenv`, or `input()` calls in scripts, and environment variable requirements in `compose.yml`.
3. Locate artifact production (outputs): search for `open('...', 'w')`, `.to_csv()`, `json.dump()`, or shell redirection `> log.txt` patterns that create persistent files.
4. Scan for data transformation steps: identify code that reads a file (`input`), processes it, and writes a new file (`artifact`).
5. Map artifact locations: identify standard output directories like `out/`, `reports/`, `logs/`, and `proof/`.
6. Identify network and side-effect outputs: search for `requests.*`, `httpx.*`, or database write operations (cross-reference with C3).
7. Build relationship graph: trace the flow of data from inputs to transformation logic and final artifact production.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in workflow I/O mapping.
9. For each WORKFLOW_IO_MAP item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID.
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W2 — WORKFLOW INPUTS / OUTPUTS / ARTIFACTS

TASK: Extract workflow I/O and artifact production.

OUTPUTS:
	•	WORKFLOW_IO_MAP.json
```

---

## Prompt
- prompt_id: rte_w_w3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W3
- short_name: Multi Service Coordination / Compose Tmux
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W3_MULTI_SERVICE_COORDINATION___COMPOSE_TMUX.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_COORDINATION_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W3

## Goal
Produce `W3` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- `WORKFLOW_IO_MAP.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_COORDINATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_COORDINATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W3`
    - `id_rule`: `WORKFLOW_COORDINATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the multi-service coordination (compose/tmux) partition as primary scan surface.
2. Map Docker Compose coordination: scan `compose.yml` for `depends_on`, `healthcheck`, `networks`, and `volumes` that define service inter-dependencies.
3. Map TMUX coordination: scan `tmux.conf` or `*.tmux.yaml` for session layouts, window names, and specific commands sent to panes via `send-keys`.
4. Identify synchronization points: search for `wait-for-it.sh`, `nc -z`, or health-check polling loops that block service startup until dependencies are ready.
5. Locate global orchestrator logic: identify scripts like `dopemux.rb` or `install.sh` that trigger both Compose and TMUX setup in sequence.
6. Build coordination graph: trace how a single orchestrator command propagates through TMUX panes to eventually start Docker Compose services.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in service coordination.
8. For each WORKFLOW_COORDINATION_SURFACE item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID.
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W3 — MULTI-SERVICE COORDINATION / COMPOSE / TMUX

TASK: Tie compose + tmux + scripts into a coordination view.

OUTPUTS:
	•	WORKFLOW_COORDINATION_SURFACE.json
```

---

## Prompt
- prompt_id: rte_w_w4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W4
- short_name: Workflow Failure Modes / Recovery
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W4_WORKFLOW_FAILURE_MODES___RECOVERY.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_FAILURE_RECOVERY.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W4

## Goal
Produce `W4` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- `WORKFLOW_IO_MAP.json`
- `WORKFLOW_COORDINATION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_FAILURE_RECOVERY.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_FAILURE_RECOVERY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W4`
    - `id_rule`: `WORKFLOW_FAILURE_RECOVERY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**:
    *   Load `WORKFLOW_INVENTORY.json`, `WORKFLOW_PARTITIONS.json`, `WORKFLOW_CATALOG.json`, `WORKFLOW_IO_MAP.json`, `WORKFLOW_COORDINATION_SURFACE.json`.
    *   Define the primary scan surface using the workflow failure modes and recovery partition from `WORKFLOW_PARTITIONS.json`.
    *   Identify all files within the `Source scope` (lines 9-13: `scripts/**`, `services/**`, `docs/02-how-to/**`, `docs/03-reference/**`, `compose.yml`) for detailed content analysis.

2.  **Extract Workflow Failure Modes and Recovery Facts**:
    For each file identified in the scan context, perform the following pattern matching and fact extraction:
    *   **Shell Scripts (`.sh`, `.bash`, etc.)**:
        *   **`set -e`**:
            *   Identify lines containing `set -e` or shell shebangs like `#!/bin/bash -e`.
            *   **Extract**: The presence of `set -e`.
            *   **Classify**: "Script-level exit-on-error".
        *   **`trap`**:
            *   Identify lines containing `trap <command> <signal>`.
            *   **Extract**: The `command` and `signal` arguments (e.g., `trap 'cleanup_func' ERR EXIT`).
            *   **Classify**: "Signal-based recovery/cleanup".
        *   **`rollback` logic**:
            *   Identify functions, blocks, or conditional statements (`if ... then ... else ...`) that contain keywords like `rollback`, `undo`, `cleanup`, `revert`, especially when associated with error conditions or `trap` handlers.
            *   **Extract**: The function/block name, relevant conditional logic, and the commands executed.
            *   **Classify**: "Imperative rollback mechanism".
    *   **Python Files (`.py`)**:
        *   **`try/except`**:
            *   Identify `try: ... except <ExceptionType>: ...` blocks.
            *   **Extract**: The `ExceptionType` (e.g., `IOError`, `Exception` as `e`), the content of the `except` block, and the surrounding function/method.
            *   **Classify**: "Exception handling block".
        *   **`retry` decorators**:
            *   Identify functions/methods decorated with `@retry`, `@tenacity.retry`, or similar patterns (e.g., `from retrying import retry`).
            *   **Extract**: The decorator name, its arguments (e.g., `attempts`, `delay`, `stop_max_attempt_number`), and the decorated function/method name.
            *   **Classify**: "Automated retry mechanism".
        *   **`rollback` logic**:
            *   Identify `finally:` blocks or specific functions/methods (e.g., `_rollback()`, `cleanup_resources()`) that are called within error handling contexts or explicitly named `rollback`, `cleanup`, `undo`.
            *   **Extract**: The function/method name, its arguments, and its execution context (e.g., `finally` block).
            *   **Classify**: "Programmatic rollback mechanism".
    *   **YAML Files (`.yaml`, `compose.yml`, `docs/02-how-to/**.yaml` for CI/CD workflows)**:
        *   **Error handling directives**:
            *   Scan for keys like `restart_policy` (in `compose.yml` services), `on-failure`, `continue-on-error` (in CI/CD job steps), `healthcheck` configurations, `condition: on-failure`.
            *   **Extract**: The service/job/step name, the specific directive (e.g., `restart_policy: on-failure`), and its configured value.
            *   **Classify**: "Declarative failure handling".

3.  **Populate WORKFLOW_FAILURE_RECOVERY Items**:
    *   For each identified fact, construct a `WORKFLOW_FAILURE_RECOVERY` item.
    *   **`id`**: Generate a deterministic ID using `WORKFLOW_FAILURE_RECOVERY:<stable-hash(path|symbol|name|extracted_value)>`. For a `set -e` in a script, `name` could be the script name, and `extracted_value` "set -e".
    *   **`path`**: Record the repo-relative path to the source file (e.g., `scripts/my_script.sh`).
    *   **`line_range`**: Record the exact `[start, end]` line numbers of the evidence.
    *   **`evidence`**: Create an evidence object as per lines 58-63: `{"path": "<repo-relative-path>", "line_range": [<start>, <end>], "excerpt": "<exact substring <=200 chars>"}`. The `excerpt` must be the exact text snippet.
    *   **`type`**: Record the classification from Step 2 (e.g., "Script-level exit-on-error", "Exception handling block").
    *   **`details`**: Include relevant extracted data (e.g., `exception_type`, `retry_attempts`, `trap_signal`, `restart_policy_value`).

4.  **Correlate with Upstream Artifacts**:
    *   For each `WORKFLOW_FAILURE_RECOVERY` item, attempt to link it to specific workflows, services, or I/O operations defined in `WORKFLOW_INVENTORY.json`, `WORKFLOW_CATALOG.json`, `WORKFLOW_IO_MAP.json`, or `WORKFLOW_COORDINATION_SURFACE.json`.
    *   Establish relationships (edges) in the output graph if applicable, documenting the connection with evidence.

5.  **Finalize and Validate Outputs**:
    *   Ensure all `WORKFLOW_FAILURE_RECOVERY` items have an `id`, `path`, `line_range`, and at least one `evidence` object.
    *   Apply deterministic sorting (lines 71-72) and deduplication (lines 73-77) to the `items` list.
    *   Validate all required fields (lines 40-41); emit `UNKNOWN` with `missing_evidence_reason` for unsatisfied values.
    *   Emit exactly one `WORKFLOW_FAILURE_RECOVERY.json` file.
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
# PROMPT_W4 — WORKFLOW FAILURE MODES / RECOVERY

TASK: Identify workflow failure modes and recovery paths.

OUTPUTS:
	•	WORKFLOW_FAILURE_RECOVERY.json
```

---

## Prompt
- prompt_id: rte_w_w5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W5
- short_name: Workflow State Dependencies / Home Vs Repo
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W5_WORKFLOW_STATE_DEPENDENCIES___HOME_VS_REPO.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_STATE_COUPLING.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W5

## Goal
Produce `W5` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- `WORKFLOW_IO_MAP.json`
- `WORKFLOW_COORDINATION_SURFACE.json`
- `WORKFLOW_FAILURE_RECOVERY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_STATE_COUPLING.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_STATE_COUPLING.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W5`
    - `id_rule`: `WORKFLOW_STATE_COUPLING:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**:
    *   Load `WORKFLOW_INVENTORY.json`, `WORKFLOW_PARTITIONS.json`, `WORKFLOW_CATALOG.json`, `WORKFLOW_IO_MAP.json`, `WORKFLOW_COORDINATION_SURFACE.json`, `WORKFLOW_FAILURE_RECOVERY.json`.
    *   Define the primary scan surface using the workflow state dependencies (home vs repo) partition from `WORKFLOW_PARTITIONS.json`.
    *   Identify all files within the `Source scope` (lines 9-13: `scripts/**`, `services/**`, `docs/02-how-to/**`, `docs/03-reference/**`, `compose.yml`) for detailed content analysis.

2.  **Extract Workflow State Coupling Facts (Home vs. Repo)**:
    For each file identified in the scan context, perform the following pattern matching and fact extraction to identify paths resolved outside the repository root:
    *   **Python Files (`.py`)**:
        *   **`os.path.expanduser`**:
            *   Identify calls to `os.path.expanduser(<path>)`.
            *   **Extract**: The argument `<path>` and the context of the call.
            *   **Classify**: "Home directory expansion".
        *   **Explicit Home Dir Environment Variables**:
            *   Identify usage of `os.environ.get('HOME')`, `os.getenv('HOME')`, `os.path.expandvars('$HOME')`, `os.path.expandvars('%USERPROFILE%')` or similar in string formatting/concatenation.
            *   **Extract**: The environment variable accessed and its usage context.
            *   **Classify**: "Environment variable based home path".
        *   **Hardcoded Home Paths**:
            *   Identify string literals containing `~`, `/home/`, `/Users/` (e.g., `pathlib.Path('~/config.ini')`, `"/home/user/data"`).
            *   **Extract**: The literal path string.
            *   **Classify**: "Hardcoded absolute/home path".
        *   **Absolute Path Construction/Resolution**:
            *   Identify `os.path.abspath()`, `os.path.realpath()`, or `pathlib.Path.resolve()` calls on paths that are not demonstrably relative to the repository root.
            *   **Extract**: The path argument and the context.
            *   **Classify**: "Absolute path resolution".
    *   **Shell Scripts (`.sh`, `.bash`, etc.)**:
        *   **Tilde `~`**:
            *   Identify usage of `~`, `~/`, `~$USER/`, or similar expansions in commands or assignments.
            *   **Extract**: The specific tilde expansion and its context.
            *   **Classify**: "Shell tilde expansion".
        *   **Explicit Home Dir Environment Variables**:
            *   Identify usage of `$HOME`, `$USERPROFILE`, or similar environment variables in commands or assignments.
            *   **Extract**: The environment variable and its usage context.
            *   **Classify**: "Shell environment variable based home path".
        *   **Hardcoded Home Paths**:
            *   Identify string literals containing `/home/`, `/Users/` (e.g., `cd /home/user/logs`, `cp /Users/shared/file`).
            *   **Extract**: The literal path string.
            *   **Classify**: "Hardcoded absolute/home path".
        *   **Absolute Path Resolution Commands**:
            *   Identify commands like `readlink -f`, `realpath` when applied to paths that may resolve outside the repository.
            *   **Extract**: The command and its path argument.
            *   **Classify**: "Shell absolute path resolution".
    *   **YAML Files (`.yaml`, `compose.yml`, `docs/02-how-to/**.yaml` for configuration)**:
        *   **Hardcoded Home Paths**:
            *   Identify string values for volume mounts, paths, or configuration parameters containing `~`, `/home/`, `/Users/` (e.g., `volumes: - ~/data:/app/data`, `config_path: /Users/shared/config.json`).
            *   **Extract**: The path string and its YAML key context.
            *   **Classify**: "Declarative hardcoded absolute/home path".
        *   **Environment Variable Usage**:
            *   Identify use of environment variable syntax like `${HOME}` or `$HOME` within path strings.
            *   **Extract**: The environment variable used in the path.
            *   **Classify**: "Declarative environment variable path".
    *   **Identify codebase reaching outside repository root**: For each identified path, determine if it resolves to a location *not* contained within the repository's root directory. This is the primary criterion for an item of type `WORKFLOW_STATE_COUPLING`.

3.  **Populate WORKFLOW_STATE_COUPLING Items**:
    *   For each identified fact representing a state dependency outside the repository root, construct a `WORKFLOW_STATE_COUPLING` item.
    *   **`id`**: Generate a deterministic ID using `WORKFLOW_STATE_COUPLING:<stable-hash(path|symbol|name|extracted_path_expression)>`. For a `~/config`, `name` could be the variable name or file, and `extracted_path_expression` "`/~/config`".
    *   **`path`**: Record the repo-relative path to the source file (e.g., `services/my_service/main.py`).
    *   **`line_range`**: Record the exact `[start, end]` line numbers of the evidence.
    *   **`evidence`**: Create an evidence object as per lines 58-63: `{"path": "<repo-relative-path>", "line_range": [<start>, <end>], "excerpt": "<exact substring <=200 chars>"}`. The `excerpt` must be the exact text snippet.
    *   **`type`**: Record the classification from Step 2 (e.g., "Home directory expansion", "Hardcoded absolute/home path").
    *   **`expression`**: Store the extracted path expression (e.g., `os.path.expanduser('~/.config')`, `~/data`, `/home/user/logs`, `$HOME/cache`).
    *   **`is_absolute`**: Boolean indicating if the path expression is inherently absolute or resolves to an absolute path.
    *   **`is_home_relative`**: Boolean indicating if the path expression uses `~` or `$HOME`.

4.  **Correlate with Upstream Artifacts**:
    *   For each `WORKFLOW_STATE_COUPLING` item, attempt to link it to specific workflows or services defined in `WORKFLOW_INVENTORY.json` or `WORKFLOW_CATALOG.json`.
    *   Establish relationships (edges) in the output graph if applicable, documenting the connection with evidence.

5.  **Finalize and Validate Outputs**:
    *   Ensure all `WORKFLOW_STATE_COUPLING` items have an `id`, `path`, `line_range`, and at least one `evidence` object.
    *   Apply deterministic sorting (lines 71-72) and deduplication (lines 73-77) to the `items` list.
    *   Validate all required fields (lines 40-41); emit `UNKNOWN` with `missing_evidence_reason` for unsatisfied values.
    *   Emit exactly one `WORKFLOW_STATE_COUPLING.json` file.
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
# PROMPT_W5 — WORKFLOW STATE DEPENDENCIES / HOME VS REPO

TASK: Extract workflow state coupling points.

OUTPUTS:
	•	WORKFLOW_STATE_COUPLING.json
```

---

## Prompt
- prompt_id: rte_w_w9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: W
- step: W9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_W9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("W")
- invokes: WORKFLOW_MERGED.json, WORKFLOW_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: W phase step W9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_W9

## Goal
Produce `W9` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- `WORKFLOW_IO_MAP.json`
- `WORKFLOW_COORDINATION_SURFACE.json`
- `WORKFLOW_FAILURE_RECOVERY.json`
- `WORKFLOW_STATE_COUPLING.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_MERGED.json`
- `WORKFLOW_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W9`
    - `id_rule`: `WORKFLOW_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `WORKFLOW_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W9`
    - `id_rule`: `WORKFLOW_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all W-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all WORKFLOW_* artifacts into WORKFLOW_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all W-Phase artifacts present, coverage complete, sort order deterministic; emit WORKFLOW_QA
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
# PROMPT_W9 — Workflows merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge workflow artifacts and report coverage.

OUTPUTS:
  • WORKFLOW_MERGED.json
  • WORKFLOW_QA.json

RULES:
  • Normalize arrays by stable sort and remove duplicates.
```

---

## Prompt
- prompt_id: rte_b_b0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: B
- step: B0
- short_name: Boundary Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("B")
- invokes: BOUNDARY_INVENTORY.json, BOUNDARY_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: B phase step B0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_B0

## Goal
Produce `B0` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
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
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B0`
    - `id_rule`: `BOUNDARY_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `BOUNDARY_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B0`
    - `id_rule`: `BOUNDARY_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `src/**`, `services/**`, `docs/90-adr/**`, `.claude/settings.json`, and `AGENTS.md` for all API surface definitions, FastAPI `Depends()` auth enforcements, tool permissions, and agent declarations.
2. For each discovered endpoint or boundary point, extract: protocol (HTTP/MCP/CLI), method signature, input validation, authentication requirements, and rate limit annotations with exact evidence.
3. Catalog all **Refusal Rails** and authorization guard clauses by tracing `raise HTTPException`, decorator chains, and policy enforcement functions in `.claude/settings.json`.
4. Inventory **Agent Boundaries**: Extract role-based access control (RBAC) and tool-use constraints declared in `AGENTS.md`.
5. Cross-reference discovered boundaries against `services/registry.yaml` to assign each boundary to its canonical service_id.
6. Build the partition plan by grouping boundary items into cohesive partitions based on owning service, protocol family, and directory locality.
7. Legacy Context is intent guidance only and is never evidence.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B0 — BOUNDARY INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the boundary plane.

OUTPUTS:
	•	BOUNDARY_INVENTORY.json
	•	BOUNDARY_PARTITIONS.json
```

---

## Prompt
- prompt_id: rte_b_b1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: B
- step: B1
- short_name: Boundary Assertions / Code Enforcement Points
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_B1_BOUNDARY_ASSERTIONS___CODE_ENFORCEMENT_POINTS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("B")
- invokes: BOUNDARY_ENFORCEMENT_POINTS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: B phase step B1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_B1

## Goal
Produce `B1` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_ENFORCEMENT_POINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_ENFORCEMENT_POINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B1`
    - `id_rule`: `BOUNDARY_ENFORCEMENT_POINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `BOUNDARY_INVENTORY.json` and `BOUNDARY_PARTITIONS.json` from upstream.
2. Extract **Enforcement Points**: Scan code for FastAPI `Depends(verify_...)`, `Security()`, or custom auth decorators that guard sensitive operations.
3. Map **Assertion Logic**: Identify the concrete check performed (e.g., token validation, role-based scope verification) with exact evidence.
4. Trace **Enforcement Context**: Link checks to the specific service or agent (from `AGENTS.md`) being protected.
5. Cross-reference with inventory to identify overrides, shadows, or gaps where a declared boundary lacks code enforcement.
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
# PROMPT_B1 — BOUNDARY ASSERTIONS / CODE ENFORCEMENT POINTS

TASK: Find boundary checks in code/config/docs (facts only).

OUTPUTS:
	•	BOUNDARY_ENFORCEMENT_POINTS.json
```

---

## Prompt
- prompt_id: rte_b_b2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: B
- step: B2
- short_name: Refusal Rails / Guardrails Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_B2_REFUSAL_RAILS___GUARDRAILS_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("B")
- invokes: REFUSAL_GUARDRAILS_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: B phase step B2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_B2

## Goal
Produce `B2` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- `BOUNDARY_ENFORCEMENT_POINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REFUSAL_GUARDRAILS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REFUSAL_GUARDRAILS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B2`
    - `id_rule`: `REFUSAL_GUARDRAILS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `BOUNDARY_INVENTORY.json` and `BOUNDARY_PARTITIONS.json` from upstream.
2. Extract **Refusal Rails**: Identify exception handlers (e.g., `401 Unauthorized`, `403 Forbidden`) and trace how errors propagate to the caller.
3. Map **Guardrail Surface**: Locate `.claude/settings.json` "preventions" or "guardrails" sections and match them to evidenced code blocks.
4. Identify **Policy Enforcement**: Scan for centralized policy checks or internal `check_policy` functions that govern cross-service access.
5. Resolve **Shadowed Guards**: If multiple guards apply (e.g., middleware + endpoint decorator), document the sequence and precedence.
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
# PROMPT_B2 — REFUSAL RAILS / GUARDRAILS SURFACE

TASK: Extract refusal rails and guardrails.

OUTPUTS:
	•	REFUSAL_GUARDRAILS_SURFACE.json
```

---

## Prompt
- prompt_id: rte_b_b3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: B
- step: B3
- short_name: Bypass Paths / Weak Guards
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_B3_BYPASS_PATHS___WEAK_GUARDS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("B")
- invokes: BOUNDARY_BYPASS_RISKS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: B phase step B3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_B3

## Goal
Produce `B3` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- `BOUNDARY_ENFORCEMENT_POINTS.json`
- `REFUSAL_GUARDRAILS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_BYPASS_RISKS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_BYPASS_RISKS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B3`
    - `id_rule`: `BOUNDARY_BYPASS_RISKS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `BOUNDARY_ENFORCEMENT_POINTS.json` and `REFUSAL_GUARDRAILS_SURFACE.json`.
2. Identify **Weak Guards**: Locate checks that can be circumvented via `DEBUG=True`, `SKIP_AUTH=1`, or missing `Depends()` on sensitive sub-routes.
3. Trace **Bypass Paths**: Document evidenced routes that allow unauthorized access to sensitive data without triggering refusal rails.
4. Check **Permission Leaks**: Verify if `.claude/settings.json` allows tools to access files or perform actions outside their declared scope.
5. Arbitration: Only report bypasses evidenced by an alternate code path or a missing check near a sensitive operation.
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
# PROMPT_B3 — BYPASS PATHS / WEAK GUARDS

TASK: Identify bypass paths and weak guards.

RULE: only report bypass when evidenced by an alternate path or missing check near a sensitive operation.

OUTPUTS:
	•	BOUNDARY_BYPASS_RISKS.json
```

---

## Prompt
- prompt_id: rte_b_b9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: B
- step: B9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_B9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("B")
- invokes: BOUNDARY_MERGED.json, BOUNDARY_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: B phase step B9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_B9

## Goal
Produce `B9` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- `BOUNDARY_ENFORCEMENT_POINTS.json`
- `REFUSAL_GUARDRAILS_SURFACE.json`
- `BOUNDARY_BYPASS_RISKS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_MERGED.json`
- `BOUNDARY_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B9`
    - `id_rule`: `BOUNDARY_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `BOUNDARY_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B9`
    - `id_rule`: `BOUNDARY_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all B-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all BOUNDARY_* artifacts into BOUNDARY_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all B-Phase artifacts present, coverage complete, sort order deterministic; emit BOUNDARY_QA
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
# PROMPT_B9 — Boundary merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge boundary artifacts and confirm coverage.

OUTPUTS:
  • BOUNDARY_MERGED.json
  • BOUNDARY_QA.json

RULES:
  • Apply stable sort and deduplicate like-for-like entries.
```

---

## Prompt
- prompt_id: rte_g_g0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G0
- short_name: Governance Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G0_GOVERNANCE_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: GOV_INVENTORY.json, GOV_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G0

## Goal
Produce `G0` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G0`
    - `id_rule`: `GOV_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `GOV_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G0`
    - `id_rule`: `GOV_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `.github/workflows/**`, `.pre-commit-config.yaml`, `CODEOWNERS`, `LICENSE`, `.gitignore`, and `pyproject.toml` for all governance and policy definitions.
2. Extract **CI Gates**: Identify job names, triggers, and success criteria in GitHub Actions that enforce quality bars.
3. Extract **Policy Files**: Inventory `LICENSE`, `CODEOWNERS`, and repo-level `.gitignore` rules for mandatory enforcement.
4. Extract **Environment Scoping**: Identify where `.env` or configuration files are loaded in scripts and entrypoints.
5. Catalog **Credential Loaders**: Locate code patterns that load secrets (e.g., `os.getenv`, `pydantic.BaseSettings`) without exposing values.
6. Build the partition plan by grouping governance items into cohesive partitions: CI, Hygiene, Policy, and Security.
7. Legacy Context is intent guidance only and is never evidence.
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
# PROMPT_G0 — GOVERNANCE INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the governance plane.

OUTPUTS:
	•	GOV_INVENTORY.json
	•	GOV_PARTITIONS.json
```

---

## Prompt
- prompt_id: rte_g_g1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G1
- short_name: Ci Gates / Quality Bars
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G1_CI_GATES___QUALITY_BARS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: GOV_CI_GATES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G1

## Goal
Produce `G1` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_CI_GATES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_CI_GATES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G1`
    - `id_rule`: `GOV_CI_GATES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `GOV_INVENTORY.json` and `GOV_PARTITIONS.json` from upstream.
2. Extract **CI Gate Logic**: Scan `.github/workflows/` for `jobs`, `steps`, and `if:` conditions that enforce quality bars (lint, test, build).
3. Map **Quality Bar Requirements**: Identify exact tool versions and command-line flags used for enforcement (e.g., `pytest --min-coverage=80`) with evidence.
4. Trace **Failure Modes**: Document how a CI failure impacts the overall pipeline (e.g., block merge, notify owners).
5. Cross-reference with inventory to identify shadows or gaps where a declared policy lacks a corresponding CI gate.
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
# PROMPT_G1 — CI GATES / QUALITY BARS

TASK: Extract CI gates and quality bars.

OUTPUTS:
	•	GOV_CI_GATES.json
```

---

## Prompt
- prompt_id: rte_g_g2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G2
- short_name: Repo Hygiene / Allowlists / Policies
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G2_REPO_HYGIENE___ALLOWLISTS___POLICIES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: GOV_HYGIENE_POLICIES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G2

## Goal
Produce `G2` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_HYGIENE_POLICIES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_HYGIENE_POLICIES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G2`
    - `id_rule`: `GOV_HYGIENE_POLICIES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `GOV_INVENTORY.json` and `GOV_PARTITIONS.json` from upstream.
2. Extract **Hygiene Rules**: Parse `.gitignore` for forbidden patterns and `.pre-commit-config.yaml` for mandatory hooks.
3. Map **Allowlists**: Identify explicitly permitted exceptions in policy files or linter configs (e.g., `.eslintignore`) with evidence.
4. Trace **Enforcement Scripts**: Locate any `scripts/` or `Make` targets that perform "lint-like" repo hygiene checks.
5. Identify **Drift**: Flag any files in the repo that violate the current `.gitignore` or `CODEOWNERS` rules.
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
# PROMPT_G2 — REPO HYGIENE / ALLOWLISTS / POLICIES

TASK: Extract repo hygiene policies and allowlists.

OUTPUTS:
	•	GOV_HYGIENE_POLICIES.json
```

---

## Prompt
- prompt_id: rte_g_g3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G3
- short_name: Policy Files / Enforcement
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G3_POLICY_FILES___ENFORCEMENT.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: GOV_POLICIES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G3

## Goal
Produce `G3` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- `GOV_HYGIENE_POLICIES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_POLICIES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_POLICIES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G3`
    - `id_rule`: `GOV_POLICIES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `GOV_INVENTORY.json`, `GOV_CI_GATES.json`, and `GOV_HYGIENE_POLICIES.json`.
2. Extract **Policy Enforcement Paths**: Connect policy declarations (e.g., `LICENSE`) to concrete CI gates or pre-commit hooks.
3. Map **Authority Owners**: Link specific files/folders to owners identified in `CODEOWNERS` with exact evidence.
4. Document **Escalation Rails**: Trace how policy violations are reported and to whom (based on `CODEOWNERS` or PR templates).
5. Resolve **Conflicting Policies**: If multiple policies apply to the same scope, apply the most restrictive rule and cite both.
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
# PROMPT_G3 — Policy files + enforcement

ROLE: Governance extractor.
GOAL: catalog policy files and the enforcement mechanisms they trigger.

OUTPUTS:
  • GOV_POLICIES.json

RULES:
  • Document each policy file and any hooks/scripts that enforce it.
```

---

## Prompt
- prompt_id: rte_g_g4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G4
- short_name: Security / Secrets / Reduction Facts
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G4_SECURITY___SECRETS___REDUCTION_FACTS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: GOV_SECRETS_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G4

## Goal
Produce `G4` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- `GOV_HYGIENE_POLICIES.json`
- `GOV_POLICIES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_SECRETS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_SECRETS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G4`
    - `id_rule`: `GOV_SECRETS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `GOV_INVENTORY.json` and relevant partitions from upstream.
2. Extract **Credential Reading Patterns**: Scan code for `os.environ`, `dotenv`, and Secret Manager API calls (symbols and paths only).
3. Identify **Hardcoded Risk**: Scan for potential hardcoded secrets or default credentials in configs and scripts (Patterns + Paths only).
4. Map **Secret Loaders**: Identify exact symbols/classes responsible for injecting secrets into the runtime environment.
5. Check **.gitignore Violations**: Verify if any evidenced secret files (e.g., `.env`, `*.pem`) are missing from `.gitignore`.
6. Arbitration: Never extract secret contents; document only the location, pattern, and loader symbol with evidence.
7. Legacy Context is intent guidance only and is never evidence.
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
# PROMPT_G4 — SECURITY / SECRETS / REDUCTION FACTS

TASK: Extract security and secrets reduction facts.

RULE: No secret contents; extract paths + patterns + loaders only.

OUTPUTS:
	•	GOV_SECRETS_SURFACE.json
```

---

## Prompt
- prompt_id: rte_g_g5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G5
- short_name: Auth Flow Surface
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G5_AUTH_FLOW_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: AUTH_FLOW_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G5

## Goal
Produce `G5` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Extract authentication and authorization flow implementations: dependency-injection auth guards, JWT/OAuth2 token handling, permission checks, role-based access control, and session management patterns across all services.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `shared/**`
- `plugins/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- `GOV_HYGIENE_POLICIES.json`
- `GOV_POLICIES.json`
- `GOV_SECRETS_SURFACE.json`
- `API_DASHBOARD_SURFACE.json`
- `SERVICE_ENTRYPOINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `AUTH_FLOW_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"AUTH_FLOW_SURFACE@v1","items":[...]}`
- Output contracts:
  - `AUTH_FLOW_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G5`
    - `id_rule`: `AUTH_FLOW_SURFACE:<stable-hash(path|symbol|auth_type)>`
    - `required_item_fields`: `id, auth_type, mechanism, protected_symbol, enforcement_point, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "AUTH_FLOW_SURFACE:<hash>",
  "auth_type": "dependency_injection|decorator_guard|middleware|manual_check|token_validation|role_check|permission_check|session_management",
  "mechanism": "fastapi_depends|oauth2_password_bearer|http_bearer|api_key_header|api_key_query|jwt_decode|custom_middleware|manual_if_check",
  "protected_symbol": "<function or route being protected>",
  "guard_symbol": "<the auth function/class invoked, e.g. 'get_current_user'>",
  "guard_module": "<repo-relative path to guard implementation>",
  "enforcement_point": "route_parameter|decorator|middleware_stack|manual_inline",
  "token_type": "jwt|oauth2|api_key|session_cookie|bearer_opaque|none",
  "claims_extracted": ["<JWT claims accessed, e.g. 'sub', 'exp', 'roles'>"],
  "roles_required": ["<role strings if RBAC, e.g. 'admin', 'editor'>"],
  "permissions_required": ["<permission strings if fine-grained, e.g. 'tasks:write'>"],
  "fallback_behavior": "401_unauthorized|403_forbidden|redirect_login|silent_skip|custom",
  "is_optional": false,
  "bypass_conditions": "<conditions under which auth is skipped, or null>",
  "service_name": "<service name from registry.yaml>",
  "path": "<repo-relative path to auth usage site>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Auth Type Definitions
- **dependency_injection**: Auth enforced via FastAPI `Depends(get_current_user)` or similar DI pattern
- **decorator_guard**: Auth enforced via `@requires_auth`, `@login_required`, or custom decorators
- **middleware**: Auth enforced at middleware layer before route handlers execute
- **manual_check**: Inline `if not user.is_authenticated` or equivalent conditional checks
- **token_validation**: Explicit JWT decode/verify calls (e.g., `jwt.decode()`, `jose.jwt.decode()`)
- **role_check**: Role-based access control check (e.g., `if user.role != 'admin': raise 403`)
- **permission_check**: Fine-grained permission check (e.g., `if 'tasks:write' not in user.permissions`)
- **session_management**: Session creation, validation, or destruction (login/logout flows)

### Mechanism Definitions
- **fastapi_depends**: `Depends(callable)` in FastAPI route signature
- **oauth2_password_bearer**: `OAuth2PasswordBearer(tokenUrl=...)` scheme
- **http_bearer**: `HTTPBearer()` or `HTTPAuthorizationCredentials` scheme
- **api_key_header**: API key extracted from request header
- **api_key_query**: API key extracted from query parameter
- **jwt_decode**: Direct call to `jwt.decode()`, `jose.jwt.decode()`, or equivalent
- **custom_middleware**: Application-level middleware class or function
- **manual_if_check**: Inline conditional checking auth state

### Enforcement Point Definitions
- **route_parameter**: Auth injected as a route handler parameter via DI
- **decorator**: Auth checked via decorator before handler body executes
- **middleware_stack**: Auth checked in middleware before request reaches router
- **manual_inline**: Auth checked inside handler body with manual conditional logic

### Fallback Behavior Definitions
- **401_unauthorized**: Returns HTTP 401 with WWW-Authenticate header
- **403_forbidden**: Returns HTTP 403 Forbidden
- **redirect_login**: Redirects to login page/endpoint
- **silent_skip**: Silently proceeds without auth (dangerous)
- **custom**: Application-defined error handling

### Worked Example
```json
{
  "id": "AUTH_FLOW_SURFACE:f2a7c3d1",
  "auth_type": "dependency_injection",
  "mechanism": "fastapi_depends",
  "protected_symbol": "decompose_task",
  "guard_symbol": "get_current_user",
  "guard_module": "services/task-orchestrator/app/auth.py",
  "enforcement_point": "route_parameter",
  "token_type": "jwt",
  "claims_extracted": ["sub", "exp"],
  "roles_required": [],
  "permissions_required": [],
  "fallback_behavior": "401_unauthorized",
  "is_optional": false,
  "bypass_conditions": null,
  "service_name": "task-orchestrator",
  "path": "services/task-orchestrator/app/api/pm_tools.py",
  "line_range": [45, 48],
  "status": "ok",
  "evidence": [{"path": "services/task-orchestrator/app/api/pm_tools.py", "line_range": [45, 46], "excerpt": "async def decompose_task(request: DecomposeRequest, user = Depends(get_current_user)):"}]
}
```

## Extraction Procedure
1. Load upstream GOV_INVENTORY, GOV_PARTITIONS, and GOV_SECRETS_SURFACE; use governance partition as scan surface.
2. Scan for **FastAPI Depends auth**: search for `Depends(get_current_user)`, `Depends(get_api_key)`, or any `Depends()` call where the injected callable performs authentication. Record the route handler, guard function, and module path.
3. Scan for **OAuth2 schemes**: search for `OAuth2PasswordBearer(`, `OAuth2PasswordRequestForm`, `HTTPBearer(`, `HTTPAuthorizationCredentials`. Record scheme configuration (tokenUrl, auto_error).
4. Scan for **JWT token handling**: search for `jwt.decode(`, `jose.jwt.decode(`, `JWTBearer`, token validation functions. Record claims accessed, secret key source, algorithm.
5. Scan for **decorator-based auth**: search for `@requires_auth`, `@login_required`, `@permission_required`, `@roles_required` or custom auth decorators. Record decorator name and wrapped function.
6. Scan for **middleware auth**: search for middleware classes/functions that inspect `Authorization` headers, cookies, or session tokens. Record middleware registration and protected routes.
7. Scan for **role/permission checks**: search for `user.role`, `user.is_admin`, `user.permissions`, `has_permission(`, `check_role(`. Record the check, required values, and fallback behavior.
8. Scan for **session management**: search for session creation (`session[`, `request.session`), login/logout handlers, session configuration.
9. Cross-reference with `API_DASHBOARD_SURFACE.json` to identify which routes have auth and which don't — flag unprotected endpoints that handle sensitive data.
10. Build deterministic IDs using stable content keys `(path|symbol|auth_type)`.
11. Attach evidence to every item with exact excerpts showing the auth pattern.
12. Emit exactly `AUTH_FLOW_SURFACE.json` and no additional files.

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
- Do not invent auth mechanisms, guard functions, or permission requirements.
- Do not assume auth is present because a route handles sensitive data — only record explicit auth code.
- If auth presence is ambiguous (e.g., inherited from middleware but not visible in handler), mark `status: needs_review`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not extract secret values (tokens, keys, passwords) — only extract paths, patterns, and loaders.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Dynamic auth: if auth is configured at runtime (e.g., feature flags), emit with `status: needs_review` and note the dynamic configuration.
- Transitive auth: if a function delegates to another for auth checking, record both the delegation site and the actual check, linked by evidence.

---

## Prompt
- prompt_id: rte_g_g9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: G
- step: G9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("G")
- invokes: GOV_MERGED.json, GOV_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: G phase step G9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_G9

## Goal
Produce `G9` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- `GOV_HYGIENE_POLICIES.json`
- `GOV_POLICIES.json`
- `GOV_SECRETS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_MERGED.json`
- `GOV_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G9`
    - `id_rule`: `GOV_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `GOV_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G9`
    - `id_rule`: `GOV_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all G-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all GOV_* artifacts into GOV_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all G-Phase artifacts present, coverage complete, sort order deterministic; emit GOV_QA
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
# PROMPT_G9 — Governance merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge governance outputs and provide coverage/consistency checks.

OUTPUTS:
  • GOV_MERGED.json
  • GOV_QA.json

RULES:
  • Sort arrays stably and remove duplicates.
```

---

## Prompt
- prompt_id: rte_x_x0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: X
- step: X0
- short_name: Feature Index Inventory / Partition Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("X")
- invokes: FEATURE_INDEX_INVENTORY.json, FEATURE_INDEX_PARTITIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: X phase step X0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_X0

## Goal
Produce `X0` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `README.md`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_INDEX_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X0`
    - `id_rule`: `FEATURE_INDEX_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FEATURE_INDEX_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X0`
    - `id_rule`: `FEATURE_INDEX_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan feature-relevant sources (user-facing code, docs, configs) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the feature-relevant sources (user-facing code, docs, configs) domain
3. Build FEATURE_PARTITIONS by grouping files into logical categories with rationale
4. For each FEATURE_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each FEATURE_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
# PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN

TASK: Build feature-index inventory and deterministic partition plan.

SCAN TARGETS:
- services/
- src/
- docs/
- config/
- scripts/
- Makefile
- docker-compose*.yml

OUTPUTS:
- FEATURE_INDEX_INVENTORY.json
- FEATURE_INDEX_PARTITIONS.json

RULES:
- Enumerate candidate feature surfaces, owning code paths, and related docs.
- Partition deterministically for downstream X1 extraction.
- Preserve literal evidence and source paths.
```

---

## Prompt
- prompt_id: rte_x_x1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: X
- step: X1
- short_name: Feature Surface Extract
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_X1_FEATURE_SURFACE_EXTRACT.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("X")
- invokes: FEATURE_SURFACE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: X phase step X1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_X1

## Goal
Produce `X1` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `services/agents/**`
- `src/dopemux/hooks/**`



- `README.md`
- Upstream normalized artifacts available to this step:
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X1`
    - `id_rule`: `FEATURE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the feature surface extraction partition as primary scan surface
2. Extract feature surface extraction facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted feature surface extraction elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each FEATURE_SURFACES item, populate `id`, required fields, and `evidence`
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
# PROMPT_X1_FEATURE_SURFACE_EXTRACT

TASK: Extract feature surfaces from each partition.

OUTPUTS:
- FEATURE_SURFACE.json

REQUIREMENTS:
- Capture feature id/name, entrypoints, triggers, service touchpoints, and user-visible outcomes.
- Include provenance with file path and evidence snippets.
- Do not infer behavior without direct evidence.

DOPEMUX FEATURE CATEGORIES (use as classification hints):
- ADHD Engine: signal collectors, scorers, suggestion engines, focus sessions, break scheduling
- Two-Plane Architecture: PM plane, Cognitive plane, plane coordination, boundary enforcement
- Hook System: event hooks, lifecycle hooks, Claude Code hooks, git hooks, event bus
- MCP Integration: MCP servers, MCP proxies, tool definitions, transport layers
- Profile System: user profiles, editor profiles, extraction profiles
- Agent Orchestration: agent launch, supervisor patterns, session management, agent communication
- CLI System: Click/Typer commands, command groups, CLI routing
- Editor Integration: Claude Code, Codex Desktop, Copilot, Vibe, VS Code extensions
```

---

## Prompt
- prompt_id: rte_x_x2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: X
- step: X2
- short_name: Feature To Code Map
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_X2_FEATURE_TO_CODE_MAP.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("X")
- invokes: FEATURE_CODE_MAP.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: X phase step X2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_X2

## Goal
Produce `X2` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `README.md`
- Upstream normalized artifacts available to this step:
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- `FEATURE_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_CODE_MAP.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_CODE_MAP.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X2`
    - `id_rule`: `FEATURE_CODE_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the feature-to-code mapping partition as primary scan surface
2. Extract feature-to-code mapping facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted feature-to-code mapping elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each FEATURE_CODE_MAP item, populate `id`, required fields, and `evidence`
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
# PROMPT_X2_FEATURE_TO_CODE_MAP

TASK: Build deterministic map from feature surface to code implementation loci.

OUTPUTS:
- FEATURE_CODE_MAP.json

REQUIREMENTS:
- For each feature, map to concrete modules/functions/scripts/services.
- Include coupling points to control-plane and runtime config where present.
- Retain unresolved mappings in unknowns with reasons.
```

---

## Prompt
- prompt_id: rte_x_x3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: X
- step: X3
- short_name: Feature To Doc Map
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_X3_FEATURE_TO_DOC_MAP.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("X")
- invokes: FEATURE_DOC_MAP.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: X phase step X3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_X3

## Goal
Produce `X3` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `README.md`
- Upstream normalized artifacts available to this step:
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- `FEATURE_SURFACE.json`
- `FEATURE_CODE_MAP.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_DOC_MAP.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_DOC_MAP.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X3`
    - `id_rule`: `FEATURE_DOC_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the feature-to-doc mapping partition as primary scan surface
2. Extract feature-to-doc mapping facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted feature-to-doc mapping elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each FEATURE_DOC_MAP item, populate `id`, required fields, and `evidence`
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
# PROMPT_X3_FEATURE_TO_DOC_MAP

TASK: Map features to documentation coverage and drift signals.

OUTPUTS:
- FEATURE_DOC_MAP.json

REQUIREMENTS:
- Link features to docs pages, ADR/RFC references, and runbooks.
- Flag missing or stale docs links as explicit gaps.
- Keep mapping deterministic and evidence-based.
```

---

## Prompt
- prompt_id: rte_x_x4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: X
- step: X4
- short_name: Feature Dependency Graph
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_X4_FEATURE_DEPENDENCY_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("X")
- invokes: FEATURE_DEP_GRAPH.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: X phase step X4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_X4

## Goal
Produce `X4` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `README.md`
- Upstream normalized artifacts available to this step:
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- `FEATURE_SURFACE.json`
- `FEATURE_CODE_MAP.json`
- `FEATURE_DOC_MAP.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_DEP_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_DEP_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X4`
    - `id_rule`: `FEATURE_DEP_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the feature dependency graph partition as primary scan surface
2. Extract feature dependency graph facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted feature dependency graph elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each FEATURE_DEPS item, populate `id`, required fields, and `evidence`
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
# PROMPT_X4_FEATURE_DEPENDENCY_GRAPH

TASK: Build feature dependency graph across services, configs, and workflows.

OUTPUTS:
- FEATURE_DEP_GRAPH.json

REQUIREMENTS:
- Emit directed dependencies between features and critical infra/services.
- Include runtime-mode and environment dependencies where observable.
- Preserve cycle information; do not collapse conflicting edges.
```

---

## Prompt
- prompt_id: rte_x_x9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: X
- step: X9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_X9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("X")
- invokes: FEATURE_INDEX_MERGED.json, FEATURE_INDEX_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: field_extraction
- purpose: X phase step X9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_X9

## Goal
Produce `X9` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `README.md`
- Upstream normalized artifacts available to this step:
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- `FEATURE_SURFACE.json`
- `FEATURE_CODE_MAP.json`
- `FEATURE_DOC_MAP.json`
- `FEATURE_DEP_GRAPH.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_INDEX_MERGED.json`
- `FEATURE_INDEX_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_INDEX_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X9`
    - `id_rule`: `FEATURE_INDEX_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FEATURE_INDEX_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X9`
    - `id_rule`: `FEATURE_INDEX_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all X-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all FEATURE_* artifacts into FEATURE_INDEX_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all X-Phase artifacts present, coverage complete, sort order deterministic; emit FEATURE_INDEX_QA
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
# PROMPT_X9_MERGE___QA

TASK: Merge Feature Index outputs and emit QA.

INPUTS:
- Raw/partition outputs from X0..X4.

OUTPUTS:
- FEATURE_INDEX_MERGED.json
- FEATURE_INDEX_QA.json

RULES:
- Deterministic merge only; no rescans.
- Deduplicate by stable feature identity keys.
- Report coverage, unresolved mappings, and schema/required-field checks.
```

---
