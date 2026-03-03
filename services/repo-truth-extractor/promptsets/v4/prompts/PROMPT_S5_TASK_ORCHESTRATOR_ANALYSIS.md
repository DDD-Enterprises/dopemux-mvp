# PROMPT_S5

## Goal
Produce phase `S5` synthesis artifacts analyzing the Task Orchestrator. This step consolidates integration scope, delegation properties, predictive routing characteristics, and orchestrator boundaries compared against Phase R arbitration.

## Inputs
- Source scope:
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/A_repo_control_plane/norm/**`
  - `extraction/**/C_code_baseline/norm/**`
- Required artifacts:
  - `TASKX_INTEGRATION_TRUTH.md`
  - `WORKFLOWS_TRUTH_GRAPH.md`
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
  - `CONTROL_PLANE_TRUTH_MAP.md`
- Optional synthesis helpers:
  - `REPO_TASKX_SURFACE.json`
  - `SERVICE_ENTRYPOINTS.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`

## Outputs
- `TASK_ORCHESTRATOR_SYNTHESIS.md`
- `S5_TASK_ORCHESTRATOR.md`

## Schema
- Artifact kind: markdown outputs with deterministic headings and tables where appropriate.
- Canonical writer: `S5` for every declared output in this step.
- Required sections:
  - Dispatch & Routing Topology
  - Authority & Constraints
  - Failure Domain and Blast Radius
  - System Dependencies
  - Operational Gaps
- Alias requirement:
  - `TASK_ORCHESTRATOR_SYNTHESIS.md` and `S5_TASK_ORCHESTRATOR.md` must remain semantically aligned.

## Extraction Procedure
1. Load Phase A, C, and R synthesis inputs related to Task Orchestration and TaskX.
2. Formulate the Dispatch & Routing Topology using workflow and surface artifacts.
3. Validate Authority & Constraints boundaries using Truth artifacts.
4. Synthesize Failure Domain metrics using the Truth maps.
5. Identify unevidenced or highly-coupled dependencies and Operational Gaps.
6. Format identically into both `TASK_ORCHESTRATOR_SYNTHESIS.md` and `S5_TASK_ORCHESTRATOR.md`.

## Evidence Rules
- Every mechanism (e.g., routing algorithm, dependency check) must cite the provided extraction file.
- Fallback behaviors must explicitly reference code or control truth evidence.
- Do not cite files outside of the provided scope.

## Determinism Rules
- Fix the output structure and sort lists lexicographically by dependency name.
- Avoid runtime elements like timestamps or generic speculative language.

## Anti-Fabrication Rules
- Do not infer orchestrator plugins or modules that have no presence in the artifacts.
- Do not claim the orchestrator controls services decoupled in the `WORKFLOWS_TRUTH_GRAPH.md`.

## Failure Modes
- Missing TaskX / Task Orchestrator inputs: state `UNKNOWN` orchestrator status and abort further evaluation.
- Contradictory truth sources: emit `ESCALATE_TO_PRO` describing the contradiction.
