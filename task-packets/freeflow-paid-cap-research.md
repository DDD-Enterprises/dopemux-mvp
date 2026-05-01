---
id: TP-DMX-FREEFLOW-PAID-CAP-0001-RESEARCH
title: Freeflow Cheap and Self-Hosted LLM Research
type: explanation
owner: '@codex'
date: '2026-05-01'
author: '@hu3mann'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Research basis for opt-in paid-cap routing and local/self-host recommendations.
---
# Freeflow Paid-Cap Research

Verified on 2026-05-01. Provider prices and quotas are mutable; this file records the sources used for the initial paid-cap allowlist.

## Recommendation

Use local inference for continuous flow and privacy. On an M4 Pro Mac with 24 GB unified memory, the conservative default should be `qwen2.5-coder:7b` for headroom, with `qwen2.5-coder:14b` as the better local coding model when memory pressure is acceptable. The Ollama catalog lists Qwen2.5-Coder 7B at 4.7 GB, 14B at 9.0 GB, and 32B at 20 GB, all with 32K context. The 32B model leaves too little runtime and KV-cache headroom for this machine.

Use hosted paid-cap only as an opt-in overflow path after strict-free and local capacity. The first paid-cap route should be Gemini Flash-Lite Preview because the current Google pricing page lists `gemini-2.5-flash-lite-preview-09-2025` at $0.10/M input and $0.40/M output, while stable `gemini-2.5-flash-lite` is listed higher at $0.18/M input and $0.72/M output.

Use OpenRouter Qwen3-Coder-Next as the second paid-cap route for code-heavy fallback and model diversity. OpenRouter lists `qwen/qwen3-coder-next` with 262K context at $0.12/M input and $0.80/M output. OpenRouter lists full `qwen/qwen3-coder` at $0.22/M input and $1.80/M output, so it should remain cataloged but not enabled in the default paid-cap allowlist.

Do not treat cloud GPU rental as the cheapest always-on path unless utilization is high. RunPod bills pods by the second and points operators to live console pricing. Vast.ai is marketplace priced and varies by host, region, reliability, and demand. Those are useful for burst self-hosting, testing larger models, or privacy-sensitive jobs, but idle hours can exceed low-token API spend quickly.

## Researched Options

### Local Mac

* `qwen2.5-coder:7b`: best first local coding model for 24 GB memory headroom.
* `qwen2.5-coder:14b`: stronger local coding model, still plausible on 24 GB if context and parallelism are controlled.
* `qwen2.5-coder:32b`: catalog weight size is 20 GB before runtime/KV overhead, so this is not a headroom-safe default.
* Qwen3-Coder-Next: the technical report describes an 80B MoE with 3B active parameters; capability is attractive, but memory footprint and deployment complexity make it a later local experiment rather than the default for this Mac.

### Cheap Hosted API

* Gemini Flash-Lite Preview: first paid-cap candidate, low cost, direct provider key, current preview price $0.10/M input and $0.40/M output.
* OpenRouter Qwen3-Coder-Next: second paid-cap candidate, code-specialized, 262K context, current price $0.12/M input and $0.80/M output.
* OpenRouter Qwen3-Coder 480B A35B: catalog only, not enabled by default because output cost is materially higher.
* Cloudflare Workers AI: useful when Dopemux is already in Cloudflare, with 10,000 neurons/day free allocation and paid overage at $0.011 per 1,000 neurons. The listed Qwen2.5-Coder-32B price is $0.660/M input and $1.000/M output, so it is not the first cheap paid coding route.
* DeepInfra: attractive generic cheap models exist, including DeepSeek-V4-Flash at $0.14/M input and $0.28/M output and Step-3.5-Flash at $0.10/M input and $0.30/M output. This is research-only in this slice because the router needs explicit provider validation and model behavior tests before admission.
* Together AI: current Qwen3-Coder-Next price is $0.50/M input and $1.20/M output, so OpenRouter is cheaper for that model at the time of this research.

### Self-Hosted Cloud

* RunPod: good for explicit burst pods; official docs state pods are billed by the second for compute and storage, with latest GPU prices in the console.
* Vast.ai: good for price hunting and experiments; official docs describe market-driven pricing, real-time dashboard/CLI/API discovery, and per-second billing.
* Fireworks on-demand GPU: strong managed deployment option, but not a super-cheap default for this use case; official pricing shows H100/H200 class hourly pricing and a May 1, 2026 increase.

## Architecture Decision

Add paid-cap as an opt-in layer under `freeflow.paid_cap`, not a new mode. This preserves config version `1`, keeps strict-free semantics stable, and avoids hidden paid fallback behavior.

Default paid-cap allowlist:

* `gemini-flash-lite-preview-paid-cap`
* `openrouter-qwen3-coder-next-paid-cap`

Cataloged but not default-allowlisted:

* `openrouter-qwen3-coder-paid-cap`

## Sources

* Google Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
* Google Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
* OpenRouter Qwen3-Coder-Next pricing: https://openrouter.ai/qwen/qwen3-coder-next/pricing
* OpenRouter Qwen3-Coder pricing: https://openrouter.ai/qwen/qwen3-coder/pricing
* Cloudflare Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
* DeepInfra model pricing: https://deepinfra.ai/
* Together AI pricing: https://www.together.ai/pricing
* RunPod pod pricing: https://docs.runpod.io/pods/pricing
* Vast.ai pricing model: https://docs.vast.ai/guides/instances/pricing
* Fireworks pricing: https://fireworks.ai/pricing
* Ollama Qwen2.5-Coder catalog: https://registry.ollama.ai/library/qwen2.5-coder
* Qwen3-Coder-Next technical report: https://arxiv.org/abs/2603.00729
