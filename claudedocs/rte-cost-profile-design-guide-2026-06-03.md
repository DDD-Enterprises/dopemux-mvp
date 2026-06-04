# RTE Cost-Profile Design Guide — adding Gemini / xAI / OpenRouter profiles

**Date:** 2026-06-03 · **Basis:** main @ `31d1f168e` (read in worktree) + the
`docs/06-research/extraction/rte-cost-profile-redesign/` research.
**Companion:** see `rte-final-go-live-audit-2026-06-03.md` for the cost-safety findings this builds on.

---

## 0. The one thing you must understand first

A "cost profile" is **not** where model selection actually happens today. There are **three
route-resolution layers** in v5 (`run_extraction_v5.py:resolve_effective_step_route:5501`), in order:

1. **Explicit override** — `--model-alias K=V`, env vars (`_resolve_explicit_route_override`).
2. **Benchmark-owned route** — the benchmarking-governance lane can *own* a step's route
   (`_resolve_benchmark_owned_stage_route`); alias-resolved via `_resolve_route_entry_alias`.
3. **`model_map.yaml` `primary_routes` / `repair_routes` / `sidefill_routes`** — the per-step
   contract. **This is what actually runs for normal use.**

**Critical finding:** `promptsets/v4/model_map.yaml` contains **555 hardcoded `model_id:` entries
and ZERO `${ALIAS}` placeholders.** Cost profiles expose `cell_aliases` (e.g.
`VALUE_DEFAULT_SYNTH_CRITICAL_MODEL`), but nothing in `model_map.yaml` references them — so
**a profile's `cell_aliases` are currently inert for normal runs.** This is exactly why the
audit's cost preview showed economy ≈ quality (~$47) despite "different" models: the models come
from `model_map.yaml`, not the profile.

What a profile *does* reliably change today:
`default_service_tier`, `enable_cached_input`, `enable_batch_when_supported`,
`escalation_max_hops`, `max_cost_usd_default`, `cost_cap_mode`, and (via `routing_policy`) the
**tier** selection. Model identity is dominated by `model_map.yaml` + benchmark ownership.

> Side note: `model_map.yaml` already routes many steps to **`grok-4.3`** and `gpt-5.5` — so
> xAI is already in the default path; Gemini/OpenRouter are not, at the primary tier.

---

## 1. Two honest ways to "design more profiles"

### Approach A — Route via `model_map.yaml` (works today, NOT profile-switchable)
Edit the per-step `primary_routes` / `repair_routes` / `sidefill_routes` in
`promptsets/v4/model_map.yaml` to use Gemini/xAI/OpenRouter models. Dispatch reads this directly.
**Limitation:** one shared map → you can't switch providers per `--cost-profile`; you'd fork the
map or use `--model-alias`/env overrides per run.

### Approach B — Make profiles real (the intended design; needs a wiring fix first)
Convert the model_map routes you want profile-switchable from hardcoded IDs to `${ALIAS}`
placeholders, then each profile's `cell_aliases` supplies the concrete model. This is what the
`cell_aliases` mechanism was built for (`resolve_cell_alias` / `_resolve_route_entry_alias`
already resolve `${...}` with precedence: CLI `--model-alias` > env > profile default). **Until
the placeholders exist in `model_map.yaml`, new profiles' `cell_aliases` do nothing.**

**Recommendation:** do **B** for the cells you care about (CE/SYNTH/EXTRACT/BULK) so profiles
become meaningful and switchable; fall back to **A** (or `--model-alias`) for one-off runs. Track
the model_map-placeholder conversion as its own task — it's the prerequisite that makes the whole
profile system actually function.

---

## 2. What the research recommends per provider

From `routing-design-2026-05.md` + `routing-consensus-2026-05.md` (Phase C design / Phase D
consensus), `GEMINI_ROUTING_FIX_PLAN.md`, `PRESCAN_GROK_PASSES_OPTIMIZATION_PLAN.md`:

- **Gemini** — strong/cheap on **non-code bulk + docs** (phases A,H,W,D docs, EXTRACT low/med);
  weak on code synthesis; **never put it on SYNTH-critical**. Use `gemini-3-flash-preview`
  (docs bulk) and `gemini-3.1-pro-preview` (synthesis fallback only). No strict-JSON guarantee.
- **xAI / Grok** — excellent/cheap on **code extract** and reasoning; reliability on strict-JSON
  RTE cells unproven → keep off SYNTH-critical, use as primary on EXTRACT(code) / repair on SYNTH.
  Use `grok-4-fast` (fast/cheap), `grok-4-1-fast-reasoning` (reasoning), `grok-4.3` (already in
  model_map). **Disable batch for xAI** (`enable_batch_when_supported` semantics + xAI batch
  unverified — Phase D consensus).
- **OpenRouter** — use as the **resilient primary for CE cells + Anthropic access** (Sonnet/Opus);
  multi-upstream failover replaces a circuit breaker. Aggregator latency is the tradeoff.
  Per-request failover: on 5xx/429/timeout try the next ladder route once before backoff.

---

## 3. Exact priced model keys (use these verbatim — wrong format → silent fallback)

`MODEL_COST_RATES` in `lib/spend_ledger.py` (59 entries). Keys are **provider-prefixed**; a
bare/incorrect key silently bills at the ledger fallback ($30/$180 per 1M). Verified-present keys:

- **Gemini (direct):** `gemini/gemini-2.5-flash`, `gemini/gemini-2.5-flash-lite`,
  `gemini/gemini-2.5-pro`, `gemini/gemini-3-flash-preview`, `gemini/gemini-3.1-flash-lite`,
  `gemini/gemini-3.1-pro-preview`, `gemini/gemini-3.5-flash`
- **xAI (direct):** `xai/grok-4-fast`, `xai/grok-4-1-fast-non-reasoning`,
  `xai/grok-4-1-fast-reasoning`, `xai/grok-4.3`, `xai/grok-code-fast-1`, `xai/grok-4.20-beta`
- **OpenRouter:** `openrouter/anthropic/claude-haiku-4.5`,
  `openrouter/anthropic/claude-sonnet-4.5`, `openrouter/anthropic/claude-sonnet-4.6`,
  `openrouter/anthropic/claude-opus-4.5`, `openrouter/anthropic/claude-opus-4.6`,
  `openrouter/anthropic/claude-opus-4.7`, `openrouter/openai/gpt-5.3-codex`,
  `openrouter/openai/gpt-5.4`, `openrouter/openai/gpt-5.4-mini`,
  `openrouter/x-ai/grok-4.1-fast`, `openrouter/x-ai/grok-4.3`,
  `openrouter/google/gemini-3-pro-preview`, `openrouter/google/gemini-3.5-flash`

Auth env per provider (`PROVIDER_API_KEY_ENV`): `gemini→GEMINI_API_KEY`, `xai→XAI_API_KEY`,
`openrouter→OPENROUTER_API_KEY`. Any **new** model id you introduce must be added to
`MODEL_COST_RATES` before go-live or the estimate/ledger is wrong.

---

## 4. Proposed profiles (concrete, research-aligned)

Each shown as profile knobs + the cell→model intent. **Models are profile-switchable only after
the Approach-B placeholder conversion** (§1); otherwise set them via `model_map.yaml`/`--model-alias`.

### `gemini-value` — cheap docs/non-code lean
```
routing_policy: balanced_openrouter   default_service_tier: flex
enable_cached_input: true   enable_batch_when_supported: true   escalation_max_hops: 2
max_cost_usd_default: 8.00            cost_cap_mode: preventive
cells:  BULK_EXTRACT/docs → gemini/gemini-3-flash-preview
        CE_MEDIUM (code)  → openai/gpt-5.3-codex   (gemini weak on code)
        SYNTH_HIGH        → gemini/gemini-3.1-pro-preview
        SYNTH_CRITICAL    → openrouter/anthropic/claude-opus-4.6   (never gemini)
```

### `grok-fast` — cheapest code-extract lean
```
routing_policy: balanced_grok_openrouter   default_service_tier: flex
enable_cached_input: true   enable_batch_when_supported: false   (xAI batch unverified)
escalation_max_hops: 2      max_cost_usd_default: 6.00   cost_cap_mode: preventive
cells:  BULK_EXTRACT       → xai/grok-4-fast   (repair → openai/gpt-5.4-mini)
        CE_MEDIUM (code)   → xai/grok-4.3
        SYNTH_HIGH         → xai/grok-4-1-fast-reasoning   (repair → openrouter/anthropic/claude-sonnet-4.6)
        SYNTH_CRITICAL     → openrouter/anthropic/claude-opus-4.6   (never grok)
```

### `openrouter-resilient` — single-key, multi-upstream, Anthropic-forward
```
routing_policy: balanced_openrouter   default_service_tier: default
enable_cached_input: true   enable_batch_when_supported: false
escalation_max_hops: 3      max_cost_usd_default: 20.00   cost_cap_mode: preventive
cells:  CE_MEDIUM      → openrouter/openai/gpt-5.3-codex   (repair → direct openai/gpt-5.3-codex)
        CE_HIGH        → openrouter/anthropic/claude-opus-4.5
        BULK_EXTRACT   → openrouter/openai/gpt-5.4-mini
        SYNTH_HIGH     → openrouter/anthropic/claude-sonnet-4.6
        SYNTH_CRITICAL → openrouter/anthropic/claude-opus-4.6
```

Every proposal **sets a `max_cost_usd_default`** — do not repeat the default/quality profiles'
`None` (uncapped) mistake from the audit.

---

## 5. Wiring checklist (per new profile)

1. **`run_extraction_v5.py:624` `COST_PROFILES`** — add the entry with all required fields
   (`routing_policy, default_service_tier, enable_cached_input, enable_batch_when_supported,
   escalation_max_hops, max_cost_usd_default, cost_cap_mode, notes, cell_aliases`; `warning`
   optional). Required-field set enforced by `test_cost_profiles.py::test_each_profile_has_required_fields`.
2. **`--cost-profile` choices** — defined at `run_extraction_v5.py:21656`. Confirm whether
   `choices=` is static (edit the list) or derived from `COST_PROFILES.keys()` (auto). *Verify
   before relying on auto.*
3. **`routing_policy`** — reuse an existing one (`balanced_openrouter`, `balanced_grok_openrouter`,
   `quality`, `cost`, `optimal`) or add a new policy + its per-tier ladders to the routing tables
   (`run_extraction_v5.py` ~918/1079). Reusing is simplest.
4. **Models that actually run** — either (A) edit `promptsets/v4/model_map.yaml` step routes, or
   (B) convert target steps to `${ALIAS}` and let `cell_aliases` drive them.
5. **`lib/spend_ledger.py` `MODEL_COST_RATES`** — ensure every model id (exact prefixed key) is
   present; add any new ones with real rates.
6. **`enable_batch_when_supported: false`** whenever xAI is primary on batch-eligible cells.
7. **Docs** — `docs/02-how-to/extraction/rte-cost-profiles.md`.

## 6. Validate before live

- `pytest services/repo-truth-extractor/tests/test_cost_profiles.py -q` (structure/aliases).
- `--print-cost-preview --phase ALL --cost-profile <new> --dry-run` → sanity $ + confirm the
  intended provider/model appears per phase. **Caveat (from audit): the preview under-reflects
  profile model choices** — verify the actual `model_map`/alias resolution, don't trust the $ alone.
- Pre-live validator: `--preset first-live --execute --cost-profile <new>` (with `DPMX_LIVE_OK`)
  must pass route-derivation + active-model-resolution + the **P0 online preflight** (every
  routed model must be reachable on its key — the audit caught `gpt-5.3-codex` 404ing; check your
  Gemini/xAI/OpenRouter keys actually serve the chosen models).
- After: reconcile a small completing run against `SPEND_LEDGER.json` before trusting estimates.

---

## 7. Decisions for you

- **Approach A (model_map edit, ships now) vs B (placeholder conversion, makes profiles real)?**
  B is the right long-term fix but is a bigger change; A is faster for a one-off provider trial.
- **Which of the 3 proposed profiles** (or a single multi-provider "balanced-all-three") to build?
- Want me to **wire** the chosen profile(s) end-to-end (with the model_map placeholder conversion
  if Approach B), add `MODEL_COST_RATES` entries, and run the validator? That's an implementation
  task — say the word and I'll do it on a branch with a proof bundle.
