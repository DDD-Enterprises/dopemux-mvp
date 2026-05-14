# RTE Runtime Pointers

This is a pointer index, not a source dump. Line numbers are OBSERVED in HEAD `a4214ca5bf431e1b59791661e2b664a6cd24c1da`.

| Axis | Pointer | Why It Matters |
| --- | --- | --- |
| v5 entrypoint | `services/repo-truth-extractor/run_extraction_v5.py:18758` `main()` | Current direct runner CLI surface. |
| routing policy | `run_extraction_v5.py:497` `ROUTING_POLICY_VERSION`, line 498 `DEFAULT_ROUTING_POLICY` | Routing identity and default policy. |
| model defaults | `run_extraction_v5.py:499-502` `DEFAULT_GEMINI_MODELS` | Model inventory baseline; do not infer provider behavior from names alone. |
| config object | `run_extraction_v5.py:1321` `RunnerConfig` | Run-time knobs including escalation, batch, comparison, and output layout. |
| model selection | `run_extraction_v5.py:4750` `choose_model_for_step`, `:4765` `resolve_effective_step_route` | Step route resolution and override boundary. |
| doctor | `run_extraction_v5.py:6105` `run_doctor_checks` | Operator readiness and diagnosis path. |
| prescan | `run_extraction_v5.py:6514` `run_integrated_prescan_stage` | Integrated prescan stage and receipt path. |
| live LLM ladder | `run_extraction_v5.py:9197` and `llm_runtime.py:716` `call_llm_with_ladder` | Escalation/fallback/repair behavior. |
| JSON repair | `run_extraction_v5.py:9656` `try_repair_json_truncation` | Structured-output repair path. |
| escalation gate | `run_extraction_v5.py:10335` `should_escalate_for_failure_type` | Failure class escalation decision. |
| comparison lane | `run_extraction_v5.py:11422`; `llm_runtime.py:1134` | Multi-model comparison behavior. |
| verification | `run_extraction_v5.py:15270` `verify_phase_output` | Phase output validation. |
| dashboard/status | `run_extraction_v5.py:15397` `emit_run_dashboard_snapshot`, `:15473` `run_status_loop` | Operator monitoring outputs. |
| coverage/proof | `run_extraction_v5.py:16368` `generate_coverage_report`, `:16621` `update_proof_pack` | Proof and coverage emission. |
| phases | `run_extraction_v5.py:17507-18560` `run_phase_*` | Phase execution map. |
| proof filenames | `services/repo-truth-extractor/rte_config.py:29-132` | Canonical artifact filenames and roots. |
| structured outputs | `services/repo-truth-extractor/lib/structured_output_contracts.py:543` `build_provider_structured_output` | Provider response-format contract handling. |
| prescan engine | `services/repo-truth-extractor/lib/prescan/engine.py:38` `PrescanEngine` | Corpus, duplicate, enrichment, cost, and routing-plan orchestration. |
| corpus walker | `services/repo-truth-extractor/lib/prescan/corpus_walker.py:47` `CorpusWalker` | Source inclusion/exclusion and hash inventory. |
| CLI canonical group | `src/dopemux/cli.py:4859` `@click.group("rte")` | Canonical operator command group. |
| CLI legacy aliases | `src/dopemux/cli.py:3065-3078` | `upgrades` alias and hidden `extractor` surface. |
| legacy scan opt-in | `src/dopemux/cli.py:4884-4929`; `run_repscan.py:74-75` | v3 scan remains available only with explicit opt-in. |
| runner selection | `src/dopemux/commands/extractor_commands.py:467` `_extractor_runner_path` | Pipeline version guard boundary. |
