# Pipeline Phase Map

## Discovery pass
- Active runtime entrypoint: `services/repo-truth-extractor/run_extraction_v5.py`
- Active prompt contract source: `services/repo-truth-extractor/promptsets/v4/`
- Prescan entrypoint: `services/repo-truth-extractor/run_prescan.py` with embedded model-facing prompts in `lib/prescan/grok_passes.py`
- Active model-using surfaces outside the core promptset tree: `prompts/phase_s`, `prompts/phase_fl_int`, `lib/prescan/grok_passes.py`, `lib/prescan/provider_catalog.py`
- Legacy prompt trees not currently proven active: `services/repo-truth-extractor/prompts/v3`, `services/repo-truth-extractor/archive/legacy_prompts`
- Runtime / contract mismatch: the v5 runner executes prompt/contract authority that is still rooted in `promptsets/v4`.

## Runtime phase order

| Order | Phase | Prompt source | Prompt count | Required by promptset | Notes |
|---|---|---|---:|---|---|
| 1 | A | `promptsets/v4` | 15 | `A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A99` | first-live initial set |
| 2 | H | `promptsets/v4` | 9 | `H0, H1, H2, H3, H4, H5, H6, H7, H9` | first-live initial set |
| 3 | D | `promptsets/v4` | 6 | `D0, D1, D2, D3, D4, D5` | first-live initial set |
| 4 | C | `promptsets/v4` | 18 | `C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17` | first-live initial set |
| 5 | E | `promptsets/v4` | 8 | `E0, E1, E2, E3, E4, E5, E6, E9` | runtime phase |
| 6 | W | `promptsets/v4` | 7 | `W0, W1, W2, W3, W4, W5, W9` | runtime phase |
| 7 | B | `promptsets/v4` | 5 | `B0, B1, B2, B3, B9` | runtime phase |
| 8 | G | `promptsets/v4` | 7 | `G0, G1, G2, G3, G4, G5, G9` | runtime phase |
| 9 | X | `promptsets/v4` | 6 | `X0, X1, X2, X3, X4, X9` | first-live post-review set |
| 10 | Q | `promptsets/v4` | 6 | `Q0, Q1, Q2, Q3, Q9, Q11` | runtime phase |
| 11 | R | `promptsets/v4` | 12 | `R0, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11` | first-live post-review set; requires A/H/D/C; optional B/E/G/W/Q/X inputs |
| 12 | T | `promptsets/v4` | 7 | `T0, T1, T2, T3, T4, T5, T9` | first-live post-review set |
| 13 | Z | `promptsets/v4` | 4 | `Z0, Z1, Z2, Z9` | first-live post-review set |
| 14 | S | `prompts/phase_s registry` | 13 | `S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12` | first-live post-review set; registry-driven outside promptsets/v4; optional deps X/T/Z/MANUAL |

## Non-PHASES model-using surfaces

| Surface | Entrypoint | Prompt source | Dependencies | Notes |
|---|---|---|---|---|
| Prescan | `run_prescan.py` | embedded prompts in `lib/prescan/grok_passes.py` | emits intelligence and provider catalog used to guide runtime routing | separate pre-extraction pipeline; code/schema-driven with four embedded passes |
| FL_INT | `fl_int/run_fl_int.py` | `prompts/phase_fl_int/registry.json` | consumes D/C/R/X outputs and prior FL_INT steps | separate synthesis runner with explicit ladders and JSON schemas |
| S_INT | `s_int/run_s_int.py` | `prompts/phase_s_int` | adjacent to S family; JSON-schema validated | not primary Prompt 3 scope, but active neighboring model surface |

## Retry, repair, and validation touchpoints

- `Q` is the explicit runtime repair / QA bundle in the active promptset.
- `lib/structured_output_contracts.py` enforces schema IDs, required keys, item-level required fields, and alias normalization.
- `lib/phase_contract_map.py` compiles the contract map from `promptset.yaml`, `artifacts.yaml`, `model_map.yaml`, and prompt-declared schema sections.
- `run_extraction_v5.py` gates live runs via promptset preflight and the pre-live validator before execution.
- Prescan validates top-level JSON shape through `BatchResponseValidator` and emits `prescan_intelligence.json` governed by `lib/prescan/schemas.py`; it is looser than the main runtime contract system.
- FL_INT and S_INT both use explicit per-step JSON schema files and fail-closed validation in their dedicated runners.
