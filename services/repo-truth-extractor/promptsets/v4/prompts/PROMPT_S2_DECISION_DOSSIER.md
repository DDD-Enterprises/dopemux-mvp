# PROMPT_S2

## Goal
Produce phase `S2` decision dossier artifacts that compress synthesis results into implementation-ready decision rows. The dossier must preserve evidence traceability, unknown boundaries, and escalation hooks for unresolved conflicts.

## Inputs
- Source scope:
  - `extraction/**/S_synthesis/norm/**`
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/T_task_packets/norm/**`
- Required artifacts:
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
  - `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`
  - `CONFLICT_LEDGER.md`
  - `RISK_REGISTER_TOP20.md`
- Optional artifacts:
  - `TP_MERGED.json`
  - `FEATURE_INDEX_MERGED.json`
- Constraint:
  - Decision rows must be grounded in supplied evidence only.

## Outputs
- `DECISION_DOSSIER_OPUS.md`
- `S2_DECISION_DOSSIER.md`

## Schema
- Artifact kind: markdown decision tables and registers.
- Canonical writer: `S2` for both outputs.
- Required row fields per decision:
  - `decision_id`
  - `context`
  - `options`
  - `recommendation`
  - `evidence`
  - `risk_ids`
  - `verification_suggestions`
  - `stop_conditions`
- Required sections:
  - Decision table
  - Escalation queue
  - Unknown register
- Output alias requirement:
  - `DECISION_DOSSIER_OPUS.md` and `S2_DECISION_DOSSIER.md` must convey the same decision corpus.

## Extraction Procedure
1. Load all required upstream artifacts as specified in the inputs section. Produce a decision dossier by aggregating all architectural decisions, trade-offs, conflicts, and risk assessments from R-phase reports. Organize decisions by domain, link to supporting evidence, and highlight unresolved decisions requiring human input.
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
