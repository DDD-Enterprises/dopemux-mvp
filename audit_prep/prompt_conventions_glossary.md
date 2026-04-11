# Prompt Conventions Glossary

## Naming patterns
- `PROMPT_<PHASE><STEP>_...` is the dominant step naming convention in both `promptsets/v4/prompts` and `prompts/v3`.
- `A/H/D/C/E/W/B/G/X/Q/R/T/Z` are runtime phases in `run_extraction_v5.py`.
- `S` is runtime-active but registry-driven from `prompts/phase_s`.
- `F*` and `L*` are FL_INT step IDs from `prompts/phase_fl_int/registry.json`.
- `MANUAL_PRO_*` files are contract-policy references rather than first-pass extraction prompts.

## Terms

- `runtime authority`: The code path that actually executes in current repo truth. Here that is `run_extraction_v5.py` for the main extractor runtime.
- `contract authority`: The files that define the active step inventory, output contracts, and model routing. Here that is primarily `promptsets/v4/` despite the runtime being v5.
- `active supporting surface`: A model-using or prompt-defining surface outside the main promptset tree that still materially affects current behavior. Examples: prescan embedded prompts, `phase_s`, `phase_fl_int`.
- `legacy reference`: Older prompt material kept only for lineage or migration analysis; not treated as active unless invocation is proven.
- `prescan`: A separate pre-extraction intelligence pipeline run via `run_prescan.py`; mostly code/schema-driven, with four embedded system prompts in `grok_passes.py`.
- `phase S`: Registry-driven synthesis phase (`S0`-`S12`) executed by the v5 runtime but sourced from `prompts/phase_s` rather than `promptsets/v4`.
- `FL_INT`: Separate synthesis runner for design and feature ledgers, defined by `prompts/phase_fl_int/registry.json` and per-step schemas.
- `S_INT`: Adjacent schema-validated synthesis runner for `S16`-`S20`; not primary Prompt 3 scope but relevant as a neighboring model surface.
- `strict schema`: A step posture in `model_map.yaml` where the primary route is expected to satisfy a strict JSON-schema contract.
- `sidefill`: Supplemental route path declared in `model_map.yaml` for filling missing information when the primary pass is insufficient.
- `repair route`: A secondary route declared in `model_map.yaml` or dedicated repair phase `Q` to recover from malformed or incomplete outputs.
- `merge / QA step`: A prompt step that consolidates prior artifacts and checks drift, completeness, or collisions rather than extracting raw facts from source material.
- `OpenClaw suitability`: Whether a step looks safe for an agent-loop execution model versus requiring a deterministic, tightly schema-bound single completion path.
