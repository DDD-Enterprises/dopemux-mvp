# Promptset Inventory

## Active Or High-Relevance Prompt Surfaces

| Path | Apparent Purpose | Role in v5/v4/v3 | Gating/Validation Connection | Risk Notes |
| --- | --- | --- | --- | --- |
| `services/repo-truth-extractor/promptsets/v4/promptset.yaml` | v4 promptset manifest | OBSERVED v4 compatibility prompt contract; v5 imports promptset truth surfaces | Promptset audit/lint and v4 wrapper | Authority may be shared with generated promptsets and phase registries; audit exact loading path. |
| `services/repo-truth-extractor/promptsets/v4/model_map.yaml` | promptset model map | OBSERVED in v4 promptset tree | Potential routing/prompt contract input | Do not infer live provider behavior without runtime route resolution. |
| `services/repo-truth-extractor/promptsets/v4/prompts/` | v4 phase prompts | OBSERVED active prompt bundle | Promptset lint/tests | Audit hallucination controls, citation requirements, repair instructions, and output schema alignment. |
| `services/repo-truth-extractor/promptsets/v4/schemas/` | v4 output schemas | OBSERVED prompt contract schemas | Structured-output validation connection | Need compare with `lib/structured_output_contracts.py` and phase contract map. |
| `services/repo-truth-extractor/promptsets/generated/dopemux-mvp-2e346e2084bc/` | generated promptset package | OBSERVED generated promptset tree | UNKNOWN current load precedence | Generated content is not automatically source authority. |
| `services/repo-truth-extractor/prompts/phase_s/registry.json` | SP/Phase S registry | OBSERVED registry-backed Phase S/SP surface | Phase S warning in prior audit | Prior audit warned Phase S legacy usage; closure not found. |
| `services/repo-truth-extractor/prompts/phase_s_int/registry.json` | integrated Phase S prompts | OBSERVED registry and schemas | UNKNOWN current runtime use | Needs audit against `run_phase_S` and `run_phase_SP`. |
| `services/repo-truth-extractor/prompts/phase_fl_int/registry.json` | feature/design ledger integrated prompts | OBSERVED registry and schemas | UNKNOWN current runtime use | Audit schema and prompt contract drift. |
| `services/repo-truth-extractor/prompts/prescan/registry.json` | prescan metadata registry | OBSERVED registry | Prior pre-live report says prompt text lives in Python constants | Risk: registry may be governance metadata, not canonical prompt text. |
| `services/repo-truth-extractor/lib/prescan/grok_passes.py` | prescan pass prompt constants | OBSERVED by prior report as source of prescan prompt text | Prior lint mismatch around finding constants | Audit current tests before trusting historical mismatch. |
| `services/repo-truth-extractor/prompts/v3/` | legacy v3 prompt archive | OBSERVED large v3 prompt tree | Legacy v3 execution gated by proof #605 | Risk if v3 prompts can still influence current outputs through opt-in paths. |
| `services/repo-truth-extractor/lib/promptgen/` | prompt generation helpers | OBSERVED helper package | UNKNOWN exact current generation role | Audit deterministic generation and source authority. |

## Required Prompt Audit Questions

- OBSERVED: prompt authority is not single-file. GPT-5.5 Pro should trace actual loader code before ranking prompt sources.
- UNKNOWN: whether every v5 phase consumes v4 promptset, generated promptset, phase registry, or embedded/legacy prompt material.
- RISK: repair and sidefill prompts can blur OBSERVED facts with inferred/generated content if schemas and provenance are weak.
- RISK: model-routing names in prompt/config files are not proof that providers support current structured output semantics.
