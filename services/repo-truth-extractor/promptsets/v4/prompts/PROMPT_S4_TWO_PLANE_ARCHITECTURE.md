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

## Evidence Rules
- Every structural claim must carry a citation to the provided R/S input artifacts.
- No inference outside of actual evidence (e.g. do not invent new planes or hand-off mechanisms).
- Unsupported intersections must be marked `UNKNOWN` with missing evidence rationale.
- All evidence citations must include `path`, `line_range`, and `excerpt` keys.

## Determinism Rules
- Sort all intersection lists deterministically by boundary name.
- Do not output timestamps, run IDs, or `generated_at` fields.
- Ensure identical semantics for BOTH alias files; the output must be stable across multiple runs with the same input.
- Avoid any nondeterministic elements such as randomly ordered lists or speculative language.

## Anti-Fabrication Rules
- Do not hallucinate external integrations without evidence.
- Do not invent new components that span planes unless specified in the truth inputs.
- Do not assume a plane performs a task without an explicit workflow trace.

## Failure Modes
- Missing context from S0 or R3: Add partial completeness warning and list missing inputs.
- If no explicit dual-plane distinction exists in evidence, output `UNKNOWN` and describe the observed monolithic state.
