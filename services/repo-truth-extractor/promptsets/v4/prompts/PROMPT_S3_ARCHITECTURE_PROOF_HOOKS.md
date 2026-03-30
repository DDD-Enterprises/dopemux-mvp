# PROMPT_S3

## Goal
Produce phase `S3` proof-hook artifacts that transform architecture and migration claims into minimal verification guidance. This step must preserve evidence traceability and avoid implying that commands were executed.

## Inputs
- Source scope:
  - `extraction/**/S_synthesis/norm/**`
  - `extraction/**/R_arbitration/norm/**`
  - `extraction/**/T_task_packets/norm/**`
- Required artifacts:
  - `S0_ARCHITECTURE_SYNTHESIS_OPUS.md`
  - `S1_MCP_TO_HOOKS_MIGRATION_PLAN.md`
  - `S2_DECISION_DOSSIER.md`
  - `RISK_REGISTER_TOP20.md`
- Optional artifacts:
  - `TP_MERGED.json`
  - `FREEZE_MANIFEST.json`
- Constraint:
  - Hooks must be generated from supplied claim evidence only.

## Outputs
- `ARCHITECTURE_PROOF_HOOKS.md`
- `S3_ARCH_PROOF_HOOKS.md`

## Schema
- Artifact kind: markdown tables for claim-to-proof mapping.
- Canonical writer: `S3` for both outputs.
- Required table fields:
  - `claim_id`
  - `claim_statement`
  - `evidence`
  - `verification_command_suggestion`
  - `expected_signal`
  - `risk_link`
  - `confidence`
- Required sections:
  - Full claim-to-proof table
  - Priority proof set
  - Unknown hooks register
- Alias requirement:
  - `ARCHITECTURE_PROOF_HOOKS.md` and `S3_ARCH_PROOF_HOOKS.md` must remain semantically aligned.

## Extraction Procedure
1. Load all required upstream artifacts as specified in the inputs section. Produce architecture proof hooks by identifying verification points where automated checks can validate architectural invariants. Map each proof hook to the architectural claim it validates, the enforcement mechanism, and the evidence source.
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
