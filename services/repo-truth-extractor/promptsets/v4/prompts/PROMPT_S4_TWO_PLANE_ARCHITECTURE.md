# PROMPT_S4

## Goal
Produce phase `S4` synthesis artifacts analyzing the Dual-Plane Architecture (PM Planning vs Implementation Plane) from arbitration and code truth inputs. This step evaluates boundary separation, integration points, and architectural consistency compared to Trinity and other core features.

## Inputs
- Source scope:
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/S_synthesis/norm/**`
- Required artifacts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
  - `WORKFLOWS_TRUTH_GRAPH.md`
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
- Optional synthesis helpers:
  - `TP_MERGED.json`
  - `WORKFLOW_MERGED.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`

## Outputs
- `TWO_PLANE_ARCHITECTURE_ANALYSIS.md`
- `S4_TWO_PLANE_ARCHITECTURE.md`

## Schema
- Artifact kind: markdown outputs with deterministic headings and tables where appropriate.
- Canonical writer: `S4` for every declared output in this step.
- Required sections:
  - PM Planning Plane (Boundaries, Actors, Artifacts)
  - Implementation Plane (Boundaries, Actors, Artifacts)
  - Intersection & Hand-off Points
  - Comparison with Trinity Architecture
  - Unknowns & Evidence Gaps
- Alias requirement:
  - `TWO_PLANE_ARCHITECTURE_ANALYSIS.md` and `S4_TWO_PLANE_ARCHITECTURE.md` must remain semantically aligned.

## Extraction Procedure
1. Load Phase R and S synthesis inputs.
2. Outline the PM Planning Plane focusing on workflow entrypoints and authority.
3. Outline the Implementation Plane focusing on execution, agents, and state.
4. Detail the intersection points between the two planes.
5. Contrast the Dual-Plane model against the Trinity architecture guarantees.
6. Write the analysis with strict evidence anchors.
7. Mirror the outputs into their respective alias files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
