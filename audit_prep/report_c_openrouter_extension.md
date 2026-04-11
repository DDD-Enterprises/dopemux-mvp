# Dopemux Repo Truth Extractor OpenRouter Model Portfolio Extension

## Executive verdict

A **true $0 entrance profile** can exist **today** on entity["company","OpenRouter","ai model routing platform"], but it’s **research-only**: the free plan is capped at **50 requests/day** and **20 requests/minute**, and free-tier usage can be throttled by providers during peak times; failed attempts still count toward the daily quota. citeturn25view2turn25view1 That combination makes a $0 profile unsuitable for any serious repo-scale RTE run unless your entire run fits comfortably into <50 LLM calls/day (rare for validator-gated, retry-minimized pipelines). citeturn25view2

The best hidden-value models discovered (in “hidden” = operationally relevant to RTE, not hype):

- **Free frontier-ish candidates that are actually usable for structured extraction experiments**:
  - **google/gemma-4-31b-it:free** (256K context, native function calling + structured output support, $0 tokens). citeturn10search0  
  - **qwen/qwen3-coder:free** (agentic coding–oriented MoE, 262K context, $0 tokens). citeturn23search0  
  - **minimax/minimax-m2.5:free** (196K context, $0 tokens; positioned for real productivity + agentic workflows). citeturn16search0turn21view1  
  - **meta-llama/llama-3.3-70b-instruct:free** (65K context, $0 tokens; stable baseline free general model). citeturn19search2  
  - **qwen/qwen3-next-80b-a3b-instruct:free** (262K context, explicitly optimized for stability + deterministic “no thinking traces” style). citeturn23search1  

- **Ultra-cheap paid models that look unusually well-matched to “bulk extraction + structure” economics**:
  - **deepseek/deepseek-v3.2** ($0.26/M in, $0.38/M out; 164K context). citeturn8search1  
  - **nousresearch/hermes-4-70b** ($0.13/M in, $0.40/M out; explicitly calls out JSON mode, schema adherence, function calling). citeturn18search0  
  - **meta-llama/llama-4-scout** ($0.08/M in, $0.30/M out; 327K context on OpenRouter; cheap long-context general workhorse). citeturn20view0  
  - **upstage/solar-pro-3** ($0.15/M in, $0.60/M out; 128K context). citeturn15search15  

Biggest research surprises (i.e., things that meaningfully change a routing portfolio):

- entity["company","Google","technology company, us"] / entity["organization","Google DeepMind","ai research unit, uk"] **Gemma 4 free variants exist** (not just “cheap”), and the model card explicitly claims **native function calling + structured output support**—which is exactly what RTE cares about. citeturn10search0turn10search1  
- **The free pool is not just “toy 7B models.”** As of April 2026, OpenRouter is advertising **25+ free models** from **4 free providers**. citeturn25view1  
- The free tier is **fragile by design**: an example in your face is **stepfun/step-3.5-flash:free** marked **“Going away April 9, 2026”** (tomorrow, relative to this report date). citeturn15search2  
- entity["company","MiniMax","ai company, china"]’s M2 line is now a legitimate **low-cost agentic coding / workflow** option and even has a **free variant** for M2.5. citeturn16search0turn16search1turn16search2  

Biggest operational traps (the stuff that will silently destroy “retry minimization” and budget discipline):

- **Free plan quotas** (50 req/day, 20 rpm) make “$0” mostly a **demo mode**, not a “profile.” citeturn25view2  
- **Free models churn**: OpenRouter explicitly warns availability changes frequently. citeturn15search12  
- **Provider throttling + quota counting**: OpenRouter notes free-tier usage may be rate-limited by the provider and failed attempts count toward the daily quota. citeturn25view2  
- **Tiered pricing / “starting at” prices** (notably in some long-context models) can blow up cost assumptions once requests exceed thresholds. Example: multiple Qwen endpoints note pricing varies by context length. citeturn8search3turn23search0turn13view3  
- **Data logging / retention caveats**: some model pages explicitly say prompts/completions are logged by the provider (e.g., Hunter Alpha; Qwen preview variants). citeturn6search19turn23search6  
- **Schema reliability is not “model intelligence.”** You need enforcement mechanisms: OpenRouter supports **JSON Schema–enforced structured outputs** for compatible models using `response_format.type=json_schema` with `strict: true`, and can fail fast if unsupported. citeturn5view2  
- **You should exploit OpenRouter routing economics**: when routing/fallback is enabled, you’re billed **only for the successful model run.** citeturn25view0  

## Method and evidence policy

How this extension was assembled:

- **Primary discovery** used OpenRouter first-party pages: pricing, structured outputs docs, model pages for candidate models, free models router docs, and OpenRouter’s “Free AI Models” collection as the most current *official* snapshot of free availability (updated “April 2026”). citeturn25view1turn5view2turn11view0turn15search12turn6search12  
- **Family coverage** was driven by targeted searches for model families and underused providers (MiniMax M2, Z.ai GLM-5/4.7, Devstral, Qwen3.* coder and “Next” variants, Gemma 4, xAI code-fast variants, Moonshot Kimi). citeturn16search1turn7search5turn6search0turn8search3turn10search1turn22search0turn7search3  

Evidence classification used throughout the tables:

- **First-party verified**: OpenRouter model pages, OpenRouter docs, OpenRouter announcements, and provider model pages surfaced through OpenRouter. These are used for **pricing, context windows, lifecycle tags (e.g., “going away”), and explicit feature claims** like “supports function calling.” citeturn25view1turn21view2turn10search1turn18search0turn16search2  
- **Reported / inferred**: Any claim that a model “behaves well” on strict JSON, or that it is “stable,” unless the model page explicitly states structured output/function calling support or it can be verified by supported-parameter metadata. OpenRouter itself notes structured outputs work only for compatible models and recommends checking supported parameters. citeturn5view2turn5view0  

What remains uncertain without a harness:

- **Per-model schema adherence rates** (validator pass/fail, malformed JSON frequency, retry rate). Docs can’t give you this; you must measure it. citeturn5view2  
- **Provider spread for each model** (multi-endpoint resilience) can’t always be reliably extracted from the static HTML in this environment; you should use OpenRouter’s Models/Endpoints APIs in your own tooling. citeturn5view0turn5view1turn4search9  

## OpenRouter candidate inventory

The inventory below is deliberately **ops-first**: pricing, context, and (most importantly) structured-output enforcement capability matter more than “leaderboard vibes.” OpenRouter provides schema-enforced structured outputs for compatible models via `response_format.type=json_schema` and recommends strict mode; requests fail if unsupported. citeturn5view2

**Legend (support columns):**  
- **Yes (doc)** = explicitly stated on model page or OpenRouter docs.  
- **Likely** = OpenRouter says “most open-source models” support structured outputs, but the specific model page doesn’t explicitly claim it. Treat as *needs harness verification*. citeturn5view2  
- **Unknown** = no reliable evidence captured in sources.

### Candidate inventory table

| Model family | OpenRouter model id | Free / promo / paid | Price (in/out) | Context | Structured outputs | JSON Schema mode | Tool / function calling | Provider spread | Lifecycle status | Availability notes | Major strengths for RTE | Major risks for RTE | Evidence class | Confidence |
|---|---:|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| Router | openrouter/free | Free | $0 / $0 | 200K | Yes (doc: router filters for structured outputs) | Likely | Yes (doc: router filters for tool calling) | Multi (routes among free models) | Active | Random model selection; feature-filtered | Quick $0 experimentation across free pool | Non-deterministic; free pool churn; quotas | First-party | High citeturn6search12turn15search12turn25view2 |
| Router | openrouter/auto | Paid (priced by routed model) | $0 “meta”; priced per routed model | 2M | Depends on routed model | Depends | Depends | Multi | Active | Routes to a fixed set of models | Useful as a *control*: “what OpenRouter would do” | Hard to reason about validator economics; non-deterministic | First-party | High citeturn19search21turn25view0 |
| Anthropic (control) | anthropic/claude-sonnet-4 | Paid | $3 / $15 (+$10/K web search) | 200K | Supported (per OpenRouter structured output support for Anthropic models Sonnet 4.5+ / Opus 4.1+) | Yes (doc class) | Yes (native tools for Anthropic models, via OpenRouter if model supports tools) | Multi (OpenRouter routing) | Active | Premium-ish but widely used control | High-quality reasoning + coding; strong for final synthesis / rescue | Expensive retries; must enforce schemas | First-party (pricing page + model page + OR feature doc) | High citeturn21view2turn5view2turn25view0 |
| OpenAI (control) | openai/gpt-4.1 | Paid | $2 / $8 | (not captured) | Supported (OpenAI GPT-4o+) | Yes (doc class) | Yes | Multi | Active | Good control for schema-disciplined extraction | Strong structured extraction; good reliability | Higher cost than “cheap ladder” models | First-party (OpenRouter announcement + structured outputs doc) | High citeturn1search15turn5view2 |
| OpenAI (control) | openai/gpt-4.1-mini | Paid | $0.40 / $1.60 | (not captured) | Supported (OpenAI GPT-4o+) | Yes (doc class) | Yes | Multi | Active | Cheap control for structured tasks | Best “value control” vs frontier | Still costs if retries spike | First-party | High citeturn1search15turn5view2 |
| OpenAI (control) | openai/gpt-4.1-nano | Paid | $0.10 / $0.40 | (not captured) | Supported (OpenAI GPT-4o+) | Yes (doc class) | Yes | Multi | Active | Ultra-cheap control for routing/classification tasks | Great router / classifier baseline | Likely weaker for deep repo reasoning | First-party | High citeturn1search15turn5view2 |
| Google / Gemma | google/gemma-4-31b-it:free | Free | $0 / $0 | 262K | Yes (doc on model page) | Yes (implied by structured output support) | Yes (native function calling on model page) | Unknown (needs API check) | Active | Free variant currently available | Strong $0 candidate for strict JSON + extraction | Free-tier throttling; availability churn | First-party | High citeturn10search0 |
| Google / Gemma | google/gemma-4-31b-it | Paid | $0.14 / $0.40 | 262K | Yes (doc on model page) | Likely | Yes (native function calling) | Unknown | Active | Paid variant exists; cheaper than many | Excellent low-cost “bulk extraction + schema” | Still needs harness validation | First-party | High citeturn10search1 |
| Google / Gemma | google/gemma-4-26b-a4b-it | Paid | $0.13 / $0.40 | 262K | Yes (doc on model page) | Likely | Yes (native function calling) | Unknown | Active | MoE with low active params | Very strong low-cost structured extraction | Same as above | First-party | High citeturn9search1 |
| Google / Gemma | google/gemma-3-27b-it:free | Free | $0 / $0 | 131K | Yes (model page claims structured outputs + function calling) | Likely | Yes | Unknown | Active | Free; older than Gemma 4 | Solid $0 baseline model | Smaller context + older | First-party | High citeturn9search0 |
| Google / Gemma | google/gemma-3-4b-it:free | Free | $0 / $0 | 32,768 | Yes (family claim) | Likely | Likely | Unknown | Active | Small free model | Cheap router/classifier / triage | Too small for hard repo synthesis | First-party | Medium citeturn10search2 |
| Google / Gemma | google/gemma-3-1b-it:free | Free | $0 / $0 | 32,000 | Yes (family claim) | Likely | Likely | Unknown | Active | Tiny; non-multimodal | Ultra-cheap routing, JSON repair drafts | Weak on hard reasoning | First-party | Medium citeturn9search12 |
| Google / Gemma | google/gemma-3n-e4b-it:free | Free | $0 / $0 | 8,192 (page shows 8,192) | Unknown | Unknown | Unknown | Unknown | Active | Conflicting text says “flexible 32K,” page shows 8,192 | Only as a tiny experimental router | Context uncertainty; too small | First-party (but internally inconsistent) | Low citeturn10search4 |
| Qwen | qwen/qwen3-coder:free | Free | $0 / $0 | 262K | Unknown (not explicitly “structured outputs” but built for agentic tool use) | Unknown | Implied by “function calling/tool use” positioning | Unknown | Active | Free variant exists | Best $0 code-aware extraction candidate | Needs proof of schema discipline | First-party | Medium citeturn23search0 |
| Qwen | qwen/qwen3-coder-flash | Paid | from $0.195 / $0.975 | 1,000,000 | Unknown | Unknown | Yes (agentic programming via tool calling) | Unknown | Active | Tiered pricing by context length | Massive-context code extraction at low cost | “Starting at” pricing + long context can still cost | First-party | High citeturn8search3 |
| Qwen | qwen/qwen3-next-80b-a3b-instruct:free | Free | $0 / $0 | 262,144 | Unknown | Unknown | Unknown | Unknown | Active | Explicit “stable, deterministic final answers” pitch | Free stable general lane for JSON extraction | Must test schema reliability | First-party | Medium citeturn23search1 |
| Qwen | qwen/qwen3.6-plus | Paid | $0.325 / $1.95 | 1,000,000 | Yes (OpenRouter supports reasoning_details; model used heavily) | Unknown | Unknown | Unknown | Active | 1M context | Huge-context parsing / synthesis | Expensive output tokens; validate tool support | First-party | High citeturn24view2turn8search2 |
| Qwen | qwen/qwen3.6-plus:free | Free (implied by “free” labeling in OpenRouter rankings) | Not shown on page | 1,000,000 | Unknown | Unknown | Unknown | Unknown | Active | “Qwen3.6 Plus (free)” appears in OpenRouter rankings as top used model | Potentially the single best $0 long-context lane | Pricing not explicitly shown on model page; must verify id + support via Models API | First-party for existence, not for all fields | Low citeturn17search24turn24view0turn25view2 |
| DeepSeek | deepseek/deepseek-v3.2 | Paid | $0.26 / $0.38 | 163,840 | Unknown | Unknown | Tool-use positioning; reasoning toggle mentioned | Unknown | Active | Very high real usage | Excellent cheap bulk extraction + repair | Must measure schema breaks; avoid “benchmark claims” | First-party | High citeturn8search1turn15search25 |
| DeepSeek | deepseek/deepseek-r1 | Paid | $0.70 / $2.50 | 64,000 | Unknown | Unknown | Reasoning model | Unknown | Active | Reasoning tokens “open” claim on model page | Strong contradiction detection / deep reasoning | Costly outputs; smaller context | First-party | High citeturn8search0 |
| MiniMax (M2) | minimax/minimax-m2.5:free | Free | $0 / $0 | 196,608 | Unknown | Unknown | Unknown | Unknown | Active | Free variant exists | Strong $0 agentic workflow / extraction | Needs schema testing | First-party | High citeturn16search0turn21view1 |
| MiniMax (M2) | minimax/minimax-m2.5 | Paid | $0.118 / $0.99 | 196,608 | Unknown | Unknown | Unknown | Unknown | Active | Paid variant exists | Cheap “production-ish” agentic model | Output tokens pricey vs some alternatives | First-party | High citeturn16search1 |
| MiniMax (M2) | minimax/minimax-m2.1 | Paid | $0.29 / $0.95 | 196,608 | Unknown | Unknown | “Preserve reasoning between turns” note | Unknown | Active | Coding/agentic | Good low-cost code-aware extraction | Must manage reasoning_details; schema unknown | First-party | High citeturn16search2 |
| MiniMax (M2) | minimax/minimax-m2 | Paid | $0.255 / $1.00 | 196,608 | Unknown | Unknown | Agentic coding / compile-run-fix focus | Unknown | Active | Coding focused | Repair passes for code extraction | Schema discipline unknown | First-party | High citeturn16search5 |
| MiniMax (M2) | minimax/minimax-m2.7 | Paid | $0.30 / $1.20 | 205K | Unknown | Unknown | Multi-agent collaboration positioning | Unknown | Active | Newer flagship | “Bigger brain” in M2 family | Costs higher than M2.5 | First-party | Medium citeturn16search1 |
| Z.ai / GLM | z-ai/glm-4.6 | Paid | $0.39 / $1.90 | 204,800 | Unknown | Unknown | Explicit “supports tool use during inference” | Unknown | Active | Tool + coding improvements | Strong low-cost long-context agent step | Schema unknown | First-party | High citeturn7search13turn7search4 |
| Z.ai / GLM | z-ai/glm-4.7 | Paid | $0.39 / $1.75 | 202,752 | Unknown | Unknown | Unknown | Unknown | Active | Newer than 4.6 | Better agent stability (claimed) | Verify; avoid trusting marketing | First-party | High citeturn7search0 |
| Z.ai / GLM | z-ai/glm-5-turbo | Paid | $1.20 / $4.00 | 202,752 | Unknown | Unknown | Tool use positioning | Unknown | Active | “Turbo” agent stability | Premium-ish step for hard tasks | Costs; schema unknown | First-party | High citeturn7search6 |
| Moonshot / Kimi | moonshotai/kimi-k2.5 | Paid | $0.3827 / $1.72 | 262,144 | Unknown | Unknown | “agentic tool-calling” positioning | Multi (pricing lists multiple providers) | Active | Multiple providers listed on pricing | Solid alternative long-context reasoning | Must test JSON discipline | First-party | High citeturn7search3turn7search7 |
| xAI | x-ai/grok-code-fast-1 | Paid | $0.20 / $1.50 (+$5/K web search) | 256K | Unknown | Unknown | Agentic coding; reasoning traces visible | Unknown | Active | Code-fast variant | Great for repair and code extraction | Output tokens pricey; schema unknown | First-party | High citeturn22search0 |
| xAI | x-ai/grok-4.1-fast | Paid | from $0.20 / $0.50 (+$5/K web search) | 2,000,000 | Unknown | Unknown | Tool calling positioning; reasoning toggle | Unknown | Active | Very long context | Serious long-context alternative | Must test schema; web search costs separate | First-party | High citeturn22search1 |
| xAI | x-ai/grok-4.20 | Paid | $2 / $6 (+$5/K web search) | 2,000,000 | Unknown | Unknown | Tool calling positioning; reasoning toggle | Unknown | Active | Newest flagship | Premium rescue alternative | Marketing claims need validation | First-party | Medium citeturn22search9 |
| Meta Llama | meta-llama/llama-4-scout | Paid | $0.08 / $0.30 | 327,680 | Likely (open-source class) | Likely | Unknown | Unknown | Active | Cheap long-context | Strong ultra-low-cost bulk lane | Must test structured outputs | First-party (pricing/context) + inferred support | Medium citeturn20view0turn5view2 |
| Meta Llama | meta-llama/llama-4-maverick | Paid | $0.15 / $0.60 | 1,048,576 | Likely | Likely | Unknown | Unknown | Active | 1M context | Massive-context synthesis / cross-file reasoning | Schema unknown; output costs matter | First-party + inferred | Medium citeturn20view1turn5view2 |
| Meta Llama | meta-llama/llama-3.3-70b-instruct:free | Free | $0 / $0 | 65,536 | Likely | Likely | Unknown | Unknown | Active | Free baseline | Stable $0 bulk extraction | Smaller context than 128K+ lanes | First-party + inferred | Medium citeturn19search2turn5view2 |
| Meta Llama | meta-llama/llama-3.3-70b-instruct | Paid | $0.10 / $0.32 | 131,072 | Likely | Likely | Unknown | Unknown | Active | Paid baseline exists | Cheap and stable control-ish baseline | Needs schema testing | First-party + inferred | Medium citeturn19search3turn5view2 |
| Mistral / Devstral | mistralai/devstral-2512 | Paid | $0.40 / $2.00 | 262,144 | Unknown | Unknown | Agentic coding focus | Unknown | Active | Open-source model; huge context | High-quality code-aware extraction | Output tokens not cheap | First-party | High citeturn6search0 |
| Mistral | mistralai/mistral-large | Paid | $2.00 / $6.00 | 128,000 | Unknown | Unknown | Explicitly claims “JSON” excellence | Unknown | Active | Strong general model | Strong synthesis / rescue | Not cheap | First-party | High citeturn6search1 |
| Nous | nousresearch/hermes-4-70b | Paid | $0.13 / $0.40 | 131,072 | Yes (explicit) | Yes (explicit “schema adherence”) | Yes (explicit) | Unknown | Active | Cheap + explicit structure support | Best “cheap structured judge/repair” candidate | Needs harness confirmation for real schemas | First-party | High citeturn18search0 |
| Nous | nousresearch/hermes-4-405b | Paid | $1.00 / $3.00 | 131,072 | Yes (explicit) | Yes | Yes | Unknown | Active | Larger Hermes 4 | Better reasoning/judgment lane (likely) | More expensive; still not frontier quality guaranteed | First-party | High citeturn17search0 |
| Nous | nousresearch/hermes-3-llama-3.1-405b:free | Free | $0 / $0 | 131,072 | Claimed by model page (“structured output capabilities”) | Unknown | Claimed (“function calling”) | Unknown | Active | Free large finetune | Interesting $0 judge/repair | Community reports of refusals/noise exist historically | First-party + reported | Medium citeturn6search2turn6search10 |
| Upstage | upstage/solar-pro-3 | Paid | $0.15 / $0.60 | 128,000 | Unknown | Unknown | Unknown | Unknown | Active | Korean-optimized MoE | Cheap bulk extraction | Schema unknown; language bias | First-party | Medium citeturn15search15 |
| Upstage | upstage/solar-pro-3:free | Free (variant exists) | Not shown on page | 128,000 | Unknown | Unknown | Unknown | Unknown | Active | Mentioned as free model selection example | Potential $0 bulk lane | Need to verify token price + limits | First-party for existence (partial) | Low citeturn15search4turn15search1turn25view2 |
| Stepfun | stepfun/step-3.5-flash:free | Free | $0 / $0 | 256,000 | Unknown | Unknown | Unknown | Unknown | Sunsetting | “Going away April 9, 2026” | High-throughput free reasoning lane (today) | Literally disappears tomorrow; do not anchor portfolio | First-party | High citeturn15search2 |

**Important note:** OpenRouter’s free plan is explicitly limited to **free models only** and **50 requests/day**. citeturn25view1turn25view2 The table above includes paid models because your requested routing portfolio includes ultra-low-cost through premium rescue ladders.

## Free / $0 candidate shortlist

This is the “if we have to build a $0 entry mode, what’s the least dumb way?” shortlist. It is **not** a production recommendation, because $0 + validator gating + retry minimization is a hostile triangle. citeturn25view2

| Model | Exact use case in RTE | Why it might work | Why it might fail | Experiment-worthy vs curiosity |
|---|---|---|---|---|
| openrouter/free | Quick $0 smoke tests for prompts/schemas across random free pool | Filters for needed features (tool calling, structured outputs) and costs $0. citeturn6search12turn15search12 | Non-deterministic model selection; free pool churn; daily quotas. citeturn15search12turn25view2 | **Experiment-worthy** (prompt + schema prototyping), not for measurement-grade A/B |
| google/gemma-4-31b-it:free | Primary $0 strict-JSON extraction lane | Explicit claims: structured output support + native function calling + 256K context, at $0. citeturn10search0 | Free-tier throttling; availability changes. citeturn25view2turn15search12 | **Experiment-worthy** and closest thing to “real” $0 structured extraction |
| qwen/qwen3-coder:free | $0 code-aware extraction + repair lane | Explicit code-agent positioning; repo reasoning orientation. citeturn23search0 | Tool/schema discipline not explicitly proven; tiered-pricing warning hints at complexity. citeturn23search0turn13view3 | **Experiment-worthy**, but gate with validator + strict retry caps |
| minimax/minimax-m2.5:free | $0 bulk extraction, mid-depth reasoning | 196K context; pitched as real productivity / workflows. citeturn16search0 | Schema discipline unproven; still subject to free quotas. citeturn25view2turn16search0 | **Experiment-worthy** (especially for long-context parsing) |
| qwen/qwen3-next-80b-a3b-instruct:free | $0 “stable final answer” lane for deterministic JSON | Explicitly optimized for stable, non-thinking-trace responses. citeturn23search1 | Stability claim ≠ schema adherence; must measure. citeturn23search1turn5view2 | **Experiment-worthy** |
| meta-llama/llama-3.3-70b-instruct:free | $0 cheap baseline for extraction/router tasks | A good “boring baseline” free model. citeturn19search2 | Smaller context than 128K+ options; may underperform on repo-wide synthesis. citeturn19search2 | **Experiment-worthy** as a control baseline in $0 mode |
| nousresearch/hermes-3-llama-3.1-405b:free | $0 judge/repair experiments | Model page claims structured output + function calling improvements. citeturn6search2 | Community reports mention refusals/noise; reliability uncertain. citeturn6search10 | **Curiosity → experiment** only if it beats Gemma 4 free in harness |
| stepfun/step-3.5-flash:free | *Do not build on it* (but test today if you want results) | High-volume free reasoning lane right now. citeturn15search2 | Sunsets **April 9, 2026**. citeturn15search2 | Only **curiosity testing** (it’s a disappearing floorboard) |

## Control-model refresh

The baseline report (per your summary) already prioritized schema reliability; current OpenRouter evidence supports doubling down on that by using enforced structured outputs + fallbacks rather than trusting “smart models” to behave. OpenRouter supports JSON Schema enforcement with strict mode for compatible models. citeturn5view2

Key control refresh points (pricing/lifecycle/support status):

- **OpenRouter free-tier limits are hard constraints on evaluation throughput**: 50 req/day and 20 rpm on the free plan. citeturn25view2 If you want meaningful harness runs, the minimum practical upgrade is “pay-as-you-go with at least $10 credits,” which removes limits on paid models and increases free-model allowance to 1000 requests (still 20 rpm). citeturn25view2  
- **Fallback economics are favourable for retry minimization**: OpenRouter states that with routing/fallback enabled, you’re billed only for the successful run. citeturn25view0 That means your config should bias to *quick failure + fallback* over *self-repair loops*.  
- **OpenAI GPT-4.1 series pricing is now clearly stratified for routing ladders**: GPT‑4.1 ($2/$8), GPT‑4.1 mini ($0.40/$1.60), GPT‑4.1 nano ($0.10/$0.40). citeturn1search15 The mini/nano tiers are ideal “control routers” for classification and schema-constrained extraction tasks where you need predictable compliance more than maximal reasoning.  
- **Anthropic Claude Sonnet 4 pricing** on OpenRouter is $3/$15 and adds a separate web search line item ($10 per 1K searches). citeturn21view2 Use this as a control for “premium rescue” and final synthesis, but do not let it soak retries.  
- **Meta Llama 4 Scout is a legitimate ultra-low-cost long-context control** ($0.08/$0.30; 327K context). citeturn20view0 For budgeted RTE steps needing longer context but not frontier-level reasoning, it’s an unusually attractive baseline.  
- **xAI’s “fast” family is priced for high-volume agent workflows** (e.g., Grok 4.1 Fast from $0.20/$0.50 with 2M context; Grok Code Fast 1 $0.20/$1.50). citeturn22search1turn22search0 These are plausible “alternative routing profiles,” but schema discipline is not proven by docs in the sources captured here.  
- **Model churn is real and immediate**: Step 3.5 Flash (free) is explicitly “Going away April 9, 2026.” citeturn15search2 Treat this as a warning pattern for any free dependency.

## Workload-fit analysis and profile construction

OpenRouter’s structured output capability is the cornerstone for RTE: you can enforce a JSON Schema using `response_format.type=json_schema` and `strict: true`, and OpenRouter notes the request fails if the model doesn’t support structured outputs. citeturn5view2 That is exactly aligned with validator-gated output and retry minimization (fail fast → fallback). citeturn25view0turn5view2

### Workload-fit highlights by lane

**Cheap routing / classification (low tokens, high volume).**  
The economic sweet spot for “router” is extremely cheap models with good instruction-following. For paid controls: **openai/gpt-4.1-nano** is priced at $0.10/$0.40, a good canonical control router. citeturn1search15 For ultra-low-cost non-OpenAI alternatives: **meta-llama/llama-4-scout** ($0.08/$0.30) is compelling when you need more context. citeturn20view0 For $0 experiments: **google/gemma-3-4b-it:free** or **meta-llama/llama-3.3-70b-instruct:free** are plausible, but you must accept free-tier quotas. citeturn10search2turn19search2turn25view2

**Bulk extraction (moderate tokens, many calls).**  
The best price/perf candidates in current evidence are: **deepseek/deepseek-v3.2** ($0.26/$0.38) citeturn8search1, **upstage/solar-pro-3** ($0.15/$0.60) citeturn15search15, and **nousresearch/hermes-4-70b** ($0.13/$0.40 with explicit structured output claims). citeturn18search0 Free options exist (Gemma 4 31B free; MiniMax M2.5 free; Qwen3 Next 80B free), but you cannot treat them as stable production lanes due to quota and churn risk. citeturn10search0turn16search0turn23search1turn25view2turn15search12

**Strict schema JSON (validator-gated JSON objects).**  
This lane should be *schema-enforced* (OpenRouter structured outputs) whenever possible. citeturn5view2 Best doc-supported candidates found:
- **google/gemma-4-31b-it** explicitly claims “structured output support” and “native function calling.” citeturn10search1  
- **nousresearch/hermes-4-70b** explicitly claims JSON mode, schema adherence, function calling, tool use. citeturn18search0  
- **OpenAI GPT-4.1 series** is a strong control set because OpenRouter lists OpenAI GPT-4o+ as structured-output compatible. citeturn1search15turn5view2  
- **Anthropic Claude Sonnet 4** as a premium judge/synth control; OpenRouter lists Anthropic Sonnet 4.5+ / Opus 4.1+ as structured-output compatible and Claude Sonnet 4 is in that generation. citeturn5view2turn21view2  

**Code-aware extraction (AST-ish understanding, cross-file reasoning).**  
Best candidates from this pass:
- **mistralai/devstral-2512** (262K context; explicit “codebase exploration… across multiple files”). citeturn6search0  
- **qwen/qwen3-coder-flash** and **qwen/qwen3-coder:free** (agentic coding, tool calling positioning). citeturn8search3turn23search0  
- **minimax/minimax-m2.1** / **minimax/minimax-m2** (explicit coding/agentic workflow emphasis). citeturn16search2turn16search5  
- **x-ai/grok-code-fast-1** (explicitly for agentic coding; reasoning traces visible). citeturn22search0  

**Contradiction detection / judge roles.**  
The judge is where you pay for correctness *and* schema. It should also be the lane with the strictest validator contract. OpenRouter structured outputs can enforce schemas; pick models explicitly compatible. citeturn5view2 Best candidates:
- **anthropic/claude-sonnet-4** for premium judgment where cost is acceptable. citeturn21view2  
- **openai/gpt-4.1** for structured adjudication and consistency. citeturn1search15turn5view2  
- **nousresearch/hermes-4-70b** as a low-cost judge with explicit structured output claims. citeturn18search0  
- **deepseek/deepseek-r1** for reasoning-heavy contradiction hunts (but it’s not cheap). citeturn8search0  

**Repair passes (schema repair / extraction correction).**  
Repair should be cheap, deterministic, and constrained. Use OpenRouter structured outputs when possible; otherwise mandate “JSON only” plus a repair transform. citeturn5view2 In a paid profile, **gpt-4.1-mini** is a great repair model ($0.40/$1.60). citeturn1search15 In open-weight land, **Hermes 4 70B** and **Llama 4 Scout** are plausible repair candidates but require harness proof of schema pass-rate. citeturn18search0turn20view0turn5view2  

### Zero-cost entrance profile design

**Verdict:** viable only as **experimental entrance** (prompt/schema prototyping + tiny repos), not as a production profile, because the free plan caps you at **50 requests/day**. citeturn25view2turn15search12

**Lane-by-lane assignment (best-effort with current evidence):**

- **Router / classifier**: google/gemma-3-4b-it:free (or meta-llama/llama-3.3-70b-instruct:free if classification needs more reasoning). citeturn10search2turn19search2  
- **Bulk extraction**: minimax/minimax-m2.5:free (long-ish context) with strict output contract and immediate fallback. citeturn16search0  
- **Strict JSON extraction**: google/gemma-4-31b-it:free as the primary, because it explicitly claims structured output support + function calling + 256K context. citeturn10search0  
- **Code-aware extraction / repair**: qwen/qwen3-coder:free. citeturn23search0  
- **Judge / contradiction detection**: meta-llama/llama-3.3-70b-instruct:free or qwen/qwen3-next-80b-a3b-instruct:free (prefer stability claims for deterministic outputs). citeturn19search2turn23search1  

**Which phases/steps it can cover:**  
- Prompt shaping, schema design, validator contract tuning, and very small-scale repo trials. This aligns with OpenRouter’s own positioning of free models for “learning and experimentation” and warns production users to consider paid models. citeturn15search4turn25view2  

**Which phases/steps it should not be trusted for:**  
- Large repo runs (token-heavy), multi-step judge loops, and anything where validator failures would require several retries—because retries burn request quota and free tier may be throttled; failed attempts still count toward the daily quota. citeturn25view2  

**Escalation rules (in $0 mode):**
- Hard cap: **1 attempt per lane**; if validator fails → fallback once; if fails again → **abort the step** and mark “needs paid lane.” This is because your real cost in $0 mode is *quota*, not money. citeturn25view2turn25view0  
- Avoid openrouter/free for evaluation runs because it changes the model under you; use it only for exploratory “does any free model answer this at all?” tests. citeturn6search12turn15search12  

**Why this is experimental rather than production-safe:**  
Because OpenRouter explicitly states free availability changes frequently, and the platform-level free limits are tight. citeturn15search12turn25view2turn15search2

### Alternative cost profiles

These profiles assume you’re using OpenRouter pay-as-you-go so you can actually run a harness consistently and avoid the free-plan choke point. Pay-as-you-go has no minimum spend and no lock-in. citeturn25view0

**Ultra-low-cost profile (cheapest credible ladder)**  
Goal: minimize $ while keeping schema success rate reasonable (with harness-verified candidates).

- Router/classifier: openai/gpt-4.1-nano citeturn1search15  
- Bulk extraction: meta-llama/llama-4-scout ($0.08/$0.30) or upstage/solar-pro-3 ($0.15/$0.60) depending on context needs citeturn20view0turn15search15  
- Strict JSON: nousresearch/hermes-4-70b (explicit schema/function calling claims) citeturn18search0  
- Code-aware extraction/repair: minimax/minimax-m2.1 or qwen/qwen3-coder-flash (tool-calling coding orientation) citeturn16search2turn8search3  
- Judge/rescue: openai/gpt-4.1-mini citeturn1search15  

Retry sensitivity: moderate; you must still cap retries because output tokens dominate costs. citeturn25view0

**Low-cost balanced profile (better reliability per dollar)**  
Goal: fewer retries, stronger schema success, still cheap.

- Router/classifier: openai/gpt-4.1-mini citeturn1search15  
- Bulk extraction: deepseek/deepseek-v3.2 citeturn8search1  
- Strict JSON: google/gemma-4-31b-it (paid) or hermes-4-70b (choose via harness) citeturn10search1turn18search0  
- Code-aware extraction: mistralai/devstral-2512 (big context) or qwen/qwen3-coder-flash (1M context) citeturn6search0turn8search3  
- Judge/validator: openai/gpt-4.1 (or gpt-4.1-mini if adequate) citeturn1search15  

**Production default profile (boring, reliable, minimized retries)**  
Goal: maximize validator pass rate and reduce operational surprises.

- Router/classifier: openai/gpt-4.1-mini citeturn1search15  
- Bulk extraction: deepseek/deepseek-v3.2 or gemma-4-31b-it (paid), selected via measured schema pass-rate and latency citeturn8search1turn10search1  
- Strict JSON: openai/gpt-4.1 with structured outputs enforced citeturn1search15turn5view2  
- Repair: openai/gpt-4.1-mini (cheap) with schema enforcement citeturn1search15turn5view2  
- Judge/synthesis: anthropic/claude-sonnet-4 citeturn21view2  

Operational note: configure OpenRouter fallbacks aggressively because only successful runs are billed with routing/fallback enabled. citeturn25view0

**Premium rescue profile (when correctness trumps cost)**  
Goal: one-shot salvage with the least nonsense.

- Deep reasoning / contradiction hunts / final synthesis: anthropic/claude-sonnet-4 citeturn21view2  
- Alternative premium long-context: x-ai/grok-4.1-fast (2M context) citeturn22search1  
- Giant-context synthesis alternative: meta-llama/llama-4-maverick (1,048,576 context) citeturn20view1  

Rescue profile must still enforce schemas via OpenRouter structured outputs where supported. citeturn5view2

## Raw comparison matrix

This matrix is meant to make candidates “comparable enough” for routing decisions without pretending docs can replace harness measurement.

| Model | Cost (in/out) | Context | Structured-output evidence | Tool evidence | Likely RTE lane | Volatility risk | Notes |
|---|---:|---:|---|---|---|---|---|
| google/gemma-4-31b-it:free | $0/$0 | 262K | Explicit structured outputs claim citeturn10search0 | Native function calling claim citeturn10search0 | $0 strict JSON extraction | Medium | Best $0 candidate found |
| qwen/qwen3-coder:free | $0/$0 | 262K | Not explicit | Agentic tool use positioning citeturn23search0 | $0 code extraction/repair | Medium | Must measure schema pass-rate |
| minimax/minimax-m2.5:free | $0/$0 | 196K | Not explicit | Not explicit | $0 bulk extraction | Medium | Good long-context free lane |
| meta-llama/llama-3.3-70b-instruct:free | $0/$0 | 65K | Inferred (open-source class) citeturn5view2turn19search2 | Unknown | $0 baseline extraction/router | Medium | Smaller context |
| deepseek/deepseek-v3.2 | $0.26/$0.38 | 164K | Unknown | Reasoning toggle mentioned citeturn8search1 | Cheap bulk extraction | Low | Very strong economics |
| nousresearch/hermes-4-70b | $0.13/$0.40 | 131K | Explicit JSON/schema/function calling citeturn18search0 | Explicit citeturn18search0 | Cheap strict JSON + judge | Medium | Dark-horse “structured judge” |
| openai/gpt-4.1-mini | $0.40/$1.60 | (n/a) | OpenAI GPT-4o+ structured compatible citeturn5view2turn1search15 | Yes (family) citeturn5view2 | Control router/repair | Low | Best paid glue model |
| anthropic/claude-sonnet-4 | $3/$15 | 200K | Anthropic structured compatible citeturn5view2turn21view2 | Likely | Premium synthesis/judge | Low | Don’t waste retries here |
| meta-llama/llama-4-scout | $0.08/$0.30 | 327K | Inferred (open-source class) citeturn5view2turn20view0 | Unknown | Ultra-low-cost bulk | Medium | Great economics; measure schema |
| mistralai/devstral-2512 | $0.40/$2.00 | 262K | Unknown | Unknown | Code-aware extraction | Medium | Promising for repo-wide coding |

## Config-ready routing recommendations

OpenRouter facts to treat as “constraints” in config:

- Free plan: **50 requests/day**, **20 rpm**; free-model usage may be throttled; failures count toward quota. citeturn25view2  
- Routing/fallback billing: **only successful run billed** when routing/fallback enabled. citeturn25view0  
- Structured outputs: enforce JSON Schema using `response_format.type=json_schema` and `strict: true` for compatible models. citeturn5view2  

### Profile summary table

| Profile | Intent | Default lane | Fallback | Judge lane | Notes |
|---|---|---|---|---|---|
| $0 entrance (experimental) | Prompt/schema prototyping | gemma-4-31b-it:free | minimax-m2.5:free → qwen3-coder:free | llama-3.3-70b-instruct:free | Cap retries hard due to 50 req/day citeturn25view2turn10search0turn16search0turn23search0turn19search2 |
| Ultra-low-cost | Min $/run | llama-4-scout | solar-pro-3 → deepseek-v3.2 | hermes-4-70b | Great if schema holds in harness citeturn20view0turn15search15turn8search1turn18search0 |
| Balanced low-cost | Fewer retries | deepseek-v3.2 | gemma-4-31b-it → gpt-4.1-mini | gpt-4.1 | Standard “cheap but sane” citeturn8search1turn10search1turn1search15 |
| Production default | Reliability | gpt-4.1-mini | gpt-4.1 → claude-sonnet-4 | claude-sonnet-4 | Rescue is expensive; keep rare citeturn1search15turn21view2 |
| Premium rescue | Salvage | claude-sonnet-4 | grok-4.1-fast | claude-sonnet-4 | Use for hardest steps only citeturn21view2turn22search1 |

### Routing-policy summary

- Always request **structured outputs** (JSON Schema strict) where supported; fail fast otherwise. citeturn5view2  
- On validator failure: **no more than 1 retry per lane**; then escalate to next lane. This exploits OpenRouter’s “only successful run billed” behaviour under routing/fallback. citeturn25view0  
- Treat free models as **non-contractual capacity**; never rely on them for production SLAs. Free model availability changes frequently. citeturn15search12turn25view2  
- Avoid dependency on models with explicit near-term lifecycle changes (example: Step 3.5 Flash (free) sunsets April 9, 2026). citeturn15search2  

### Config-ready YAML sketch

```yaml
profiles:
  zero_cost_entrance:
    budget:
      max_cost_usd: 0.00
      max_requests_per_day: 50   # hard external constraint on OpenRouter free plan
    lanes:
      route_classify:
        primary: google/gemma-3-4b-it:free
        fallback: meta-llama/llama-3.3-70b-instruct:free
        max_attempts: 1
      extract_json:
        primary: google/gemma-4-31b-it:free
        fallback: minimax/minimax-m2.5:free
        max_attempts: 1
        require_json_schema: true
      code_extract_repair:
        primary: qwen/qwen3-coder:free
        fallback: google/gemma-4-31b-it:free
        max_attempts: 1
        require_json_schema: true
      judge_contradictions:
        primary: qwen/qwen3-next-80b-a3b-instruct:free
        fallback: meta-llama/llama-3.3-70b-instruct:free
        max_attempts: 1

  ultra_low_cost:
    budget:
      max_cost_usd: 0.50
    lanes:
      route_classify:
        primary: openai/gpt-4.1-nano
        fallback: meta-llama/llama-4-scout
        max_attempts: 1
      bulk_extract:
        primary: meta-llama/llama-4-scout
        fallback: upstage/solar-pro-3
        max_attempts: 1
      strict_json:
        primary: nousresearch/hermes-4-70b
        fallback: openai/gpt-4.1-mini
        max_attempts: 1
        require_json_schema: true
      code_extract_repair:
        primary: qwen/qwen3-coder-flash
        fallback: minimax/minimax-m2.1
        max_attempts: 1
      judge_final:
        primary: openai/gpt-4.1-mini
        fallback: openai/gpt-4.1
        max_attempts: 1
        require_json_schema: true

  production_default:
    budget:
      max_cost_usd: 5.00
    lanes:
      route_classify:
        primary: openai/gpt-4.1-mini
        fallback: openai/gpt-4.1
        max_attempts: 1
      bulk_extract:
        primary: deepseek/deepseek-v3.2
        fallback: google/gemma-4-31b-it
        max_attempts: 1
      strict_json:
        primary: openai/gpt-4.1
        fallback: anthropic/claude-sonnet-4
        max_attempts: 1
        require_json_schema: true
      code_extract_repair:
        primary: mistralai/devstral-2512
        fallback: openai/gpt-4.1-mini
        max_attempts: 1
      judge_final:
        primary: anthropic/claude-sonnet-4
        fallback: openai/gpt-4.1
        max_attempts: 1
        require_json_schema: true

policy:
  escalation_triggers:
    - validator_failed
    - invalid_json
    - missing_required_keys
    - exceeded_max_tokens
  no_go:
    - use_random_router_for_eval: openrouter/free   # only for ad-hoc experiments
```

## What still needs real evaluation harness testing

Even with strong model-page evidence, the operator-critical questions for RTE are **empirical**.

What must be tested inside the Dopemux RTE harness:

- **Schema pass-rate per model and lane**, using OpenRouter structured outputs with strict JSON Schema. Record: first-pass valid JSON %, validator pass %, retries per step, median tokens, and timeouts. citeturn5view2turn25view0  
- **Retry sensitivity curves**: for each lane, run with max_attempts = 1 vs 2 and measure marginal gain vs cost; OpenRouter’s “only successful run billed” changes the economics of fallback vs retry. citeturn25view0  
- **Free-tier operational realism**: under the free plan, test whether your typical RTE run fits inside **50 requests/day**; quantify how many steps can complete before quota exhaustion. citeturn25view2  
- **Provider throttling impact**: measure request error rate and latency variance at peak hours; OpenRouter notes free-tier may be rate-limited by providers. citeturn25view2  
- **Long-context correctness vs cost**: for 128K/256K/1M context lanes, measure whether longer context actually reduces calls (net cheaper) or increases output verbosity (net more expensive). Candidates: llama-4-scout, qwen3.6-plus, grok-4.1-fast. citeturn20view0turn24view2turn22search1  
- **Tool/function calling correctness** where relevant (e.g., when RTE invokes repo scanners or validators as “tools”): models that explicitly advertise function calling should be compared head-to-head under identical tool schemas. Candidates with explicit claims: gemma-4-31b-it, hermes-4-70b. citeturn10search1turn18search0  

Datasets / step types to use (to keep eval fair and “RTE-real”):

- A fixed set of repos with controlled complexity: small (single package), medium (multi-module), large (monorepo). Keep prompts identical and measure validator outcomes. (No public source covers your private repos; this is by necessity internal.)  
- Step types aligned to RTE: “entity extraction from code,” “config extraction,” “API surface summarization,” “contradiction detection across files,” “JSON repair pass,” “final synthesis.”  
- Always include at least one **control model** (gpt-4.1-mini and/or gpt-4.1) to avoid fooling yourself with novelty. citeturn1search15  

How to compare “free obscure models” fairly:

- Use the same schema, same max tokens, same temperature, same validator, same budget caps.  
- Track both **success probability** and **expected total cost**, where “cost” in free mode is quota consumption and time. citeturn25view2turn25view0  

## Confidence and uncertainty register

**High confidence (first-party confirmed and stable enough to route on):**

- Free plan quota and throttling constraints (50 req/day, 20 rpm; provider throttling; failed attempts count). citeturn25view2  
- OpenRouter structured outputs mechanism via JSON Schema strict mode + failure behaviour when unsupported. citeturn5view2  
- Key model prices + contexts when captured from OpenRouter model pages: Claude Sonnet 4 citeturn21view2, GPT-4.1 series pricing citeturn1search15, Gemma 4 31B paid/free citeturn10search0turn10search1, DeepSeek V3.2 citeturn8search1, Hermes 4 70B citeturn18search0, MiniMax M2.5 free citeturn16search0, Llama 4 Scout citeturn20view0, Grok 4.1 Fast citeturn22search1.  
- Immediate churn risk example: Step 3.5 Flash (free) going away April 9, 2026. citeturn15search2  

**Medium confidence (good candidates, but schema discipline/tool behaviour must be measured):**

- qwen/qwen3-coder:free as a code-aware extraction lane (strong positioning, but not explicit schema guarantees). citeturn23search0turn5view2  
- meta-llama/llama-4-scout as an ultra-low-cost bulk extraction model (great pricing/context; structured-output support inferred). citeturn20view0turn5view2  
- minimax/minimax-m2.1 / minimax/minimax-m2 for repair loops (agentic coding claims; schema pass-rate unknown). citeturn16search2turn16search5  

**Low confidence (evidence gaps that block “decision-grade” use today):**

- Any free model where pricing or exact structured-output support is not explicitly confirmed on the captured model page (example: upstage/solar-pro-3:free; qwen/qwen3.6-plus:free). citeturn15search1turn24view0turn17search24  
- Provider spread/resilience across multiple endpoints for many models (needs your own OpenRouter Models/Endpoints API query). citeturn5view0turn5view1turn4search9  

**Unstable / likely to change soon:**

- Free model roster (OpenRouter explicitly says availability changes frequently). citeturn15search12  
- Any model marked preview or with explicit logging caveats (e.g., Hunter Alpha prompts logged; Qwen preview data collection). citeturn6search19turn23search6