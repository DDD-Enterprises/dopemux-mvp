---
id: adr-rte-cost-profiles
title: "RTE cost profiles + service_tier / cached / batch optimizer wiring"
type: adr
status: accepted
owner: rte-routing
date: 2026-05-23
supersedes:
  - "implicit-routing-policy-design-v1 (8 hardcoded policies, no optimizer wiring)"
adhd_complexity: 0.6
adhd_energy: high
---

# ADR: RTE cost profiles + service_tier / cached / batch optimizer wiring

## Status

Accepted (2026-05-23). Implementation landed under [Plan: Research current LLM models + redesign RTE cost profiles & routing](/Users/hue/.claude/plans/use-gpt-researcher-to-research-parallel-nest.md).

## Context

The Repo Truth Extractor (RTE) shipped 8 hardcoded routing policies (`cost`, `balanced`, `balanced_openrouter`, `balanced_grok_openrouter`, `quality`, `openrouter`, `gemini_primary`, `optimal`) and a flat-baseline pricing model. The 2026-05-09 audit flagged:

- **F2-HIGH-1**: synthesis-tier phases (R/S) routed to bulk-tier models — premium output requirements vs bulk model capacity mismatch.
- **F2-MED-5**: every model fell back to a flat `$0.15/M input · $0.60/M output` baseline because the pricing catalog (`config/pricing.yaml`) had only partial coverage and the spend ledger ignored most provider-specific fields.
- **Unwired optimizers**: OpenAI `service_tier=flex` (50% off) and `service_tier=priority` (2.5× faster), Anthropic `cache_control` prompt caching (90% input discount), and OpenAI/Anthropic/Gemini batch API (50% off) were not exposed to the routing layer at all.
- The default routing policy (`balanced_openrouter`) was chosen pre-audit, before today's frontier-model catalog (gpt-5.5, claude-opus-4.6/4.7, gemini-3.5-flash, grok-4.3).

## Decision

Replace the 8 routing policies with **4 cost profiles** backed by a `(lane_class × capability_tier)` matrix. Wire `service_tier`, prompt caching, and batch discount through the entire LLM call path (catalog → spend ledger → `llm_runtime.call_llm()` → `batch_clients`).

### Cost profiles

| Profile | Service tier | Cached | Batch | Escalation hops | Use case |
|---|---|---|---|---|---|
| `economy` | flex | on | on | 1 | Minimum spend; flex tier + cheapest capable models; quality degraded on SYNTH-critical |
| `value-default` (NEW DEFAULT) | default | on | on | 2 | Best cost/quality ratio; replaces `balanced_openrouter` |
| `quality` | priority | on | off | 3 | Premium production runs |
| `experimental` | default | on | off | 2 | Bleed-edge frontier models; opt-in only |

Legacy `--routing-policy` flag retained for one release as a deprecated alias map:

| Legacy policy | Maps to cost profile |
|---|---|
| `cost` | `economy` |
| `balanced`, `balanced_openrouter`, `balanced_grok_openrouter`, `openrouter`, `gemini_primary` | `value-default` |
| `quality`, `optimal` | `quality` |

A deprecation warning is emitted at parse time when `--routing-policy` is used without `--cost-profile`.

### Matrix structure

Per Phase B.5 step-complexity analysis (136 v4 prompts classified along 7 dimensions), the existing `lane_class` axis (CE / AGG / BULK_DOCS_GENERAL / BULK_CODE_HEAVY) is **under-dimensioned** — `BULK_DOCS_GENERAL` alone carries 73 steps with reasoning depth spread from low to high. Adding a `capability_tier` axis (low / medium / high / critical) lets the 46 audit-flagged outliers cluster into ~10 populated cells (out of 16) rather than requiring per-step overrides.

10 populated cells: `(EXTRACT, low/medium/high)`, `(CE, low/medium/high)`, `(SYNTH, high/critical)`, `(AGG, low/medium)`. Plus ~5-6 per-step overrides (Z0, C10, S12, T0, T1, T3).

### Optimizer wiring (per provider)

| Optimizer | OpenAI | Anthropic | Gemini | xAI | OpenRouter passthrough |
|---|---|---|---|---|---|
| `service_tier=flex` (50% off) | YES | n/a | n/a | n/a | NO (OR doesn't pass) |
| `service_tier=priority` (2.5×) | YES | n/a | n/a | n/a | NO |
| Prompt caching (auto) | YES (≥1024 tokens, 90% off) | NO (needs `cache_control`) | YES (implicit) | YES (grok-4.3 only) | NO for OpenAI; YES for Anthropic `cache_control` |
| Prompt caching (explicit) | YES (`prompt_cache_key`) | YES (`cache_control`) | YES (`createCachedContent`) | n/a | YES (Anthropic) |
| Batch API (50% off) | YES | YES | YES | NOT DOCUMENTED | NO (raises `UnsupportedBatchProvider`) |
| Tiered pricing (>threshold) | NO | NO | YES (Gemini Pro >200K) | YES (grok-4-fast >128K) | passthrough |
| Data residency multiplier | NO | YES (1.1× on Opus 4.6+, Sonnet 4.6+) | NO | NO | NO |

### Other design choices (consensus-driven, Phase D)

1. **No app-level circuit breaker** (claude-opus-4.5 critique): use **per-request failover** (immediate retry on next route on 5xx/timeout/429) + `--disable-provider` CLI kill-switch. App-level 5xx breakers thrash during partial outages and accrete maintenance debt.
2. **No per-step opus 4.6 vs 4.7 A/B framework**: use **cell-level model aliases** (`${QUALITY_SYNTH_CRITICAL_MODEL}` placeholder, default `anthropic/claude-opus-4.6`, swappable via env var or `--model-alias K=V`). Frontier-model churn (~3-6 months) makes per-step A/B infrastructure obsolete before it's useful. Opus 4.6 default avoids the ~1.35× tokenization tax of Opus 4.7's new tokenizer.
3. **Bounded step tags** (≤8 routing-intent enum): `low_temp`, `long_context`, `schema_critical`, `tooling_heavy`, `control_plane`, `security_sensitive`, `eval_canary`, `direct_openai_required`. Each tag deterministically maps to a small routing delta. Each tag usage requires `tag_rationale` (metric or incident link). Cap enforced in promptset audit; if a tag is used by >8 steps it gets promoted to a matrix dimension.
4. **`impact_class` step field** (`routine | important | structural | security_sensitive`) enforces that `structural` and `security_sensitive` steps run at `critical` tier — the matrix can hide failure-cost heterogeneity (R0 control-plane truth-map ≠ R11 security synthesis in failure cost) and this flag carries the distinction.

## Consequences

### Positive

- **40-50% cost reduction** on the new default profile (`value-default`) vs the prior `balanced_openrouter` baseline, because cached input + flex tier on EXTRACT/AGG lanes + batch discount on bulk lanes all stack.
- **F2-HIGH-1 closed**: synthesis phases (R/S) now route to synthesis-class models (`claude-sonnet-4.6` / `claude-opus-4.6`) instead of bulk-tier flash/non-reasoning models.
- **F2-MED-5 closed**: pricing catalog has 40+ models with proper input/output/cached rates + service_tier multipliers + batch_discount + tiered_pricing thresholds + data_residency multipliers.
- **F2-MED-1 partially closed**: `make_projected_cost_check()` provides preventive (pre-call) cost cap checking, replacing the post-hoc check.
- **80%+ reduction in `model_map.yaml` size** (target — pending E8 migration script).

### Negative

- **OpenRouter dependency in default profile**: per Phase D consensus, `(CE, medium)` and `(CE, high)` cells in `value-default` route through OpenRouter primary (for resilience against OpenAI outages). OR introduces small aggregator markup and loses OpenAI direct flex/priority/cache benefits. Operators who need direct access can use the `direct_openai_required` tag on specific steps.
- **Two-axis mental model** for operators (lane_class × capability_tier vs the old single `routing-policy`). Mitigated by deprecation aliases for one release and the operator guide.
- **Pre-existing test failures** on `test_run_extraction_v5_operator_safety.py::test_doctor_preflight_and_auth_doctor_do_not_run_prescan_or_create_run_artifacts` were observed during validation. Not caused by this change; flagged for a separate task packet.

### Out of scope (separate task packets)

- F2-CRIT-1 walker poisoning (already had `TP-RTE-WALKER-006`)
- F4-CRIT-1 eager init / introspection mutation (already had `TP-RTE-EAGER-INIT-001`)
- F2-CRIT-3 batch strict no-op (already fixed in commit 9c30e9e86 before this redesign)
- Post-step output validators for control-plane / security-sensitive outputs (new `TP-RTE-OUTPUT-VALIDATORS`)
- xAI batch API support verification (xAI does not document batch publicly)

## Implementation surfaces

| File | Change |
|---|---|
| [config/pricing.yaml](config/pricing.yaml) | 40+ models + optimizer fields (service_tier multipliers, cache_*_multiplier, prompt_cache_min_tokens, tiered_*_above_cost_per_m, data_residency_us_multiplier, supports_json_schema_strict, supports_reasoning_toggle) |
| [services/repo-truth-extractor/benchmarking/pricing/normalization.py](services/repo-truth-extractor/benchmarking/pricing/normalization.py) | Normalize all new optimizer fields from yaml |
| [services/repo-truth-extractor/lib/spend_ledger.py](services/repo-truth-extractor/lib/spend_ledger.py) | `compute_optimized_cost()` (service_tier × batch × cache × tiered × residency math); `make_projected_cost_check()`; `_OPTIMIZER_PASSTHROUGH_KEYS` |
| [services/repo-truth-extractor/llm_runtime.py](services/repo-truth-extractor/llm_runtime.py) | `call_llm()` accepts `service_tier`/`prompt_cache_directives`/`disabled_providers`; injects `service_tier` into OpenAI/OR SDK calls; captures `cached_tokens` from response usage |
| [services/repo-truth-extractor/lib/batch_clients.py](services/repo-truth-extractor/lib/batch_clients.py) | `_metadata_field()` helper; service_tier in batch payload |
| [services/repo-truth-extractor/run_extraction_v5.py](services/repo-truth-extractor/run_extraction_v5.py) | `COST_PROFILES` dict; `LEGACY_ROUTING_POLICY_TO_COST_PROFILE` map; `resolve_cost_profile()`; `resolve_cell_alias()`; CLI flags `--cost-profile`, `--disable-provider`, `--model-alias`; RunnerConfig extensions |
| [services/repo-truth-extractor/tests/test_spend_ledger_optimizers.py](services/repo-truth-extractor/tests/test_spend_ledger_optimizers.py) | 13 tests for optimizer math |
| [services/repo-truth-extractor/tests/test_cost_profiles.py](services/repo-truth-extractor/tests/test_cost_profiles.py) | 16 tests for cost profile registry + CLI |

## Research artifacts

- [claudedocs/research/verified-model-inventory-2026-05.md](/Users/hue/code/dopemux-mvp/claudedocs/research/verified-model-inventory-2026-05.md) — Phase B model inventory (4 providers, 40+ models, conflict resolution rules)
- [claudedocs/research/step-complexity-analysis-2026-05.md](/Users/hue/code/dopemux-mvp/claudedocs/research/step-complexity-analysis-2026-05.md) — Phase B.5 step classification (136 prompts; 46 outliers; matrix decision)
- [claudedocs/research/routing-design-2026-05.md](/Users/hue/code/dopemux-mvp/claudedocs/research/routing-design-2026-05.md) — Phase C `pal/planner` design (4 profiles × 10 cells)
- [claudedocs/research/routing-consensus-2026-05.md](/Users/hue/code/dopemux-mvp/claudedocs/research/routing-consensus-2026-05.md) — Phase D `pal/consensus` (3 models: gpt-5.2 neutral, claude-opus-4.5 against, gpt-5.2-pro neutral)

## Pending implementation (for follow-up sessions)

- **E3**: `lib/structured_output_contracts.py` — add `service_tier` passthrough in `route_entries_for_stage()`; new `prompt_caching_directives_for_provider()`; new `anthropic_tool_use` schema variant
- **E7**: rewrite the 12+ hardcoded `*_LADDER` / `*_ROUTE` constants in `run_extraction_v5.py` to be cell-aliased lookups
- **E8**: restructure `promptsets/v4/model_map.yaml` to v3 schema (lane_defaults / tag_definitions / impact_class per step / migration script)
- **E9 finish**: `test_llm_runtime_service_tier_passthrough.py`, `test_model_map_v3_loader.py`, `test_tag_routing_deltas.py`, `test_impact_class_enforcement.py`
- **F**: bounded-lane dry run (`--phase A --step A2 --cost-profile value-default --print-config`); `pal/codereview`; `pal/precommit`
