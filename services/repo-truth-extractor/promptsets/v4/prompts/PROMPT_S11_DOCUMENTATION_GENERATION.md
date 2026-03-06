# PROMPT_S11

## Goal
Produce `S11` synthesis output for phase `S` with deterministic structure and explicit evidence anchors.
Consolidate all S0–S10 synthesis outputs into a final documentation generation artifact. This step does NOT scan the repository directly — it consumes only upstream synthesis artifacts and cites their IDs for provenance.

## Inputs
- Required upstream artifacts (consume only, no repo scan):
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
  - `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`
  - `S2_DECISION_DOSSIER.md`
  - `S3_ARCH_PROOF_HOOKS.md`
  - `S4_TWO_PLANE_ARCHITECTURE.md`
  - `S5_TASK_ORCHESTRATOR.md`
  - `S6_LEANTIME_SYNTHESIS.md`
  - `S7_OVERSEER_AGENT_FLOW_DESIGN.md`
  - `S8_ARCHITECTURE_DIAGRAMS.md`
  - `S9_DEPENDENCY_GRAPH_SUMMARY.md`
  - `S10_API_SURFACE_REFERENCE.md`
- Optional upstream artifacts:
  - `ARCHITECTURE_SYNTHESIS_OPUS.md`
  - `RISK_REGISTER_TOP20.md`
  - `CONFLICT_LEDGER.md`
  - `TP_SUMMARY.md`
  - `FREEZE_README.md`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Consume only precollected phase inputs. Do not scan source trees directly.
  - Every section must cite the upstream artifact ID it draws from.

## Outputs
- `S11_DOCUMENTATION_GENERATION.md`

## Schema
- Artifact kind: markdown output — consolidated documentation.
- Canonical writer: `S11`
- Required output content contracts:
  - `S11_DOCUMENTATION_GENERATION.md`
    - Section 1: **Executive Summary** — high-level architecture narrative from `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
    - Section 2: **Architecture Overview** — diagrams and topology from `S8_ARCHITECTURE_DIAGRAMS.md`
    - Section 3: **Two-Plane Architecture** — PM plane + cognitive plane from `S4_TWO_PLANE_ARCHITECTURE.md`
    - Section 4: **Service Catalog & Dependencies** — dependency analysis from `S9_DEPENDENCY_GRAPH_SUMMARY.md`
    - Section 5: **API Reference** — unified API surface from `S10_API_SURFACE_REFERENCE.md`
    - Section 6: **Agent Orchestration** — overseer/agent flow from `S7_OVERSEER_AGENT_FLOW_DESIGN.md` and `S5_TASK_ORCHESTRATOR.md`
    - Section 7: **Key Decisions** — decision dossier from `S2_DECISION_DOSSIER.md`
    - Section 8: **Migration & Evolution** — MCP-to-hooks migration from `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`
    - Section 9: **Risk Register** — top risks from `RISK_REGISTER_TOP20.md` (if available)
    - Section 10: **Appendix: Artifact Provenance** — table mapping each section to its source artifact IDs
    - Each section header must include `Source: <artifact_ID>`
- Required citation shape:
  - `SOURCE: <artifact_filename>`

## Extraction Procedure
1. Load all available upstream synthesis artifacts from S0 through S10
2. For each section, extract the key findings and structure from the corresponding source artifact
3. Preserve the essential content — do not paraphrase excessively; maintain the analytical integrity of upstream synthesis
4. Build the provenance table: for each section, list every upstream artifact ID referenced
5. For sections whose source artifact is missing, emit: `⚠️ Source not available: <artifact_filename>`
6. Cross-reference between sections to add navigation links (e.g., "See Section 4 for dependency details")
7. Validate that every load-bearing claim has a source citation
8. Emit exactly the declared output and no additional files

## Evidence Rules
- Every section must begin with a source citation: `SOURCE: <artifact_filename>`
- Every load-bearing claim within a section must be traceable to the cited source artifact.
- The provenance appendix must be complete: every referenced artifact must appear.
- Do not include claims that cannot be traced to any upstream artifact.

## Determinism Rules
- Do not include `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Use fixed section ordering as specified in the schema (Sections 1–10).
- Use consistent terminology from upstream artifacts; do not introduce synonyms.
- Keep headings, citation styles, and formatting deterministic across runs.

## Anti-Fabrication Rules
- Do not invent architectural claims, decisions, or analysis not present in upstream artifacts.
- Do not scan the repository directly — all information must come from declared inputs.
- Do not add editorial commentary, recommendations, or opinions beyond what upstream synthesis provides.
- If an upstream artifact is empty or missing, state the gap explicitly rather than fabricating content.
- Do not introduce references to artifacts outside this step's supplied input set.

## Failure Modes
- Missing required S-phase artifacts: emit section header with `⚠️ Source not available` note and continue with remaining sections.
- All artifacts missing: emit a minimal document with the provenance table listing all expected artifacts as `NOT_AVAILABLE`.
- Conflicting information across synthesis artifacts: cite both sources and note the conflict explicitly.
- Upstream synthesis was partial: propagate partial status with `[PARTIAL]` annotation and evidence of what is covered vs. missing.
- Exceeds reasonable document length: summarize verbose sections and note `[SUMMARIZED: see <artifact> for full detail]`.
