# PROMPT_R9

## Goal
Synthesize a deterministic, evidence-anchored truth memo that describes how Leantime integration is implemented across the repository today.
This is a reconciliation step over upstream norm artifacts, not freeform analysis.

## Inputs
- Upstream normalized artifacts:
  - `REPO_LEANTIME_SURFACE.json`
  - `LEANTIME_INTEGRATION_SURFACE.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `SERVICE_CATALOG.json`
  - `RISK_REGISTER_TOP20.md`
- Supporting source files when needed for disambiguation:
  - `services/leantime-bridge/**`
  - `src/dopemux/**`
  - `services/registry.yaml`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `LEANTIME_INTEGRATION_TRUTH.md`

## Schema
- Output type: deterministic markdown report (`kind: markdown`, `merge_strategy: markdown_concat`).
- Output contract:
  - `LEANTIME_INTEGRATION_TRUTH.md`
    - `canonical_writer_step_id`: `R9`
    - `required_sections`: `Scope, Confirmed Integration Surfaces, Data and Event Flows, Configuration and Runtime Contracts, Gaps and Unknowns, Evidence Index`
- Required section order:
  1. `## Scope`
  2. `## Confirmed Integration Surfaces`
  3. `## Data and Event Flows`
  4. `## Configuration and Runtime Contracts`
  5. `## Gaps and Unknowns`
  6. `## Evidence Index`
- Every claim section must include explicit evidence bullets (`path`, `line_range`, `excerpt`).

## Extraction Procedure
1. Load `REPO_LEANTIME_SURFACE.json`, `LEANTIME_INTEGRATION_SURFACE.json`, and EventBus/Service artifacts.
2. Confirm **Integration Surfaces**: Identify exact API endpoints, database schemas, or symbols used for Leantime integration from Phase C.
3. Map **Data & Event Flows**: Trace events from production points to Leantime handlers/consumers identified in `EVENT_CONSUMERS.json`.
4. Verify **Runtime Contracts**: Extract environment variables and configuration keys (Phase A/H) required for the Leantime bridge.
5. Identify **Gaps & Unknowns**: Flag any integration points declared in documentation (Phase D) but lacking implementation evidence (Phase C).
6. Arbitration: Resolve conflicts by prioritizing direct Code evidence (Phase C) over Architectural Surface definitions (Phase A).
7. Emit required sections in the exact order defined in the schema.
8. Legacy Context is intent guidance only and is never evidence.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: R9 - Leantime Integration Truth
Phase: R
Step: R9
Outputs:
- LEANTIME_INTEGRATION_TRUTH.md
Mode: synthesis
Strict: evidence_only
```
