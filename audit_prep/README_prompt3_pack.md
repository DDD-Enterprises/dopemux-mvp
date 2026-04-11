# Prompt 3 Input Pack

## Discovery findings

- Active runtime entrypoint(s): `services/repo-truth-extractor/run_extraction_v5.py`, with prescan preflight in `services/repo-truth-extractor/run_prescan.py`.
- Active prompt contract source(s): `services/repo-truth-extractor/promptsets/v4/promptset.yaml`, `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`, and `services/repo-truth-extractor/promptsets/v4/model_map.yaml`.
- Prescanner source(s): `services/repo-truth-extractor/run_prescan.py`, `services/repo-truth-extractor/lib/prescan/`, and embedded system prompts in `services/repo-truth-extractor/lib/prescan/grok_passes.py`.
- Active model-using surfaces outside the core promptset tree: `services/repo-truth-extractor/prompts/phase_s`, `services/repo-truth-extractor/prompts/phase_fl_int`, and adjacent `services/repo-truth-extractor/s_int`.
- Legacy prompt trees not currently invoked: `services/repo-truth-extractor/prompts/v3`, `services/repo-truth-extractor/archive/legacy_prompts`.
- Runtime / contract mismatch: current runtime is v5, but current prompt contract authority remains rooted in `promptsets/v4`.

## Scope roots
- v5 runtime: `services/repo-truth-extractor/run_extraction_v5.py`
- prescan: `services/repo-truth-extractor/run_prescan.py` and `services/repo-truth-extractor/lib/prescan`
- contract v4: `services/repo-truth-extractor/promptsets/v4`
- phase S: `services/repo-truth-extractor/prompts/phase_s`
- FL_INT: `services/repo-truth-extractor/prompts/phase_fl_int`
- legacy v3: `services/repo-truth-extractor/prompts/v3`

## Files included
- `prompt_inventory_manifest.md`
- `pipeline_phase_map.md`
- `validators_and_schemas.md`
- `prompt_conventions_glossary.md`
- `prompts_active_prescan_bundle.md`
- `prompts_active_extraction_bundle_1.md`
- `prompts_active_extraction_bundle_2.md`
- `prompts_active_repair_retry_bundle.md`
- `prompts_active_adjudication_bundle.md`
- `prompts_active_output_shaping_bundle.md`
- `prompts_runtime_v5_contract_v4_bundle.md`
- `prompts_legacy_v3_v4_reference_bundle.md`
- `prompt3_refactored.md`
- `prompt3_runner_wrapper.md`
- `prompt3_pipeline_audit.md`
- `supervisor_llm_update_blurb.md`
- `README_prompt3_pack.md`
- `prompt1_handoff_pack_normalized.md` copied from `prompt1_handoff_pack_normalized.md`
- `prompt2_final_audit.md` copied from `prompt2_final_audit.md`
- `report_a_inventory_audit.md` copied from `report_a_inventory_audit.md`
- `report_b_portfolio_brain.md` copied from `report_b_portfolio_brain.md`
- `report_c_openrouter_extension.md` copied from `report_c_openrouter_extension.md`

## Prompt and surface counts
- total manifest rows: 252
- active rows: 139
- legacy rows: 113
- prescan embedded prompts: 4
- promptset/v4 runtime prompts: 110
- phase S prompts: 13
- FL_INT prompts: 8
- contract-authority policy docs: 4
- legacy v3 bundle rows: 113

## Assumptions
- Prescan should be represented through embedded prompt constants and contract surfaces rather than fabricated standalone Markdown prompt files.
- `phase_s` and `phase_fl_int` are in scope because they are active model-using prompt families even though they are outside `promptsets/v4`.
- `services/repo-truth-extractor/archive/legacy_prompts` was not bundled to avoid dead-prompt archaeology; it remains a known legacy tree.

## Known ambiguities
- `run_extraction_v5.py:get_phase_prompts()` labels many active promptset/v4 prompts with `source="legacy"`; the pack treats them as active contract authority because the runtime still loads them.
- `phase_s` has an active registry and outputs, but no adjacent JSON schema directory like FL_INT or S_INT; its contract rigor is therefore only partially explicit.
- FL_INT is an active model-using surface but not part of the main `PHASES` runtime sequence; it is included as supporting scope for model-fit analysis.

## Missing artifacts

## Recommended next step
Run `prompt3_refactored.md` with `prompt3_runner_wrapper.md` over this pack and write `prompt3_pipeline_audit.md`.
