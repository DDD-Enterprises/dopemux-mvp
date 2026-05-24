# Verified Provider Model Inventory — May 2026

**Source:** Phase A research (WebSearch + WebFetch against provider docs) + PAL `listmodels` + RTE `model_map.yaml` + RTE `config/pricing.yaml`.
**Date verified:** 2026-05-23.
**Conflict resolution rule:** provider's own pricing/docs page is authoritative. PAL catalog is authoritative for what's callable through the PAL MCP. OpenRouter catalog is authoritative for OR-routed IDs and any markup. Existing RTE strings are documented as aliases, not canonical.

> All prices are USD per 1M tokens unless noted otherwise.
> "Cached" = price for a cache-hit / cached input read.
> Service tier multipliers stack with batch and cache pricing where applicable.

---

## OpenAI (direct API)

Source: [openai.com/api/pricing](https://openai.com/api/pricing/), [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing).

| Model ID | Input | Cached | Output | Context | Strict JSON | Batch | Flex | Priority | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `gpt-5.5` | $5.00 | $0.50 | $30.00 | 1,050,000 | ✅ | ✅ 50% | ✅ 50% | ✅ 2.5× | NEW (May 2026). 128K max output. Default cache retention 24h. |
| `gpt-5.5-pro` | $30.00 | — | $180.00 | 1,050,000 | ✅ | ✅ 50% | ✅ 2.5× | ✅ | Most capable reasoning. |
| `gpt-5.4` | $2.50 | $0.25 | $15.00 | 400,000 | ✅ | ✅ 50% | ✅ 50% | ✅ 2.5× | Stable mid-tier flagship. |
| `gpt-5.4-mini` | $0.75 | $0.075 | $4.50 | 400,000 | ✅ | ✅ 50% | ✅ 50% | ✅ 2.5× | Best cost/perf for general work. |
| `gpt-5.4-nano` | $0.20 | $0.02 | $1.25 | 400,000 | ✅ | ✅ 50% | ✅ 50% | — | Cheapest. Bulk classification. |
| `gpt-5.4-pro` | $30.00 | — | $180.00 | 400,000 | ✅ | ✅ 50% | ✅ 2.5× | ✅ | Equivalent to 5.5-pro on the 5.4 family. |
| `gpt-5.3-codex` | $1.75 | $0.175 | $14.00 | 400,000 | ✅ | ✅ 50% | ✅ 50% | ✅ | Code-specialized. RTE current primary CE model. |
| `gpt-5.2` | $2.50 | $0.25 | $15.00 | 400,000 | ✅ | ✅ 50% | ✅ 50% | ✅ 2.5× | Mid-tier. PAL-available. |
| `gpt-5.1-codex` | ~$2.00 | ~$0.20 | ~$12.00 | 400,000 | ✅ | ✅ 50% | ✅ 50% | ✅ | Code-specialized older. PAL alias `codex-5.1`. |
| `gpt-5.1-codex-mini` | ~$0.50 | ~$0.05 | ~$3.00 | 400,000 | ✅ | ✅ 50% | ✅ 50% | — | Cost-efficient codex. |
| `gpt-5-mini` | $0.15 | $0.075 | $0.60 | 400,000 | ✅ | ✅ 50% | ✅ 50% | ✅ | Cheap general purpose. |
| `gpt-5-nano` | $0.05 | $0.025 | $0.20 | 400,000 | ✅ | ✅ 50% | ✅ 50% | — | Cheapest. Summarization/classification. |
| `o3-pro` | (see o-series pricing) | — | — | 200,000 | ✅ | — | ✅ 50% | ✅ | Reasoning premium. |
| `o3` | — | — | — | 200,000 | ✅ | — | ✅ 50% | ✅ | Reasoning standard. |
| `o3-mini` | — | — | — | 200,000 | ✅ | — | ✅ 50% | — | Reasoning fast. |
| `o4-mini` | — | — | — | 200,000 | ✅ | — | ✅ 50% | ✅ | Latest fast reasoning. |

**Service tier mechanics:**
- `service_tier` parameter values: `auto` (default) | `flex` | `priority` | `default`
- `flex`: 50% discount, async ~24h SLA, equivalent to batch pricing but per-request. Available for `o3`, `o4-mini`, `gpt-5.x` family.
- `priority`: 2.5× standard rate, faster + more consistent latency. Available for `gpt-4`, `gpt-5`, `gpt-5-mini`, `o3`, `o4-mini`, `gpt-5.4`, `gpt-5.5`.
- Cache discounts apply on top of any tier.
- Source: [platform.openai.com/docs/guides/flex-processing](https://platform.openai.com/docs/guides/flex-processing), [platform.openai.com/docs/guides/priority-processing](https://platform.openai.com/docs/guides/priority-processing).

**Structured outputs:** `response_format={"type":"json_schema","json_schema":{"strict":true,"schema":{...}}}` is the canonical strict mode. Defaults to `strict=true` on gpt-5.x.

**Prompt caching:** Automatic for prompts ≥1024 tokens. 90% discount on cached reads (10% of input price). `prompt_cache_key` parameter exists for explicit cache scoping. Default retention: 24h for gpt-5.5+.

**Batch API:** 50% discount. Async 24h. Same correctness, no SLA on individual requests.

---

## Anthropic Claude (direct API)

Source: [docs.anthropic.com/en/docs/about-claude/pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) (redirects to `platform.claude.com`).

| Model ID | Input | 5m Write | 1h Write | Cache Read | Output | Context | Batch | Notes |
|---|---|---|---|---|---|---|---|---|
| `claude-opus-4-7` | $5 | $6.25 | $10 | $0.50 | $25 | 1M | ✅ 50% ($2.50/$12.50) | NEW. Uses new tokenizer (~35% more tokens/text). |
| `claude-opus-4-6` | $5 | $6.25 | $10 | $0.50 | $25 | 1M | ✅ 50% | Stable Opus 4 generation, 1M context standard. |
| `claude-opus-4-5` | $5 | $6.25 | $10 | $0.50 | $25 | 200K | ✅ 50% | Same price as 4.6/4.7. PAL/OR catalog. |
| `claude-opus-4-1` | $15 | $18.75 | $30 | $1.50 | $75 | 200K | ✅ 50% ($7.50/$37.50) | OLD. 3× more expensive than 4.5+. |
| `claude-sonnet-4-6` | $3 | $3.75 | $6 | $0.30 | $15 | 1M | ✅ 50% ($1.50/$7.50) | Latest Sonnet. Same price as 4.5. |
| `claude-sonnet-4-5` | $3 | $3.75 | $6 | $0.30 | $15 | 200K | ✅ 50% | Stable. |
| `claude-haiku-4-5` | $1 | $1.25 | $2 | $0.10 | $5 | 200K | ✅ 50% ($0.50/$2.50) | Cheapest. Up to 90% savings with caching. |
| `claude-haiku-3-5` | $0.80 | $1 | $1.60 | $0.08 | $4 | 200K | ✅ 50% | Retired (Bedrock/Vertex only). |

**Prompt caching:** `cache_control` markers placed on individual content blocks for fine-grained control, or `cache_control` at request top level for automatic management. Multipliers:
- 5-minute cache write: **1.25×** base input
- 1-hour cache write: **2×** base input
- Cache read (hit): **0.1×** base input (90% discount)
- Stacks with batch + data residency multipliers.

**Structured outputs:** Tool use mode with `tool_choice` is the canonical structured-output mechanism (no native `response_format` strict mode). Tool use overhead: 313-346 system prompt tokens.

**Batch API:** 50% discount across input + output. Async 24h.

**Fast mode (beta, opt-in):** Opus 4.6 / 4.7 only. 6× standard rates ($30/$150). Stacks with caching. NOT available with batch.

**Inference geography:** `inference_geo="us"` adds 1.1× multiplier on Opus 4.6+ and Sonnet 4.6+. Default global = standard.

---

## Google Gemini (direct API)

Source: [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing).

| Model ID | Input ≤200K | Input >200K | Output ≤200K | Output >200K | Cached | Context | Batch | Notes |
|---|---|---|---|---|---|---|---|---|
| `gemini-3.5-flash` | $1.50 | — | $9.00 | — | $0.15 | 1M | ✅ 50% | NEWEST flash. $1/hr cache storage. |
| `gemini-3.1-pro-preview` | $2.00 | $4.00 | $12.00 | $18.00 | $0.20 / $0.40 | 1M | ✅ 50% | Tier pricing. $4.50/hr cache storage. |
| `gemini-3.1-flash-lite` | $0.25 | — | $1.50 | — | $0.025 | 1M | ✅ 50% | Cheap, fast. Audio +$0.50. $1/hr cache storage. |
| `gemini-2.5-pro` | $1.25 | $2.50 | $10.00 | $15.00 | (10% of input) | 1M | ✅ 50% | Stable previous-gen pro. |
| `gemini-2.5-flash` | $0.30 | — | $2.50 | — | (10% of input) | 1M | ✅ 50% | Text/media; audio $1. |
| `gemini-2.5-flash-lite` | $0.10 | — | $0.40 | — | (10% of input) | 1M | ✅ 50% | Cheapest. Audio $0.30. |
| `gemini-2.0-flash` | $0.10 | — | $0.40 | — | — | 1M | ✅ 50% | DEPRECATED — shutdown June 1, 2026. |

**Notes:**
- Gemini 3 GA pricing kicks in July 1, 2026; current 3.x pricing is preview-tier.
- `gemini-3-flash-preview` (the RTE-config string) appears to map to `gemini-3-flash` or the newer `gemini-3.5-flash`; needs explicit alias mapping.
- `gemini-3.1-pro-preview` is verified at $2/$12 ≤200K, $4/$18 >200K.

**Context caching:** Cached tokens billed at ~10% of input price (varies by model: $0.025 for flash-lite, $0.15 for flash, $0.20 for pro ≤200K). Storage billed hourly ($1/hr for flash, $4.50/hr for pro). Implicit caching available for 2.5+ models — no explicit cache_control needed.

**Structured outputs:** `responseSchema` + `responseMimeType: "application/json"`. Strict schema adherence supported. No extra charge for `responseSchema`.

**Batch API:** 50% discount across all models. Cache hits within batch are priced same as non-batch.

---

## xAI Grok (direct API)

Source: [docs.x.ai/developers/models](https://docs.x.ai/developers/models), [x.ai/news/grok-4-1-fast](https://x.ai/news/grok-4-1-fast) (search results — page blocked WebFetch).

| Model ID | Input | Cached | Output | Context | Reasoning | Structured | Notes |
|---|---|---|---|---|---|---|---|
| `grok-4.3` | $1.25 | $0.20 | $2.50 | 1M | ✅ (none/low/med/high) | ✅ | NEWEST flagship. Function calling. |
| `grok-4.20-0309-reasoning` | $1.25 | — | $2.50 | 1M | ✅ | ✅ | Beta variant. RTE-used. |
| `grok-4.20-0309-non-reasoning` | $1.25 | — | $2.50 | 1M | (off) | ✅ | RTE-used. |
| `grok-4.20-multi-agent-0309` | $1.25 | — | $2.50 | 1M | ✅ | ✅ | Multi-agent variant. |
| `grok-4-fast` | $0.20 | — | $0.50 | 2M | (off) | ✅ | DEPRECATED path. Rates 2× over 128K context. |
| `grok-4-1-fast-reasoning` | $1.25 | — | $2.50 | 2M | ✅ | ✅ | Reasoning fast. RTE-used (`grok-4-1-fast-non-reasoning` exists in RTE strings — verify name). |
| `grok-code-fast-1` | $0.10 | — | $0.40 | — | (off) | ✅ | Code-specialized. RTE-used. |
| `grok-build-0.1` | $1.00 | — | $2.00 | 256K | — | — | Build agent variant. |

**Retirements (May 15, 2026):** Several earlier models retired; requests to retired slugs redirect to `grok-4.3`. The exact list isn't in our research; mark current RTE strings for verification.

**Service tier:** Not documented. xAI does not appear to offer a flex/priority tier equivalent.

**Batch API:** Not documented for xAI as of May 2026. RTE's `XAIBatchClient` extends OpenAIBatchClient with `https://api.x.ai/v1` base URL — works for sync but batch endpoint may not exist (see audit F2-CRIT-1 family).

**Prompt caching:** `grok-4.3` lists $0.20/M cached input (~16% of input). Mechanism not specified — likely automatic.

**Structured outputs:** JSON schema supported with caveats. Schema variant `xai_relaxed` in RTE strips `allOf, minLength, maxLength, minItems, maxItems`.

---

## OpenRouter (aggregator passthrough)

OpenRouter exposes models from many providers via a unified OpenAI-compat API. Pricing is **per-route**; some routes have a markup, others match the provider's direct rate. The RTE OR-routed models we use are:

| OR Model ID | Underlying | Input | Output | Notes |
|---|---|---|---|---|
| `openai/gpt-5.4` | OpenAI gpt-5.4 | $2.50 | $15.00 | Direct rate. No batch/flex via OR (OR doesn't pass batch). |
| `openai/gpt-5.3-codex` | OpenAI gpt-5.3-codex | $1.75 | $14.00 | Direct rate. |
| `openai/gpt-5-mini` | OpenAI gpt-5-mini | $0.15 | $0.60 | Direct rate. |
| `openai/gpt-5.1-codex-mini` | OpenAI codex-mini | ~$0.50 | ~$3.00 | Aggregator-priced. |
| `openai/gpt-5.4-mini` | OpenAI gpt-5.4-mini | $0.75 | $4.50 | Direct rate. |
| `anthropic/claude-opus-4.5` | Anthropic Opus 4.5 | $5.00 | $25.00 | Direct rate. |
| `anthropic/claude-sonnet-4.5` | Anthropic Sonnet 4.5 | $3.00 | $15.00 | Direct rate. |
| `anthropic/claude-haiku-4.5` | Anthropic Haiku 4.5 | $1.00 | $5.00 | Direct rate. |
| `x-ai/grok-4.1-fast` | xAI Grok 4.1 Fast | $0.20 | $0.50 | OR-priced. RTE catalog confirms. |
| `google/gemini-3-pro-preview` | Google Gemini 3 Pro | — | — | Available; pricing per OR page. |

**OpenRouter caveats:**
- OpenRouter does NOT support OpenAI batch API (RTE `OpenRouterBatchClient` raises `UnsupportedBatchProvider`).
- OpenRouter does NOT pass through OpenAI `service_tier` (flex/priority).
- OpenRouter DOES pass through Anthropic `cache_control` markers.
- Schema adaptation: RTE's `provider_schema_variant` returns `xai_relaxed` for `x-ai/*`, `gemini_relaxed` for `google/*` or `gemini*`, `canonical` for everything else.

---

## RTE → Canonical name reconciliation

| RTE string (current) | Canonical | Status | Action |
|---|---|---|---|
| `openai/gpt-5.3-codex` | `gpt-5.3-codex` | ✅ valid | keep |
| `openai/gpt-5.4` | `gpt-5.4` | ✅ valid | keep |
| `openai/gpt-5-mini` | `gpt-5-mini` | ✅ valid | keep |
| `openai/gpt-5.1-codex-mini` | `gpt-5.1-codex-mini` | ✅ valid | keep |
| `anthropic/claude-opus-4-6` | `claude-opus-4-6` | ✅ valid | keep, but `claude-opus-4-5` is cheaper at same headline price; consider whether routing should prefer 4.5 vs 4.6/4.7 |
| `anthropic/claude-opus-4-5` | NEW addition | ✅ valid | add |
| `anthropic/claude-sonnet-4-6` | NEW addition | ✅ valid | add (mid-tier) |
| `anthropic/claude-haiku-4-5` | NEW addition | ✅ valid | add (cheap tier) |
| `gemini-3-flash-preview` | LIKELY `gemini-3-flash` or `gemini-3.5-flash` | ⚠️ name uncertain | verify against Vertex/AI Studio direct lookup; alias mapping required |
| `gemini-3.1-pro-preview` | `gemini-3.1-pro-preview` | ✅ valid (preview) | keep |
| `xai/grok-code-fast-1` | `grok-code-fast-1` | ✅ valid | keep |
| `xai/grok-4.20-beta-0309-reasoning` | `grok-4.20-0309-reasoning` | ⚠️ "beta-" prefix in RTE not on docs page | verify; likely alias to non-beta-prefixed |
| `xai/grok-4.20-beta-0309-non-reasoning` | `grok-4.20-0309-non-reasoning` | ⚠️ same | verify |
| `xai/grok-4-1-fast-non-reasoning` | LIKELY `grok-4-1-fast` (non-reasoning variant) | ⚠️ | xAI docs show `grok-4-1-fast-reasoning`; non-reasoning variant exists in RTE but not directly in xAI docs page — verify in next phase or treat as alias |
| `xai/grok-4.20-beta` | LIKELY `grok-4.20` (base) | ⚠️ | verify; possibly retired May 15 2026 |

**Recommendation for Phase E:** Build a `_canonicalize_model_id()` helper in `lib/structured_output_contracts.py` that maps RTE legacy strings to canonical IDs and emits a deprecation warning when an alias is hit. This keeps existing config working while telling operators to migrate.

---

## Pricing catalog gap analysis vs current `config/pricing.yaml`

Current catalog (15 entries) is **partially populated** with confirmed pricing for OpenAI gpt-5.4 family, gpt-5.3-codex, Anthropic Claude 3.5 era models, Gemini 1.5, Gemini 3.1 pro preview. Missing or stale:

**Missing entirely (need to add for Phase E1):**
- `openai/gpt-5.5`, `openai/gpt-5.5-pro`
- `openai/gpt-5.4-pro`, `openai/gpt-5.4-nano`
- `openai/gpt-5-mini`, `openai/gpt-5-nano`
- `openai/gpt-5.2`, `openai/gpt-5.1-codex`, `openai/gpt-5.1-codex-mini`
- `openai/o3-pro`, `openai/o3`, `openai/o3-mini`, `openai/o4-mini`
- `anthropic/claude-opus-4-7`, `claude-opus-4-6`, `claude-opus-4-5`
- `anthropic/claude-sonnet-4-6`, `claude-sonnet-4-5`
- `anthropic/claude-haiku-4-5`
- `gemini/gemini-3.5-flash`, `gemini-3.1-flash-lite`
- `gemini/gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`
- `xai/grok-4.3`, `grok-4-fast`, `grok-4-1-fast-reasoning`, `grok-build-0.1`
- All OR aggregator routes for the above models

**Stale (need refresh):**
- `xai/grok-4.20-beta-0309-reasoning`: current catalog shows $3/$15 (STALE_NEEDS_REFRESH). Verified: $1.25/$2.50. Confidence LOW → HIGH.
- `xai/grok-code-fast-1`: STALE_NEEDS_REFRESH. Verified: $0.10/$0.40. Confidence LOW → MEDIUM (xAI doc doesn't explicitly confirm this exact ID anymore).

**Schema extensions needed:**
- Add `service_tier_multipliers: {flex: 0.5, priority: 2.5, default: 1.0}` per OpenAI model
- Add `prompt_cache_min_tokens` (1024 for OpenAI; varies for others)
- Add `cache_write_5m_multiplier: 1.25`, `cache_write_1h_multiplier: 2.0` for Anthropic models
- Add `cache_read_multiplier` (0.1 for Anthropic, 0.1 for OpenAI cached_input, ~0.1 for Gemini cached)
- Add `tiered_pricing: {threshold_tokens: 200000, input_above: ..., output_above: ...}` for Gemini Pro >200K
- Add `data_residency_multiplier: 1.1` for Anthropic Sonnet 4.6+/Opus 4.6+ when `inference_geo="us"`

---

## Decision input for Phase C (routing design)

**Role → recommended canonical model map (input for `pal/planner`):**

| Role | Best fit canonical | Tier 2 fallback | Tier 3 fallback |
|---|---|---|---|
| `frontier-strict-code` (CE code) | `openai/gpt-5.3-codex` (direct) | `openrouter/openai/gpt-5.3-codex` | `openrouter/openai/gpt-5.4` |
| `frontier-strict-synthesis` (R/S CE) | `anthropic/claude-opus-4-7` (direct) | `openai/gpt-5.5` (direct) | `openrouter/anthropic/claude-opus-4-5` |
| `mid-strict-code` (CE code lighter) | `openai/gpt-5.4-mini` (direct) | `openai/gpt-5.1-codex-mini` | `openrouter/openai/gpt-5.4-mini` |
| `mid-strict-synthesis` | `anthropic/claude-sonnet-4-6` (direct) | `openai/gpt-5.4` | — |
| `bulk-fast-strict` (CE bulk extract) | `openai/gpt-5-mini` (direct) | `gemini-3.5-flash` | `gemini-3.1-flash-lite` |
| `bulk-fast-relaxed` (BULK_DOCS_GENERAL) | `gemini-3.5-flash` (direct) | `xai/grok-4-fast` | `xai/grok-code-fast-1` |
| `bulk-fast-code-heavy` (BULK_CODE_HEAVY) | `xai/grok-code-fast-1` | `xai/grok-4.3` non-reasoning | `openai/gpt-5.4-mini` |
| `cheap-classification` | `gpt-5-nano` (direct) | `gpt-5.4-nano` | `gemini-2.5-flash-lite` |

**Cost-profile to role mapping (preliminary, refine in Phase C):**

- **`economy`**: every role → cheapest tier. Flex on. Cached input on. Batch on if supported.
- **`value-default`**: code/synthesis → mid-tier; bulk → cheap tier. Flex on for BULK lanes. Cached input on. Batch on for BULK.
- **`quality`**: code/synthesis → frontier tier with reasoning. Priority tier on. Cached input on. No batch (latency-sensitive).
- **`experimental`**: bleed-edge models (gpt-5.5-pro, claude-opus-4-7, gemini-3.1-pro-preview). Standard tier. Cached on.

---

## UNKNOWNs to close in Phase C / E

1. **Exact pricing for some PAL-only models** (`gpt-5.2`, `gpt-5.1-codex`, `o3`, `o3-pro`, `o3-mini`, `o4-mini`): not in current OpenAI pricing page snapshot. Need to fetch [openai.com/api/pricing](https://openai.com/api/pricing/) more carefully or accept `PRICED_WITH_CAVEAT` status.
2. **`gemini-3-flash-preview` ↔ canonical mapping**: Gemini docs show `gemini-3.5-flash` and `gemini-3.1-flash-lite` but not `gemini-3-flash-preview` directly. Either RTE config is using a now-retired preview ID or it maps to one of the current names. Phase E1 must verify against the Google Vertex pricing page.
3. **xAI `grok-4.20-beta-*` retirement**: The May 15 2026 xAI retirement may have removed these. Need to verify whether `grok-4.20-0309-*` is still callable or has been auto-redirected to `grok-4.3`. Phase E7 must confirm before keeping them in ladders.
4. **xAI batch API support**: Not documented in xAI's public pricing. The RTE `XAIBatchClient` exists but may be ineffective at the API level. Recommend `enable_batch_when_supported = false` for xAI provider until verified.
5. **OpenRouter batch passthrough**: Confirmed unsupported by RTE design (`OpenRouterBatchClient` raises). OR users can use only sync mode + flex pricing fallback.

---

**Status:** Phase B complete. This document supersedes the audit's pricing observations (F2-MED-5) — the catalog is partially populated, not flat-baseline. The bigger fix is filling missing entries + adding service_tier / cache_write multipliers / tiered_pricing fields.

**Next:** Phase B.5 step-complexity analysis (running in background as Explore agent). When that completes + this inventory, Phase C (pal/planner) gets the full input it needs.
