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

## Evidence Rules
- Each load-bearing statement must cite evidence in this structure:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- Evidence must reference repository files or upstream norm artifacts only.
- No paraphrased quotes in evidence index.
- Evidence paths remain repo-relative for portability.

## Determinism Rules
- Markdown output must not contain timestamps, run IDs, or non-deterministic counters.
- Sort evidence entries by `(path, line_start, excerpt)` and claims by stable claim key.
- Keep heading order fixed exactly as defined in the schema.
- Use deterministic bullet ordering for repeated categories.

## Anti-Fabrication Rules
- Do not invent integration paths, APIs, or runtime behavior.
- Do not promote inferred architecture claims to fact.
- If an expected integration surface has no evidence, mark as `UNKNOWN`.
- Never use `Legacy Context` as evidence.

## Failure Modes
- Missing upstream artifacts: emit report with `Scope` + `Gaps and Unknowns` + `Evidence Index`.
- Conflicting artifact claims: include both with explicit conflict notes and evidence.
- Partial evidence: keep claim as tentative with `status: needs_review`.
- Markdown schema risk: prefer empty section placeholders over dropping required headings.

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
