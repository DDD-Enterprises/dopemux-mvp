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

## Evidence Rules
- Every decision row must include evidence anchors in canonical format.
- Every recommendation must map to at least one `R8` risk ID.
- Conflicted decisions must cite the associated `R7` conflict entry.
- If evidence is missing, set recommendation to `UNKNOWN` and cite missing artifacts.
- If structured evidence snippets appear, they must include `path`, `line_range`, and `excerpt`.
- No decision may be emitted without traceable evidence.
- Escalation queue items must cite exact anchors that triggered escalation.

## Determinism Rules
- Disallow runtime keys: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Use fixed headings and table column order.
- Order decisions by `decision_id` or deterministic fallback key.
- Normalize status tokens (`RECOMMEND`, `DEFER`, `UNKNOWN`, `ESCALATE_TO_PRO`).
- Keep both outputs synchronized from the same deterministic representation.
- Avoid free-text drift by using concise, bounded language.

## Anti-Fabrication Rules
- Do not invent decision IDs, risk IDs, or conflict IDs without evidence.
- Do not infer implementation readiness when evidence is incomplete.
- Do not add hidden assumptions to recommendation rationale.
- Do not claim command execution; suggestions only.
- Do not synthesize options that are not represented in source artifacts.
- Do not suppress unknowns to make decisions look complete.

## Failure Modes
- Missing S0 or S1 input artifacts: emit unknown-only dossier with explicit missing inputs.
- Risk linkage absent for a decision: downgrade recommendation to `DEFER` and request evidence.
- Conflict unresolved and no clear winning evidence: enqueue `ESCALATE_TO_PRO`.
- Duplicate decision IDs detected: merge deterministically and retain complete evidence union.
- Alias output mismatch: regenerate both outputs from a single in-memory table model.
- Oversized decision text reducing auditability: enforce concise row summaries and retain detail in evidence anchors.
- Multiple R-phase reports provide contradictory inputs to the synthesis: document both perspectives with evidence and flag with `status: unresolved_contradiction`.
- Synthesis output would exceed the declared output format constraints: emit a complete-but-summarized version and note truncated sections in `coverage_notes`.
