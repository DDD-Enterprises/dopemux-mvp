You are running a Prompt 3 pipeline audit for the Repo Truth Extractor inside the Dopemux repository.

Use the files in `audit_prep/` exactly as follows:

- `prompt_inventory_manifest.md` = authoritative discovered-prompt inventory
- `pipeline_phase_map.md` = authoritative phase/step map for runtime v5 + prescan
- `validators_and_schemas.md` = authoritative validator/schema contract source
- `prompt_conventions_glossary.md` = terminology and classification guide
- `prompts_active_prescan_bundle.md` = active prescan prompt text
- `prompts_active_extraction_bundle_1.md` and `prompts_active_extraction_bundle_2.md` = active extraction prompt text
- `prompts_active_repair_retry_bundle.md` = active repair/retry prompt text
- `prompts_active_adjudication_bundle.md` = active adjudication/judging prompt text
- `prompts_active_output_shaping_bundle.md` = active output-shaping prompt text
- `prompts_runtime_v5_contract_v4_bundle.md` = material included specifically to preserve the runtime-v5 / contract-v4 authority split
- `prompts_legacy_v3_v4_reference_bundle.md` = legacy reference material only unless current code path requires it
- `prompt1_handoff_pack_normalized.md` = current-state model/route authority artifact
- `prompt2_final_audit.md` = final corrected model/research audit
- `report_a_inventory_audit.md`, `report_b_portfolio_brain.md`, `report_c_openrouter_extension.md` = historical research hypotheses only

Execution constraints:

- Primary scope is runtime v5 + prescan.
- Prompt and contract authority may still live under `promptsets/v4`.
- Legacy v4/v3 prompts are secondary and should only be analyzed deeply if still invoked, still authoritative for contract behavior, or still causing migration debt.
- Do not redo Prompt 1 or Prompt 2.
- Do not rebuild the model inventory.
- Do not broaden scope to unrelated Dopemux prompts.
- Do not invent missing validator/schema details.
- Preserve uncertainty and current-state authority boundaries.
- Prefer structured tables and explicit labels over narrative prose.
- If a prompt appears runtime-active but contract-authoritative text lives elsewhere, preserve that split rather than normalizing it away.
