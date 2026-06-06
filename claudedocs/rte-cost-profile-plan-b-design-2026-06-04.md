# RTE Cost-Profile Plan B — Direct-Provider Alias Wiring + Profile Design

**Date:** 2026-06-04 · **Base:** `main @ 31d1f168e` · **Branch:** `claude/happy-bhabha-69cdf1`
**Scope (user-approved):** Full wiring (bulk + strict CE/SYNTH) · Direct-provider per profile · 7 new profiles.

## Ground truth (verified, corrects the guide)

| Claim in guide | Verified reality |
|---|---|
| `MODEL_COST_RATES` = 59 priced keys | `lib/spend_ledger.py` dict = **21 baseline placeholders** (0.15/0.60). **Real prices live in `config/pricing.yaml`** (59 models, `PRICED_CONFIRMED`), merged over baseline at `spend_ledger.py:137`. |
| Profiles' `cell_aliases` inert; needs wiring fix | **Primary-route aliasing already wired** at `run_extraction_v5.py:5565` (`_resolve_route_entry_alias`). |
| — | Alias keys are **profile-prefixed** today (`VALUE_DEFAULT_CE_MEDIUM_MODEL`). Shared `model_map.yaml` needs **profile-agnostic keys**; `_resolve_route_model_alias` raises `ValueError` on unresolved `${...}`. |
| — | Only `model_id` is aliased; `provider`/`api_key_env` are hardcoded. Direct-provider switching needs **all three** derived from the alias value. |
| — | Strict checks key on the route's hardcoded `strict_json_schema` flag + provider, not the resolved model (`structured_output_contracts.py:213`). `xai` is in the strict-capable provider set → **fail-open risk** on strict lanes. `gemini` → fails closed. |
| — | Unwrapped `route_entries_for_stage(…,"primary")` sites (`6188`,`6275`,`12716`,`12800`) match resolved (provider,model) against raw `${...}` routes → identity-match breakage post-conversion. Cost preview + P0 preflight also unwrapped. |

`--cost-profile choices = sorted(COST_PROFILES.keys())` (dynamic — new profiles auto-register).
`test_cost_profiles.py::test_cost_profiles_dict_has_four_canonical_profiles` asserts **exactly** the 4 names → must update.

## Cell taxonomy (4 cells, 1:1 with `lane_class`)

| Cell key (profile-agnostic) | lane_class | count | strict | notes |
|---|---|---|---|---|
| `${BULK_DOCS_MODEL}` | BULK_DOCS_GENERAL | 73 | no | provider-diverse OK (gemini/xai) |
| `${BULK_CODE_MODEL}` | BULK_CODE_HEAVY | 6 | no | code; xai strong |
| `${CE_MODEL}` | CE | 43 | **yes** | strict-capable provider only |
| `${SYNTH_MODEL}` | AGG | 14 | **yes** | synthesis-critical; strict-capable only |

## Alias-value format & resolution

Cell-alias values are `provider/model` (existing convention). New full resolver derives the whole triple:
- `xai/grok-4.3` → provider `xai`, env `XAI_API_KEY`, model_id `grok-4.3`
- `openrouter/anthropic/claude-opus-4.6` → provider `openrouter`, env `OPENROUTER_API_KEY`, model_id `anthropic/claude-opus-4.6`
- `openai/gpt-5.3-codex` → provider `openai`, env `OPENAI_API_KEY`, model_id `gpt-5.3-codex`
- bare literal (no `${}`) → unchanged (backward compatible)

**Fail-closed strict guard:** for `strict_required` steps, resolved provider must be in `{openai, openrouter}` (allowlist), else `RuntimeError` before any spend. This closes the `xai`-on-strict fail-open hole the advisor flagged and the gemini-on-strict case (already closed by capability check). Profiles are *also* designed never to map CE/SYNTH to gemini/xai — guard is defense-in-depth against `--model-alias`/env override.

## Resolver change (the only hard part)

Add `_resolve_route_entry_alias_full(route, cfg)` that resolves `model_id`, and **when the original was a `${...}` placeholder**, also overrides `provider` + `api_key_env` from the resolved `provider/model` value. Apply it everywhere raw model_map routes are consumed:
- primary: `run_extraction_v5.py:5565` (swap helper)
- benchmark: `5432`, `5544`
- repair/sidefill: pre-resolve the contract's routes before `resolve_stage_route` at the dispatch sites (`15527/15642/15732/17051`) — OR centralize (see PAL decision)
- identity-match sites `6275/12716/12800` + ladder `6188`: resolve before identity comparison
- cost preview + P0 preflight: ensure they go through resolved routes

**Centralization decision (PAL gpt-5.2 validated):**
- Single `resolve_contract_routes(contract, cfg)` returns a deep-copied, alias-resolved contract; raw contracts stay cached cfg-independently (`_step_contract_for`); resolved views go through `resolved_contract_for(phase, step_id, cfg)` with a **separate cfg-scoped cache keyed by (phase, step_id, cost_profile)** — never mix raw/resolved in one cache.
- Resolution is **idempotent**: only rewrite `model_id` matching `^\$\{[A-Z0-9_]+\}$`; bare literals untouched.
- Keep `lib/structured_output_contracts.py` **cfg-free**: pre-resolve the contract before calling `route_entries_for_stage` / `resolve_stage_route` / `route_entry_by_identity`. Do **not** thread cfg into the lib.
- Formal `_parse_alias_provider_model(value)`: split first segment as provider (allowlist {openai,gemini,xai,openrouter}); remainder must be non-empty; **disallow direct `anthropic/…`** (anthropic only via openrouter); preserve the openrouter namespace remainder (`x-ai/`,`google/`,`anthropic/`) intact for `provider_schema_variant` (run_extraction_v5.py:507).
- Identity-match sites (6275/12716/12800) compare resolved-vs-resolved by passing them the resolved contract.

**Strict guard placement (revised per PAL):** NOT in `strict_capability_reason` (keep it pure technical capability). Enforce the `{openai, openrouter}` allowlist for strict_required steps at **(a) dispatch/selection** in `resolve_effective_step_route` strict path (authoritative, RuntimeError before spend) and **(b) preflight** (early failure across all strict steps).

## Profiles (final set)

Profile-agnostic keys `{BULK_DOCS_MODEL, BULK_CODE_MODEL, CE_MODEL, SYNTH_MODEL}` defined in **every** profile. Strict cells (CE/SYNTH) → openai or anthropic-via-openrouter only. All have a non-null `max_cost_usd_default`.

| Profile | BULK_DOCS | BULK_CODE | CE (strict) | SYNTH (strict) | cap |
|---|---|---|---|---|---|
| `gemini-value` | gemini/gemini-3-flash-preview | gemini/gemini-3.1-pro-preview | openai/gpt-5.3-codex | openrouter/anthropic/claude-opus-4.6 | 8 |
| `grok-fast` | xai/grok-4-fast | xai/grok-4.3 | xai/grok-4.3→**openai/gpt-5.3-codex** | openrouter/anthropic/claude-opus-4.6 | 6 |
| `openrouter-resilient` | openrouter/openai/gpt-5.4-mini | openrouter/openai/gpt-5.3-codex | openrouter/openai/gpt-5.3-codex | openrouter/anthropic/claude-opus-4.6 | 20 |
| `openai-heavy` | openai/gpt-5.4-mini | openai/gpt-5.3-codex | openai/gpt-5.3-codex | openai/gpt-5.5 | 15 |
| `balanced-mix` | gemini/gemini-3-flash-preview | xai/grok-4.3 | openai/gpt-5.3-codex | openrouter/anthropic/claude-opus-4.6 | 12 |
| `quality-mix` | openai/gpt-5.4 | openai/gpt-5.3-codex | openai/gpt-5.5 | openrouter/anthropic/claude-opus-4.6 | 30 |
| `budget-mix` | gemini/gemini-3-flash-preview | xai/grok-4-fast | openai/gpt-5.3-codex | openai/gpt-5.4 | 6 |

(grok-fast CE: strict lane cannot use grok → resolves to openai/gpt-5.3-codex; xai shown as intent only.)
Existing `economy`, `value-default`, `quality`, `experimental` keep their semantics but migrate to the 4 profile-agnostic keys.

All model ids above are present + `PRICED_CONFIRMED`/`PRICED_WITH_CAVEAT` in `config/pricing.yaml` (verified). No new pricing rows required; if any added later, follow the v2 schema with explicit `pricing_status`.

## Test + doc updates
- `test_cost_profiles.py`: replace the "four canonical" assert with the new set; keep required-fields check; add direct-provider full-alias resolution tests (provider+env+model derived; strict guard rejects xai/gemini on strict cell).
- `docs/02-how-to/extraction/rte-cost-profiles.md`: profiles-at-a-glance + cell-alias tables for the new set.

## Implementation status

### Increment 1 — mechanism + profiles + tests (DONE, verified)
- Added to `run_extraction_v5.py`: `COST_PROFILE_CELL_KEYS`, `COST_PROFILE_STRICT_CELL_KEYS`, `STRICT_ALLOWED_PROVIDERS`; helpers `_is_alias_placeholder`, `_parse_alias_provider_model`, `_resolve_route_entry_alias_full`, `_resolve_lane_routes_alias`, `resolve_contract_routes`, `assert_strict_route_provider_allowed`.
- Migrated 4 existing profiles to canonical 4-key cell_aliases; added 7 new profiles (gemini-value, grok-fast, openrouter-resilient, openai-heavy, balanced-mix, quality-mix, budget-mix). All strict cells on {openai,openrouter}; all new profiles capped.
- Swapped primary + benchmark alias resolution to the full resolver (3 sites). Wired the fail-closed strict guard at dispatch in `resolve_effective_step_route`.
- Updated `--model-alias` help; updated/added tests. **`pytest test_cost_profiles.py test_pricing_coverage.py` = 30 passed**; full tests/ collection clean (no import breakage).
- **Runtime behavior unchanged** — profiles are real but INERT until model_map is converted (Increment 2), because resolution is idempotent on the still-hardcoded literals.

### Increment 2 — make profiles live (DONE, verified — full RTE suite 1159 passed / 0 failed)

Shipped: strict-cell profile values corrected to OpenAI-only (catalog says anthropic-via-OpenRouter is NOT `supports_json_schema_strict`, and the 57 CE/AGG steps require strict primary — user confirmed keeping strict cells OpenAI-only); strengthened the dispatch guard to `openai/*` or `openrouter/openai/*`; converted all 136 model_map lead primary routes to `${CELL}` (ruamel round-trip, stripped provider-specific `reasoning_effort`/`service_tier`); threaded `cost_profile` through the preflight/readiness path (`collect_provider_routes`/`derive_route_readiness_summary`) so preflight probes the active profile's models; made `effective_model_routing_payload` resolve placeholders for display; ported a value-default placeholder resolver into the legacy `run_extraction_v3.py` (shared model_map; used by `run_repscan`/`run_probe` `--execute`). Updated 7 test files to the new contract. Verified: resolution invariant (0 leaks, strict→OpenAI) across 6 profiles × 136 steps; cost preview confirms per-profile models via the real resolver; no live LLM calls.

#### Original Increment-2 task list (all completed)
1. **Convert model_map.yaml primary routes** to `${CELL}` by lane_class (CE→`${CE_MODEL}`, AGG→`${SYNTH_MODEL}`, BULK_DOCS_GENERAL→`${BULK_DOCS_MODEL}`, BULK_CODE_HEAVY→`${BULK_CODE_MODEL}`). **Decision: convert the LEAD primary route only**, keep subsequent primary entries as hardcoded provider fallbacks (preserves the fallback ladder + determinism). Repair/sidefill stay hardcoded.
2. Add `resolved_contract_for(phase, step_id, cfg)` (raw `_step_contract_for` + `resolve_contract_routes`, cfg-scoped cache keyed by (phase, step_id, cost_profile)).
3. Rewire raw-route consumers to the resolved contract: `resolve_step_ladder:6186` (needs cfg threaded — signature change), `_structured_output_mode_for_static_route:6273`, identity-match sites (`_contract_route_entry_for_provider_model`, `_batch_route_entry_for_selected_route`), cost preview, P0 preflight (`run_provider_preflight`, `evaluate_online_preflight`). Add the strict allowlist check to preflight (early failure across all strict steps).
4. Verify each consumer compares resolved-vs-resolved (no `${` leaks post-resolution; add a debug invariant).

## Verification (proof)
1. `pytest services/repo-truth-extractor/tests/test_cost_profiles.py tests/test_pricing_coverage.py -q` → **DONE: 30 passed**.
2. (Increment 2) full RTE suite + route-derivation; `--print-cost-preview --phase ALL --cost-profile <each>` → confirm intended provider/model per cell (not baseline fallback); strict guard rejects a forced xai/gemini strict override.
3. `pal/codereview` + `precommit` on the diff.
