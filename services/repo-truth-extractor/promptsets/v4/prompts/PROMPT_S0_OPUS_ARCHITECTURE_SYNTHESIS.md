# PROMPT_S0

## Goal
Produce phase `S0` synthesis artifacts from arbitration truth inputs with deterministic structure and explicit evidence anchors. This step consolidates implementation reality, conflict resolution status, and risk-mapped decision framing without performing any additional repository excavation.

## Inputs
- Source scope:
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/X_feature_index/norm/**`
  - `extraction/**/T_task_packets/norm/**`
  - `extraction/**/Z_handoff_freeze/norm/**`
- Required arbitration artifacts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
  - `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
  - `EVENTBUS_WIRING_TRUTH.md`
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
  - `TASKX_INTEGRATION_TRUTH.md`
  - `WORKFLOWS_TRUTH_GRAPH.md`
  - `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
  - `CONFLICT_LEDGER.md`
  - `RISK_REGISTER_TOP20.md`
- Optional synthesis helpers:
  - `FEATURE_INDEX_MERGED.json`
  - `TP_MERGED.json`
  - `TP_SUMMARY.md`
  - `FREEZE_MANIFEST.json`
  - `FREEZE_README.md`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Consume only precollected phase inputs. Do not scan source trees directly.

## Outputs
- `ARCHITECTURE_SYNTHESIS_OPUS.md`
- `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`

## Schema
- Artifact kind: markdown outputs with deterministic headings and tables where appropriate.
- Canonical writer: `S0` for every declared output in this step.
- Required output content contracts:
  - `CONTROL_PLANE_TRUTH_MAP.md`: control-plane realities with implemented vs planned separation and evidence anchors.
  - `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`: memory subsystem findings, persistence surfaces, and bounded unknowns.
  - `EVENTBUS_WIRING_TRUTH.md`: producer/consumer pathways, payload surfaces, and conflict annotations.
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`: boundary/guardrail traces with explicit enforcement points.
  - `TASKX_INTEGRATION_TRUTH.md`: TaskX coupling map, authority touchpoints, and drift indicators.
  - `WORKFLOWS_TRUTH_GRAPH.md`: workflow graph narrative with dependency and failure-mode evidence.
  - `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`: portability risks with mitigation notes tied to R8 risk IDs.
  - `CONFLICT_LEDGER.md`: conflict intake with `RESOLVED` or `ESCALATE_TO_PRO` outcomes.
  - `RISK_REGISTER_TOP20.md`: top risks with severity rationale and explicit evidence references.
  - `ARCHITECTURE_SYNTHESIS_OPUS.md`: decision-grade architecture narrative.
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`: alias copy of architecture synthesis for step-scoped consumers.
- Required citation shape for load-bearing claims:
  - `EVIDENCE: <artifact_filename>#<section_heading_or_anchor>`

## Extraction Procedure
1. Load all required upstream artifacts as specified in the inputs section. Produce architecture synthesis by loading all R-phase truth reports and reconciliation outputs. Synthesize a unified architectural view covering control planes, memory implementation, eventbus wiring, boundary enforcement, TaskX integration, and workflow orchestration.
2. For each synthesis claim or recommendation, require evidence chains tracing back to normalized extraction artifacts. Do not introduce claims unsupported by upstream evidence.
3. Structure the output with clear sections, evidence citations (artifact ID, path, line range), and an explicit UNKNOWN/gaps section for areas where evidence is insufficient.
4. Cross-reference the synthesis against upstream QA reports (`PIPELINE_DOCTOR_REPORT.json` if available) to validate that the synthesis does not depend on artifacts flagged as incomplete or corrupted.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
