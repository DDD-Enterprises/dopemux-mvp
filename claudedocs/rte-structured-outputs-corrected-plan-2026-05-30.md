# Corrected Plan: Strict Structured-Output Attestation for RTE

**Supersedes:** `rte_openrouter_structured_outputs_plan.md` (Antigravity/Gemini draft)
**Author:** Claude (audit + redesign)
**Date:** 2026-05-30
**Baseline:** main HEAD `755bf3846`, RTE at `services/repo-truth-extractor`
**Status:** Plan only — describes implementation, does not execute it. No code edits made.

---

## 0. Why the original plan was rejected

The Antigravity draft proposed (a) blanket-returning `"canonical"` from `provider_schema_variant()` for all OpenRouter routes, (b) adding `strict:true` to the Grok prescan path, and (c) "trusting OpenRouter's compatibility list." It was rejected because:

1. It conflated **schema shaping** (`provider_schema_variant`) with **strict gating** (`strict_capability_reason`). They are separate functions; flipping the variant does not enable strict mode and *does* stop necessary keyword filtering.
2. It was unaware of the existing **two-flag attestation system** (`strict_json_schema` advertised vs `strict_passthrough_verified` empirically confirmed) and the fail-closed gate at `structured_output_contracts.py:223`.
3. Its premise ("OpenRouter natively proxies strict outputs, so just trust it") is contradicted by provider behavior (see §2) and by the fact that **the production v4 map routes zero traffic through OpenRouter** — all strict routes are direct-provider.

This plan keeps the goal (less fragile JSON, more strict routes) but routes it through the machinery RTE already has.

---

## 1. The real unit of work

Not "OpenRouter structured outputs." The unit is **strict-output attestation per `(model, transport)`**. `strict_capability_reason(route, transport)` already takes transport; the map already carries per-route flags. OpenRouter is just *one* transport option, and not the one production uses today.

### Current production routing (v4 `model_map.yaml`, 4437 lines, verified)
| Lane class | Strict req? | Models (direct providers) | Flag state |
|---|---|---|---|
| **CE** (critical extraction) | yes | `openai/gpt-5.3-codex` → `gpt-5.5` (flex) | `verified: true` |
| **AGG** (aggregation) | yes | `openai/gpt-5.5` (flex) | `verified: true` |
| **CE in Phase D** | yes | `gemini-3.1-pro-preview` (primary) → `gpt-5.3-codex`/`gpt-5.5` fallback | gemini `verified: false`, openai `true` |
| **BULK_DOCS_GENERAL** | no | `xai/grok-4.3` (or `gemini-3-flash-preview` in D) | `verified: false` |
| **BULK_CODE_HEAVY** | no | `xai/grok-build-0.1` → `grok-4.3` | `verified: false` |

Providers in map: openai (228 routes), xai (266), gemini (61). **openrouter: 0.**

---

## 2. Research findings (all sourced — see §6)

### 2a. OpenRouter advertises structured outputs broadly (live `/models` API, 2026-05-30)
`GET /api/v1/models?supported_parameters=structured_outputs` returns **234 models**. Every family RTE uses is present, including the exact model IDs:

| Model (OpenRouter id) | ctx | $in /M | $out /M | advertises `structured_outputs` |
|---|---|---|---|---|
| `openai/gpt-5.5` | 1.05M | $5.00 | $30.00 | ✅ |
| `openai/gpt-5.4` | 1.05M | $2.50 | $15.00 | ✅ |
| `openai/gpt-5.3-codex` | 400k | $1.75 | $14.00 | ✅ |
| `openai/gpt-5.4-mini` | 400k | $0.75 | $4.50 | ✅ |
| `anthropic/claude-opus-4.8` | 1M | $5.00 | $25.00 | ✅ |
| `anthropic/claude-sonnet-4.6` | 1M | $3.00 | $15.00 | ✅ |
| `anthropic/claude-haiku-4.5` | 200k | $1.00 | $5.00 | ✅ |
| `google/gemini-3.1-pro-preview` | 1.05M | $2.00 | $12.00 | ✅ |
| `google/gemini-3.5-flash` | 1.05M | $1.50 | $9.00 | ✅ |
| `google/gemini-3-flash-preview` | 1.05M | $0.50 | $3.00 | ✅ |
| `x-ai/grok-4.3` | 1M | $1.25 | $2.50 | ✅ |
| `x-ai/grok-build-0.1` | 256k | $1.00 | $2.00 | ✅ |

### 2b. "Advertised" ≠ "strict passthrough verified" — the gap is real and provider-specific
- **xAI direct** (docs.x.ai): Grok accepts `response_format: {type: json_schema, strict: true}`, **but** the docs state outputs "**are not guaranteed to satisfy these constraints**, so validation is recommended." xAI **does not support `additionalProperties: false`** — OpenAI-style canonical schemas inject it and xAI/Grok **rejects with HTTP 400** (reproduced in the wild: agno #7455). → This is best-effort, not strict. **Directly validates RTE's `xai_relaxed` variant and `verified: false`.**
- **Gemini direct** (ai.google.dev): A Nov-2025 update **added** `anyOf`, `$ref`, and `additionalProperties` support and key-order preservation. **But** "not all features are supported, and the model **ignores unsupported properties**" (silent — a correctness hazard), and it "may reject very large or deeply nested schemas." → Keyword stripping (`gemini_relaxed`) is now **loosenable but not removable**, and needs per-keyword re-verification against the actual extraction schemas.
- **OpenRouter proxy**: `supported_parameters` is a *capability advertisement*. It does not guarantee the underlying provider enforces strict adherence, and it adds proxy variance on top of the provider's own best-effort behavior. Unsupported requests **fail with an error (no silent fallback)** — good for fail-closed, but it means routing must know support ahead of time.

**Conclusion:** the precise gap between "the API accepts `response_format`" and "output is schema-exact without repair" is exactly what RTE's `strict_passthrough_verified` flag encodes. The original plan wanted to delete that gap by fiat; the evidence says it must be *measured*.

### 2c. Is OpenRouter even the right transport? (Mostly no, for strict routes)
Production deliberately uses direct providers for strict routes. For **strict CE/AGG**, OpenRouter adds proxy variance and a second best-effort layer with no upside — keep direct. OpenRouter's legitimate, narrow uses: (i) **fallback diversity** when a direct provider is down, (ii) reaching a model without provisioning a separate API key. Neither is a strict-correctness argument. **Recommendation: do not migrate strict routes to OpenRouter; keep the relaxation logic dormant-but-present.**

---

## 3. The highest-value concrete win (small, direct, no OpenRouter)

The Phase-D CE/AGG lanes (`D0/D1/D4/D5`) run `gemini-3.1-pro-preview` as **strict-required primary** today but with `strict_passthrough_verified: false`, so the gate forces fallback to OpenAI for the strict guarantee. Given Gemini's Nov-2025 keyword broadening (§2b):

> **Re-attest `gemini-3.1-pro-preview` on the direct route against the actual CE/AGG extraction schemas. If it passes, flip `strict_passthrough_verified: true` and relax `gemini_relaxed` to the minimum still required.** This is the concrete payoff — it lets Gemini carry strict CE work directly instead of always deferring to OpenAI.

Grok stays `verified: false` (best-effort + `additionalProperties` rejection) unless a benchmark proves otherwise. That matches the docs.

---

## 4. Implementation (built on existing machinery — do NOT author a new harness)

The verification harness already exists: `benchmarking/campaigns/` (`admissibility`, `route_identity`, `route_separation`, `selection`), `benchmarking/registry/registry_loader.py` (which sets `strict_passthrough_verified=True`), and `benchmarking/cli/benchmark_live_route_readiness_smoke.py` (already contains `route_openrouter_openai_*` IDs). The attestation contract is the `STRICT_ATTESTATION.json` artifact gated by `tests/test_strict_passthrough_attestations.py`.

**Step 1 — Define candidate routes (config only).** In the benchmark registry, register the `(model, transport)` candidates to attest. Priority order: `gemini-3.1-pro-preview` direct (the §3 win); then optionally OpenRouter variants of already-verified OpenAI models for fallback diversity. *No `model_map.yaml` edit yet.*

**Step 2 — Run the live route-readiness campaign.** Use the existing readiness smoke + admissibility/route-separation to drive real calls with the actual CE/AGG extraction schemas. Capture: schema-exact pass rate, repair-cascade invocation rate, 400/keyword-rejection events, and route-identity separation (no cross-talk). This is what decides "best" — research only narrows candidates; the campaign picks the winner.

**Step 3 — Promote only what passed.** For routes meeting the attestation bar, emit/refresh `STRICT_ATTESTATION.json` and flip `strict_passthrough_verified: true` in `model_map.yaml` **per model**. Keep `test_strict_passthrough_attestations.py` green as the gate. Treat `model_map.yaml` and `structured_output_contracts.py` as **contract-sensitive** (canonical-writer review + the attestation test must pass).

**Step 4 — Prescan path (`grok_passes.py`).** Replace the original plan's `strict:true`-on-Grok step. Grok is best-effort and rejects `additionalProperties:false`, so: add **non-strict `response_format: {type:"json_object"}`** (cheap, safe, reduces raw-`json.loads` failures) and keep the repair cascade. Only add `json_schema` here if/when a benchmark attests the specific prescan model+transport.

**Step 5 — Telemetry (keep from original — the one good idea).** In `parse_json_from_response_with_provenance` (`llm_runtime.py:1247`), record when the repair cascade fires on a route that *claimed* strict support. This surfaces models whose advertised support degrades in practice — feeding the next attestation cycle.

**Do not:** edit `provider_schema_variant()` to blanket-`canonical`; add strict to unverified routes; migrate strict CE/AGG to OpenRouter.

---

## 5. Candidate table per lane (gate = advertised strict support; winner = benchmark)

Cost/ctx are OpenRouter list prices (§2a); direct-provider pricing may differ. "Strict reality" reflects §2b. **Final selection is the campaign's job, not this table's.**

| Lane | Incumbent | Strict-capable candidates (meet the gate) | Strict reality / notes |
|---|---|---|---|
| **CE** | `gpt-5.3-codex`→`gpt-5.5` | `gpt-5.3-codex`, `gpt-5.4`, `gpt-5.5`, `claude-sonnet-4.6`, `gemini-3.1-pro-preview` | OpenAI = true-strict (verified). Gemini candidate per §3. Claude advertises but UNVERIFIED in RTE. |
| **AGG** | `gpt-5.5` | `gpt-5.4` (cheaper, same ctx tier), `gpt-5.5`, `claude-sonnet-4.6` | `gpt-5.4` is a plausible cost cut for aggregation — benchmark vs `gpt-5.5`. |
| **BULK_DOCS_GENERAL** | `grok-4.3` / `gemini-3-flash-preview` | (non-strict lane) `grok-4.3`, `gemini-3-flash-preview`, `gemini-3.5-flash` | Cheapest = `gemini-3-flash-preview` ($0.50/$3). Grok best-effort; lane doesn't require strict. |
| **BULK_CODE_HEAVY** | `grok-build-0.1`→`grok-4.3` | (non-strict) `grok-build-0.1`, `grok-4.3` | `grok-build-0.1` cheapest + code-tuned; keep. |

---

## 6. Sources

- OpenRouter — Structured Outputs guide: https://openrouter.ai/docs/guides/features/structured-outputs
- OpenRouter — live models API (queried 2026-05-30): `https://openrouter.ai/api/v1/models?supported_parameters=structured_outputs` (234 models; pricing/ctx per-model)
- OpenRouter — API parameters: https://openrouter.ai/docs/api/reference/parameters
- xAI — Structured Outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- agno #7455 (xAI rejects `additionalProperties:false`): https://github.com/agno-agi/agno/issues/7455
- Google — JSON Schema support announcement: https://blog.google/innovation-and-ai/technology/developers-tools/gemini-api-structured-outputs/
- Gemini structured output docs: https://ai.google.dev/gemini-api/docs/structured-output
- googleapis/python-genai #1815 (`additionalProperties` since Nov 2025): https://github.com/googleapis/python-genai/issues/1815

---

## 7. Validation / uncertainty

- **PASS** — codebase claims (variant logic, gate, attestation flags, zero-OpenRouter-in-v4) verified against `755bf3846`.
- **PASS** — OpenRouter support list + pricing fetched live from the API.
- **NOT_RUN** — no live extraction call made; whether `gemini-3.1-pro-preview`/`grok-4.3` *strictly* hold on RTE's real schemas is exactly what Step 2 must measure. Treat all "strict reality" rows as hypotheses until attested.
- **UNKNOWN** — Anthropic Claude is advertised strict-capable via OpenRouter but is **not in RTE's map at all**; adding it is a separate decision (new API key, new attestation), out of scope here.
- **UNKNOWN** — direct-vs-OpenRouter price deltas for the specific models (only OpenRouter list prices fetched).
