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
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- `WORKFLOWS_TRUTH_GRAPH.md`
- `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
- `CONFLICT_LEDGER.md`
- `RISK_REGISTER_TOP20.md`
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
1. Load only provided phase synthesis inputs and build a deterministic evidence index keyed by artifact and section.
2. Produce implemented/planned splits for each subsystem before writing conclusions.
3. Consume `CONFLICT_LEDGER.md` and classify each material conflict as `RESOLVED` or `ESCALATE_TO_PRO` with evidence.
4. Build risk-to-decision mapping so each decision references one or more `R8` risk IDs.
5. Write each declared output with stable section order, stable list ordering, and explicit unknown handling.
6. Mirror the architecture narrative into both `ARCHITECTURE_SYNTHESIS_OPUS.md` and `S0_ARCHITECTURE_SYNTHESIS_OPUS.md` so compatibility and step-specific consumers receive the same deterministic payload.

## Evidence Rules
- Every non-trivial sentence must terminate with an evidence anchor in the canonical form.
- Evidence anchors must resolve to supplied artifacts only; unsupported anchors are invalid.
- For structured rows, include source evidence in the row itself rather than a detached appendix.
- If evidence is conflicting, cite both sides and identify whether the item is resolved or escalated.
- If evidence is absent, emit `UNKNOWN` and include `missing_evidence` details.
- Evidence objects, when used in structured snippets, must include keys `path`, `line_range`, and `excerpt` to keep parity with norm contracts.
- No uncited policy claims, no uncited migration advice, and no uncited risk severity assertions.

## Determinism Rules
- Do not include generated timestamps or runtime identity keys such as `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Use fixed heading order and fixed row ordering by deterministic keys.
- Keep terminology stable: use `IMPLEMENTED`, `PLANNED`, `UNKNOWN`, `RESOLVED`, `ESCALATE_TO_PRO` exactly as spelled.
- Avoid speculative language such as "probably", "likely", or "might be" unless explicitly qualified as `UNKNOWN` with evidence gaps.
- Ensure alias outputs are semantic copies of their canonical siblings.
- Keep markdown deterministic: no random bullet ordering, no free-form appendices that alter ordering between runs.

## Anti-Fabrication Rules
- Do not infer mechanisms from filenames, directory names, or prior expectations.
- Do not invent services, endpoints, guardrails, workflows, or migration stages.
- Do not claim commands were executed; only provide bounded verification suggestions where requested.
- Do not collapse conflicting evidence into a single assertion without conflict status.
- Do not replace missing evidence with intuition; retain explicit `UNKNOWN` entries.
- Do not introduce references to artifacts outside this step's supplied input set.
- Do not emit hidden assumptions; every assumption must be explicit and evidence-backed.

## Failure Modes
- Missing required `R*` artifacts: fail closed by writing only `UNKNOWN` conclusions and listing missing artifacts.
- Conflicting arbitration statements without enough evidence to resolve: mark `ESCALATE_TO_PRO` and identify required ruling scope.
- Partial optional inputs (`X`, `T`, `Z`) absent: continue with required `R` artifacts and annotate reduced context.
- Risk mapping cannot be completed: include explicit `UNKNOWN` decision risk links and missing artifact references.
- Output alias mismatch between `ARCHITECTURE_SYNTHESIS_OPUS.md` and `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`: treat as invalid and rewrite both deterministically.
- Non-deterministic wording drift: normalize section names and status tokens to the prescribed vocabulary before final output.
