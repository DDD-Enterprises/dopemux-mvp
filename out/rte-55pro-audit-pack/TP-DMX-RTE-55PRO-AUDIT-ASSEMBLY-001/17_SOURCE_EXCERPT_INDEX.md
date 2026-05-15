# Source Excerpt Index

This index identifies selected excerpts to request or inspect during GPT-5.5 Pro passes. It does not paste source dumps.

| Path | Line Range | Symbols | Reason Selected | Audit Axis |
| --- | --- | --- | --- | --- |
| `services/repo-truth-extractor/run_extraction_v5.py` | 497-502 | routing/model constants | Baseline routing policy and model defaults. | model routing |
| `services/repo-truth-extractor/run_extraction_v5.py` | 1321-1450 | `RunnerConfig`, output layout fields | Runtime knobs and output-root controls. | architecture, determinism |
| `services/repo-truth-extractor/run_extraction_v5.py` | 4750-4805 | `choose_model_for_step`, `resolve_effective_step_route` | Step route resolution. | model routing |
| `services/repo-truth-extractor/run_extraction_v5.py` | 6105-6514 | doctor/preflight/prescan setup | Operator readiness and prescan entry. | UX, prescan |
| `services/repo-truth-extractor/run_extraction_v5.py` | 9197-10400 | LLM ladder, repair, escalation | Provider call, repair, and escalation logic. | repair, safety |
| `services/repo-truth-extractor/run_extraction_v5.py` | 11422-11550 | `run_comparison_lane` | Multi-model comparison. | model routing |
| `services/repo-truth-extractor/run_extraction_v5.py` | 15270-16680 | verify, dashboard, status, coverage, proof | Operator-visible outputs and proof. | proof, UX |
| `services/repo-truth-extractor/run_extraction_v5.py` | 17507-18560 | `run_phase_*` | Phase map and phase-specific routing. | architecture |
| `services/repo-truth-extractor/rte_config.py` | 29-132 | artifact filenames and v5 roots | Proof filenames and output roots. | proof, determinism |
| `services/repo-truth-extractor/llm_runtime.py` | 716-1180 | `call_llm_with_ladder`, comparison lane helpers | Runtime LLM wrapper behavior. | provider routing, repair |
| `services/repo-truth-extractor/lib/structured_output_contracts.py` | 543-700 | `build_provider_structured_output` | Provider response-format contract. | structured output |
| `services/repo-truth-extractor/lib/prescan/engine.py` | 38-180 | `PrescanEngine` | Prescan orchestration. | prescan |
| `services/repo-truth-extractor/lib/prescan/corpus_walker.py` | 47-220 | `CorpusWalker` | Source inclusion/exclusion and hashes. | source hygiene, security |
| `services/repo-truth-extractor/lib/prescan/provider_catalog.py` | full focused excerpt | provider catalog/routing plan | Prescan route readiness and external provider assumptions. | routing, UX |
| `src/dopemux/cli.py` | 3065-3078 | legacy alias setup | Command-family confusion. | UX |
| `src/dopemux/cli.py` | 4859-5538 | `rte` group and attached commands | Canonical operator surface. | UX, architecture |
| `src/dopemux/commands/extractor_commands.py` | 467-523 | `_extractor_runner_path`, runner invocation | Pipeline version guarding. | safety |
| `services/repo-truth-extractor/validate_pre_live_gate_v25.py` | focused by validator entrypoints | pre-live gate checks | Launch readiness gate. | validation |
| `services/repo-truth-extractor/promptsets/v4/promptset.yaml` | full small manifest | promptset contract | Prompt authority and phase/step outputs. | prompts |
| `services/repo-truth-extractor/prompts/phase_s/registry.json` | full registry | SP/Phase S prompt registry | Phase S warning crosscheck. | prompts |
