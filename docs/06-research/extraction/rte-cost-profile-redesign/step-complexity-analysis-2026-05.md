---
id: step-complexity-analysis-2026-05
title: RTE v4 Promptset Step Complexity Analysis
type: reference
owner: rte-routing
date: 2026-05-23
adhd_complexity: 0.7
adhd_energy: high
status: draft
author: '@hu3mann'
last_review: '2026-05-24'
next_review: '2026-08-22'
prelude: RTE v4 Promptset Step Complexity Analysis (reference) for dopemux documentation
  and developer workflows.
---
# RTE v4 Promptset Step Complexity Analysis

**Date**: 2026-05-23
**Scope**: All 136 steps in `services/repo-truth-extractor/promptsets/v4/`
**Purpose**: Pre-design analysis for `model_map.yaml` restructuring. Drives the choice between (a) lane-class defaults + per-step overrides, (b) `(lane_class, capability_tier)` matrix, or (c) per-step blocks for outliers + matrix for the rest.
**Status**: Phase B input for the routing redesign. Does **not** specify new routes or rename lanes — that's Phase C.

---

## 1. Methodology

**Data sources**:
- `services/repo-truth-extractor/promptsets/v4/model_map.yaml` (existing `lane_class` + `strict_schema_required_primary` per step)
- `services/repo-truth-extractor/promptsets/v4/promptset.yaml` (phase membership, prompt filename, declared outputs per step)
- `services/repo-truth-extractor/promptsets/v4/artifacts.yaml` (209 artifacts: `canonical_writer_step_id`, `kind`, `merge_strategy`)
- `services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_*.md` (136 files; only `## Goal`, `## Inputs`, and `## Extraction Procedure` / `## Synthesis Procedure` sections read for classification)

**Classification rules** (deterministic, applied via Python):

- **`output_kind`**: dominant `artifact.kind` across the step's outputs (or `mixed(...)` if heterogeneous). Source: `artifacts.yaml`.
- **`reasoning_depth`** ∈ {low, medium, high}: derived from (a) phase (R/S → high default; M/Z → low default; T → medium-high), (b) filename keywords (truth_map / reconcil / synthesis / dossier / opus_ → high; partition_plan → medium; checksums / export_safe → low), (c) procedure-section keyword counts (`HIGH_DEPTH_STRONG` includes "arbitrate", "reconcile", "judge", "conflict ledger"; `MEDIUM_DEPTH_STRONG` includes "call sites", "import graph", "unreferenced", "cross-module"). `*_partition_plan` and any prompt with multi-module symbol reasoning floors at `medium`.
- **`code_specialist_needed`**: true for phase C (default), or when prompt mentions AST / call graph / FastAPI / Pydantic / Depends() / unreferenced / source-file globs (`services/`, `src/`, `.py`, `.ts`, etc.). The C99/merge-QA steps are explicitly false.
- **`strict_json_required`**: exact copy of `strict_schema_required_primary` from `model_map.yaml`.
- **`synthesis_vs_extraction`** ∈ {extraction, hybrid, synthesis}: phase-driven (R/S → synthesis; T-factory/authority → synthesis; T-dedup/ordering → hybrid; Q → hybrid; M/Z-freeze → extraction; A/B/C/D/E/G/H/W/X → extraction default), refined by keyword counts of `SYNTHESIS_KW` vs `EXTRACTION_KW`.
- **`partition_input_size_class`** ∈ {small, medium, large}: R/S/T/Z/Q → large (cross-phase); `*_partition_plan` and `*_merge_*` → medium; `*_snapshots`, `*_table_counts`, `*_export_*`, `*_health`, `*_checksums` → small; rest → medium.
- **`premium_floor`**: true iff at least one of the step's declared outputs is consumed by a prompt in phase R/S/T/Z, where "consumed" means (i) verbatim mention of the artifact filename in the consumer's prompt body, OR (ii) a generic phase reference like *"all R-phase truth reports"* targeting the producing step's phase. Generic-reference detection uses targeted patterns ({phase}-phase artifacts / {phase}-phase outputs / {phase}-phase truth / all {phase}-phase). The unbounded *"all upstream"* pattern is intentionally **not** matched, because every R/S/T/Z prompt contains it and matching would flag every step in the entire pipeline as premium.

**Coverage**: 136/136 prompts parsed successfully; no `PROMPT_MISSING` flags.

**Caveats**:
1. Goal sections in v4 prompts are largely templated ("Produce X for phase Y with strict schema..."); the load-bearing signal is in `## Extraction Procedure`. Filename keywords were the most stable single signal.
2. The `premium_floor` regex catches verbatim artifact names and named phase patterns. It still understates true cross-phase coupling when a downstream synthesis prompt says *"all upstream extraction artifacts"* with no narrower phrase. That generic phrase appears in 15 prompts (R11, S0–S3, S8, S10, T0–T5, Z0, Z2); had it been counted, every A/B/C/D/E/G/H/M/Q/W/X step would flip to `premium_floor=True`. The targeted-phase patterns give a defensible middle ground but still likely understate the truth by a handful of additional steps.

---

## 2. Full 136-Row Table

| step_id | phase | lane_class | prompt_filename | output_kind | reasoning_depth | code_specialist_needed | strict_json_required | synthesis_vs_extraction | partition_input_size_class | premium_floor | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | A | CE | PROMPT_A0_REPO_CONTROL_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | False | — |
| A1 | A | CE | PROMPT_A1_INSTRUCTION_SURFACES.md | json_item_list | medium | True | True | extraction | medium | False | — |
| A2 | A | BULK_DOCS_GENERAL | PROMPT_A2_MCP_SERVER_DEFS.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A3 | A | BULK_DOCS_GENERAL | PROMPT_A3_MCP_PROXY_SURFACE.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A4 | A | BULK_DOCS_GENERAL | PROMPT_A4_ROUTER_SURFACE.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A5 | A | BULK_DOCS_GENERAL | PROMPT_A5_HOOKS_SURFACE.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A6 | A | BULK_DOCS_GENERAL | PROMPT_A6_COMPOSE_SERVICE_GRAPH.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A7 | A | BULK_DOCS_GENERAL | PROMPT_A7_LITELLM_SURFACE.md | json_item_list | medium | True | False | extraction | medium | False | — |
| A8 | A | BULK_DOCS_GENERAL | PROMPT_A8_TASKX_SURFACE.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A9 | A | BULK_DOCS_GENERAL | PROMPT_A9_IMPLICIT_BEHAVIOR_HINTS.md | json_item_list | medium | True | False | extraction | medium | False | — |
| A10 | A | BULK_DOCS_GENERAL | PROMPT_A10_LEANTIME_SURFACE.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| A11 | A | CE | PROMPT_A11_EDITOR_INTEGRATION_SURFACES.md | json_item_list | medium | True | True | extraction | medium | True | — |
| A12 | A | CE | PROMPT_A12_CLI_COMMAND_SURFACE.md | json_item_list | medium | True | True | extraction | medium | True | — |
| A13 | A | CE | PROMPT_A13_HOOK_CONTRACT_SURFACE.md | json_item_list | medium | True | True | extraction | medium | True | — |
| A99 | A | AGG | PROMPT_A99_MERGE___QA.md | json_item_list | medium | True | True | hybrid | medium | True | — |
| B0 | B | CE | PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | False | — |
| B1 | B | BULK_DOCS_GENERAL | PROMPT_B1_BOUNDARY_ASSERTIONS___CODE_ENFORCEMENT_POINTS.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| B2 | B | BULK_DOCS_GENERAL | PROMPT_B2_REFUSAL_RAILS___GUARDRAILS_SURFACE.md | json_item_list | medium | True | False | extraction | medium | False | — |
| B3 | B | BULK_DOCS_GENERAL | PROMPT_B3_BYPASS_PATHS___WEAK_GUARDS.md | json_item_list | medium | True | False | extraction | medium | False | — |
| B9 | B | AGG | PROMPT_B9_MERGE___QA.md | json_item_list | medium | True | True | hybrid | medium | True | — |
| C0 | C | CE | PROMPT_C0_CODE_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C1 | C | BULK_CODE_HEAVY | PROMPT_C1_SERVICE_ENTRYPOINTS.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| C2 | C | CE | PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C3 | C | CE | PROMPT_C3_DOPE_MEMORY_SURFACES.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C4 | C | CE | PROMPT_C4_TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C5 | C | BULK_CODE_HEAVY | PROMPT_C5_TASKX_INTEGRATION_SURFACES.md | json_item_list | medium | True | False | extraction | medium | False | — |
| C6 | C | BULK_CODE_HEAVY | PROMPT_C6_WORKFLOW_RUNNERS___MULTI_SERVICE_COORDINATION.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| C7 | C | BULK_CODE_HEAVY | PROMPT_C7_API___DASHBOARDS.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| C8 | C | CE | PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C9 | C | AGG | PROMPT_C9_MERGE___NORMALIZE___QA.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C10 | C | BULK_CODE_HEAVY | PROMPT_C10_SERVICE_CATALOG_DEEP.md | json_item_list | high | True | False | hybrid | medium | False | lane vs depth mismatch (high reasoning on bulk lane) |
| C11 | C | BULK_CODE_HEAVY | PROMPT_C11_LEANTIME_INTEGRATION_SURFACES.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| C12 | C | CE | PROMPT_C12_AGENT_ORCHESTRATION_SURFACE.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C13 | C | CE | PROMPT_C13_ADHD_ENGINE_SURFACE.md | json_item_list | medium | True | True | extraction | medium | False | — |
| C14 | C | CE | PROMPT_C14_CODE_HEALTH_SURFACE.md | json_item_list | medium | True | True | extraction | small | True | — |
| C15 | C | CE | PROMPT_C15_DEAD_CODE_INVENTORY.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C16 | C | CE | PROMPT_C16_DEPENDENCY_GRAPHS.md | json_item_list | medium | True | True | extraction | medium | True | — |
| C17 | C | CE | PROMPT_C17_COGNITIVE_FEATURES_SURFACE.md | json_item_list | medium | True | True | extraction | medium | False | — |
| C18 | C | CE | PROMPT_C18_OBSERVABILITY_SURFACE.md | json_item_list | medium | True | True | extraction | medium | False | — |
| C19 | C | CE | PROMPT_C19_ERROR_HANDLING_PATTERNS.md | json_item_list | medium | True | True | extraction | medium | False | — |
| C20 | C | CE | PROMPT_C20_STATE_MANAGEMENT_SURFACE.md | json_item_list | medium | True | True | extraction | medium | False | — |
| C21 | C | CE | PROMPT_C21_PERFORMANCE_SURFACE.md | json_item_list | medium | True | True | extraction | medium | False | — |
| D0 | D | CE | PROMPT_D0_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | False | True | extraction | medium | True | — |
| D1 | D | CE | PROMPT_D1_CLAIMS___BOUNDARIES___SUPERSESSION.md | json_item_list | medium | False | True | extraction | medium | True | — |
| D2 | D | BULK_DOCS_GENERAL | PROMPT_D2_DEEP_EXTRACTION.md | json_item_list | medium | False | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| D3 | D | BULK_DOCS_GENERAL | PROMPT_D3_CITATION___REFERENCE_GRAPH.md | json_item_list | medium | False | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| D4 | D | AGG | PROMPT_D4_MERGE___NORMALIZE___COVERAGE_QA.md | json_item_list | medium | False | True | extraction | medium | True | — |
| D5 | D | AGG | PROMPT_D5_DOC_TOPIC_CLUSTERS_JSON.md | json_item_list | medium | False | True | extraction | medium | True | — |
| E0 | E | CE | PROMPT_E0_EXECUTION_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | False | — |
| E1 | E | BULK_DOCS_GENERAL | PROMPT_E1_BOOTSTRAP_COMMANDS_SURFACE.md | json_item_list | medium | True | False | extraction | medium | False | — |
| E2 | E | BULK_DOCS_GENERAL | PROMPT_E2_ENV_LOADING___CONFIG_CHAIN.md | json_item_list | medium | True | False | extraction | medium | False | — |
| E3 | E | BULK_DOCS_GENERAL | PROMPT_E3_SERVICE_STARTUP_GRAPH.md | json_item_list | medium | True | False | extraction | medium | False | — |
| E4 | E | BULK_DOCS_GENERAL | PROMPT_E4_RUNTIME_MODES___DELTA_REPORT.md | json_item_list | medium | True | False | extraction | medium | False | — |
| E5 | E | BULK_DOCS_GENERAL | PROMPT_E5_ARTIFACT_OUTPUTS___LOGS___STATE.md | json_item_list | medium | True | False | extraction | medium | False | — |
| E6 | E | BULK_DOCS_GENERAL | PROMPT_E6_EXECUTION_RISKS___ORDERING___STATE_DEPENDENCY.md | json_item_list | medium | True | False | extraction | medium | False | — |
| E9 | E | AGG | PROMPT_E9_MERGE___NORMALIZE___QA.md | json_item_list | medium | True | True | extraction | medium | False | — |
| G0 | G | CE | PROMPT_G0_GOVERNANCE_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | False | — |
| G1 | G | CE | PROMPT_G1_CI_GATES___QUALITY_BARS.md | json_item_list | medium | True | True | extraction | medium | False | — |
| G2 | G | BULK_DOCS_GENERAL | PROMPT_G2_REPO_HYGIENE___ALLOWLISTS___POLICIES.md | json_item_list | medium | True | False | extraction | medium | False | — |
| G3 | G | BULK_DOCS_GENERAL | PROMPT_G3_POLICY_FILES___ENFORCEMENT.md | json_item_list | medium | True | False | extraction | medium | False | — |
| G4 | G | BULK_DOCS_GENERAL | PROMPT_G4_SECURITY___SECRETS___REDUCTION_FACTS.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| G5 | G | CE | PROMPT_G5_AUTH_FLOW_SURFACE.md | json_item_list | medium | True | True | extraction | medium | True | — |
| G6 | G | CE | PROMPT_G6_DEPENDENCY_HEALTH_SURFACE.md | json_item_list | medium | True | True | extraction | small | False | — |
| G7 | G | CE | PROMPT_G7_TECHNICAL_DEBT_REGISTER.md | json_item_list | medium | True | True | extraction | medium | False | — |
| G9 | G | AGG | PROMPT_G9_MERGE___QA.md | json_item_list | medium | True | True | hybrid | medium | False | — |
| H0 | H | CE | PROMPT_H0_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | False | True | extraction | medium | False | — |
| H1 | H | CE | PROMPT_H1_KEYS___REFERENCES.md | json_item_list | medium | False | True | extraction | medium | False | — |
| H2 | H | BULK_DOCS_GENERAL | PROMPT_H2_MCP_SURFACE.md | json_item_list | medium | False | False | extraction | medium | False | — |
| H3 | H | CE | PROMPT_H3_ROUTER___PROVIDER_LADDERS.md | json_item_list | medium | False | True | extraction | medium | False | — |
| H4 | H | BULK_DOCS_GENERAL | PROMPT_H4_LITELLM_SURFACES.md | json_item_list | medium | True | False | extraction | medium | False | — |
| H5 | H | BULK_DOCS_GENERAL | PROMPT_H5_PROFILES___SESSIONS.md | json_item_list | medium | False | False | extraction | medium | False | — |
| H6 | H | BULK_DOCS_GENERAL | PROMPT_H6_TMUX___WORKFLOW_HELPERS.md | json_item_list | medium | True | False | extraction | medium | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| H7 | H | BULK_DOCS_GENERAL | PROMPT_H7_SQLITE___STATE_DB_METADATA.md | json_item_list | medium | False | False | extraction | medium | False | — |
| H9 | H | AGG | PROMPT_H9_MERGE___QA.md | json_item_list | medium | False | True | hybrid | medium | True | — |
| M0 | M | BULK_DOCS_GENERAL | PROMPT_M0_RUNTIME_EXPORT_INVENTORY.md | json_item_list | low | False | False | extraction | small | False | — |
| M1 | M | BULK_DOCS_GENERAL | PROMPT_M1_SQLITE_SCHEMA_SNAPSHOTS.md | json_item_list | low | False | False | extraction | small | False | — |
| M2 | M | BULK_DOCS_GENERAL | PROMPT_M2_SQLITE_TABLE_COUNTS.md | json_item_list | low | False | False | extraction | small | False | — |
| M3 | M | BULK_DOCS_GENERAL | PROMPT_M3_CONPORT_EXPORT_SAFE.md | json_item_list | low | False | False | extraction | small | False | — |
| M4 | M | BULK_DOCS_GENERAL | PROMPT_M4_DOPE_CONTEXT_EXPORT_SAFE.md | json_item_list | low | False | False | extraction | small | False | — |
| M5 | M | BULK_DOCS_GENERAL | PROMPT_M5_MCP_HEALTH_EXPORT_SAFE.md | json_item_list | low | False | False | extraction | small | False | — |
| M6 | M | BULK_DOCS_GENERAL | PROMPT_M6_RUNTIME_EXPORT_INDEX.md | json_item_list | low | False | False | extraction | small | False | — |
| Q0 | Q | CE | PROMPT_Q0_PIPELINE_COMPLETENESS___MANIFEST.md | json_item_list | medium | False | True | hybrid | large | False | — |
| Q1 | Q | BULK_DOCS_GENERAL | PROMPT_Q1_MISSING_ARTIFACTS___RECOVERY_PLAN.md | json_item_list | medium | False | False | hybrid | large | False | — |
| Q2 | Q | BULK_DOCS_GENERAL | PROMPT_Q2_DUPLICATE_IDS___PROMPT_COLLISIONS.md | json_item_list | medium | False | False | hybrid | large | False | — |
| Q3 | Q | BULK_DOCS_GENERAL | PROMPT_Q3_DRIFT_DETECTION___NORM_DIFFS.md | json_item_list | medium | False | False | hybrid | large | False | — |
| Q9 | Q | AGG | PROMPT_Q9_MERGE___QA.md | json_item_list | medium | False | True | hybrid | large | True | — |
| Q11 | Q | AGG | PROMPT_Q11_ARTIFACT_COLLISION_REPORT.md | json_item_list | medium | True | True | hybrid | large | False | — |
| R0 | R | BULK_DOCS_GENERAL | PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R1 | R | CE | PROMPT_R1_DOPE_MEMORY_IMPLEMENTATION_TRUTH.md | mix(json_item_list+markdown) | high | False | True | synthesis | large | True | — |
| R2 | R | BULK_DOCS_GENERAL | PROMPT_R2_EVENTBUS_WIRING_TRUTH.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R3 | R | BULK_DOCS_GENERAL | PROMPT_R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R4 | R | BULK_DOCS_GENERAL | PROMPT_R4_TASKX_INTEGRATION_TRUTH.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R5 | R | BULK_DOCS_GENERAL | PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R6 | R | BULK_DOCS_GENERAL | PROMPT_R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R7 | R | BULK_DOCS_GENERAL | PROMPT_R7_CONFLICT_LEDGER.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R8 | R | BULK_DOCS_GENERAL | PROMPT_R8_RISK_REGISTER_TOP20.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R9 | R | BULK_DOCS_GENERAL | PROMPT_R9_LEANTIME_INTEGRATION_TRUTH.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R10 | R | BULK_DOCS_GENERAL | PROMPT_R10_TWO_PLANE_ARCHITECTURE_TRUTH.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| R11 | R | BULK_DOCS_GENERAL | PROMPT_R11_SECURITY_RISK_SYNTHESIS.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S0 | S | BULK_DOCS_GENERAL | PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S1 | S | BULK_DOCS_GENERAL | PROMPT_S1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S2 | S | BULK_DOCS_GENERAL | PROMPT_S2_DECISION_DOSSIER.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S3 | S | BULK_DOCS_GENERAL | PROMPT_S3_ARCHITECTURE_PROOF_HOOKS.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S4 | S | BULK_DOCS_GENERAL | PROMPT_S4_TWO_PLANE_ARCHITECTURE.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S5 | S | BULK_DOCS_GENERAL | PROMPT_S5_TASK_ORCHESTRATOR_ANALYSIS.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S6 | S | BULK_DOCS_GENERAL | PROMPT_S6_LEANTIME_ANALYSIS.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S7 | S | BULK_DOCS_GENERAL | PROMPT_S7_OVERSEER_AGENT_FLOW_DESIGN.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S8 | S | BULK_DOCS_GENERAL | PROMPT_S8_ARCHITECTURE_DIAGRAMS.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S9 | S | BULK_DOCS_GENERAL | PROMPT_S9_DEPENDENCY_GRAPH_SUMMARY.md | markdown | high | True | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S10 | S | BULK_DOCS_GENERAL | PROMPT_S10_API_SURFACE_REFERENCE.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S11 | S | BULK_DOCS_GENERAL | PROMPT_S11_DOCUMENTATION_GENERATION.md | markdown | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| S12 | S | CE | PROMPT_S12_STABILITY_SIGNATURE.md | json_item_list | high | False | True | synthesis | large | False | — |
| T0 | T | CE | PROMPT_T0_TASK_PACKET_FACTORY.md | markdown | high | False | True | synthesis | large | True | — |
| T1 | T | CE | PROMPT_T1_EMIT_TASK_PACKETS___TOP10.md | mix(markdown+json_item_list) | medium | False | True | hybrid | large | True | — |
| T2 | T | BULK_DOCS_GENERAL | PROMPT_T2_PACKET_SCHEMA___AUTHORITY_RULES.md | json_item_list | high | False | False | synthesis | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| T3 | T | CE | PROMPT_T3_PACKET_GENERATION___BATCHED.md | mix(markdown+json_item_list) | medium | False | True | hybrid | large | True | — |
| T4 | T | BULK_DOCS_GENERAL | PROMPT_T4_PACKET_DEDUP___COLLISION_RESOLUTION.md | json_item_list | medium | True | False | hybrid | large | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| T5 | T | BULK_DOCS_GENERAL | PROMPT_T5_PACKET_ORDERING___RUN_PLAN.md | json_item_list | medium | True | False | hybrid | large | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| T9 | T | AGG | PROMPT_T9_MERGE___QA.md | mix(json_item_list+markdown) | medium | False | True | hybrid | large | True | — |
| W0 | W | CE | PROMPT_W0_WORKFLOW_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | False | — |
| W1 | W | CE | PROMPT_W1_WORKFLOW_CATALOG___RUNBOOK_FACTS.md | json_item_list | medium | True | True | extraction | medium | False | — |
| W2 | W | BULK_DOCS_GENERAL | PROMPT_W2_WORKFLOW_INPUTS_OUTPUTS___ARTIFACTS.md | json_item_list | medium | True | False | extraction | medium | False | — |
| W3 | W | BULK_DOCS_GENERAL | PROMPT_W3_MULTI_SERVICE_COORDINATION___COMPOSE_TMUX.md | json_item_list | medium | True | False | extraction | medium | False | — |
| W4 | W | BULK_DOCS_GENERAL | PROMPT_W4_WORKFLOW_FAILURE_MODES___RECOVERY.md | json_item_list | medium | True | False | extraction | medium | False | — |
| W5 | W | BULK_DOCS_GENERAL | PROMPT_W5_WORKFLOW_STATE_DEPENDENCIES___HOME_VS_REPO.md | json_item_list | medium | True | False | extraction | medium | False | — |
| W9 | W | AGG | PROMPT_W9_MERGE___QA.md | json_item_list | medium | True | True | hybrid | medium | True | — |
| X0 | X | CE | PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN.md | json_item_list | medium | True | True | extraction | medium | False | — |
| X1 | X | CE | PROMPT_X1_FEATURE_SURFACE_EXTRACT.md | json_item_list | medium | True | True | extraction | medium | False | — |
| X2 | X | BULK_DOCS_GENERAL | PROMPT_X2_FEATURE_TO_CODE_MAP.md | json_item_list | medium | True | False | extraction | medium | False | — |
| X3 | X | BULK_DOCS_GENERAL | PROMPT_X3_FEATURE_TO_DOC_MAP.md | json_item_list | medium | True | False | extraction | medium | False | — |
| X4 | X | BULK_DOCS_GENERAL | PROMPT_X4_FEATURE_DEPENDENCY_GRAPH.md | json_item_list | medium | True | False | extraction | medium | False | — |
| X9 | X | AGG | PROMPT_X9_MERGE___QA.md | json_item_list | medium | True | True | hybrid | medium | True | — |
| Z0 | Z | CE | PROMPT_Z0_FREEZE_INVENTORY___CHECKSUMS.md | json_item_list | low | False | True | extraction | large | True | lane vs depth mismatch (CE on low-depth step) |
| Z1 | Z | BULK_DOCS_GENERAL | PROMPT_Z1_PROOF_PACK___RUNBOOK.md | markdown | medium | False | False | hybrid | large | True | F2-HIGH-1: premium downstream consumer on bulk lane |
| Z2 | Z | BULK_DOCS_GENERAL | PROMPT_Z2_OPUS_INPUT_BUNDLE___MANIFEST.md | json_item_list | high | False | False | hybrid | large | True | F2-HIGH-1: premium downstream consumer on bulk lane; lane vs depth mismatch (high reasoning on bulk lane) |
| Z9 | Z | AGG | PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md | mix(json_item_list+markdown) | low | False | True | extraction | large | True | — |

---

## 3. Pivot Tables

### 3.1 lane_class × reasoning_depth

| lane_class | low | medium | high | total |
|---|---:|---:|---:|---:|
| AGG | 1 | 13 | 0 | 14 |
| BULK_CODE_HEAVY | 0 | 5 | 1 | 6 |
| BULK_DOCS_GENERAL | 7 | 41 | 25 | 73 |
| CE | 1 | 39 | 3 | 43 |
| **total** | **9** | **98** | **29** | **136** |

**Reading**: BULK_DOCS_GENERAL has 25 high-reasoning steps (34% of the lane), all 25 in R/S/T/Z synthesis phases — the central evidence for the F2-HIGH-1 audit finding. CE is well-aligned (39/43 medium; only 1 low — the deterministic Z0).

### 3.2 phase × premium_floor

| phase | premium_floor=True | premium_floor=False | total |
|---|---:|---:|---:|
| A | 11 | 4 | 15 |
| B | 2 | 3 | 5 |
| C | 14 | 8 | 22 |
| D | 6 | 0 | 6 |
| E | 0 | 8 | 8 |
| G | 2 | 7 | 9 |
| H | 2 | 7 | 9 |
| M | 0 | 7 | 7 |
| Q | 1 | 5 | 6 |
| R | 12 | 0 | 12 |
| S | 12 | 1 | 13 |
| T | 7 | 0 | 7 |
| W | 1 | 6 | 7 |
| X | 1 | 5 | 6 |
| Z | 4 | 0 | 4 |
| **total** | **75** | **61** | **136** |

**Reading**: D-phase flips wholesale to premium because S1 explicitly says *"D-phase artifacts"*. R10/R11 are now correctly premium (caught by S0's *"all R-phase truth reports"*). E and M phases never feed downstream beyond their cluster (E feeds merge/QA only; M is runtime export); G/H/W/X feed only sparsely. R/S/T are nearly 100% premium because they feed each other. **Caveat**: this count is a lower bound (see §1 caveat 2).

### 3.3 strict_json_required × synthesis_vs_extraction

| strict_json_required | extraction | hybrid | synthesis | total |
|---|---:|---:|---:|---:|
| True | 42 | 12 | 3 | 57 |
| False | 47 | 8 | 24 | 79 |
| **total** | **89** | **20** | **27** | **136** |

**Reading**: Strict schema is the gate for *extraction* lanes (74% of strict steps are extraction). Synthesis steps are predominantly non-strict (24/27 → False), because R/S/T output markdown reports with optional JSON sidecars. This pivot validates that strict_json and synthesis are largely orthogonal concerns and should be separate dimensions in the new map.

### 3.4 lane_class × code_specialist_needed

| lane_class | code=True | code=False | total |
|---|---:|---:|---:|
| AGG | 8 | 6 | 14 |
| BULK_CODE_HEAVY | 6 | 0 | 6 |
| BULK_DOCS_GENERAL | 45 | 28 | 73 |
| CE | 31 | 12 | 43 |
| **total** | **90** | **46** | **136** |

**Reading**: 45 BULK_DOCS_GENERAL steps need code specialization but are routed to a generic-docs lane. BULK_CODE_HEAVY only covers 6 steps (C1, C5, C6, C7, C10, C11) — woefully undersized for the actual code-specialist surface (90 steps). The distinction between `BULK_DOCS_GENERAL` and `BULK_CODE_HEAVY` is currently almost vestigial.

### 3.5 Bonus — lane_class × synthesis_vs_extraction (for completeness)

| lane_class | extraction | hybrid | synthesis | total |
|---|---:|---:|---:|---:|
| AGG | 5 | 9 | 0 | 14 |
| BULK_CODE_HEAVY | 5 | 1 | 0 | 6 |
| BULK_DOCS_GENERAL | 42 | 7 | 24 | 73 |
| CE | 37 | 3 | 3 | 43 |

**Reading**: 24 synthesis steps live on BULK_DOCS_GENERAL — the single largest cluster of mis-routing. CE is correctly extraction-heavy (37/43).

---

## 4. Callout Lists — Mismatch Steps

### 4.1 `premium_floor=True` AND lane_class ∈ {BULK_DOCS_GENERAL, BULK_CODE_HEAVY} (44 steps — F2-HIGH-1 family)

These are the audit-confirmed routing mismatches: bulk lanes producing artifacts that authoritative synthesis steps depend on. Source-truth poisoning risk.

| step_id | lane_class | reasoning_depth | upstream of |
|---|---|---|---|
| A2 | BULK_DOCS_GENERAL | medium | MCP server defs → R/S |
| A3 | BULK_DOCS_GENERAL | medium | MCP proxy surface → R/S |
| A4 | BULK_DOCS_GENERAL | medium | Router surface → R/S |
| A5 | BULK_DOCS_GENERAL | medium | Hooks surface → R/S |
| A6 | BULK_DOCS_GENERAL | medium | Compose service graph → R/S |
| A8 | BULK_DOCS_GENERAL | medium | TaskX surface → R/S |
| A10 | BULK_DOCS_GENERAL | medium | Leantime surface → R/S |
| B1 | BULK_DOCS_GENERAL | medium | Boundary assertions → R3 |
| C1 | BULK_CODE_HEAVY | medium | Service entrypoints → R5/S5/S9 |
| C6 | BULK_CODE_HEAVY | medium | Workflow runners → R5/S5 |
| C7 | BULK_CODE_HEAVY | medium | API & dashboards → S10 |
| C11 | BULK_CODE_HEAVY | medium | Leantime integration → R9/S6 |
| D2 | BULK_DOCS_GENERAL | medium | Deep doc extraction → S1 (via D-phase reference) |
| D3 | BULK_DOCS_GENERAL | medium | Citation graph → S1 (via D-phase reference) |
| G4 | BULK_DOCS_GENERAL | medium | Security/secrets facts → R11 |
| H6 | BULK_DOCS_GENERAL | medium | Tmux/workflow helpers → R5 |
| R0 | BULK_DOCS_GENERAL | high | Control-plane truth map → S0/S4 |
| R2 | BULK_DOCS_GENERAL | high | EventBus wiring truth → S0/S4 |
| R3 | BULK_DOCS_GENERAL | high | Boundary enforcement trace → S0/S2 |
| R4 | BULK_DOCS_GENERAL | high | TaskX integration truth → S5/T-phase |
| R5 | BULK_DOCS_GENERAL | high | Workflows truth graph → S0/S4/S7 |
| R6 | BULK_DOCS_GENERAL | high | Portability/migration ledger → S1/S2 |
| R7 | BULK_DOCS_GENERAL | high | Conflict ledger → S0/S2/T0 |
| R8 | BULK_DOCS_GENERAL | high | Risk register top 20 → S2/T0 |
| R9 | BULK_DOCS_GENERAL | high | Leantime integration truth → S6 |
| R10 | BULK_DOCS_GENERAL | high | Two-plane architecture truth → S0 (via R-phase reference) |
| R11 | BULK_DOCS_GENERAL | high | Security risk synthesis → S0 (via R-phase reference) |
| S0 | BULK_DOCS_GENERAL | high | Opus architecture synthesis → S2/S3/T0/Z2 |
| S1 | BULK_DOCS_GENERAL | high | Opus MCP→Hooks migration → T0/Z2 |
| S2 | BULK_DOCS_GENERAL | high | Decision dossier → T0/Z2 |
| S3 | BULK_DOCS_GENERAL | high | Architecture proof hooks → Z1/Z2 |
| S4 | BULK_DOCS_GENERAL | high | Two-plane architecture → S0/T0 |
| S5 | BULK_DOCS_GENERAL | high | Task orchestrator analysis → T0 |
| S6 | BULK_DOCS_GENERAL | high | Leantime analysis → S0/T0 |
| S7 | BULK_DOCS_GENERAL | high | Overseer agent flow → T0 |
| S8 | BULK_DOCS_GENERAL | high | Architecture diagrams → Z2 |
| S9 | BULK_DOCS_GENERAL | high | Dependency graph summary → Z2 |
| S10 | BULK_DOCS_GENERAL | high | API surface reference → Z2 |
| S11 | BULK_DOCS_GENERAL | high | Documentation generation → Z2 |
| T2 | BULK_DOCS_GENERAL | high | Packet schema authority rules → T3/T4/T5 |
| T4 | BULK_DOCS_GENERAL | medium | Packet dedup/collision → T5/T9 |
| T5 | BULK_DOCS_GENERAL | medium | Packet ordering/run plan → T9 |
| Z1 | BULK_DOCS_GENERAL | medium | Proof pack/runbook → Z2 |
| Z2 | BULK_DOCS_GENERAL | high | Opus input bundle/manifest → Z9 |

### 4.2 `reasoning_depth=high` AND lane_class ∈ {BULK_DOCS_GENERAL, BULK_CODE_HEAVY} (26 steps)

Subset of the above — almost identical (R0–R11, S0–S11, T2, Z2, plus C10). C10 (`SERVICE_CATALOG_DEEP`) is the lone non-R/S/Z high-reasoning step on a bulk lane and is *not* premium_floor under the v3 definition.

### 4.3 `reasoning_depth=low` AND lane_class=CE (1 step)

| step_id | prompt_filename | rationale for current CE |
|---|---|---|
| Z0 | `PROMPT_Z0_FREEZE_INVENTORY___CHECKSUMS.md` | Deterministic checksum compute. CE here is justified by *strict_schema + finality*, not reasoning depth. Not a true mismatch; it shows the existing `lane_class` dimension is already overloaded (depth + strictness + finality fused). |

### 4.4 `lane_class=AGG` AND `reasoning_depth=high` (0 steps)

All 14 AGG steps are deterministic merges (medium). One (Z9) is `low`. AGG is the cleanest-mapped existing lane.

### 4.5 `synthesis_vs_extraction=synthesis` AND lane_class ∈ BULK (24 steps)

Identical population to §4.2 minus C10/T2/Z2 (which are `hybrid`). All 11 R-phase synthesis steps and all 12 S-phase synthesis steps are on BULK_DOCS_GENERAL. T2 is a `synthesis` outlier on BULK.

**Total distinct outlier steps across §4.1–§4.5 (deduplicated): 46.**

---

## 5. Structural Decision

### 5.1 The numbers

- Lane-vs-depth mismatches: **27** (high-on-bulk: 26 + low-on-CE: 1)
- Premium-floor + bulk-lane mismatches: **44** (F2-HIGH-1 family)
- Distinct outlier steps (union): **46**

Per the input rule:
- < 25 outliers → lane-class defaults + per-step overrides
- 40+ outliers OR no clear clustering → `(lane_class, capability_tier)` matrix
- Even matrix doesn't fit → per-step blocks for outliers + matrix for the rest

**Decision: `(lane_class, capability_tier)` matrix.** 46 distinct outliers significantly exceeds the 40-step threshold. But the outliers *do* cluster (R-phase all-of-one-kind, S-phase all-of-one-kind, A2–A10 + D2–D3 clean band of surface-extraction-feeding-synthesis, a clean band of T2/T4/T5 packet-engineering). The clustering pattern says the existing `lane_class` axis is *under-dimensioned*, not that the steps are individually pathological. Adding a `capability_tier` axis lets the cluster pattern express itself without 46 per-step overrides.

### 5.2 Why matrix beats per-step overrides

Per-step overrides at 46 steps creates the same maintenance burden as the current state. The clusters (all of R, almost all of S, the A2–A10 band, T2/T4/T5) are too regular to ignore. A two-axis matrix with maybe 8–10 populated cells is the right shape.

### 5.3 Why matrix beats expanding `lane_class`

You could add `SYNTH_BULK`, `SYNTH_PREMIUM`, `CE_DETERMINISTIC` etc. to the existing single axis. That hides the orthogonality between "what shape is this step" (lane_class) and "how much horsepower does it need" (capability_tier). The two axes vary independently in the data (pivot 3.3 shows strict_json and synthesis_vs_extraction are weakly correlated, r ≈ 0 in 2×3 layout). Keep them separate.

### 5.4 Residual outliers (≤ 3 expected after the matrix is applied)

Even with the matrix, expect to need 2–3 per-step blocks:
- **Z0** (CE/low) — strict-schema + finality, not reasoning-driven. Could be its own `CE × low` cell or a one-off override.
- **C10** (`SERVICE_CATALOG_DEEP`, BULK_CODE_HEAVY/high/not-premium) — sole non-R/S/Z high-reasoning step. Override or move to a new `BULK_CODE_HEAVY × high` cell.
- **S12** (`STABILITY_SIGNATURE`, CE/high/synthesis) — the lone CE-routed synthesis step. Makes sense if it produces strict-JSON signatures, but expect it to need a `CE × high` slot.

---

## 6. Recommended Phase C Input

### 6.1 Proposed matrix axes (on the **existing** lane_class taxonomy)

This analysis does **not** propose renaming `lane_class` values. Phase C may choose to rename if it judges the existing names ambiguous, but that decision is out of scope here. The recommendation is to add a second axis on top of the current 4 values.

**Axis 1 — `lane_class` (unchanged, 4 values)**:

| value | population | role today |
|---|---:|---|
| `CE` | 43 | Strict-schema + evidence-bound extraction |
| `BULK_DOCS_GENERAL` | 73 | Non-strict, doc-grade extraction (current overflow lane) |
| `BULK_CODE_HEAVY` | 6 | Non-strict, code-aware extraction |
| `AGG` | 14 | Deterministic merge/QA |

**Axis 2 — `capability_tier` (new, 4 values proposed)**:

| tier | criteria | expected population |
|---|---|---:|
| `low` | deterministic enumeration; M-phase exports, Z0 freeze, `*_partition_plan` with no classification | ~9 |
| `medium` | scan+classify, cross-module symbol search, merge/dedup with rules | ~98 |
| `high` | cross-document synthesis, arbitration, risk synthesis | ~28 |
| `critical` | premium_floor=True AND high reasoning AND output cascades to final operator decision (a hand-picked subset, e.g. S0 Opus architecture synthesis, R7 conflict ledger, T0 task packet factory) | ~1–3 |

`critical` is a routing escalation level for the steps whose mis-output would invalidate the operator's go/no-go verdict. It's not data-derivable; Phase C picks it.

### 6.2 Lane-class defaults to design (Phase C)

4 lane_class × 4 capability_tier = 16 cells. Realistically only ~10 are populated, listed here with the step families they would cover. These are **observations of how steps cluster**, not route specifications.

| Cell | observed step families |
|---|---|
| `(BULK_DOCS_GENERAL, low)` | M0–M6 — runtime exports |
| `(BULK_DOCS_GENERAL, medium)` | A2/A3/A4/A5/A6/A7/A8/A9/A10, B1–B3, D2/D3, E1–E6, G2/G3/G4, H2/H4–H7, W2–W5, X2–X4, T4/T5, Z1 — the bulk extraction surface |
| `(BULK_DOCS_GENERAL, high)` | R0/R2–R11, S0–S11, T2, Z2 — the F2-HIGH-1 mis-routed cluster |
| `(BULK_CODE_HEAVY, medium)` | C1, C5, C6, C7, C11 — code-aware extraction |
| `(BULK_CODE_HEAVY, high)` | C10 — sole high-reasoning step in this lane |
| `(CE, low)` | Z0 — deterministic freeze inventory |
| `(CE, medium)` | A0/A1/A11–A13, B0, all CE C-phase steps, D0/D1, G0/G1/G5/G6/G7, H0/H1/H3, Q0, W0/W1, X0/X1 |
| `(CE, high)` | R1, S12, T0, T1, T3 — strict-schema synthesis or mixed-kind packet steps |
| `(AGG, low)` | Z9 — freeze manifest |
| `(AGG, medium)` | All 13 `*_merge_qa` / `*_merge___qa` steps + Q9, Q11, D4, D5, T9, etc. |

### 6.3 Per-step overrides expected (Phase C)

After the matrix lands, expect these 4–6 per-step overrides:
- **Z0** — could fit `(CE, low)` cell exactly; verify the strict-JSON path doesn't need its own route.
- **C10** — `SERVICE_CATALOG_DEEP` is the only `(BULK_CODE_HEAVY, high)` occupant. Either promote to `(BULK_DOCS_GENERAL, high)` family or keep its own override.
- **S12** — sole CE-routed synthesis with high reasoning. May warrant escalation if it touches the same downstream as Z2.
- **T0** — Task packet factory; possible `critical` candidate.
- **T1, T3** — mixed-kind outputs and hybrid synthesis/extraction; verify routing fits `(CE, medium)` or needs override.

### 6.4 Cross-cutting attributes (NOT axes of the matrix)

These should be step-level *flags*, not lane axes:
- `code_specialist_required: bool` (90 true, 46 false) — currently encoded as `BULK_CODE_HEAVY` vs `BULK_DOCS_GENERAL`, which only catches 6 of 90 true cases. Promote to a flag.
- `strict_json_required: bool` (57 true, 79 false) — already exists in `model_map.yaml`; keep.
- `premium_floor: bool` (75 true, 61 false) — newly computed; use for cost-vs-quality decisions independently. **Caveat**: this is a lower bound (see §1).
- `partition_input_size_class: enum` (9 small, 85 medium, 42 large) — informs context-window pricing tier.

### 6.5 Phase C deliverables (suggested — not specified by this analysis)

1. Define the matrix with route blocks for the ~10 populated cells (~70% of `model_map.yaml` collapses to references to these cells).
2. Add the 4 step-level flags above to each step entry.
3. Per-step overrides for the ~5 outliers identified in §6.3.
4. **Propose** Phase C consider a cost-routing policy: `premium_floor=True AND capability_tier ∈ {high, critical}` should not share a route family with `premium_floor=False AND capability_tier=low`. This is a Phase C decision, not a fact from this analysis.

### 6.6 Final outlier expectation

Matrix + 4–6 per-step overrides = significant reduction in current `model_map.yaml` size (4005 lines today), and resolves all 46 mismatch steps either by cell or by named override.

---

## 7. Limitations & Open Questions

- **Reasoning-depth classifier is rule-based, not model-derived.** The 27 high-on-bulk steps were classified entirely by phase + filename + keyword cooccurrence. A spot-check on R0, S0, S2, T0 confirms `high` is correct, but borderline cases (T1, T3, T4, T5, Z1) could swing medium↔high depending on interpretation. Phase C should re-validate borderline rows against actual prompt bodies if cost/quality tradeoff is tight.
- **`premium_floor` is a lower bound.** v3 catches verbatim artifact mentions and named phase references. It does NOT catch the unbounded *"all upstream extraction artifacts"* phrasing that appears in 15 R/S/T/Z prompts. Counting those would flip every A/B/C/D/E/G/H/M/Q/W/X step to `premium_floor=True` — informative for cost decisions but useless for routing structure. The targeted-phase v3 detection captures every named consumer; the residual undercount is small (likely 5–10 steps).
- **The `code_specialist_needed` axis** is derived from prompt content + filename. Some D/H/M steps marked False are markdown/docs-heavy; that's correct. But H4 (LiteLLM surfaces) is flagged True via keyword overlap — verify if config-as-code counts.
- **Z0 mismatch is semantically expected.** Don't reclassify it to BULK based on this analysis alone; it's a finality+strict-schema special case.
- **`critical` capability_tier is not derivable from the data.** Phase C must pick the 1–3 steps where reasoning-class+extended-thinking is justified. S0, R7, T0 are the most defensible candidates; the data only narrows the candidate pool.

---

*Generated 2026-05-23 by automated analysis of v4 promptset metadata + prompt section parsing. Raw classification table cached at `/tmp/v4_step_table.json`.*
