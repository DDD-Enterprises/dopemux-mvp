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

## Evidence Rules
- Each hook row must include evidence anchors for the source claim.
- Verification suggestions must cite the claim evidence they validate.
- Risk links must reference `R8` anchors when available.
- Missing evidence must force `UNKNOWN` confidence and explicit gap notes.
- Structured evidence snippets must include `path`, `line_range`, and `excerpt` when present.
- No hook may cite artifacts outside supplied inputs.
- No claim can be marked high confidence without direct evidence support.

## Determinism Rules
- Do not emit runtime identity fields such as `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Use fixed column order and deterministic row sorting by `claim_id`.
- Normalize confidence tokens to `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`.
- Keep suggestion wording concise and stable across runs.
- Keep both output files semantically identical for compatibility.
- Avoid narrative digressions that can reorder content non-deterministically.

## Anti-Fabrication Rules
- Do not invent commands, expected signals, or claim IDs absent from evidence.
- Do not claim hooks were executed or verified.
- Do not infer infrastructure surfaces not represented in S0/S1/S2.
- Do not hide uncertainty behind broad confidence labels.
- Do not emit risk mappings without explicit anchors.
- Do not merge unrelated claims into a single hook entry.

## Failure Modes
- Claims cannot be mapped to verification suggestions: retain in unknown hooks register.
- Missing decision dossier input: degrade to partial hooks with explicit scope warning.
- Risk linkage absent: keep hook but mark risk link `UNKNOWN` with required evidence list.
- Duplicate claim IDs: merge evidence deterministically and preserve strongest expected signal text.
- Alias output mismatch: regenerate both outputs from one normalized hook table.
- Overly broad command suggestions: reduce to minimal bounded checks and note limitations.
- Multiple R-phase reports provide contradictory inputs to the synthesis: document both perspectives with evidence and flag with `status: unresolved_contradiction`.
- Synthesis output would exceed the declared output format constraints: emit a complete-but-summarized version and note truncated sections in `coverage_notes`.
