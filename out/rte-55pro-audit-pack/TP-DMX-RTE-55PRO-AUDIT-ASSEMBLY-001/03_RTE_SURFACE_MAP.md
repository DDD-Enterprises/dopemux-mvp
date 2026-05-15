# RTE Surface Map

## Active Runner Layer

- OBSERVED active v5 runner: `services/repo-truth-extractor/run_extraction_v5.py` with CLI `main()` at line 18758.
- OBSERVED v5 output constants imported from `services/repo-truth-extractor/rte_config.py`, including `V5_EXTRACTION_ROOT = extraction/repo-truth-extractor/v5` and `V5_RUNS_ROOT = extraction/repo-truth-extractor/v5/runs`.
- OBSERVED v5 contains doctor, provider preflight, prescan integration, routing, phase execution, comparison lanes, repair, coverage, proof-pack, dashboard, status loop, and batch paths.

## Compatibility And Legacy Layers

- OBSERVED v4 wrapper: `services/repo-truth-extractor/run_extraction_v4.py`; it references v4 promptset paths and delegates/syncs around v5/v3 compatibility behavior.
- OBSERVED v3 legacy/fallback runner: `services/repo-truth-extractor/run_extraction_v3.py`; proof says live execution is now gated by explicit consent.
- OBSERVED additional legacy wrapper: `services/repo-truth-extractor/run_extraction.py` exists and should be audited for current relevance.
- OBSERVED legacy scan wrapper: `services/repo-truth-extractor/run_repscan.py`; `dopemux rte scan` requires explicit `--allow-legacy-v3-scan`.

## Dopemux Command Wiring

- OBSERVED canonical operator group: `src/dopemux/cli.py:4859` defines `@click.group("rte")`.
- OBSERVED `upgrades` remains a legacy compatibility alias for `dopemux rte` at `src/dopemux/cli.py:3065-3068`.
- OBSERVED legacy `extractor` command is hidden and described as promptset/prescan cockpit support, not canonical execution, at `src/dopemux/cli.py:3071-3078`.
- OBSERVED runner path selection is in `src/dopemux/commands/extractor_commands.py:467`.

## Doctor, Preflight, Status, Coverage, Verification

- OBSERVED v5 doctor surface: `run_doctor_checks` at `run_extraction_v5.py:6105`.
- OBSERVED provider preflight/readiness functions in v5 include `collect_provider_routes`, `derive_route_readiness_summary`, `run_provider_preflight`, and launch-provider preflight guards.
- OBSERVED status and dashboard functions: `emit_run_dashboard_snapshot` at line 15397 and `run_status_loop` at line 15473.
- OBSERVED coverage/proof functions: `generate_coverage_report` at line 16368 and `update_proof_pack` at line 16621.
- OBSERVED pre-live validator: `services/repo-truth-extractor/validate_pre_live_gate_v25.py`.

## Prescan, Promptgen, Comparison, Resume, Batch

- OBSERVED integrated prescan entry in v5: `run_integrated_prescan_stage` at `run_extraction_v5.py:6514`.
- OBSERVED prescan engine: `services/repo-truth-extractor/lib/prescan/engine.py:38` and corpus walker: `lib/prescan/corpus_walker.py:47`.
- OBSERVED prompt generation helpers under `services/repo-truth-extractor/lib/promptgen/`.
- OBSERVED comparison lane functions in both `run_extraction_v5.py:11422` and `llm_runtime.py:1134`.
- OBSERVED batch clients under `lib/batch_clients.py` and batch retrieval under `lib/batch_retriever.py`.

## Tests

- OBSERVED tests live under `services/repo-truth-extractor/tests/` in this checkout.
- OBSERVED focused test themes include operator safety, promptset truth/linting, batch strict response format, strict passthrough attestations, prescan corpus/walker, v3 consent, run_repscan gating, phase contracts, and pre-live gate v25.

## Output Roots

- OBSERVED v5 root: `extraction/repo-truth-extractor/v5` from `rte_config.py`.
- OBSERVED older proof/audit reports reference historical output under `services/repo-truth-extractor/extraction/...`; treat those as historical unless current runtime verifies otherwise.

## Known Drift

- v5 is canonical, v4/v3 remain present.
- `dopemux rte scan` remains legacy-v3-backed with opt-in.
- Some prior audit upload recommendations reference `tests/unit/...`; current observed RTE tests are under `services/repo-truth-extractor/tests/`.
- Prompt authority spans v4 promptsets, generated promptsets, phase registries, prescan prompt constants, and v3 prompt archives.
