# Prompt Bundle: Active Repair and Retry Bundle

## Prompt
- prompt_id: rte_q_q0
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Q
- step: Q0
- short_name: Pipeline Completeness / Manifest
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q0_PIPELINE_COMPLETENESS___MANIFEST.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Q")
- invokes: QA_RUN_MANIFEST.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: json_repair
- purpose: Q phase step Q0 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Q0

## Goal
Produce `Q0` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_RUN_MANIFEST.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_RUN_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q0`
    - `id_rule`: `QA_RUN_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the pipeline completeness and manifest partition as primary scan surface
2. Extract pipeline completeness and manifest facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted pipeline completeness and manifest elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each QA_RUN_MANIFEST item, populate `id`, required fields, and `evidence`
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
# PROMPT_Q0 — PIPELINE COMPLETENESS / MANIFEST

TASK: Build a manifest of pipeline completeness.

INPUTS: current run dirs */raw, */norm, */qa.

OUTPUTS:
	•	QA_RUN_MANIFEST.json
```

---

## Prompt
- prompt_id: rte_q_q1
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Q
- step: Q1
- short_name: Missing Artifacts / Recovery Plan
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q1_MISSING_ARTIFACTS___RECOVERY_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Q")
- invokes: QA_MISSING_ARTIFACTS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: json_repair
- purpose: Q phase step Q1 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Q1

## Goal
Produce `Q1` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- `QA_RUN_MANIFEST.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_MISSING_ARTIFACTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_MISSING_ARTIFACTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q1`
    - `id_rule`: `QA_MISSING_ARTIFACTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the missing artifacts and recovery plan partition as primary scan surface
2. Extract missing artifacts and recovery plan facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted missing artifacts and recovery plan elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each QA_MISSING_ARTIFACTS item, populate `id`, required fields, and `evidence`
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
# PROMPT_Q1 — MISSING ARTIFACTS / RECOVERY PLAN

TASK: Identify missing artifacts and propose a recovery plan.

OUTPUTS:
	•	QA_MISSING_ARTIFACTS.json
```

---

## Prompt
- prompt_id: rte_q_q11
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Q
- step: Q11
- short_name: Artifact Collision Report
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q11_ARTIFACT_COLLISION_REPORT.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Q")
- invokes: QA_ARTIFACT_COLLISION_REPORT.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: json_repair
- purpose: Q phase step Q11 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Q11

## Goal
Produce `Q11` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Detect declared artifact collisions across the promptpack and emit a collision report that operators can use to stop unsafe norm overwrites before a live run.

## Inputs
- Source scope (scan these roots first):
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
  - `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
  - `services/repo-truth-extractor/promptsets/v4/prompts/`
- Required upstream artifacts:
  - `Q_PROMPTPACK_DECLARED_OUTPUTS.json`
- Optional upstream artifacts:
  - `QA_PROMPT_COLLISIONS.json`
  - `QA_RUN_MANIFEST.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/prompts/phase_s/registry.json`
- Constraint:
  - Compute collisions from declared promptpack metadata and in-scope files only. Do not treat repository filesystem presence as proof of canonical writers.

## Outputs
- `QA_ARTIFACT_COLLISION_REPORT.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `QA_ARTIFACT_COLLISION_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q11`
    - `id_rule`: `QA_ARTIFACT_COLLISION_REPORT:<stable-hash(artifact_name|writers|risk)>`
    - `required_item_fields`: `id, artifact_name, writers, risk, recommendation, notes, evidence`
    - `required_registry_fields`: `path, line_range, id`
- Item shape:
  - `artifact_name`: emitted artifact under review
  - `writers`: array of `{phase, step_id, prompt_file}`
  - `risk`: collision class such as `overwrites_in_norm`, `shadowed_writer`, or `unknown_writer`
  - `recommendation`: one of `LATEST_WINS`, `APPEND_LEDGER`, `MERGE_BY_ID`, `MANUAL_REVIEW`
  - `notes`: deterministic explanatory strings
  - `evidence`: array of evidence objects proving each writer declaration

## Extraction Procedure
1. Load `Q_PROMPTPACK_DECLARED_OUTPUTS.json` and normalize each declared writer by `(phase, step_id, artifact_name)`.
2. Cross-check declarations against `promptset.yaml`, `artifacts.yaml`, and prompt files to confirm the writer list is supported by in-scope contract data.
3. Group rows by `artifact_name` and identify cases where two or more distinct steps declare the same output, or where registry metadata conflicts with prompt text.
4. Build one output item per collision candidate with deterministic `id`, sorted `writers`, sorted `notes`, and explicit `risk`.
5. When a writer cannot be proven from promptpack declarations, omit the unproven writer from `writers`, add a note containing `UNKNOWN`, and preserve evidence gaps.
6. Attach at least one evidence object to every collision item and to every non-derived writer entry.
7. Emit exactly `QA_ARTIFACT_COLLISION_REPORT.json` and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

---

## Prompt
- prompt_id: rte_q_q2
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Q
- step: Q2
- short_name: Duplicate Ids / Prompt Collisions
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q2_DUPLICATE_IDS___PROMPT_COLLISIONS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Q")
- invokes: QA_PROMPT_COLLISIONS.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: json_repair
- purpose: Q phase step Q2 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Q2

## Goal
Produce `Q2` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- `QA_RUN_MANIFEST.json`
- `QA_MISSING_ARTIFACTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_PROMPT_COLLISIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_PROMPT_COLLISIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q2`
    - `id_rule`: `QA_PROMPT_COLLISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the duplicate IDs and prompt collisions partition as primary scan surface
2. Extract duplicate IDs and prompt collisions facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted duplicate IDs and prompt collisions elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each QA_PROMPT_COLLISIONS item, populate `id`, required fields, and `evidence`
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
# PROMPT_Q2 — DUPLICATE IDS / PROMPT COLLISIONS

TASK: Detect duplicate IDs and prompt collisions.

OUTPUTS:
	•	QA_PROMPT_COLLISIONS.json
```

---

## Prompt
- prompt_id: rte_q_q3
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Q
- step: Q3
- short_name: Drift Detection / Norm Diffs
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q3_DRIFT_DETECTION___NORM_DIFFS.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Q")
- invokes: QA_NORM_DRIFT_REPORT.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: json_repair
- purpose: Q phase step Q3 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Q3

## Goal
Produce `Q3` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- `QA_RUN_MANIFEST.json`
- `QA_MISSING_ARTIFACTS.json`
- `QA_PROMPT_COLLISIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_NORM_DRIFT_REPORT.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_NORM_DRIFT_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q3`
    - `id_rule`: `QA_NORM_DRIFT_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the drift detection and norm diffs partition as primary scan surface
2. Extract drift detection and norm diffs facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted drift detection and norm diffs elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each QA_NORM_DRIFT_REPORT item, populate `id`, required fields, and `evidence`
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
# PROMPT_Q3 — DRIFT DETECTION / NORM DIFFS

TASK: compare raw vs norm counts + schema sanity + truncation flags.

OUTPUTS:
	•	QA_NORM_DRIFT_REPORT.json
```

---

## Prompt
- prompt_id: rte_q_q9
- canonical_scope: rte_runtime_v5_contract_v4
- version_line: contract_v4
- phase: Q
- step: Q9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: services/repo-truth-extractor/run_extraction_v5.py:get_phase_prompts("Q")
- invokes: PIPELINE_DOCTOR_REPORT.json, QA_SERVICE_COVERAGE.json
- status: active
- authority_role: contract_authority
- prompt_kind: runtime_prompt
- category: json_repair
- purpose: Q phase step Q9 in the active runtime sequence.
- output_contract: structured_json
- validator_dependency: yes
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: secondary
- notes: Loaded by run_extraction_v5.py from promptsets/v4; runtime is v5 while prompt contract authority remains v4.

### Full prompt text
# PROMPT_Q9

## Goal
Produce `Q9` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- `QA_RUN_MANIFEST.json`
- `QA_MISSING_ARTIFACTS.json`
- `QA_PROMPT_COLLISIONS.json`
- `QA_NORM_DRIFT_REPORT.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PIPELINE_DOCTOR_REPORT.json`
- `QA_SERVICE_COVERAGE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PIPELINE_DOCTOR_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q9`
    - `id_rule`: `PIPELINE_DOCTOR_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `QA_SERVICE_COVERAGE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `single_payload`
    - `canonical_writer_step_id`: `Q9`
    - `id_rule`: `QA_SERVICE_COVERAGE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`

## Extraction Procedure
1. Load all Q-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all QA_* artifacts into PIPELINE_DOCTOR_REPORT using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all Q-Phase artifacts present, coverage complete, sort order deterministic; emit QA_SERVICE_COVERAGE
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
# PROMPT_Q9 — Pipeline doctor merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge pipeline doctor outputs into a single report.

OUTPUTS:
  • PIPELINE_DOCTOR_REPORT.json

RULES:
  • Maintain deterministic ordering and mark any empty sections explicitly.
```

---
