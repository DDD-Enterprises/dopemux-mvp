# PROMPT_S6

## Goal
Produce phase `S6` synthesis artifacts detailing the Leantime integration footprint. This step builds an aggregate report of how Leantime interacts with the orchestration layer, syncs state, and manages PM context based on upstream truth extractions.

## Inputs
- Source scope:
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/C_code_baseline/norm/**`
- Required artifacts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
  - `WORKFLOWS_TRUTH_GRAPH.md`
  - `EVENTBUS_WIRING_TRUTH.md`
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
- Optional synthesis helpers:
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`

## Outputs
- `LEANTIME_INTEGRATION_SYNTHESIS.md`
- `S6_LEANTIME_SYNTHESIS.md`

## Schema
- Artifact kind: markdown outputs with deterministic headings and tables where appropriate.
- Canonical writer: `S6` for every declared output in this step.
- Required sections:
  - Leantime Bridge Role
  - State Sync & Event Mappings
  - PM Context Surfaces
  - Security & Authorization
  - Unmapped Footprint & Gaps
- Alias requirement:
  - `LEANTIME_INTEGRATION_SYNTHESIS.md` and `S6_LEANTIME_SYNTHESIS.md` must remain semantically aligned.

## Extraction Procedure
1. Load Phase C and R synthesis inputs.
2. Outline the Bridge Role using control plane and code inputs.
3. Map State Sync using Eventbus Wiring truths.
4. Detail the PM Context footprint (how data enters/exits Leantime).
5. Document any identified security, key, or token flows using truth artifacts.
6. Create identical canonical output files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
