# Dopemux Routing Logic — Design Doc & Spec (v0.1)

> Purpose: Define a provider-agnostic routing layer for Dopemux that defaults to Anthropic’s Claude (subscription-backed) for “cc default”, and intelligently shifts traffic to a programmable fallback hub (via LiteLLM or native adapters) based on limits, context size, task type, cost/latency, and provider health. Debugging transcripts have been intentionally omitted; this is a clean specification.

---

## 1) Goals & Non‑Goals

### Goals

1. **Native‑first**: Use the user’s **Claude subscription** (e.g., Sonnet 4 via Claude Code UI) as the default path for interactive coding/chat, labeled **cc‑default**.
2. **Adaptive fallback**: When subscription **hour limits** or **provider errors** occur, automatically reroute to configured alternates (e.g., DeepSeek V3.1 via OpenRouter) with minimal disruption.
3. **Task‑aware routing**: First‑class routes for **default**, **background**, **think**, and **longContext** workloads.
4. **Provider‑agnostic**: Uniform interface across OpenAI‑style, Anthropic, OpenRouter, DeepSeek, Google, x‑AI, and Qwen endpoints.
5. **Observability & budgets**: Structured logging, metrics (SLA/SLO), and optional spend & rate governance.
6. **Simple operator UX**: Declarative config + some runtime slash‑commands for overrides.

### Non‑Goals

- Recreating full Claude Code Router (CCR). Dopemux integrates the parts we need; CCR may still be used for Claude UI compatibility but Dopemux’s router stands alone.
- Model‑training or safety policy design. We only route among already‑available models.
- Provider account provisioning. Keys/tokens are assumed available at runtime.

---

## 2) Key Concepts & Terminology

- **Route**: A named policy (e.g., `default`, `background`, `think`, `longContext`) mapping to a **priority‑ordered** list of model targets.
- **Target**: `(provider, model)` pair plus **adapter** (request/response transformer) and **limits** (ctx window, rate, cost).
- **Adapter**: Code that normalizes Dopemux’s internal message format to a provider’s API and back (OpenAI‑chat, Anthropic‑messages, OpenRouter‑proxy, DeepSeek‑reasoning fields, etc.).
- **Trigger**: Condition that changes the route or advances to next fallback (e.g., 429, usage‑limit message, token length > threshold, circuit‑breaker open).
- **Circuit breaker**: Temporary “do not use” flag for a target after repeated failures.

---

## 3) Architecture Overview

```
User (CLI/TUI) ──> Dopemux Router ──> Target Adapter(s) ──> Providers
                        │                         
                        ├─ Observability (logs, metrics, traces)
                        ├─ Governance (budgets, rate limits, per‑key scopes)
                        └─ Config Store (hot‑reloadable YAML/JSON)
```

- **Control plane**: Config, budgets, circuit breakers, and model catalogs.
- **Data plane**: Request → policy evaluation → target attempt(s) → response.
- **Optional external hub**: LiteLLM proxy can serve as a multiprovider backend; Dopemux treats it as a single target while still keeping per‑model visibility in labels/headers.

---

## 4) Routing Strategies (by Task Type)

### 4.1 `default` (cc‑default)

- **Intent**: Interactive coding/chat. Highest UX fidelity.
- **Primary**: Native Claude **subscription** (Sonnet 4 via Claude Code). **Never** burn Anthropic API unless the local client path is unavailable.
- **Fallbacks** (priority order): DeepSeek V3.1 (OpenRouter) → Qwen3‑Coder (OpenRouter) → GPT‑5 (OpenRouter, if enabled).
- **Triggers to leave primary**:
  - Usage/weekly limit message, HTTP 429, or repeated 5xx.
  - Explicit user override (`/model …`).

### 4.2 `background`

- **Intent**: Longer running, cost/latency‑optimized tasks (indexing, scaffold generation).
- **Primary**: Grok Code Fast 1 (OpenRouter) or equivalent.
- **Fallbacks**: DeepSeek V3.1 → default chain.

### 4.3 `think`

- **Intent**: Reasoning traces / deliberate steps when requested.
- **Primary**: DeepSeek R1 (distilled `…qwen3‑8b`) or other thinking‑enabled model.
- **Behavior**: Capture `reasoning_content`/thought fields when present; **persist** traces to artifacts according to retention policy.

### 4.4 `longContext`

- **Intent**: Requests exceeding a configurable token threshold.
- **Policy (final)**:
  - **≤ 128k** tokens → **DeepSeek V3.1** (cost‑effective, solid coding).
  - **128k – 400k** → **GPT‑5** via OpenRouter, if enabled for higher quality at mid‑range context.
  - **> 400k** (up to \~1M) → **Gemini 2.5 Pro**.
  - If an **Anthropic API key** is supplied and Sonnet 4 (1M context) is available, it may be added as an alternate for the >400k tier.
- **Trigger**: `estimated_tokens(input + history) > threshold`; multi‑tier thresholds supported.

---

## 5) Decision Flow (request lifecycle) (request lifecycle)

```
[Start]
  │
  ├─► 1) Classify task → route = {default|background|think|longContext}
  │        ├─ If longContext triggers, set route = longContext
  │        └─ Apply user override if present
  │
  ├─► 2) For route, build target list L = [t1, t2, ...]
  │
  ├─► 3) For each target t in L:
  │        a) Check circuit breaker, budget, rate limit
  │        b) Transform request via adapter(t)
  │        c) Call provider with retries (jittered backoff)
  │           • On success → normalize → return
  │           • On retriable error → retry up to N
  │           • On non‑retriable or exhausted retries → mark failure and continue
  │
  └─► 4) If all targets fail → terminal error with failure summary
```

**Error classes** (default handling):

- `429/usage_limit`: advance to next target, open breaker for the interval.
- `5xx/network`: limited retries, then advance; breaker if repeated.
- `4xx/invalid_request`: do **not** retry; surface error; consider policy‑guided rewrite if known fix.

---

## 6) Configuration Schema (Dopemux)

### 6.1 High‑level YAML

```yaml
version: 1
logging:
  level: info
  json: true
observability:
  tracing: false
  sample_rate: 0.05
budgets:
  enabled: true
  default_monthly_usd: 50
  per_key: {}
providers:
  - name: anthropic_native
    type: claude_subscription   # special adapter → uses installed Claude client/subscription
    # no api_key here; uses local app token/session

  - name: openrouter
    type: openai_compatible
    api_base: https://openrouter.ai/api/v1
    api_key: env:OPENROUTER_API_KEY

adapters:
  claude_subscription: { }
  openai_compatible:
    request_format: openai_chat
    response_format: openai_chat

models:
  - id: cc_sonnet4
    provider: anthropic_native
    meta:
      family: claude-sonnet
      max_context: 200k   # tune per discovery
      quality: high
      cost_tier: native

  - id: or_deepseek_v31
    provider: openrouter
    model: deepseek/deepseek-chat-v3.1
    meta: { family: deepseek, max_context: 128k, cost_tier: low }

  - id: or_grok_code_fast_1
    provider: openrouter
    model: x-ai/grok-code-fast-1
    meta: { family: grok, cost_tier: low, latency: low }

  - id: or_gemini_25_pro
    provider: openrouter
    model: google/gemini-2.5-pro
    meta: { family: gemini, max_context: 1000000, cost_tier: med }

  - id: or_openai_gpt5
    provider: openrouter
    model: openai/gpt-5
    meta: { family: gpt5, max_context: 400000, cost_tier: high }

routes:
  default:
    order: [cc_sonnet4, or_deepseek_v31, or_qwen3_coder, or_openai_gpt5]
    retry:
      per_target_retries: 2
      backoff_ms: [250, 750, 1500]
  background:
    order: [or_grok_code_fast_1, or_deepseek_v31]
  think:
    order: [or_deepseek_r1_qwen3_8b, cc_sonnet4]
    options:
      expose_reasoning: true
      persist_reasoning: true
  longContext:
    thresholds_tokens:
      - 128000
      - 400000
    # mapping: [ ≤128k, 128k–400k, >400k ]
    order_matrix:
      - [or_deepseek_v31, or_openai_gpt5, or_gemini_25_pro]
    # If Anthropic API is configured with 1M context Sonnet 4, append cc_sonnet4_api to the last column

circuit_breakers:
  failure_window_s: 60
  max_failures: 2
  cooldown_s: 45

rate_limits:
  enabled: true
  rules:
    - scope: per_key
      limit_per_min: 30
      burst: 60
  enabled: true
  rules:
    - scope: per_key
      limit_per_min: 30
      burst: 60
```

### 6.2 Notes

- `type: claude_subscription` is a special adapter that calls the local Claude client / embedded channel rather than Anthropic’s paid API key.
- `openai_compatible` handles OpenRouter (and any gateway that exposes `/v1/chat/completions`).
- `routes.*.order` expresses priority; Dopemux advances on failures per **Error classes**.

---

## 7) Provider Adapters (API Contracts)

### 7.1 OpenAI‑compatible (OpenRouter, LiteLLM, OpenAI)

- **Request**: `{model, messages[], temperature, top_p, max_tokens, ...}`
- **Response**: `choices[0].message.content`; optional `reasoning_content` captured to `meta.reasoning` when present.
- Supports `stream: true` with SSE; Dopemux merges partials.

### 7.2 Anthropic Subscription (Claude Code / Native)

- Interface through installed app or embedded local API (no API key).
- Respect subscription usage limits; detect banner/error strings and translate to `USAGE_LIMIT` internal code.

### 7.3 DeepSeek specifics

- Reasoning models may return separate thought fields; map to `meta.reasoning` and gate UI exposure by route option.

### 7.4 Gemini specifics

- Large context; verify token estimator pre‑call; support JSON mode where available; ensure safety settings are configurable per call.

---

## 8) Heuristics & Policy Rules

- **Limit detection**: Regex on error text + HTTP status (e.g., `/5[- ]?hour limit|weekly limit|usage limit/i` or 429).
- **Context estimator**: Tokenize `(history + prompt + tools)` with a conservative multiplier; compare vs `threshold_tokens` and vs each target’s `max_context`.
- **Cost guardrails**: Optional rule `max_usd_per_call`; if exceeded, prefer cheaper target unless user overrides.
- **User override precedence**: Explicit `/model provider,model` or `/route think` wins over automatic decisions for that session/thread.

---

## 9) Observability & Governance

- **Structured logs** (JSON): request id, route, attempt order, provider, model, tokens\_in/out, latency\_ms, cost\_estimate\_usd, result (ok|retry|fallback|fail), breaker state.
- **Metrics**: success rate by route/target; P50/P95 latency; fallback rate; token usage; per‑key spend.
- **Tracing**: optional OpenTelemetry spans: `route.evaluate`, `adapter.transform`, `provider.call`.
- **Budgets**: monthly per‑key caps; soft warning at 80%; hard stop at 100% → force native/zero‑cost where possible.

---

## 10) Security & Key Management

- **Secrets** only from environment or OS keychain. No keys in repo.
- **Virtual keys** (optio
