---
id: UPGRADES_PROMPTSET_AUDIT_2026-02-20
title: UPGRADES Promptset Audit (Completeness + Comprehensiveness)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Audit of the UPGRADES extraction pipeline promptset for completeness and comprehensiveness (no prompt edits).
---
# UPGRADES Promptset Audit (2026-02-20)

## Summary (Observed)
- Prompt files audited: 102 in `UPGRADES/` + 38 in `UPGRADES/_legacy_prompts/`.
- v3-active prompts (per `UPGRADES/run_extraction_v3.py` `PHASE_DIR_NAMES`): 93.
- v3-inactive prompts present in `UPGRADES/` (not in `PHASE_DIR_NAMES`): 9 (currently `M*` and `S*`).
- Heuristic completeness (UPGRADES root): complete=11, partial=53, stub=38.

Notes:
- The v3 runner enforces a strict JSON output envelope (it wraps every prompt with hard output rules),
  so this audit focuses on semantic completeness: inputs, schema, evidence, determinism, and anti-fabrication rails.

## System-of-prompts audit (Observed)

### How the prompt system executes
- Prompts are loaded per phase via `get_phase_prompts()` and are fail-closed on duplicate Step IDs. (`UPGRADES/run_extraction_v3.py`)
- Each prompt declares its output artifact names in a `Goal:` / `Outputs:` section; the runner extracts these via `extract_output_artifacts()`.
- The runner enforces a strict JSON envelope (`build_output_envelope_instructions()`), then normalizes/merges per-step outputs into `norm/<artifact_name>` (`normalize_step()`).

### Implication: output-name collisions overwrite
Because each step writes to `norm/<artifact_name>` inside the phase directory, if two steps declare the same artifact name, the later step will overwrite the earlier step's normalized artifact.

This is often intentional for merge steps (e.g., `A99`, `C9`, `T9`), but it reduces traceability for intermediate steps and can hide partial/failed merge behavior.

## Output artifact collisions (Observed, UPGRADES root)

- CONCURRENCY_RISK_LOCATIONS.json: C8, C9
- DETERMINISM_RISK_LOCATIONS.json: C8, C9
- DOC_TOPIC_CLUSTERS.json: D4, D5
- DOPE_MEMORY_CODE_SURFACE.json: C3, C9
- DOPE_MEMORY_DB_WRITES.json: C3, C9
- DOPE_MEMORY_SCHEMAS.json: C3, C9
- EVENTBUS_SURFACE.json: C2, C9
- EVENT_CONSUMERS.json: C2, C9
- EVENT_PRODUCERS.json: C2, C9
- IDEMPOTENCY_RISK_LOCATIONS.json: C8, C9
- REFUSAL_AND_GUARDRAILS_SURFACE.json: C4, C9
- REPO_COMPOSE_SERVICE_GRAPH.json: A6, A99
- REPO_HOOKS_SURFACE.json: A5, A99
- REPO_IMPLICIT_BEHAVIOR_HINTS.json: A99, A9
- REPO_INSTRUCTION_REFERENCES.json: A1, A99
- REPO_INSTRUCTION_SURFACE.json: A1, A99
- REPO_LITELLM_SURFACE.json: A7, A99
- REPO_MCP_PROXY_SURFACE.json: A3, A99
- REPO_MCP_SERVER_DEFS.json: A2, A99
- REPO_ROUTER_SURFACE.json: A4, A99
- REPO_TASKX_SURFACE.json: A8, A99
- SERVICE_ENTRYPOINTS.json: C1, C9
- TASKX_INTEGRATION_SURFACE.json: C5, C9
- TP_BACKLOG_TOPN.json: T0, T5, T9
- TP_INDEX.json: T0, T9
- TRINITY_ENFORCEMENT_SURFACE.json: C4, C9
- WORKFLOW_RUNNER_SURFACE.json: C6, C9

## Completeness breakdown by phase (Heuristic, UPGRADES root)

- Phase A: complete=10, partial=1, stub=0
- Phase B: complete=0, partial=0, stub=5
- Phase C: complete=0, partial=2, stub=8
- Phase D: complete=0, partial=6, stub=0
- Phase E: complete=0, partial=4, stub=4
- Phase G: complete=0, partial=0, stub=6
- Phase H: complete=1, partial=8, stub=0
- Phase M: complete=0, partial=7, stub=0
- Phase Q: complete=0, partial=0, stub=5
- Phase R: complete=0, partial=9, stub=0
- Phase S: complete=0, partial=2, stub=0
- Phase T: complete=0, partial=7, stub=0
- Phase W: complete=0, partial=0, stub=7
- Phase X: complete=0, partial=6, stub=0
- Phase Z: complete=0, partial=1, stub=3

## Gaps that affect completeness/comprehensiveness (Observed -> Implications)

### 1) Many phase prompt bodies are schema-light or schema-absent
- Several phases (notably `B`, `G`, `Q`, `W`, most of `C`) contain prompts that only state a task + output filename, without defining the payload shape, stable IDs, or evidence fields.
- The runner *will* still produce a file, but downstream arbitration becomes less reliable when payloads vary run-to-run.

### 2) Evidence requirements are inconsistent with runner QA expectations
- The runner's per-step QA checks for `path`, `line_range`, and `id` keys in merged JSON items (`REQUIRED_ITEM_KEYS` in `UPGRADES/run_extraction_v3.py`).
- Many prompts ask for "cite" or "evidence" in prose, but do not require these keys explicitly, so QA will likely show missing-key counts.

### 3) Determinism vs timestamps
- Multiple prompts include `generated_at` in required shapes.
- The runner also emits `generated_at` in step QA JSON, which is inherently non-deterministic.
- If drift detection is meant to be signal-bearing, the promptset should either avoid timestamps in normative artifacts or explicitly isolate them.

### 4) Active vs inactive prompt drift
- `M*` and `S*` prompts exist in `UPGRADES/` but are not part of the v3 phase set (no `M`/`S` in `PHASE_DIR_NAMES`).
- `_legacy_prompts/` contains older variants that are often *more explicit* about evidence/determinism/coverage than the active stubs.


## Per-prompt audit table (UPGRADES root)

| Step | Prompt | Outputs | Rating | Missing | Flags |
| --- | --- | --- | --- | --- | --- |
| A0 | UPGRADES/PROMPT_A0_REPO_CONTROL_INVENTORY___PARTITION_PLAN.md | REPOCTRL_INVENTORY.json, REPOCTRL_PARTITIONS.json | partial | schema, determinism, anti_fabrication | - |
| A1 | UPGRADES/PROMPT_A1_INSTRUCTION_SURFACES.md | REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json | complete | schema | - |
| A2 | UPGRADES/PROMPT_A2_MCP_SERVER_DEFS.md | REPO_MCP_SERVER_DEFS.json | complete | determinism | mentions_generated_at |
| A3 | UPGRADES/PROMPT_A3_MCP_PROXY_SURFACE.md | REPO_MCP_PROXY_SURFACE.json | complete | determinism | mentions_generated_at |
| A4 | UPGRADES/PROMPT_A4_ROUTER_SURFACE.md | REPO_ROUTER_SURFACE.json | complete | determinism | mentions_generated_at |
| A5 | UPGRADES/PROMPT_A5_HOOKS_SURFACE.md | REPO_HOOKS_SURFACE.json | complete | determinism | mentions_generated_at |
| A6 | UPGRADES/PROMPT_A6_COMPOSE_SERVICE_GRAPH.md | REPO_COMPOSE_SERVICE_GRAPH.json | complete | determinism | mentions_generated_at |
| A7 | UPGRADES/PROMPT_A7_LITELLM_SURFACE.md | REPO_LITELLM_SURFACE.json | complete | determinism | mentions_generated_at |
| A8 | UPGRADES/PROMPT_A8_TASKX_SURFACE.md | REPO_TASKX_SURFACE.json | complete | determinism | mentions_generated_at |
| A9 | UPGRADES/PROMPT_A9_IMPLICIT_BEHAVIOR_HINTS.md | REPO_IMPLICIT_BEHAVIOR_HINTS.json | complete | determinism | mentions_generated_at |
| A99 | UPGRADES/PROMPT_A99_MERGE___QA.md | REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json, REPO_MCP_SERVER_DEFS.json, REPO_MCP_PROXY_SURFACE.json, REPO_ROUTER_SURFACE.json, REPO_HOOKS_SURFACE.json, REPO_IMPLICIT_BEHAVIOR_HINTS.json, REPO_COMPOSE_SERVICE_GRAPH.json, REPO_LITELLM_SURFACE.json, REPO_TASKX_SURFACE.json, REPOCTRL_NORM_MANIFEST.json, REPOCTRL_QA.json | complete | - | mentions_generated_at |
| B0 | UPGRADES/PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md | BOUNDARY_INVENTORY.json, BOUNDARY_PARTITIONS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| B1 | UPGRADES/PROMPT_B1_BOUNDARY_ASSERTIONS___CODE_ENFORCEMENT_POINTS.md | BOUNDARY_ENFORCEMENT_POINTS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| B2 | UPGRADES/PROMPT_B2_REFUSAL_RAILS___GUARDRAILS_SURFACE.md | REFUSAL_GUARDRAILS_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| B3 | UPGRADES/PROMPT_B3_BYPASS_PATHS___WEAK_GUARDS.md | BOUNDARY_BYPASS_RISKS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| B9 | UPGRADES/PROMPT_B9_MERGE___QA.md | BOUNDARY_MERGED.json, BOUNDARY_QA.json | stub | inputs, schema, evidence, anti_fabrication | - |
| C0 | UPGRADES/PROMPT_C0_CODE_INVENTORY___PARTITION_PLAN.md | CODE_INVENTORY.json, CODE_PARTITIONS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C1 | UPGRADES/PROMPT_C1_SERVICE_ENTRYPOINTS.md | SERVICE_ENTRYPOINTS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C2 | UPGRADES/PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md | EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C3 | UPGRADES/PROMPT_C3_DOPE_MEMORY_SURFACES.md | DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C4 | UPGRADES/PROMPT_C4_TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.md | TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C5 | UPGRADES/PROMPT_C5_TASKX_INTEGRATION_SURFACES.md | TASKX_INTEGRATION_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C6 | UPGRADES/PROMPT_C6_WORKFLOW_RUNNERS___MULTI_SERVICE_COORDINATION.md | WORKFLOW_RUNNER_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| C7 | UPGRADES/PROMPT_C7_API___DASHBOARDS.md | API_DASHBOARD_SURFACE.json | stub | inputs, schema, determinism, anti_fabrication | - |
| C8 | UPGRADES/PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md | DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json | partial | inputs, schema, evidence, anti_fabrication | - |
| C9 | UPGRADES/PROMPT_C9_MERGE___NORMALIZE___QA.md | SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json, DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json, TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json, TASKX_INTEGRATION_SURFACE.json, WORKFLOW_RUNNER_SURFACE.json, DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, CODE_SURFACES_QA.json | partial | inputs, schema, evidence, anti_fabrication | - |
| D0 | UPGRADES/PROMPT_D0_INVENTORY___PARTITION_PLAN.md | DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| D1 | UPGRADES/PROMPT_D1_CLAIMS___BOUNDARIES___SUPERSESSION.md | DOC_INDEX.partX.json, DOC_CONTRACT_CLAIMS.partX.json, DOC_BOUNDARIES.partX.json, DOC_SUPERSESSION.partX.json, CAP_NOTICES.partX.json | partial | inputs, schema, determinism, anti_fabrication | - |
| D2 | UPGRADES/PROMPT_D2_DEEP_EXTRACTION.md | DOC_INTERFACES.partX.json, DOC_WORKFLOWS.partX.json, DOC_DECISIONS.partX.json, DOC_GLOSSARY.partX.json | partial | inputs, schema, determinism, anti_fabrication | - |
| D3 | UPGRADES/PROMPT_D3_CITATION___REFERENCE_GRAPH.md | DOC_CITATION_GRAPH.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| D4 | UPGRADES/PROMPT_D4_MERGE___NORMALIZE___COVERAGE_QA.md | DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json, DOC_RECENCY_DUPLICATE_REPORT.json, DOC_COVERAGE_REPORT.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| D5 | UPGRADES/PROMPT_D5_DOC_TOPIC_CLUSTERS_JSON.md | DOC_TOPIC_CLUSTERS.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| E0 | UPGRADES/PROMPT_E0_EXECUTION_INVENTORY___PARTITION_PLAN.md | EXEC_INVENTORY.json, EXEC_PARTITIONS.json | partial | inputs, schema, evidence, anti_fabrication | - |
| E1 | UPGRADES/PROMPT_E1_BOOTSTRAP_COMMANDS_SURFACE.md | EXEC_BOOTSTRAP_COMMANDS.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| E2 | UPGRADES/PROMPT_E2_ENV_LOADING___CONFIG_CHAIN.md | EXEC_ENV_CHAIN.json | partial | inputs, schema, evidence, determinism | - |
| E3 | UPGRADES/PROMPT_E3_SERVICE_STARTUP_GRAPH.md | EXEC_STARTUP_GRAPH.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| E4 | UPGRADES/PROMPT_E4_RUNTIME_MODES___DELTA_REPORT.md | EXEC_RUNTIME_MODES.json, EXEC_MODE_DELTA_REPORT.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| E5 | UPGRADES/PROMPT_E5_ARTIFACT_OUTPUTS___LOGS___STATE.md | EXEC_ARTIFACT_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| E6 | UPGRADES/PROMPT_E6_EXECUTION_RISKS___ORDERING___STATE_DEPENDENCY.md | EXEC_RISK_FACTS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| E9 | UPGRADES/PROMPT_E9_MERGE___NORMALIZE___QA.md | EXEC_MERGED.json, EXEC_QA.json | partial | inputs, schema, evidence, anti_fabrication | - |
| G0 | UPGRADES/PROMPT_G0_GOVERNANCE_INVENTORY___PARTITION_PLAN.md | GOV_INVENTORY.json, GOV_PARTITIONS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G1 | UPGRADES/PROMPT_G1_CI_GATES___QUALITY_BARS.md | GOV_CI_GATES.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G2 | UPGRADES/PROMPT_G2_REPO_HYGIENE___ALLOWLISTS___POLICIES.md | GOV_HYGIENE_POLICIES.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G3 | UPGRADES/PROMPT_G3_POLICY_FILES___ENFORCEMENT.md | GOV_POLICIES.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G4 | UPGRADES/PROMPT_G4_SECURITY___SECRETS___REDUCTION_FACTS.md | GOV_SECRETS_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G9 | UPGRADES/PROMPT_G9_MERGE___QA.md | GOV_MERGED.json, GOV_QA.json | stub | inputs, schema, evidence, anti_fabrication | - |
| H0 | UPGRADES/PROMPT_H0_INVENTORY___PARTITION_PLAN.md | HOME_INVENTORY.json, HOME_PARTITIONS.json | complete | evidence | mentions_generated_at |
| H1 | UPGRADES/PROMPT_H1_KEYS___REFERENCES.md | HOME_KEYS_SURFACE.json, HOME_REFERENCES.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H2 | UPGRADES/PROMPT_H2_MCP_SURFACE.md | HOME_MCP_SURFACE.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H3 | UPGRADES/PROMPT_H3_ROUTER___PROVIDER_LADDERS.md | HOME_ROUTER_SURFACE.json, HOME_PROVIDER_LADDER_HINTS.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H4 | UPGRADES/PROMPT_H4_LITELLM_SURFACES.md | HOME_LITELLM_SURFACE.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H5 | UPGRADES/PROMPT_H5_PROFILES___SESSIONS.md | HOME_PROFILES_SURFACE.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H6 | UPGRADES/PROMPT_H6_TMUX___WORKFLOW_HELPERS.md | HOME_TMUX_WORKFLOW_SURFACE.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H7 | UPGRADES/PROMPT_H7_SQLITE___STATE_DB_METADATA.md | HOME_SQLITE_SCHEMA.json | partial | inputs, determinism, anti_fabrication | mentions_generated_at |
| H9 | UPGRADES/PROMPT_H9_MERGE___QA.md | HOMECTRL_NORM_MANIFEST.json, HOMECTRL_QA.json | partial | inputs, anti_fabrication | mentions_generated_at |
| M0 | UPGRADES/PROMPT_M0_RUNTIME_EXPORT_INVENTORY.md | M0_RUNTIME_EXPORT_INVENTORY.json | partial | inputs, schema, evidence, determinism, anti_fabrication | inactive_v3 |
| M1 | UPGRADES/PROMPT_M1_SQLITE_SCHEMA_SNAPSHOTS.md | M1_SQLITE_SCHEMA_SNAPSHOTS.json | partial | inputs, schema, evidence, determinism, anti_fabrication | inactive_v3 |
| M2 | UPGRADES/PROMPT_M2_SQLITE_TABLE_COUNTS.md | M2_SQLITE_TABLE_COUNTS.json | partial | inputs, schema, evidence, anti_fabrication | inactive_v3 |
| M3 | UPGRADES/PROMPT_M3_CONPORT_EXPORT_SAFE.md | M3_CONPORT_EXPORT_SAFE.json | partial | inputs, schema, evidence, anti_fabrication | inactive_v3 |
| M4 | UPGRADES/PROMPT_M4_DOPE_CONTEXT_EXPORT_SAFE.md | M4_DOPE_CONTEXT_EXPORT_SAFE.json | partial | inputs, schema, evidence, anti_fabrication | inactive_v3 |
| M5 | UPGRADES/PROMPT_M5_MCP_HEALTH_EXPORT_SAFE.md | M5_MCP_HEALTH_EXPORT_SAFE.json | partial | inputs, schema, evidence, determinism, anti_fabrication | inactive_v3 |
| M6 | UPGRADES/PROMPT_M6_RUNTIME_EXPORT_INDEX.md | M6_RUNTIME_EXPORT_INDEX.json | partial | inputs, schema, evidence, determinism, anti_fabrication | inactive_v3 |
| Q0 | UPGRADES/PROMPT_Q0_PIPELINE_COMPLETENESS___MANIFEST.md | QA_RUN_MANIFEST.json | stub | schema, evidence, determinism, anti_fabrication | - |
| Q1 | UPGRADES/PROMPT_Q1_MISSING_ARTIFACTS___RECOVERY_PLAN.md | QA_MISSING_ARTIFACTS.json | stub | inputs, schema, evidence, determinism | - |
| Q2 | UPGRADES/PROMPT_Q2_DUPLICATE_IDS___PROMPT_COLLISIONS.md | QA_PROMPT_COLLISIONS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| Q3 | UPGRADES/PROMPT_Q3_DRIFT_DETECTION___NORM_DIFFS.md | QA_NORM_DRIFT_REPORT.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| Q9 | UPGRADES/PROMPT_Q9_MERGE___QA.md | PIPELINE_DOCTOR_REPORT.json | stub | inputs, schema, evidence, anti_fabrication | - |
| R0 | UPGRADES/PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md | CONTROL_PLANE_TRUTH_MAP.md | partial | inputs, determinism | - |
| R1 | UPGRADES/PROMPT_R1_DOPE_MEMORY_IMPLEMENTATION_TRUTH.md | DOPE_MEMORY_IMPLEMENTATION_TRUTH.md | partial | inputs, determinism, anti_fabrication | - |
| R2 | UPGRADES/PROMPT_R2_EVENTBUS_WIRING_TRUTH.md | EVENTBUS_WIRING_TRUTH.md | partial | inputs, determinism | - |
| R3 | UPGRADES/PROMPT_R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md | TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md | partial | inputs, determinism | - |
| R4 | UPGRADES/PROMPT_R4_TASKX_INTEGRATION_TRUTH.md | TASKX_INTEGRATION_TRUTH.md | partial | inputs, determinism, anti_fabrication | - |
| R5 | UPGRADES/PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md | WORKFLOWS_TRUTH_GRAPH.md | partial | inputs, determinism | - |
| R6 | UPGRADES/PROMPT_R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md | PORTABILITY_AND_MIGRATION_RISK_LEDGER.md | partial | inputs, determinism, anti_fabrication | - |
| R7 | UPGRADES/PROMPT_R7_CONFLICT_LEDGER.md | CONFLICT_LEDGER.md | partial | inputs, determinism, anti_fabrication | - |
| R8 | UPGRADES/PROMPT_R8_RISK_REGISTER_TOP20.md | RISK_REGISTER_TOP20.md | partial | inputs, anti_fabrication | - |
| S0 | UPGRADES/PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md | (none) | partial | inputs, determinism | inactive_v3 |
| S1 | UPGRADES/PROMPT_S1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md | (none) | partial | inputs, determinism | inactive_v3 |
| T0 | UPGRADES/PROMPT_T0_TASK_PACKET_FACTORY.md | TP_BACKLOG_TOPN.json, TP_INDEX.json | partial | schema, anti_fabrication | mentions_generated_at |
| T1 | UPGRADES/PROMPT_T1_EMIT_TASK_PACKETS___TOP10.md | TP_PACKETS_TOP10.partX.md, TP_PACKET_IMPLEMENTATION_INDEX.json | partial | schema, anti_fabrication | mentions_generated_at |
| T2 | UPGRADES/PROMPT_T2_PACKET_SCHEMA___AUTHORITY_RULES.md | TP_SCHEMA.json, TP_AUTHORITY_RULES.json | partial | inputs, schema, determinism, anti_fabrication | - |
| T3 | UPGRADES/PROMPT_T3_PACKET_GENERATION___BATCHED.md | TP_BATCHED_PACKETS.partX.md, TP_BATCH_INDEX.json | partial | inputs, schema, anti_fabrication | - |
| T4 | UPGRADES/PROMPT_T4_PACKET_DEDUP___COLLISION_RESOLUTION.md | TP_DEDUPED.json, TP_COLLISIONS.json | partial | inputs, schema, anti_fabrication | - |
| T5 | UPGRADES/PROMPT_T5_PACKET_ORDERING___RUN_PLAN.md | TP_RUN_PLAN.json, TP_BACKLOG_TOPN.json | partial | inputs, schema, evidence, anti_fabrication | - |
| T9 | UPGRADES/PROMPT_T9_MERGE___QA.md | TP_INDEX.json, TP_MERGED.json, TP_QA.json, TP_SUMMARY.md, TP_BACKLOG_TOPN.json | partial | inputs, schema, determinism, anti_fabrication | - |
| W0 | UPGRADES/PROMPT_W0_WORKFLOW_INVENTORY___PARTITION_PLAN.md | WORKFLOW_INVENTORY.json, WORKFLOW_PARTITIONS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W1 | UPGRADES/PROMPT_W1_WORKFLOW_CATALOG___RUNBOOK_FACTS.md | WORKFLOW_CATALOG.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W2 | UPGRADES/PROMPT_W2_WORKFLOW_INPUTS_OUTPUTS___ARTIFACTS.md | WORKFLOW_IO_MAP.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W3 | UPGRADES/PROMPT_W3_MULTI_SERVICE_COORDINATION___COMPOSE_TMUX.md | WORKFLOW_COORDINATION_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W4 | UPGRADES/PROMPT_W4_WORKFLOW_FAILURE_MODES___RECOVERY.md | WORKFLOW_FAILURE_RECOVERY.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W5 | UPGRADES/PROMPT_W5_WORKFLOW_STATE_DEPENDENCIES___HOME_VS_REPO.md | WORKFLOW_STATE_COUPLING.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W9 | UPGRADES/PROMPT_W9_MERGE___QA.md | WORKFLOW_MERGED.json, WORKFLOW_QA.json | stub | inputs, schema, evidence, anti_fabrication | - |
| X0 | UPGRADES/PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN.md | FEATURE_INDEX_INVENTORY.json, FEATURE_INDEX_PARTITIONS.json | partial | inputs, schema, anti_fabrication | - |
| X1 | UPGRADES/PROMPT_X1_FEATURE_SURFACE_EXTRACT.md | FEATURE_SURFACE.json | partial | inputs, schema, determinism, anti_fabrication | - |
| X2 | UPGRADES/PROMPT_X2_FEATURE_TO_CODE_MAP.md | FEATURE_CODE_MAP.json | partial | inputs, schema, evidence, anti_fabrication | - |
| X3 | UPGRADES/PROMPT_X3_FEATURE_TO_DOC_MAP.md | FEATURE_DOC_MAP.json | partial | inputs, schema, anti_fabrication | - |
| X4 | UPGRADES/PROMPT_X4_FEATURE_DEPENDENCY_GRAPH.md | FEATURE_DEP_GRAPH.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| X9 | UPGRADES/PROMPT_X9_MERGE___QA.md | FEATURE_INDEX_MERGED.json, FEATURE_INDEX_QA.json | partial | schema, evidence, anti_fabrication | - |
| Z0 | UPGRADES/PROMPT_Z0_FREEZE_INVENTORY___CHECKSUMS.md | FREEZE_FILE_INDEX.json, FREEZE_CHECKSUMS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| Z1 | UPGRADES/PROMPT_Z1_PROOF_PACK___RUNBOOK.md | PROOF_PACK.md | stub | inputs, evidence, determinism, anti_fabrication | - |
| Z2 | UPGRADES/PROMPT_Z2_OPUS_INPUT_BUNDLE___MANIFEST.md | OPUS_INPUT_MANIFEST.json | stub | inputs, schema, evidence, anti_fabrication | - |
| Z9 | UPGRADES/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md | FREEZE_MANIFEST.json, FREEZE_README.md, FREEZE_QA.json | partial | inputs, schema, evidence, anti_fabrication | - |

## Legacy promptset snapshot (Heuristic, UPGRADES/_legacy_prompts)

- Legacy prompts: complete=0, partial=28, stub=10
- Legacy phase B: complete=0, partial=6, stub=2
- Legacy phase E: complete=0, partial=3, stub=0
- Legacy phase G: complete=0, partial=5, stub=3
- Legacy phase H: complete=0, partial=2, stub=0
- Legacy phase Q: complete=0, partial=4, stub=2
- Legacy phase W: complete=0, partial=6, stub=2
- Legacy phase X: complete=0, partial=0, stub=1
- Legacy phase Z: complete=0, partial=2, stub=0

## Per-prompt audit table (UPGRADES/_legacy_prompts)

| Step | Prompt | Outputs | Rating | Missing | Flags |
| --- | --- | --- | --- | --- | --- |
| B0 | UPGRADES/_legacy_prompts/PROMPT_B0_BOUNDARY_INVENTORY___SOURCES_AND_PARTITIONS.md | BOUNDARY_SOURCE_INDEX.json, BOUNDARY_PARTITIONS.json | partial | schema, anti_fabrication | - |
| B1 | UPGRADES/_legacy_prompts/PROMPT_B1_BOUNDARY_RULES___IMPLEMENTED.md | TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json | partial | inputs, schema, determinism, anti_fabrication | - |
| B1 | UPGRADES/_legacy_prompts/PROMPT_B1_BOUNDARY_SURFACE___EXTRACT.partX.md | BOUNDARY_SURFACE.partX.json | partial | inputs, schema, anti_fabrication | - |
| B2 | UPGRADES/_legacy_prompts/PROMPT_B2_BOUNDARY_RULES___PLANNED.md | BOUNDARY_BYPASS_RISKS.json | partial | inputs, schema, determinism, anti_fabrication | - |
| B2 | UPGRADES/_legacy_prompts/PROMPT_B2_BYPASS_CANDIDATES___MECHANICAL_PAIRING.md | BOUNDARY_BYPASS_CANDIDATES.json | partial | inputs, schema, anti_fabrication | - |
| B3 | UPGRADES/_legacy_prompts/PROMPT_B3_BOUNDARY_MERGE___QA.md | BOUNDARY_SURFACE.json, BOUNDARY_QA.json | partial | inputs, schema, anti_fabrication | - |
| B3 | UPGRADES/_legacy_prompts/PROMPT_B3_REFUSAL_RAILS___PROPAGATION.md | BOUNDARY_REFUSAL_PATHS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| B4 | UPGRADES/_legacy_prompts/PROMPT_B4_BOUNDARY_PLANE_MERGE___QA.md | BOUNDARY_MERGED.json, BOUNDARY_QA.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| E1 | UPGRADES/_legacy_prompts/PROMPT_E1_EXEC_COMMAND_INDEX___WHAT_STARTS_WHAT.md | EXEC_COMMAND_INDEX.partX.json, EXEC_SIDE_EFFECTS.partX.json | partial | inputs, schema, anti_fabrication | - |
| E2 | UPGRADES/_legacy_prompts/PROMPT_E2_EXEC_START_GRAPH___MERGE_NORMALIZE.md | EXEC_COMMAND_INDEX.json, EXEC_SERVICE_START_GRAPH.json, EXEC_QA.json | partial | inputs, schema, anti_fabrication | - |
| E3 | UPGRADES/_legacy_prompts/PROMPT_E3_EXEC_QA___COVERAGE.md | EXEC_COVERAGE_QA.json | partial | inputs, schema, anti_fabrication | - |
| G0 | UPGRADES/_legacy_prompts/PROMPT_G0_GOVERNANCE_INVENTORY___POLICY_SOURCES.md | GOVERNANCE_SOURCE_INDEX.json, GOVERNANCE_PARTITIONS.json | partial | inputs, schema, anti_fabrication | - |
| G1 | UPGRADES/_legacy_prompts/PROMPT_G1_CI_WORKFLOWS___GATES.md | CI_GATES_TRUTH.json | partial | inputs, schema, evidence, determinism | - |
| G1 | UPGRADES/_legacy_prompts/PROMPT_G1_GOVERNANCE_EXTRACT___RULES_AND_GATES.partX.md | GOVERNANCE_RULES.partX.json | partial | inputs, schema, anti_fabrication | - |
| G2 | UPGRADES/_legacy_prompts/PROMPT_G2_GOVERNANCE_MERGE___QA.md | GOVERNANCE_RULES.json, GOVERNANCE_QA.json | partial | inputs, schema, anti_fabrication | - |
| G2 | UPGRADES/_legacy_prompts/PROMPT_G2_SCHEMA_CONTRACTS___LOCKS.md | INSTRUCTION_AUTHORITY_POLICY.json, SUPERSESSION_POLICY_SURFACE.json | partial | inputs, schema, evidence, determinism | - |
| G3 | UPGRADES/_legacy_prompts/PROMPT_G3_VERSIONING___PINNING___LOCKS.md | GOV_PINNING_SURFACE.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G4 | UPGRADES/_legacy_prompts/PROMPT_G4_RELEASE___VERSIONING___MIGRATIONS.md | GOV_RELEASE_MIGRATION.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| G5 | UPGRADES/_legacy_prompts/PROMPT_G5_GOVERNANCE_PLANE_MERGE___QA.md | GOV_MERGED.json, GOV_QA.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| H8 | UPGRADES/_legacy_prompts/PROMPT_H8_NORMALIZE___MERGE___CANONICALIZE.md | (none) | partial | inputs | mentions_generated_at |
| H9 | UPGRADES/_legacy_prompts/PROMPT_H9_COVERAGE_QA___DRIFT___SAFETY_CHECKS.md | (none) | partial | inputs | mentions_generated_at |
| Q0 | UPGRADES/_legacy_prompts/PROMPT_Q0_PIPELINE_DOCTOR___COVERAGE_AND_SCHEMA.md | PIPELINE_DOCTOR_REPORT.json | partial | schema, anti_fabrication | - |
| Q0 | UPGRADES/_legacy_prompts/PROMPT_Q0_PIPELINE_PROOF_INVENTORY.md | PIPELINE_PROOF_INDEX.json, PIPELINE_PROOF_CHECKLIST.json | partial | schema, determinism, anti_fabrication | - |
| Q1 | UPGRADES/_legacy_prompts/PROMPT_Q1_DOC_RECENCY___DUPLICATE_GROUPS.md | DOC_RECENCY_DUPLICATE_REPORT.json | partial | schema, anti_fabrication | - |
| Q1 | UPGRADES/_legacy_prompts/PROMPT_Q1_FAILURE_CLASSIFICATION.md | DRIFT_SIGNALS.json, COVERAGE_GAPS.json | partial | inputs, schema, evidence, determinism, anti_fabrication | - |
| Q2 | UPGRADES/_legacy_prompts/PROMPT_Q2_COVERAGE_GAPS___WHAT_WASNT_SCANNED.md | PIPELINE_COVERAGE_GAPS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| Q4 | UPGRADES/_legacy_prompts/PROMPT_Q4_QA_MERGE___SUMMARY.md | QA_SUMMARY.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W0 | UPGRADES/_legacy_prompts/PROMPT_W0_WORKFLOW_INVENTORY___SOURCES_AND_PARTITIONS.md | WORKFLOW_SOURCE_INDEX.json, WORKFLOW_PARTITIONS.json, WORKFLOW_TODO_QUEUE.json | partial | inputs, schema, anti_fabrication | - |
| W1 | UPGRADES/_legacy_prompts/PROMPT_W1_WORKFLOW_CATALOG___HUMAN_RUNBOOKS.md | WORKFLOW_CATALOG.json | partial | schema, determinism | - |
| W1 | UPGRADES/_legacy_prompts/PROMPT_W1_WORKFLOW_EXTRACT___STRUCTURED.partX.md | WORKFLOWS_EXTRACTED.partX.json, WORKFLOW_INTERFACE_TOUCHES.partX.json | partial | inputs, schema, anti_fabrication | - |
| W2 | UPGRADES/_legacy_prompts/PROMPT_W2_WORKFLOWS_MERGE___NORMALIZE_QA.md | WORKFLOWS_EXTRACTED.json, WORKFLOW_TOUCHES.json, WORKFLOW_QA.json | partial | inputs, schema, anti_fabrication | - |
| W2 | UPGRADES/_legacy_prompts/PROMPT_W2_WORKFLOW_RUNNERS___CODE_PATHS.md | WORKFLOW_SERVICE_GRAPH.json | partial | inputs, schema, determinism, anti_fabrication | - |
| W3 | UPGRADES/_legacy_prompts/PROMPT_W3_CROSS_SERVICE_COORDINATION.md | WORKFLOW_STATE_SURFACE.json, WORKFLOW_COUPLING_POINTS.json | partial | inputs, schema, determinism | - |
| W4 | UPGRADES/_legacy_prompts/PROMPT_W4_WORKFLOW_IO_CONTRACTS.md | WORKFLOW_CONTRACTS.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| W6 | UPGRADES/_legacy_prompts/PROMPT_W6_WORKFLOW_PLANE_MERGE___QA.md | WORKFLOW_MERGED.json, WORKFLOW_QA.json | stub | inputs, schema, evidence, determinism, anti_fabrication | - |
| X0 | UPGRADES/_legacy_prompts/PROMPT_X0_FEATURE_INDEX.md | FEATURE_INDEX.json, X_SERVICE_CATALOG.json, X_FEATURE_WORKFLOWS.json, X_CONTRACT_CATALOG.json, X_INSTRUCTION_SURFACE_CATALOG.json, X_DB_CATALOG.json, X_EVENT_CATALOG.json | stub | inputs, schema, determinism, anti_fabrication | - |
| Z0 | UPGRADES/_legacy_prompts/PROMPT_Z0_HANDOFF_BUNDLE___FREEZE_RUN.md | HANDOFF_BUNDLE.md, HANDOFF_BUNDLE.json | partial | schema, anti_fabrication | - |
| Z0 | UPGRADES/_legacy_prompts/PROMPT_Z0_HANDOFF_FREEZE___RUN_DIGEST.md | HANDOFF_DIGEST.md, ARCHIVE_MANIFEST.json, OPUS_CONTEXT_BUNDLE_INDEX.json | partial | inputs, schema, evidence | - |
