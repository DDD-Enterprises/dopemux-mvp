# Prompt 3 Audit Workflow for RTE Runtime v5 / Contract v4

## Summary

Run the workflow in three Codex threads or worktrees:

1. `pack-builder`
2. `prompt-refactor`
3. `audit-runner`

Keep the **repo root** as the Codex project so the builder can inspect supporting surfaces outside the extractor subtree.

Carry these distinctions explicitly through every artifact:

- **runtime version**: active runner is v5
- **contract authority version**: active prompt and contract authority may still be rooted in `promptsets/v4`
- **legacy version**: v4 and v3 materials that are no longer authoritative unless still invoked or still causing migration debt

Do not use filenames or headings that imply the active prompt text is “v5-authored” when repo truth says contract authority still comes from `promptsets/v4`.

---

## Implementation Changes

### 1. Pack builder thread

Create `audit_prep/` and begin with a required **repo-truth discovery pass**.

Before any bundling, write a short discovery section in `README_prompt3_pack.md` that identifies:

- active runtime entrypoint(s)
- active prompt contract source(s)
- prescanner source(s)
- active model-using surfaces outside the core promptset tree
- legacy prompt trees not currently invoked
- any runtime/contract version mismatches

Then build these pack files:

- `prompt_inventory_manifest.md`
- `pipeline_phase_map.md`
- `validators_and_schemas.md`
- `prompt_conventions_glossary.md`
- `README_prompt3_pack.md`

Use authority-safe bundle names:

- `prompts_active_prescan_bundle.md`
- `prompts_active_extraction_bundle_1.md`
- `prompts_active_extraction_bundle_2.md`
- `prompts_active_repair_retry_bundle.md`
- `prompts_active_adjudication_bundle.md`
- `prompts_active_output_shaping_bundle.md`
- `prompts_runtime_v5_contract_v4_bundle.md`
- `prompts_legacy_v3_v4_reference_bundle.md`

### Bundle naming rule

- `active_*` means currently relevant to the runtime path
- `runtime_v5_contract_v4_*` is used where the file is included specifically to preserve the runtime/contract authority split
- `legacy_*` is for reference-only material

Copy into `audit_prep/` if present:

- `prompt1_handoff_pack_normalized.md`
- `prompt2_final_audit.md`
- `report_a_inventory_audit.md`
- `report_b_portfolio_brain.md`
- `report_c_openrouter_extension.md`

If absent, list them under **Missing artifacts** in `README_prompt3_pack.md`.

### Manifest requirements

Use the expanded inventory schema already planned.

Add `authority_role` with allowed values:

- `runtime_authority`
- `contract_authority`
- `active_supporting_surface`
- `legacy_reference`
- `migration_debt_only`
- `unknown`

Classify each prompt or surface with both `status` and `authority_role`.

Preserve exact version-line separation.

Do not merge similarly named prompts across versions.

If prompt IDs are absent, derive stable IDs and state that in notes.

### Pack content rules

- preserve exact prompt text in bundles
- prepend deterministic metadata wrappers
- mark missing metadata as `UNKNOWN`
- include prescanner, `phase_s`, and `phase_fl_int` if they are active model-using surfaces even when they are not under the main promptset tree
- include legacy prompts only when they are still invoked, explain migration debt, or clarify duplicate/conflicting active behavior

---

### 2. Prompt refactor thread

Create:

- `audit_prep/prompt3_refactored.md`
- `audit_prep/prompt3_runner_wrapper.md`

Use the user-provided Prompt 3 text as the baseline, but update file references to match the final authority-safe bundle names from the pack-builder.

#### Required preservation

- primary scope is runtime v5 plus prescanner
- prompt and contract authority may live under `promptsets/v4`
- legacy v4 and v3 get secondary treatment only
- audit is framed as pipeline and workload decomposition, not generic prompt review
- output sections, labels, and rigor rules remain intact
- explicit distinctions remain:
  - prompt defect
  - model mismatch
  - route mismatch
  - validator weakness
  - missing decomposition

Also create:

- `audit_prep/supervisor_llm_update_blurb.md`

That blurb should tell the supervisor LLM to:

- preserve the runtime-v5 / contract-v4 distinction
- include all model-using surfaces for prescan, `S`, and `FL_INT`
- weight active contract authority above legacy prompt archaeology
- keep validator/schema uncertainty explicit
- force step/archetype-level routing, escalation, and benchmark outputs

---

### 3. Audit runner thread

Run the audit using:

- `audit_prep/prompt3_refactored.md`
- `audit_prep/prompt3_runner_wrapper.md`
- all supporting files in `audit_prep/`

Write:

- `audit_prep/prompt3_pipeline_audit.md`

#### Runner rules

- do not redo Prompt 1 or Prompt 2
- do not rebuild the model inventory
- do not broaden to unrelated Dopemux prompt surfaces
- do not invent missing validator/schema details
- if the manifest or phase map shows a v4 or v3 prompt is not currently invoked and does not explain active migration debt, mention it briefly in the legacy table and move on
- prefer tables and explicit labels over prose
- keep the output directly usable for Prompt 3.5 and Prompt 4

---

## Test Plan

Validate each stage narrowly before moving on.

### Pack-builder validation

- every manifest `source_path` exists
- every manifest `authority_role` is populated from the allowed set
- bundle contents reconcile with manifest counts
- bundle filenames and README terminology do not falsely imply v5-authored contract authority
- README includes discovery findings, scope roots, counts, assumptions, ambiguities, missing artifacts, and runtime/contract mismatch notes

### Prompt-refactor validation

- both files exist
- all file references match actual `audit_prep/` filenames
- no required Prompt 3 sections or labels were dropped
- wrapper and prompt both preserve the runtime-v5 / contract-v4 distinction

### Audit-runner validation

- `prompt3_pipeline_audit.md` exists
- it contains all required sections in order
- legacy analysis remains bounded
- it includes step/archetype-level findings for capability floors, route sensitivity, OpenClaw suitability, escalation triggers, and benchmark input sets

---

## Assumptions

- `services/repo-truth-extractor/run_extraction_v5.py` remains the active runtime authority.
- `services/repo-truth-extractor/promptsets/v4/` remains the active contract authority unless deeper discovery proves otherwise.
- Prescanner may be code/schema-driven more than prompt-driven. If so, include its authoritative model-using and contract surfaces in the pack instead of forcing fake prompt bundles.
- `phase_s` and `phase_fl_int` are active model-using prompt families and must be included if current code, tests, or registries show they still matter.
- Missing named handoff or report artifacts should be recorded as missing, not recreated or inferred.
