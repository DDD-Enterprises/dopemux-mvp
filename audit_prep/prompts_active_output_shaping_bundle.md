# Prompt Bundle: Active Output Shaping Bundle

## Prompt
- prompt_id: rte_t_t0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T0
- short_name: Task Packet Factory
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T0_TASK_PACKET_FACTORY.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: PROJECT_INSTRUCTIONS.md, TP_BACKLOG_TOPN.json, TP_INDEX.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T0 in the active runtime sequence.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T0

## Goal
Produce `T0` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PROJECT_INSTRUCTIONS.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T0`
    - `id_rule`: `PROJECT_INSTRUCTIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for task packet factory design
2. Analyze extraction outputs to identify actionable work items for TASK_PACKET_FACTORY
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
Goal: Produce an implementation-ready top-10 TP backlog from R/X norm artifacts.

Role:
- Arbitration planner only. Do not implement code.
- Truth authority is R norm artifacts.

Inputs:
- R norm artifacts (R0-R8 outputs) from extraction/runs/<run_id>/R_arbitration/norm/
- X feature/risk catalogs from extraction/runs/<run_id>/X_feature_index/norm/
- Repo governance constraints from AGENTS.md and .claude/PROJECT_INSTRUCTIONS.md

Outputs:
- TP_BACKLOG_TOPN.json
- TP_INDEX.json

Required schema keys for TP_BACKLOG_TOPN.json:
- run_id
- generated_at
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].priority
- packets[].problem_statement
- packets[].authority_inputs (array of repo paths to R artifacts)
- packets[].invariants (array)
- packets[].scope_in
- packets[].scope_out
- packets[].acceptance_criteria (array)
- packets[].rollback
- packets[].stop_conditions (array)
- packets[].implementer_target

Hard rules:
- implementer_target must equal "Codex Desktop (GPT-5.3-Codex)" for every packet.
- authority_inputs must reference only R/X norm artifacts by path.
- No packet may require repo re-scan or truth reinterpretation.
- No packet may omit deterministic verification commands.

Stop conditions:
- Any TP missing scope, invariants, commands, acceptance criteria, rollback, or stop conditions.
- Any TP proposes a refactor without evidence-driven necessity.
```

---

## Prompt
- prompt_id: rte_t_t1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T1
- short_name: Emit Task Packets / Top10
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T1_EMIT_TASK_PACKETS___TOP10.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: TP_PACKETS_TOP10.partX.md, TP_PACKET_IMPLEMENTATION_INDEX.json, TP_BACKLOG_TOPN.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T1 in the active runtime sequence.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T1

## Goal
Produce `T1` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_BACKLOG_TOPN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_PACKETS_TOP10.partX.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T1`
    - `id_rule`: `TP_PACKETS_TOP10:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_PACKET_IMPLEMENTATION_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T1`
    - `id_rule`: `TP_PACKET_IMPLEMENTATION_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for top-10 task packet emission
2. Analyze extraction outputs to identify actionable work items for TASK_PACKETS_TOP10
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
MODE: Arbitration output only. Do not implement code.
EVIDENCE REQUIRED: Every load-bearing claim must map to authority input paths.
OUTPUT: Markdown packets plus JSON index.
STABLE ORDER: Sort packets by priority, then tp_id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase T1: Emit Task Packets (Top 10)

Outputs:
- TP_PACKETS_TOP10.partX.md
- TP_PACKET_IMPLEMENTATION_INDEX.json

Prompt:
ROLE: GPT-5.2 (arbitration).
Inputs:
- TP_BACKLOG_TOPN.json
- R norm artifact paths referenced by each backlog item

Action:
Generate complete Task Packet markdowns for the top 10 items in the backlog.
Each packet must be implementation-ready for Codex Desktop and must not relitigate truth.

Required packet header block (exact keys):
- Implementer: Codex Desktop (GPT-5.3-Codex)
- Authority Inputs: <list of R/X norm artifact paths>
- Forbidden: re-run extraction; reinterpret truth without new evidence
- Required Proofs: git diff --stat, tests run, acceptance checks, rollback verification

Required sections per packet:
- Objective
- Scope (IN / OUT)
- Invariants
- Plan
- Exact commands
- Acceptance criteria
- Rollback
- Stop conditions

Required schema keys for TP_PACKET_IMPLEMENTATION_INDEX.json:
- run_id
- generated_at
- packet_count
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].implementer_target
- packets[].authority_inputs
- packets[].packet_markdown_locator
```

---

## Prompt
- prompt_id: rte_t_t2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T2
- short_name: Packet Schema / Authority Rules
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T2_PACKET_SCHEMA___AUTHORITY_RULES.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: TP_SCHEMA.json, TP_AUTHORITY_RULES.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T2

## Goal
Produce `T2` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_SCHEMA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T2`
    - `id_rule`: `TP_SCHEMA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_AUTHORITY_RULES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T2`
    - `id_rule`: `TP_AUTHORITY_RULES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for packet schema and authority rules
2. Analyze extraction outputs to identify actionable work items for PACKET_SCHEMA_RULES
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
# PROMPT_T2 — PACKET SCHEMA / AUTHORITY RULES

TASK: Define the canonical Task Packet schema and authority hierarchy used by Phase T.

OUTPUTS:
- TP_SCHEMA.json
- TP_AUTHORITY_RULES.json

Rules:
- implementer_target must be exactly `Codex Desktop (GPT-5.3-Codex)`.
- Authority hierarchy is strict: R norm artifacts > X norm artifacts > policy docs.
- Every packet must include evidence-backed `authority_inputs` paths.
- No packet may require re-scan, truth reinterpretation, or undocumented assumptions.
- Define required fields, validation constraints, and failure reasons for schema noncompliance.
```

---

## Prompt
- prompt_id: rte_t_t3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T3
- short_name: Packet Generation / Batched
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T3_PACKET_GENERATION___BATCHED.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: TP_BATCHED_PACKETS.partX.md, TP_BATCH_INDEX.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T3 in the active runtime sequence.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T3

## Goal
Produce `T3` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_BATCHED_PACKETS.partX.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T3`
    - `id_rule`: `TP_BATCHED_PACKETS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_BATCH_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T3`
    - `id_rule`: `TP_BATCH_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for batched packet generation
2. Analyze extraction outputs to identify actionable work items for PACKET_BATCH
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
# PROMPT_T3 — PACKET GENERATION / BATCHED

TASK: Generate implementation-ready Task Packets in deterministic batches from R and X norm artifacts.

OUTPUTS:
- TP_BATCHED_PACKETS.partX.md
- TP_BATCH_INDEX.json

Rules:
- Emit packets in stable order by priority, then `tp_id`.
- Each packet must include: objective, scope in/out, invariants, plan, exact commands, acceptance criteria, rollback, stop conditions.
- Each packet must include a commit plan and explicit acceptance gates.
- Every load-bearing claim must cite `authority_inputs` paths.
- If output exceeds context, split into `.partX` artifacts and include full index references in `TP_BATCH_INDEX.json`.
```

---

## Prompt
- prompt_id: rte_t_t4
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T4
- short_name: Packet Dedup / Collision Resolution
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T4_PACKET_DEDUP___COLLISION_RESOLUTION.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: TP_DEDUPED.json, TP_COLLISIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T4

## Goal
Produce `T4` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_DEDUPED.json`
- `TP_COLLISIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_DEDUPED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T4`
    - `id_rule`: `TP_DEDUPED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_COLLISIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T4`
    - `id_rule`: `TP_COLLISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for packet dedup and collision resolution
2. Analyze extraction outputs to identify actionable work items for PACKET_DEDUP
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
# PROMPT_T4 — PACKET DEDUP / COLLISION RESOLUTION

TASK: Deduplicate Task Packets and resolve title/id collisions deterministically.

OUTPUTS:
- TP_DEDUPED.json
- TP_COLLISIONS.json

Rules:
- Detect duplicate `tp_id`, duplicate normalized titles, and materially overlapping scopes.
- Resolve collisions with deterministic tie-breaks: higher evidence density, lower blast radius, earlier dependency.
- Preserve traceability from deduped packets to source packet IDs.
- Record dropped/merged packets and reason codes in `TP_COLLISIONS.json`.
```

---

## Prompt
- prompt_id: rte_t_t5
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T5
- short_name: Packet Ordering / Run Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T5_PACKET_ORDERING___RUN_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: TP_RUN_PLAN.json, TP_BACKLOG_TOPN.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T5

## Goal
Produce `T5` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`
- `TP_DEDUPED.json`
- `TP_COLLISIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_RUN_PLAN.json`
- `TP_BACKLOG_TOPN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_RUN_PLAN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T5`
    - `id_rule`: `TP_RUN_PLAN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for packet ordering and run plan
2. Analyze extraction outputs to identify actionable work items for PACKET_RUN_PLAN
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
# PROMPT_T5 — PACKET ORDERING / RUN PLAN

TASK: Build the execution order for Task Packets using dependency-aware planning.

OUTPUTS:
- TP_RUN_PLAN.json
- TP_BACKLOG_TOPN.json

Rules:
- Build a dependency graph across packets and topologically sort the plan.
- Default precedence: control plane -> extraction -> arbitration -> synthesis.
- Produce a runnable sequence with blocking dependencies, parallel-safe groups, and gate checks.
- Include explicit prerequisites and postconditions per packet.
```

---

## Prompt
- prompt_id: rte_t_t9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: T
- step: T9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_T9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("T")
- invokes: TP_INDEX.json, TP_MERGED.json, TP_QA.json, TP_SUMMARY.md, TP_BACKLOG_TOPN.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: T phase step T9 in the active runtime sequence.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_T9

## Goal
Produce `T9` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`
- `TP_DEDUPED.json`
- `TP_COLLISIONS.json`
- `TP_RUN_PLAN.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_INDEX.json`
- `TP_MERGED.json`
- `TP_QA.json`
- `TP_SUMMARY.md`
- `TP_BACKLOG_TOPN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_SUMMARY.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_SUMMARY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all T-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all TASK_* artifacts into TASK_PACKETS_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all T-Phase artifacts present, coverage complete, sort order deterministic; emit TASK_PACKETS_QA
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
# PROMPT_T9 — MERGE / QA

TASK: Merge all Phase T packet artifacts, run QA, and emit canonical Task Packet outputs.

OUTPUTS:
- TP_INDEX.json
- TP_MERGED.json
- TP_QA.json
- TP_SUMMARY.md
- TP_BACKLOG_TOPN.json

QA requirements:
- Validate required schema fields for every packet.
- Validate implementer target, evidence paths, and acceptance/rollback completeness.
- Emit missing-evidence list and unresolved-collision list.
- Emit packet counts by priority and dependency tier.
- Fail closed if required canonical outputs cannot be produced.
```

---

## Prompt
- prompt_id: rte_z_z0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Z
- step: Z0
- short_name: Freeze Inventory / Checksums
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Z0_FREEZE_INVENTORY___CHECKSUMS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Z")
- invokes: FREEZE_FILE_INDEX.json, FREEZE_CHECKSUMS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: Z phase step Z0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Z0

## Goal
Produce `Z0` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FREEZE_FILE_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z0`
    - `id_rule`: `FREEZE_FILE_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FREEZE_CHECKSUMS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z0`
    - `id_rule`: `FREEZE_CHECKSUMS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all finalized extraction artifacts as input for freeze inventory and checksums
2. Compute checksums and integrity metadata for FREEZE_INVENTORY
3. Build FREEZE_INVENTORY: compile all required components with provenance tracking
4. Validate completeness: verify all expected artifacts are present and checksums match
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
# PROMPT_Z0 — FREEZE INVENTORY / CHECKSUMS

TASK: Build an inventory and checksums for the handoff freeze.

OUTPUTS:
	•	FREEZE_FILE_INDEX.json
	•	FREEZE_CHECKSUMS.json
```

---

## Prompt
- prompt_id: rte_z_z1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Z
- step: Z1
- short_name: Proof Pack / Runbook
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Z1_PROOF_PACK___RUNBOOK.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Z")
- invokes: PROOF_PACK.md
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: Z phase step Z1 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: partial
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Z1

## Goal
Produce the `Z1` proof-pack output for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable freeze evidence and proof-pack assembly facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PROOF_PACK.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PROOF_PACK.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `Z1`
    - `id_rule`: `PROOF_PACK:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load all finalized freeze artifacts required to assemble `PROOF_PACK.md`.
2. Compute or verify proof-pack integrity metadata from the supplied freeze inputs.
3. Build `PROOF_PACK.md` as the single declared output with provenance tracking for each required section.
4. Validate completeness: verify all expected proof-pack inputs are present and note any missing components explicitly in the output.
5. For each load-bearing section, attach evidence per the schema contract above.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared output and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Z1 — PROOF PACK

TASK: Generate a proof pack snapshot.

OUTPUTS:
	•	PROOF_PACK.md
```

---

## Prompt
- prompt_id: rte_z_z2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Z
- step: Z2
- short_name: Opus Input Bundle / Manifest
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Z2_OPUS_INPUT_BUNDLE___MANIFEST.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Z")
- invokes: OPUS_INPUT_MANIFEST.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: Z phase step Z2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Z2

## Goal
Produce `Z2` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- `PROOF_PACK.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `OPUS_INPUT_MANIFEST.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `OPUS_INPUT_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z2`
    - `id_rule`: `OPUS_INPUT_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all finalized extraction artifacts as input for opus input bundle and manifest
2. Compute checksums and integrity metadata for OPUS_INPUT_BUNDLE
3. Build OPUS_INPUT_BUNDLE: compile all required components with provenance tracking
4. Validate completeness: verify all expected artifacts are present and checksums match
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
# PROMPT_Z2 — OPUS INPUT BUNDLE / MANIFEST

TASK: Generate a deterministic export bundle manifest for Opus + Codex.

OUTPUTS:
	•	OPUS_INPUT_MANIFEST.json
```

---

## Prompt
- prompt_id: rte_z_z9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Z
- step: Z9
- short_name: Freeze Manifest / Checksums
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Z")
- invokes: FREEZE_MANIFEST.json, FREEZE_README.md, FREEZE_QA.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: output_normalization
- purpose: Z phase step Z9 in the active runtime sequence.
- output_contract: semi_structured_json
- validator_dependency: yes
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: possible
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Z9

## Goal
Produce `Z9` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- `PROOF_PACK.md`
- `OPUS_INPUT_MANIFEST.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FREEZE_MANIFEST.json`
- `FREEZE_README.md`
- `FREEZE_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FREEZE_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FREEZE_README.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_README:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `FREEZE_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all Z-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all FREEZE_* artifacts into FREEZE_MANIFEST using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all Z-Phase artifacts present, coverage complete, sort order deterministic; emit FREEZE_CHECKSUMS
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
# PROMPT_Z9 — FREEZE MANIFEST / CHECKSUMS

TASK: Produce a deterministic freeze handoff manifest with verification instructions and QA.

OUTPUTS:
- FREEZE_MANIFEST.json
- FREEZE_README.md
- FREEZE_QA.json

Rules:
- Include SHA-256 for every file in phase `norm/` and `qa/` outputs for A/H/D/C/E/W/B/G/Q/R/X/T/Z when present.
- Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
- Record missing expected artifacts and failure counts by phase.
- `FREEZE_README.md` must document deterministic verification commands.
```

---

## Prompt
- prompt_id: rte_s_s0
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S0
- short_name: Opus Architecture Synthesis
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S0 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S0 - OPUS ARCHITECTURE + SUBSYSTEM SYNTHESIS (registry mode)

OUTPUTS:
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md

Use only supplied synthesis inputs. Do not rescan the repo. Every non-trivial claim must cite evidence anchors. If evidence is missing, write UNKNOWN and list the missing artifacts.

---

## Prompt
- prompt_id: rte_s_s1
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S1
- short_name: Opus Mcp To Hooks Migration Plan
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S1 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S1 - OPUS MCP TO HOOKS MIGRATION PLAN (registry mode)

OUTPUTS:
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md

Use only provided synthesis artifacts. Keep the plan mechanical, evidence-bounded, and fail closed on missing evidence.

---

## Prompt
- prompt_id: rte_s_s10
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S10
- short_name: Redaction Pass
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S10_REDACTION_PASS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S10_REDACTION_PASS.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S10 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S10 - REDACTION PASS

OUTPUTS:
- S10_REDACTION_PASS.json

SYSTEM
You are a redaction auditor. You never print secrets. You only flag locations for redaction.
Output JSON only.

USER
Input:
- CANONICAL: JSON object

Task:
Identify locations that look like secrets or sensitive material.
Do not output the secret value. Only output the JSON path and reason.

Reason codes:
- looks_like_api_key
- looks_like_token
- looks_like_password
- looks_like_private_url
- looks_like_personal_data

Rules:
- If the input cannot be evaluated safely, set status="FAIL_CLOSED".
- Never reveal or restate a secret-like value.

Output JSON:
{
  "status": "OK" | "FAIL_CLOSED",
  "findings": [
    {"path": "dot.path", "reason": "looks_like_api_key"}
  ]
}

CANONICAL:
{{CANONICAL_JSON}}

---

## Prompt
- prompt_id: rte_s_s11
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S11
- short_name: Contract Linter
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S11_CONTRACT_LINTER.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S11_CONTRACT_LINTER.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S11 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S11 - CONTRACT LINTER

OUTPUTS:
- S11_CONTRACT_LINTER.json

SYSTEM
You are a contract linter. You validate cross-field invariants that schemas do not enforce.
Output JSON only.

USER
Inputs:
- CANONICAL: JSON object
- CONTRACT_RULES: list of invariant rules with ids and descriptions

Task:
Evaluate all rules against CANONICAL.

Rules:
- If a rule requires evidence not present, mark it as UNKNOWN and set status="NEEDS_REVIEW".
- Do not invent violations. Only report what you can prove from CANONICAL.
- If the input is incomplete for reliable evaluation, set status="FAIL_CLOSED".

Output JSON:
{
  "status": "PASS" | "FAIL" | "NEEDS_REVIEW" | "FAIL_CLOSED",
  "violations": [
    {"rule_id": "...", "path": "dot.path", "severity": "high|med|low", "detail": "..."}
  ],
  "unknowns": [
    {"rule_id": "...", "reason": "..."}
  ]
}

CONTRACT_RULES:
{{CONTRACT_RULES_JSON}}

CANONICAL:
{{CANONICAL_JSON}}

---

## Prompt
- prompt_id: rte_s_s12
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S12
- short_name: Stability Signature
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S12_STABILITY_SIGNATURE.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S12_STABILITY_SIGNATURE.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S12 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S12 - STABILITY SIGNATURE

OUTPUTS:
- S12_STABILITY_SIGNATURE.json

SYSTEM
You are a stability signature generator. Output must be deterministic.
Output JSON only.

USER
Input:
- CANONICAL: JSON object

Task:
Produce a deterministic signature for regression tracking.

Rules:
- Do not include secret values.
- Use stable normalization assumptions described in NORMALIZATION.
- Provide section hashes and counts.
- If normalization cannot be applied safely, set status="FAIL_CLOSED".

Output JSON:
{
  "status": "OK" | "FAIL_CLOSED",
  "normalization": {
    "sorted_keys": true,
    "stable_lists": true,
    "notes": "..."
  },
  "hashes": [
    {"section": "root", "hash_alg": "sha256", "hash": "<hex>"}
  ],
  "counts": [
    {"name": "items", "count": 0}
  ]
}

NORMALIZATION:
- Sort object keys lexicographically.
- For lists: do not reorder unless list elements have stable ids; if stable ids exist, sort by id.
- Hash algorithm is sha256 over the normalized JSON string.

CANONICAL:
{{CANONICAL_JSON}}

---

## Prompt
- prompt_id: rte_s_s2
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S2
- short_name: Decision Dossier
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S2_DECISION_DOSSIER.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S2_DECISION_DOSSIER.md
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S2 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S2 - DECISION DOSSIER (registry mode)

OUTPUTS:
- S2_DECISION_DOSSIER.md

Convert supplied synthesis artifacts into a deterministic decision dossier. Use evidence anchors for every decision. Emit UNKNOWN when evidence is insufficient.

---

## Prompt
- prompt_id: rte_s_s3
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S3
- short_name: Arch Proof Hooks
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S3_ARCH_PROOF_HOOKS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S3_ARCH_PROOF_HOOKS.md
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S3 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S3 - ARCHITECTURE PROOF HOOKS (registry mode)

OUTPUTS:
- S3_ARCH_PROOF_HOOKS.md

Produce minimal proof hooks from supplied claims only. Do not claim commands were executed. If a proof hook cannot be defined from evidence, emit UNKNOWN.

---

## Prompt
- prompt_id: rte_s_s4
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S4
- short_name: Truth Pack Index
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S4_TRUTH_PACK_INDEX.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S4_TRUTH_PACK_INDEX.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S4 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S4 - TRUTH PACK INDEX (registry mode)

OUTPUTS:
- S4_TRUTH_PACK_INDEX.json

Build a deterministic truth-pack provenance index from supplied inputs only. Do not fabricate hashes, paths, or source phases.

---

## Prompt
- prompt_id: rte_s_s5
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S5
- short_name: Decision Graph
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S5_DECISION_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S5_DECISION_GRAPH.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S5 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S5 - DECISION GRAPH (registry mode)

OUTPUTS:
- S5_DECISION_GRAPH.json

Build a deterministic graph of decisions, risks, conflicts, and evidence from supplied synthesis inputs only. Omit ungrounded edges and record UNKNOWN notes instead.

---

## Prompt
- prompt_id: rte_s_s6
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S6
- short_name: Leantime Analysis
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S6_LEANTIME_ANALYSIS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S6_LEANTIME_ANALYSIS.md
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S6 in the active runtime sequence.
- output_contract: freeform_markdown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S6 - LEANTIME ANALYSIS (registry mode)

OUTPUTS:
- S6_LEANTIME_ANALYSIS.md

Summarize Leantime-related findings from supplied synthesis artifacts only. Preserve implemented versus planned distinctions and fail closed on missing evidence.

---

## Prompt
- prompt_id: rte_s_s7
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S7
- short_name: Dedupe Sort
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S7_DEDUPE_SORT.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S7_DEDUPE_SORT.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S7 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S7 - DEDUPE AND STABLE SORT

OUTPUTS:
- S7_DEDUPE_SORT.json

SYSTEM
You are a deterministic normalizer. You do not invent facts. You only dedupe and reorder deterministically.
Output JSON only.

USER
Inputs:
- CANONICAL: a JSON object
- RULES: dedupe_keys and stable_sort rules
- SCHEMA: JSON schema for CANONICAL

Task:
1) Remove duplicates deterministically using RULES.dedupe_keys.
2) Apply stable sorting using RULES.sort_order.
3) Do not change values other than removing exact duplicates and reordering.

Rules:
- Never merge two distinct objects unless dedupe keys match exactly.
- If duplicates have conflicting values, do not merge. Emit conflicts[] and set status="NEEDS_REVIEW".
- If required output structure cannot be preserved from the input evidence, set status="FAIL_CLOSED".
- Output ordering must be deterministic.

Output JSON:
{
  "status": "OK" | "NEEDS_REVIEW" | "FAIL_CLOSED",
  "conflicts": [
    {"key": "...", "values": [{"value": "...", "source": "..."}]}
  ],
  "output": "<normalized CANONICAL>"
}

SCHEMA:
{{SCHEMA_JSON}}

RULES:
{{RULES_JSON}}

CANONICAL:
{{CANONICAL_JSON}}

---

## Prompt
- prompt_id: rte_s_s8
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S8
- short_name: Drift Check
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S8_DRIFT_CHECK.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S8_DRIFT_CHECK.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S8 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S8 - DRIFT CHECK

OUTPUTS:
- S8_DRIFT_CHECK.json

SYSTEM
You are a deterministic diff auditor. You do not guess causes. You report exact diffs.
Output JSON only.

USER
Inputs:
- BASE: canonical output from a prior run
- NEW: canonical output from this run

Task:
Compute a stable, sorted structured diff and classify drift.

Diff kinds:
- reorder_only
- value_change
- missing_field
- added_field
- type_change

Rules:
- Do not rewrite artifacts.
- Sort diff paths deterministically.
- If only ordering differs, set reorder_only=true and status="OK".
- If either input is unusable or incomplete, fail closed with status="FAIL_CLOSED".

Output JSON:
{
  "status": "OK" | "NEEDS_REVIEW" | "FAIL_CLOSED",
  "reorder_only": true | false,
  "counts": {
    "value_change": 0,
    "missing_field": 0,
    "added_field": 0,
    "type_change": 0
  },
  "diffs": [
    {"path": "dot.path", "kind": "value_change", "base": "...", "new": "..."}
  ]
}

BASE:
{{BASE_JSON}}

NEW:
{{NEW_JSON}}

---

## Prompt
- prompt_id: rte_s_s9
- canonical_scope: rte_phase_s
- version_line: registry_v1
- phase: S
- step: S9
- short_name: Promotion Readiness
- source_path: services/repo-truth-extractor/prompts/phase_s/PROMPT_S9_PROMOTION_READINESS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("S")
- invokes: S9_PROMOTION_READINESS.json
- status: active
- authority_role: active_supporting_surface
- prompt_kind: runtime_prompt
- category: cross-source_synthesis
- purpose: S phase step S9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: secondary
- notes: Registry-driven prompt family outside promptsets/v4; still active in run_extraction_v5.py.

### Full prompt text
# PROMPT_S9 - PROMOTION READINESS

OUTPUTS:
- S9_PROMOTION_READINESS.json

SYSTEM
You are a conservative promotion gate. If uncertain, fail closed.
Output JSON only.

USER
Inputs:
- CANONICAL: final canonical artifact
- METRICS: missing_fields, conflicts, unverified, drift
- PROMOTION_RULES: Trinity and plane rules

Task:
Decide if promotion is safe, and emit a checklist.

Rules:
- PASS only if required checks are satisfied.
- If required evidence is missing, set status="FAIL_CLOSED".
- Do not assume anything is true without evidence.

Output JSON:
{
  "status": "PASS" | "FAIL" | "NEEDS_REVIEW" | "FAIL_CLOSED",
  "reasons": ["..."],
  "checklist": [
    {"id": "rule_1", "required": true, "ok": true, "note": "..."}
  ]
}

PROMOTION_RULES:
{{PROMOTION_RULES_JSON}}

METRICS:
{{METRICS_JSON}}

CANONICAL:
{{CANONICAL_JSON}}

---
