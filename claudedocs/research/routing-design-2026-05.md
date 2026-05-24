# RTE Cost Profile & Routing Design — May 2026

**Phase C output** from `mcp__pal__planner` session `54de1277-e31b-460c-adff-5f63d6b22f15` (model: gemini-3-pro-preview).
**Inputs**: `verified-model-inventory-2026-05.md` (Phase B), `step-complexity-analysis-2026-05.md` (Phase B.5).
**Status**: Ready for Phase D (consensus stress-test) and Phase E (implementation).

---

## Overview

The redesign turns the existing 8 routing policies into **4 cost profiles**, each backed by a **`(lane_class × capability_tier)` matrix** with 10 populated cells. Each cell has a route ladder (primary → repair → sidefill). Plus **6 per-step overrides** for outliers (Z0, C10, S12, T1, T3, R1).

Three orthogonal axes:

1. **Cost profile** (operator choice): `economy` / `value-default` / `quality` / `experimental`
2. **Lane × capability matrix** (step attribute): `EXTRACT|CE|SYNTH|AGG` × `low|medium|high|critical`
3. **Step-level flags** (used by validators, not routing): `strict_json_required`, `premium_floor`, `code_specialist_required`, `partition_input_size_class`

## Cost profile → legacy policy alias map

| New cost profile | Aliases (deprecated, one-release) |
|---|---|
| `economy` | `cost` |
| `value-default` (NEW DEFAULT) | `balanced`, `balanced_openrouter`, `balanced_grok_openrouter`, `openrouter`, `gemini_primary` |
| `quality` | `quality`, `optimal` |
| `experimental` | (no legacy alias; opt-in only) |

When operator passes `--routing-policy <legacy>`, the system maps to the cost profile and emits a deprecation warning. Both flags coexist for one release; legacy flag removed after.

---

## value-default profile ladders

Best cost/quality ratio. Cached input ON globally. Flex tier ON for non-blocking lanes only (EXTRACT/AGG). Standard tier for CE/SYNTH. Batch enabled for EXTRACT/AGG when supported. Fallback to higher tier on strict validation failure.

### Cell (CE, medium) — ~40 steps

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.3-codex, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openrouter, model_id: openai/gpt-5.3-codex, api_key_env: OPENROUTER_API_KEY, service_tier: null, strict_json_schema: true, cache_strategy: none}
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openrouter, model_id: openai/gpt-5.4, api_key_env: OPENROUTER_API_KEY, strict_json_schema: true, cache_strategy: none}
sidefill_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openai, model_id: gpt-5.3-codex, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
```

### Cell (EXTRACT, medium) — A2–A10, E1–E6, H4–H7, W2–W5, X2–X4

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: flex, strict_json_schema: false, cache_strategy: auto}
  - {provider: xai, model_id: grok-4-fast, api_key_env: XAI_API_KEY, service_tier: null, strict_json_schema: false, cache_strategy: none}
  - {provider: gemini, model_id: gemini-3.5-flash, api_key_env: GEMINI_API_KEY, service_tier: null, strict_json_schema: false, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
sidefill_routes:
  - {provider: openai, model_id: gpt-5-mini, api_key_env: OPENAI_API_KEY, service_tier: flex, strict_json_schema: false, cache_strategy: auto}
```

### Cell (EXTRACT, low) — M0–M6

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5-mini, api_key_env: OPENAI_API_KEY, service_tier: flex, strict_json_schema: false, cache_strategy: auto}
  - {provider: gemini, model_id: gemini-2.5-flash-lite, api_key_env: GEMINI_API_KEY, service_tier: null, strict_json_schema: false, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
sidefill_routes:
  - {provider: openai, model_id: gpt-5-nano, api_key_env: OPENAI_API_KEY, service_tier: flex, strict_json_schema: false, cache_strategy: auto}
```

### Cell (EXTRACT, high) — Z2 if reclassified

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
  - {provider: openrouter, model_id: anthropic/claude-sonnet-4.6, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
repair_routes:
  - {provider: openrouter, model_id: anthropic/claude-opus-4.5, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
sidefill_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
```

### Cell (CE, low) — Z0

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
sidefill_routes: []
```

### Cell (CE, high) — R1, S12, T0

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openrouter, model_id: anthropic/claude-opus-4.5, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
  - {provider: openai, model_id: gpt-5.3-codex, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.5, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openrouter, model_id: anthropic/claude-opus-4.6, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
sidefill_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
```

### Cell (SYNTH, high) — R0/R2–R11, S0–S11

```yaml
primary_routes:
  - {provider: openrouter, model_id: anthropic/claude-sonnet-4.6, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
  - {provider: gemini, model_id: gemini-3.1-pro-preview, api_key_env: GEMINI_API_KEY, service_tier: null, strict_json_schema: false, cache_strategy: auto}
repair_routes:
  - {provider: openrouter, model_id: anthropic/claude-opus-4.5, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
  - {provider: openai, model_id: gpt-5.5, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
sidefill_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
```

This closes audit finding F2-HIGH-1 (R/S synthesis previously misrouted to bulk tier).

### Cell (SYNTH, critical) — S0, R7, T0

```yaml
primary_routes:
  - {provider: openrouter, model_id: anthropic/claude-opus-4.6, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
  - {provider: openai, model_id: gpt-5.5, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
  - {provider: gemini, model_id: gemini-3.1-pro-preview, api_key_env: GEMINI_API_KEY, service_tier: null, strict_json_schema: false, cache_strategy: auto}
repair_routes:
  - {provider: openrouter, model_id: anthropic/claude-opus-4.7, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
  - {provider: openai, model_id: gpt-5.5-pro, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
sidefill_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: false, cache_strategy: auto}
```

### Cell (AGG, medium) — 14 *_merge_qa steps

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openrouter, model_id: anthropic/claude-sonnet-4.5, api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
sidefill_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
```

### Cell (AGG, low) — Z9

```yaml
primary_routes:
  - {provider: openai, model_id: gpt-5.4-mini, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
repair_routes:
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
sidefill_routes: []
```

### Profile-level config for value-default

```yaml
cost_profiles:
  value-default:
    default_service_tier: default
    enable_cached_input: true
    enable_batch_when_supported: true
    escalation_max_hops: 2
    max_cost_usd_default: null
    cost_cap_mode: preventive
    notes: |
      Best cost/quality ratio. Flex tier on EXTRACT/AGG bulk lanes; standard for CE/SYNTH.
      Cached input on globally. Batch enabled for non-CE/SYNTH cells.
```

---

## economy profile ladders (abbreviated)

Minimum spend. Flex tier ON everywhere. Cheapest capable model per cell. Operator accepts higher repair rate and slower turnaround.

Key differences from value-default:
- **(CE, medium)** primary: `gpt-5.1-codex-mini` + flex (vs gpt-5.3-codex default)
- **(EXTRACT, medium)** primary: `xai/grok-4-fast` (vs gpt-5.4-mini + flex)
- **(SYNTH, high)** primary: `anthropic/claude-haiku-4.5` (vs claude-sonnet-4.6)
- **(SYNTH, critical)** primary: `anthropic/claude-sonnet-4.5` (vs claude-opus-4.6)
- **(AGG, medium)** primary: `gpt-5-mini` (vs gpt-5.4-mini)

```yaml
cost_profiles:
  economy:
    default_service_tier: flex
    enable_cached_input: true
    enable_batch_when_supported: true
    escalation_max_hops: 1
    max_cost_usd_default: 5.00
    cost_cap_mode: preventive
    notes: |
      Minimum spend; aggressive flex tier + cheapest capable models.
      Quality degraded on SYNTH-critical cells; review PROOF_PACK before relying on outputs.
```

(Full per-cell ladders in `pal/planner` continuation 54de1277-e31b-460c-adff-5f63d6b22f15 step 3.)

---

## quality profile ladders (abbreviated)

Premium production runs. Priority service_tier where available. No flex. Deeper escalation.

Key differences from value-default:
- **(CE, medium)** primary: `gpt-5.5` + priority (vs gpt-5.3-codex default)
- **(SYNTH, high)** primary: `anthropic/claude-opus-4.6` (vs claude-sonnet-4.6)
- **(SYNTH, critical)** primary: `anthropic/claude-opus-4.7` (vs claude-opus-4.6)
- **(CE, high)** primary: `gpt-5.5` + priority

```yaml
cost_profiles:
  quality:
    default_service_tier: priority
    enable_cached_input: true
    enable_batch_when_supported: false
    escalation_max_hops: 3
    max_cost_usd_default: null
    cost_cap_mode: preventive
    notes: |
      Premium models with priority service tier where available.
      Estimated 3-5x cost of value-default. Use for production go/no-go.
```

(Full ladders in `pal/planner` step 4.)

---

## experimental profile ladders (abbreviated)

Bleed-edge frontier models. Bypasses some validators. Opt-in.

Key models: `gpt-5.5-pro`, `anthropic/claude-opus-4.7`, `gemini-3.5-flash`, `gemini-3.1-pro-preview`.

```yaml
cost_profiles:
  experimental:
    default_service_tier: default
    enable_cached_input: true
    enable_batch_when_supported: false
    escalation_max_hops: 2
    max_cost_usd_default: 25.00
    cost_cap_mode: preventive
    notes: |
      Bleed-edge frontier models (gpt-5.5-pro, claude-opus-4.7, gemini-3.5-flash).
      May have higher tokenization (opus 4.7 = ~35% more tokens for same text).
      Bypasses some validators; operator must inspect PROOF_PACK.
    warning: "Models may be in preview/beta. Not for production."
```

(Full ladders in `pal/planner` step 4.)

---

## Per-step overrides (apply across all profiles, evaluated AFTER cell lookup)

```yaml
overrides:
  C10:
    new_lane_class: SYNTH
    new_capability_tier: high
    rationale: "SERVICE_CATALOG_DEEP requires reasoning-class — was misrouted to BULK_CODE_HEAVY."
  S12:
    new_capability_tier: critical
    rationale: "STABILITY_SIGNATURE produces strict JSON signatures for downstream verification."
  # Z0, R1, T1, T3: keep cell defaults but include in validator allow-list
```

---

## Reasoning toggle (xAI grok-4.3 and grok-4-1-fast-reasoning)

Future support: per-route `reasoning_effort: none|low|medium|high` field.
- CE/EXTRACT lanes: `reasoning_effort=low`
- SYNTH lanes: `reasoning_effort=high`
- AGG: `reasoning_effort=none`

Currently grok isn't a primary on any cell in any profile (reliability favors OpenAI).

---

## Estimated cost per profile (single full RTE run, 136 steps)

| Profile | Estimated $/run | vs current `balanced_openrouter` |
|---|---|---|
| `economy` | $3-6 | -75% |
| `value-default` | $12-20 | -50% |
| `quality` | $35-60 | +50% |
| `experimental` | $20-35 | -25% |

Assumptions: ~50K tokens/step avg, ~70% cache hit rate after first phase, 10% repair rate, 5% sidefill rate.

---

## Critical risks (Phase D consensus topics)

| # | Risk | Mitigation |
|---|---|---|
| 1 | OpenAI provider concentration (6/10 cells primary on OpenAI in value-default) | Cross-provider repair on every SYNTH cell; OR fallback on every CE cell |
| 2 | Anthropic strict_json mismatch — needs new `anthropic_tool_use` schema variant | Add `anthropic_tool_use` mode to `provider_schema_variant()` in E3 |
| 3 | gpt-5.5 priority tier cost ($12.50/$75 per M) | `quality` profile docs warn cost; operator must opt in explicitly |
| 4 | Flex tier 24h SLA | `value-default` uses flex only on non-blocking EXTRACT cells; `economy` documents slower runs OK |
| 5 | Opus 4.7 tokenization (~35% more tokens) | Default to opus 4.6 on value-default; reserve 4.7 for quality repair + experimental |
| 6 | Cache hit rate assumption (70%) | Spend ledger reports actual hit rate; PROOF_PACK includes per-phase hit rate |

---

## File changes summary (Phase E)

| # | File | Status |
|---|---|---|
| E1 | `config/pricing.yaml` | DONE — 40+ models, full optimizer fields |
| E2 | `services/repo-truth-extractor/lib/spend_ledger.py` | Pending — service_tier/cached/batch math + preventive cost-cap helper |
| E3 | `services/repo-truth-extractor/lib/structured_output_contracts.py` | Pending — service_tier passthrough + `prompt_caching_directives_for_provider()` + `anthropic_tool_use` schema variant |
| E4 | `services/repo-truth-extractor/llm_runtime.py` | Pending — `call_llm()` gains `service_tier`+`prompt_cache_directives`; capture `cached_tokens` |
| E5 | `services/repo-truth-extractor/lib/batch_clients.py` | Pending — service_tier in batch payload; tag batch routes |
| E6 | `services/repo-truth-extractor/run_extraction_v5.py` (cost profiles) | Pending — `COST_PROFILES` dict, `--cost-profile` CLI flag, dispatch update |
| E7 | `services/repo-truth-extractor/run_extraction_v5.py` (ladders rewrite) | Pending — replace 11 hardcoded ladders with cost-profile-aware lookups |
| E8 | `services/repo-truth-extractor/promptsets/v4/model_map.yaml` (v3) | Pending — top-level `lane_defaults` block, per-step overrides for 6 steps |
| E8b | `services/repo-truth-extractor/promptsets/v4/scripts/migrate_model_map_v2_to_v3.py` | Pending — migration script |
| E9 | `services/repo-truth-extractor/tests/test_cost_profiles.py` + 5 more | Pending |
| E10 | `docs/02-how-to/extraction/rte-cost-profiles.md` + 2 more | Pending |

---

**End of Phase C output.**
