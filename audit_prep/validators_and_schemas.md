# Validators and Schemas

## Core runtime contract authority

- `services/repo-truth-extractor/promptsets/v4/promptset.yaml` is the canonical step inventory and required section contract for the active runtime prompt stack.
- Required prompt sections declared there: `Goal`, `Inputs`, `Outputs`, `Schema`, `Extraction Procedure`, `Evidence Rules`, `Determinism Rules`, `Anti-Fabrication Rules`, `Failure Modes`.
- `services/repo-truth-extractor/promptsets/v4/artifacts.yaml` is the artifact-level contract: canonical writer step, merge strategy, `norm_artifact`, allowed empty arrays, and required fields such as `id`, `path`, and `line_range`.
- `services/repo-truth-extractor/promptsets/v4/model_map.yaml` is the route/repair/sidefill contract: lane class, strict-schema requirement, primary routes, repair routes, and sidefill routes.

## Contract compiler and validator surfaces

- `lib/phase_contract_map.py` compiles `PHASE_CONTRACT_MAP_V2` from the promptset, artifacts, model map, and prompt-declared schema sections.
- `lib/structured_output_contracts.py` normalizes payload envelopes, normalizes schema aliases, and rejects missing schema IDs, missing required keys, empty contract-critical fields, and invalid line ranges.
- `run_extraction_v5.py` enforces promptset preflight, phase-output verification, and a pre-live validator gate before live execution.

## Model-map summary

- Total model-mapped steps: 130
- Strict-schema-primary steps: 51
- Non-strict-primary steps: 79
- Lane classes: `AGG`=14, `BULK_CODE_HEAVY`=6, `BULK_DOCS_GENERAL`=73, `CE`=37
- Dominant provider references across map: `xai`=266, `openrouter`=204, `gemini`=61
- Dominant model references across map: `openai/gpt-5.4`=153, `grok-4.20-beta-0309-non-reasoning`=139, `grok-4.20-beta-0309-reasoning`=121, `openai/gpt-5.3-codex`=44, `gemini-3-flash-preview`=43, `gemini-3.1-pro-preview`=18

## Prescan contracts

- Embedded system prompts live in `lib/prescan/grok_passes.py` under `dedup`, `discover`, `feasibility`, and `optimize`.
- `BatchResponseValidator` only enforces required top-level keys per pass and basic JSON decoding; it is materially weaker than the main runtime contract layer.
- `lib/prescan/schemas.py` defines `PRESCAN_INTELLIGENCE_SCHEMA`, which governs the emitted `prescan_intelligence.json` structure.
- `lib/prescan/provider_catalog.py` builds a provider/model catalog from the runner authority and selects routes by required prescan tier.
- Current pass defaults in `grok_passes.py`: `dedup`, `discover`, and `feasibility` default to `openai:gpt-5-nano`; `optimize` uses the configured provider/model.

## Phase S / FL_INT / S_INT schema posture

- `prompts/phase_s/registry.json` defines step order and tier for `S0`-`S12`, but there are no adjacent JSON schema files in that directory. Output-contract rigor for `S` is therefore weaker than FL_INT and should be treated as partially explicit.
- `prompts/phase_fl_int/registry.json` defines prompt path, schema path, outputs, ladder, routing tier, max hops, and dependencies for `F0`-`L4`. Each FL_INT step has an adjacent JSON schema file under `prompts/phase_fl_int/schemas/`.
- `s_int/run_s_int.py` is adjacent rather than primary scope, but it is actively schema-validated and relevant to the broader model-surface discussion. `S16`-`S20` use explicit schemas and ladders from `s_int/models.py`.

## Failure criteria and malformed-output handling

- Runtime fail-closed conditions include missing `schema`, schema ID mismatch, missing contract-required fields, empty critical keys, invalid `line_range`, promptset preflight failures, and pre-live validator blocks.
- Prescan malformed output handling is salvage-oriented: JSON parse fallback by substring extraction plus pass-level required-key checks.
- FL_INT and S_INT normalize envelopes and validate against per-step schemas; invalid payloads raise immediately in their runners.
