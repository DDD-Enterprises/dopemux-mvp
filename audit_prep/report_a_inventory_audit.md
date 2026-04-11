# Dopemux RTE and OpenClaw model inventory and routing-intake audit

## Scope, conventions, and executive findings

**Executive summary**

This audit is about production routing reality, not vibes. The current landscape is dominated by a few “clean” first‑party API surfaces with explicit controls (batch, caching, ZDR/residency, tool calling), plus a messy-but-valuable aggregator layer (OpenRouter) that expands the portfolio and adds routing/failover—at the cost of a longer trust chain. citeturn13view2turn10search3turn10search7turn10search0turn11view0

For Dopemux Repo Truth Extractor (RTE), the winning pattern is a **cost-aware escalation ladder**:

- **Prescan + routing-intake normalization:** ultra-cheap models with strong instruction adherence and predictable token accounting (often “mini/nano/flash-lite” tiers) plus aggressive caching. citeturn26view0turn14view0turn14view1turn23search0  
- **Schema-bound extraction + repair loops:** models with **explicit structured output** + tool/function calling stability, and whose providers document retention/routing controls well enough to pass governance. citeturn13view2turn10search7turn9search20turn25view5  
- **Synthesis (high-stakes merge, citations, narrative):** flagship reasoning models (or research agents) with web/search tooling and stable long-context handling—ideally with batch for large backfills. citeturn26view1turn10search27turn14view2turn12view2  

For OpenClaw-oriented agentic development, the constraints shift: you care less about single-shot brilliance and more about **tool-loop reliability**, long-context “memory” economics, and low-latency iteration (agents die by a thousand slow RTTs). The OpenRouter rankings strongly imply OpenClaw is already living in that ecosystem at significant scale (OpenClaw appears as the top app/agent by token usage in the OpenRouter rankings view). citeturn11view0

Where it gets dangerous (in the “you’ll regret this in prod” sense):

- **Subscription/chat surfaces** (ChatGPT plans, Grok app plans, etc.) are **not** clean substitutes for API surfaces. They’re excellent for operator productivity but usually lousy as a canonical benchmark substrate because limits/quotas/tooling/model mixes are plan-governed and can drift. citeturn27view0turn19view0  
- **Aggregator routing** can improve uptime and add fallbacks, but it expands the data-handling chain. You must treat “OpenRouter route” as a separate surface from “direct provider API.” citeturn10search3turn10search0turn10search7turn10search11  
- **Free lanes** are great for experimentation, sometimes great for throughput, and almost always terrible for governance (unless your workload is non-sensitive by design). citeturn10search16turn10search6turn10search34  

**Canonical naming corrections**

The user-provided names contained a mix of correct identifiers, marketing-ish labels, and a few “maybe-real” variants that must be treated as unverified until first-party docs list them. Below is a canonical map, oriented around **exact IDs and surfaces** (not brand families).

> Evidence-level legend used throughout: **OFFICIAL**, **AGGREGATOR-OFFICIAL**, **THIRD-PARTY**, **INFERRED**, **UNKNOWN**.

| User-mentioned name | Corrected official name | Exact model ID(s) | Surface type(s) | Status notes | Evidence level |
|---|---|---|---|---|---|
| GPT-5.4 | GPT-5.4 | `gpt-5.4` | general API model | Stable flagship pricing published | OFFICIAL citeturn26view0turn24view0 |
| GPT-5.4 Pro | GPT-5.4 pro | `gpt-5.4-pro` | general API model; (also appears as a ChatGPT Pro entitlement) | “Pro” is not a plan name here; it’s a model variant. | OFFICIAL citeturn4view0turn27view0 |
| GPT-5.4 variants | GPT-5.4 mini, GPT-5.4 nano | IDs not fully confirmed in this run (likely `gpt-5.4-mini`, `gpt-5.4-nano`) | general API model (mini/nano tiers) | Prices published; ID strings should be verified in model catalog before hardcoding | OFFICIAL for pricing; INFERRED for IDs citeturn26view0turn19view0 |
| GPT-5.2 | GPT-5.2 | ID not confirmed in this run (likely `gpt-5.2`) | general API model | Listed as “more models” in OpenAI model catalog | OFFICIAL for existence; INFERRED for ID string citeturn19view0 |
| GPT-5.3-Codex | GPT-5.3-Codex | `gpt-5.3-codex` | coding-specialized API model | Pricing + limits shown on model page | OFFICIAL citeturn2view0 |
| GPT-5.2-Codex | GPT-5.2-Codex | ID not confirmed in this run | coding-specialized API model | Listed in OpenAI model catalog; verify IDs before registry freeze | OFFICIAL for existence; UNKNOWN for exact ID citeturn19view0 |
| GPT-4.1 variants | GPT-4.1, GPT-4.1 mini, GPT-4.1 nano | IDs not confirmed in this run | general API model | Listed as current models (keep as controls) | OFFICIAL for existence; UNKNOWN for exact IDs citeturn19view0 |
| GPT-4 variants still relevant | GPT-4, GPT-4 Turbo | IDs not confirmed in this run | deprecated/legacy controls | Keep only as baselines; some variants explicitly marked deprecated | OFFICIAL citeturn19view0 |
| GPT-4o variants | GPT-4o, GPT-4o mini; “ChatGPT-4o” (ChatGPT-only, deprecated) | IDs not confirmed in this run | general API model; chat-only model surface | “ChatGPT-4o” is explicitly a ChatGPT model surface, not recommended for API | OFFICIAL citeturn19view0 |
| o3 / o3-pro / o4 variants | o3, o3-pro, o4-mini | IDs not confirmed in this run | general API model (reasoning) | o3-pro pricing published on model page; others listed as “more models” | OFFICIAL for existence; OFFICIAL for o3-pro pricing citeturn3view0turn19view0 |
| deep-research variants | o3-deep-research; o4-mini-deep-research | IDs not confirmed in this run | deep-research model / research agent | Listed as dedicated “Deep research” models | OFFICIAL for existence; UNKNOWN for pricing/limits in this run citeturn19view0 |
| Claude Opus 4.5 / 4.6 | Claude Opus 4.6; Claude Opus 4.5 | IDs: `claude-opus-4-6` etc. | general API model | Listed in Anthropic docs model overview; Bedrock context expands to 1M for 4.6 | OFFICIAL citeturn7search1turn7search37 |
| Claude Sonnet 4.5 / 4.6 | Claude Sonnet 4.6; Claude Sonnet 4.5 | IDs: `claude-sonnet-4-6` etc. | general API model | Pricing for Sonnet 4.6 stated on product page | OFFICIAL citeturn7search26turn7search37 |
| Claude Haiku 4.5 / 4.6 if real | Claude Haiku 4.5 exists; “Haiku 4.6” not confirmed | IDs: `claude-haiku-4-5` etc. | general API model (fast tier) | Treat “Haiku 4.6” as invalid until first-party lists it | OFFICIAL (Haiku 4.5); UNKNOWN (Haiku 4.6) citeturn7search1turn7search22 |
| Gemini 3.x current variants | Gemini 3.1 Pro Preview; Gemini 3 Flash Preview; Gemini 3.1 Flash-Lite Preview | `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview` | general API model | All are explicitly “preview” in identifiers | OFFICIAL citeturn14view0turn8search6 |
| Gemini 2.5 controls | Gemini 2.5 Pro / Flash / Flash-Lite | `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` | general API model | Pricing and batch pricing published | OFFICIAL citeturn14view1turn14view2 |
| Grok 4.20 / 4.1 variants | grok-4.20-*; grok-4-1-fast-* | `grok-4.20-reasoning`, `grok-4.20-non-reasoning`, `grok-4-1-fast-reasoning`, `grok-4-1-fast-non-reasoning` | general API model | Official pricing table lists them; note hyphen/period placement | OFFICIAL citeturn25view4turn25view5 |
| grok-code-fast-1 | Grok Code Fast 1 | `grok-code-fast-1` | coding-specialized API model | Official model page exists | OFFICIAL citeturn9search1 |
| SuperGrok (plan tier) | SuperGrok | N/A (plan) | subscription / plan tier / app surface | Must not be treated as a model family | OFFICIAL as plan surface; UNKNOWN for quota details | OFFICIAL citeturn9search5 |
| openrouter/free router surface | Free Models Router | `openrouter/free` | aggregator-routed model | Randomly selects from free pool; feature-filtered | AGGREGATOR-OFFICIAL citeturn10search16turn10search9 |

**Comparison taxonomy**

To avoid fraudulent “apples-to-oranges” benchmarking (the #1 way model evaluations get stupid), comparisons must be stratified by **surface** and **workload class**:

- **Deep research agents vs plain generation APIs.** Deep research models (e.g., OpenAI “deep-research” entries) are specialized surfaces and not fair baselines for ordinary completions-style models. citeturn19view0  
- **Coding-specialized models vs general extraction models.** Coding models (e.g., “Codex” line) should be compared to other coding-tuned models, not to “mini/nano” generalists, unless you are explicitly analyzing “coding at minimal cost.” citeturn2view0turn19view0turn9search1  
- **Tool-integrated platforms vs tool-neutral models.** A “model + integrated web search + code execution” surface (xAI Agent Tools, OpenAI web search/containers, Gemini grounding) changes the task. Treat it as a different product. citeturn24view1turn9search9turn14view1turn25view5  
- **Subscription/chat surfaces vs token-billed APIs.** Subscription plans have opaque/per-plan quotas and changing model mixes; APIs are meterable. Don’t mix them in the same harness unless your benchmark explicitly targets “operator economics.” citeturn27view0turn13view2  
- **Direct-provider routes vs aggregator routes.** OpenRouter routing, BYOK, ZDR filters, and provider fallbacks materially change both risk and performance. “Same model name” does not imply “same surface.” citeturn10search3turn10search11turn10search7turn10search27  
- **Local/open-weight vs hosted frontier APIs.** Open-weight models can be excellent, but they shift constraints to hardware, quantization quality, latency, and ops. Treat them as separate lanes with explicit deployment assumptions. citeturn21view4turn8search3turn16search8turn18search3  

## Canonical model-and-route registry

**Canonical model-and-route registry**

This registry is intentionally “surface-first”: the same underlying model family can appear in multiple rows if the **route** changes risk, pricing, limits, or tool availability.

Field conventions:

- Any value not explicitly sourced is marked **UNKNOWN** (not guessed).
- For OpenRouter rows, pricing/limits/tools are **AGGREGATOR-OFFICIAL** unless a first-party source is cited.
- “Context (in/out)” uses provider doc conventions. Gemini 3 models explicitly publish in/out. citeturn14view0  

### Core registry

| Canonical display name | Route (surface) | Exact ID(s) to route | Surface classification | Status | Context / output limits | Structured output + tools | Pricing (USD; per 1M tokens unless noted) | Evidence level |
|---|---|---|---|---|---|---|---|---|
| GPT-5.4 | Direct OpenAI API | `gpt-5.4` | general API model | Stable | UNKNOWN in this run (see model page separately) | Prompt caching supported platform-wide; supports web search tool as separate billable tool | Input $2.50; cached input $0.25; output $15.00 | OFFICIAL citeturn26view0turn23search0turn24view1 |
| GPT-5.4 mini | Direct OpenAI API | **UNKNOWN** (verify ID before hardcoding) | general API model; “mini tier” | Stable | UNKNOWN | Same platform tool surface; caching supported | Input $0.750; cached input $0.075; output $4.500 | OFFICIAL (pricing); UNKNOWN (ID) citeturn26view0turn23search0 |
| GPT-5.4 nano | Direct OpenAI API | **UNKNOWN** (verify ID before hardcoding) | general API model; “nano tier” | Stable | UNKNOWN | Same platform tool surface; caching supported | Input $0.20; cached input $0.02; output $1.25 | OFFICIAL (pricing); UNKNOWN (ID) citeturn26view0turn23search0 |
| GPT-5.4 pro | Direct OpenAI API | `gpt-5.4-pro` | general API model | Stable | 1,050,000 context; 128,000 max output | Supports tool usage per platform; “full chain-of-thought” not stated here | Input $30.00; output $180.00 | OFFICIAL citeturn4view0 |
| GPT-5.3 Chat | Direct OpenAI API | `gpt-5.3-chat-latest` | app/chat-oriented API model | Stable | 128,000 context; 16,384 max output | Not a deep-research agent; normal generation | Input $1.00; output $5.00 | OFFICIAL citeturn0search1 |
| GPT-5.3-Codex | Direct OpenAI API / Codex | `gpt-5.3-codex` | coding-specialized API model | Stable | 400,000 context; 128,000 max output | Built for agentic coding; Codex integration surface | Input $2.00; output $8.00 | OFFICIAL citeturn2view0 |
| GPT-5-Codex | Direct OpenAI API / Codex | `gpt-5-codex` | coding-specialized API model | Stable | 400,000 context; 128,000 max output | Built for agentic coding; Codex integration surface | Input $1.25; output $10.00 | OFFICIAL citeturn2view1 |
| o3-pro | Direct OpenAI API | `o3-pro` | general API model (reasoning) | Stable | UNKNOWN | Normal tool surface; priority processing available separately | Input $10.00; output $40.00 (batch price shown on page as Input $20, Output $80—interpretation unclear without full context) | OFFICIAL (pricing shown); UNKNOWN (batch semantics) citeturn3view0 |
| o3-deep-research | Direct OpenAI API | **UNKNOWN** (verify ID) | deep-research model / research agent | Stable | UNKNOWN | Deep research surface | UNKNOWN | OFFICIAL for existence; UNKNOWN for details citeturn19view0 |
| o4-mini-deep-research | Direct OpenAI API | **UNKNOWN** (verify ID) | deep-research model / research agent | Stable | UNKNOWN | Deep research surface | UNKNOWN | OFFICIAL for existence; UNKNOWN for details citeturn19view0 |
| gpt-oss-120b | Local/open-weight (download) | Weights: `gpt-oss-120b` | local/open-weight model | Stable weights | 131,072 context; 131,072 max output | “Agentic capabilities” claimed; tool execution still requires host runtime | Self-host cost = infra; API pricing not provided here | OFFICIAL citeturn21view1 |
| gpt-oss-20b | Local/open-weight (download) | Weights: `gpt-oss-20b` | local/open-weight model | Stable weights | 131,072 context; 131,072 max output | Same as above | Self-host cost = infra | OFFICIAL citeturn21view4 |
| Claude Sonnet 4.6 | Direct Anthropic API | `claude-sonnet-4-6` (exact string must be confirmed from Anthropic console) | general API model | Stable | Output limit up to 300k with special header (max across synced tiers is model-dependent) | Tool use + “extended thinking” supported; prompt caching feature exists and is ZDR-eligible | Input $3; output $15 (as stated on Anthropic site) | OFFICIAL (feature+cap); OFFICIAL (pricing statement) citeturn7search1turn7search26turn23search1 |
| Claude Opus 4.6 | Amazon Bedrock route | Bedrock model IDs differ (not captured here) | cloud-platform route | Stable | 1M context on Bedrock for Opus 4.6 | Tooling depends on Bedrock integration | Pricing/quotas per Bedrock; not captured here | OFFICIAL for context-on-Bedrock; UNKNOWN for costs | citeturn7search37 |
| Gemini 3.1 Pro Preview | Direct Gemini API | `gemini-3.1-pro-preview` | general API model | Preview | 1M / 64k (in/out) | Thinking controls via `thinking_level`; grounding billed separately | Input $2/$4 (>200k); output $12/$18; caching priced + storage hourly | OFFICIAL citeturn14view0turn14view1 |
| Gemini 3 Flash Preview | Direct Gemini API | `gemini-3-flash-preview` | general API model | Preview | 1M / 64k (in/out) | Thinking controls; multimodal; caching | Input $0.50; output $3.00 (paid tier shown) | OFFICIAL citeturn14view0turn14view1 |
| Gemini 3.1 Flash-Lite Preview | Direct Gemini API | `gemini-3.1-flash-lite-preview` | general API model (low-cost) | Preview | 1M / 64k (in/out) | Designed for high-volume agentic tasks; batch pricing available | Standard input $0.25/$0.50 (audio); output $1.50; Batch halves those | OFFICIAL citeturn14view0turn14view1turn14view2 |
| Gemini 2.5 Flash-Lite | Direct Gemini API | `gemini-2.5-flash-lite` | general API model (low-cost control) | Stable | 1M context (model list implies long-context class; exact in/out not shown here) | Batch supported; caching supported | Standard input $0.10; output $0.40; Batch input $0.05; output $0.20 | OFFICIAL citeturn14view1turn14view2 |
| Gemma 4 | Local/open-weight | Gemma 4 weights (various sizes) | local/open-weight model | New | 128K context (small/edge); 256K (larger) | Reasoning with configurable “thinking”; multimodal (varies by size) | Self-host cost = infra | OFFICIAL citeturn8search3turn8search7 |
| grok-4.20-reasoning | Direct xAI API | `grok-4.20-reasoning` | general API model | New | 2M context | Function calling + structured outputs listed; reasoning auto | Text in $2.00; image in $2.00; output $6.00 | OFFICIAL citeturn25view4turn25view5 |
| grok-4-1-fast-reasoning | Direct xAI API | `grok-4-1-fast-reasoning` | general API model (fast tool-caller) | Stable | 2M context | Designed for tool calling; Agent Tools API exists | Text in $0.20; output $0.50 | OFFICIAL citeturn25view4turn9search9 |
| Grok Code Fast 1 | Direct xAI API | `grok-code-fast-1` | coding-specialized API model | Stable | UNKNOWN | Coding prompt engineering guidance exists | Pricing not captured from first-party in this run | OFFICIAL for existence; UNKNOWN for pricing/limits citeturn9search1turn9search13 |
| openrouter/free | OpenRouter router surface | `openrouter/free` | aggregator-routed model; free-entry lane | Stable router | 200,000 context (router surface listing) | Filters pool by required features; selects at random | $0 | AGGREGATOR-OFFICIAL citeturn10search9turn10search16 |
| Step 3.5 Flash | Direct StepFun / open-source weights | Weights: Step-3.5-Flash repo; (OpenRouter ID: `stepfun/step-3.5-flash`) | local/open-weight model; aggregator-routed model | Released | Context 262,144 shown on OpenRouter model page | Tool-use claims vary by route | On OpenRouter: input $0.10; output $0.30; free variant exists | OFFICIAL (weights); AGGREGATOR-OFFICIAL (OpenRouter economics) citeturn17search9turn17search1turn11view0 |
| MiMo-V2-Pro | Direct Xiaomi API; OpenRouter route available | Official: MiMo-V2-Pro; pricing tiered by context size | general API model (agentic) + routed | New | 1M context; tiered pricing above 256K | Cache write temporarily free | Up to 256K: in $1/out $3; 256K–1M: in $2/out $6 | OFFICIAL citeturn17search2turn11view2 |
| MiniMax-M2.7 | Direct MiniMax API; OpenRouter route exists | `MiniMax-M2.7` (and `MiniMax-M2.7-highspeed`) | general API model; agentic/coding leaning | Current | Multiple models listed; some specify 200k context in docs | Tool calling and agent workflows emphasized | Pricing exists on MiniMax docs but not captured line-by-line here | OFFICIAL for lineup; UNKNOWN for exact token pricing in this run citeturn17search4turn17search0 |
| DeepSeek-V3.2 (API) | Direct DeepSeek API | `deepseek-chat`, `deepseek-reasoner` (mapped to DeepSeek-V3.2) | general API model (chat + reasoning variants) | Current | 128K context limit stated | Caching appears as pricing dimension (cache hit vs miss) | Exact numbers not captured from first-party lines here; pricing page exists | OFFICIAL for mapping + context; UNKNOWN for exact prices in this run citeturn16search6turn18search2 |
| Qwen3.6-Plus | Alibaba Cloud Model Studio (official API) | `qwen3.6-plus` | general API model; agentic coding positioned | New | 1M context claimed in official blog | Has OpenAI-compatible endpoints + tool surfaces in Model Studio | Pricing table exists; not fully extracted for this specific model in this run | OFFICIAL for availability + integration surface; UNKNOWN for price | citeturn18search1turn18search21turn18search4 |

**Batch support and economics matrix**

Batch matters for RTE because extraction pipelines are embarrassingly parallel and latency-insensitive. Instead of pretending “RPM” is your limiter, you build a queue.

| Provider surface | Batch support | Batch mode name | Published discount | Published queue/file limits | Notes | Evidence level |
|---|---|---|---|---|---|---|
| OpenAI API | Yes | Batch API | “Save 50% on inputs and outputs” and runs async over 24 hours | Data residency endpoints note `/v1/batches` persistence implications | Pair with prompt caching; watch ZDR incompatibilities for some features | OFFICIAL citeturn24view1turn13view2 |
| Gemini API | Yes | Batch API / Batch Mode | Batch pricing explicitly listed per model (often ~50% off) | Concurrent batch requests 100; input file 2GB; storage 20GB; per-model “enqueued tokens” caps | Quotas are separate from online calls | OFFICIAL citeturn14view1turn14view2turn8search4 |
| Vertex AI (Gemini) | Yes | Batch prediction | Request limits: up to 200,000 requests per batch job; file size limit 1GB; queue up to 72h before expiry | Vertex-specific batch semantics differ from Gemini API batch | Use when you need cloud-region processing guarantees | OFFICIAL citeturn8search12turn15search2 |
| Vertex AI (Claude partner models) | Yes | Batch predictions with Claude | Documented as batch predictions | Vertex quotas apply | This is not the “Anthropic direct” batch surface; it’s a Google-hosted route | OFFICIAL citeturn7search34 |
| OpenRouter | Not a batch API per se | N/A | N/A | N/A | You can parallelize client-side; provider limits still apply; fallbacks available | AGGREGATOR-OFFICIAL citeturn10search3turn10search27 |
| xAI | Yes (documented) | Batch API | Discount not captured here | Limits not captured here | xAI docs list Batch API as an advanced feature | OFFICIAL for existence; UNKNOWN for economics/limits citeturn9search1turn25view5 |

**Provider, country, and data-risk matrix**

Hard truth: “data risk” is mostly about **chain complexity + contractual controls + residency clarity**. If you can’t prove where data goes or who can log it, you don’t have compliance—you have coping.

Risk-level rubric applied:

- **LOW**: direct provider route + explicit ZDR/residency controls + short/defined retention and clear no-training posture.  
- **MODERATE**: direct provider route with no-training + limited retention, but residency ambiguous or controls gated.  
- **HIGH**: intermediary routing OR limited transparency OR geo/retention ambiguities that matter for your workload.  
- **VERY HIGH**: free routing pools, unknown providers, or known opaque chains where you cannot meaningfully enforce policy.

| Provider surface | Documented retention / logging | Residency / region controls | Intermediaries | Data risk level | Rationale | Evidence level |
|---|---|---|---|---|---|---|
| OpenAI API (direct) | Abuse monitoring retention shown as 30 days for `/v1/chat/completions` and `/v1/responses`; ZDR/MAM available by approval; some features incompatible with ZDR | Data residency regions include entity["country","United States","country"], entity["country","Canada","country"], entity["country","Japan","country"], entity["country","India","country"], entity["country","Singapore","country"], entity["country","South Korea","country"], entity["country","United Kingdom","country"], entity["country","Australia","country"], entity["country","United Arab Emirates","country"]; EU region includes EEA + entity["country","Switzerland","country"]; non‑US requires ZDR amendment | None | LOW–MODERATE (depends on controls enabled) | Strongest documented controls in this audit set; ZDR/residency gated by approval | OFFICIAL citeturn13view1turn13view2turn13view0 |
| Gemini API (direct) | Logs expire after 55 days by default (logs policy); Paid Services: Google does not use prompts/responses to improve products; Terms state prompts/responses may be logged for policy enforcement and “stored transiently or cached in any country” where Google or agents have facilities | No “per-request processing region” guarantee on Gemini API docs; batch quotas defined | None | MODERATE | No-training for paid is good; geography language (“any country”) is a residency red flag for regulated work unless you move to Vertex | OFFICIAL citeturn15search1turn15search5turn15search13 |
| Vertex AI (Gemini/Claude routes) | Governed under Google Cloud controls; data residency doc states ML processing occurs within region/multi-region where request is made (with caveats for endpoints not listed) | Stronger region control story (per-region processing guarantees described) | Google Cloud as intermediary between you and model author (for partner models) | MODERATE–LOW | Better residency story than Gemini API; but partner-model routes add a contract layer | OFFICIAL citeturn15search2turn7search34 |
| OpenRouter (aggregator) | OpenRouter states it doesn’t store prompts/responses unless you opt into logging; ZDR can restrict to “zero retention” endpoints; provider training/logging policies vary and are selectable; BYOK changes routing priority | Regional routing is available on paid/enterprise plans | Intermediary always present; and then a second hop to underlying provider(s) | MODERATE–HIGH (workload-dependent) | More moving parts; you can mitigate with ZDR + provider allowlists + BYOK, but chain is longer and failure modes are richer | AGGREGATOR-OFFICIAL citeturn10search14turn10search7turn10search0turn10search11turn10search34 |
| Alibaba Cloud Model Studio (Qwen3.6-Plus) | Not fully audited here (retention controls not extracted) | International mode: endpoints and data storage in Singapore; inference compute scheduled worldwide excluding Chinese mainland; China mode: endpoints/storage in Beijing and compute restricted to Chinese mainland | None (direct) | HIGH (until policy is audited) | Region info is good; policy/retention posture not captured here; treat as higher risk by default for sensitive repos | OFFICIAL (region statement); UNKNOWN (retention posture) citeturn18search4turn18search1 |
| xAI API (direct) | Data & Privacy page exists but not extracted here; model access may vary by geography | Regional endpoints exist (docs link) but details not captured | None | MODERATE (provisional) | Good first-party model/pricing docs; privacy/residency not fully captured in this run | OFFICIAL for docs existence; UNKNOWN for posture citeturn25view5turn24view6 |

## OpenRouter route analysis

**OpenRouter route analysis**

OpenRouter is not “just a reseller”; it’s a routing layer, and that changes your engineering leverage. The platform documents:

- **Provider routing** (load balancing, provider selection overrides via `provider` object). citeturn10search3  
- **Model fallbacks** across models (try alternates when down/rate-limited/refusals). citeturn10search27  
- **BYOK** semantics: BYOK endpoints are tried first and override provider ordering until exhausted. citeturn10search11  
- **ZDR controls**: both account-level and per-request (`zdr`) with endpoint-specific compatibility. citeturn10search7turn10search14  
- **Provider logging policies**: varies per provider; OpenRouter exposes structured policy metadata and lets you disallow “training on prompts” providers. citeturn10search0  
- **Free model routers**: `openrouter/free` selects a free model at random from a filtered pool, and the chosen underlying model is returned in the response. citeturn10search16turn10search9  
- **Pricing posture**: “We do not mark up provider pricing” and billing is per-model at posted rates; failed/fallback attempts are not billed. citeturn10search34turn10search27  

### What’s actually “top” on OpenRouter right now (and why it matters)

OpenRouter’s own rankings show that the top weekly token consumption is not dominated by the US frontier labs—Chinese and “unconventional” entrants are leading by usage. The current published top-10 includes Qwen3.6 Plus (free) at 6.27T tokens, DeepSeek V3.2 at 1.22T, Step 3.5 Flash (free) at 1.19T, MiniMax M2.7 at 1.15T, MiMo V2 Pro at 1.1T, Claude Sonnet 4.6 at 1.07T, Claude Opus 4.6 at 1.02T, Gemini 3 Flash Preview at 992B, and Kimi K2.5 0127 at 636B. citeturn11view0  

That’s not an endorsement; it’s a routing fact. If you want “future automatic portfolio updates,” your registry should ingest OpenRouter rankings and flag any model with sustained high usage share as a candidate for controlled evaluation—**but only after policy/risk checks**. citeturn11view0turn10search0turn10search7  

### Does OpenRouter meaningfully change cost, limits, uptime, latency?

It can, but only if you use it intentionally:

- **Uptime/fallback behaviour:** OpenRouter explicitly routes across providers by default and supports model fallbacks; this can outperform single-provider uptime if configured well. citeturn10search3turn10search27  
- **Rate limits:** OpenRouter’s own free-tier limits are explicitly defined (50 requests/day for free users per FAQ; pricing page lists free-user limits like 50/day and 20 RPM), while pay-as-you-go may have no platform-level limits on paid models (provider limits still exist). citeturn10search6turn10search34  
- **Data risk:** OpenRouter itself claims ZDR posture and no prompt storage unless opt-in, but underlying provider policies still govern, and routing adds an intermediary by definition. citeturn10search14turn10search0turn10search7  
- **Cost:** OpenRouter states it does not mark up provider pricing, and it exposes provider-specific effective pricing on some model pages (still an aggregator fact, not first-party). citeturn10search34turn10search26  

## Open and unconventional ecosystems

**Open/open-weight and unconventional-provider analysis**

This section focuses on candidates that have evidence of either (a) serious usage in routing ecosystems, (b) notable price/performance, or (c) strong agent/coding adoption. “Trendy but unsupported” is excluded by design.

### Open-weight / local candidates that are real (and worth your time)

- **gpt-oss-120b / gpt-oss-20b**: OpenAI-published open-weight models under Apache 2.0, both advertising 131,072 context and 131,072 max output tokens, with “agentic capabilities” (function calling, browsing, Python, structured outputs) positioned as native abilities. Treat tool execution as a host/runtime concern, not magic. citeturn21view1turn21view4  
  - Deployment practicality (INFERRED): 20B-class is plausible on a single high-VRAM GPU with quantization; 120B-class wants datacenter-grade GPU(s). Don’t benchmark these without fixing quantization + runtime, or you’ll benchmark your own incompetence.  
- **Gemma 4**: Google DeepMind open-weight family with 128K–256K contexts depending on size, and explicit “agentic workflow” positioning. citeturn8search3turn8search7turn8search15  
- **Llama 4 (Scout/Maverick)**: Meta’s open-weight multimodal line; model card docs exist; licensing is “community license” rather than permissive Apache. (Licensing constraints can be operationally more important than benchmark deltas.) citeturn16search0turn16search8turn16search12  
- **Devstral / Devstral 2**: Mistral’s coding/agentic family; Devstral 2 announced with two sizes and “free to use via API” at launch; Devstral (original) also exists with Apache 2.0 and an API name `devstral-small-2505` published by Mistral. citeturn18search3turn18search7  
- **Step 3.5 Flash**: StepFun open-source MoE, with explicit agentic/reasoning positioning and open weights on GitHub; OpenRouter shows a “free” variant and significant usage. citeturn17search9turn11view0turn17search1  

### Unconventional hosted candidates with unusually strong evidence

These show up as top weekly usage on OpenRouter (evidence of real deployment), or have first-party APIs with long-context and agentic claims:

- **MiMo-V2-Pro** (Xiaomi): first-party page publishes 1M context and tiered pricing by context range ($1/$3 up to 256K; $2/$6 up to 1M) and explicitly compares to Claude pricing. citeturn17search2turn11view0  
- **MiniMax-M2.7 / M2.5**: first-party docs position M2.7 as SOTA across programming/tool calling/search and list “highspeed” variants; OpenRouter shows huge weekly usage for M2.7/M2.5. citeturn17search0turn17search4turn11view0  
- **Qwen3.6-Plus** (Alibaba): official blog says it’s generally available via Alibaba Cloud Model Studio API; Model Studio docs show clear “International vs Chinese mainland” deployment modes with endpoint/data storage regions and inference scheduling constraints. citeturn18search1turn18search4turn18search5  
- **DeepSeek-V3.2**: first-party DeepSeek API docs map `deepseek-chat` and `deepseek-reasoner` to DeepSeek-V3.2 and state a 128K context limit for those endpoints. citeturn16search6turn18search2  
- **Kimi K2.5**: first-party platform claims K2.5 API supports 256K long context and tool calling; OpenRouter aligns on model presence and high usage. citeturn17search11turn11view0  
- **GLM-5 via Z.AI**: first-party pricing page exists for GLM family and shows token pricing; OpenRouter lists `z-ai/glm-5` as an available endpoint. (Treat “Z.AI vs Zhipu” naming carefully; don’t merge until you have first-party corporate mapping.) citeturn16search11turn16search3  

## RTE and OpenClaw suitability shortlists

**RTE suitability shortlist**

RTE is basically a factory: you want repeatability, schema correctness, and predictable escalation when something breaks.

- **Premium / highest-reliability lane:** GPT-5.4 (direct), Claude Opus 4.6 (direct or Bedrock where 1M context is documented), Gemini 3.1 Pro Preview (paid tier, direct Gemini API; or Vertex for region control). citeturn26view0turn7search37turn14view0turn14view1  
- **Balanced production lane:** GPT-5.4 mini, Claude Sonnet 4.6, Gemini 3 Flash Preview. citeturn26view0turn7search26turn14view0  
- **Low-cost production lane:** GPT-5.4 nano, Gemini 2.5 Flash-Lite, (plus one “cheap but strong” routed model that you explicitly risk-accept). citeturn26view0turn14view1turn11view0  
- **Structured extraction lane (strict JSON):** Prefer routes/models that explicitly support structured outputs and function calling as first-party guarantees; xAI documents structured outputs “with tools” for Grok 4 family. citeturn9search20turn25view5turn13view2  
- **Citation-heavy work:** Use explicit web/grounding tools: OpenAI web search tool is separately priced; Gemini grounding with Google Search is separately billed; OpenRouter also routes models with tool/search capability but must be constrained by policy. citeturn24view1turn14view1turn10search3turn10search0  
- **Low-cost batch lanes:** OpenAI Batch API publishes 50% savings; Gemini Batch pricing is published per model and quotas are explicit. citeturn24view1turn14view1turn14view2  
- **Free-entry lanes:** `openrouter/free` + specific `:free` variants where the workload is non-sensitive and you can tolerate volatility. citeturn10search16turn10search30  

**OpenClaw suitability shortlist**

OpenClaw roles assume an agent runtime that does tool calls, iterates, and must not collapse under long prompts.

Rating scale required by user: **UNSUITABLE**, **EXPERIMENTAL ONLY**, **VIABLE SECONDARY**, **VIABLE PRIMARY**, **STRONG PRIMARY**.

- **OpenClaw primary-agent lane (STRONG PRIMARY):**  
  - GPT-5.4 (direct) — best-documented flagship economics + caching; pair with ZDR/residency if repo sensitivity demands it. citeturn26view0turn13view1turn23search0  
  - Claude Sonnet 4.6 — explicitly positioned for coding/agents; prompt caching exists and is ZDR-eligible in Anthropic docs. citeturn7search26turn23search1  
  - grok-4-1-fast-reasoning — very low token pricing for 2M context; explicitly launched as best tool-calling model with Agent Tools API. citeturn25view4turn9search9  
  - Gemini 3 Flash Preview — 1M/64k in/out, tuned for speed/value and agentic workflows with thinking controls. citeturn14view0turn14view1  

- **OpenClaw primary-agent lane (VIABLE PRIMARY, but governance-sensitive):**  
  - Qwen3.6-Plus via Alibaba Model Studio — strong long-context and explicit “OpenAI-compatible endpoints + built-in tools” surface in Model Studio docs, but governance posture was not fully extracted here. citeturn18search1turn18search21turn18search4  
  - MiMo-V2-Pro (direct) — long context and competitive pricing; treat privacy/retention as HIGH until policy is audited. citeturn17search2turn11view0  

- **OpenClaw cheap-subagent lane (VIABLE SECONDARY):**  
  - GPT-5.4 nano, Gemini 2.5 Flash-Lite, Gemini 3.1 Flash-Lite Preview (batch for swarm jobs), plus selected OpenRouter-routed cheap models when risk-accepted. citeturn26view0turn14view1turn10search3turn11view0  

- **OpenClaw local fallback lane (EXPERIMENTAL ONLY → VIABLE SECONDARY depending on ops):**  
  - gpt-oss-20b, Gemma 4, Devstral Small 2 / Devstral small — viable if you can standardize runtime, quantization, and tool-call formatting; otherwise they become “randomness generators with electricity bills.” citeturn21view4turn8search3turn18search3turn18search7  

**Free / low-cost / watchlist shortlist**

- **Free-entry lane:** `openrouter/free` (random free pool) and `:free` variants for targeted testing. This is for sandboxing, not for sensitive repo payloads. citeturn10search16turn10search30  
- **Near-zero cost (paid but tiny):** Gemini 2.5 Flash-Lite (not free, but extremely low cost), GPT-5.4 nano. citeturn14view1turn26view0  
- **Watchlist (high usage, needs governance verification):** Qwen3.6 Plus (free), DeepSeek V3.2, MiniMax M2.7, Kimi K2.5, MiMo V2 Pro, Step 3.5 Flash (free). These are important because they dominate OpenRouter usage, not because marketing says so. citeturn11view0  

**Controls and baseline models to keep**

Controls are not “old models you forgot to delete”; they’re anchors to detect regression and route drift.

- **Non-reasoning control:** GPT-4.1 (listed as “smartest non-reasoning model”). citeturn19view0  
- **Small-model control:** GPT-4o mini (widely used on OpenRouter; cheap and stable baseline). citeturn11view2turn19view0  
- **Long-context + low-cost control:** Gemini 2.5 Flash-Lite (publishable pricing + batch). citeturn14view1turn14view2  
- **Agentic/coding control:** Claude Sonnet 4.6 and/or GPT-5.3-Codex (one from each ecosystem if you care about cross-provider drift). citeturn7search26turn2view0  
- **Aggregator control:** `openrouter/free` for “free lane health checks” (your harness should detect which underlying model got selected). citeturn10search16turn10search9  

## Benchmarking unknowns and harness design

**Unknowns requiring live benchmarking**

Documentation will not save you from reality in these areas (so stop pretending).

- **True schema reliability under adversarial inputs** (nested JSON, long lists, partial retries, tool-call interleaving). Docs rarely quantify this. (UNKNOWN)  
- **Retry stability** (does the model “repair” or “rewrite”? does it drift schemas under pressure?). (UNKNOWN)  
- **Omission behaviour** in extraction (silent drops vs explicit “missing” fields), especially under long contexts. (UNKNOWN)  
- **Latency under load by route** (direct vs OpenRouter vs cloud platform). Provider routing and quota contention dominate this in practice. citeturn10search3turn14view2  
- **Tool-calling robustness** across long agent loops (100+ tool calls): xAI and some others market this, but you must test in your own harness with your own tools. citeturn9search9turn25view5  
- **Effective economics under caching and batch**: caching hit rates and batch queue behaviour determine actual $/task, not list prices. citeturn23search0turn14view2turn24view1  
- **Route-specific quality deltas** (same “model name” across providers can behave differently due to snapshots, safety layers, or hidden system prompts). (UNKNOWN)  
- **Subscription-surface economics**: ChatGPT plan pages in this run did not expose numeric prices in parseable HTML (values appear non-textual), so you must capture those manually if you want $/seat comparisons. citeturn27view0turn28view0  

**Recommended inclusions for benchmark harness design**

Your benchmark harness should be built like a routing lab, not a leaderboard toy.

- **Surface-normalized request schema:**  
  - Normalize: messages, tool definitions, structured output schema, “store”/state toggles, and caching/batch settings per provider. citeturn13view2turn14view1turn10search3  
- **Route-level metadata capture:**  
  - Record: provider route (`direct`, `openrouter`, `vertex`, `bedrock`), region/endpoint prefix, ZDR/residency flags, and any fallback/provider selection decisions. citeturn13view0turn10search3turn10search7  
- **Cost accounting that matches provider semantics:**  
  - Separate: input vs cached input vs output; model-specific long-context tiers (OpenAI pricing notes “standard… under 270K” and 10% uplift on residency endpoints). citeturn26view0turn13view1turn14view1  
- **Batch harness module:**  
  - Create parallel benchmarks for synchronous vs batch; Gemini batch quotas are explicit; OpenAI batch discount is explicit. citeturn14view2turn24view1  
- **Agent-loop benchmark suite (OpenClaw-specific):**  
  - Track: tool-call success rate, state drift, latency per loop, and “recovery after tool failure.” Use fixed, replayable tool outputs to isolate model behaviour. (UNKNOWN, but required)  
- **Extraction suite (RTE-specific):**  
  - Include: noisy repos, partial diffs, missing files, conflicting claims, and “must emit schema even when uncertain.” Then score JSON validity + field completeness + citation grounding. (UNKNOWN, but required)  
- **Automatic portfolio updates:**  
  - Pull and diff: OpenAI model catalog pages, Gemini model/pricing tables, OpenRouter rankings + free-model set changes; flag new entrants that exceed usage thresholds or beat price-performance baselines. citeturn19view0turn14view0turn11view0turn10search16  

**Appendix: source-quality notes and evidence confidence**

- **OpenAI official docs quality:** High for model existence, pricing (API Pricing page), data controls (retention/ZDR/residency), and caching; region table explicitly enumerates domain prefixes and eligibility conditions. citeturn26view0turn13view1turn13view2turn23search0  
- **Gemini official docs quality:** High for model IDs, in/out context, pricing tables (including batch/flex/priority), batch quotas, and explicit statements about paid-tier training restrictions; Terms language about transient storage “in any country” is a governance-critical detail. citeturn14view0turn14view1turn14view2turn15search5turn15search13  
- **OpenRouter docs quality:** High for routing mechanics, ZDR/provider logging controls, BYOK semantics, and free-router behaviour; rankings are a strong signal for ecosystem importance but not automatically a quality/safety endorsement. citeturn10search3turn10search7turn10search0turn10search11turn11view0turn10search16  
- **xAI docs quality:** High for model lineup, context windows, features, and pricing tables; some privacy/residency posture was not extracted in this run and remains a required follow-up. citeturn25view4turn25view5  
- **Anthropic pricing page issue:** In this run, the Anthropic pricing page content appeared partially dynamic (“Loading…”) and did not expose the full base token pricing table in captured text; therefore some pricing entries above rely on other first-party statements (e.g., Sonnet 4.6 pricing line) plus feature docs (prompt caching). Treat gaps as **UNKNOWN** until captured from a stable first-party table or console export. citeturn24view4turn7search26turn23search1  
- **ChatGPT plan pricing numeric values:** The ChatGPT pricing page did not contain parseable currency figures in captured text (no `$`/`USD` matches), so numeric subscription pricing is **UNKNOWN** in this audit output despite plan feature descriptions being available. citeturn28view0turn27view0