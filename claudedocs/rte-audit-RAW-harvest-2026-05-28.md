# RTE Distributed Audit — RAW HARVEST (run wf_08e6e042-1c2, schemaless, stalled)

HEAD 755bf3846 · harvested final markdown from all completed agents. MCP audit hung (partial); synthesis never ran.



==========================================================================================
## RTE-CORE S1-authority  (workflow-subagent, a17781efdd9b0ff5d, 5329 chars)
==========================================================================================

I'll audit stage S1-authority of the Repo Truth Extractor, verifying the authority map's claims against primary source. Let me start by orienting myself.

I'm on a fresh main checkout (HEAD `755bf3846`). Note: the authority map I was given cites line numbers against a `run_extraction_v5.py` of 23,375 lines — that matches what I see here (23,375 lines confirmed). Let me verify the key authority claims against primary source.

Let me look at the canonical pointer claims first.

Three of four authority-map claims confirmed against source. Let me verify the v4/v5 wrapper relationship, the v3 docstring-fork claim, and the v3 live-execute path. These are the load-bearing claims for stage S1.

Important discrepancy found: the authority map says `run_extraction_v4.py` is 1,142 lines and a "Typer wrapper" — confirmed Typer (`APP = typer.Typer`, v4:29). But v4 has its own `PHASE_DIR_NAMES` dict that **diverges** from `phases.py`: v4:59 defines `"S": "S_synthesis_trace"` while `phases.py:153` defines `S → "S_synthesis"`. And v4 has no `SP` phase. This is a fragmentation finding. Let me dig into the v3 live-execute path and verify how v4 actually invokes v5 (does it terminate execution itself, or hand off?).

Two important refinements to the authority map:

1. v5 does **not** define its own `RUNNER_SCRIPT` self-reference — it relies on `rte_config.py:126`. v3 *does* self-reference (`v3:159`). The map's claim "v5 owns its own `main()` argparse CLI (v5:21502)" and the v3/v5 fork claim need verifying.
2. v4 calls v5 via `subprocess` (v4:205, `sys.executable str(V5_RUNNER)`) — so v4 does NOT terminate execution; it spawns v5 as a child process. Confirmed.

Let me verify v5's `main()`/argparse, the v3 `--execute` gate logic (does `DPMX_LIVE_OK` actually gate it, fail-closed?), and run a falsifiability check on the "v3 still reachable in runtime" claim (grep non-test references).

Glob escaping issue under zsh. Let me re-run with rg, which handles globs internally, and verify the v3 fail-closed gate at line 11234.

Now I have a critical finding. The authority map says v3 is referenced in non-test runtime "only by run_repscan.py, run_probe.py, tools/phase0_serialize_partitions.py". But I found **two more critical references the map missed**:

1. `src/dopemux/commands/extractor_commands.py:474` → `return base / "run_extraction_v3.py"` — the operator CLI itself can resolve to v3.
2. `scripts/reprocess_failed_partitions.py:17` → `RUNNER_SCRIPT = Path(".../run_extraction_v3.py")` — an operator script hardcoded to v3.

Let me inspect `extractor_commands.py` around 470-474 to understand the v3/v5 selection logic — this is the central alias-drift question for S1.

This is now a material finding. The operator CLI (`extractor_commands.py:467-478`) is a **multi-version dispatcher** that accepts `pipeline_version` of v5/v4/v3 and resolves to the corresponding runner via subprocess. So v3 *is* operator-reachable, not just helper-imported. I need to check what default `pipeline_version` the operator CLI passes here — if it defaults to v3 anywhere, that contradicts the "v5 is operator default" claim.

Let me check the default wiring for this dispatcher and whether `reprocess_failed_partitions.py` can trigger live v3.

Now I have the full picture for the `rte run` dispatcher path. Let me read the actual command definition (lines ~278-340) to confirm whether `--pipeline-version` with `default="v5"` feeds the `_run_extractor_runner` subprocess dispatcher (live-capable), or only a read-only status forwarder. The help text at line 310 says "forward runtime status" and line 333 says "not the canonical runtime run-status surface" — I need to disambiguate which command actually launches a runner.

Key clarification: the `extractor` command group's `run` (line 282) is **disabled** (raises ClickException at line 291) — it does NOT reach `_run_extractor_runner`. And `status` (line 323) disables the legacy `--pipeline-version` alias (line 339). So in *this* command file, the v3/v4/v5 dispatcher `_run_extractor_runner` (line 481) and `_extractor_runner_path` (line 467) exist but I need to find their actual *live* call sites. Let me find who calls `_run_extractor_runner` with what default, and locate the canonical `rte run` (the one with `default="v5"` at cli.py:4920 per the authority map).

Now I have the complete dispatcher picture. Critical observations:

- `cli.py:4920` (`default="v5"`) and `cli.py:4949` (truth-run alias hardcodes v5) — **CONFIRMED** as authority map claims, but the line numbers shifted slightly (the `default="v5"` is at 4920 in the map; I see it at line ~4919 in `_pipeline_version_options`). Let me not quibble — the substance holds.
- BUT: `_resolved_pipeline_version` (cli.py:4926) lets a hidden `--engine-version` legacy flag (cli.py:4910, `default=None`) **override** the v5 default. And most `rte` subcommands pass `effective_version` (not hardcoded v5) to `_run_extractor_runner`. So an operator passing `--engine-version v3` or `--pipeline-version v3` reaches live v3.
- `cli.py:5522` hardcodes `pipeline_version="v4"` for one command — need to know which.

Let me confirm the `effective_version` flow reaches a **live** (`--execute`-capable) v3 path and identify the v4-hardcoded command. Let me also verify v5's `main()` terminates (the `if __name__ == "__main__"` at v5:23374).

==========================================================================================
## RTE-CORE S2-prompts  (workflow-subagent, aa4733dc902b3947a, 6293 chars)
==========================================================================================

I'll audit the S2-prompts stage. Let me start by orienting myself to the actual files before relying on the authority map's claims.

I'm in the main repo at HEAD `755bf3846`. The authority map references `services/repo-truth-extractor/`. Note this is on `main`, not a worktree with the RTE-specific commits the memory files reference (`8ea182dd3`, etc.). Let me record where I am and proceed.

Let me read the core S2-prompts authority files. I'll start with the prompt resolution logic, the v4 promptset.yaml, and the two registries.

Now I have the core resolution logic and both registries. Let me examine the v4 promptset.yaml (section/schema authority) and the actual Phase S prompt files to look for "legacy context" fabrication-risk blocks and section/schema drift.

This is rich. I now see a critical Phase S split-authority situation. Let me map it carefully:

**Three separate "Phase S" sources exist:**
1. `promptsets/v4/promptset.yaml` declares phase `S` with steps S0-S12 (13 steps), file `promptsets/v4/prompts/PROMPT_S*.md` (13 S files confirmed)
2. `prompts/phase_s/registry.json` declares phase `SP` with steps SP0-SP12 (13 steps), files `PROMPT_SP*.md`
3. `prompts/phase_s_int/registry.json` declares some phase with S16-S20

There's a clear mismatch between the v4 promptset's S-phase step definitions and the SP registry. Note: v4 S0-S12 vs SP registry SP0-SP12 have DIFFERENT semantics at some indices (e.g., v4 S4 = TWO_PLANE_ARCHITECTURE, but SP4 = TRUTH_PACK_INDEX; v4 S5 = TASK_ORCHESTRATOR, SP5 = DECISION_GRAPH). They are NOT the same pipeline renamed.

Now let me look at the actual prompt content for fabrication-risk "legacy context" blocks, and check `phases.py` for `REQUIRED_PROMPT_STEP_IDS`, and the phase_s_int registry.

Now I have the structural picture. Key confirmations:

1. `phases.py:37-40` — `PHASE_S_BASE_STEPS = S0..S12`, `PHASE_SP_BASE_STEPS = SP0..SP12`. `REQUIRED_PROMPT_STEP_IDS["S"]` = S0-S12, `["SP"]` = SP0-SP12 (phases.py:197-198).
2. `prompts/phase_s/registry.json` declares phase `SP` (SP0-SP12) — but `phase_s_registry_dir` (rte_promptset.py:65-76) resolves the SP registry FROM the `phase_s` directory. So phase "S" in registry mode resolves SP prompts. There's an interesting overload here.

Critically, `resolve_phase_s_prompts` (rte_promptset.py:291-352): when mode == "registry", it loads `phase_s/registry.json` (which is the SP registry), iterates its steps (SP0-SP12), and builds specs with step_id = SP0..SP12 but for phase "S". Then `prompt_hash_report_for_phase("S", specs)` expects `REQUIRED_PROMPT_STEP_IDS["S"]` = {S0..S12}, but observed steps are {SP0..SP12}. This would flag ALL S0-S12 as MISSING and all SP0-SP12 as unexpected-but-present. Let me verify how this is actually wired — does the runtime call `resolve_phase_s_prompts` with phase "S" and then hash against "S" required steps? This is a potential CRIT (promptset always-blocked or split authority). Let me trace the v5 wiring.

Let me now read the actual S-phase prompt content for fabrication-risk "legacy context" blocks (the core S2-prompts concern), and trace how v5 wires phase S resolution + hashing.

The "Legacy Context" phrase appears in the v4 S-prompts as a guardrail: "Legacy Context is intent guidance only and is never evidence." This is an anti-fabrication rule, not an injection of a fabrication-risk block. But the prompts *reference* "Legacy Context" as if a block named that is injected into the prompt at runtime. The question for fabrication risk: is there actually a "Legacy Context" block injected, and what's in it? If a legacy doc is injected and the guardrail line is the only thing stopping the model from treating it as truth, that's a fabrication-risk surface. Let me find where "Legacy Context" gets injected and what content it carries.

Let me also check the two divergent S2 prompts more carefully — v4 `PROMPT_S2` requires sections "Goal/Inputs/Outputs/Schema/..." (matches `required_prompt_sections`), but the `phase_s/PROMPT_SP2` uses a totally different format (SYSTEM/USER/Rules, no Goal/Schema/Anti-Fabrication sections). This is the split-authority drift. Let me verify the section-validation enforcement and the legacy-context injection.

Two important null results:
1. "Legacy Context" is NOT injected anywhere in `run_extraction_v5.py`. The v4 S-prompts reference "Legacy Context" as a guardrail concept ("is intent guidance only and is never evidence"), but no runtime code injects a block named "Legacy Context". Let me check v3/v4 and the wrappers, and grep more broadly (manual dir, etc.).
2. `required_prompt_sections` from promptset.yaml is NOT enforced in v5 or v4 (no grep hits). The promptset declares 9 required sections but nothing validates prompts against them. Let me confirm this across the whole service.

Let me broaden the search.

This sharpens the picture significantly:

1. **"Legacy Context" is referenced in prompts but NEVER injected** — zero hits in any `.py` file (non-test). The v4 S-prompts say "Legacy Context is intent guidance only and is never evidence," referring to a block that runtime never provides. This is dead/stale prompt text — at best harmless, at worst misleading because it implies a context block exists.

2. **`required_prompt_sections` is consumed by v4's `load_promptset()`** (run_extraction_v4.py:103-104) but I need to verify if v4 actually *validates* prompts against the 9 required sections. It's referenced in `lib/promptgen/contract_generator.py:25` (generator-side) and `tests/test_promptset_v4_lint.py`. The promptset.yaml is the v4-contract source. Let me check whether v4 enforces sections and whether v5 (the terminal engine) loads promptset.yaml at all — it appears v5 only loads `PROMPTSET_RULES.md` (run_extraction_v5.py:13885), NOT promptset.yaml. So the section/output contracts in promptset.yaml may not be enforced by the terminal engine.

3. The SP2 prompt has a `FAIL_CLOSED` rule; the v4 S2 prompt does not have an explicit FAIL_CLOSED but references PROMPTSET_RULES.md.

Let me verify: (a) does v4 validate required sections; (b) does v5 consume promptset.yaml's per-step output contracts or only resolve prompts from the filesystem glob; (c) the `phase_s` registry-vs-required-steps mismatch I flagged. Let me trace v5's phase-S resolution wiring concretely.

==========================================================================================
## RTE-CORE S3-prescan  (workflow-subagent, a4602e76d532cab5e, 33872 chars)
==========================================================================================

I'll audit the S3-prescan stage. Let me start by orienting myself in the codebase and verifying the authority map's claims against primary source.

I have the file inventory. The prescan-related files are small and focused. Let me read the core files for the S3-prescan stage. I'll read them in parallel.

I have the core prescan files. Now I need to see the engine (which orchestrates passes and reordering), the grok_passes (the LLM-driven passes), the models (config), and the cost_estimator/provider_catalog (for model-tiering claims). Let me read these.

This is rich. I'm building a clear picture. The prescan stage produces `extraction_hints` (skip lists, model_routing_hints, compress_chains) via LLM "grok passes" and deterministic heuristics. Now I need to verify the critical claims:

1. **Opaque reordering heuristics** — where does prescan output feed back into extraction ordering? I need the `engine.py` and how `extraction_hints` are consumed by the runner.
2. **Unproven net-value** — does the prescan's "savings" / skip-list ever get validated, or is it just trusted?
3. **Model-tiering** — `model_routing_hints` route "high-complexity to premium, boilerplate to economy". Is this LLM-emitted and then trusted blindly?

Let me read the engine and check how the optimize-pass output (skip_list, model_routing_hints) is consumed downstream by the runner. Also `run_repscan.py` and `run_probe.py`.

Now I have a comprehensive picture. Let me drill into the three core audit targets:

1. **Opaque reordering heuristics** — I now see batching groups by `authority_class` then iterates files **in arbitrary input order** within a class. And the `optimize` pass emits `model_routing_hints`, `phase_routing_overrides`, `skip_list`, `compress_chains`. I need to check whether the LLM-emitted `optimize` results (skip_list, model_routing_hints) actually feed back into the deterministic engine/extraction, or whether they're advisory only.

2. **Unproven net-value** — the `CostEstimator` claims "80% reduction for version chains" and "savings_pct" but these are pure heuristics never validated against actuals.

3. **Model-tiering** — `provider_catalog.py` builds the routing plan and "selected_tier"/"tier_adjustment". Let me read that.

Let me also check: how does the engine consume `grok_passes` results (the LLM optimize output)? And verify the `version_chain` ordering bug I suspect.

Now I have a thorough understanding of the prescan stage. The critical questions for my three audit targets are about **net-value proof** and whether the LLM-emitted hints (`skip_list`, `model_routing_hints`, `compress_chains`) get *consumed* downstream by the extraction engine. Let me verify the consumption side — does the v5 runner actually read `extraction_hints` / `grok_passes.optimize.skip_list` and act on it? This determines whether the "opaque heuristics" are merely advisory artifacts or whether they materially gate extraction (and thus whether unproven net-value is a go-live blocker).

Let me grep for consumption of these keys and the `intelligence_router`.

Let me look at how `run_extraction_v5.py` consumes these prescan keys, and what `intelligence_router.py` does (it's imported by the engine and prescan `__init__`). This is the load-bearing question: do the prescan hints gate real extraction?

This is the load-bearing consumption. The v5 runner consumes `prescan.skip_list` for **scope reduction** (8585-8611), `model_routing_hints` and `phase_routing_overrides` (8721-8733), and `compress_candidates` (12042). Let me read these consumption sites closely — especially the scope-reduction one (8585) and the routing-hint one (8721), because these determine whether the opaque/unproven heuristics actually gate live extraction.

This is the crux. Now I can see the consumption clearly:
- `should_skip` + `allow_prescan_scope_reduction` gates whether files are dropped from extraction (8544-8550).
- `tier_override` is **applied** (8739-8741) — partition gets a `premium/standard/economy → synthesis/extract/bulk` tier override that drives model selection.
- `model_routing_hints` is recorded as a label but `does_not_claim_executed_route=True` (8722).
- `phase_routing_overrides` is `applied=False` / `not_consumed_by_v5_partition_execution` (8734).

So the engine has self-aware labels distinguishing applied vs advisory. Now I need the `IntelligenceRouter` itself — `should_skip`, `reorder_partition`, `get_model_tier` — to assess whether the reordering/tiering heuristics are **opaque** and whether net-value is **proven**. Let me read it, plus the `partition_brief_generator` and check how `tier_override` actually changes the model/cost downstream.

Now I have the complete picture of the IntelligenceRouter, which is the heart of the prescan→extraction influence. Several critical observations are crystallizing. Let me note the key findings forming:

1. **`get_model_tier` (740-771)** returns the **raw LLM-emitted string** `hint.get("recommended_model", "standard")` directly as a tier. But the consumer at v5:8700-8712 only matches `"premium"|"standard"|"economy"`. The LLM `model_routing_hints` schema says "route to premium models / economy models" — but `recommended_model` could be an arbitrary model name (e.g. `"gpt-5-pro"`), not one of those three tokens. If the LLM emits a model name, `get_model_tier` returns that name, which won't match any branch at v5:8700 → silently ignored. This is opaque/unproven coupling.

2. **`reorder_partition` (828-834)** sorts by `get_composite_priority`, which defaults to **0.5 for every file not in `processing_order`** (730). Python's `sorted` is stable, so files all at 0.5 keep input order — but any file *in* processing_order jumps ahead. The `processing_order` scores come from `code_intelligence_report.json` with no documented derivation visible here.

3. **`get_model_tier` premium via pagerank (763-769)**: `top_10_pct = scores[max(0, len(scores)//10)]`. This indexes the **sorted-descending** list at position `len//10`, and labels anything `>= top_10_pct` as premium. For small corpora this is degenerate (e.g. 5 scores → index 0 → the max → only the single top file, OR ties promote many). And `model_routing_hints` (LLM) **overrides** deterministic pagerank/hotspot tiering (checked first, 748).

4. **Net-value: never proven.** `estimate_token_savings` and `CostEstimator` produce *estimates* (80% version-chain reduction hardcoded, 0.15 output ratio). Nothing compares prescan's predicted savings against actual post-extraction token spend. The `optimize` pass's `estimated_savings` is just **logged** (v5:7800-7802).

Let me verify the tier→model wiring (does `tier_override` actually change which model runs?) and check the cost_estimator's version-chain claim consumption, plus confirm `should_skip` default-skip risk. Let me look at how `tier_override` maps to models and the partition execution.

Good — scope reduction is **default-off** (`prescan_allow_scope_reduction: bool = False`, 1746) and requires explicit operator opt-in, with `can_influence` gating. That's a fail-closed posture for skipping. Now let me read the `tier_override` → model resolution chain (5019-5040 `classify_step_type`, 5485-5509 `resolve_step_tier`, 5647 `choose_model_for_step`) and the inventory ordering (8505-8538), since that's the **default-on** reordering path. Let me also look at the `_resolve_inventory` ordering and how tier maps to a real model.

Critical confirmation. There are **two distinct tier-override vocabularies and a translation gap**:

- **Deterministic `resolve_step_tier` / `classify_step_type` (5019-5066)** use vocabulary `{bulk, extract, synthesis, qa}` (`_VALID_PROMPT_TIERS`).
- **The router-driven `_apply_router_partition_hints` (v5:8700-8741)** maps router tiers `premium → "synthesis"`, `standard → "extract"`, `economy → "bulk"`, and stores `partition["tier_override"] = highest_tier`. So `premium`/`standard`/`economy` are correctly translated to the valid prompt tiers. Good — no crash there.

But `get_model_tier` in the router (740-771) returns `hint.get("recommended_model", "standard")` — the **raw LLM string**. If the LLM `model_routing_hints` emits `recommended_model: "premium"`, it works. If it emits an actual model name like `"gpt-5-pro"` (which the optimize prompt's directive "Route...to premium models" invites), then `get_model_tier` returns `"gpt-5-pro"`, which does **not** equal `"premium"`/`"standard"`/`"economy"` at v5:8700-8709 → the partition gets **no tier override at all** (highest_tier stays None for that file). So an LLM-emitted model-name hint is silently dropped from tier influence, while the `routing_model_hint` label is still recorded as `applied=True` (8714-8725). That's a label/effect mismatch.

Let me verify `_VALID_PROMPT_TIERS` and confirm the `routing_model_hint` `applied=True` vs actual no-op, and check the schema for what `recommended_model` is expected to contain. Let me also confirm there's NO post-hoc validation that prescan's skip/savings were correct.

Important schema observations:
1. The `extraction_hints.skip_duplicates` schema declares items as **strings** (paths), but `IntelligenceRouter.compress_map` (intelligence_router.py:261) reads `compress_candidates` as **objects** with `chain_id`. The schema allows `oneOf` string|object for compress_candidates, but the router's `compress_map` comprehension (`{c["chain_id"]: c for c in ...}`) will **KeyError/TypeError on a bare string** member. Let me verify that's reachable.
2. The schema has **no definition for `grok_passes`** (the LLM optimize output: `skip_list`, `model_routing_hints`, `compress_chains`, `phase_routing_overrides`). So the most consequential prescan→extraction influence channel (LLM-emitted skip/route/compress) is **entirely unschematized and unvalidated** — `BatchResponseValidator` (grok_passes.py:168-191) only checks `discover.hidden_features` and that `optimize.skip_list` is a list; it never validates `model_routing_hints` or `compress_chains` shape.

Let me verify the `compress_candidates` string-vs-object crash path and check whether the corpus_summary key mismatch (`total_included_size_bytes` in schema/router vs `total_size_bytes` actually emitted by engine) breaks `estimate_token_savings`. Let me also do a quick check of the README/docs claims about net-value and whether any validator proves it. Let me consult the advisor before finalizing — I have substantial findings forming and want a sanity check on severity calibration before I write. Actually, the contract says do NOT use advisor (it consumes the final turn). I'll skip advisor per the explicit output rule.

Let me verify the two suspected crash/no-op paths empirically via AST/grep.

Two confirmations:

1. **Key mismatch confirmed (observed):** `engine.py:725` emits `corpus_summary.total_size_bytes`, but `intelligence_router.py:811` reads `total_included_size_bytes` (also matches the schema's name, but NOT what the engine writes). So `estimate_token_savings` always computes `total_size = 0` → `reduction_pct = 0` always. The router's own savings self-report is dead. (The schema and the engine disagree on the key name; the engine is the canonical writer, so this is real drift.)

2. **`compress_candidates` crash path (observed):** `intelligence_router.py:261` does `{c["chain_id"]: c for c in self.hints.get("compress_candidates", [])}` at `__init__`. The **engine never populates `compress_candidates`** in `extraction_hints` — it only writes `skip_duplicates` and `compression_candidates` (note: `compression_candidates`, engine.py:747, a *different* key, plural-prefix). So for a locally-generated prescan, `compress_candidates` is absent → empty → no crash. But the **schema** (`schemas.py`) declares `compress_candidates` as `oneOf[string, object]`. If an imported prescan (or the optimize pass) provides a **bare-string** member in `compress_candidates`, `c["chain_id"]` raises `TypeError: string indices must be integers` at router construction → the whole extraction crashes. The optimize-pass merge at 296-299 extends `compress_candidates` with `compress_chains` objects, so that path is object-shaped, but the import path trusts the schema which permits strings.

Also note `extraction_hints.compression_candidates` (engine, plural) vs `compress_candidates` (router/schema) — the engine's `compression_candidates` key is **never read** by the router. Dead output.

I now have more than enough verified material. Let me do one final targeted check: confirm there is no net-value validation anywhere (no comparison of predicted vs actual savings/tokens post-extraction) and check the inventory reorder is unconditional/default-on (not gated by the scope-reduction flag), since that's the "opaque reordering, default-on" core finding.

Confirmed:
- **No net-value validation exists anywhere** in the runtime (search returned nothing). Prescan's predicted savings/skip decisions are never reconciled against actual post-extraction token spend or coverage.
- **Reordering is default-on:** when `active_router` is truthy (a valid local or accepted-imported prescan), inventory is re-sorted by `get_routing_priority` (8530-8536) and partitions are re-sorted by `get_composite_priority` (8662) **unconditionally** — NOT gated by `prescan_allow_scope_reduction`. Only file *dropping* is gated. So order-of-extraction (which affects partition packing, char-budget boundaries, and therefore which files land together in an LLM call) is silently mutated whenever a prescan is present.
- The composite priority is `pagerank*0.4 + entry_proximity*0.3 + hotspot_score*0.3` (code_intelligence_report.py:267) — a fixed, undocumented weighting. `get_routing_priority` (router 719-725) uses a *different* heuristic (`50 + (100 - min(topo_index, 50))`). So inventory-level reorder and partition-level reorder use **two different, uncoordinated priority functions**.

Let me grab the composite-priority weighting block and the README's claims about prescan value to finalize the "unproven net-value" and "opaque heuristic" findings with exact line cites.

I have everything I need, verified at file:line. The docstring confirms the composite-priority weighting is hardcoded with two arbitrary regimes (`0.4/0.3/0.3` churn-on, `0.55/0.45` churn-off), and `hotspot_score` itself is min-max normalized to the top file (185-196), making it corpus-relative and non-portable across runs/repos.

One last check: the `hotspot_score` raw derivation and whether `use_churn` toggles silently between the two weighting regimes (which would make priority non-reproducible depending on git availability). Let me grab the hotspot raw-score formula and the `use_churn` determination quickly, then write findings.

Final confirmation. `use_churn = git_depth == "full"` (line 83). So whether the priority/tiering uses `churn×complexity` (full git) vs `complexity-only` (shallow git) flips silently based on the operator's git clone depth — making prescan-derived ordering and premium-tier selection **non-reproducible across environments** (shallow clone, CI, fresh checkout all differ). The `hotspot_score >= 0.7 → premium` threshold (router 759) is applied to a corpus-relative min-max-normalized score (line 196), so the *same file* can be premium in one repo slice and not in another.

I have a complete, verified picture across all three audit targets plus collateral findings. The deliverable is the findings list itself (no file to persist per output rules). Writing final output now.

# STAGE S3-prescan — Audit Findings

Scope audited: `run_prescan.py`, `lib/prescan/*` (engine, code_prescan, batch_planner, classifier, duplicate_detector, cost_estimator, grok_passes, provider_catalog, token_counter, models, schemas), `lib/intelligence_router.py`, `run_repscan.py`, `run_probe.py`, plus the v5 consumption sites (`run_extraction_v5.py:7798-8760, 5019-5066, 1746`). Authority-map claims that prescan tooling is layered on v5 and that v3 is the legacy/shadow engine were **verified**: `run_repscan.py:72` delegates to v3; `run_probe.py:45` loads v3; `lib/prescan/provider_catalog.py:34` imports `run_extraction_v5`. The S3-prescan engine itself (`lib/prescan/engine.py`) is engine-agnostic and feeds both via `IntelligenceRouter`.

Theme verdict: the three flagged concerns are all **real and substantiated**. Opaque reordering is default-on and uncoordinated; net-value is asserted by heuristic and never validated against actuals; model-tiering mixes an LLM free-text channel with an environment-dependent deterministic channel. Several are latent correctness bugs, not just transparency gaps.

---

- **[S3-01] HIGH — Prescan reordering is default-on, uncoordinated across two priority functions, and silently mutates LLM call composition**
  - files: `run_extraction_v5.py:8528-8538` (inventory reorder), `run_extraction_v5.py:8662` (partition reorder), `lib/intelligence_router.py:719-725` (`get_routing_priority`), `lib/intelligence_router.py:727-730,828-834` (`get_composite_priority`/`reorder_partition`)
  - evidence: observed. When `active_router` is truthy (any valid local prescan or accepted import), inventory is re-sorted by `get_routing_priority` and each partition by `get_composite_priority` **unconditionally** — this path is NOT gated by `prescan_allow_scope_reduction` (that flag only gates file *dropping*, `:8545`). The two reorder stages use **different, uncoordinated heuristics**: inventory-level uses `50 + (100 - min(topo_index,50))` (router `:721-724`); partition-level uses `code_intelligence_report.processing_order` scores (router `:729-730`). Reordering changes which files accumulate into each char-budgeted partition (`:8552-8562`), hence which files share a single LLM context — a material extraction-content change, not cosmetic.
  - why it matters (bounds go-live): extraction output can differ run-to-run for the same corpus purely because a prescan artifact is present vs absent, with no operator opt-in for the reorder behavior and no single documented ordering contract. For a "fail-closed, deterministic, replayable" pipeline (AGENTS.md doctrine), an always-on, dual-heuristic reorder that alters partition packing is a determinism/auditability hazard. Bounds go-live to "prescan-absent" or "operator accepts non-deterministic ordering" lanes.
  - falsifying check: run `_build_partitions_for_phase` (the `:8495` function) twice on identical inventory — once with `router=None`, once with a router whose `processing_order`/`topo_index` reorder ≥1 file — and diff partition `paths`/`id` assignment. If partition membership is identical in both, the finding is disproven.

- **[S3-02] HIGH — Net token/cost "savings" are heuristic-only and never validated against actuals (unproven net-value)**
  - files: `lib/prescan/cost_estimator.py:41-49` (hardcoded 80% version-chain reduction, 0.15 output ratio, 3.5 chars/token), `lib/intelligence_router.py:808-826` (`estimate_token_savings`), `run_extraction_v5.py:7798-7802` (optimize-pass `estimated_savings` only logged)
  - evidence: observed. A repo-wide search for any reconciliation of predicted vs realized savings (`actual_savings|realized_savings|savings_validat|reduction_realized|prescan.*accuracy`, excluding tests) returned **nothing**. `CostEstimator.estimate` asserts "version chain compression (estimated 80% reduction)" (`:41-44`) and "Blended ~15% output ratio" (`:48-49`) as fixed constants. The optimize pass's `estimated_savings` is read at `run_extraction_v5.py:7802` and only passed to a log/record call — never checked post-extraction.
  - why it matters (bounds go-live): the prescan's central justification (skip/compress to save tokens) is an unfalsified claim. Operators cannot see whether prescan actually reduced spend or whether it dropped/compressed content that the extraction needed. Combined with S3-04 (default-on skip when enabled) this is a value-and-safety gap. Does not by itself block a prescan-absent go-live; blocks any claim that prescan delivers measured net value.
  - falsifying check: locate any artifact or code path that records realized extraction token usage and diffs it against `cost_estimate.net_estimates` or `optimize.estimated_savings` for the same run. If such a reconciliation exists and emits a PASS/FAIL, the finding is disproven.

- **[S3-03] HIGH — Model-tier routing trusts raw LLM free-text and mixes it with an environment-dependent deterministic heuristic; LLM-emitted model names are silently dropped while labeled `applied=True`**
  - files: `lib/intelligence_router.py:740-771` (`get_model_tier` returns `hint.get("recommended_model","standard")` verbatim), `run_extraction_v5.py:8700-8712` (only `premium|standard|economy` are honored), `run_extraction_v5.py:8714-8725` (`routing_model_hint` recorded `applied=True`), `lib/prescan/grok_passes.py:147-159` (optimize prompt directive "Route…to premium models…economy models"), `lib/prescan/grok_passes.py:168-191` (validator never checks `model_routing_hints` shape)
  - evidence: observed. `get_model_tier` returns the LLM's `recommended_model` string unmodified. The consumer at `:8700-8709` matches only `"premium"/"standard"/"economy"`; any other value (e.g. an actual model id like `gpt-5-pro`, which the prompt at `grok_passes.py:153` actively invites — "Route…to premium models") yields no tier override for that file. Yet `_apply_router_partition_hints` still emits a `routing_model_hint` label with `applied=True` (`:8718`) whenever `routing_hint_values` is non-empty (`:8714`), even though the tier effect was a no-op. `BatchResponseValidator.validate` (`grok_passes.py:178-191`) validates only `discover.hidden_features` and that `optimize.skip_list` is a list — `model_routing_hints` is entirely unvalidated.
  - why it matters (bounds go-live): the audit label claims an influence that did not occur (`applied=True` for a dropped hint) — directly violating proof-truthfulness. The model-tiering is opaque (free-text from a model, no schema), and the deterministic fallback is non-reproducible (see S3-05). For an auditable pipeline this is a misleading-success/observability defect on a contract-sensitive surface (proof labels).
  - falsifying check: construct `prescan_intelligence.grok_passes.optimize.model_routing_hints=[{"partition_pattern":"*.py","recommended_model":"gpt-5-pro"}]`, run `_apply_router_partition_hints` over a partition of `.py` files, and inspect emitted labels + `partition["tier_override"]`. If the label reports `applied=False`/no-op OR the tier override is actually set to a synthesis/extract/bulk value, the mismatch is disproven.

- **[S3-04] MED — LLM-emitted `optimize.skip_list` is merged into the live skip set with no schema validation of its contents**
  - files: `lib/intelligence_router.py:283-293` (merge `optimize.skip_list` into `self.skip_list`), `lib/intelligence_router.py:704-706` (`should_skip`), `run_extraction_v5.py:8544-8550` (skip gated by `allow_prescan_scope_reduction`), `lib/prescan/grok_passes.py:186-189` (validator only asserts list-ness)
  - evidence: observed. `optimize.skip_list` (LLM output) is unioned into the skip set at `:287`. `should_skip` then drops those paths from extraction when the operator passes `--prescan-allow-scope-reduction`. The only validation is "`skip_list` must be a list" (`grok_passes.py:188`) — no check that members are real corpus paths, no confidence floor, no cross-check that the LLM-skipped file is actually a confirmed duplicate/ghost. Mitigation present: skipping is default-OFF (`run_extraction_v5.py:1746`, `prescan_allow_scope_reduction=False`) and requires `can_influence_execution`.
  - why it matters (bounds go-live): when an operator enables scope reduction, an unconstrained LLM list can silently exclude canonical files from truth extraction with no per-path evidence requirement. The default-off posture is the only thing keeping this fail-closed. Bounds the "prescan + scope-reduction" lane to attended use until skip provenance is enforced.
  - falsifying check: feed `optimize.skip_list=["does/not/exist.py","CLAUDE.md"]`, build the router, call `should_skip("CLAUDE.md")`. If it returns False (i.e., LLM skips are filtered against confirmed-duplicate/ghost evidence before entering `skip_list`), the finding is disproven.

- **[S3-05] MED — Hotspot/priority scores are corpus-relative and git-depth-dependent → tiering and ordering are non-reproducible across environments**
  - files: `lib/prescan/code_intelligence_report.py:83` (`use_churn = git_depth == "full"`), `:173-196` (raw `churn*complexity` vs complexity-only, then min-max normalize to top file), `:267-294` (composite weighting `0.4/0.3/0.3` vs `0.55/0.45`), `lib/intelligence_router.py:754-769` (`hotspot_score>0.7`/top-10%-pagerank → `premium`)
  - evidence: observed. `use_churn` flips on whether the git clone is full-depth (`:83`). With churn off, hotspot becomes complexity-only (`:176-178`) and the composite weighting changes regime (`:294`). Hotspot scores are then min-max normalized against the single top file (`:193-196`), so the `>0.7→premium` threshold (router `:759`) is relative to corpus composition, not absolute. PageRank-premium uses `top_10_pct = scores[max(0,len//10)]` (router `:766`), degenerate for small corpora (e.g. <10 files → index 0 → only the max qualifies, or ties promote many).
  - why it matters (bounds go-live): the same file can be "premium" (routed to expensive synthesis-tier models, raising cost) in a full clone and "standard" in a shallow/CI clone, and partition ordering shifts accordingly — defeating replayability and making cost non-deterministic. Bounds go-live where reproducible cost/tiering is required.
  - falsifying check: run `CodeIntelligenceBuilder.build` on the same corpus with `git_depth="full"` vs not, and diff `pagerank_scores`/`hotspots`/`processing_order` and the resulting per-file `get_model_tier`. Identical results disprove it.

- **[S3-06] MED — `IntelligenceRouter.estimate_token_savings` reads a corpus_summary key the engine never writes → always reports 0% reduction (silent dead self-report)**
  - files: `lib/intelligence_router.py:810-819` (reads `corpus_summary.total_included_size_bytes`), `lib/prescan/engine.py:719-727` (engine writes `corpus_summary.total_size_bytes`)
  - evidence: observed. Engine's canonical `_build_intelligence_base` emits `"total_size_bytes"` (engine `:725`). Router reads `stats.get("total_included_size_bytes", 0)` (router `:811`). The keys differ; the engine is the canonical writer, so `total_size` is always `0` → `reduction_pct` is always `0.0` (router `:819`). The prescan schema (`schemas.py`, `corpus_summary.total_included_size_bytes`) matches the router, not the engine — so schema and runtime disagree, and runtime (engine) is authoritative.
  - why it matters (bounds go-live): a savings-reporting surface is silently broken — reinforces S3-02 (the one in-code attempt to quantify savings returns a constant 0 regardless of how many files are skipped). An operator reading this number is misled. Low blast radius (advisory metric) but a correctness defect on the value-reporting path and a schema/runtime drift.
  - falsifying check: call `router.estimate_token_savings(manifest)` on a corpus with a non-empty `skip_list` and ≥1 skipped file present in `manifest`. If `estimated_reduction_pct > 0`, the key-mismatch is disproven.

- **[S3-07] MED — `compress_candidates` schema permits bare strings, but `IntelligenceRouter.__init__` indexes them as objects → `TypeError` crashes router construction on a schema-valid imported prescan**
  - files: `lib/intelligence_router.py:261` (`{c["chain_id"]: c for c in self.hints.get("compress_candidates", [])}`), `lib/prescan/schemas.py` (`extraction_hints.compress_candidates` declared `oneOf:[string, object]`), `lib/prescan/engine.py:746-751` (engine emits `skip_duplicates` + `compression_candidates`, never `compress_candidates`)
  - evidence: observed. Router constructor unconditionally subscripts `c["chain_id"]` over every `compress_candidates` member (`:261`). The schema explicitly allows string members (`schemas.py` `oneOf`). A string member → `TypeError: string indices must be integers`. Locally-generated prescans dodge this because the engine writes the *differently named* key `compression_candidates` (engine `:747`, never read) and leaves `compress_candidates` absent; but `from_dir`/`load_imported` (`:638-702`) loads `prescan_intelligence.json` verbatim and trusts schema-shaped input. Note also the dead-key drift: engine writes `compression_candidates`, router/schema use `compress_candidates` — the engine's compression hint output is never consumed.
  - why it matters (bounds go-live): an imported prescan artifact that conforms to the published schema (string-form compress candidates) hard-crashes the router at construction, taking down extraction — a fail-open-to-crash on a contract-sensitive surface (the import boundary). Bounds the imported-prescan lane.
  - falsifying check: construct `IntelligenceRouter({"extraction_hints":{"compress_candidates":["docs/old.md"]}})`. If it does not raise `TypeError`, the finding is disproven.

- **[S3-08] LOW — `run_prescan.py --no-code/--no-git/--no-cost-estimate/--no-batch-mode` flags are dead (paired `store_true` defaults make the positive flag always True)**
  - files: `run_prescan.py:70-129` (`--code default=True`, `--git default=True`, `--cost-estimate default=True`, `--batch-mode default=True`), `:183-188` (config uses `args.code and not args.no_code`, etc.)
  - evidence: observed. Each capability flag is `action="store_true", default=True`, so it is always `True`. The config expression `args.code and not args.no_code` (`:183`) does correctly let `--no-code` win, so the negative flags *do* work — but the positive flags are inert and the help text "[default: enabled]" plus a redundant positive flag is misleading. (Re-examined: the `--no-*` flags are functional via the `and not` guard; the defect is the useless positive flags + confusing CLI surface, hence LOW not MED.)
  - why it matters: minor operator-UX/clarity issue; no correctness impact on the disable path. Does not bound go-live.
  - falsifying check: `python run_prescan.py --help` and confirm both `--code` and `--no-code` exist with `--code` defaulting enabled; then verify `--no-code` flips `enable_code_prescan` False. Already consistent with code at `:183`.

- **[S3-09] OBS — Prescan influence is self-labeled with honest `applied`/`does_not_claim_executed_route`/`not_consumed_by_v5_partition_execution` markers (positive control)**
  - files: `run_extraction_v5.py:8722` (`does_not_claim_executed_route=True` on model hints), `:8734` (`runtime_consumer="not_consumed_by_v5_partition_execution"` on phase hints), `lib/intelligence_router.py:399-433` (`can_influence_execution`, `available_influence_classes`), `:497-636` (import freshness gating: repo/source/corpus-hash/git-sha must match or artifact is `rejected_stale`/advisory-only)
  - evidence: observed. The runtime distinguishes applied vs advisory influence and gates imported prescans on a corpus-manifest-hash identity match (`:609`), failing closed to `advisory_only` on any mismatch or missing metadata (`:578-587`). `phase_routing_overrides` is correctly marked non-consumed (`:8734`). This is good fail-closed design and partially mitigates S3-01/S3-04 — but it does NOT fix S3-03's `applied=True`-on-no-op label, which contradicts this otherwise-honest scheme.
  - why it matters: documents that the influence-labeling framework is largely trustworthy; the S3-03 mislabel is the exception that should be corrected to preserve it.
  - falsifying check: n/a (positive observation).

---

## Validation Performed
- **PASS (static, observed at file:line):** all findings above are grounded in read source + `rg` confirmation of key mismatches (`total_size_bytes` vs `total_included_size_bytes`), tier vocabularies (`_VALID_PROMPT_TIERS={bulk,extract,synthesis,qa}` at v5:1383), consumption gating (`prescan_allow_scope_reduction=False` default at v5:1746), and absence of any predicted-vs-actual savings reconciliation (empty search result).
- **NOT_RUN (requires execution; barred by read-only contract):** the falsifying checks in S3-01, S3-03, S3-04, S3-06, S3-07 each name an exact constructor/function call to confirm at runtime. Residual risk: a caller upstream of `IntelligenceRouter.__init__` might pre-sanitize `compress_candidates` (S3-07) or filter `skip_list` (S3-04) before the router sees it; I found no such sanitizer in `lib/prescan/*`, `intelligence_router.py`, or the v5 load sites (`from_dir`/`load_imported`), but did not exhaustively trace every v5 import entry point (888k-line file). Human-verify command for S3-07: `cd services/repo-truth-extractor && python -c "from lib.intelligence_router import IntelligenceRouter; IntelligenceRouter({'extraction_hints':{'compress_candidates':['x.md']}})"` (expect `TypeError`).

## Remaining Uncertainty
- I did not trace whether any v5 caller validates `model_routing_hints`/`compress_candidates`/`skip_list` shape *before* router construction (searched the prescan lib and the router; none found there). If such validation exists elsewhere in v5, S3-03/S3-04/S3-07 severities drop.
- `processing_order` is truncated to top-100 (`code_intelligence_report.py:165`); files beyond rank 100 fall to the 0.5 default in `get_composite_priority`, so partition reorder (S3-01) only perturbs the top-100 plus their stable-sort interaction — I did not quantify the magnitude of reorder on a real corpus (NOT_RUN).

## Authority Used
Runtime code (canonical, per Truth Order): `lib/prescan/*`, `lib/intelligence_router.py`, `run_extraction_v5.py`, `run_prescan.py`, `run_repscan.py`, `run_probe.py`. Schema (`lib/prescan/schemas.py`) treated as subordinate to engine output where they disagree (S3-06, S3-07). No reliance on README claims for findings.

==========================================================================================
## RTE-CORE S4-integration  (workflow-subagent, ac6ed2405c8cbec57, 32759 chars)
==========================================================================================

I'll audit STAGE S4-integration: phase coupling and the registry-bootstrapping paradox in `phases.py`, `rte_phase_wrappers.py`, and the `PHASE_*.md` docs. Let me start by orienting myself to the files.

Now let me read the three core files in full: `phases.py`, `rte_phase_wrappers.py`, and the two small Phase S/T docs (which the authority map flagged as having a separate registry).

I have the three core files. The authority map flagged a "registry-bootstrapping paradox" and a separate Phase S/SP registry (`prompts/phase_s/registry.json`). Let me verify the registry files and how the wrappers connect to runtime (v5) and the prompt registry. This is the crux of my stage.

Now I have the registry-bootstrapping paradox in view. Key observations forming:

1. **`phases.py:198`** declares `REQUIRED_PROMPT_STEP_IDS["SP"] = set(PHASE_SP_BASE_STEPS)` = `{SP0..SP12}` (13 steps).
2. The **`prompts/phase_s/registry.json`** declares `"phase": "SP"` but lives in a directory named `phase_s`, and the docs are split: `PHASE_S_SYSTEM_TRUTHS_GPT52.md` describes Phase S steps S1/S2, while the registry/prompts inside are all SP* steps.
3. The validator (`rte_promptset.py:validate_phase_s_registry`) **requires the registry's observed steps to exactly equal `REQUIRED_PROMPT_STEP_IDS["SP"]`** — meaning the JSON file's contents must match the Python constant exactly, or it fails closed. That's the bootstrapping coupling.

Let me verify the exact coupling: how the SP steps are enumerated, whether the file's steps match `phases.py` exactly, and how `phases.py` `PhaseId.S` vs `PhaseId.SP` map to dir names and the `phase_s` directory. Let me also check the v5 call sites that consume these.

Confirmed: the `phase_s/registry.json` steps exactly match `phases.py`'s `REQUIRED_PROMPT_STEP_IDS["SP"]`. The validator enforces this equality (fail-closed). Now let me examine the critical coupling points more precisely:

1. The `phase_s_registry_dir`/`phase_s_registry_path` builders in `rte_promptset.py` (the dir is named `phase_s` but declares phase `SP`).
2. The Phase S→SP relationship: `phases.py` has BOTH `S` (`S_synthesis`) and `SP` (`SP_synthesis_pipeline`) as distinct phases, both depending on `R`. Let me see how the wrappers (`plan_s_phase` reads `dirs["S"]`? No — it reads `dirs["R"]`, `dirs["X","T","Z"]`, and `dirs["root"]`) and how `dirs` is populated, plus whether S and SP both run.

Let me read the v5 call sites and the registry path/dir builders.

Now I see the full picture of the registry-bootstrapping paradox. Let me read the `resolve_phase_s_prompts` and `resolve_phase_sp_prompts` functions (lines 291-410 in rte_promptset.py) to understand how the SP-declared registry serves BOTH Phase S and Phase SP prompt resolution. This is the heart of my stage.

Now I have the complete picture of the registry-bootstrapping paradox and the S/SP coupling. Critical findings crystallizing:

**The paradox**: `resolve_phase_s_prompts` (Phase S, "registry" mode) loads `load_phase_s_registry()` — which loads `prompts/phase_s/registry.json` declaring `phase: "SP"` with steps `SP0..SP12`. So when Phase **S** runs in registry mode, it resolves **SP-prefixed prompts** (line 327-328 iterates `registry.keys()` which are all `SP*`), and the contract dispatch at line 347 checks `startswith("SP")` → routes everything to the `SP` contract. There are NO `S0..S12` entries in the registry. So Phase S in registry mode actually executes the SP step set.

Let me verify a few remaining things: (1) how v5 dispatches Phase S vs SP (do both run, or is S the registry-mode alias for SP?); (2) the `step_contract_for` and whether `S` contract is ever reachable; (3) whether `dirs` includes both "S" and "SP" keys so the wrappers can read them. Let me read the v5 dispatch around 21240-21300 and the contract lookup.

Now I have a clear comment at v5:21245 confirming the S/SP relationship: "S_PROMPTS_MODE=legacy (V4 prompts; SP phase for registry pipeline)" and v5:21288 "S_PROMPTS_MODE=registry (SP pipeline prompts)". So:

- **Phase S** = legacy V4 prompts (S0..S12 from `promptsets/v4/prompts/`)
- **Phase SP** = registry pipeline prompts (SP0..SP12 from `prompts/phase_s/registry.json`)

But the prompt resolver dispatch at v5:6611-6617 is keyed on something. Let me read 6585-6620 and 17575-17595 to confirm the actual dispatch logic, plus verify `step_contract_for("S",...)` reachability. This determines whether the registry-mode `resolve_phase_s_prompts` path (which would resolve SP prompts under phase "S") is actually live or dead.

Now I have the critical paradox confirmed. Let me nail down the live default and the contract dispatch consequence:

- `_ACTIVE_S_PROMPTS_MODE = S_PROMPTS_LEGACY` (v5:1382) — default mode is **legacy**.
- `get_phase_prompts("S")` → `_resolve_phase_s_prompts(get_active_s_prompts_mode())`. In default (legacy) mode, returns `legacy_phase_prompt_specs("S")` → S0..S12 from `promptsets/v4/prompts/`.
- BUT if `REPO_TRUTH_EXTRACTOR_S_PROMPTS_MODE=registry` is set, `resolve_phase_s_prompts` enters the registry branch (rte_promptset.py:314), loads the `phase: "SP"` registry, and resolves **SP0..SP12** prompts — under phase "S". The contract dispatch at rte_promptset.py:347 routes them to the "SP" contract. So **Phase S in registry mode silently becomes the SP pipeline**, while emitting under the `S` phase id/dir (`S_synthesis`).

Let me verify the remaining coupling questions: (1) what `S_PROMPTS_MODES` allows and whether `registry` is a valid value for Phase S; (2) the `_validate_s_steps` constraint (S0-S12 only) vs registry returning SP* — does selecting `--s-steps` while in registry mode break, since registry returns SP* but the selector validates S*?; (3) confirm `step_contract_for("S", ...)` — whether a real S contract exists or it's vestigial. Let me also check the registry's `phase_s_int` (a different sub-pipeline) to not conflate.

Now let me read the `_step_contract_for` impl in v5 and the `get_active_s_prompts_mode` / `_set_active_s_prompts_mode` to confirm the `auto` mode resolution, plus check the contract definitions for S vs SP. This determines whether the S-contract is reachable/defined or vestigial, and whether `auto` mode resolves to registry (making the paradox the default path).

Now I understand `auto` mode handling: in `resolve_phase_s_prompts`, `normalized_mode == legacy_mode` returns legacy; otherwise (auto OR registry) it tries the registry. The difference between `auto` and `registry`: on registry-load failure, `auto` falls back to legacy (rte_promptset.py:319), `registry` hard-fails (line 317). So **both `auto` and `registry` modes for Phase S resolve SP* prompts from the SP-declared registry**.

Let me confirm the `get_step_contract` for "S" vs "SP" (whether an S contract exists at all), and verify the `_validate_s_steps` / `--s-steps` interaction with registry mode (the S0-S12 selector vs SP* registry output — a real coupling defect). Let me also check how `selected_step_ids` filtering at v5:17578 interacts when registry returns SP* but `cfg.selected_s_steps` contains S*.

This confirms a concrete coupling defect. Let me read `lib/phase_contract_map.py` to see whether `S` and `SP` contracts both exist, and confirm the `--s-steps` × registry-mode collision precisely. The filter at v5:17572-17577 raises `RuntimeError` if a requested step isn't in `prompt_map`. So if `--s-steps S1` is set (validated as S0-S12 OK) AND mode is registry/auto, `get_phase_prompts("S")` returns SP* specs → `prompt_map` keys are SP* → `S1` is "missing" → **hard RuntimeError**. Let me verify the contract map and confirm S-phase prompts existence in v4 (so legacy mode actually works).

Now I understand the contract source. The contract map is built ONLY from `repo_truth_map.json` JSON-managed steps (scope = `json_managed_only`, line 376). Phase S/SP steps are markdown-only (their registry `schema_path: null` for most, outputs are `.md`), so `get_step_contract("S",...)` and `get_step_contract("SP",...)` likely return `None` for most steps. The `_step_contract_for` catches exceptions and returns None. So the contract dispatch at rte_promptset.py:347 (`"SP" if startswith("SP") else "S"`) is largely vestigial for markdown steps — but matters for SP4/SP5/SP7+ which DO have `schema_path` (JSON outputs).

Let me verify: (1) whether SP4/SP5/etc. are in `repo_truth_map.json` under phase "SP" (so their contracts resolve), and whether phase "S" steps S0-S12 exist there too; (2) confirm v4 S-prompts exist so legacy mode works. Then check the registry validator's `is_within` and the v4 promptset.yaml for SP coverage. Let me also verify the `phase_s_int` (S16-S20) — a THIRD S-family — to map the full fragmentation.

Now the fragmentation is fully mapped and it's significant. Critical asymmetry confirmed:

- **`repo_truth_map.json`** (contract source): has 13 `S` steps (S0-S12), **ZERO `SP` steps**.
- **`promptset.yaml`** (v4 contract): has `S` phase (S0-S12), **NO `SP` phase**.
- **`phase_s/registry.json`** (registry-mode source): declares `phase: "SP"` with SP0-SP12, **NO S steps**.

So the contract dispatch in `resolve_phase_sp_prompts` calls `step_contract_for("SP", step_id)` for every SP step → but NO `SP:*` key exists in the contract map → **all SP contracts resolve to `None`**. Meanwhile `resolve_phase_s_prompts` in legacy mode resolves `S:*` contracts which DO exist. This means the registry (SP) pipeline runs **without any phase-contract enforcement** (no required_fields, no schema_aliases, no lane class), while legacy (S) runs **with** contracts.

This is a material go-live finding. Let me do final verification: (1) confirm SP4/SP5/SP7 have `schema_path` set (JSON outputs that SHOULD have contracts but don't), (2) confirm there's no `SP` alias mapping that would let `SP:SP4` resolve to `S:S4`, (3) check the dependency-DAG consistency between `phases.py` (S deps `R`; SP deps `R`) and the registry's `input_phase_ids`/`prior_step_ids`. Let me verify these then write findings.

I now have everything needed. Let me do two final confirmations to make the findings airtight: (1) verify the contract-map `lru_cache` argument behavior (whether `get_step_contract` with `emit_warnings=False` vs the `write_phase_contract_map` with `emit_warnings=True` produce two cached payloads — relevant to the warning suppression claim), and (2) confirm the `plan_t_phase` / `plan_s_phase` wrappers read `dirs["R"]` but `phases.py` declares T requires `("R","X")` and S requires `("R",)` — checking the wrapper-vs-DAG consistency for the "phase coupling" goal. Let me also confirm there's no `M` phase definition in `PHASE_DEFINITIONS` despite `M` appearing in `REQUIRED_PROMPT_STEP_IDS` (phases.py:199).

Let me read the canonical phase ordering (v5:18259) to confirm whether S precedes Z (which would make S's optional read of Z's `norm` outputs structurally impossible in a single forward run), and confirm the `M` phase orphan's blast radius.

I have enough to characterize the ordering question. The phase execution order is driven per-invocation (operator selects `--phase`), not a single hardcoded forward sequence in these files; `plan_s_phase`'s reads of Z/T/X `norm` are *optional* (guarded by `.exists()`), so a missing Z dir is tolerated, not a crash. I'll characterize the S-reads-Z relationship as a soft ordering coupling (OBS), not a CRIT, since the wrapper fails-open on absence by design.

I have a complete, verified map of the S4-integration stage. Let me confirm the M-phase orphan blast radius (one more quick check) then write findings.

I have everything. The `M` phase appears in `PREMIUM_SYNTHESIS_PHASES`/`OPTIMAL_NO_CODE_PHASES` routing sets (v5:1151, 1222) and `REQUIRED_PROMPT_STEP_IDS["M"]` (phases.py:199), but is NOT in the `PhaseId` enum, `PHASE_DEFINITIONS`, `PHASE_DIR_NAMES`, or `VERIFY_PHASE_CHOICES` — so it has no dir, no deps, and cannot be selected/dispatched. It's a dangling phase identity.

All claims are verified against primary source. Writing final findings.

---

# RTE STAGE S4-INTEGRATION — FINDINGS

**Scope audited:** `phases.py`, `rte_phase_wrappers.py`, `PHASE_*.md` (all 8), plus the coupling surfaces required to verify them: `rte_promptset.py` (registry resolution), `run_extraction_v5.py` (phase dispatch, prompt resolution, step filtering), `lib/phase_contract_map.py` (contract source), `prompts/phase_s/registry.json` + sibling registries, `promptsets/v4/promptset.yaml`, `reports/repo_truth_map.json`, `rte_config.py`. HEAD `755bf38460`. Read-only; no pipeline executed.

**Authority-map claims I verified as TRUE:** (a) `phases.py` is canonical for phase IDs/dirs/DAG/`REQUIRED_PROMPT_STEP_IDS` and v5 imports it directly (v5:58, 185+); (b) Phase S/SP use a separate registry `prompts/phase_s/registry.json` declaring `phase: "SP"` (rte_promptset.py:65-89, registry version=1); (c) only v5 (+tests) imports `phases.py`/`rte_phase_wrappers.py` — no other runtime consumer. The map's framing of "Phase S/SP forks to a JSON registry" is correct but understates the coupling defects below.

---

- **[S4-CRIT-1] CRIT — Phase-S "registry"/"auto" mode silently swaps the entire step set from S0–S12 to SP0–SP12 while still writing under the `S` phase id and `S_synthesis` dir**
  - files: `run_extraction_v5.py:6612-6618` (`get_phase_prompts("S")` → `_resolve_phase_s_prompts(get_active_s_prompts_mode())`); `rte_promptset.py:311-352` (`resolve_phase_s_prompts`: legacy → `legacy_phase_prompt_specs("S")`; else loads SP registry and iterates `registry.keys()` = SP0..SP12); `prompts/phase_s/registry.json` (declares only SP* steps); `phases.py:152-158` (`PhaseId.S` dir_name=`S_synthesis`)
  - evidence: observed. `get_active_s_prompts_mode` defaults to `legacy` (v5:1382 `_ACTIVE_S_PROMPTS_MODE = S_PROMPTS_LEGACY`), but `DOPEMUX_S_PROMPTS` env (rte_config.py:21) accepts `auto`/`registry` (rte_config.py:28). In `resolve_phase_s_prompts`, any non-legacy mode (`auto` OR `registry`) takes the registry branch (rte_promptset.py:311 inverts only on `== legacy_mode`) and resolves SP prompts. Confirmed registry contains exactly `{SP0..SP12}` and zero S steps (python load). Phase id passed to `_run_phase_inner` is still `"S"` (v5:21270), so outputs land in `S_synthesis/`, not `SP_synthesis_pipeline/`.
  - why it matters (blocks/bounds go-live): the *same* `--phase S` invocation produces two structurally different artifact sets (S-named markdown vs SP-named pipeline outputs incl. JSON) depending solely on an env var, both written to the `S_synthesis` directory. Downstream consumers keyed on `S_synthesis/norm/*` (e.g. nothing reads S as an input phase — see DAG — but proof/coverage rollups enumerate `REQUIRED_PROMPT_STEP_IDS["S"]` = S0..S12 at v5:18263-18264) will see SP* artifacts that don't match the required S* step ids → coverage/proof step-id mismatch. This is exactly the "two engines emit proof bundles" hazard the authority map flagged, but *within one phase id*. Go-live must pin `DOPEMUX_S_PROMPTS=legacy` or the S-phase artifact identity is non-deterministic w.r.t. environment.
  - falsifying check: `DOPEMUX_S_PROMPTS=registry python -c "import run_extraction_v5 as r; print([s.step_id for s in r.get_phase_prompts('S')])"` — if it prints `S0..S12` (not `SP0..SP12`), the swap does not occur and this is disproven. (NOT_RUN here: import executes module-level code; run under the human-verify harness.)

- **[S4-CRIT-2] CRIT — SP pipeline runs with ZERO phase-contract enforcement: every `step_contract_for("SP", …)` resolves to `None` because `repo_truth_map.json` and `promptset.yaml` define phase `S` but no phase `SP`**
  - files: `rte_promptset.py:346-349` (S path: `"SP" if step_id.startswith("SP") else "S"`) and `rte_promptset.py:380` (SP path: `step_contract_for("SP", step_id)`); `lib/phase_contract_map.py:376` (`"scope": "json_managed_only"`), `:306` (steps built only from `repo_truth_map.json` scope), `:392-399` (`get_step_contract` keys `PHASE:STEP`); `reports/repo_truth_map.json` (S=13 steps, **SP=0**); `promptsets/v4/promptset.yaml` (phases include `S`, **not `SP`**)
  - evidence: observed. Phase histogram of `repo_truth_map.json`: `S:13`, no `SP` key; `promptset.yaml` phases list has `S` but no `SP` (both via python load). The contract map is compiled exclusively from `repo_truth_map.json` JSON-managed steps (`_repo_truth_scope_by_key`, line 268-273; `steps_payload[f"{phase}:{step}"]`, line 344). Lookup key for SP is `SP:SP4` etc., which is absent → `get_step_contract` returns `None` (line 398-399), swallowed by `_step_contract_for` (v5:5140-5145). No SP→S alias exists (`rg` for any remap returned nothing). SP4/SP5/SP7–SP12 declare real JSON outputs with `schema_path` (registry: `SP4_TRUTH_PACK_INDEX.json` schemas/SP4.json, etc.) yet get `contract=None`.
  - why it matters (blocks/bounds go-live): in the registry pipeline (the one the SP phase is *for* — v5:21288 "registry pipeline prompts"), 9 SP steps emit JSON artifacts but carry no contract → no `required_fields`, no `canonical_schema_id`/`schema_aliases`, no lane class, no strict-schema gate. The fail-closed schema enforcement that the rest of the pipeline relies on is structurally bypassed for the terminal synthesis phase. By contrast, legacy Phase S (S0..S12) resolves real `S:Sn` contracts (13 present in repo_truth_map). So the "modern" registry path is *less* governed than the legacy path it's meant to supersede.
  - falsifying check: `python -c "from lib.phase_contract_map import get_step_contract as g; print(g('SP','SP4'), g('SP','SP7'))"` — if either returns a non-None dict, SP contracts resolve and this is disproven. (Static evidence already strong: zero SP rows in either source file.)

- **[S4-HIGH-1] HIGH — `--s-steps`/`DOPEMUX_S_STEPS` validates against S0–S12 but, in registry/auto mode, the resolved prompt map contains only SP0–SP12 → selecting any S step hard-crashes the phase**
  - files: `rte_promptset.py:121-143` (`_validate_s_steps` rejects anything outside `PHASE_S_BASE_STEP_SET` = S0..S12; `get_s_step_controls` returns normalized S* list); `phases.py:39-40` (`PHASE_SP_BASE_STEP_SET` is the SP* set, distinct); `run_extraction_v5.py:21277-21281` (passes `cfg.selected_s_steps` as `selected_step_ids`); `run_extraction_v5.py:17572-17577` (raises `RuntimeError("Selected steps are not resolvable for phase S: …")` when a requested id is absent from `prompt_map`)
  - evidence: observed. `get_s_step_controls` only accepts S0–S12 (raises otherwise, rte_promptset.py:124-127). In registry/auto mode `get_phase_prompts("S")` returns specs whose `step_id` ∈ {SP0..SP12} (per S4-CRIT-1). `_run_phase_inner` builds `prompt_map = {spec.step_id: spec}` (v5:17571) = SP* keys; any requested S* id is "missing" → `RuntimeError` (v5:17575-17577). Confirmed `PHASE_S_BASE_STEPS` vs `PHASE_SP_BASE_STEPS` are disjoint string sets (phases.py:37-40).
  - why it matters (bounds go-live): operator workflow `--phase S --s-steps S4` (a documented selective-rerun pattern) is silently mode-dependent: works in legacy, throws in registry/auto with a message claiming the steps "are not resolvable" — misleading, since the real cause is the S→SP step-set swap, not a missing prompt. Partial reruns of synthesis are unavailable in the registry pipeline.
  - falsifying check: `DOPEMUX_S_PROMPTS=registry DOPEMUX_S_STEPS=S4 <runner> --phase S` against a fixture run dir — PASS would be S4 executing; expected is `RuntimeError: Selected steps are not resolvable for phase S: S4`. (NOT_RUN: requires a runner invocation with a run root.)

- **[S4-HIGH-2] HIGH — Registry/dir naming inversion: directory `prompts/phase_s/` and functions `phase_s_registry_dir`/`load_phase_s_registry`/`validate_phase_s_registry` all say "S", but the payload and every error message assert `phase == "SP"`**
  - files: `rte_promptset.py:65-76` (`phase_s_registry_dir` → `…/phase_s`), `:79-89` (`phase_s_registry_path` → `phase_s/registry.json`), `:212-226` (`validate_phase_s_registry` requires `payload["phase"] == "SP"` and version=1), `:224` error text "Phase SP registry must declare phase='SP'"; `prompts/phase_s/registry.json:3` (`"phase": "SP"`); `PHASE_S_SYSTEM_TRUTHS_GPT52.md` (documents Phase **S** steps S1/S2, "Synthesize a unified architectural vision"); the registry inside that same `phase_s` dir is all SP*
  - evidence: observed. The dir literal is `"phase_s"` (line 75-76); the registry file declares `phase: "SP"` (python load). `validate_phase_s_registry` rejects the payload unless it says `SP` (line 222-226). The doc `PHASE_S_SYSTEM_TRUTHS_GPT52.md` describes S (Opus, S1 ARCHITECTURAL_SYNTHESIS.md / S2 MIGRATION_PLAN.md) — which matches the *legacy v4* `PROMPT_S*` files (`PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md` exists, 13 v4 S prompts confirmed), NOT the SP registry it sits beside.
  - why it matters (bounds go-live / auditability): an operator or auditor reading `phase_s/registry.json` + `PHASE_S_SYSTEM_TRUTHS_GPT52.md` will reasonably conclude this directory configures Phase S. It configures Phase SP. The `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` override (rte_promptset.py:71-75) places the SP registry at `<root>/phase_s`, so a relocated prompt root inherits the inversion. This is the "multi-rooted prompt truth" risk made worse by mislabeling: the fingerprint (`promptset_sha256`) will pin an `SP`-phase payload retrieved from an `S`-named path.
  - falsifying check: `grep '"phase"' prompts/phase_s/registry.json` returns `"phase": "SP"` while the dir is `phase_s` — already confirmed; disproof would require the file to declare `"phase": "S"` (it does not).

- **[S4-HIGH-3] HIGH — Dependency DAG for S and SP is dual-encoded and the two encodings disagree on step-level inputs vs the wrappers' actual reads**
  - files: `phases.py:152-166` (S: required `("R",)`, optional `("X","T","Z","MANUAL")`; SP: required `("R",)`, optional `("X","T","Z")`); `rte_phase_wrappers.py:296-320` (`plan_s_phase` hard-reads `dirs["R"]/norm`, then `extend_input_sources_with_phase_norms(... ["X","T","Z"])`, then `add_manual_rulings_sources(dirs["root"])`); `rte_phase_wrappers.py:323-346` (`plan_sp_phase` reads R + X/T/Z, **no MANUAL**); `prompts/phase_s/registry.json` per-step `input_phase_ids`/`prior_step_ids` (SP0 inputs `["R","X","T","Z"]`; SP1..SP12 inputs `[]`, chained via `prior_step_ids`)
  - evidence: observed. `MANUAL` is in `phases.py` S optional deps and is honored by `plan_s_phase` (line 306 `add_manual_rulings_sources`) but is **not** a real phase (no `PhaseId.MANUAL`; `dirs` has no MANUAL key — it reads `run_root/manual_rulings/PRO_*.json`, wrappers line 288-293). `plan_sp_phase` omits MANUAL entirely. Meanwhile the registry encodes a *third* dependency view at step granularity (SP0 gets R/X/T/Z, downstream SP steps get nothing but prior-step chaining). Three sources of dependency truth: `phases.py` (phase-level), the wrapper code (what's actually globbed), and `registry.json` (`input_phase_ids`).
  - why it matters (bounds go-live): `phases.py` is asserted canonical for the DAG (authority map), but it does not capture (a) that `MANUAL` is a run-root sidecar not a phase, (b) the per-step input wiring that the registry actually drives for SP. An auditor validating "S depends on R, optionally X/T/Z" against `phases.py` will miss that SP's real per-step inputs come from `registry.json["SPn"]["input_phase_ids"]`, and that S pulls `manual_rulings/` which `phases.py` lists as a pseudo-dep. Dependency claims in `phases.py` are necessary-but-incomplete; they cannot be trusted as the sole DAG authority for the synthesis phases.
  - falsifying check: confirm a single canonical reader: `rg -n "input_phase_ids|PHASE_REQUIRED_DEPENDENCIES\[.S" run_extraction_v5.py` — if SP execution actually consumed `PHASE_REQUIRED_DEPENDENCIES["SP"]` rather than the registry's per-step `input_phase_ids`, the registry field would be dead and the dual-encoding harmless. (Registry `input_phase_ids` is carried into `PromptSpec` via the resolvers; whether v5 *enforces* it at runtime is the open question — see S4-MED-2.)

- **[S4-MED-1] MED — Orphan phase id `"M"` in `REQUIRED_PROMPT_STEP_IDS` and routing sets, absent from the `PhaseId` enum / definitions / dir map / verify-choices**
  - files: `phases.py:199` (`"M": {"M0".."M6"}` in `REQUIRED_PROMPT_STEP_IDS`); `phases.py:8-23` (no `M` in `PhaseId`); `run_extraction_v5.py:1151` (`PREMIUM_SYNTHESIS_PHASES = {…,"M"}`), `:1222` (`OPTIMAL_NO_CODE_PHASES = {…,"M"}`); `reports/repo_truth_map.json` (`M:7` steps present)
  - evidence: observed. Python introspection: `"M" in REQUIRED_PROMPT_STEP_IDS` True, but `"M" in PHASES` / `PHASE_DIR_NAMES` False, and `VERIFY_PHASE_CHOICES` has no `M`. `repo_truth_map.json` carries 7 `M` steps (so contracts *would* resolve for `M:Mn`), and routing sets include `M`, yet there is no `PhaseDefinition`, no dir, no dependency edge, and no dispatch path (`run_phase_M` does not exist; grep for phase-`M` dispatch returned only unrelated tokens).
  - why it matters (bounds go-live): `M` is a half-wired phase — it has a contract surface (repo_truth_map) and routing-tier membership but no executable definition. Either a phase was removed and these references are stale, or one is planned and partially landed. Coverage/verify tooling that iterates `REQUIRED_PROMPT_STEP_IDS` (e.g. v5:18263) will surface `M0..M6` as "required" for a phase that can never run, biasing completeness math. Not blocking (cannot be selected), but it's latent drift on a contract-sensitive surface.
  - falsifying check: `rg -n "run_phase_M|\"M\":|PhaseId\.M" run_extraction_v5.py` — if a dispatch/handler for phase M exists, M is live and this is downgraded to OBS. (Confirmed no dispatcher in v5.)

- **[S4-MED-2] MED — `validate_phase_s_registry` enforces SP step-set equality against `phases.py` but ignores the registry's own DAG fields (`input_phase_ids`, `prior_step_ids`, `schema_path`), so a malformed SP dependency graph passes validation**
  - files: `rte_promptset.py:212-272` (validator checks: version==1, phase=="SP", `observed == expected` step set, `prompt_path` relative + within root + exists, `routing_tier` ∈ valid tiers, `outputs` non-empty list — **no validation of `input_phase_ids`, `prior_step_ids`, or `schema_path`**); `prompts/phase_s/registry.json` (each step carries `input_phase_ids`/`prior_step_ids`/`schema_path`); `phases.py:198` (`REQUIRED_PROMPT_STEP_IDS["SP"]`)
  - evidence: observed. The validator's `validated[step_id]` dict (line 268-271) only retains `prompt_path` and `tier`; it never reads `input_phase_ids`, `prior_step_ids`, or `schema_path`. The registry-bootstrapping coupling is therefore *one-directional and partial*: the JSON must match `phases.py`'s SP step ids exactly (`observed != expected → ValueError`, line 233-237), but the dependency/schema metadata in the JSON is unvalidated and (per S4-CRIT-2 + S4-HIGH-3) not cross-checked against any contract or DAG source.
  - why it matters (bounds go-live): the "paradox" the map points at is real but narrower than total: the registry is bootstrapped *for step identity only*. A `prior_step_ids` cycle, a dangling `prior_step_ids` reference, or a `schema_path` pointing at a nonexistent schema would all pass `validate_phase_s_registry`. Combined with S4-CRIT-2 (SP contracts are None anyway), the SP step ordering/schema is effectively unenforced. Fail-closed guarantees stop at the prompt-file level.
  - falsifying check: temporarily set `prompts/phase_s/registry.json` `SP5.prior_step_ids = ["SP99"]` (nonexistent) in a scratch copy and run `validate_phase_s_registry` — if it raises, dependency validation exists and this is disproven. (NOT_RUN: would mutate a contract file; static read of the validator body confirms no such check.)

- **[S4-OBS-1] OBS — `plan_s_phase` optionally ingests `Z` norm outputs, but `Z` depends on `T` and is a freeze/handoff phase that normally runs after synthesis — a soft ordering coupling that fails-open**
  - files: `rte_phase_wrappers.py:305` (`extend_input_sources_with_phase_norms(input_sources, dirs, phases=["X","T","Z"])`); `phases.py:143-150` (`Z` requires `("R","X","T")`); `phases.py:156-157` (`S` optional `("X","T","Z",…)`)
  - evidence: observed. `plan_s_phase` reads `dirs["Z"]/norm` if it `.exists()` (via `extend_input_sources_with_phase_norms`, lines 281-285). Z is "Handoff Freeze" (phases.py:145-147). Whether Z precedes S depends on the operator's `--phase` ordering (no single hardcoded full sequence in these files; `FIRST_LIVE_INITIAL_PHASES` is only A/H/D/C, rte_config.py:105). The read is `.exists()`-guarded, so absent Z is tolerated (fail-open), not a crash.
  - why it matters: low — it's a benign optional input that resolves to "skipped" when Z hasn't run. But it does mean S's `truth_pack_manifest` provenance (wrappers:308) is order-sensitive: the same R/X/T inputs yield different S manifests depending on whether Z ran first. Determinism of S output is conditioned on phase ordering, not just inputs. Worth a note for reproducibility claims.
  - falsifying check: run `--phase S` twice against the same run root, once with `Z_handoff_freeze/norm` populated and once empty; diff the S `TRUTH_PACK` manifest. Identical manifests would disprove order-sensitivity. (NOT_RUN.)

- **[S4-OBS-2] OBS — `LEGACY_PHASE_DIR_ALIASES` maps only `R2_synthesis → R_arbitration`; no alias covers the S/SP `phase_s`-named dir, so relocated/legacy SP runs have no dir-alias safety net**
  - files: `phases.py:202-204` (`LEGACY_PHASE_DIR_ALIASES = {"R2_synthesis": "R_arbitration"}`); `phases.py:160-162` (SP dir `SP_synthesis_pipeline`); `rte_promptset.py:75` (`phase_s` literal)
  - evidence: observed. Only one legacy alias exists. The SP *output* dir is `SP_synthesis_pipeline` (phases.py:161) while the SP *prompt registry* dir is `phase_s` (rte_promptset.py:75) — two different "phase_s/SP" spellings with no alias linking them, and none of the historical `S`/`SP` dir variants are aliased.
  - why it matters: low — informational. If older runs used a different S/SP dir name, resume/replay against `PHASE_DIR_NAMES` would not auto-resolve it the way `R2_synthesis` does. Given the S/SP naming churn evidenced in S4-HIGH-2, the absence of aliases here is a small replay-robustness gap.
  - falsifying check: `rg -n "phase_s|SP_synthesis|S_synthesis" -- LEGACY_PHASE_DIR_ALIASES` (i.e. inspect the dict) — any S/SP entry would disprove. Confirmed only `R2_synthesis` present.

---

## Summary

The S4-integration stage is where the authority map's "registry-bootstrapping paradox" and "multi-rooted prompt truth" risks become concrete defects. Two are **CRIT** for go-live:

1. **S4-CRIT-1** — `--phase S` resolves a *different step set* (S0–S12 vs SP0–SP12) and writes both to `S_synthesis/` based purely on `DOPEMUX_S_PROMPTS`; artifact identity is environment-dependent and clashes with the S* step ids that coverage/proof tooling expects.
2. **S4-CRIT-2** — the SP (registry) pipeline runs with **no phase-contract enforcement** because `repo_truth_map.json` / `promptset.yaml` define phase `S` but never `SP`; 9 JSON-emitting SP steps get `contract=None`, bypassing the schema/lane gates the rest of the pipeline depends on.

The remaining HIGHs (S→SP step-selection crash; the `phase_s`/`SP` naming inversion; triple-encoded S/SP dependencies) compound auditability and operator-workflow risk. The bootstrapping coupling in `validate_phase_s_registry` is **real but partial** (S4-MED-2): it pins SP *step identity* to `phases.py` and fails closed on mismatch, but does not validate the registry's dependency graph or schema paths.

**`phases.py` and `rte_phase_wrappers.py` themselves are clean, deterministic, and faithfully canonical for what they encode** — the defects live in the *seams* between `phases.py` (phase-level DAG + step-id sets), the SP registry (per-step prompt/DAG/schema), the v4 contract sources (`repo_truth_map.json` + `promptset.yaml`, S-only), and v5's mode-dependent dispatch. No invented findings; every claim is anchored to a verified file:line above.

**Go-live verdict for this stage:** NOT_READY while the SP pipeline is reachable, unless (a) `DOPEMUX_S_PROMPTS` is pinned to `legacy` and SP dispatch is fenced off, OR (b) phase `SP` is added to `repo_truth_map.json`/`promptset.yaml` so SP contracts resolve and the S/SP step-set swap is made explicit rather than env-implicit.

**NOT_RUN items** (require execution under the human-verify harness, each with the exact command in its falsifying check): S4-CRIT-1 prompt-set probe, S4-CRIT-2 contract lookup, S4-HIGH-1 step-selection crash, S4-MED-2 registry-DAG validation, S4-OBS-1 ordering determinism. Static evidence for each is strong (source-file reads + JSON/YAML loads), but the runtime assertions were not exercised — NOT collapsed into PASS.

==========================================================================================
## RTE-CORE S5-routing  (workflow-subagent, a69a087a7a6f74f04, 5839 chars)
==========================================================================================

I'll audit the S5-routing stage. Let me start by verifying the authority map's claims against primary source, focusing on the four files specified.

The files match the authority map's references. Now let me read the four target files. Let me start with the smaller, foundational ones and the gate validator.

`rte_config.py` confirmed. Key observations: `DPMX_LIVE_OK_ENV = "DPMX_LIVE_OK"` (line 120), routing env vars (108-114), and `BENCHMARK_ROUTE_OWNERSHIP_MODE = "strict_extraction_lane_owned_v1"` (line 123). Now let me read the gate validator and output_safety in parallel.

Both files confirmed. `output_safety.py` is thorough — multiple redaction passes including provider-payload sanitization. The gate validator has a clear blocker/condition taxonomy. Now let me read the critical sections of the gate validator: the online preflight, DPMX_LIVE_OK handling, and the main gate logic. Let me also start reading llm_runtime.py.

This is a multi-step audit. Before I commit to an interpretation of fail-closed correctness, let me get oriented with the key sections, then consult the advisor. Let me read more of the gate validator (the preflight and main flow) and the start of llm_runtime.py.

Interesting — `llm_runtime.py` has NO references to `DPMX_LIVE_OK`, `_execute`, `dry_run`, etc. That's notable. The waiver mechanism in the gate (`split_findings_by_waiver`, line 1015) only waives **P1 severity** blockers. Let me dig into the waiver logic and the live consent path in llm_runtime more broadly.

Now I understand the architecture better. `llm_runtime.py` uses a `LiveLLMDeps` dependency injection (lines 32-33) where `live_llm_calls_blocked_for_tests` and `live_llm_tests_env` are injected callables — the actual `DPMX_LIVE_OK` gate lives in the runner (v5), not in this module. Let me read the key sections of `llm_runtime.py`: the header/deps structure, the provider call guard (lines 380-410), the provider-fallback logic (around 1081), and the call orchestration. Let me read these in chunks.

Now let me read the critical provider-call guard (around line 380-410) and the fallback/escalation logic. This is the heart of the routing stage.

I see the core call guard at lines 387-404. The sanitization of system_prompt and user_content happens at lines 405-406 before sending to provider. Note: the `live_llm_calls_blocked_for_tests` check is a **test guard**, not the production live-consent gate. The DPMX_LIVE_OK gate is in the runner (v5), which is out of my 4-file scope but I should verify its relationship.

Let me continue reading the call orchestration and then find the fallback/escalation logic which is the "provider-fallback concentration" concern in my stage goal.

I have a good understanding of the call flow. Now I need the fallback/escalation/concentration logic — the higher-level routing that selects providers and what happens on failure. Let me find the orchestration functions (escalation, fallback, route selection) which is the "provider-fallback concentration" concern.

The "provider-fallback concentration" logic is `call_llm_with_ladder` (line 1064). This is the key function for the fallback concern. Let me read it in full.

Now I understand the ladder/fallback logic well. Key findings forming:
- The "route guard" (lines 1185-1194) only blocks the next hop if `failure_type == "quota_or_billing"` AND the next route shares the same `api_key_env`. This is the provider-fallback concentration guard.
- Note the guard checks `api_key_env` equality, NOT provider equality.

Now let me examine the gate validator's critical paths: the online preflight (800-920), the DPMX_LIVE_OK / live consent path, the waiver logic (1015-1044), and the main verdict computation. Let me also check how the live consent path relates between gate and runtime — and whether `DPMX_LIVE_OK` consent is verified in the gate at all.

Critical finding forming: when `--allow-online-preflight` is NOT passed, the online provider preflight is downgraded to a **Condition (WARN)**, NOT a Blocker (lines 807-832). The preflight uses `live_ok=False` and `dry_run=True` (lines 835, 870). This means the gate can return GO without ever verifying providers are reachable. Let me verify how Conditions vs Blockers affect the final verdict, and read the waiver split logic + verdict computation.

This is very important for the verdict logic. Key observations:
1. `derive_operator_verdict` (1122-1138) returns `GO_NOW` only when `blockers` is empty. **Conditions never block the verdict.** So when `--allow-online-preflight` is omitted, the online preflight becomes a Condition, and the gate returns `GO_NOW`.
2. The waiver only applies to **P1 severity** blockers (line 1031). All the online preflight failure blockers are created with severity `"P0"` (line 901, 911). So those genuinely can't be waived.
3. `build_environment_summary` (1145) explicitly states tooling can pass while live readiness is "blocked or unverified" — this is documented/intentional design.

This tells me the gate is intentionally a "tooling + offline" gate that does NOT verify live provider reachability unless explicitly asked. Let me verify by reading the main() flow and how the verdict/exit code is computed, plus check the `--allow-online-preflight` default and severity assignments throughout.

Before I crystallize findings, let me consult the advisor since I've gathered the core evidence and am about to commit to an interpretation of fail-closed correctness.

I see only one `"P1"` severity (line 771): the route-derivation blocker is P0 only if `active_route_required AND not fallback_chain_present`, else P1. So the waiver mechanism (`--waiver-code` + P1) applies essentially only to route-derivation findings where a fallback chain is present. Let me look at the route-derivation logic (lines 700-780) and the main() exit code mapping (around 1300-1375).

==========================================================================================
## RTE-CORE S6-operator  (workflow-subagent, af520fed497c15775, 17886 chars)
==========================================================================================

I'll audit the operator-facing surfaces (S6-operator stage). Let me start by orienting against the primary source files, verifying the authority map's claims as I go.

The files exist with the expected line counts. The shell init warning is harmless. Now let me read all four target files in full to understand the operator-facing surfaces.

These two files are mostly mechanical (path layout, proof-pack writers). The operator-visible status/terminology surfaces are more likely in `rte_ops_surfaces.py` and `reporting.py`. Let me read those.

Now the big one. Let me read `reporting.py` — this is where the human-facing status snapshots and dashboard get written.

I now have the full picture of all four files. This is an "operator status surface" audit focused on visual-only status, terminology clarity, and accessibility. Let me note what these files actually are: they emit **JSON artifacts** (no TTY/color/ANSI rendering here), so "accessibility" maps to machine-readability of status, and "visual" maps to where these JSON statuses are surfaced to a human reader.

Two critical observations are already visible:
1. **Status vocabulary fragmentation** across artifacts (`PASS/FAIL/UNKNOWN`, `VERIFIED/BLOCKED/UNKNOWN`, `OK/BLOCKED`, `ready/blocked`, `CLEAR/BLOCKED`, `pass/fail`, `PASS/FAIL/SKIPPED`).
2. The authority map claims `reporting.py:1026/1077` consume `runner_script` — let me verify that, plus check where these statuses get *rendered* to a human (the "visual-only status" part of my mandate), and whether there's a terminology collision around `OK` vs `PASS`.

Let me verify the key cross-file claims with targeted reads before writing findings.

Confirmed: no rendering/color/emoji in these four files. They are pure JSON artifact writers. The "visual-only status, terminology clarity, accessibility" mandate must be interpreted against the JSON status vocabulary that operators (and downstream renderers) consume.

Key finding crystallizing: there are at least **four disjoint status vocabularies** across these artifacts. Critically, `compute_run_status` returns `OK` (reporting.py:587, 901, 968-978) while `_normalize_gate_status` (reporting.py:167-173) treats `OK` as an *alias for PASS* — but the certification gate uses `PASS/FAIL/UNKNOWN→VERIFIED/BLOCKED/UNKNOWN`, and per-phase coverage uses `PASS/FAIL` (reporting.py:830), and `blocked_promptset.status` uses `CLEAR/BLOCKED` (reporting.py:824). An operator reading these side-by-side sees `OK`, `PASS`, `VERIFIED`, `CLEAR`, `ready`, and `SKIPPED` all meaning roughly "good," and `FAIL`, `BLOCKED`, `blocked`, `fail` all meaning "bad."

Let me verify two things: (1) the exact return values of `compute_run_status` (to confirm `OK` is the canonical "good" run status, not `PASS`), and (2) whether `_normalize_gate_status` ever actually receives an `OK`/`CLEAR` token from these run-status artifacts (i.e., is the alias load-bearing or latent).

This is highly material. `compute_run_status` (v5:3598-3615) returns a **fifth** vocabulary: `OK / BLOCKED / COST_ABORTED`. Note `COST_ABORTED` is a distinct terminal status that is NOT in `_normalize_gate_status`'s alias table (reporting.py:167-173) — so if a `COST_ABORTED` run-status token ever reached the gate normalizer it would map to `UNKNOWN`, not `FAIL`. Let me verify whether that path is reachable (does the certification gate ever normalize a run_status/coverage status that could be `COST_ABORTED`?), and confirm the `CLEAR` token has no consumer (latent/decorative).

Let me also check the doctor/preflight terminology divergence (`run_pre_live_validator` emits lowercase `pass/fail` at rte_ops_surfaces.py:188 while `run_provider_preflight` emits uppercase `PASS/FAIL` at :812) and how the certification gate reads the validator status — because `_normalize_gate_status` uppercases, so lowercase `pass` is handled, but I should confirm.

Let me consult the advisor now — I have the full primary-source map, I've found the central thread (status-vocabulary fragmentation + a possible COST_ABORTED→UNKNOWN gap), and before I commit to severity ratings I want a second read on whether the COST_ABORTED gate gap is real or latent, and whether I'm over/under-calling the terminology findings for this "operator status surface" stage.

I have everything I need. Let me record key facts durably before consulting the advisor (so the deliverable survives), then call advisor on severity calibration.

Key verified facts:
1. **Five disjoint status vocabularies** in scope: `compute_run_status` → `OK/BLOCKED/COST_ABORTED` (v5:3606-3615); certification gates → `PASS/FAIL/UNKNOWN` rolled to `VERIFIED/BLOCKED/UNKNOWN` (reporting.py:439-445); per-phase coverage → `PASS/FAIL` (reporting.py:830); `blocked_promptset.status` → `CLEAR/BLOCKED` (reporting.py:824); resume → `ready/blocked` (reporting.py:978); validator → lowercase `pass/fail` (rte_ops_surfaces.py:188); preflight/batch → `PASS/FAIL/SKIPPED` (rte_ops_surfaces.py:763, 812, 733).
2. **`_normalize_gate_status` alias table is asymmetric** (reporting.py:167-173): maps `OK→PASS` and `BLOCKED→FAIL`, but `COST_ABORTED`, `CLEAR`, `UNKNOWN` fall through to `UNKNOWN`. The gate only normalizes validator/dashboard/topology/preflight `status`, none of which carry `COST_ABORTED` — confirmed (no COST_ABORTED in reporting.py). So that specific gap is **latent**, not active — important for severity.
3. **`CLEAR` token has zero consumers** (only emitted at reporting.py:824, never read) — decorative/asymmetric vs the `BLOCKED`/`OK` family.
4. No color/emoji/ANSI/TTY rendering in any of the four files — they are JSON writers. The "visual" surface is the JSON status fields themselves + downstream renderers (`lib/risk_dashboard.py`, v5).

Let me consult the advisor on calibration before finalizing.

Advisor confirms my calibration. Writing the terminal deliverable now.

---

# RTE STAGE S6-operator — Audit Findings

**Scope:** `rte_ops_surfaces.py`, `rte_reports.py`, `reporting.py`, `rte_output_layout.py` (HEAD `755bf38460`). Mandate: visual-only status, terminology clarity, accessibility.

**Scoping note (verified true-negative on traditional a11y):** All four files are **JSON-artifact writers**. There is no ANSI/color/emoji/TTY rendering in any of them — confirmed by clean grep for `[✅❌⚠️🟢🟡🔴→⇒]`, `\033[`, `colorama`, `rich.`, `click.`, `print(` (only the imported filename constants matched). The human-facing "visual surface" of this stage is therefore the **JSON status fields themselves** plus downstream renderers (`run_extraction_v5.py`, `lib/risk_dashboard.py` — out of scope). "Accessibility" here = machine-readability and cross-artifact consistency of status vocabulary. Findings below are scoped accordingly; the absence of color-contrast/keyboard findings is correct, not skipped.

**Top-line verdict:** Every status path in these files is **fail-closed** (unknown/missing → `UNKNOWN`/`BLOCKED`, never silent PASS/VERIFIED). **Nothing in this stage blocks go-live.** The findings below *bound* unattended operation by raising the risk of operator misread across artifacts; none is a machine fail-open. I did not find a single concrete cross-artifact handoff that consumes another component's status under a mismatched vocabulary in a way that flips a verdict (the one real handoff is consistent — see [S6-OBS-1]). I resisted manufacturing a CRIT.

---

- **[S6-MED-1] MED — Five disjoint terminal-status vocabularies across operator artifacts; same field written by two writers with two vocabularies**
  - files:
    - `run_extraction_v5.py:3606-3615` (`compute_run_status` → `OK` / `BLOCKED` / `COST_ABORTED`)
    - `reporting.py:439-445` (certification `overall_status` → `VERIFIED` / `BLOCKED` / `UNKNOWN`, rolled from gate `PASS`/`FAIL`/`UNKNOWN` at `reporting.py:352,363,371,384`)
    - `reporting.py:830` (per-phase coverage `status` → `PASS` / `FAIL`)
    - `reporting.py:824` (`blocked_promptset.status` → `CLEAR` / `BLOCKED`)
    - `reporting.py:978` (resume `resume_status` → `ready` / `blocked`)
    - `rte_ops_surfaces.py:812,763,733` (preflight/batch `status` → `PASS` / `FAIL` / `SKIPPED`)
    - **Same-field divergence:** `reporting.py:587` hardcodes `run_status` to only `OK`/`BLOCKED` in `write_run_manifest`, while `run_extraction_v5.py:3631-3643` (`update_run_manifest_status`) later overwrites the *same* `run_status` field with `compute_run_status`'s output, which includes `COST_ABORTED`.
  - evidence: observed (all literals grepped and read at the cited lines; the two `RUN_MANIFEST.run_status` writers observed at reporting.py:587 and v5:3643).
  - why it matters (bounds go-live): an operator (or an unattended supervisor script) reconciling run state reads at least six artifacts where "good" is spelled `OK`, `VERIFIED`, `PASS`, `CLEAR`, `ready`, and `SKIPPED`, and "bad" is spelled `FAIL`, `BLOCKED`, `blocked`. A reader who learns one artifact's vocabulary can misread another — e.g., expecting `PASS` at the run level and not finding it because the run level says `OK`, or seeing `RUN_MANIFEST.run_status` flip from a value `write_run_manifest` can never emit (`COST_ABORTED`) to a value it can. This does not flip any *machine* gate (each path is internally consistent and fail-closed), so it bounds rather than blocks: it raises operator cognitive load and the chance of a wrong manual GO/NO-GO call during unattended-run review.
  - falsifying check: `rg -n '"status"|"run_status"|"resume_status"|"overall_status"' reporting.py rte_ops_surfaces.py | rg -o '"[A-Za-z_]+"' | sort -u` — if this yields a single shared enum (or the codebase defines one canonical status-string constant set that all writers import), the finding is disproved. (Observed today: it yields the divergent set above; no shared enum constant is imported.)

- **[S6-OBS-1] OBS — `_normalize_gate_status` alias table is asymmetric (`OK`/`READY`→PASS, `BLOCKED`/`NO_GO`→FAIL) but `COST_ABORTED`/`CLEAR` fall through to UNKNOWN; latent today**
  - files: `reporting.py:167-173` (normalizer); consumers at `reporting.py:365-369` (topology, dashboard), `:382` (live provider), `:398` (static/validator).
  - evidence: observed. The normalizer uppercases input then maps `{PASS,PASSED,READY,OK}→PASS` and `{FAIL,FAILED,BLOCKED,NO_GO}→FAIL`, else `UNKNOWN`. `COST_ABORTED` (the third terminal run-status from v5:3606) and `CLEAR` (reporting.py:824) are absent from both buckets. **Verified latent:** `rg -n COST_ABORTED reporting.py` returns zero hits — the four gate inputs the normalizer actually receives (`validator.status`/`final_verdict`, `dashboard.status`/`overall_status`, `topology.status`, `provider_preflight.status`) never carry `COST_ABORTED` or `CLEAR`. So no live mis-normalization occurs at this HEAD.
  - why it matters (bounds, does not block): this is a fragility marker, not an active defect. If a future change ever routed `coverage_rollup.run_status` or `RUN_MANIFEST.run_status` (which *can* be `COST_ABORTED`) through this normalizer, a cost-aborted run would normalize to `UNKNOWN` → certification `overall_status` UNKNOWN, not `BLOCKED`. That is fail-*soft* (UNKNOWN never becomes VERIFIED at reporting.py:440), so even the hypothetical activation cannot fabricate a GO. Hence OBS, not HIGH/CRIT.
  - falsifying check: `rg -n 'COST_ABORTED|"CLEAR"' reporting.py` — any hit feeding a `_normalize_gate_status(...)` call site would upgrade this to a live MED. (Today: no such feed.)

- **[S6-OBS-2] OBS — `blocked_promptset.status: "CLEAR"` token has no reader; decorative and inconsistent with the surrounding OK/BLOCKED family**
  - files: emitted at `reporting.py:824` (`"status": "BLOCKED" if blocked_promptset else "CLEAR"`).
  - evidence: observed. Repo-wide `rg -rn '"CLEAR"' --glob '*.py'` (excluding tests) returns only the emit sites in `reporting.py` and the legacy `run_extraction_v3.py`; no `== "CLEAR"` / `.get(...) == "CLEAR"` consumer exists. Inferred (low): the value is informational-only for human eyes / future tooling.
  - why it matters (bounds): a unique "good" word (`CLEAR`) used in exactly one nested status field, with no consumer and no presence in the gate normalizer's alias table, is a small terminology-clarity tax — a reader must learn that `CLEAR` here means the same as `OK`/`PASS` elsewhere. No machine impact.
  - falsifying check: `rg -rn '== *"CLEAR"|get\([^)]*\) *== *"CLEAR"' --glob '*.py'` — any consumer disproves "decorative/unread."

- **[S6-OBS-3] OBS — `write_run_dashboard_snapshot` writes no top-level `status`, but the certification topology fallback reads `dashboard.get("status")`; fail-closed-safe**
  - files: writer `reporting.py:149-164` (snapshot keys = `generated_at`, `run_id`, `source`, `summary`, `payload` — no top-level `status`/`overall_status`); reader `reporting.py:368-369` (`elif isinstance(dashboard, dict) and dashboard: topology_status = _normalize_gate_status(str(dashboard.get("status") or dashboard.get("overall_status") or ""))`).
  - evidence: observed. The dashboard snapshot's only status-bearing data lives under `summary`/`payload`; the certification reader looks for `status`/`overall_status` at the top level, which the snapshot writer never sets. The `or ""` → `_normalize_gate_status("")` → `UNKNOWN`.
  - why it matters (bounds, does not block): when `DOCTOR_FULL.json` is absent and the dashboard is the topology fallback, the `operator_topology_resilience` gate silently resolves `UNKNOWN`. That is the safe direction (UNKNOWN cannot yield `VERIFIED`; reporting.py:440 requires all four gates `PASS`). The cost is interpretive: an operator may expect the dashboard to satisfy the topology gate and instead see UNKNOWN with no explicit "dashboard carried no top-level status" note. The gate's `notes` (reporting.py:435) does say artifact completeness alone is insufficient, which partially mitigates.
  - falsifying check: `python - <<'PY'` constructing a dashboard snapshot via the writer's key set and asserting `("status" in snapshot or "overall_status" in snapshot)` — it will assert False at this HEAD, confirming the reader's key never exists in the writer's output. (Marked NOT_RUN — read-only contract; smallest human-verify command is that snippet against `reporting.write_run_dashboard_snapshot`.)

- **[S6-OBS-4] OBS — lowercase `pass`/`fail` in validator result is NOT a defect (handled by normalizer); noted only for vocabulary inventory**
  - files: `rte_ops_surfaces.py:188` (`"status": "pass" if result.returncode == 0 else "fail"`); consumed at `reporting.py:398` via `_normalize_gate_status`, which does `.strip().upper()` first (reporting.py:168).
  - evidence: observed. The casing mismatch versus the uppercase `PASS`/`FAIL` used at `rte_ops_surfaces.py:812` is absorbed by the normalizer's uppercasing before lookup.
  - why it matters: included so the vocabulary census in [S6-MED-1] is complete and to pre-empt a false "casing bug" call. No action required; no machine or operator-read risk because the only consumer normalizes case.
  - falsifying check: confirm `_normalize_gate_status` is the sole consumer of `PRELIVE_VALIDATOR_RESULT.json`'s `status`: `rg -rn 'PRELIVE_VALIDATOR_RESULT|validator_payload.*status' --glob '*.py' | grep -v test`. If a case-sensitive `== "PASS"` consumer of this field exists, this becomes a real LOW.

---

## Validation Performed
- **PASS:** Read all four target files in full; verified every status-literal site by grep + read. Verified `_normalize_gate_status` alias table and its four call sites (reporting.py:365-398). Verified `compute_run_status` returns `OK`/`BLOCKED`/`COST_ABORTED` (v5:3606-3615). Verified `COST_ABORTED`/`CLEAR` are NOT consumed by the gate normalizer (zero hits → [S6-OBS-1], [S6-OBS-2] are latent/decorative). Verified the dual-writer divergence on `RUN_MANIFEST.run_status` (reporting.py:587 vs v5:3643). Verified no color/emoji/ANSI/TTY rendering in scope.
- **FAIL:** None.
- **NOT_RUN:** The [S6-OBS-3] dashboard-snapshot key-presence assertion (read-only audit contract; runtime construction not permitted). Human-verify command given inline. No `run_extraction_v*` / prescan / probe / LLM / network calls were made.

## Authority Used
Runtime code (the four target files + `run_extraction_v5.py` for `compute_run_status`/`update_run_manifest_status`), grep across the service for status-token consumers. Authority-map claims relevant to this stage were re-verified against source: `reporting.py:1026/1077` do consume `deps.runner_script` via `sha256_text` (confirmed, update_proof_pack/write_blocked_promptset_proof_pack) — consistent with the map.

## Remaining Uncertainty / Risk
- Downstream human renderers (`run_extraction_v5.py`, `lib/risk_dashboard.py`) are out of scope; if one of them maps these JSON statuses to color/glyphs, a separate a11y (color-contrast/colorblind) audit of *that* layer is warranted — not assessable from these four files.
- [S6-OBS-3]'s safe-UNKNOWN behavior assumes the dashboard never gains a top-level `status` elsewhere in the pipeline; I confirmed the in-scope writer does not set one, but a different writer to the same `RUN_DASHBOARD.json` (if any exists in v5) was not exhaustively traced.

## Files Touched
None (read-only audit).

## Git State
Branch `main`, HEAD `755bf38460d1f2f6bba6e072ec9a627e9e218b15`. No working-tree changes made by this audit.

## Requested Next Step
Treat [S6-MED-1] as the actionable item: introduce one canonical status-string constant set (or a documented mapping table) shared by `reporting.py` writers and `compute_run_status`, and reconcile the two `RUN_MANIFEST.run_status` writers (reporting.py:587 ↔ v5:3643) so the field can only carry one vocabulary. [S6-OBS-1..4] need no code change now but should be captured as guardrails (add `COST_ABORTED`/`CLEAR` to the normalizer's tables defensively, or assert they never reach it) before any future change routes run-level status through `_normalize_gate_status`.

==========================================================================================
## RTE-CORE S7-tests  (workflow-subagent, a1e7b7bd3dd60380e, 5666 chars)
==========================================================================================

I'll audit the S7-tests stage. Let me start by orienting myself in the test directory and the pre-live gate validator.

This is a large test suite (178 test files). My audit focus is process-success vs truth-quality blindness and gate coverage gaps. Let me read the core gate validator and its test first, then the truth-quality-relevant tests. Let me orient before diving deep.

Let me read the rest of the gate validator (the core decision logic and how it executes tests), plus the gate test and key truth-quality tests.

I found something significant. `collect_truth_split` at line 476-478 is a **stubbed placeholder** that always returns PASS with zero mismatches, regardless of actual runtime state. This is one of the gate's most important truth-quality layers (it's supposed to detect runner/promptset/model-map/artifact drift — the "STALE_*" classifications). Yet the classification function `classify_truth_split_row` exists and is fully tested, but is never wired into the gate's actual collection. Let me verify this is the live code path and not overridden elsewhere, then continue reading the gate's pytest layer and verdict logic.

Confirmed: `collect_truth_split` (line 476-478) is a hardcoded stub that always returns PASS/0-mismatches, and `classify_truth_split_row` is **only** referenced at its own definition (line 171) — never called by the gate's live path. The fragmentation risks the authority map flagged (drift between runner/promptset/model-map) are NOT actually checked by the gate. The test (`test_pre_live_gate_v25.py:215,328`) monkeypatches `collect_truth_split` with a PASS stub, so the test mirrors the dead stub and never exercises real drift detection.

Now let me read the pytest layer (how it runs critical tests), the smoke layer, and the verdict logic — these are the heart of "process-success vs truth-quality blindness."

Now let me see the rest of `run_gate` (verdict assembly) and the critical-test list wiring, then look at the gate's own test for the critical-test layer. Let me also check the key truth-quality tests the gate relies on.

Now I have the full gate structure. Key observations so far:

1. `collect_truth_split` is a stub → truth_split_audit always PASS. The `TARGET_TRUTH_SPLIT_MISMATCH` blocker code (line 103) is defined but **never emitted** anywhere. The whole STALE_* drift detection is non-functional.
2. The gate runs only **5 critical tests** (line 47-53) as blocking + 1 repo-drift test as non-blocking, out of 178 test files. Most truth-quality tests (truth_label_preservation, source-truth poisoning, output_safety, strict_passthrough) are NOT in the gate's blocking set.
3. The 3 golden smoke tests are the only end-to-end evidence, and they run in dry-run (no real LLM, no truth-quality assertion).

Let me now examine the smoke tests and golden fixture to assess whether they validate *truth quality* or just *process success*. Let me also look at the key truth-quality tests to see if they assert content correctness or just structural shape.

The smoke tests are critical for my finding. They use **pre-built fixture artifacts** (`build_smoke_run`) and `verify_phase_output` — which only checks that artifact *files exist and are structurally valid*. The golden smoke explicitly blocks `call_llm` (offline). So the gate's only "end-to-end" evidence validates that the runner can *assemble proof files from already-correct fixtures* — it never validates that the LLM extraction produces correct truth content. Let me confirm by reading the smoke helper.

This confirms the core finding. The smoke test fixtures are **hand-constructed valid payloads** (`make_valid_d1_success_payload` builds artifacts to satisfy the contract). The smoke run never invokes the LLM (golden explicitly throws on `call_llm`). `verify_phase_output` checks structural existence. So the gate's end-to-end evidence proves the *plumbing* (proof emission, determinism, coverage rollup) works on pre-validated inputs — it is structurally incapable of detecting whether the LLM produces faithful truth.

Let me call the advisor now — I'm before the substantive write, I have a clear picture of the gate but want to pressure-test my framing and make sure I'm not missing what the broader test suite *does* cover for truth quality (so I don't overclaim "blindness"). Wait — the output rules explicitly forbid using the advisor (it consumes my final turn). I'll skip it and instead empirically check the truth-quality tests to ground my claims. Let me examine the tests that *should* catch truth-quality regressions, to fairly assess what the suite does and doesn't cover.

Important nuance. The `test_truth_label_preservation.py` suite is a genuinely strong truth-quality test (it asserts UNKNOWN/CONFLICTING labels cannot be silently upgraded by repair/sidefill/prescan — the "source-truth poisoning" defense). This is good. But note it is **NOT in the gate's `CRITICAL_TEST_PATHS`** — so the gate does not run it as a blocking layer.

Also a significant find: `test_code_prescan_truthfulness.py` has **3 `@pytest.mark.xfail(strict=True)`** tests deferred to "TP-RTE-WALKER-006" — meaning known prescan truthfulness bugs (relative-import emission, API-surface substring false positives, arrow-function signature coverage) are documented-as-broken and the test passes *because they fail*. These are prescan correctness gaps that feed the truth pipeline's inputs.

Let me check how widespread `xfail`/`skip` is across the suite (this is the "process-success hides known-broken" pattern), and verify the gate is invoked by CI / packaged anywhere, and whether `test_run_extraction_v5_live_readiness.py` (gate-adjacent) gates on anything real.

==========================================================================================
## RTE-CORE S8-boundaries  (workflow-subagent, a71940acc53396bd2, 26291 chars)
==========================================================================================

I'll audit stage S8-boundaries (out-of-scope writes, legacy script pollution) for the Repo Truth Extractor. Let me start by orienting myself to the target files.

Now let me examine the archive/ directory contents and how these modules are used. Let me look at the archive subdirectories and check the legacy script pollution.

This is the orientation phase. I have read all three target areas (output_safety.py, extraction_hygiene.py, archive/). Now I need to verify the actual S8-boundary concerns: (1) out-of-scope writes — where do these modules write to disk, and can they escape their intended sandbox; (2) legacy script pollution — is the archive/ dir referenced by live runtime, are legacy scripts still reachable.

Let me trace the write paths and references. The key risk areas I see already:
1. `extraction_hygiene.py:776` does `shutil.move()` — a real filesystem mutation. Need to verify the quarantine destination can't escape, and that `--apply` isn't reachable from the live pipeline.
2. `run_apply` operates on `repo_root` which defaults to `_REPO_ROOT_DEFAULT` (the whole dopemux-mvp repo, not the service dir) — out-of-scope blast radius.
3. archive/ — is it referenced anywhere in runtime?

Let me investigate these in parallel.

Key findings emerging:
- `extraction_hygiene.py` has **zero runtime importers** (only invoked via its own CLI `__main__`). 
- `output_safety.py` is widely imported by live runtime (v5, llm_runtime, gate, etc.) — it's load-bearing.
- `archive/legacy_prompts` and `archive/legacy_artifact_gates` are **never referenced** anywhere — confirmed dead pollution. The grep hits for "archive/" are all about `docs/archive/` (a different path) and `SYSTEM_ARCHIVE/`, not this service's `archive/` dir.

Let me verify the archive/ non-reference more rigorously (search whole repo, not just service), check if extraction_hygiene is wired into any CI/hook/gate, and examine the blast-radius of run_apply's repo_root default.

Now I have a much clearer picture. `extraction_hygiene.py` IS wired into the operator CLI via `src/dopemux/commands/extract_commands.py` (dynamic import at line 856-863, used at 1129). Let me read that integration to understand whether `apply` (the mutating path) is reachable from the operator CLI, and with what arguments. The main repo copy (not worktree) is what matters. Let me also confirm the README's reference to the archive dir and check the `_REPO_ROOT_DEFAULT` blast radius concern.

This is highly material. The mutating `run_apply(dry_run=False)` IS reachable from the operator CLI `dopemux extract truth-run --apply-cleanup` (extract_commands.py:1163), and it operates on `repo_root` which `run_scan`/`_load_hygiene_module` sets to `parents[3]` = the **entire dopemux-mvp repo**, not the service directory. This is the out-of-scope-write surface for this stage.

But I need to be careful and precise: the apply path has guardrails (`_is_canonical_protected`, candidates limited to `extraction/repo-truth-extractor/{v3,v4}/runs` + `extraction/**/.DS_Store`). Let me verify whether the truth-run alias's hygiene phase is on the v5 critical path or just a preflight, and check the `--apply-cleanup` default, the `--force` behavior, and whether scan itself walks the whole repo (perf/scope). Let me also confirm there's no `archive/` reference in the README and check the v5 runner default `repo_root` for hygiene.

Let me look at the truth-run command signature/options and the `rte run` real entry (cli.py:4920 area from the authority map).

Let me read the truth-run option definitions precisely (lines 919-990) to nail down defaults for `--skip-hygiene`, `--apply-cleanup`, `--force`, and the help text describing scope.

I have enough to characterize the apply path: `--apply-cleanup` is opt-in (`is_flag`, default False), and the quarantine logic is constrained to `extraction/repo-truth-extractor/{v3,v4}/runs` + `extraction/**/.DS_Store`, with `_is_canonical_protected` as a backstop. So the mutating path is bounded and operator-gated — that's a MED/OBS, not CRIT.

Now let me verify the two most important S8-boundary concerns with primary source:

1. **Scope/path-scoping discrepancy in the hygiene scan**: `truth_run` calls `mod.run_scan(repo_root=repo_root)` where `repo_root` = `parents[3]` (whole repo). But `extraction_hygiene._DEFAULT_RUNNER = Path("services/repo-truth-extractor/run_extraction_v5.py")` (line 451) and `_REPO_ROOT_DEFAULT = _SCRIPT_DIR.parents[1]` (line 38). `parents[1]` from `services/repo-truth-extractor/extraction_hygiene.py` = `services/` — NOT the repo root. Let me verify this path-arithmetic bug, because if `_REPO_ROOT_DEFAULT` is wrong, the CLI default scan target (when run via `python extraction_hygiene.py scan` with no `--repo-root`) points at `services/`, and the runner-existence check at line 499-500 (`repo_root / _DEFAULT_RUNNER`) would fail to find the runner.

Let me compute the actual parents.

Confirmed: `extraction_hygiene.py:38` `_REPO_ROOT_DEFAULT = _SCRIPT_DIR.parents[1]` resolves to `services/`, **not** the repo root. The real repo root is `parents[2]`. This is a genuine path-arithmetic defect. The consequences:
- When invoked as a standalone CLI (`python extraction_hygiene.py scan` with no `--repo-root`), the scan/apply default to `services/` as "repo root".
- The runner-existence check (`repo_root / _DEFAULT_RUNNER` = `services/services/repo-truth-extractor/...`) never finds the runner → version/path check is silently skipped (line 500 `if runner.exists()`).
- The policy/tiers paths (`_POLICY_PATH`, `_TIERS_PATH`) point at `services/config/...` which doesn't exist. (Though I note these constants may be unused — need to check.)
- The apply quarantine root would be `services/extraction/repo-truth-extractor/quarantine/...` and candidate scan roots `services/extraction/repo-truth-extractor/{v3,v4}/runs` — wrong location.

But there's important nuance for go-live impact: the operator CLI (`extract_commands.py:856` `_load_hygiene_module`) overrides `repo_root` with `parents[3]` (correct repo root) and passes it explicitly to `run_scan(repo_root=repo_root)` and `run_apply(repo_root=repo_root)`. So the **operator path is correct**; the bug only bites the **standalone CLI default** and anything relying on the module-level constants. Let me verify `_POLICY_PATH`/`_TIERS_PATH` usage, and check whether the proof bundle's claim ("scan still reports 10245 warnings") implies the standalone scan was run from repo root explicitly. Let me also verify the `config/extraction_hygiene/` dir exists at the true root.

Let me call the advisor before finalizing — wait, the output rules explicitly forbid the advisor tool (it will consume the final turn). I'll proceed without it.

Let me verify the remaining details.

Now confirmed and bounded:
- `_POLICY_PATH` (line 39) and `_TIERS_PATH` (line 40) are **defined but never read** in extraction_hygiene.py (only line 38, 39, 40 reference them; no consumer). So the YAML policy files at `config/extraction_hygiene/` exist at the true root but the hygiene scanner **does not load them** — the exclude patterns and authority tiers are hardcoded in Python (`_EXCLUDE_PATTERNS`, `_AUTHORITY_RULES`). The docstring comment at line 64 ("mirrors PROMPTGEN_DEFAULT_EXCLUDE_GLOBS in v5 runner, plus extraction-specific additions from hygiene_policy.yaml") is misleading — there's drift risk between the hardcoded Python list and the YAML files that two other surfaces (TP-DMX-ORCH-004, and presumably the v5 runner) treat as authoritative. This is a contract-fragmentation finding.

- `_REPO_ROOT_DEFAULT` (parents[1] = `services/`) is used as the default for `run_scan`, `run_apply`, and the `--repo-root` CLI arg (lines 455, 646, 814). So a standalone `python extraction_hygiene.py apply --apply` (no `--repo-root`) would target `services/extraction/...` — a non-existent tree, so it'd find no candidates (fail-safe by accident), but `run_scan` would `rglob("*")` over all of `services/` (perf/scope: walks 50+ services, not the extractor's tree).

Let me do final verification: (a) confirm README still documents the archive dir as if live (the worktree grep showed README:394 referencing legacy_prompts), (b) confirm output_safety has no write/path operations (it's pure-transform — verify no out-of-scope write there), and (c) check `_increment_apply_summary`/quarantine dest can't escape via symlink/`..`. Let me also sanity-check the `.DS_Store` apply loop logic which looked convoluted.

`output_safety.py` confirmed: zero filesystem operations — pure in-memory sanitization transforms. No out-of-scope-write surface there. Good (it's the safe-output writer used by the live runtime, and it only produces sanitized strings/bytes; the actual writing is done by callers).

The README at HEAD (`755bf3846`) no longer references `archive/legacy_prompts` (that hit was only in worktree copies, not main). But README:79-87 still documents v3 runner invocations as live operator commands while the engine is v5 — that's the doc-drift the authority map already flagged (pre-existing, not S8-specific). README:103 correctly documents v5 root.

Now let me nail the last two things for S8-boundaries: (1) quarantine-dest path-traversal/symlink safety in `run_apply`, and (2) the convoluted `.DS_Store` apply loop — does its `for/else/break/continue` correctly skip blocked runs, or does it have a logic bug that could quarantine files it shouldn't. And verify the `extraction/` tree it walks is even inside the service or at repo root (out-of-scope-write determination).

Interesting — there are **two** `extraction/` trees: one at repo root (`/dopemux-mvp/extraction/repo-truth-extractor/...`, the real run-output location per README:103) and one service-local (`services/repo-truth-extractor/extraction/repo-truth-extractor/`). This confirms the scope picture:

- The **correct** quarantine/scan target is repo-root `extraction/repo-truth-extractor/{v3,v4}/runs` — reached only when `repo_root` is the true root (operator CLI path: `extract_commands.py` passes `parents[3]`).
- The **buggy default** (`_REPO_ROOT_DEFAULT` = `services/`) would make `run_apply` look under `services/extraction/repo-truth-extractor/{v3,v4}/runs` — which doesn't exist, so standalone `apply --apply` finds nothing (accidental fail-safe), but standalone `scan` walks all of `services/`.

Now let me verify the quarantine destination cannot escape repo_root (path traversal / symlink), and examine the `.DS_Store` apply loop logic for a skip-blocked bug. These determine whether the bounded write path has a real escape.

Now I understand the `.DS_Store` loop. The `for version / else` construct: if a `.DS_Store` is under a blocked run (in v3 or v4), it `break`s out of the version loop (skipping the `else`), so it's NOT added as a candidate — correct skip. If `_candidate_run_dir` returns None for both versions (i.e., the `.DS_Store` is anywhere else under `repo_root/extraction/` but not inside a v3/v4 run dir), the `else` fires and it's added as a candidate. This means: a `.DS_Store` under `extraction/v4/`, `extraction/doctor/`, `extraction/prescan_v5_code_test/`, or even `extraction/repo-truth-extractor/v5/` would be quarantined. That's broader than "v3/v4 runs only" — the `.DS_Store` sweep covers the **entire** `repo_root/extraction/` subtree. It's still scoped to `extraction/` (won't touch `src/`, etc.), and `.DS_Store` is genuinely junk, so low severity, but it is a wider write radius than the FAILED-sidecar and zip sweeps (which are correctly confined to v3/v4 runs).

Now the path-traversal check on quarantine dest (line 753: `dest = quarantine_root / src.relative_to(repo_root)`). Since `src` comes from `rglob` under `repo_root`, `src.relative_to(repo_root)` is always relative and inside repo_root; `quarantine_root` is `repo_root/extraction/repo-truth-extractor/quarantine/<ts>`. The only escape vector would be a symlink in the run tree resolving outside (rglob follows symlinks for the move source). `shutil.move` on a symlink moves the link itself, not the target, so no out-of-tree destruction. Path-traversal is not exploitable here. I'll note symlink-follow as an OBS but not a finding.

Let me do one final check: confirm `extraction_hygiene.py` is NOT imported by the v5 runner itself (i.e., the runner doesn't auto-run apply), and confirm no `__main__`-level auto-execution. Then I'll write findings.

Confirmed: neither the v5 runner nor the pre-live gate imports `extraction_hygiene` or invokes `run_apply`. The only invoker of the mutating path is the operator CLI `dopemux extract truth-run --apply-cleanup` (opt-in flag). The v5 raw runner does not auto-quarantine.

I have a complete, verified picture. Let me write the final findings.

---

# RTE STAGE S8-BOUNDARIES — FINDINGS

**Scope audited:** `services/repo-truth-extractor/{output_safety.py, extraction_hygiene.py, archive/}` plus their reachability from runtime (`run_extraction_v5.py`, `validate_pre_live_gate_v25.py`, `src/dopemux/commands/extract_commands.py`, `src/dopemux/cli.py`).
**Goal:** out-of-scope writes; legacy script pollution.
**HEAD:** `755bf38460d1f2f6bba6e072ec9a627e9e218b15` (branch `main`, dirty: only unrelated `claudedocs/*` audit files).
**Authority-map claims independently re-verified:** `output_safety` importers (v5, llm_runtime, gate, lib/*, fl_int, s_int) — confirmed observed. `extraction_hygiene` is NOT imported by any runtime extractor module — confirmed.

---

- **[S8-001] HIGH — `extraction_hygiene._REPO_ROOT_DEFAULT` resolves to `services/`, not the repo root (off-by-one in `parents[]`)**
  - files: `services/repo-truth-extractor/extraction_hygiene.py:37-40` (`_SCRIPT_DIR.parents[1]`); consumed at `:455`, `:646`, `:814`; runner check `:499-501`.
  - evidence: observed. Script lives at `services/repo-truth-extractor/extraction_hygiene.py`; `parents[1]` = `/dopemux-mvp/services` (verified via `Path(...).resolve().parents`), but the real repo root is `parents[2]` = `/dopemux-mvp`. The `_DEFAULT_RUNNER = "services/repo-truth-extractor/run_extraction_v5.py"` (`:451`) joined to the buggy default yields `services/services/repo-truth-extractor/run_extraction_v5.py` (`exists()==False`, verified), so the version/path mismatch check at `:500` is silently skipped (`if runner.exists()`).
  - why it matters (bounds go-live): the operator's canonical path is *not* affected — `extract_commands.py:855-863` (`_load_hygiene_module`) recomputes `repo_root = parents[3]` (= true root, verified) and passes it explicitly to `run_scan`/`run_apply`. But any **standalone** invocation (`python extraction_hygiene.py scan|apply` with no `--repo-root`, exactly as the module docstring `:6-16` instructs) operates against `services/` as "repo root": `run_scan` walks all 50+ services via `rglob("*")` (`:469`, `:550`) instead of the extractor tree, and emits a misleading authority/noise summary; `run_apply` targets `services/extraction/repo-truth-extractor/{v3,v4}/runs` which does not exist (so it accidentally fail-safes to zero candidates). A future caller trusting the default `repo_root` gets wrong-scoped results with no error.
  - falsifying check: `python3 -c "from pathlib import Path; p=Path('services/repo-truth-extractor/extraction_hygiene.py').resolve(); print(p.parents[1])"` — if it prints `/…/dopemux-mvp` (not `/…/dopemux-mvp/services`) the finding is wrong. (Ran it: prints `…/services`.)

- **[S8-002] MED — Hardcoded exclude/authority policy in `extraction_hygiene.py` diverges from the canonical YAML it claims to mirror; `_POLICY_PATH`/`_TIERS_PATH` are dead constants**
  - files: `extraction_hygiene.py:39-40` (`_POLICY_PATH`, `_TIERS_PATH` defined), `:64` (comment "plus extraction-specific additions from hygiene_policy.yaml"), `:66-104` (`_EXCLUDE_PATTERNS` hardcoded), `:233-278` (`_AUTHORITY_RULES`/`_CONTAINS` hardcoded); canonical YAMLs at `config/extraction_hygiene/hygiene_policy.yaml` + `authority_tiers.yaml` (both exist at true root, verified).
  - evidence: observed. `grep` shows `_POLICY_PATH`/`_TIERS_PATH` are assigned (`:39-40`) and never read anywhere in the module (no `yaml.load`, no further reference). The exclusion globs and authority tiers are instead frozen in Python lists. Meanwhile `task-packets/generated/TP-DMX-ORCH-004.json:84` lists `config/extraction_hygiene/authority_tiers.yaml` as an authoritative surface, and the runner (`run_extraction_v5.py`) carries its own `PROMPTGEN_DEFAULT_EXCLUDE_GLOBS` the comment says this list "mirrors."
  - why it matters (bounds go-live): three sources of truth for the same exclusion/authority contract (Python list here, two YAMLs, v5 runner constant) with no loader binding them. Editing `hygiene_policy.yaml` (the apparent config seam) has zero effect on what the hygiene scanner actually excludes or how it tiers authority — silent contract drift on a contract-sensitive surface. The dead constants advertise a config seam that does not exist.
  - falsifying check: `grep -nE "yaml|_POLICY_PATH|_TIERS_PATH" services/repo-truth-extractor/extraction_hygiene.py` — if any line *loads* the YAML (beyond the `:39-40` assignments) the divergence is not silent. (Ran: only the two assignment lines + the runner-symbol regex; no load.)

- **[S8-003] MED — `--apply-cleanup` quarantine performs real `shutil.move()` across the whole repo tree, scoped only by hardcoded prefixes + a backstop allowlist**
  - files: `extraction_hygiene.py:645-800` (`run_apply`), mutation at `:776` (`shutil.move`); reachable via `src/dopemux/commands/extract_commands.py:1160-1163` (`mod.run_apply(repo_root=repo_root, dry_run=False)`), exposed as `dopemux extract truth-run --apply-cleanup` (`extract_commands.py:923-925`, `is_flag`, default False).
  - evidence: observed. The mutating path is opt-in (flag default False) and gated behind a hygiene scan; candidate sweeps are confined to `repo_root/extraction/repo-truth-extractor/{v3,v4}/runs` for FAILED-sidecars (`:667-693`) and zips (`:715-735`), with `_is_canonical_protected` (`:574-606`, blocks `src/`, `.claude/`, `config/`, `services/`, etc.) as a final backstop (`:750-752`). Destination is always `quarantine_root / src.relative_to(repo_root)` (`:753`), so it cannot escape `repo_root`. v5 runner and the pre-live gate do **not** import or call `run_apply` (verified empty grep) — only the operator CLI does.
  - why it matters (bounds go-live): this is the single out-of-scope-write surface in the stage. Blast radius is bounded today (opt-in, prefix-scoped, allowlist backstop, in-tree dest), so it does not *block* go-live, but it is a destructive operator action whose scope is governed entirely by hardcoded string prefixes rather than the YAML policy of S8-002 — a quiet coupling between a "cleanup" UX and the path-arithmetic correctness of `repo_root`. Combined with S8-001, a mis-scoped `repo_root` is the only thing standing between this and the wrong tree.
  - falsifying check: `grep -n "shutil\|move\|rmtree\|unlink" services/repo-truth-extractor/extraction_hygiene.py` then confirm every mutation sits under the `if dry_run: return plan` guard at `:768-769`. If a mutation precedes that guard, the dry-run contract is broken (it does not — all moves are at `:772-783`, after the guard).

- **[S8-004] LOW — `.DS_Store` quarantine sweep covers the entire `repo_root/extraction/` subtree, wider than the v3/v4-runs scope used by the other two sweeps**
  - files: `extraction_hygiene.py:695-712` (`for ds in (repo_root / "extraction").rglob(".DS_Store")`).
  - evidence: observed. The FAILED-sidecar (`:667`) and zip (`:715`) sweeps iterate only `extraction/repo-truth-extractor/{v3,v4}/runs`. The `.DS_Store` sweep instead `rglob`s all of `repo_root/extraction/` and, via the `for…else` (`:698-712`), quarantines any `.DS_Store` **not** inside a blocked v3/v4 run — i.e. it will also move `.DS_Store` from `extraction/v4/`, `extraction/doctor/`, `extraction/prescan_v5_*`, and `extraction/repo-truth-extractor/v5/`. (Repo-root `extraction/` confirmed to contain `v4/`, `doctor/`, `prescan_v5_code_test/`, etc.)
  - why it matters: inconsistent scoping; only matters when `--apply-cleanup` is used. `.DS_Store` is genuine OS junk so data-loss risk is negligible, but the asymmetry means the v5 proof/run tree (`extraction/repo-truth-extractor/v5/`) gets touched by a sweep the other buckets deliberately exclude. Does not block go-live.
  - falsifying check: place an empty `extraction/repo-truth-extractor/v5/proofs/.DS_Store`, run `python extraction_hygiene.py apply --repo-root <root> --bucket os_artifact` (dry-run) and confirm whether it appears as a planned `os_artifact` action. If it is excluded, this finding is wrong. (NOT_RUN — read-only contract; logic trace shows it would be included.)

- **[S8-005] OBS — `output_safety.py` is a pure in-memory sanitizer with no filesystem operations; no out-of-scope-write surface, but it is load-bearing for proof-bundle integrity**
  - files: `services/repo-truth-extractor/output_safety.py` (entire, 281 lines); importers: `run_extraction_v5.py`, `llm_runtime.py`, `validate_pre_live_gate_v25.py`, `lib/batch_clients.py`, `lib/risk_dashboard.py`, `fl_int/run_fl_int.py`, `lib/prescan/grok_passes.py`, `s_int/run_s_int.py` (verified).
  - evidence: observed. `grep` for write/open/mkdir/shutil/os-mutation in `output_safety.py` returns nothing — it only does regex substitution and `json.dumps` (`:257`, `:274`). It produces sanitized strings/bytes; callers own the actual disk writes. So the module itself cannot write out of scope.
  - why it matters: not a defect — recorded so S8-boundaries explicitly confirms the "safe output writer" introduces no write surface. The corollary risk lives in callers: anything that writes a proof/sidecar/report must route through `sanitized_json_bytes`/`sanitize_payload_for_*`; a caller bypassing these would leak secrets into on-disk artifacts. That caller-side audit is out of this stage's three files but should be a S-series follow-up.
  - falsifying check: `grep -nE "open\(|write_(text|bytes)|mkdir|shutil|os\.(remove|rename|makedirs|unlink)" services/repo-truth-extractor/output_safety.py` — any hit disproves "no filesystem ops." (Ran: none.)

- **[S8-006] OBS — `archive/legacy_prompts/` (38 files) and `archive/legacy_artifact_gates/` (2 files) are unreferenced dead pollution, not reachable legacy scripts**
  - files: `services/repo-truth-extractor/archive/legacy_prompts/*.md` (38), `archive/legacy_artifact_gates/{R_REQUIRED_ARTIFACT_GROUPS_BASE,FULL}.json` (2).
  - evidence: observed. Repo-wide grep for `repo-truth-extractor/archive`, `legacy_artifact_gates`, and `R_REQUIRED_ARTIFACT_GROUPS` returns **no** runtime reference to these files: the `R_REQUIRED_ARTIFACT_GROUPS` symbol is defined fresh in `run_extraction_v5.py:544` and `run_extraction_v3.py:241` (Python dicts), not loaded from the archived JSON; all archive-name hits are in `.claude/worktrees/*` copies or `docs/`. The legacy_prompts `.md` files are not on any prompt-resolution path (`rte_promptset.py` resolution order targets `promptsets/v4/prompts/`, `prompts/v3/`, `prompts/phase_s/` — never `archive/`). No `.py` lives under `archive/`, so there is no executable legacy script here, only inert content.
  - why it matters: pure workspace clutter — these 40 inert files are dead weight, not an execution or contract hazard. They do **not** block go-live. The genuine "legacy script pollution" risk (a still-live `run_extraction_v3.py` with its own `DPMX_LIVE_OK`-gated `--execute`) lives outside this stage's three files (it is `run_extraction_v3.py` at the service root, already flagged by the authority map as fragmentation risk #2) — `archive/` is not where that risk resides.
  - falsifying check: `grep -rn "archive/legacy_prompts\|archive/legacy_artifact_gates" --include="*.py" services/repo-truth-extractor/ | grep -v tests/` — any non-test runtime hit disproves "unreferenced." (Ran: none.)

---

## Summary

| ID | Sev | One-line |
|----|-----|----------|
| S8-001 | HIGH | `_REPO_ROOT_DEFAULT = parents[1]` points at `services/`, not repo root; mis-scopes standalone scan/apply and silently disables the version/path check (operator CLI path unaffected — it overrides `repo_root`). |
| S8-002 | MED | Hardcoded Python exclude/authority policy diverges from canonical `config/extraction_hygiene/*.yaml`; `_POLICY_PATH`/`_TIERS_PATH` are never loaded — silent contract drift. |
| S8-003 | MED | `--apply-cleanup` does real `shutil.move()` over the repo tree; bounded (opt-in, prefix-scoped, allowlist backstop, in-tree dest) but is the stage's only write surface, coupled to S8-001's `repo_root` correctness. |
| S8-004 | LOW | `.DS_Store` quarantine sweep spans all of `extraction/`, wider than the v3/v4-runs scope of the other buckets (touches the v5 proof tree). |
| S8-005 | OBS | `output_safety.py` is a pure sanitizer — zero filesystem ops, no write surface; risk is caller-side bypass (out of stage). |
| S8-006 | OBS | `archive/` (40 inert files) is unreferenced dead clutter; the real live-legacy risk (`run_extraction_v3.py --execute`) is outside this stage. |

**Out-of-scope-write verdict:** one real write surface (`extraction_hygiene.run_apply`, S8-003), opt-in and bounded today; its safety depends on `repo_root` being correct, which the off-by-one in S8-001 silently breaks for any non-operator caller. No write surface in `output_safety.py`. 
**Legacy-pollution verdict:** `archive/` is inert dead files (S8-006), not reachable scripts — cosmetic. No archived JSON/prompt is loaded by the v5 runtime.

**Validation buckets:** PASS — path-arithmetic (S8-001), dead-constant (S8-002), no-fs-ops (S8-005), unreferenced-archive (S8-006), no-runner-import-of-apply (S8-003) all verified by read-only inspection / `python3 -c` path resolution. NOT_RUN — S8-004 dynamic dry-run trace (read-only contract; logic-traced only) and any live `extraction_hygiene apply` execution; human-verify command given inline. FAIL — none.
**Files touched:** none (read-only audit).
**Remaining uncertainty:** I did not exhaustively confirm every `output_safety` *caller* routes on-disk writes through the sanitizer (S8-005 corollary) — that spans files outside this stage. The v5 runner's `PROMPTGEN_DEFAULT_EXCLUDE_GLOBS` vs the hygiene Python list (S8-002) were not diffed line-by-line.

==========================================================================================
## CLI  (root-cause-analyst, a2b7a30e8a8bdf644, 5182 chars)
==========================================================================================

I'll audit the dopemux/RTE CLI systematically. Let me start by orienting myself to the command surfaces, then trace call paths to verify the classification of each command.

This is a large surface. Let me orient on the structure before diving deep. I'll read the CLI entry point's command registration, the `LegacyReplacementCommand` mechanism (critical for reachability), and the RTE ops surfaces in parallel.

This is a Click-based CLI. Let me read the critical structural pieces: the `LegacyReplacementCommand` class, the RTE group definition, and the `truth` command — these are the highest-risk areas mentioned in the task.

I have the structure. There's an important nuance already: the `rte` group has BOTH a native `scan` command (cli.py:4958) AND aliased commands from `upgrades`/`extractor` (cli.py:5596-5625). Let me read the rest of the `rte` wiring, the `truth` command, and the three `LegacyReplacementCommand` blocks (4194, 4408, 4819) to understand what's shadowed vs reachable.

Now I have the key structural facts. Let me look at the critical execution-class commands and their consent gating. I need to trace: (1) `rte list`/`extractor_list` — the known regression — to verify whether it runs prescan/LLM now; (2) the `_run_extractor_runner` helper to understand dry-run/execute; (3) the `extractor` group definition and `LegacyReplacementCommand` at 3170 and 4408/4819.

Let me read the extractor command helpers and the remaining legacy-replacement blocks in parallel.

Now let me read the two critical runner helpers (`_run_extractor_runner` at 481, `_run_repscan_runner` at 505) and the command bodies in `extractor_commands.py` that get aliased into `rte`. This is the core of the consent/execute gating analysis.

Now the command bodies in `extractor_commands.py`. These are aliased into `rte` as `list`, `run`, `doctor`, `status`, `preflight`, `validate-live`, `trace`. But wait — at cli.py:5027+ I saw `extractor_list`, `extractor_run` etc. are defined as `@upgrades.command(...)` in **cli.py**, not in extractor_commands.py. Let me check what's actually in extractor_commands.py vs cli.py, and reconcile the aliasing.

Now the picture is clear. The `rte` subcommands (`list`, `run`, `doctor`, `status`, `preflight`, `validate-live`, `trace`) are the `@upgrades.command(...)` functions defined in **cli.py** (5027-5547), which call `_run_extractor_runner`. The `extractor` group in extractor_commands.py (with `prescan`, `init`, `run`, `status`, `validate`) is the OLD cockpit — but it's shadowed by `LegacyReplacementCommand` at cli.py:3170.

Let me read all seven rte-aliased command bodies in cli.py (5027-5547) carefully — these define the actual operator surface and its execute/consent semantics. This is the heart of the audit.

I have the full operator-surface picture for `rte run`. The dry-run/execute split is correct: `--dry-run/--execute` defaults to dry-run=True (5072), and live LLM spend requires the explicit `--allow-online-llm` flag forwarded to v5 (5126, 5252). Now let me verify the most critical claim in the task: **does `rte list` (extractor_list) trigger a prescan/LLM?** And check `rte status`/`trace`. 

The `extractor_list` body (5030-5057) calls `_run_extractor_runner` with `["--print-config"]` for non-v4, or `["--promptset-audit", "--no-strict-audit"]` for v4. I need to verify what v5's `--print-config` and `--status` actually do in the runner — whether they trigger prescan. Let me check v5's argparse handling of these flags, and trace whether `--status`/`--print-config`/`--preflight-providers` are read-only.

This is the crux. v5's `main()` has an introspection short-circuit. Let me read the exact control flow at lines 22019-22090 and 22460-22530 and 22640-22810 to verify that `--print-config`, `--status`, `--preflight-providers` exit BEFORE prescan/extraction runs. The known regression was `rte list` running a full prescan. Let me confirm whether the current code short-circuits.

Now I need to verify the most important question: where does `readonly_introspection` get computed, and does it short-circuit BEFORE `run_integrated_prescan_stage`? `args.status` exits at 22525 (before prescan). But `--print-config` and `--preflight-providers` — I need to confirm they exit before prescan too. Let me read 22640-22820 (where print_config and preflight_providers are handled) and find where `readonly_introspection` is defined and where prescan is invoked in main.

**Verified — the known `rte list` prescan regression is fixed.** `--print-config` exits at line 22645 via `sys.exit(0)`, which is BEFORE the prescan stage at line 22700. Similarly `--preflight-providers` exits at 22673, `--status` at 22526, `--doctor` at 22687 — all before prescan. The introspection short-circuit block (22643-22687) precedes `run_integrated_prescan_stage` (22701).

Now let me verify the `readonly_introspection` definition and the earlier short-circuits (around 3129-3245 which looked like a cost-preview path), plus confirm `rte status` (`run_status_loop`) is read-only and doesn't have a watch-loop that polls forever. Let me also check `--preflight-providers` `run_provider_preflight` with `persist_run_root=False` — does it make network calls?

==========================================================================================
## INSTALL  (devops-architect, a173fd39a54c26c75, 35571 chars)
==========================================================================================

I'll audit the install/bootstrap path without executing anything. Let me start by orienting myself to the canonical documented path and the installer files.

The canonical path uses `install.sh` (57KB at root) and `INSTALL.md`, not `scripts/install.py`/`scripts/setup.sh`. There's also `installers/` and `test_installer_*.sh`. Let me establish the documented canonical path first by reading the docs, then map all installers.

The README/QUICK_START canonical path is now clear: `uv sync --frozen --extra dev` + manual `docker compose -f compose.yml up -d --build`. Notably, **neither doc mentions `install.sh`, `scripts/install.py`, `scripts/setup.sh`, or `installers/`** — those are legacy/alternate. Let me confirm what `INSTALL.md` documents and what `installers/` contains, then read the actual installer scripts.

Now I have the canonical picture. Key finding emerging: `scripts/install.py` is a **standalone-CLI installer** that's divergent from the canonical `install.sh`/compose path — and crucially, **neither `scripts/install.py` nor `scripts/setup.sh` is referenced by README/QUICK_START/INSTALL.md**. Let me check the bash logging bug in install.py (the `logger.info("...", var)` calls won't interpolate), then read the canonical `install.sh` and the rest of the targets. Let me also verify references.

There's a prior audit at `claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md` that covered much of this same ground. I should not duplicate it blindly — I'll verify the key claims myself against current source (it's dated today, but the contract here is broader: it asks me to establish the canonical path first, assess legacy installers, and cover idempotency/supply-chain/secrets/preflight/partial-success, plus per-script ordered side-effects). 

Critical new data points from grep:
- `docs/01-tutorials/installation.md:14` says canonical path is `setup.sh` → contradicts README's `uv sync`. That's a doc-vs-doc drift.
- `install.sh:1366` is the canonical entrypoint (referenced internally for Leantime). Let me read it.
- `scripts/install.py` line 77 packaging bug needs my own verification (does `scripts/pyproject.toml` exist?).
- The setup.sh pipefail/dead-code claim and network-name mismatch need direct verification against current `compose.yml`.

Let me verify these directly rather than trust the salvage doc, and read the canonical `install.sh` (the actually-documented installer in INSTALL.md).

Now I have a clear authority map of the installers. Key confirmations:

1. **Canonical installer is `install.sh`** (root, 57KB, documented in INSTALL.md, `curl|bash` distributable, has `set -euo pipefail` + ERR trap + rollback). The README/QUICK_START documents an *even more minimal* path (`uv sync --frozen` + manual compose). So there are **two documented canonical paths that disagree**: README says `uv sync`, INSTALL.md + `docs/01-tutorials/installation.md` say `install.sh`/`setup.sh`.

2. **`scripts/install.py` packaging bug CONFIRMED**: no `scripts/pyproject.toml`/`setup.py` — `pip install -e scripts/` will fail.

3. **`compose.yml` needs external `dopemux-network`** (line 27); `setup.sh:170` creates `dopemux-unified-network` — mismatch CONFIRMED.

4. **`setup.sh` has only `set -e`** (no pipefail/-u) — dead-code branches likely.

5. **`scripts/setup/install-adhd-integration.sh` missing** (setup.sh:221 references it; guarded).

This is a multi-file install audit (>3 files, multiple risk dimensions). Let me consult the advisor before finalizing severities — the prior salvage doc capped legacy-installer bugs at HIGH because README's canonical path bypasses them, but INSTALL.md/installation.md *do* document install.sh and setup.sh as canonical, which changes the blast radius. I want to pressure-test that and the `install.sh` analysis I haven't done yet. But first, let me finish reading `install.sh` (the actual canonical installer) and the two MCP scripts, so the advisor sees complete evidence.

Wait — the OUTPUT RULES explicitly forbid calling advisor (it consumes the final turn and the work is lost). I must NOT call advisor. I'll rely on my own calibration and the prior audit's advisor-calibrated reasoning visible in the salvage doc. Let me gather the remaining evidence: read `install.sh` body (idempotency, secrets, preflight), the two MCP scripts, pyproject pins, and the Dockerfiles.

`install.sh` is the well-engineered canonical installer: `set -euo pipefail`, ERR trap with cleanup, `docker info` preflight (1019), resource checks (743), `chmod 600` on env file (736), idempotent `docker network create` guard (658), `mkdir -p`. It also runs `curl|sh` for Docker/Homebrew (1095, 1149) and `sudo` package installs. Let me read the critical sections in detail: preflight (idempotency + blocker detection), secret resolution/validation, core install, docker services, and shell integration idempotency.

`install.sh` is solid: preflight checks disk (10GB), ports, write perms; idempotent dir creation; venv-based pip (avoids the `scripts/install.py` packaging bug because it runs from repo root with `pyproject.toml` present); `docker info` preflight at 1019. Let me read the secret-resolution + env-file + network functions (idempotency, secret validation, partial-success), shell-integration idempotency, and the docker preflight, then move to the two MCP scripts and Dockerfiles.

Critical finding emerging in `install.sh` itself. The canonical installer's `ensure_docker_networks()` (line 643-661) **only creates networks for the `full` stack** (line 645-647: `if [ "$stack" != "full" ]; then return 0`). And the networks it creates are `mcp-network`, `dopemux-unified-network`, `leantime-net` — **NOT `dopemux-network`**, which is the external network `compose.yml:25-27` actually requires. So:

- For **core/research** stacks, `install.sh` creates **no network at all**, then runs `docker compose -f compose.yml up -d` (line 1359), which will fail because `dopemux-network` (external) doesn't exist.
- For **full** stack, it creates three networks, none of which is `dopemux-network`.

This is a genuine break in the canonical `install.sh` path — more severe than the salvage doc found (which focused on `setup.sh`). Let me verify the network names compose actually declares vs what install.sh creates, and check whether compose has additional networks beyond `dopemux-network`.

Confirmed beyond doubt: **`compose.yml` declares exactly ONE external network, `dopemux-network` (lines 25-27), used by all 23 services. `install.sh` NEVER creates `dopemux-network`** — for core/research it creates no network; for full it creates `mcp-network`/`dopemux-unified-network`/`leantime-net` (line 652). So the canonical `install.sh` → `docker compose up -d` (line 1359) fails on the external-network precondition for every stack. The env-file handling is good (mktemp + atomic mv + chmod 600, dedup-merge = idempotent).

This is materially more severe than the salvage doc's framing — that doc looked at `setup.sh` (which creates the wrong-named network) but I've now found the *documented canonical installer* `install.sh` has the same class of break. Let me check `check_docker` preflight (does it detect the disk/VM blocker?), the `--verify`/`--uninstall` idempotency, then read the two MCP scripts and Dockerfiles, and pyproject pins.

`check_docker` (1019) detects daemon-not-running, but **`docker info` succeeding does NOT detect the Docker-VM-disk-exhaustion blocker** (the memory note: "Docker VM disk"). `docker info` returns 0 even when the VM disk is full; the failure surfaces later at `docker compose pull/up`. Disk preflight at 1235 checks `$HOME` free space (host), not the Docker VM's allocated disk — those are different on macOS Docker Desktop. So the known "Docker VM disk" blocker is NOT preflighted. Let me read the two MCP scripts (supply-chain: curl|sh, git clone unpinned, auto-run with keys) and pyproject pins + Dockerfiles in parallel.

`install-docker-mcp-servers.sh` confirms supply-chain issues:
- Line 57: `git clone <repo> .` at HEAD (unpinned, no `--branch`/SHA pin) — third-party `mcp-server-mas-sequential-thinking` from `FradSer/`.
- Line 54: `git pull origin main` on update (mutable HEAD).
- Lines 63-84: writes operator API keys (DEEPSEEK/OPENAI/GITHUB/EXA) into a `.env` **with no chmod 600** (world-readable per umask).
- Line 303: **auto-builds and runs** the cloned third-party code via `start-all-mcp-servers.sh` (line 240 `docker-compose up -d --build`) — executing unpinned remote code with secrets injected.
- `mas-sequential-thinking` is provisioned here but **absent from canonical `compose.yml`** (which ships `pal` at line 273) — stale per the salvage doc.

Also it depends on legacy `docker-compose` (v1, line 105/240), and is referenced by `scripts/deploy/setup/install-mcp-servers.sh:128`. Now let me read `mcp-proxy-setup.sh`, pyproject pins, and the Dockerfiles.

`mcp-proxy-setup.sh` is well-formed (`set -euo pipefail`, idempotent `claude mcp remove ... || true` before add, PID-file lifecycle). But it's **stale**: targets `mcp-mas-sequential-thinking`, `mcp-zen`, `mcp-claude-context` (line 53) — containers that don't exist in canonical `compose.yml` (which has `mcp-pal`, `mcp-conport`, `mcp-dope-context`). Line 44 `uv tool install mcp-proxy` is unpinned. Line 8: `PROXY_PORT=8080` collides with Leantime's `8080` (compose.yml:118 / README:118). It's only referenced by archived docs, so blast radius is low. Now pyproject pins + Dockerfiles.

pyproject pins: almost all runtime deps are **lower-bound only (`>=`)** — `click>=8.0.0`, `openai>=1.50.0`, `pymupdf>=1.23.0`, etc. The only exact pins are `dopetask==0.5.1` and the `tree-sitter-*` grammars (`==0.23.0`). `fastmcp` and `rank_bm25` (lines 97, 114) have **no version bound at all**. The canonical install path is `uv sync --frozen --extra dev` (README:83) which uses `uv.lock` for reproducibility — so the lockfile, not pyproject, is the supply-chain control for the documented path. But `install.sh`/`setup.sh`/`install.py` all use `pip install -e .` / `pip install -e .` (no lock), so those paths get unpinned floating deps. Let me verify `uv.lock` exists, check `black` target-version mismatch (line 147 `py38` vs `requires-python>=3.11`), then read the two Dockerfiles and the dope-context Dockerfile (pymupdf source-build risk).

Important findings:
- **`uv.lock` exists** (1.1MB, dated May 24) — so the canonical `uv sync --frozen` path IS reproducible. Supply-chain risk is confined to the `pip install -e .` legacy installers, which float all `>=` deps.
- **Root `Dockerfile:27`** uses `pip install --no-cache-dir .` (bare `.`, no extras, **no lock**) — floating `>=` deps at build time, non-reproducible image builds.
- **`Dockerfile.frontend:3,15,31`** uses `FROM dhi.io/node:18-alpine` — a **private/authenticated registry** (`dhi.io` = Docker Hardened Images, requires entitlement). No preflight; if the registry isn't authenticated, the build fails with an auth error. Plus `npm ci --only=production && npm install` (line 11) is contradictory/non-deterministic.
- Root Dockerfile is otherwise good: multi-stage, non-root user, healthcheck.

Now let me verify whether `Dockerfile.frontend` is even built by canonical `compose.yml` (blast radius), and read the dope-context Dockerfile for the pymupdf source-build claim, plus check `black` target-version.

Now I have the full picture:

- **`Dockerfile.frontend` is NOT referenced by `compose.yml` or any compose file** — it's orphaned. So the `dhi.io` private-registry risk has **zero blast radius on the canonical path** (downgrades it to LOW/OBS).
- **`services/dope-context/Dockerfile:18`** uses `uv pip install --system --no-cache .[services]` → installs `pymupdf>=1.23.0`. It has `build-essential` (line 13) so a source-build would succeed if no wheel matches. pymupdf ships manylinux cp311 wheels for 1.23+, so this is a latent slow-build risk, not a break. **`.[services]` does NOT use the lockfile** → floating deps in the image (same non-reproducibility class as root Dockerfile).
- **Root Dockerfile health-check** `|| exit 1` (good); dope-context healthcheck uses `|| exit 0` (line 36) — **healthcheck can never report unhealthy**, masking failures (a partial-success-looks-complete issue, but service-level not install-level).
- `compose.yml` builds 14 services from local Dockerfiles with `context: .` (root) — heavy first build.

I have enough evidence across all required dimensions. Let me do two final verifications: the `--verify`/uninstall idempotency in install.sh and confirm `ai_startup.sh`/`start.sh` (the scripts that DO create `dopemux-network` correctly, to nail the install.sh network finding as a real gap vs a workaround that exists elsewhere).

This nails the most important finding. The grep output shows `rg` collapsed the literal into `n` (display artifact from a variable named `n`), but the substance is confirmed: `start.sh`, `smoke_up.sh`, `consolidate_docker_networks.sh` all do `docker network inspect <net> || create` for the network compose needs. Crucially:

- **`install.sh` `main()` (1788) → `install_docker_services` (1588/1628) → `ensure_docker_networks` (1340), which returns early for non-full stacks (line 645) and never creates `dopemux-network`** for ANY stack. The network compose requires (line 27) is created ONLY by `start.sh`/`smoke_up.sh`, which `install.sh` does NOT invoke.
- **`test_installer_basic.sh:49,58` runs ONLY with `INSTALLER_TEST_MODE=1`** — and every Docker/network/compose operation is guarded by `if [ "$INSTALLER_TEST_MODE" = "1" ]; then ...skip...` (lines 648, 1342, etc.). So **the installer's tests exercise the skip-branches and never test real network/compose creation** — the network break is invisible to CI. This is a textbook "partial-success-that-looks-complete": tests pass green, real installs break.

Let me do a final confirmation of the `ensure_docker_networks` early-return and read the `--verify`/`--quick`/`--full` main dispatch + uninstall to assess idempotency and the documented-but-untested gap, then I'll write findings.

I now have complete evidence across every dimension the contract asked for (canonical path, idempotency, supply-chain, secrets, preflight blockers, partial-success-looks-complete, per-script side effects). 

`uninstall_dopemux` is reasonable (backup before delete, `down -v`, best-effort PATH cleanup) but note line 1680/1691: `--profile full ... down -v` always passes `-v` (destroys named volumes including Leantime MySQL data) and `sed '/# Dopemux/,+3d'` assumes a fixed 4-line block (fragile if `configure_shell_integration` wrote a different shape). Minor.

One last check: confirm `ensure_docker_networks` early-return is the *only* network-creation path in install.sh and that the README/QUICK_START canonical path (which manually creates `dopemux-network`) is the one that works — so I can correctly scope the network finding to the `install.sh`/`setup.sh` installers, not the documented `uv sync` + manual-compose path.

All claims are now verified at file:line. The picture is complete and consistent:

- **Canonical documented path = README/QUICK_START/`docs/01-tutorials/quickstart.md`**: `uv sync --frozen --extra dev` → manual `docker network inspect dopemux-network || docker network create dopemux-network` → `docker compose -f compose.yml up -d --build`. This path is **reproducible (uv.lock) and correct** (manually creates the external network).
- **Conflicting documented path = INSTALL.md + `docs/01-tutorials/installation.md`**: `./install.sh` / `setup.sh`. These installers have the network break and never create `dopemux-network`.
- `install.sh` last touched 2026-05-02; `compose.yml` last touched 2026-05-15 (13 days later) — drift window confirmed. `install-docker-mcp-servers.sh` last touched 2026-01-20 (4 months stale).

I have everything required. Writing the final findings now.

---

# Install / Bootstrap Audit — `dopemux-mvp` (READ-ONLY, nothing executed)

## Canonical path established first (authority resolution)

There are **two mutually inconsistent "documented canonical" install paths**, and they disagree on the entrypoint:

| Source | Documented install |
|---|---|
| `README.md:80-92`, `QUICK_START.md:7-20`, `docs/01-tutorials/quickstart.md:49-54` | `uv sync --frozen --extra dev` → manual `docker network create dopemux-network` → `docker compose -f compose.yml up -d --build` |
| `INSTALL.md:9-17`, `docs/01-tutorials/installation.md:14` | `./install.sh` (or `setup.sh`) "one-command" |

**The `uv`-based README/QUICK_START path is the only sound one** (observed): `uv.lock` exists (1.1 MB, `compose.yml`-era), so `--frozen` is reproducible, and it manually creates the external network compose requires (`README.md:89-90`). Per Truth Order, runtime/compose + the path that actually works outranks the older `install.sh`-centric docs. The installers (`install.sh`, `scripts/setup.sh`, `scripts/install.py`, `scripts/install-docker-mcp-servers.sh`, `scripts/mcp-proxy-setup.sh`) are **legacy/alternate**: none is referenced by README/QUICK_START; `install.sh`/`setup.sh` are referenced only by INSTALL.md and `docs/01-tutorials/installation.md` (a doc that still says canonical = `setup.sh`). Staleness (git log, observed): `install.sh` `4959a089f` 2026-05-02; `compose.yml` `1a1a82384` 2026-05-15 (13-day drift after the installer was last touched); `install-docker-mcp-servers.sh` `586ca44a4` 2026-01-20 (~4 months stale).

This audit overlaps a prior one (`claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md`); I re-verified every borrowed claim against current source and **found one break that prior audit missed**: the network defect is present in `install.sh` itself (the *documented* installer), not only in `setup.sh`. Findings below are independently confirmed.

---

## Findings

- **[INST-01] HIGH — `install.sh` (the documented installer) never creates `dopemux-network`; every stack's compose-up precondition is unmet**
  - files: `install.sh:643-661` (`ensure_docker_networks`), `install.sh:1340` (only caller), `install.sh:1359` (`docker compose ... up -d`); `compose.yml:25-27` (external `dopemux-network`, used by all 23 services e.g. `:58,:276,:325`)
  - evidence: observed. `ensure_docker_networks` returns early for any non-`full` stack (`:645-647 if [ "$stack" != "full" ]; then return 0`). For `full` it creates `mcp-network`, `dopemux-unified-network`, `leantime-net` (`:652`) — **not** `dopemux-network`. `rg "dopemux-network" install.sh` → no match (install.sh never creates it). `compose.yml:26 external: true` means Docker will not auto-create it; the correct `inspect || create` lives only in `scripts/start.sh`, `scripts/smoke_up.sh`, `scripts/consolidate_docker_networks.sh` (observed), none of which `install.sh` invokes.
  - why it matters (blocks go-live via this path): `./install.sh --quick`/`--full`/`--verify` → `install_docker_services` → `docker compose -f compose.yml up -d` fails with `network dopemux-network declared as external, but could not be found` for core **and** research stacks; full stack also fails (wrong network names). The documented `uv sync` path is unaffected because README:89-90 creates the network manually. So: installer-via-`install.sh` is broken; documented-via-README is fine.
  - falsifying check: `INSTALLER_TEST_MODE=0 ./install.sh --quick` in a clean env with `docker network rm dopemux-network` first — disproven if compose comes up healthy without a manual `docker network create dopemux-network`.

- **[INST-02] HIGH — Installer test harness runs only in `INSTALLER_TEST_MODE=1`, which dead-codes every Docker/network/compose step → green tests, broken real install (partial-success-that-looks-complete)**
  - files: `test_installer_basic.sh:49,58` (both invocations force `INSTALLER_TEST_MODE=1`); skip-guards at `install.sh:648,747,1008,1226,1298,1342,1376,1443`
  - evidence: observed. Test mode early-returns from `ensure_docker_networks` (`:648-650`), `check_system_resources` (`:747`), `check_docker` (`:1008`), `preflight_checks` (`:1226-1229`), `install_dopemux_core` (`:1298`), `install_docker_services` pull/up (`:1342-1346`), `configure_shell_integration` (`:1376`), `verify_installation` (`:1443`). The harness passes `--quick`/`--full`/`--verify` but exercises the skip branches.
  - why it matters (bounds confidence): CI cannot catch INST-01 or any compose/network regression — exactly why a 13-day `compose.yml` drift produced an undetected break. The installer's "tested" status does not cover the side-effecting path. Treat all install.sh runtime behavior as `NOT_RUN`.
  - falsifying check: grep `test_installer_basic.sh` for any invocation without `INSTALLER_TEST_MODE=1` that creates a real network/container — disproven if a real-mode integration test exists.

- **[INST-03] HIGH — `scripts/install.py` venv installer is structurally broken: `pip install -e <scripts/>` with no build metadata there**
  - files: `scripts/install.py:77` (`current_dir = Path(__file__).parent`), `:78-80` (`pip install -e str(current_dir)`)
  - evidence: observed. `__file__.parent` resolves to `scripts/`; `ls scripts/pyproject.toml scripts/setup.py scripts/setup.cfg` → all "No such file or directory". `pip install -e scripts/` fails with "neither 'setup.py' nor 'pyproject.toml' found." The comment "from current directory" is wrong — it's the script's dir, not CWD.
  - why it matters: this standalone-CLI installer can never install the package; `install_package()` raises and `main()` exits non-zero. Low blast radius (no doc references it), but it is a dead, advertised-looking entrypoint. (Secondary: `:24,:36,:44` etc. use `logger.info("text", var)` — logging treats `var` as an unused arg, so messages never interpolate; cosmetic.)
  - falsifying check: `python scripts/install.py` in a clean venv — disproven if it produces a working `dopemux` launcher.

- **[INST-04] HIGH — `scripts/setup.sh` (`set -e` only, no `pipefail`) silently reports success on compose failure, and creates the wrong network name**
  - files: `scripts/setup.sh:13` (`set -e`, no `-u`/`pipefail`), `:170` (creates `dopemux-unified-network`), `:178-183` (`docker compose ... up -d 2>&1 | tail -5` inside `if`), `:240-241` success banner; `compose.yml:25-27` (needs `dopemux-network`); `scripts/consolidate_docker_networks.sh` (documents `dopemux-unified-network` as the *legacy* network being removed)
  - evidence: observed. With only `set -e`, the `if docker compose … | tail -5` evaluates `tail`'s exit (always 0), so the `else … exit 1` (`:181-183`) is **dead code** → compose failure still prints "✅ MCP services started" and reaches the "Setup Complete" banner. Independently, `:170` creates `dopemux-unified-network` while compose needs `dopemux-network` — so even the success message is on a non-functional stack.
  - why it matters: documented by `docs/01-tutorials/installation.md:14` as the canonical quick start, yet it can claim a clean install over a stack that never started. Combines INST-01-class network break with masked failure.
  - falsifying check: `bash scripts/setup.sh` with the Docker daemon stopped — disproven if it exits non-zero instead of printing the success banner.

- **[INST-05] HIGH — `scripts/install-docker-mcp-servers.sh`: unpinned third-party `git clone` at HEAD, secrets written world-readable, then auto-built and run**
  - files: `scripts/install-docker-mcp-servers.sh:57` (`git clone <repo> .`, no SHA/tag), `:54` (`git pull origin main` on update), `:63-84` (writes `DEEPSEEK/OPENAI/GITHUB/EXA` keys into `.env`, **no `chmod 600`**), `:303` (`./start-all-mcp-servers.sh` → `:240` `docker-compose up -d --build`); referenced by `scripts/deploy/setup/install-mcp-servers.sh:128`
  - evidence: observed. Clones `github.com/FradSer/mcp-server-mas-sequential-thinking` at mutable HEAD (supply-chain: no pin, no checksum), injects operator API keys into a plaintext `.env` left at default umask, then builds and runs that code unattended (`:303`). The provisioned service `mas-sequential-thinking` is **absent from canonical `compose.yml`** (which ships `mcp-pal` at `compose.yml:273`) → stale bootstrap. Also depends on legacy `docker-compose` v1 (`:105,:240`).
  - why it matters: executing unpinned remote code with live credentials is a real supply-chain/secret-exposure path; provisioning a server the canonical stack abandoned is drift. Low blast radius (only an internal deploy script references it), so HIGH not CRIT.
  - falsifying check: `rg -n "mas-sequential" compose.yml` → 0 matches confirms staleness; inspect generated `.env` perms (`stat -f '%Sp' docker/mcp-servers/*/.env`) after a run — disproven only if perms are `600`.

- **[INST-06] MED — No preflight for the known "Docker VM disk" blocker; `docker info` and a `$HOME` df check don't cover it**
  - files: `install.sh:1019` (`docker info` liveness), `install.sh:1233-1247` (`df -k "$HOME"` ≥10 GB host check); `scripts/setup.sh:64` (only `command -v docker`); memory note "Docker VM disk" blocker
  - evidence: observed + inferred. `docker info` returns 0 even when the Docker Desktop VM disk is exhausted (inferred from Docker semantics); the disk preflight measures the host `$HOME` filesystem, not the VM's allocated disk (on macOS these differ). Neither equals "VM has room to pull/build ~14 locally-built images." `setup.sh` has no daemon liveness check at all.
  - why it matters: the documented blocker surfaces late — mid-`docker compose pull`/`build` — instead of at preflight, after the installer has already created `~/.dopemux`, venv, and shell edits.
  - falsifying check: fill the Docker VM disk, run `install.sh --quick` — disproven if preflight aborts before the compose pull.

- **[INST-07] MED — Legacy installers float all `>=` deps (no lockfile); only the documented `uv sync --frozen` path is reproducible; two deps fully unpinned**
  - files: `pyproject.toml:28-62` (runtime deps almost all `>=`), `:97` (`fastmcp`, no bound), `:114` (`rank_bm25`, no bound); `scripts/setup.sh:132` & `scripts/install.py:79` (`pip install -e .`), `install.sh:1307` (`venv/bin/pip install -e .`), root `Dockerfile:27` (`pip install --no-cache-dir .`), `services/dope-context/Dockerfile:18` (`uv pip install --system --no-cache .[services]`); `uv.lock` present
  - evidence: observed. `uv.lock` exists, so README's `uv sync --frozen` is reproducible. But every `pip install`-based installer and **all Docker image builds** ignore the lock and resolve `>=` ranges fresh, including two unbounded packages (`fastmcp`, `rank_bm25`). Image rebuilds are therefore non-deterministic over time.
  - why it matters: bounds reproducibility/auditability — a future `fastmcp` major could silently change runtime behavior in containers that the lockfile would have pinned. Not a hard break today.
  - falsifying check: `uv pip compile` diff of `.[services]` today vs `uv.lock` resolution — disproven if every transitive version already matches the lock.

- **[INST-08] MED — `services/dope-context/Dockerfile` healthcheck `|| exit 0` can never report unhealthy (failure-looks-healthy)**
  - files: `services/dope-context/Dockerfile:35-36` (`HEALTHCHECK ... CMD curl -f http://localhost:3010/health || exit 0`); contrast root `Dockerfile:68-69` (`|| exit 1`, correct)
  - evidence: observed. `|| exit 0` forces healthy regardless of `curl` result.
  - why it matters: `install.sh wait_for_containers` / README smoke checks (`README.md:127` curls `:3010/health`) can't rely on Docker health; a dead dope-context reports "healthy," masking a failed install. Service-level, but it directly defeats the install's verification step.
  - falsifying check: break the dope-context entrypoint, `docker inspect --format '{{.State.Health.Status}}'` — disproven if it ever shows `unhealthy`.

- **[INST-09] LOW — `Dockerfile.frontend` hard-depends on private `dhi.io` registry with no preflight; orphaned (zero canonical blast radius)**
  - files: `Dockerfile.frontend:3,15,31` (`FROM dhi.io/node:18-alpine`), `:11` (`npm ci --only=production && npm install`)
  - evidence: observed. `dhi.io` = Docker Hardened Images (entitled/authenticated registry); an unauthenticated `docker build` fails with a pull-auth error and no preflight. `rg "Dockerfile.frontend"` across all `*.yml/*.yaml` → **0 matches**: no compose service builds it, so the canonical stack never touches it. `:11` `npm ci --only=production` then `npm install` is contradictory/non-deterministic.
  - why it matters: latent trap if someone wires the frontend into compose later; today it cannot break the documented install. LOW because unreferenced.
  - falsifying check: `rg -l "Dockerfile.frontend" --glob '*.y*ml'` returning a compose file — disproven if any service references it.

- **[INST-10] LOW — `scripts/mcp-proxy-setup.sh` is stale (targets retired containers, port 8080 collision, unpinned tool install)**
  - files: `scripts/mcp-proxy-setup.sh:53` (`mcp-mas-sequential-thinking`, `mcp-zen`, `mcp-claude-context` — none in `compose.yml`), `:8` (`PROXY_PORT=8080`), `:44` (`uv tool install mcp-proxy`, unpinned); compose ships `mcp-pal`/`mcp-conport`/`mcp-dope-context` (`compose.yml:273,236,322`)
  - evidence: observed. Container names predate the `zen→pal` / `claude-context→dope-context` rename. `PROXY_PORT=8080` collides with Leantime's host `8080` (`compose.yml`/`README.md:118`). Otherwise well-formed (`set -euo pipefail :5`, idempotent `claude mcp remove … || true :203-209`, PID lifecycle). Only archived docs reference it.
  - why it matters: a `setup`/`start` run would mostly skip (containers absent) but could try to bind the Leantime port. Stale, low blast radius.
  - falsifying check: `./scripts/mcp-proxy-setup.sh check` against the canonical stack — disproven if any `mcp-mas-sequential-thinking`/`mcp-zen` container is reported running.

- **[INST-11] OBS — `install.sh` itself is well-engineered; defects are isolated; uninstall always passes `-v` (data loss) and uses a fixed-line `sed`**
  - files: `install.sh:21-23` (`set -euo pipefail`), `:25-40` (ERR trap + offered cleanup), `:706-738` (env file: `mktemp`→dedup-merge→atomic `mv`→`chmod 600`), `:1289-1290` (idempotent `mkdir -p`), `:654-659` (idempotent `network ls | grep` guard), `:1019` (`docker info` preflight), `Dockerfile:63-65` non-root user; `:1680` (`down -v` always), `:1691` (`sed '/# Dopemux/,+3d'`)
  - evidence: observed. The canonical installer's hygiene is genuinely strong (atomic secret write with 600 perms; rollback trap; idempotent dirs/networks). Two minor uninstall issues: `down -v` (`:1680`) destroys named volumes incl. Leantime MySQL data even though a `$DOPEMUX_HOME` backup was taken (DB not in that dir); `sed … ,+3d` (`:1691`) assumes the shell block is exactly 4 lines — fragile if `configure_shell_integration` wrote a different shape.
  - why it matters: positive evidence — the *design* is sound; the break (INST-01) is a single early-return + a network-name mismatch, not systemic. The uninstall notes are data-safety nits.
  - falsifying check: re-run `./install.sh --quick` twice (after fixing INST-01) — disproven if the 2nd run corrupts state rather than no-op'ing on existing dirs/network/env.

---

## Ordered side-effects per script (all NOT_RUN — human-verify commands inline)

**`install.sh --quick` / `--full`** (`main` `:1788` → `:1565-1589` quick / `:1622-1629` full):
1. `check_docker` `docker info` (`:1019`); 2. (full) secret resolution → write `.env` via mktemp+atomic mv+`chmod 600` (`:706-738`); 3. `preflight_checks` df `$HOME`, port `lsof`, write-perm (`:1233-1279`); 4. `create_directory_structure` `mkdir -p ~/.dopemux/{...}` (`:1289-1290`); 5. `install_dopemux_core` `python3 -m venv ~/.dopemux/venv` + `pip install -e .` + `cp -r config/*` (`:1304-1316`); 6. `ensure_docker_networks` (full only, wrong names) (`:1340`); 7. **`docker compose -f compose.yml up -d` → FAILS, missing `dopemux-network`** (`:1359`); 8. (full) `installers/leantime/install.py -u` (`:1366`); 9. `configure_shell_integration` appends to `~/.zshrc|.bashrc` (`:1373+`). Verify: `INSTALLER_TEST_MODE=0 ./install.sh --quick` in a throwaway `HOME` with `docker network rm dopemux-network`.

**`scripts/setup.sh`** (`set -e`, `:13`):
1. `mkdir -p ~/.dopemux/{profiles,databases,cache}` (`:75`); 2. `cp config/profiles/*.yaml` (`:88-100`); 3. `cp .env.example .env` if absent (`:113`); 4. `pip install -e . >/dev/null 2>&1` (`:132`, output swallowed); 5. `git submodule update --init --recursive` (`:155`); 6. `docker network create dopemux-unified-network` (**wrong name**, `:170`); 7. `docker compose -f compose.yml up -d 2>&1 | tail -5` (**fails but masked**, `:178`); 8. `sleep 15` (`:187`); 9. `dopemux health` (`:204`); 10. prompts to run missing `scripts/setup/install-adhd-integration.sh` (`:221`, file absent — guarded). Verify: `bash scripts/setup.sh --skip-docker` (avoids compose) then inspect `.env`/venv.

**`scripts/install.py`**: 1. version/pip/venv checks (`:21-45`); 2. `python -m venv ~/.dopemux/venv` (`:59`); 3. **`pip install -e scripts/` → FAILS** (`:78-80`, no build metadata); never reaches launcher creation. Verify: `python scripts/install.py`.

**`scripts/install-docker-mcp-servers.sh`** (`set -e`, `:6`): 1. `docker info` (`:110`); 2. require ≥1 provider key (`:129`); 3. `mkdir docker/mcp-servers/...` (`:48,:120`); 4. **`git clone <FradSer repo>` at HEAD** (`:57`); 5. write `.env` with keys, no chmod (`:63-84`); 6. `sed -i.bak` Dockerfile (`:89`); 7. generate compose + start/stop/logs scripts (`:179-294`); 8. **`./start-all-mcp-servers.sh` → `docker-compose up -d --build`** runs cloned code (`:303,:240`). Verify: `bash scripts/install-docker-mcp-servers.sh` in a sandbox, then `stat` the generated `.env` perms.

**`scripts/mcp-proxy-setup.sh setup`** (`set -euo pipefail`, `:5`): `uv tool install mcp-proxy` (`:44`) → `check_containers` (stale names, `:53`) → write `mcp-proxy-config.json` (`:112`) → `pkill mcp-proxy; nohup mcp-proxy --port 8080` (`:137,:152`, port clash) → `claude mcp remove…/add…` (`:203-265`). Verify: `./scripts/mcp-proxy-setup.sh check`.

## Validation
- **PASS**: none (read-only; nothing executed).
- **FAIL**: none executed.
- **NOT_RUN**: all runtime behavior above (per audit contract). Highest-value human checks: INST-01 (`INSTALLER_TEST_MODE=0 ./install.sh --quick` after `docker network rm dopemux-network`), INST-03 (`python scripts/install.py`), INST-04 (`bash scripts/setup.sh` with daemon stopped → expect success banner = confirmed).

## Remaining uncertainty
- Whether `docker info` masks VM-disk exhaustion is inferred from Docker semantics, not reproduced here (INST-06).
- pymupdf/`fastmcp` build behavior on the target arch is unverified — `services/dope-context/Dockerfile:13` ships `build-essential`, so a source build would *succeed* (slow) rather than break; classed under reproducibility (INST-07), not a hard blocker.
- I did not exhaustively trace `installers/leantime/install.py` (`install.sh:1366`); only its existence and invocation are confirmed.

## Files reviewed
`README.md`, `QUICK_START.md`, `INSTALL.md`, `docs/01-tutorials/installation.md`, `docs/01-tutorials/quickstart.md`, `install.sh`, `scripts/setup.sh`, `scripts/install.py`, `scripts/install-docker-mcp-servers.sh`, `scripts/mcp-proxy-setup.sh`, `pyproject.toml`, `uv.lock` (existence), `compose.yml`, `Dockerfile`, `Dockerfile.frontend`, `services/dope-context/Dockerfile`, `test_installer_basic.sh`; cross-referenced `scripts/start.sh`/`smoke_up.sh`/`consolidate_docker_networks.sh` (network-creation), `claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md` (prior overlap, re-verified).

==========================================================================================
## USAGE  (technical-writer, a4d4462981d185e75, 5941 chars)
==========================================================================================

I'll audit the documented RTE usage against the runtime. Let me start by gathering the documented commands and golden path from all the doc sources, then verify each against the code.

I have the root README and QUICK_START. Now let me read the RTE service README (the primary RTE doc), the extraction how-to docs, and the operator/extraction-related docs.

The RTE service README is the central doc, and there's a rich `docs/02-how-to/extraction/` directory. This is where the golden-path docs live. Let me read all the key extraction how-to docs and the universal-extractor/extraction-wizard docs that cover documented commands.

I now have a comprehensive map of documented commands. The key prompt warns specifically about `LegacyReplacementCommand` shadowing in `cli.py` that disables documented commands like `dopemux extractor init/validate/status`, and about doc-vs-code drift, canonical-naming inversions, and surprise-cost paths. 

Critically, README:37 documents `dopemux extractor validate --output-dir ...` as a current command, while the user-guide says `dopemux extractor` is a "legacy/refusal surface." That's a direct internal contradiction worth verifying. Let me now inspect the runtime CLI to verify each documented command's reachability. Let me look at the CLI registration structure first.

Now let me examine the `LegacyReplacementCommand` class definition and each of the locations where it's used, plus the `rte`, `upgrades`, `extractor`, and `extract` command group registrations. This is the critical part for verifying reachability.

This is the critical structure. The `rte` group reuses the SAME command objects as `extractor` and `upgrades` (lines 5596-5626). Now I need to verify:

1. The `extractor` group registration (line 3170-3182) using `LegacyReplacementCommand` — does it disable `dopemux extractor validate` documented in README:37?
2. Whether `extractor.commands["init"]` and `extractor.commands["validate"]` (lines 5623-5625) actually exist
3. The `truth` command (line 5550) and `extract` group
4. The legacy command blocks at 4196, 4407, 4822, 4914

Let me read these key sections.

Critical finding confirmed. At cli.py:3170-3184, `dopemux extractor` is registered as a `LegacyReplacementCommand` that **disables ALL subcommands** including `validate`. The `replacement_by_arg["validate"]` maps to `dopemux rte promptset validate`. But README:37 documents `dopemux extractor validate --output-dir ...` as a current/working command.

But wait — there are TWO `extractor` registrations. Line 3170 registers the `LegacyReplacementCommand` named "extractor" on `cli`. But line 3165 imports the real `extractor` group, and lines 5596+ reuse its subcommands (`extractor_list`, etc.) onto `rte`. The `cli.add_command(...)` at 3170 — does it OVERRIDE the import at 3165? Note the real `extractor` group is NEVER added to `cli` directly; only the `LegacyReplacementCommand` shell is added under name "extractor". So `dopemux extractor <anything>` hits the legacy refusal. This confirms the README inversion.

Now I need to verify: (1) Does `extractor.commands` contain "init" and "validate" (line 5622/5624 guards)? (2) Does `dopemux rte promptset validate` actually exist and work? (3) The `extract` group and the legacy blocks at 4196/4407/4822/4914. Let me check the extractor_commands module and those legacy blocks.

Now I have what I need on `extractor`. The real `extractor` group (extractor_commands.py) DOES define `init` (line 172) and `validate` (line 406, signature `validate(output_dir: str)`). So the guards at cli.py:5622/5624 succeed: `dopemux rte promptset sync` and `dopemux rte promptset validate` are wired to the real init/validate command objects. Good — the canonical replacement the README *should* point to exists.

But the README:37 says `dopemux extractor validate --output-dir ...` — that path is shadowed by the LegacyReplacementCommand. Let me confirm the `validate` command's actual option name and the `extract` group / its truth-run alias, plus the legacy blocks at 4407/4822/4914 (the latter is inside `extract`). Let me also check the `--output-dir` flag exists on the real validate command.

Interesting — `repscan` is disabled and points to `dopemux rte scan` (cli.py:4824), but I noticed `rte` does NOT have a `scan` subcommand registered (lines 5596-5603 only register list/run/doctor/status/preflight/validate-live/trace/wizard). Let me verify whether `dopemux rte scan` actually exists. Also the README:36 documents `dopemux rte preflight --auth-doctor` and README:35 `dopemux rte validate-live`. And README common workflows reference `dopemux rte ...`.

Let me check: (1) does `rte scan` exist (referenced by repscan refusal and run-prescan.md indirectly)? (2) The `extract truth-run` alias (line 4914 block + the extract group). (3) The `upgrades validate-live` import-origin gate vs README. Let me look at the extract group and the truth-run alias around 4900-4952, and grep for "scan" on rte.

`rte scan` DOES exist — it's defined at cli.py:4958 via `@rte.command("scan", ...)`. Good, so the repscan refusal pointer is valid. Let me read the `rte scan` command (4958-5027) to understand what it does and whether it's a surprise-cost path (the prompt specifically asks: does a "first/safe" command avoid LLM/network cost?). Then I need to verify the `extract truth-run` alias and the `upgrades`/`rte run` `--dry-run` default behavior (cost safety of the documented "first" command).

The user-guide §4 documents `dopemux rte run --pipeline-version v5 --phase ALL --dry-run` as the scanning/safe command. The README:34 documents the same. I need to verify `--dry-run` is the default and is truly LLM-free, AND check prescan: run-prescan.md says `dopemux rte run --phase A --dry-run` "Runs local prescan automatically" — does dry-run prescan make LLM calls? The RTE README:144 says prescan has its own cost. Let me read the `rte run` / extractor_run command and the scan command.

==========================================================================================
## MCP(partial/hung)  (security-engineer, a04479a129f428346, 4681 chars)
==========================================================================================

I'll conduct this security and correctness audit of the MCP layer. Let me start by orienting myself to the codebase structure for both parts.

This is a substantial read-only audit. Let me read the core authority files first (Part 1), since the authority model is the central question. I'll read the smaller, central files in parallel.

I have the core authority files for Part 1. The `gate.py` is central to the fail-open/closed question, and I've spotted some interesting patterns already (the ConPort glob "both spellings" logic on lines 66-70 looks like a no-op bug). Let me read the role filtering files now — roles.py is the heart of "how tools are filtered per role."

Now I have the role/discovery picture. Critically, `roles.py` defines roles and escalations but I haven't yet seen the **enforcement** point — where tool calls are actually filtered/blocked per role. That's the broker. Let me read the broker (the enforcement engine), session_manager, and token_manager, and check the gate's caller in cli.py. Let me also look at how the broker enforces authority.

I now have the broker's enforcement model. Key observations forming:
1. `_verify_tool_access` (broker.py:833-835) checks `tool_name in session.mounted_tools` — but `tool_name` is actually the **server_name** passed to `server_manager.call_tool(server_name=request.tool_name, ...)` (broker.py:490-491). This is a server-level gate, not a tool-level gate. The method/args inside aren't filtered.
2. The `escalation_config.get(...)` calls (broker.py:562, 570, 583, 589) are on an `EscalationRule` **dataclass**, not a dict — `EscalationRule` has no `.get()` method. This would `AttributeError` at runtime. Let me verify this against roles.py — confirmed, `EscalationRule` is a dataclass (roles.py:42-55), so `escalation_config.get("approval_required")` (broker.py:570) would crash. This means `request_escalation` is broken/dead.

Let me read the token_manager and session_manager, then the gate caller in cli.py. Let me also check the policy config to understand what roles/tools actually exist.

Critical finding emerging: there is **no `policy.yaml`** at the path the broker expects (`/config/mcp/policy.yaml`, broker.py:72). The MetaMCPBroker (`call_tool`, `_verify_tool_access`, `switch_role`) appears to never be instantiated in real runtime — the only `call_tool` references are in standalone services (mcp-client, mcp-integration-bridge) which have their own implementations, not the broker. Let me confirm whether the broker is dead/unwired and check the gate caller in cli.py to understand the real enforcement path.

Let me call the advisor now, before I commit to the interpretation that the orchestration broker is effectively dead code. This is a load-bearing claim for the whole Part 1 authority model.

This confirms a major architectural finding: **MetaMCPBroker (and the entire RoleManager/TokenBudgetManager role-enforcement stack) is only instantiated in `docs/archive/integration-transient/` — archived/dead code.** The live `mcp start` (cli.py:3755) runs only the `DiscoveryGate`, never the broker. The `SessionManager` instantiations elsewhere are *different* SessionManager classes (serena, gpt-researcher, etc.), not `mcp/session_manager.py`.

This reframes Part 1: the "authority model" via roles is **not enforced at runtime** — the only thing wired in is the Phase 0 DiscoveryGate. That's the central finding. Let me verify the gate's fail-open/closed behavior more rigorously (the `is_mandatory` logic and exception handling) and read session_manager.py to be thorough, plus check server_manager for the actual tool-call path and confirm session_manager.py isn't imported elsewhere.

This confirms the architecture. The `registry.yaml` has **duplicate YAML keys** (e.g., `dopemux-desktop-commander`, `dopemux-gpt-researcher`, `dope-context`, `dopemux-pal` appear twice) — in YAML the last duplicate wins, so `default_enabled`/`required_for_auto` silently flip to `false`. That's a config-drift finding. Also note `registry.yaml` (used by `registry.py`) and `default_catalog.yaml` use **different server names** (`dopemux-conport` vs `conport`), and the gate's resolver reads from neither — it reads `.dopemux/mcp.instances.toml`. Three separate naming schemes.

Now let me verify the gate's fail-open/closed behavior precisely. The key question: when `required_tool_globs` is empty (the common case, since the resolver's TOML provides server URLs but the globs come from `config.get("required_tool_globs", [])`), does a reachable-but-wrong server pass? Let me read the server_manager (the actual tool-call executor in the broker path) and session_manager, then trace the gate's mandatory logic.

==========================================================================================
## REVIEW-correctness  (workflow-subagent, a23d3e60d366e8fbb, 20284 chars)
==========================================================================================

I'll re-read each cited piece of code independently before ruling. Let me start by orienting in the repo and reading the key files.

All files exist. The repo is at HEAD `755bf3846`, working tree shows the salvage audit doc as untracked. Let me now read the core files I need to verify findings against — `install.sh` (the largest), the docs, and the supporting scripts. I'll read them in parallel.

I've confirmed several key facts. Let me note discrepancies with the lane findings already:

1. **INST-01**: The finding cites `install.sh:643-661` for `ensure_docker_networks`. I read it at exactly those lines. Confirmed: returns early for non-`full` (`:645-647`), creates `mcp-network`/`dopemux-unified-network`/`leantime-net` for full (`:652`) — NOT `dopemux-network`. `compose.yml:24-27` confirms external `dopemux-network`. **But the finding's line cites for `install.sh` differ slightly from what I'm seeing** — let me verify the specific caller lines (1340, 1359), the env-file `chmod 600` claim (`:706-738` — confirmed at `:735-736`), and the skip-guards.

2. **INST-02**: `test_installer_basic.sh:49,58` force `INSTALLER_TEST_MODE=1` — **confirmed exactly** at lines 49 and 58. Skip guards at `:648, :747` confirmed. Need to verify the rest.

Let me verify the remaining `install.sh` line numbers and read the other scripts.

This confirms the core of INST-01 and INST-02 with high precision:

**INST-01 verification:**
- `install.sh` never creates `dopemux-network` — grep confirms ONLY `mcp-network`/`dopemux-unified-network`/`leantime-net` are created in `ensure_docker_networks`. The `dopemux-network` string never appears in `install.sh` (no match for it in the network grep, only the 3 wrong names).
- The only caller is `:1340` (`ensure_docker_networks "$stack"`) — confirmed.
- `docker compose ... up -d` at `:1359` with `|| fatal "Failed to start Docker services"` — confirmed (note: the finding says `:1359`, matches exactly).
- `compose.yml:25-27 external: true` — confirmed; Docker won't auto-create.
- Network creation lives in `scripts/start.sh:75`, `scripts/smoke_up.sh:85`, `consolidate_docker_networks.sh:33` — confirmed via grep, none invoked by `install.sh`.

**INST-02 verification:** All 8 skip guards confirmed at exactly the cited lines: `648, 747, 1008, 1226, 1298, 1342, 1376, 1443`. The finding cited these exact lines. `test_installer_basic.sh:49,58` force `INSTALLER_TEST_MODE=1` — confirmed.

One nuance for INST-01: the finding's "why it matters" claims core AND research stacks fail. `ensure_docker_networks` returns early (creates nothing) for core/research, so for those stacks NO network is created at all, and compose needs `dopemux-network` → fails. For `full`, wrong names created → also fails. The finding's logic holds. Let me now read the README/QUICK_START/docs for the canonical path claim, and the other scripts.

The authority-resolution claim is confirmed. The two documented paths exist and disagree:

- **README.md:80-92** + **QUICK_START.md:7-20** + **docs/01-tutorials/quickstart.md:49-54**: `uv sync --frozen --extra dev` → manual `docker network inspect dopemux-network || docker network create dopemux-network` → `docker compose -f compose.yml up -d --build`. Confirmed at exact lines. This path manually creates the network — sound.
- **INSTALL.md:9-17**: `./install.sh` "one-command" — confirmed at `:9-17` (the finding says `:9-17`, I see the install block at `:9-16`, close enough — the recommendation header is `:7`).
- **docs/01-tutorials/installation.md:14**: `setup.sh` canonical quick start — confirmed at `:14` (`git clone` → `setup.sh` → `dopemux init`).

Now let me verify the remaining install.sh details (chmod 600, ERR trap, uninstall) and read the other scripts: `setup.sh`, `install.py`, `install-docker-mcp-servers.sh`, `mcp-proxy-setup.sh`, and the Dockerfiles.

Excellent verification. Multiple findings confirmed precisely:

**INST-01** fully confirmed:
- `ensure_docker_networks "$stack"` at `:1340` — confirmed exact line.
- `docker compose ... up -d || fatal` at `:1359` — confirmed exact line.
- `compose.yml` existence check at `:1335` and the network creation at `:1340` runs BEFORE the up at `:1359` but creates wrong/no networks.

**INST-06** confirmed:
- `df -k "$HOME"` disk check at `:1235` (finding says `:1233-1247`, the df is `:1235`, threshold `:1238` — matches range). The check measures `$HOME` host fs.
- `docker info` liveness — need to verify `:1019`.

**INST-11** confirmed:
- `set -euo pipefail` at `:20-22` — confirmed.
- ERR trap with offered cleanup at `:25-40` — confirmed exactly.
- env file mktemp→atomic mv→chmod 600 at `:706-738` (confirmed `:735-736` earlier).
- idempotent `mkdir -p` at `:1289-1290` — confirmed.
- idempotent network guard `network ls | grep` at `:654` — confirmed.
- uninstall `down -v` at `:1680` — confirmed exact line (data loss: `-v` destroys volumes; backup at `:1673` copies `$DOPEMUX_HOME` only, NOT the MySQL volume).
- uninstall `sed '/# Dopemux/,+3d'` at `:1691` — confirmed exact line.

Now let me verify `docker info` at `:1019` and read the remaining scripts and Dockerfiles in parallel.

Now I can rule on several findings precisely:

**INST-03** — `scripts/install.py`:
- `current_dir = Path(__file__).parent` at `:77` — confirmed exact.
- `pip install -e str(current_dir)` at `:78-80` — confirmed exact.
- Comment "from current directory" at `:76` — confirmed (says "from current directory" but resolves to `scripts/`).
- No build metadata in `scripts/` — confirmed earlier (`ls scripts/pyproject.toml scripts/setup.py scripts/setup.cfg` all missing). Let me double-check.
- Secondary `logger.info("text", var)` at `:24` (`"❌ Python 3.8+ required. Current version:", sys.version`) — confirmed; logging treats the 2nd arg as a logging-format arg, not str concatenation, so it won't interpolate. Also `:170` `logger.error("Error:", result.stderr)`.

**INST-04** — `scripts/setup.sh`:
- `set -e` only, no `pipefail` at `:13` — confirmed exact (`set -e  # Exit on error`, and there is no `set -o pipefail` anywhere — let me grep to be sure).
- `docker network create dopemux-unified-network` at `:170` — confirmed exact.
- `docker compose ... up -d 2>&1 | tail -5` inside `if` at `:178`, with `else ... exit 1` at `:181-183` — confirmed exact. With only `set -e`, the `if` tests `tail`'s exit (0), so `else exit 1` is dead code. Success banner at `:240-241` — confirmed.

The finding's claim about `dopemux-unified-network` being the *legacy* network is corroborated by `consolidate_docker_networks.sh:3` ("Consolidates mcp-network and dopemux-unified-network into single dopemux-network").

Let me verify `set -o pipefail` absence in setup.sh, check `scripts/` for build metadata, and verify INSTALL.md line range for the install block.

More confirmations:

**INST-04** fully confirmed: `setup.sh` has `set -e` only (`:13`), NO `pipefail`/`set -u` (grep returned no match for those in setup.sh). `dopemux-unified-network` at `:170`, masked compose-up at `:178-183`, success banner. Dead `else exit 1` confirmed.

**INST-05** — `scripts/install-docker-mcp-servers.sh`:
- `git clone "$repo_url" .` at `:57` (no SHA/tag) — confirmed exact. The repo URL `github.com/FradSer/mcp-server-mas-sequential-thinking.git` passed at `:172` — confirmed.
- `git pull origin main` on update at `:54` — confirmed exact.
- `.env` written with `DEEPSEEK/OPENAI/GITHUB/EXA` keys at `:63-84`, **no `chmod 600`** — confirmed exact (the heredoc writes `.env`, no chmod follows; `install_docker_mcp_server` ends at `:95` with no chmod).
- `./start-all-mcp-servers.sh` → `docker-compose up -d --build` at `:303` → `:240` — confirmed exact.
- `mas-sequential-thinking` absent from canonical `compose.yml` — need to confirm via grep.
- `docker-compose` v1 dependency at `:105, :240` — confirmed.

Finding note about `scripts/deploy/setup/install-mcp-servers.sh:128` referencing this — need to verify.

**INST-03** fully confirmed: no build metadata in `scripts/` (all three missing). `pip install -e scripts/` will fail.

**INSTALL.md** confirmed: `./install.sh` at `:15` (the finding cited `:9-17`; the block is `:9-16` with the "Recommended" header at `:7-8`; the cite range is essentially accurate).

Let me now verify the `mas-sequential` absence in compose.yml, the deploy script reference, and read the remaining files: `mcp-proxy-setup.sh`, the Dockerfiles, and `pyproject.toml`.

All remaining findings now confirmed:

**INST-05**: `mas-sequential` is NOT in `compose.yml` (only `mcp-conport`, `mcp-pal`, `mcp-dope-context` appear) — confirmed stale. The deploy script reference at `scripts/deploy/setup/install-mcp-servers.sh:128` (`DOCKER_INSTALLER="$(dirname "$0")/install-docker-mcp-servers.sh"`) — confirmed exact line.

**INST-08**: `services/dope-context/Dockerfile:36-37` `HEALTHCHECK ... CMD curl -f http://localhost:3010/health || exit 0` — confirmed exact (finding cited `:35-36`, actual is `:36-37`; off by one but the content is exact and unambiguous). Root `Dockerfile:68-69` `|| exit 1` (correct) — confirmed exact. The `|| exit 0` forces healthy regardless.

**INST-07**: `services/dope-context/Dockerfile:19` `uv pip install --system --no-cache .[services]` — confirmed exact. `build-essential` at `:15` present (supports the "would build, slowly" uncertainty note). Root `Dockerfile:27` `pip install --no-cache-dir .` — confirmed exact. Need to verify pyproject `>=` deps and unbounded `fastmcp`/`rank_bm25`.

**INST-09**: `Dockerfile.frontend:3,15,31` `FROM dhi.io/node:18-alpine` — confirmed exact (all three stages). `:11` `npm ci --only=production && npm install` — confirmed exact (contradictory). Zero compose references — confirmed (grep for `Dockerfile.frontend` in *.yml/*.yaml returned nothing).

Let me verify `pyproject.toml` deps for INST-07 and read `mcp-proxy-setup.sh` for INST-10. I'll also confirm INST-06's `setup.sh` daemon-liveness absence claim.

Both final findings confirmed:

**INST-07**: pyproject.toml deps are almost all `>=` (`:29-62` runtime, `:88-120` services). `fastmcp` at `:97` has NO version bound — confirmed exact. `rank_bm25` at `:114` has NO version bound — confirmed exact. The finding cited `:97` and `:114` precisely. (Note: `:53` `pymilvus>=2.3.0` is present — the finding's `pymupdf` reference is at `:111`, also `>=`.)

**INST-10**: `scripts/mcp-proxy-setup.sh:8` `PROXY_PORT=8080` — confirmed exact. `:53` container list includes `mcp-mas-sequential-thinking`, `mcp-claude-context`, `mcp-zen` (all retired, none in `compose.yml`) — confirmed exact. `:44` `uv tool install mcp-proxy` unpinned — confirmed exact. `:5` `set -euo pipefail` — confirmed exact. Leantime host port 8080 collision — `compose.yml` Leantime port is documented at `README.md:118` as `8080`; let me note this is consistent with the README table I already read (Leantime `8080`).

I have now independently reproduced the cited evidence for all 11 findings. Let me do one final precision check on a few line-number citations that were slightly off, and confirm the `chmod 600` absence in the MCP-servers `.env` write and the INST-06 `setup.sh` no-daemon-check claim, plus the Leantime 8080 port in compose.yml.

Final confirmations:

- **INST-05** `chmod`: only `chmod +x` on the three management scripts (`:259, :276, :294`); NO `chmod 600` on the generated `.env` — confirmed. The `.env` (written `:63-84`) is left at default umask.
- **INST-06** `setup.sh`: zero `docker info`/`daemon` references — confirmed. `setup.sh` has no daemon-liveness check at all (only `command -v docker` at `:64`).
- **INST-10** Leantime port: `compose.yml:165` `"${LEANTIME_PORT:-8080}:80"` — confirmed; default host port 8080, which `mcp-proxy-setup.sh:8 PROXY_PORT=8080` would collide with.
- **Staleness dates**: `install.sh` `4959a089f` 2026-05-02; `compose.yml` `1a1a82384` 2026-05-15 (13-day drift after installer last touched) — both confirmed exactly. `install-docker-mcp-servers.sh` last commit `764a929cb` 2026-04-12 — **finding claimed `586ca44a4` 2026-01-20 (~4 months stale)**. The SHA and date the finding cited do NOT match the actual last-touch commit. The file's *content* claims and its staleness relative to compose still hold (Apr 12 vs May 15 = ~1 month stale, and it provisions a server absent from compose), but the specific "`586ca44a4` 2026-01-20, ~4 months stale" provenance is wrong. This is a minor evidence error within an otherwise-correct finding — I'll note it in INST-05's verdict.

I have independently reproduced every load-bearing claim. The findings are correctness-focused and overwhelmingly accurate. Let me render the review.

---

# Adversarial Correctness Review — Install/Bootstrap Lane

Repo `/Users/hue/code/dopemux-mvp` @ HEAD `755bf3846`. Every citation below was independently re-read; nothing executed (read-only contract honored).

| Finding | Verdict | Justification (independently reproduced) |
|---|---|---|
| **INST-01** | **CONFIRMED** | `ensure_docker_networks` (`install.sh:643-661`) returns early for non-`full` (`:645-647`) and for `full` creates only `mcp-network`/`dopemux-unified-network`/`leantime-net` (`:652`). `rg dopemux-network install.sh` → no match. Sole caller `:1340`; `docker compose ... up -d \|\| fatal` at `:1359`; `compose.yml:25-27` `external: true name: dopemux-network`. Network creation lives only in `scripts/start.sh:75`/`smoke_up.sh:85`/`consolidate_docker_networks.sh:33`, none invoked by `install.sh`. Core/research stacks get *no* network created; full gets *wrong* names — both miss `dopemux-network`. Reproduces exactly. |
| **INST-02** | **CONFIRMED** | `test_installer_basic.sh:49,58` both hard-set `INSTALLER_TEST_MODE=1`. All 8 skip-guards present at the cited lines `648,747,1008,1226,1298,1342,1376,1443` (grep-verified). Test-mode early-returns from network/compose/preflight/core/shell/verify, so the side-effecting path (incl. INST-01) is never exercised in CI. Reproduces. |
| **INST-03** | **CONFIRMED** | `scripts/install.py:77` `current_dir = Path(__file__).parent` (→ `scripts/`), `:78-80` `pip install -e str(current_dir)`. `ls scripts/{pyproject.toml,setup.py,setup.cfg}` → all absent, so `pip install -e scripts/` cannot resolve build metadata; `install_package` raises, `main()` exits non-zero. Comment `:76` "from current directory" is misleading. Secondary `logger.info("…:", sys.version)` at `:24` (and `:170`) passes a value as a logging-format arg → never interpolates (cosmetic). Reproduces. |
| **INST-04** | **CONFIRMED** | `scripts/setup.sh:13` `set -e` only; `grep pipefail\|set -u` → no match. `:178` `if docker compose … up -d 2>&1 \| tail -5; then` evaluates `tail`'s exit (0), making the `else … exit 1` (`:181-183`) dead → success banner (`:240-241`) prints on compose failure. Independently, `:170` creates `dopemux-unified-network`, the *legacy* net per `consolidate_docker_networks.sh:3`, not the required `dopemux-network`. Documented as canonical by `docs/01-tutorials/installation.md:14`. Reproduces. |
| **INST-05** | **CONFIRMED** (severity HIGH upheld; one provenance datum wrong) | `scripts/install-docker-mcp-servers.sh:57` `git clone "$repo_url" .` unpinned; repo `FradSer/mcp-server-mas-sequential-thinking` at `:172`; update path `git pull origin main` `:54`. `.env` written `:63-84` with DEEPSEEK/OPENAI/GITHUB/EXA keys; `grep chmod` → only `chmod +x` on management scripts (`:259,:276,:294`), **no `chmod 600` on `.env`**. Auto-build+run via `:303`→`:240` `docker-compose up -d --build`. `mas-sequential` absent from `compose.yml` (only `mcp-conport`/`mcp-pal`/`mcp-dope-context`). Referenced by `scripts/deploy/setup/install-mcp-servers.sh:128`. **Correction:** finding cites last-touch `586ca44a4` 2026-01-20 (~4 months stale); actual is `764a929cb` 2026-04-12 (~1 month before compose). Code claims unaffected; the staleness provenance datum is wrong. |
| **INST-06** | **CONFIRMED** | `install.sh:1019` `docker info &>/dev/null` (binary liveness, returns 0 on VM-disk-full per Docker semantics — *inferred*, flagged as such in finding). `:1235` `df -k "$HOME"` measures host `$HOME`, not the Docker Desktop VM disk (distinct on macOS — inferred). `scripts/setup.sh` `grep "docker info\|daemon"` → no match, so it has no daemon-liveness check (only `command -v docker` `:64`). The hard claims reproduce; the "masks VM disk" mechanism is correctly labeled inferred. MED appropriate. |
| **INST-07** | **CONFIRMED** | `pyproject.toml` runtime deps `:29-62` and services `:88-120` are nearly all `>=`; `fastmcp` `:97` and `rank_bm25` `:114` are fully unbounded. `uv.lock` exists (1.1 MB) → README `uv sync --frozen` reproducible. `pip install -e .` installers + image builds (root `Dockerfile:27` `pip install … .`; `services/dope-context/Dockerfile:19` `uv pip install --system … .[services]`) ignore the lock → non-deterministic rebuilds. Reproduces. MED appropriate. |
| **INST-08** | **CONFIRMED** | `services/dope-context/Dockerfile:37` `HEALTHCHECK CMD curl -f http://localhost:3010/health \|\| exit 0` — `\|\| exit 0` forces healthy regardless of `curl`. Contrast root `Dockerfile:69` `\|\| exit 1` (correct). README smoke check curls `:3010/health` (`README.md:126`), so a dead service still reports healthy. (Finding cited `:35-36`; actual `:36-37` — off-by-one, content exact.) Reproduces. |
| **INST-09** | **CONFIRMED** | `Dockerfile.frontend:3,15,31` all `FROM dhi.io/node:18-alpine` (entitled registry, no preflight → unauthenticated build fails). `:11` `npm ci --only=production && npm install` is contradictory/non-deterministic. `rg Dockerfile.frontend --include=*.yml --include=*.yaml` → 0 matches: orphaned, zero canonical blast radius. LOW correct. Reproduces. |
| **INST-10** | **CONFIRMED** | `scripts/mcp-proxy-setup.sh:8` `PROXY_PORT=8080`; `:53` targets `mcp-mas-sequential-thinking`/`mcp-claude-context`/`mcp-zen` (retired; absent from `compose.yml`); `:44` `uv tool install mcp-proxy` unpinned; `:5` `set -euo pipefail`. `compose.yml:165` `"${LEANTIME_PORT:-8080}:80"` confirms the host-8080 collision. Stale, low blast radius. LOW correct. Reproduces. |
| **INST-11** | **CONFIRMED** | Positive-evidence claims reproduce: `install.sh:20-22` `set -euo pipefail`; `:25-40` ERR trap with offered cleanup; `:706-738` env write via `mktemp`→dedup-merge→`mv`→`chmod 600` (`:735-736`); `:1289-1290` idempotent `mkdir -p`; `:654` idempotent `network ls\|grep`; root `Dockerfile:63-65` non-root user. Uninstall nits: `:1680` `down -v` destroys named volumes (Leantime MySQL is a volume, not under the `$DOPEMUX_HOME` backup at `:1673`); `:1691` `sed '/# Dopemux/,+3d'` assumes a fixed 4-line block. Reproduces. |

## Summary
- **CONFIRMED: 11/11.** Every finding's load-bearing code evidence reproduces from source at the cited (or off-by-one-but-unambiguous) locations.
- **No REFUTED, no severity RECALIBRATE.** Severities are well-calibrated: the two paths that fail (`install.sh` INST-01, `setup.sh` INST-04) are HIGH not CRIT because the *documented README/QUICK_START path is sound* (manually creates the network) — authority resolution is correct and materially de-escalates blast radius. INST-03/05 HIGH is justified by structural breakage / supply-chain+secret exposure with low reference count.
- **One evidence error inside INST-05** (does not change the verdict or severity): the cited staleness commit `586ca44a4` / 2026-01-20 / "~4 months" is wrong — actual last-touch is `764a929cb` / 2026-04-12, ~1 month before `compose.yml` (`1a1a82384`, 2026-05-15). The drift claim survives (still pre-dates compose; still provisions a server absent from compose); only the SHA/date/magnitude are inaccurate. `install.sh` (`4959a089f`, 2026-05-02) vs `compose.yml` 13-day drift is correct.
- **Authority resolution independently verified.** README.md:80-92 / QUICK_START.md:7-20 / docs/01-tutorials/quickstart.md:49-54 all manually create `dopemux-network`; INSTALL.md:15 + docs/01-tutorials/installation.md:14 point at the broken `install.sh`/`setup.sh`. The "two contradictory canonical paths" framing is accurate.
- **Inferred-vs-observed tagging is honest.** INST-06's "`docker info` masks VM-disk exhaustion" is explicitly labeled inferred; INST-07's pymupdf/fastmcp build behavior is correctly scoped to reproducibility, not a hard blocker (`build-essential` present in both build Dockerfiles).

==========================================================================================
## REVIEW-correctness  (workflow-subagent, a16b1e8f2d5fbd6e8, 0 chars)
==========================================================================================

(no substantial output)


==========================================================================================
## REVIEW-correctness  (workflow-subagent, afd2fcc8e153b8d77, 0 chars)
==========================================================================================

(no substantial output)


==========================================================================================
## REVIEW-security  (workflow-subagent, a9a4472dd4a581271, 19587 chars)
==========================================================================================

I'm acting as the adversarial security reviewer for the "install" lane. Let me verify each finding against the actual source code before ruling. The audit contract is read-only, so I'll inspect code/config and tag claims observed-vs-inferred.

Let me start by orienting on the key files and verifying the load-bearing claims.

The three load-bearing claims for INST-01 are confirmed at the source level:
- `ensure_docker_networks` returns early for non-`full` stacks (`install.sh:645-647`), and for `full` creates `mcp-network`/`dopemux-unified-network`/`leantime-net` — not `dopemux-network` (`install.sh:652`).
- `grep "dopemux-network" install.sh` → no match (exit 1, but my echo masked it; the grep block printed nothing).
- `compose.yml:25-27` declares `dopemux-network` as `external: true`.

But I notice something the finding got slightly wrong on the caller line, and there's a `--quick` vs `--full` nuance worth checking. Let me verify the network-name claims more carefully, and confirm whether `--quick`/core even calls compose with that network, plus check the other findings. Let me batch the independent verifications.

INST-01 is now strongly confirmed and actually slightly understated in nuance: ALL stacks (`DOCKER_COMPOSE_CORE`, `_RESEARCH`, `_FULL`) point at the same `compose.yml` (`install.sh:50-52`), and `compose.yml` has 25 `dopemux-network` references with every service on it. So even `--quick`/core hits the broken network. The finding said this; confirmed. The caller line "1340" maps to `ensure_docker_networks "$stack"` (actually 1340 per the sed output region ~1339-1340), and `up -d` is at 1359. Minor line-number drift but substantively correct.

The README path does manually create `dopemux-network` (`README.md:88-90`), confirming the two-path divergence and that the README path is sound.

Let me verify the remaining findings: the test-mode dead-coding (INST-02), install.py (INST-03), setup.sh pipefail+network (INST-04), the supply-chain script (INST-05), healthcheck (INST-08), and the uninstall `-v` claim (INST-11). Let me batch these.

Several findings confirmed precisely:

- **INST-02**: `test_installer_basic.sh:49,58` both hard-force `INSTALLER_TEST_MODE=1`. `install.sh` has 8 skip-guards (`648,747,1008,1226,1298,1342,1376,1443`) — exactly matching the finding's list. Confirmed.
- **INST-03**: `scripts/install.py:77` `current_dir = Path(__file__).parent`, `:78-80` `pip install -e str(current_dir)`, and `scripts/{pyproject.toml,setup.py,setup.cfg}` all absent. Confirmed — `pip install -e scripts/` will fail.
- **INST-04**: `scripts/setup.sh:13` is `set -e` only (no `pipefail`/`-u`). The compose call at `:178` is `if docker compose ... up -d 2>&1 | tail -5; then` — the pipe's exit status is `tail`'s (always 0), so the `else ... exit 1` at `:181-183` IS dead code. And `:170` creates `dopemux-unified-network`, not `dopemux-network`. All three sub-claims confirmed. The success banner at `:240` is reachable. Confirmed.

Now let me verify the supply-chain finding (INST-05), the healthcheck (INST-08), the uninstall `-v`/sed claims (INST-11), and the git staleness dates, plus Dockerfile.frontend (INST-09).

All findings now verified at source. Key confirmations and one calibration note:

- **INST-05**: `git clone "$repo_url" .` at HEAD (no SHA/tag, `:57`), `git pull origin main` on update (`:54`); `.env` written via heredoc with `DEEPSEEK/OPENAI/GITHUB/EXA` keys (`:63-84`); chmod only `+x` on the three wrapper scripts (`:259,276,294`) — **no `chmod 600` on `.env`**; `./start-all-mcp-servers.sh` auto-runs (`:303`) → `docker-compose up -d --build` (`:240`). `compose.yml:273` ships `mcp-pal`, and `mas-sequential` has 0 matches → stale. Referenced only by `scripts/deploy/setup/install-mcp-servers.sh:128`. All confirmed. This is a genuine supply-chain + secret-exposure path.

- **INST-08**: `services/dope-context/Dockerfile:36` is `curl -f ... || exit 0` (always healthy); root `Dockerfile:69` is `|| exit 1` (correct contrast). Confirmed.

- **INST-11**: `install.sh:1680` `down -v` (volume destruction), `:1691` `sed '/# Dopemux/,+3d'` (fixed 4-line assumption). Confirmed.

- **Staleness dates — one discrepancy**: The finding claims `install.sh` = `4959a089f` 2026-05-02 (confirmed exactly) and `compose.yml` = `1a1a82384` 2026-05-15 (confirmed exactly), so the 13-day drift window holds. But the finding states `install-docker-mcp-servers.sh` = `586ca44a4` 2026-01-20; git shows `764a929cb` **2026-04-12**. The script is stale (~6 weeks, not ~4 months) but the SHA and date cited are both wrong. This affects only INST-05's staleness sub-claim flavor, not its security core.

Let me do final verification on a few remaining specifics: the `df $HOME` preflight + `docker info` (INST-06), Dockerfile.frontend dhi.io + npm contradiction (INST-09), mcp-proxy-setup port 8080 collision (INST-10), and the dependency pinning claims (INST-07).

All findings now verified at source level. Final confirmations:

- **INST-06**: `docker info &> /dev/null` liveness check at `install.sh:1019` (confirmed), `df -k "$HOME"` ≥10 GB at `:1233-1247` (confirmed). The "docker info masks VM-disk exhaustion" is correctly self-flagged as inferred. `setup.sh` has no daemon liveness (only `command -v docker`). Confirmed; severity-appropriate MED.

- **INST-09**: `Dockerfile.frontend:3,15,31` all `FROM dhi.io/node:18-alpine`; `:11` `npm ci --only=production && npm install` (contradictory). Zero compose references (grep exit 1). Confirmed; LOW appropriate (orphaned).

- **INST-10**: `PROXY_PORT=8080` (`:8`), stale container names `mcp-mas-sequential-thinking`, `mcp-claude-context`, `mcp-zen` (`:53`), Leantime maps host `8080:80` (`compose.yml:165`). Port collision confirmed (though note: Leantime is full-profile only). Confirmed; LOW appropriate.

- **INST-07**: deps are `>=` (`:28-62`), `fastmcp` (`:97`) and `rank_bm25` (`:114`) unbounded, `uv.lock` present (1.1 MB). Confirmed; MED reproducibility, appropriate.

I have everything I need. The findings are overwhelmingly accurate at the code level. My security/severity-calibration job now is to judge each on inflated/deflated severity, missed security angle, and go-live-impact validity. The most important calibration questions:

1. **INST-01 (HIGH)**: Is the documented-installer-breaks-compose claim go-live-blocking, or is severity inflated given the README path works? The audit already resolved authority correctly (README/`uv` path is canonical and sound). Since the *documented canonical* path works and creates the network, and `install.sh`/`setup.sh` are the *alternate* documented path, this is a real break in an advertised entrypoint but not a total go-live blocker. HIGH (not CRIT) is correctly calibrated — but I should weigh whether the dual-documentation itself is the deeper defect.

2. **INST-05 (HIGH)**: This is the one with a genuine security core (unpinned remote code execution + plaintext secrets at default umask, auto-built/run). I'll assess whether HIGH is deflated — running unpinned third-party code with live credentials is arguably the highest-severity *security* item here, but blast radius is low (one internal deploy script references it). The severity tension is real.

3. **INST-08 (MED)**: `|| exit 0` healthcheck — does it deserve elevation given it defeats the install's own verification step and could mask a dead service in production? 

4. The **staleness SHA/date error** in INST-05 needs flagging.

I have a complete, consistent evidence base. Writing the review now.

---

# Adversarial Security Review — Install Lane (SECURITY & SEVERITY-CALIBRATION lens)

**Verdict legend:** CONFIRMED = severity + security framing sound · RECALIBRATE = severity or framing needs adjustment · REFUTED = claim/severity unsupported. All code re-verified independently at `HEAD` (`compose.yml` @ `1a1a82384`).

---

**[INST-01] HIGH — `install.sh` never creates `dopemux-network`** — **CONFIRMED (severity sound; one framing sharpening)**
Verified: `ensure_docker_networks` early-returns for non-`full` (`install.sh:645-647`), and for `full` creates `mcp-network`/`dopemux-unified-network`/`leantime-net` — not `dopemux-network` (`install.sh:652`). `grep dopemux-network install.sh` → 0 matches. `compose.yml:25-27` declares it `external: true`, and **all three stacks point at the same `compose.yml`** (`install.sh:50-52`), with **25 service-level `dopemux-network` references** (`compose.yml`, every service `:58…:647`) — so even `--quick`/core breaks, not just core+research. The correct `inspect || create` lives only in `scripts/start.sh:75`, `scripts/smoke_up.sh:85`, `scripts/consolidate_docker_networks.sh:33` — none invoked by `install.sh`. HIGH (not CRIT) is correctly calibrated: the *canonical documented* path (README:88-90 / `uv sync`) manually creates the network and works, so the documented happy path is not blocked. **Security angle the finding undersells:** the deeper defect is governance, not networking — two checked-in docs (INSTALL.md / `docs/01-tutorials/installation.md`) advertise a broken entrypoint as canonical, which is a *trust/operator-safety* failure for unattended go-live. Severity stays HIGH; the dual-canonical-doc contradiction deserves its own line (overlaps INST-04).

**[INST-02] HIGH — Test harness forces `INSTALLER_TEST_MODE=1`, dead-coding every side-effecting step** — **CONFIRMED (severity sound)**
Verified: `test_installer_basic.sh:49,58` both hard-set `INSTALLER_TEST_MODE=1`; `install.sh` has exactly the 8 skip-guards cited (`648,747,1008,1226,1298,1342,1376,1443`), covering network creation, resource/docker checks, preflight, core install, compose pull/up, shell config, and verification. This is the correct *root-cause* finding — it explains why the 13-day `compose.yml` drift (INST-01) went undetected. Severity HIGH is right: a test suite that structurally cannot exercise the side-effecting path is a false-assurance / "green-but-broken" hazard directly bearing on go-live confidence. The mandate to treat all `install.sh` runtime as `NOT_RUN` is the correct security-conservative posture. Not inflated.

**[INST-03] HIGH — `scripts/install.py` does `pip install -e scripts/` with no build metadata** — **RECALIBRATE (down to MED; correctly broken, but blast radius is too low for HIGH)**
Verified: `scripts/install.py:77` `current_dir = Path(__file__).parent` → `scripts/`; `:78-80` `pip install -e str(current_dir)`; `scripts/{pyproject.toml,setup.py,setup.cfg}` all absent. The install *will* fail — claim CONFIRMED on the merits. **But the finding itself states "Low blast radius (no doc references it)"**, which contradicts a HIGH rating. No README/QUICK_START/INSTALL.md path invokes `scripts/install.py`; it is a dead, unadvertised entrypoint. A broken script that nothing calls and no doc points to is a MED at most (dead code that looks live). No security dimension. Recommend **MED**. (The `logger.info("text", var)` non-interpolation at `:24,:36…` is correctly classed cosmetic.)

**[INST-04] HIGH — `scripts/setup.sh` masks compose failure (`set -e`, no `pipefail`) and creates wrong network name** — **CONFIRMED (severity sound; this is the sharpest security finding by impact-class)**
Verified all three sub-claims: `:13` `set -e` only (no `-u`/`pipefail`); `:178` `if docker compose … up -d 2>&1 | tail -5; then` — pipe exit = `tail` = always 0, so the `else … exit 1` at `:181-183` is **dead code**; `:170` creates `dopemux-unified-network` (the *legacy* net per `consolidate_docker_networks.sh:3`), not `dopemux-network`; success banner at `:240` is reachable. `docs/01-tutorials/installation.md:14` advertises this as canonical quick-start. This is a genuine **fail-closed violation**: the installer reports a clean install over a stack that never started — exactly the "misleading success state" the governance doctrine prohibits. HIGH correctly calibrated; arguably the most operator-dangerous item because it actively lies about success rather than failing loudly. Not inflated.

**[INST-05] HIGH — `install-docker-mcp-servers.sh`: unpinned `git clone` + world-readable secrets + auto-build/run** — **CONFIRMED on security core; RECALIBRATE one sub-claim (staleness SHA/date is wrong)**
Verified the security core precisely: `:57` `git clone "$repo_url" .` at mutable HEAD (no SHA/tag), `:54` `git pull origin main` on update; `.env` heredoc writes `DEEPSEEK/OPENAI/GITHUB/EXA` keys (`:63-84`); **only `chmod +x` appears (`:259,276,294`) — no `chmod 600` on `.env`**, so secrets land at default umask; `./start-all-mcp-servers.sh` auto-runs (`:303`) → `docker-compose up -d --build` (`:240`) builds and executes the freshly-cloned code. `compose.yml:273` ships `mcp-pal`; `mas-sequential` → 0 matches (stale provisioning). Referenced only by `scripts/deploy/setup/install-mcp-servers.sh:128`.

This is the **only finding with a true supply-chain + credential-exposure vector** (unpinned remote code executed with live API keys), and the security framing is correct. **Severity tension:** on a pure security axis this is the most dangerous item (arbitrary upstream code + secret leak); the finding correctly holds it at HIGH-not-CRIT *because blast radius is one internal deploy script* with no canonical/doc path. That trade-off is defensible — I concur with HIGH. **One factual defect:** the finding dates this script `586ca44a4` / 2026-01-20 (~4 months stale); `git log` shows `764a929cb` / **2026-04-12** (~6 weeks stale). The SHA and the "4 months" characterization are both wrong. Staleness conclusion survives, but correct the provenance.

**[INST-06] MED — No preflight for the Docker-VM-disk blocker** — **CONFIRMED (severity sound)**
Verified: `docker info &> /dev/null` liveness at `install.sh:1019`; `df -k "$HOME"` ≥10 GB host check at `:1233-1247`; `setup.sh:64` only `command -v docker`. The claim that `docker info` returns 0 with an exhausted VM disk, and that host-`$HOME` df ≠ VM-allocated disk on macOS, is **correctly self-tagged as inferred** (Docker semantics, not reproduced). No security angle; this is a UX/late-failure issue. MED is appropriate — not inflated, honestly hedged.

**[INST-07] MED — Legacy installers + all image builds float `>=` deps; `fastmcp`/`rank_bm25` unpinned** — **CONFIRMED (severity sound)**
Verified: deps `:28-62` nearly all `>=`; `fastmcp` (`:97`) and `rank_bm25` (`:114`) unbounded; `uv.lock` present (1.1 MB). The reproducibility framing is correct: the README `uv sync --frozen` path is deterministic, but every `pip install -e .` (`setup.sh:132`, `install.py:79`, `install.sh:1307`) and Docker build ignores the lock. **Minor security adjacency the finding could note:** unpinned `>=` with no hash-pinning is a soft supply-chain surface (a yanked/compromised minor could land in a rebuild). The finding scopes it as reproducibility/auditability, which is the right primary axis. MED appropriate.

**[INST-08] MED — `services/dope-context/Dockerfile` healthcheck `|| exit 0` can never be unhealthy** — **CONFIRMED (severity sound; resist elevation)**
Verified exactly: `services/dope-context/Dockerfile:36` `CMD curl -f http://localhost:3010/health || exit 0` vs root `Dockerfile:69` `|| exit 1`. This is a real **fail-closed violation** (failure-looks-healthy) and it defeats the install's own verification (`README.md` curls `:3010/health`; `install.sh wait_for_containers`). I considered elevating to HIGH on the "masks a dead service in production" argument, but **MED is correct**: it degrades a health signal for one service, doesn't break startup, and the operator's explicit `curl` smoke checks (README) catch a truly-dead service independently of Docker health. Severity sound — not deflated.

**[INST-09] LOW — `Dockerfile.frontend` hard-deps private `dhi.io`, orphaned** — **CONFIRMED (severity sound)**
Verified: `:3,15,31` `FROM dhi.io/node:18-alpine`; `:11` `npm ci --only=production && npm install` (contradictory/non-deterministic); **0 compose references** (grep exit 1). LOW correctly calibrated — latent trap with zero current blast radius. The `dhi.io` (entitled registry) dependency is a minor availability/auth footgun if later wired in, not a present security issue. Appropriate.

**[INST-10] LOW — `scripts/mcp-proxy-setup.sh` stale (retired containers, port 8080 collision, unpinned tool)** — **CONFIRMED (severity sound; one scope nuance)**
Verified: `PROXY_PORT=8080` (`:8`); stale names `mcp-mas-sequential-thinking`/`mcp-claude-context`/`mcp-zen` (`:53`); `uv tool install mcp-proxy` unpinned (`:44`); Leantime maps host `${LEANTIME_PORT:-8080}:80` (`compose.yml:165`). Port collision is real **but bounded**: Leantime is a full-profile service, so the clash only manifests on a full stack with the proxy script run concurrently — niche. LOW appropriate; the finding's own "mostly skip / low blast radius" framing is accurate.

**[INST-11] OBS — `install.sh` is well-engineered; `down -v` data-loss + fixed-line `sed` nits** — **CONFIRMED (severity sound; the `down -v` nit is the most security-relevant of the two)**
Verified the positive evidence: `set -euo pipefail` (`:21-23`), ERR trap (`:25-40`), atomic secret write with `chmod 600` (`:706-738`) — note this is the *correct* secret handling that INST-05 lacks, a useful contrast. Uninstall nits verified: `:1680` `down -v` destroys named volumes incl. Leantime MySQL (and the `$DOPEMUX_HOME` backup doesn't cover DB volumes → genuine **silent data-loss on uninstall**); `:1691` `sed '/# Dopemux/,+3d'` assumes a 4-line block (fragile). The `down -v` item is arguably a LOW data-safety finding rather than pure OBS, but folding it into the positive-evidence note is acceptable since uninstall isn't a go-live-path operation. Severity framing sound.

---

## Calibration summary

| Finding | Lane severity | Security ruling | Action |
|---|---|---|---|
| INST-01 | HIGH | CONFIRMED | Keep HIGH; surface dual-canonical-doc contradiction as governance defect |
| INST-02 | HIGH | CONFIRMED | Keep — correct false-assurance root cause |
| INST-03 | HIGH | **RECALIBRATE → MED** | Self-described low blast radius contradicts HIGH; dead unadvertised entrypoint |
| INST-04 | HIGH | CONFIRMED | Keep — sharpest fail-closed violation (lies about success) |
| INST-05 | HIGH | CONFIRMED (core) / **RECALIBRATE provenance** | Keep HIGH; fix wrong SHA `764a929cb`/2026-04-12 (~6 wks, not 4 mo) |
| INST-06 | MED | CONFIRMED | Keep — honestly hedged inference |
| INST-07 | MED | CONFIRMED | Keep — note soft supply-chain adjacency |
| INST-08 | MED | CONFIRMED | Keep — resist HIGH; README curl catches dead service |
| INST-09 | LOW | CONFIRMED | Keep |
| INST-10 | LOW | CONFIRMED | Keep — collision is full-profile-only |
| INST-11 | OBS | CONFIRMED | Keep; `down -v` is a borderline-LOW data-safety nit |

**Net assessment:** Severity calibration is largely sound and security-honest. The lane correctly resisted CRIT-inflation throughout by anchoring on the *working canonical `uv` path* and on *blast radius*. **One genuine over-rating: INST-03 (HIGH→MED)** — its own evidence ("no doc references it") undercuts HIGH. **One factual correction: INST-05's staleness provenance** (SHA and "4 months" both wrong; ~6 weeks). **No under-rated findings** — INST-08 and INST-05 were both candidates for elevation but the lane's lower calls are defensible on blast-radius/compensating-control grounds. The two findings with true security cores (INST-05 supply-chain/secrets, INST-04 fail-closed-success-masking) are correctly identified and framed; no missed security angle of consequence beyond the governance/dual-doc framing on INST-01.

==========================================================================================
## REVIEW-security  (workflow-subagent, a17ab76d5d30e564c, 0 chars)
==========================================================================================

(no substantial output)


==========================================================================================
## REVIEW-security  (workflow-subagent, a7f21ac4bad8ee6a8, 0 chars)
==========================================================================================

(no substantial output)


==========================================================================================
## DISCOVER  (workflow-subagent, a0804e8a7db2f0adb, 7872 chars)
==========================================================================================

I'll map the canonical authority of the Repo Truth Extractor. Let me start by orienting myself in the directory structure and reading the key files.

This is a large service with many files. Let me read the core files in parallel to map the authority structure. The terminal engine candidate is `run_extraction_v5.py` (888KB, most recently modified May 26), but I need to verify the wrapper/shadow relationships.

Key finding so far: `rte_config.py:126` (observed) sets `RUNNER_SCRIPT = CONFIG_FILE.with_name("run_extraction_v5.py")` — so v5 is the canonical runtime engine, and `run_extraction.py` (root, 400 lines) is a legacy stub that raises `NotImplementedError` on live execution (observed `run_extraction.py:271,302`). Now let me examine the v3/v4/v5 headers, the promptset/registry truth, and the validation gate. These files are huge, so I'll read headers and key sections.

Now the picture is sharpening. Critical observations:
- v5 is the canonical engine (`rte_config.py:126`, observed). v4 (`run_extraction_v4.py`) is a thin Typer wrapper that delegates to v5 (`V5_RUNNER`, observed `run_extraction_v4.py:35`) but enforces v4 prompt/artifact contracts.
- v3 (12106 lines) and v5 (23375 lines) share the **identical docstring** — v5 is the evolved fork of v3. v3 is referenced almost exclusively by tests (shadow/legacy).
- `RUNNER_SCRIPT = Path(__file__).resolve()` appears in BOTH v3:159 and v5 (imports from rte_config). Need to confirm v5's `RUNNER_SCRIPT` resolves to itself via rte_config import.

Let me verify the v5 RUNNER_SCRIPT identity, the promptset truth (registry vs v4 promptset.yaml), and the validation gate's role. Let me also check the FIRST_LIVE preset and how phase_s registry interacts.

I now have enough to confirm the core authority chain. One subtle but important detail: `validate_pre_live_gate_v25.py:31` hardcodes `RUNNER_PATH = SERVICE_DIR / "run_extraction_v5.py"` (observed) — confirming v5 as the gated terminal engine. Also `rte_config.py:126` is the single canonical pointer that all proof/reporting reads (`reporting.py`, `rte_reports.py` consume `runner_script` from RUNTIME_PATHS).

Let me confirm two fragmentation risks before writing: (1) the v3-vs-v5 duplicated-docstring fork and whether v3 has a live `__main__` that could still be invoked, and (2) the prompt-truth split (base_prompts vs prompts/v3 vs promptsets/v4/prompts vs generated). Let me also check the ops surfaces (CLI entry) and how v5 main dispatches.

I now have a complete and verified authority map. Key confirmations:

1. **v3 is a live-capable but legacy/shadow engine**: it has its own `--execute` flag (gated by `DPMX_LIVE_OK`, observed `run_extraction_v3.py:11247-11251`) and its own `RUNNER_SCRIPT = Path(__file__).resolve()` (v3:159). README still documents v3 commands extensively (README:79-87) — this is a doc-vs-runtime fragmentation risk (README:27 says "v4 (default)" while config points to v5).

2. **README authority conflict**: README:43 says `dopemux extract truth-run` is "a compatibility alias to the canonical v5 runtime entrypoint" but README:27 calls v4 the "(default)". Meanwhile `rte_config.py:126` hardcodes v5. Three different "canonical" claims.

3. **Prompt-truth precedence is layered** (observed `rte_promptset.py:9-23`): env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` > legacy `UPGRADES_PROMPT_ROOT` > `promptsets/v4/prompts/` (if exists) > `prompts/v3/`. Phase S/SP has a *separate* registry-based truth (`prompts/phase_s/registry.json`).

This is enough. Let me do one quick verification of how the user-facing `dopemux rte`/ops surface actually selects the runner, since that's the operator entry, then write the map.

Confirmed. The operator CLI (`src/dopemux/cli.py:4920`, observed) defaults `--pipeline-version` to `v5`, and `cli.py:4949` hardcodes `pipeline_version="v5"` for the truth-run alias. This contradicts README:27 ("v4 (default)"). The runtime authority (cli.py + rte_config.py) is unambiguous: **v5 is the terminal engine and operator default**. The README's "v4 (default)" is stale doc drift. Per Truth Order, runtime outranks docs.

I have a complete, verified map. Writing the final output now.

---

# RTE AUTHORITY MAP — `services/repo-truth-extractor/`

**Terminal engine (canonical runtime):** `run_extraction_v5.py` (23,375 lines). Sole pointer of record: `rte_config.py:126` → `RUNNER_SCRIPT = run_extraction_v5.py`, fed into `RUNTIME_PATHS.runner_script` (rte_config.py:133-141) which every proof/report consumes (`reporting.py:1026/1077`, `rte_reports.py:255-256`). Operator CLI default is also v5: `src/dopemux/cli.py:4920` (`default="v5"`) and `cli.py:4949` (`truth-run` alias hardcodes v5). Pre-live gate hardcodes the same target: `validate_pre_live_gate_v25.py:31` → `RUNNER_PATH = run_extraction_v5.py`. v5 owns its own `main()` argparse CLI (v5:21502).

**Wrappers (delegate to v5, do not re-implement extraction):**
- `run_extraction_v4.py` — Typer wrapper; executes v5 (`V5_RUNNER`, v4:35) but enforces v4 prompt/artifact contracts from `promptsets/v4/`. *Authority over v4 contract shape, not execution.*
- `rte_ops_surfaces.py` / `rte_phase_wrappers.py` / `rte_promptset.py` — pure helper modules (phase planning, prompt resolution); imported by v5, hold no runner identity.
- `run_repscan.py`, `run_probe.py`, `run_fl_int.py` — operator sub-tools layered on a runner.

**Shadow / legacy:** `run_extraction_v3.py` (12,106 lines, identical docstring to v5 → v5 is its fork). Has its own live `--execute` path gated by `DPMX_LIVE_OK` (v3:11247-11251) and its own `RUNNER_SCRIPT=__file__` (v3:159). In non-test runtime it is referenced only by `run_repscan.py:72`, `run_probe.py:45`, `tools/phase0_serialize_partitions.py` (import-for-helpers). Everything else touching v3 is under `tests/`. `run_extraction.py` (root, 400 lines) is a dead stub — raises `NotImplementedError` on live (`run_extraction.py:271,302`).

**Where phase truth lives:** `phases.py` is canonical for phase IDs, dir names, dependency DAG, and `REQUIRED_PROMPT_STEP_IDS` (phases.py:183-200). v5 imports it directly (v5:185+).

**Where prompt + registry truth lives** (resolution order, `rte_promptset.py:9-23`): env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` → legacy `UPGRADES_PROMPT_ROOT` → `promptsets/v4/prompts/` (if present) → `prompts/v3/`. Phase S/SP uses a *separate* registry: `prompts/phase_s/registry.json` (version=1, declares phase "SP", rte_promptset.py:212-272). Other `registry.json` files (`prescan/`, `phase_s_int/`, `phase_fl_int/`) are sub-pipeline-scoped. `promptsets/v4/promptset.yaml` is the v4-contract source of record (phase order, required sections). `base_prompts/` (5 files) and `promptsets/generated/` (only consumed by `lib/promptgen/sync_engine.py`) are inputs, not runtime truth.

**Top 3 fragmentation risks:**
1. **Doc-vs-runtime "default" conflict.** README:27 calls v4 the "(default)"; runtime (`cli.py:4920`, `rte_config.py:126`) makes v5 the default and terminal engine. README:79-87 still documents v3 invocation. Auditors trusting the README will mis-locate authority. *Runtime outranks docs — treat v5 as canonical.*
2. **Live v3 still reachable.** v3 retains a `DPMX_LIVE_OK`-gated `--execute` path and full proof-emitting `RUNNER_SCRIPT` self-reference. Two engines can emit "runner_sha256" proof bundles; only v5 is gated by `validate_pre_live_gate_v25`. Risk: a v3 run produces audit artifacts outside the v25 gate.
3. **Multi-rooted prompt truth.** Prompt content can resolve from env override, `promptsets/v4/prompts/`, or `prompts/v3/`, while Phase S/SP forks to a JSON registry. The `promptset_sha256` fingerprint (rte_promptset.py:528-579) only pins what was resolved at runtime — divergent roots across operators yield different fingerprints for the "same" phase.

(All claims observed at file:line above; v5/v3 fork inferred from identical docstrings + shared `RUNNER_SCRIPT` idiom.)