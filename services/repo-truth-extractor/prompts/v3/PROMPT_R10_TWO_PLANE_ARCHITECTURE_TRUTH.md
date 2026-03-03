# PROMPT_R10

## Goal
Produce a deterministic, evidence-backed architecture truth report for the two-plane model currently implemented in the repository.
Focus on explicit boundaries, authority ownership, and integration edges proven by code/config/docs.

## Inputs
- Upstream normalized artifacts:
  - `SERVICE_CATALOG.json`
  - `TRINITY_ENFORCEMENT_SURFACE.json`
  - `BOUNDARY_ENFORCEMENT_POINTS.json`
  - `BOUNDARY_MERGED.json`
  - `EVENTBUS_SURFACE.json`
  - `DOPE_MEMORY_CODE_SURFACE.json`
  - `LEANTIME_INTEGRATION_TRUTH.md`
  - `RISK_REGISTER_TOP20.md`
- Supporting source/doc paths for disambiguation:
  - `src/dopemux/**`
  - `services/**`
  - `docs/90-adr/**`
  - `docs/04-explanation/**`
  - `services/registry.yaml`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `TWO_PLANE_ARCHITECTURE_TRUTH.md`

## Schema
- Output type: deterministic markdown report (`kind: markdown`, `merge_strategy: markdown_concat`).
- Output contract:
  - `TWO_PLANE_ARCHITECTURE_TRUTH.md`
    - `canonical_writer_step_id`: `R10`
    - `required_sections`: `Plane Definitions, Authority Ownership Matrix, Cross-Plane Integration Paths, Boundary Enforcement and Failure Rails, Current Drift and Risks, Evidence Index`
- Required section order:
  1. `## Plane Definitions`
  2. `## Authority Ownership Matrix`
  3. `## Cross-Plane Integration Paths`
  4. `## Boundary Enforcement and Failure Rails`
  5. `## Current Drift and Risks`
  6. `## Evidence Index`
- Ownership matrix rows must include:
  - `surface`
  - `owner_plane`
  - `evidence`

## Extraction Procedure
1. Extract explicit plane and boundary claims from upstream artifacts.
2. Build ownership rows by matching surfaces to evidenced owner components.
3. Identify cross-plane integration edges with direct evidence.
4. Capture drift/risk items only when explicitly supported by evidence.
5. Emit required sections in deterministic order.

## Evidence Rules
- Every claim and matrix row must include evidence objects:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- Evidence index must include all unique evidence references used above.
- Avoid indirect claims if direct evidence is unavailable.
- Keep all evidence paths repo-relative.

## Determinism Rules
- Output must be timestamp-free and run-id-free.
- Section order and subsection ordering are fixed.
- Matrix rows sorted by `(surface, owner_plane)`.
- Evidence entries sorted by `(path, line_start, excerpt)` with deterministic dedup.

## Anti-Fabrication Rules
- Do not invent plane boundaries or ownership rules.
- Do not infer architectural intent from naming alone.
- If ownership cannot be proven, use `UNKNOWN` with evidence gap note.
- Keep recommendations out of this truth artifact; include only evidenced state.

## Failure Modes
- Missing artifacts: emit skeletal report with required headings and explicit missing-input notes.
- Conflicting evidence: present both sides with conflict markers and evidence references.
- Ambiguous ownership: keep row with `owner_plane: UNKNOWN`.
- Excessive uncertainty: downgrade to concise truth table plus explicit unresolved list.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: R10 - Two Plane Architecture Truth
Phase: R
Step: R10
Outputs:
- TWO_PLANE_ARCHITECTURE_TRUTH.md
Mode: synthesis
Strict: evidence_only
```
