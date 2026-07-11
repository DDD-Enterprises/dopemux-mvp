# A1 — RTE Monolith Architecture Map (run_extraction_v5.py)

**Program**: RTE-TRUTH · **Pass**: A1 (architecture audit)
**Target**: `services/repo-truth-extractor/run_extraction_v5.py` @ HEAD `542c17bb4` (24,286 lines)
**Date**: 2026-07-11 · **Mode**: READ-ONLY audit; this file is the only artifact.
**Evidence labels**: OBSERVED = read directly from source this session · INFERRED = derived from observed structure · UNKNOWN = not verified.
**Line numbers are secondary to symbol names — they WILL drift. Always re-grep the symbol before cutting.**

---

## 1. Module Map — major functional regions

All OBSERVED unless noted. Ranges are approximate (± a few lines).

| Region | Symbols (anchor first) | ~Lines |
|---|---|---|
| **Imports + dynamic-import shims** | `RUNNER_SERVICE_DIR` (:42); imports from `rte_ops_surfaces` (:89–101), `rte_phase_wrappers` (:102–111 — `plan_home_phase`, `plan_q_phase`, `plan_r_phase`, `plan_repo_scan_phase`, `plan_s_phase`, `plan_sp_phase`, `plan_t_phase`, `plan_x_phase`), `rte_promptset`, `rte_config` (`PHASES` :58, `DPMX_LIVE_OK_ENV` :139, `FIRST_LIVE_PRESET_NAME` :156, `PRICING_CONFIG_PATH` :165), `lib.pricing_surface.pricing_surface_metadata` (:252), `lib.route_options` (:258); `extractor.phases.base/a/z` (:266–268); try/except+importlib fallbacks for `lib.batch_clients` (:270–299), `lib.intelligence_router` (:301–317), `lib.spend_ledger` baseline shims (:318–356); `rich` imports (:524–535) | 1–548 |
| **Cost-profile & routing config** | `EXTRACTOR_SERVICE_DIR` (:549), `R_REQUIRED_ARTIFACT_GROUPS` (:550), `DEFAULT_COST_PROFILE` (:599), `COST_PROFILES` (:650), `LEGACY_ROUTING_POLICY_TO_COST_PROFILE` (:930), `COST_PROFILE_ALIASES` (:945), `COST_PROFILE_ALIAS_METADATA` (:971), `resolve_cost_profile` (:1046), `resolve_cell_alias` (:1133), `resolve_contract_routes` (:1351), `assert_strict_route_provider_allowed` (:1370), `_apply_provider_lock` (:1433), `ROUTING_LADDERS` (:1488), `ACTIVE_ROUTING_POLICY`/`ACTIVE_ROUTING_LADDERS` (:1662–1666), `ACTIVE_OUTPUT_LAYOUT` (:1769), per-policy ladder tables (:1770–1938), `MODEL_ROUTING`/`DEFAULT_MODEL_ROUTING` (:1939–1940), `PROVIDER_BASE_URL` (:1942) | 549–1993 |
| **Prompt roots / S-mode / step parsing** | `prompt_root` (:1994), `_ACTIVE_S_PROMPTS_MODE` (:2002), `set_active_s_prompts_mode` (:2006), `step_sort_key` (:2052), `_parse_step_csv` (:2063); classification regex/const tables `TEXT_NAMES` (:2127) … `PROVIDER_API_KEY_ENV` (:2255) | 1994–2288 |
| **Logging + config dataclasses** | `configure_run_file_logger` (:2289, mutates `_RUN_FILE_HANDLER` :2285), `RunnerConfig` (:2312 — ~70 fields incl. `ledger`, `router`, cost-profile block), `PromptSpec` (:2387), `BatchWatchResult` (:2397), `UiConfig` (:2404) | 2285–2409 |
| **Output layout wrappers** | `configure_output_layout` (:2410, mutates `ACTIVE_OUTPUT_LAYOUT`), `current_output_layout`/`current_extraction_root`/`current_runs_root`/`current_doctor_root` (:2420–2449) | 2410–2451 |
| **UI / presentation** | `OperatorArgumentParser` (:2452), `UI` (:2519–3548, 28 methods) | 2452–3548 |
| **Run lifecycle / dirs / sidecars** | `PartitionExecResult` (:3549), `PromptsetBlockedError` (:3564), `now_iso` (:3571), `resolve_run_context` (:3641), `get_run_dirs` (:3658), `write_json` (:3676) | 3549–3703 |
| **Live-consent & pre-live validator gate** | `build_pre_live_validator_command` (:3704), `is_read_only_introspection_mode` (:3800), `classify_live_capable_operations` (:3826), `enforce_live_operation_consent` (:3912 — requires `DPMX_LIVE_OK=1` :3928), `enforce_home_scan_full_consent` (:3943), `enforce_pre_live_validator_for_execution` (:4103) | 3704–4176 |
| **Spend/costing + telemetry deps** | locks (:4177–4179), `SpendTrackerState` (:4183), `_ACTIVE_SPEND_TRACKER` (:4196), `_HTTP_SESSION` (:4198), `_append_jsonl` (:4240), `compute_run_status` (:4257), `update_run_manifest_status` (:4277), DI factories `_telemetry_writer_deps` (:4312) / `_reporting_deps` (:4322) / `_llm_runtime_deps` (:4371) / `_phase_runner_deps` (:4432), `load_pricing_registry` (:4452), `extract_usage_summary` (:4482), `estimate_usage_cost_usd` (:4526), `_write_spend_ledger_snapshot` (:4544), `reset_spend_tracker` (:4585), `initialize_spend_tracker` (:4591), `record_request_cost` (:4696), snapshot writers (:4829–4932) | 4177–4947 |
| **Promptgen input scan** | `_select_promptgen_files` (:4964), `scan_promptgen_inputs` (:5230) | 4948–5435 |
| **File classification** | `safe_read` (:5436), `classify_surface` (:5494), `classify_tier` (:5589), `get_git_sha` (:5615), manifest artifact collectors (:5624–5728) | 5436–5728 |
| **Env & step routing resolution** | `_env_is_truthy` (:5729), `_live_llm_calls_blocked_for_tests` (:5737), `dpmx_env_routing_payload` (:5815), `choose_model_for_step` (:6152), `resolve_effective_step_route` (:6167), `write_phase_routing_log` (:6359), batch-job manifests + webhooks (:6415–6690), ladder machinery (:6691–6963), `effective_model_routing_payload` (:6965), `apply_model_overrides` (:6830 — mutates 4 routing globals :6834–6837) | 5729–7035 |
| **Run manifest writers** | `write_run_manifest` (:7036), `write_runner_identity` (:7049), promptset-block markers (:7082–7125) | 7036–7125 |
| **Collector & prompt loading** | `Collector` (:7126), `extract_output_artifacts` (:7194), `get_phase_prompts` (:7322), `promptset_fingerprint` (:7391), `write_run_routing_fingerprint` (:7401), `resolve_phase_list` (:7573) | 7126–7663 |
| **Doctor / provider preflight** | `run_doctor_checks` (:7664), `collect_provider_routes` (:7774), `run_provider_doctor_probe` (:7873), `run_provider_preflight` (:7969), `ensure_launch_provider_preflight` (:8845), `prepare_phase_provider_preflight` (:8878), `run_gemini_list_models` (:8945), `run_doctor_full` (:9103) | 7664–9212 |
| **Prescan integration** | `run_integrated_prescan_stage` (:8111), `_load_imported_prescan_router` (:8223), influence sinks/receipts (:8276–8698) — interleaved with doctor region | 8111–8698 |
| **Inventory & partitioning** | `build_inventory` (:9213), `build_partitions` (:9261), `_apply_router_partition_hints` (:9409), chunk mergers (:9569–9692), `classify_request_failure` (:9693), `normalize_step` (:9851 — single 400-line function) | 9213–10255 |
| **Transport / LLM client layer** | `transport_for_provider` (:10256), `build_chat_payload` (:10282), gemini auth-mode machinery (:10367–10402), route fingerprints (:10411–10509), `make_headers` (:10520), `resolve_api_key` (:10574), SDK client getters (:10645–10684), `summarize_llm_response` (:10806), usage normalization (:10970–11066) | 10256–11199 |
| **Cost guard (in-flight)** | `CostLimitExceededError` (:11200), `_build_cost_abort_state` (:11206), `_raise_cost_limit_exceeded` (:11278), `_persist_cost_abort` (:11313), `_check_projected_cost_limit` (:11400), `_resolve_runtime_usage` (:11440), `_accumulate_runtime_spend` (:11472), `_reserve_projected_spend` (:11546) | 11200–11617 |
| **LLM call + retry + failure classification** | `capture_exception_metadata` (:11618), `classify_failure_type` (:11650), `call_llm` (:11826), `enrich_request_meta` (:11882), `call_llm_with_ladder` (:12088), `run_gemini_auth_probe` (:12114), `run_auth_doctor` (:12236) | 11618–12425 |
| **JSON parse/repair** | `extract_first_json_object` (:12441), `try_repair_json_truncation` (:12547), `parse_json_from_response_with_provenance` (:12623), `parse_json_from_response` (:12738) | 12426–12751 |
| **Partition context building** | `build_partition_context` (:12781), file caps (:12897–12945), `build_output_envelope_instructions` (:12946) | 12752–13013 |
| **Structured-output / schema gate + escalation** | `describe_schema_gate_failure` (:13014), `artifacts_pass_schema_gate` (:13108), `_REPAIR_COUNTERS` (:13119), `_attempt_schema_repair_path_items` (:13132), `classify_escalation_class` (:13278), `build_first_failure_context` (:13399) | 13014–13445 |
| **Batch + strict-passthrough evidence** | `build_batch_client` (:13450), batch route resolution (:13468–13619), strict-passthrough evidence chain (:13655–13868), `build_v5_batch_request` (:13869), `validate_success_partition_output` (:13966) | 13446–14197 |
| **Partition workers + comparison lane** | `_run_one_partition_worker` (:14198), `COMPARISON_ELIGIBLE_STEPS` (:14355), `run_comparison_lane` (:14504), `generate_comparison_summary` (:14548) | 14198–14687 |
| **`execute_step_for_partitions`** | (:14688–18383) — single ~3,700-line function; the deepest tangle in the file | 14688–18383 |
| **`_run_phase_inner`** | (:18384–18743) — shared phase executor, target of all `run_phase_*` | 18384–18743 |
| **Verification / status / reporting-printers** | `verify_phase_output` (:18803), `phase_status_snapshot` (:18851), `run_status_loop` (:19024), `print_promptpack` (:19062), `_pricing_preview_record` (:19105), `build_phase_cost_preview` (:19251), guide printers (:19350–19507), `tail_run_log` (:19565), coverage (:19652–20010), `print_config` (:20041), `update_proof_pack` (:20215) | 18744–20253 |
| **Audit judge (xai)** | `AUDIT_JUDGE_MODEL` (:20270), `audit_phase_sample` (:20309) | 20254–20444 |
| **Phase artifact collection + batch watch** | `collect_phase_artifacts` (:20445), `run_batch_watch` (:20579) | 20445–21071 |
| **Phase runners** | `_selected_execution_step_ids_for_phase` (:21088), `_merge_scan_excludes` (:21100), `run_phase_A` (:21113) … `run_phase_Z` (:22174); Phase R async pilot (`_build_event_store_for_runner` :21349, `run_phase_R_async_submit` :21436, `run_phase_R_finalize` :21759) | 21072–22179 |
| **Preset/validator helpers** | `run_sync_scopes` (:22180), `first_live_phase_sequence` (:22196), `apply_first_live_preset` (:22204), `run_pre_live_validator` (:22245), `write_confidence_ramp_artifacts` (:22269) | 22180–22376 |
| **`main()`** | (:22377–~24191): argparse build (:22382–~22788, 106 `add_argument` calls), `parse_args` (~:22789), S_INT branch with its own `RunnerConfig(` (~:23158), main `RunnerConfig(` (~:23447), introspection dispatch (~:23553–23597), `SpendLedger` attach (:23599–23607), prescan stage (:23610), **dead duplicate introspection block** (~:23692–23713), promptset gate (:23714), phase R async dispatch (:23815), spend tracker init (:23984–24000), `runners` dict (:24012–24028), phase loop (:24030+) | 22377–24191 |
| **Batch retrieval tail** | `run_batch_retrieval_and_integration` (:24192–EOF) | 24192–24286 |

**Sibling modules already extracted** (OBSERVED): `rte_config.py`, `rte_constants.py`, `rte_ops_surfaces.py`, `rte_phase_wrappers.py`, `rte_promptset.py`, `rte_output_layout.py`, `reporting.py`, `llm_runtime.py`, `phases.py`, plus `lib/` (spend_ledger, pricing_surface, batch_clients, intelligence_router, structured_output_contracts, …). The monolith already has a mature DI convention: `_telemetry_writer_deps`/`_reporting_deps`/`_llm_runtime_deps`/`_phase_runner_deps` (:4312–4443) build frozen deps objects consumed by extracted modules. **New seams should copy this pattern, not invent another.**

---

## 2. Seam Verdicts

### Seam 1 — UI/presentation → `extractor/ui.py` — **VALIDATED, risk LOW (one correction)**

**What moves** (OBSERVED): `UiConfig` (:2404), `UI` (:2519–3548, 28 methods: `_emit_event`, `make_trace_context`, `llm_request_event`, `spend_ledger_event`, `partition_start_event`, `retry_event`, `phase_start/step_start/step_done/phase_done`, `failure_spotlight`, `status_table`, etc.), `OperatorArgumentParser` (:2452).

**Outbound deps of `UI` body** (OBSERVED via symbol scan of :2520–3548): `rich` Console/Panel/Table/Progress (module-level import :524–535), `now_iso`, `_append_jsonl` (2 call sites), `EXTRACTOR_COMPONENT_NAME` (:4201). That is the whole observed set — very low coupling. INFERRED: `make_trace_context` likely also uses `_new_trace_id`/`_new_span_id` (:4204/:4208) — verify at cut time; both are 3-line pure functions, trivially movable.

**Outbound deps of `OperatorArgumentParser`** (OBSERVED): `ROUTING_LADDERS` (:1488, monolith constant), `DEFAULT_ROUTING_POLICY` (:598), `PHASES`, `FIRST_LIVE_PRESET_NAME`, `DPMX_LIVE_OK_ENV` (all from `rte_config` — importable directly, no monolith dependency).

**Correction to plan**: `extractor/ui.py` must NOT import from `run_extraction_v5` (circular: v5 already imports `extractor.phases.*` :266–268). Two fixes required:
1. `ROUTING_LADDERS` reference inside `OperatorArgumentParser.error()` (:2489): inject valid-policy names via constructor kwarg (or move the guidance strings to `rte_config`). Everything else it needs comes from `rte_config`.
2. `_append_jsonl` uses module global `_JSONL_WRITE_LOCK` (:4177) shared with telemetry writers. If `UI` gets its own copy of the writer, UI events and telemetry writers would hold **different locks**. UNKNOWN whether they ever append to the same file path — safe cut: inject `append_jsonl: Callable` into `UI.__init__` and keep the single monolith implementation until costing/telemetry also moves.

**Inbound**: 24 signatures reference `Optional[UI]`/`UI` (OBSERVED count) — type-only; monolith adds `from extractor.ui import UI, UiConfig, OperatorArgumentParser` and re-exports for tests.

**Global state touched**: none directly (only via injected writer). **Order: EXTRACT FIRST.**

### Seam 2 — Costing engine → `extractor/costing.py` — **CORRECTED CUT REQUIRED, risk HIGH as planned / MED as corrected**

**The plan's assumption is wrong in one important way** (OBSERVED): there are **two interleaved costing systems**, and the plan's symbol list spans both:

- **System A — SpendTracker (run-level Decimal cap)**: `SpendTrackerState` (:4183), `_ACTIVE_SPEND_TRACKER` + `_SPEND_TRACKER_LOCK` (:4196/:4179), `load_pricing_registry` (:4452, reads `PRICING_CONFIG_PATH` YAML), `estimate_usage_cost_usd` (:4526), `_write_spend_ledger_snapshot` (:4544), `reset_spend_tracker` (:4585), `initialize_spend_tracker` (:4591), `record_request_cost` (:4696), `_quantize_usd`/`_pricing_key` (:4444/:4448), `extract_usage_summary` (:4482). Activated only when `--max-cost-usd` is set (`initialize_spend_tracker` returns None otherwise, :4599–4601) and forces `--partition-workers 1` (:4602).
- **System B — SpendLedger (per-request preventive guard)**: `cfg.ledger` is a `lib.spend_ledger.SpendLedger` attached in `main()` (:23599–23607). The in-flight guard functions run on it: `_check_projected_cost_limit` (:11400, calls `cfg.ledger.check_limit` :11424), `_accumulate_runtime_spend` (:11472, `cfg.ledger.accumulate` :11498), `_reserve_projected_spend` (:11546, :11573), `_pricing_preview` (:11139, `cfg.ledger.price_usage` :11152). `CostLimitExceededError` (:11200) and `_persist_cost_abort` (:11313) serve **both** systems.

**Reconciliation verdict**: baseline-rate shims (:318–356 — `BASELINE_INPUT/OUTPUT_COST_PER_1M_USD`, `PRICING_VERSION`, `UNKNOWN_MODEL_POLICY`) are consumed only by `_pricing_preview_record` (:19105–19138) and `build_phase_cost_preview` (:19263) — the dry-run preview path — and duplicate defaults that live in `lib/spend_ledger.py`. `lib/pricing_surface.py` exists (OBSERVED) and `pricing_surface_metadata` is imported (:252) and used at :4757, :10499, :12017, :19124 for provenance metadata, not for math.

**Corrected cut**: extract **System A intact** (all SpendTracker symbols above + the singleton + lock, exposing `get_active_spend_tracker()`/`reset`/`initialize` accessors — `update_run_manifest_status` :4284–4288 reads the singleton and must switch to the accessor). Move `CostLimitExceededError` with it (both systems raise it; it is dependency-free). **Leave System B guard functions in place initially** — they are welded into `call_llm`/`enrich_request_meta`/`execute_step_for_partitions`/batch/phase-R paths at ~30 call sites (:7892–:23249 OBSERVED spread) and already flow through the `_llm_runtime_deps()` DI seam (:4371–4431 passes `check_projected_cost_limit`, `accumulate_runtime_spend`, `cost_limit_exceeded_error`). A second PR can move System B behind the same deps object.

**Inbound deps to respect**: `initialize_spend_tracker` calls `collect_provider_routes` (:7774) and `_selected_execution_step_ids_for_phase` (:21088) — inject both as callables (mirror `PhaseRunnerDeps` style). `_write_spend_ledger_snapshot` needs `write_json`, `_telemetry_path`, `now_iso`, `SPEND_LEDGER_FILENAME` — first three are small utilities; the constant comes from `rte_constants`/`rte_config` (INFERRED origin — verify).

**Risk grade**: HIGH if cut exactly as the plan words it (it would rip `CostLimitExceededError`+guards away from `cfg.ledger` call sites); **MED with the corrected two-stage cut**. **Order: THIRD** (after UI and cli_args).

### Seam 3 — Argparse builder → `extractor/cli_args.py` — **VALIDATED with caveats, risk MED**

**What moves** (OBSERVED): the parser construction block in `main()` — `OperatorArgumentParser(...)` (:22382) + 106 `add_argument` calls ending before `parse_args` (~:22789). Package as `build_parser(...) -> OperatorArgumentParser`.

**Outbound deps** (OBSERVED in argument definitions): `PHASES`, `DPMX_LIVE_OK_ENV`, `FIRST_LIVE_PRESET_NAME`, `STAGED_SAFE_PRESET_NAME` (all `rte_config` — clean), plus monolith constants `DEFAULT_GEMINI_MODEL_ID` (:1470), `COST_PROFILES` (:650), `COST_PROFILE_ALIASES` (:945), `COST_PROFILE_ALIAS_METADATA` (:971), `DEFAULT_COST_PROFILE` (:599), routing-policy choice list (:22466–22475). Same circular-import rule as UI: inject these via a small `ParserContext` dataclass or move the cost-profile tables into `rte_config` (they are contract-sensitive — moving them is a bigger review surface; injection is the minimal correct change).

**Two traps** (OBSERVED):
1. **Default-literal coupling**: profile budget overrides compare parsed args against hard-coded default literals — `if args.max_files_docs == 35` (:23641), `== 20` (:23643), `args.max_chars == 650000` (:23646), `args.file_truncate_chars == 70000` (:23653). If a default changes in `cli_args.py` without updating these literals, profile overrides silently stop applying. The extraction PR should define named constants used by BOTH sides.
2. **Parser object outlives building**: `parser.error(...)` is called from post-parse logic (e.g. `--print-phase-prompts` validation :23573/23712) — `build_parser` must return the parser, not just args.

**Sequencing note**: `OperatorArgumentParser` (Seam 1) is the class this seam instantiates. Either land ui.py first and import it from there, or put `OperatorArgumentParser` in `cli_args.py` instead of `ui.py` (it is argparse plumbing, not rendering — INFERRED better home). Recommend: **move `OperatorArgumentParser` to `cli_args.py`, not `ui.py`** — minor correction to the plan. **Order: SECOND.**

### Seam 4 — Phase modules → `extractor/phases/{c,d,x,h}.py` — **VALIDATED, risk LOW (C, D, X) / MED (H)**

**How the working extractions operate** (OBSERVED): `run_phase_A` (:21113) and `run_phase_Z` (:22174) are 2-line delegators calling `extracted_run_phase_A/Z(_phase_runner_deps(), dirs, cfg, ui=ui)`. `PhaseRunnerDeps` (`extractor/phases/base.py:9`) carries: `repo_root`, `repo_scan_excludes`, `collector_cls`, `merge_scan_excludes`, `run_phase_inner`, `selected_execution_step_ids_for_phase`, `collect_phase_artifacts`. `_phase_runner_deps()` (:4432) fills it with `Path.cwd()`, `REPO_SCAN_EXCLUDES` (:2235), `Collector` (:7126), `_merge_scan_excludes` (:21100), `_run_phase_inner` (:18384), `_selected_execution_step_ids_for_phase` (:21088), `collect_phase_artifacts` (:20445).

**How C/D/H/X are dispatched in v5** (OBSERVED): via the `runners` dict in `main()` (:24012–24028) → `run_phase_C` (:21142), `run_phase_D` (:21176), `run_phase_H` (:21119), `run_phase_X` (:22069). All four already delegate planning to `rte_phase_wrappers` (`plan_repo_scan_phase` for C/D, `plan_home_phase` for H, `plan_x_phase` for X) and then call `_run_phase_inner`.

**Deps-coverage check per candidate**:
- **C** (:21142): needs `plan_repo_scan_phase` + everything already in deps. Gap: the `plan_*` callable itself. **LOW — rank 1.**
- **D** (:21176): identical shape, smaller (targets=`["docs"]`). **LOW — rank 2.**
- **X** (:22069): identical shape via `plan_x_phase` (no targets/base_excludes params). **LOW — rank 3.**
- **H** (:21119): needs three extra dependencies not in `PhaseRunnerDeps`: `enforce_home_scan_full_consent` (:3943 — consent gate reading `DPMX_HOME_SCAN_FULL_OK` :2242), `HOME_SAFE_ROOTS` (:2155), `home_safe_filter` (:7622), plus `plan_home_phase` and `Path.home()`. **MED — rank 4, only if the wave wants 4 phases.**

**PhaseRunnerDeps extension recommendation**: add one field `plan_repo_scan_phase: Callable` (used by C, D — and E/W/B/G later, which are the same shape :21198–21318) and `plan_x_phase: Callable` for X — OR let phase modules import `plan_*` directly from `rte_phase_wrappers` (top-level sibling module, no circularity; but breaks the pure-DI convention a.py established). Prefer the deps-field route: keeps phase modules import-free of service modules and matches the existing pattern. For H, add `enforce_home_consent`, `home_safe_roots`, `home_safe_filter`, `plan_home_phase`, `home_dir`.

**Note**: E, W, B, G (:21198–21318) are structurally identical to C/D — the extraction template for C generalizes to six more phases for free. Q/R/S/SP/T have extra coupling (Q aggregates artifacts, S validates R quality :22122–22138, R has the async webhook pilot) — do not include in this wave.

**Order: can proceed in parallel with Seams 1–3** (touches different regions).

### Extraction order recommendation

1. **UI** (`ui.py`) — lowest coupling, unblocks readable diffs elsewhere.
2. **cli_args** (`cli_args.py`, absorbing `OperatorArgumentParser`) — shrinks `main()`.
3. **Phase modules C, D, X (+H optional)** — parallel-safe with 1–2.
4. **Costing System A** (`costing.py`) — after the above, with the corrected two-stage cut; System B guard migration as a follow-up PR.

---

## 3. Global-State Inventory (anything an extraction must respect)

Module-level **mutable** state (OBSERVED):

| Symbol | Line | Mutated by | Notes |
|---|---|---|---|
| `ACTIVE_ROUTING_POLICY`, `ACTIVE_ROUTING_LADDERS` | :1662–1666 | `apply_model_overrides` (:6830, `global` at :6836–6837) | routing seam hazard |
| `MODEL_ROUTING`, `DEFAULT_MODEL_ROUTING` | :1939–1940 | `apply_model_overrides` (:6834–6835) | " |
| `ACTIVE_OUTPUT_LAYOUT` | :1769 | `configure_output_layout` (:2411) | read by all `current_*_root` wrappers |
| `_ACTIVE_S_PROMPTS_MODE` | :2002 | `set_active_s_prompts_mode` (:2007) | phase S/SP prompt selection |
| `_RUN_FILE_HANDLER` | :2285 | `configure_run_file_logger` (:2290) | logging |
| `_ACTIVE_INTELLIGENCE_ROUTER` | :2286 | `main()` (:23615) | "legacy code" escape hatch for prescan router |
| `_JSONL_WRITE_LOCK`, `_TELEMETRY_SNAPSHOT_LOCK`, `_SPEND_TRACKER_LOCK` | :4177–4179 | — | lock-split hazard if writers move separately |
| `_ACTIVE_SPEND_TRACKER` | :4196 | `reset_spend_tracker`/`initialize_spend_tracker` (:4585/:4591); read by `update_run_manifest_status` (:4284) | costing seam core |
| `_HTTP_SESSION` (+lock) | :4198–4199 | `_get_http_session` (:4232) | shared connection pool |
| `_REPAIR_COUNTERS` (+lock) | :13118–13119 | schema-repair path | telemetry counters |
| `_PROMPTSET_RULES_CACHE` | :14664 | `_load_promptset_rules` (:14668) | prompt cache |

**Env reads** (OBSERVED): `DPMX_LIVE_OK_ENV` (consent, :3928/:4109), `RTE_DISABLE_LIVE_LLM_IN_TESTS`/`RTE_ALLOW_LIVE_LLM_IN_TESTS` (:2240–2241, via `_live_llm_calls_blocked_for_tests` :5737), `DPMX_HOME_SCAN_FULL_OK` (:2242), `STEP_TYPE_MODEL_ENV_VARS` (:2247, per-step model overrides via `_resolve_env_step_type_routes` :5808), `PROVIDER_API_KEY_ENV` (:2255, key resolution :10574), `WEBHOOK_DB_URL` (:21346), `LEGACY_PROMPT_ROOT_ENV_VAR` (rte_config import :162 area). INFERRED: more env reads exist inside `execute_step_for_partitions` — not exhaustively swept.

---

## 4. Dead / Duplicate Code

- **CONFIRMED (OBSERVED)**: the duplicated introspection block at ~:23692–23713 (`args.print_config` / `print_run_order` / `print_phase_routing` / `print_phase_prompts`) is unreachable. The first block (~:23553–23597) handles the identical flags and every branch ends in `sys.exit(...)` (:23555, :23558, :23561, :23574) — if any of those flags is set, control never reaches :23692. The `should_gate_promptset` logic at :23714 immediately after IS live; a deletion PR must cut exactly :23692–23713.
- Redundant re-derivation (live, not dead): `phase_sequence` is computed before the first introspection block and recomputed at :23656 (`resolve_phase_list`) with a repeated `if not phase_sequence and preset_phase_sequence` fallback (:23550 and :23657). Consolidation candidate for the cli_args PR.
- `"compose.yml"` appears twice in the targets list of `extractor/phases/a.py` (OBSERVED) — harmless duplicate.
- Legacy siblings `run_extraction_v3.py` (469 KB) and `run_extraction_v4.py` remain in-tree (OBSERVED); out of A1 scope but relevant to any dead-code sweep.
- UNKNOWN: no full sweep for other unreachable regions inside `execute_step_for_partitions` (:14688–18383) was performed — its size demands a dedicated pass.

---

## 5. Reachability Notes (regression-risk bounding)

- **Read-only introspection** (`is_read_only_introspection_mode` :3800; flags `--print-config`, `--print-run-order`, `--print-phase-routing`, `--print-phase-prompts`, `--doctor-auth`, `--print-promptpack`, `--coverage-report`, `--verify-phase-output`, `--doctor`, `--list-phases`, guide printers): exits inside the block at ~:23553–23597 (or earlier, ~:22881–22885 for guides) — **before** SpendLedger attach (:23599), prescan (:23610), spend tracker init (:23984), and the phase loop (:24030). Extractions touching only costing or phase runners cannot regress these modes; extractions touching cli_args or config resolution can.
- **Dry-run** (`--dry-run`): traverses the FULL path — parser → cfg → prescan → manifest writers → phase loop → `_run_phase_inner` → partition building — with live LLM calls suppressed. All four seams are exercised by dry-run, which is the cheapest regression harness.
- **Live (`--execute`)**: requires `--execute` AND `DPMX_LIVE_OK=1` (`enforce_live_operation_consent` :3912, :3928; parser help :22386). Live-only regions: `call_llm` network paths (:11826+), cost guard Systems A+B accumulation, batch submit/watch (:20579), webhooks (:6584–6690), phase R async pilot (:21436/:21759), audit judge (:20309). Cost tracker (System A) additionally requires `--max-cost-usd`.
- **Batch-only**: `run_batch_watch` (:20579), `run_batch_retrieval_and_integration` (:24192) — reachable only with batch mode flags.
- **Test guard**: `_live_llm_calls_blocked_for_tests` (:5737) blocks live calls under pytest unless `RTE_ALLOW_LIVE_LLM_IN_TESTS` is set — extraction PRs can rely on the existing test suite (`tests/`, 180 entries) without live spend.
- **S_INT branch** (:23148–23158): separate sub-runtime imported lazily inside `main()` (`s_int.run_s_int`), with its own `RunnerConfig(` construction (~:23158) — cli_args extraction must not disturb the S_INT early path.

---

## 6. Open UNKNOWNs for extraction PRs

1. Whether `UI._emit_event` and telemetry `_append_jsonl` callers ever target the same file (lock-split hazard, Seam 1). Verify before giving UI its own lock.
2. Exact origin module of `SPEND_LEDGER_FILENAME`, `EXTRACTOR_COMPONENT_NAME` re-export needs (INFERRED `rte_config`/local).
3. Full closure of `UI.make_trace_context` over `_new_trace_id`/`_new_span_id` (INFERRED yes).
4. Env-read census inside `execute_step_for_partitions` — not exhaustively swept.
5. Whether any test imports `OperatorArgumentParser`/`UiConfig` from `run_extraction_v5` directly (re-export shims needed) — grep `tests/` at cut time.
