# A2 — Cost Truthfulness Audit (RTE-TRUTH program)

- **Audit pass**: A2 of RTE-TRUTH
- **Worktree**: `/Users/hue/code/dopemux-mvp/.claude/worktrees/focused-mahavira-5bd29b` @ `542c17bb4`
- **Scope**: `services/repo-truth-extractor/` cost estimation, spend accounting, cap enforcement, temperature control
- **Method**: static read-only trace. No live LLM/provider calls, no network. Evidence labels: **OBSERVED** (read in source at this SHA), **INFERRED** (derived from observed code, not executed), **UNKNOWN**.

---

## Verdict

**Spend ACCOUNTING is conditionally trustworthy; spend ESTIMATION is not.**

- The **runtime cap tracker** (`SpendTrackerState` + `estimate_usage_cost_usd`, pricing.yaml-backed, fail-closed) is the most truthful component: it prices actual provider-returned usage against a provenance-carrying catalog and refuses to run with missing pricing. Trust it *when a cap is set* — it is entirely inert otherwise (OBSERVED: `run_extraction_v5.py:23985` — `initialize_spend_tracker` only runs `if cfg.max_cost_usd is not None`, and the cap defaults to `None` at `:2368`).
- The **estimate chain** cannot be trusted: three parallel estimators disagree on tokenizer (chars/3.5 vs chars/4), output ratio (15% vs 10% vs 2%), and unknown-model pricing ($0.15/$0.60 vs max-of-catalog $30/$180 — a **200×/300× spread**, confirming and quantifying the prior audit's "~200x divergence").
- **Two independent ledgers accumulate the same run's spend with different prices** (SpendLedger applies flex 0.5× / priority 2.5× / batch / cache multipliers; SpendTrackerState prices flat). On any flex-tier profile their totals diverge ~2× on OpenAI traffic, and both can independently abort the run.

---

## 1. The full estimate chain, end-to-end

### 1.1 Three subsystems compute "cost" (OBSERVED)

| # | Subsystem | Pricing source | Token counting | Output projection | Failure posture |
|---|-----------|---------------|----------------|-------------------|-----------------|
| E1 | **Prescan `CostEstimator`** — `lib/prescan/cost_estimator.py:21`, wired unconditionally via `lib/prescan/engine.py:64` | `lib/spend_ledger.get_model_cost_rate` (catalog→baseline→max-fallback); on *any import/exception*: flat `$0.15/$0.60` (`:19`) | `chars_per_token = 3.5` (`:33`) | flat **15%** of net input (`:49`) | fail-open (logs warning, returns cheap fallback) |
| E2 | **Runtime `SpendLedger`** — `lib/spend_ledger.py:619`; instantiated into `cfg.ledger` at `run_extraction_v5.py:23599–23607` | `MODEL_COST_RATES` = 22 hardcoded `$0.15/$0.60` baseline rows (`:47–69`) **overwritten** by `benchmarking/pricing/catalog.py` rows at import (`:137`) | consumes provider usage when available; else `_estimate_text_tokens` = chars // 4 (`v5:11066`) | `_project_output_tokens` = input // 10, or len(response)//4 (`v5:11071`); preview: **2%** for json-managed steps, min 64 (`v5:11077–11084`) | fail-open: unknown model → `_fallback_cost_rate()` = **max input & max output across the whole registry** (`:286–299`) |
| E3 | **Runtime `SpendTrackerState`** — `run_extraction_v5.py:4183`; init at `:23984–24000` only when `--max-cost-usd` set | `load_pricing_registry()` (`:4452`) reads `config/pricing.yaml` directly, records `pricing_sha256` | none — prices **actual provider usage** only | none — actual `completion_tokens` | **fail-closed**: missing route coverage → `RuntimeError` at init (`:4621–4625`); missing pricing at record time → `RuntimeError` (`:4536`); missing usage in response → run aborted with `cost_cap_usage_unavailable` (`:4735–4737`); init failure → `sys.exit(1)` (`:24000`) |

### 1.2 Chain trace (OBSERVED)

1. **Prescan** (Stage 0, runs by default — `v5:23610`): `CostEstimator.estimate()` produces `net_estimates.total_cost_usd` from corpus bytes using **a single provider/model** (`PrescanConfig.provider/model`) — it prices the entire corpus at one model's rate even though execution fans out across 4 cells and up to 4 providers.
2. **`--print-cost-preview`** (opt-in, requires `--dry-run` + `--phase|--preset` — `v5:22940–22943`): `build_phase_cost_preview` (`rte_ops_surfaces.py:288`, called from `v5:18495/24165`) is per-step route-aware: resolves the effective cell route per step, counts prompt+partition tokens (`preview_partition_usage`, floor 128), projects output at 2% (json-managed) or 10% (others), and prices through `cfg.ledger.price_usage` (E2 rates + optimizer multipliers). It prints `input_estimation_mode`/`output_estimation_mode` labels per step and flags `unknown_model`.
3. **Preventive cap check**: `_check_projected_cost_limit` (`v5:11400`) runs `breach_stage="pre_model_execution"` at ~10 dispatch sites (`v5:7892, 11561, 12131, 12285, 15904, 16915, 17213, 20343, 21600, 23224`); prices projected next call via `cfg.ledger.price_usage` and tests `cfg.ledger.check_limit(estimated)`.
4. **Post-response accounting**, twice in parallel:
   - `_accumulate_runtime_spend` (`v5:11472`) → `cfg.ledger.accumulate(...)` (E2), raises `CostLimitExceededError` `breach_stage="post_model_output"` (`:11517–11540`);
   - `record_request_cost` (`v5:4696`, called at `:12078`) → E3 tracker: prices provider usage flat against pricing.yaml, appends event, sets `cost_abort_triggered` when `total > max` (`:4807–4812`), snapshots `telemetry/spend_ledger.json` with `pricing_sha256`.
5. **Reconciliation**: none. No code compares E1 vs preview vs E2 vs E3 (OBSERVED absence; searched for any cross-check).

### 1.3 Same quantity computed differently in two+ places (OBSERVED)

| Quantity | Place A | Place B | Place C |
|---|---|---|---|
| chars→tokens | prescan **/3.5** (`cost_estimator.py:33`) | runtime/preview **//4** (`v5:11066`) | — |
| output tokens | prescan **15%** (`cost_estimator.py:49`) | runtime fallback **10%** or resp_len//4 (`v5:11071`) | preview json-managed **2%**, min 64 (`v5:11083`) |
| unknown-model rate | estimator except-branch **$0.15/$0.60** (`cost_estimator.py:19`) | E2 fallback **max-of-registry = $30/$180** with catalog loaded (`spend_ledger.py:286`; max verified against pricing.yaml: input 0.05–30.00, output 0.20–180.00) | E3 **raises** (`v5:4536`) |
| run total spend | `SpendLedger.record.total_cost_usd` (multiplier-adjusted) | `SpendTrackerState.total_cost_usd` (flat rates) | — |
| cap breach | `check_limit` pre+post (E2) | `total > max` post-hoc (E3, `v5:4807`) | — |
| version-chain savings | prescan **80% reduction** for non-latest chain members (`cost_estimator.py:44`) | no equivalent anywhere in runtime — INFERRED unvalidated guess | — |

**INFERRED — the catalog-absent trap**: `MODEL_COST_RATES.update(_catalog_rates())` (`spend_ledger.py:137`) silently degrades to `{}` when the catalog import or load fails (`:20–21, :95–97`). Then *every* model — including gpt-5.5 (true $5/$30) — prices at the baseline $0.15/$0.60: a **33×/50× under-accounting**, and `_fallback_cost_rate()`'s "max" also collapses to $0.15/$0.60. The E2 ledger reports success either way (`pricing_source` field is the only tell). This is the mechanism behind the historic ~200× estimator-vs-ledger divergence: with catalog loaded, estimator except-branch $0.15/$0.60 vs ledger unknown-model $30/$180 = **200× input / 300× output**.

---

## 2. Profile × cell model resolution and pricing coverage

### 2.1 Cell resolution (OBSERVED, `v5:650–926`)

| Profile | BULK_DOCS | BULK_CODE | CE | SYNTH | cap $ |
|---|---|---|---|---|---|
| economy | openai/gpt-5.4-mini | openai/gpt-5.4-mini | openai/gpt-5.1-codex-mini | openai/gpt-5.4 | 5 |
| value-default | openai/gpt-5.4-mini | openai/gpt-5.3-codex | openai/gpt-5.3-codex | openai/gpt-5.5 | 5 |
| quality | openai/gpt-5.4 | openai/gpt-5.5 | openai/gpt-5.5 | openai/gpt-5.5 | 25 |
| experimental | gemini/gemini-3.5-flash | openai/gpt-5.5 | openai/gpt-5.5 | openai/gpt-5.5 | 25 |
| gemini-value | gemini/gemini-3-flash-preview | gemini/gemini-3.1-pro-preview | openai/gpt-5.3-codex | openai/gpt-5.5 | 8 |
| grok-fast | xai/grok-4-fast | xai/grok-4.3 | openai/gpt-5.3-codex | openai/gpt-5.4 | 6 |
| openrouter-resilient | or/openai/gpt-5.4-mini | or/openai/gpt-5.3-codex | or/openai/gpt-5.3-codex | or/openai/gpt-5.4 | 20 |
| openai-heavy | openai/gpt-5.4-mini | openai/gpt-5.3-codex | openai/gpt-5.3-codex | openai/gpt-5.5 | 15 |
| balanced-mix | gemini/gemini-3-flash-preview | xai/grok-4.3 | openai/gpt-5.3-codex | openai/gpt-5.5 | 12 |
| quality-mix | openai/gpt-5.4 | openai/gpt-5.3-codex | openai/gpt-5.5 | openai/gpt-5.5 | 30 |
| budget-mix | gemini/gemini-3-flash-preview | xai/grok-4-fast | openai/gpt-5.3-codex | openai/gpt-5.4 | 6 |

Ladder-hardcoded fallback models reachable regardless of profile (OBSERVED, `promptsets/v4/model_map.yaml`): `openai/gpt-5.5` (flex), `xai/grok-4.3`, `openai/gpt-5.3-codex` (Phase D AGG repair).

### 2.2 Coverage verdict (OBSERVED)

**All 13 distinct profile-cell models AND all 3 ladder fallbacks have priced entries in `config/pricing.yaml`** (RTE_PRICING_V2, 68 model keys, 57 with both `input_cost_per_m` and `output_cost_per_m`). Provenance fields present per row: `pricing_source_type`, `pricing_source_ref` (URLs), `pricing_confidence`, `pricing_status`, `effective_start_date`, plus optimizer fields. Verified inventory doc referenced in header: `docs/06-research/extraction/rte-cost-profile-redesign/verified-model-inventory-2026-05.md`.

- **UNKNOWN — staleness**: entries dated 2026-05-23; whether vendors' prices changed since cannot be verified offline. `effective_end_date: null` everywhere; nothing enforces recency.
- **OBSERVED — 11 of 68 entries lack numeric rates** (57 priced): those rows are skipped by both loaders; if such a model is ever routed, E3 fails closed but E2 silently max-prices it.
- **OBSERVED — coverage of profiles is complete today**, but there is no CI gate tying `COST_PROFILES` cell_aliases + ladder fallbacks to pricing.yaml keys; coverage is only checked at runtime, and only in E3 (`v5:4616–4625`), and only when a cap is set. A new profile alias can silently route an unpriced model with no cap → E2 max-fallback pricing distorts the ledger; with a cap → hard startup failure (good, but late).

### 2.3 Quantified plausible estimate error (INFERRED, arithmetic from OBSERVED rates)

Using gpt-5.5 ($5/$30 per 1M) on 1M net input tokens:

| Output assumption | Est. cost | vs actual 50% output ratio ($20) |
|---|---|---|
| prescan 15% | $9.50 | **2.1× under** |
| runtime 10% | $8.00 | 2.5× under |
| preview json-managed 2% | $5.60 | 3.6× under |

Reasoning-heavy models are worse: reasoning tokens bill as output; xai reasoning variants (e.g. `grok-4.20-beta-0309-reasoning`, priced in catalog) can emit output comparable to input. A 15% assumption vs a real 100% output ratio on a $30/1M-output model is a **~4–6× total-cost underestimate**; on synthesis/AGG phases (SYNTH cell = gpt-5.4/5.5 in every profile) this is the dominant error term.

Tokenizer error: chars/3.5 (prescan) vs chars/4 (runtime) is a systematic **14% disagreement** between the two estimates of the *same corpus* before any model even runs. Neither uses a real tokenizer (no tiktoken anywhere in the service — OBSERVED absence). Code-heavy corpora tokenize denser than 4 chars/token, so both under-count input on code (INFERRED, typically 10–25%).

Version-chain "80% reduction" (`cost_estimator.py:44`): no runtime mechanism corresponds to it — the savings are claimed in the estimate but nothing in the dispatch path dedupes version-chain members at an 80% rate (UNKNOWN whether chunker achieves anything comparable). Pure optimism in the preview number.

Compounding worst case (economy profile, code repo, reasoning-heavy fallback engaged, catalog present): 14% token undercount × ~2–4× output undercount × unmodeled repair/sidefill retries (preview prices only primary routes' single pass — OBSERVED: `build_phase_cost_preview` iterates prompts×partitions once, no retry/repair multiplier) → **preview plausibly 3–8× below realized spend**. Conversely, on cache-heavy reruns E3 flat pricing ignores cached-input discounts and *over*-reports vs true bill (INFERRED).

---

## 3. Cap enforcement

- **"preventive" semantics (OBSERVED)**: all 11 profiles declare `cost_cap_mode: "preventive"` and `RunnerConfig` defaults to `"preventive"` (`v5:2380`), but no code branches on the field's value other than carrying it in config output — searched; the preventive behavior is unconditionally provided by `_check_projected_cost_limit` call sites. The knob is decorative (INFERRED: post_hoc value would change nothing).
- **Where checks run (OBSERVED)**: pre-dispatch (`pre_model_execution`, E2-priced projection incl. optimizer multipliers) at ~10 sites; post-response twice (E2 `post_model_output` raise; E3 `total > max` flag). E3 permits **one-call overshoot**: cost is recorded, *then* compared (`v5:4806–4812`) — the breaching call's full cost is spent. E2's `make_projected_cost_check` helper (`spend_ledger.py:580`, closes audit finding F2-MED-1) exists but is **not referenced from v5** (OBSERVED absence) — the shipped preventive path is `_check_projected_cost_limit` instead.
- **Preview and cap do NOT use the same numbers (OBSERVED)**: preview + preventive check price via E2 (`cfg.ledger.price_usage`: catalog rates × flex/priority/batch/cache multipliers, `v5:11152–11163`); the authoritative abort tracker E3 prices flat pricing.yaml rates with no multipliers (`v5:4526–4541`). On flex-tier profiles (economy, gemini-value, grok-fast, budget-mix; OpenAI flex multiplier 0.5) the projection is half the E3 accounting rate — a run projected to fit the cap can be E3-aborted at ~half the expected work (INFERRED).
- **Concurrency (OBSERVED)**: cap requires `--partition-workers 1` (`v5:4603`) — deterministic but serializing; E3 handles the concurrent-breach race defensively anyway (`:4716–4728`).
- **Cap defaults (OBSERVED)**: `max_cost_usd` defaults `None`; profile `max_cost_usd_default` values exist but a capless invocation gets **no tracker, no fail-closed pricing check, and E2's fail-open max/baseline pricing as the only accounting**. `fail_closed_if: ["unknown_pricing_with_cost_cap"]` in alias metadata is declarative only — the actual enforcement lives in E3 init and is conditioned on the cap being set, matching the metadata by coincidence of implementation (INFERRED).
- **Abort integrity (OBSERVED, good)**: `COST_ABORTED` propagates to run status (`compute_run_status:4264`), resume is refused, partial outputs retained, `spend_ledger.json` snapshot carries `pricing_sha256` — good auditability on the E3 side.

---

## 4. Temperature

**OBSERVED — three hardcoded 0.1 sites, confirmed:**
1. `run_extraction_v5.py:10292` — `build_chat_payload` calls `resolve_temperature(provider, model_id, 0.1)`; `resolve_temperature` (`:10264–10269`) returns `None` (omit) **only** for `provider == "openai" and model_id.startswith("gpt-5")`, else the literal default `0.1`.
2. `run_extraction_v5.py:10624` — `_build_gemini_config_for_model`: `"temperature": 0.1` in the Gemini SDK config dict (native-SDK transport path, bypasses `build_chat_payload`).
3. `llm_runtime.py:735` — `"temperature": 0.1` in that runtime's payload builder (forwarded to chat kwargs at `:773–774`).

No CLI flag, env var, or profile key controls temperature (OBSERVED absence — searched arg parser and RunnerConfig).

**Minimal operator-facing design (proposed):**
- Add `--llm-temperature FLOAT` (default `0.1`, range-validated 0.0–2.0) → `RunnerConfig.llm_temperature`; optional env `RTE_LLM_TEMPERATURE` with CLI taking precedence.
- Thread `cfg` (or the resolved float) into the three sites so each becomes `resolve_temperature(provider, model_id, cfg.llm_temperature)`. `resolve_temperature` stays the **single omission-policy choke point** — the gpt-5 `None` rule is preserved untouched, and the Gemini/llm_runtime sites gain the same rule for free (today site 2 and 3 don't consult it at all; site 2 would send `temperature` to a gpt-5 model if OpenAI models ever routed through the Gemini builder — currently unreachable, but the asymmetry is latent debt).
- Record `temperature_effective` (float or `"omitted"`) in request meta / PROOF_PACK so runs are reproducible and auditable.
- Fail closed on out-of-range values at parse time; no per-step override in v1 (YAGNI).

---

## 5. DESIGN — the truthful estimator

**Headline: one pricing authority, one tokenizer, per-family output models, printed assumptions, fixture-locked accuracy.**

1. **Single pricing source with provenance (collapse E1/E2/E3 onto pricing.yaml).**
   - `config/pricing.yaml` already carries the right schema (`pricing_source_type/ref/confidence/status`, `effective_start_date`, optimizer fields). Make `benchmarking/pricing/catalog.py` the *only* loader; delete `MODEL_COST_RATES` static baselines and `BASELINE_*_COST_PER_1M_USD` from `lib/spend_ledger.py` (and the v5 `:339–356` shims).
   - Unknown model + cap set → **raise** (align E2 with E3). Unknown model + no cap → refuse to print a dollar estimate; print `UNPRICED` with the model key instead of inventing $0.15 or $30.
   - Catalog load failure is a startup error whenever any costed operation is requested — never a warning that silently flips every rate to $0.15/$0.60.
   - Add `stale_after` (e.g. 90 days past `effective_start_date`) → estimates print a `PRICING_STALE` warning; CI gate asserts every model reachable from `COST_PROFILES` cell_aliases + model_map ladder fallbacks resolves to a priced, non-stale row.

2. **Per-model-family output multipliers, calibrated from the ledger.**
   - Replace the 15%/10%/2% scatter with one table: `output_ratio[lane_class][model_family]` shipped in pricing.yaml (e.g. `BULK_DOCS×gpt-5-mini: 0.08`, `CE×codex: 0.03` for json-managed, `AGG×gpt-5.5: 0.35`, `*×reasoning: 1.0+`), each row carrying `ratio_source: {measured|assumed}` and sample count.
   - Feedback loop: `telemetry/spend_ledger.json` entries already contain phase/step/model prompt+completion tokens — add a small offline job that recomputes ratios from the last N runs and emits a calibration diff for review. Reasoning models get an explicit `reasoning_output_multiplier` instead of being averaged away.
   - Model retry/repair/sidefill expected overhead as a per-lane multiplier (measured re-dispatch rate), so previews stop pricing exactly one pass.

3. **Tokenization strategy.**
   - One shared `estimate_tokens(text, provider, model_id)` util used by prescan, preview, and runtime fallback. OpenAI/OpenRouter-OpenAI → tiktoken `o200k_base` when importable; Gemini/xAI → chars/4 tagged `tokenizer: heuristic_chars4`. Delete the 3.5 constant. Every estimate carries `tokenizer` + `confidence` fields.
   - Prescan must estimate **per-cell blended cost** using the active profile's cell_aliases and the model_map lane distribution — not a single `PrescanConfig.model` for the whole corpus. Drop the version-chain "80%" claim unless the chunker measurably dedupes; report measured dedupe instead.

4. **Printed assumptions in every preview.**
   Preview header must state: pricing file + `pricing_sha256` + version + newest `effective_start_date`; per-cell resolved model and rate; tokenizer mode; output ratio used per step (already partially present as `output_estimation_mode` — extend with the numeric ratio and its `ratio_source`); tier/batch/cache multipliers applied; retry overhead multiplier; count of UNPRICED/stale models; and the sentence "cap enforcement prices this run with the SAME rates shown above" — made true by folding E3's flat pricing and E2's multiplier pricing into one `price_call()` used by preview, preventive check, and accounting.

5. **Fixture-table acceptance spec.**
   Commit `tests/fixtures/cost_truth/` with recorded runs (prompt corpora + captured provider usage JSON, no live calls):

   | profile | phase | repo-size fixture | expected est. USD | tolerance |
   |---|---|---|---|---|
   | economy | A | small (2 MB) | from fixture | ±20% |
   | value-default | A, C | medium (20 MB) | from fixture | ±25% |
   | quality | R/S synth | medium | from fixture | ±30% |
   | grok-fast | C | code-heavy | from fixture | ±30% |
   | gemini-value | D | docs-heavy | from fixture | ±30% |
   | openrouter-resilient | A | small | from fixture | ±25% |

   Acceptance: (a) `--print-cost-preview` vs replayed-ledger actuals within tolerance per cell; (b) preview total == preventive-check pricing == accounting pricing on identical usage (exact, same code path); (c) unknown-model fixture → hard failure with cap, `UNPRICED` label without; (d) flex-tier fixture → single ledger total, no 2× shadow divergence; (e) tolerance breach fails CI, forcing recalibration of the ratio table rather than silent drift.

---

## Defect register (severity-ordered)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| A2-1 | CRIT | Preview/preventive-check pricing (E2, multiplier-adjusted) ≠ abort-authority pricing (E3, flat) — ~2× divergence on flex profiles; two ledgers, two totals, both can abort | OBSERVED `v5:11152` vs `v5:4526`; INFERRED magnitude |
| A2-2 | CRIT | Fail-open pricing collapse: catalog load failure silently reprices everything at $0.15/$0.60 (33–50× under on gpt-5.5); unknown-model fallback = max-of-registry $30/$180 (200×/300× vs estimator except-branch) | OBSERVED `spend_ledger.py:19,95–97,137,286–299`; rates verified vs pricing.yaml |
| A2-3 | HIGH | Three contradictory output-token heuristics (15%/10%/2%) and two tokenizers (3.5/4.0), none measured, none printed with the prescan number; reasoning models unmodeled (~4–6× under on synth) | OBSERVED `cost_estimator.py:33,49`; `v5:11066,11071,11083` |
| A2-4 | HIGH | Cap entirely opt-in: default `max_cost_usd=None` disables E3 including its fail-closed pricing coverage check; profile `max_cost_usd_default` values are not applied automatically (UNKNOWN whether any wrapper applies them — not found in v5 arg handling) | OBSERVED `v5:2368,23985` |
| A2-5 | MED | Prescan estimator prices whole corpus at one model, claims unverified 80% version-chain savings, prices no repair/sidefill overhead | OBSERVED `cost_estimator.py:27,44` |
| A2-6 | MED | `cost_cap_mode` field is decorative; `make_projected_cost_check` (F2-MED-1 fix) dead code in v5 | OBSERVED absence of consumers |
| A2-7 | MED | E3 allows one-call overshoot (record then compare); usage-absent responses abort the whole run (fail-closed but blunt) while E2 concurrently fabricates estimated usage for the same event | OBSERVED `v5:4806–4812,4735; 11458–11469` |
| A2-8 | LOW | Temperature hardcoded 0.1 at 3 sites; only `build_chat_payload` honors the gpt-5 omission rule; no operator control | OBSERVED `v5:10264–10303,10624; llm_runtime.py:735` |

## Residual unknowns

- Real-world accuracy of pricing.yaml rates vs current vendor price sheets (network-verifiable only).
- Whether any orchestration wrapper injects `max_cost_usd_default` from the profile (not found in `run_extraction_v5.py`; UNKNOWN for external callers).
- Actual measured output ratios per lane (requires ledger history from live runs; recommend running the §5.2 calibration job on existing `telemetry/spend_ledger.json` artifacts).
