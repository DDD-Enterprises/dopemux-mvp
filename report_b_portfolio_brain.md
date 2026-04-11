# Dopemux RTE Model Portfolio and Routing Brain

## Executive summary

This research is scoped to a **production routing portfolio** for the Dopemux Repo Truth Extractor (RTE): step-scoped execution (`--phase`, `--step`), hard cost caps (`--max-cost-usd`), and a validator gate (your “pre-live” validator) where **structured JSON reliability** matters more than vibes. The architecture constraints imply a routing brain that treats “JSON compliance” as a first-class capability, not a nice-to-have. citeturn24search0turn1search5

The current state of the model market (as of **April 5, 2026**) makes one design choice painfully obvious:

- **For strict schema JSON** (manifests, ledgers, coverage rollups), use models that explicitly support **json_schema** / structured outputs. OpenRouter supports `response_format: { type: "json_schema", ... }` for compatible models, and OpenAI models expose structured outputs support at the model level. citeturn24search0turn10search5turn10search3  
- **Do not “premium” your way into JSON** with OpenAI’s top “pro” variant: **`gpt-5.4-pro` does _not_ support structured outputs** per its model card, so it’s the wrong hammer for JSON-critical nails. citeturn10search0turn25search1  
- **Deprecation risk is not theoretical**. Google’s Gemini 2.5 Pro has an “earliest shutdown” in **June 2026**, which is close enough to be operational risk if you bake it into default production routing today. citeturn23search0  

Recommended top-level strategy:

- **Hybrid stack (recommended):**
  - Default: **OpenRouter** for cost/uptime elasticity + structured outputs + provider routing controls. citeturn24search2turn24search5turn24search0  
  - “Truth core” steps (JSON-critical + validator): **direct provider** where possible for predictability, plus OpenRouter as a fallback lane. This is especially relevant when you need consistent behavior across runs and want to minimize silent provider variance. citeturn24search2  

If you want a ruthless guiding principle: **don’t spend premium tokens to get prettier hallucinations. Spend to reduce retries, schema breaks, and validator failures.**

## Current model inventory by provider

The tables below focus on **text/vision general models** relevant to RTE workloads. Image/video generation and niche modalities are excluded unless they affect tool/JSON behavior.

### entity["company","OpenAI","ai company, us"]

OpenAI currently exposes a clear frontier family (GPT‑5.4) plus cheaper legacy GPT‑5 variants. Model cards explicitly state **pricing**, **context**, and whether **Structured outputs** are supported. citeturn10search5turn10search3turn9view0

| Direct API model ID | Lifecycle status | Strengths for RTE | Weaknesses / risks | Structured outputs | Tool/function calling | Context | Pricing (input/output per 1M tokens) | OpenRouter availability |
|---|---|---|---|---|---|---:|---:|---|
| `gpt-5.4` | GA (default) | Best “generalist for hard work”: long context (1.05M), broad tool support; structured outputs supported | More expensive than small models; long-context prompts >272K have surcharges | Supported citeturn10search3 | Supported citeturn10search3 | 1,050,000 citeturn10search3 | $2.50 / $15.00 citeturn10search3 | Yes (`openai/gpt-5.4`) citeturn4search0 |
| `gpt-5.4-mini` | GA (default) | Strong cost/perf for high-throughput extraction; structured outputs supported | Less headroom than `gpt-5.4` on gnarly cross-file contradictions | Supported citeturn5search14 | Supported citeturn5search14 | 400,000 citeturn5search14 | $0.75 / $4.50 citeturn5search14 | Yes (`openai/gpt-5.4-mini`) citeturn5search0 |
| `gpt-5.4-nano` | GA (default) | Cheap, fast; explicitly positioned for classification/data extraction/ranking | Lower reasoning strength; more likely to require escalation for ambiguous code semantics | Supported citeturn25search11 | Supported citeturn25search11 | 400,000 citeturn25search11 | $0.20 / $1.25 citeturn25search11 | Yes (`openai/gpt-5.4-nano`) citeturn5search1 |
| `gpt-5-mini` | GA (default) | Very low-cost general runner; structured outputs supported | Older cutoff (May 2024); OpenAI itself recommends newer 5.4 mini for new workloads | Supported citeturn10search2 | Supported citeturn10search2 | 400,000 citeturn10search2 | $0.25 / $2.00 citeturn10search2 | Likely yes (commonly mirrored) |
| `gpt-5-nano` | GA (default) | Ultra-cheap routing/tagging; structured outputs supported | Older cutoff; weakest reasoning; use only where errors are cheap | Supported citeturn9view0 | Supported citeturn9view0 | 400,000 citeturn9view0 | $0.05 / $0.40 citeturn9view0 | Likely yes (commonly mirrored) |
| `gpt-5.4-pro` | GA (default) | Maximum “think harder” behavior for long, complex tasks | **Structured outputs not supported** → not safe for JSON-critical steps; very expensive | **Not supported** citeturn10search0 | Supported citeturn10search0 | 1,050,000 citeturn10search0 | $30 / $180 citeturn10search0 | Yes (`openai/gpt-5.4-pro`) exists in OpenRouter catalog citeturn5search15 |

Deprecation note: OpenAI’s launch post states **GPT‑5.2 Thinking** retires **June 5, 2026** (ChatGPT), which is a canary for fleet churn; don’t anchor long-lived production routing to “legacy thinking” SKUs. citeturn4search2

### entity["company","Anthropic","ai company, us"]

Claude 4.6 variants are explicitly positioned for agents/coding and long context. Anthropic’s docs provide **model lifecycle** (active/legacy/deprecated) with “not sooner than” retirement guidance. citeturn21view0turn20search6turn26search3

| Direct API model ID | Lifecycle status | Strengths for RTE | Weaknesses / risks | Structured outputs | Tool/function calling | Context | Pricing (input/output per 1M tokens) | OpenRouter availability |
|---|---|---|---|---|---|---:|---:|---|
| `claude-sonnet-4-6` | Active | Strong coding/agent balance; 1M context (beta on API); max output 64K | More expensive than cheap extractors; long context is “beta” on API | Supported via Claude API features (and OpenRouter structured outputs where supported) citeturn20search6turn24search0 | Supported (Claude API features) citeturn20search6 | 1,000,000 citeturn20search6 | $3 / $15 citeturn26search3turn20search1 | Yes (`anthropic/claude-…4.6…`) citeturn7search0turn24search2 |
| `claude-opus-4-6` | Active | Highest Claude capability; strong long-horizon coding; 1M context (beta), 128K output tokens | Pricier than Sonnet; use only when escalation is justified | Supported via Claude API features / OpenRouter structured outputs | Supported citeturn20search6 | 1,000,000 citeturn20search6 | $5 / $25 citeturn26search3turn26search1 | Yes (`anthropic/claude-opus-4.6`) citeturn7search0 |
| `claude-haiku-4-5-20251001` | Active | Fast, smaller Claude; good for cheap classification/extraction where Claude-style writing helps | More expensive than OpenAI nano-tier; less ideal as “ultra cheap” | Supported (Claude API features) | Supported | 200K-class per older docs; lifecycle active | $1 / $5 citeturn26search3 | Usually available via OpenRouter catalogs |

Lifecycle guarantee: Anthropic lists “not sooner than” retirement dates per model (e.g., Sonnet 4.6 not sooner than Feb 17, 2027). That’s unusually valuable for production stability planning. citeturn21view0

### entity["company","Google","technology company, us"]

Google’s Gemini API has **explicit deprecations/shutdown schedules** for stable models. Gemini 3 series is currently **preview** (per the Gemini 3 guide and model pages). citeturn23search0turn23search9turn23search3

Key operational fact for routing: **Gemini 2.5 Pro’s earliest shutdown is June 2026**, with recommended replacement `gemini-3-pro`. That’s a short runway from the current date. citeturn23search0

| Direct API model code | Lifecycle status | Strengths for RTE | Weaknesses / risks | Structured outputs | Function calling | Context | Pricing (input/output per 1M tokens) | OpenRouter availability |
|---|---|---|---|---|---|---:|---:|---|
| `gemini-3-pro-preview` | Preview | 1M input / 64K output; supports structured outputs, function calling, file search, caching, Batch API | Preview drift risk; not a “locked” behavior baseline | Supported citeturn23search3 | Supported citeturn23search3 | 1,048,576 in / 65,536 out citeturn23search3 | $2 / $12 (<200k) tiered prices citeturn23search9turn11view0 | Often yes via OpenRouter (`google/gemini-3-pro-preview`) citeturn24search2 |
| `gemini-3-flash-preview` | Preview | “Pro-level at Flash speed” positioning; structured outputs supported | Preview drift; less predictable for validator steps | Supported citeturn23search3 | Supported citeturn23search3 | 1M / 64K citeturn23search9 | $0.50 / $3.00 citeturn23search9 | Often yes via OpenRouter |
| `gemini-2.5-flash-lite` | GA (but on a deprecation clock) | Very cheap; high throughput | Google forum reports of repetition loops in Flash‑Lite class in some scenarios; deprecation earliest July 2026 | Supported citeturn23search0turn23search3 | Supported citeturn23search3 | 1,048,576 in class citeturn5search4 | Commonly ~$0.10 / $0.40 via OpenRouter citeturn5search4 | Yes (`google/gemini-2.5-flash-lite`) citeturn5search4 |
| `gemini-2.5-pro` | GA (but “earliest June 2026” shutdown) | Strong thinking model; long-context reasoning; good code/repo analysis | **Earliest June 2026 shutdown** → don’t make it your long-lived default | Supported | Supported | Long context | Pricing varies by platform; OpenRouter lists $1.25 / $10 | Yes (`google/gemini-2.5-pro`) citeturn7search4 |

Deprecation reality check: Google explicitly lists shutdown schedules, and stable Gemini models can have “earliest” shutdown dates about a year after release. Bake this into routing configs as a **migration trigger**, not a surprise outage. citeturn23search0turn23search5

### entity["company","xAI","ai company, us"]

xAI now publishes a straightforward model/pricing table on its API page including Grok 4.20 and Grok 4.1 Fast variants (reasoning and non-reasoning). citeturn18view0turn12view0

| Direct API model ID | Lifecycle status | Strengths for RTE | Weaknesses / risks | Structured outputs | Function calling | Context | Pricing (input/output per 1M tokens) | OpenRouter availability |
|---|---|---|---|---|---|---:|---:|---|
| `grok-4.20-reasoning` | New | 2M context; lower hallucination positioning; agentic tool calling | Ecosystem maturity vs OpenAI/Anthropic; long-context pricing nuances unclear from static crawl | Supported (xAI docs list structured outputs for Grok 4.20) citeturn12view0 | Supported citeturn12view0 | 2,000,000 citeturn18view0turn12view0 | $2 / $6 citeturn18view0 | Yes (`x-ai/grok-4.20`) citeturn19view0 |
| `grok-4.20-non-reasoning` | New | Same price, “latency-sensitive” variant | Non-reasoning variant may fail harder reasoning cases sooner | Supported (feature family) | Supported | 2,000,000 citeturn18view0 | $2 / $6 citeturn18view0 | Yes (OpenRouter lists `x-ai/grok-4.20`) citeturn19view0 |
| `grok-4-1-fast-non-reasoning` | GA-ish | Ultra-cheap for 2M context; tool calling focus | Not a deep reasoner; treat as throughput model | — | — | 2,000,000 citeturn18view0 | $0.20 / $0.50 citeturn18view0 | Yes (OpenRouter has “Grok 4.1 Fast” lines) citeturn6search13 |

xAI also lists tool pricing (web search, code execution, etc.) which matters if you unintentionally enable server-side tools in a cost-capped pipeline. citeturn12view0

### entity["company","Mistral AI","ai company, france"]

Mistral provides explicit per-model pages with **model ID**, **price**, **context**, and feature support including **Structured Outputs** and **Function Calling**. citeturn22search2turn22search0turn22search1

| Direct API model ID | Lifecycle status | Strengths for RTE | Weaknesses / risks | Structured outputs | Function calling | Context | Pricing (input/output per 1M tokens) | OpenRouter availability |
|---|---|---|---|---|---|---:|---:|---|
| `mistral-small-2603` | GA (frontier small) | Strong price/perf; 262K context; good default cheap extractor | Less “frontier reasoning” than top-tier | Supported citeturn6search15 | Supported citeturn6search15 | 262,144 citeturn6search15 | $0.15 / $0.60 citeturn6search15 | Yes (`mistralai/mistral-small-2603`) citeturn6search15 |
| `mistral-large-2512` | GA | Open-weight frontier; structured outputs + function calling; 256K context | Higher cost than Small; still not “free” | Supported citeturn22search0 | Supported citeturn22search0 | 256K citeturn22search0 | $0.50 / $1.50 citeturn22search0 | Yes (OpenRouter lists Mistral Large 3 2512 family) citeturn7search2 |
| `mistral-medium-2508` | GA | Mid-tier with structured outputs; good for “strong default without OpenAI tax” | Costs approach some frontier models | Supported citeturn22search1 | Supported citeturn22search1 | 128K citeturn22search1 | $0.40 / $2.00 citeturn22search1 | Yes (OpenRouter catalog shows Medium 3.x variants) citeturn7search2 |
| `ministral-3b-2512` | GA | Very cheap; structured outputs supported; 256K context | Small model limits; best for routing/simple extraction | Supported citeturn22search7 | Supported citeturn22search7 | 256K citeturn22search7 | $0.10 / $0.10 citeturn22search7 | Typically yes via OpenRouter catalogs citeturn7search2 |

### entity["company","OpenRouter","ai routing platform"]

OpenRouter’s routing layer matters because it is **not just a reseller**; it is a **routing policy engine**.

Key capabilities for your RTE use case:

- **Provider routing controls** (`provider: { order, allow_fallbacks, require_parameters, … }`) and default load balancing that prioritizes price among stable providers. citeturn24search2turn24search1  
- **Structured outputs** with `response_format: { type: "json_schema", json_schema: { strict: true, … } }`. citeturn24search0turn24search9  
- Billing transparency and fees: OpenRouter says it passes through provider inference pricing without markup (but charges a fee when buying credits; and BYOK has a fee after a threshold). citeturn24search5  

Operational reality: OpenRouter can be the right “default lane” when you want uptime, arbitrage, and fallback across providers—**but it can also introduce variance** if you don’t lock provider slugs and require parameter support on JSON steps. citeturn24search1turn24search2

## RTE workload mapping and step types

Because your pipeline is multi-phase and step-scoped, the only sane portfolio is **per workload type**. Below is a routing map across your required workload categories (cheap routing, bulk extraction, strict JSON, cross-file reasoning, validation/judge, code-aware reasoning, repair passes, final synthesis). The “best model(s)” are the default picks; escalation ladders are defined later.

### Cheap routing and classification

Best models:
- `gpt-5-nano` (direct) or `openai/gpt-5.4-nano` (OpenRouter) when you still need structured outputs support cheaply. citeturn9view0turn5search1  
- `ministral-3b-2512` (Mistral) if you want a non-OpenAI ultra-cheap lane with structured outputs on Mistral’s platform. citeturn22search7  

Why:
- Cost dominates; errors must be cheap to correct.
- Still want structured outputs support so your routing annotations don’t break downstream parsers. citeturn9view0turn24search0  

Failure modes:
- Overconfident misclassification → wrong downstream model assignment → “silent quality loss” that the validator might not catch.
- Cheap models can also drift into partial JSON on long prompts; keep prompts tiny.

Cost sensitivity: extreme  
Latency sensitivity: high

### Bulk extraction

Best models:
- `gpt-5.4-nano` for high-volume, structured extraction when you can’t tolerate schema breakage. citeturn25search11  
- `mistral-small-2603` as a low-cost workhorse with structured outputs support. citeturn6search15  

Why:
- Both are priced for throughput.
- Both support structured outputs and function calling (required for reliable JSON extraction at scale). citeturn25search11turn6search15turn24search0  

Failure modes:
- Extraction omissions (missing facts) more common than hallucinated additions if schemas are strict.
- Long-context files can cause “field drop” where model truncates or underfills arrays—watch max_tokens and chunking.

Cost sensitivity: high  
Latency sensitivity: medium

### Strict structured JSON extraction

Best models:
- `gpt-5.4-mini` for “JSON under pressure” tasks. citeturn10search6  
- `gpt-5.4` for schemas requiring cross-file reasoning or heavy constraints. citeturn10search3  

Why:
- OpenAI model cards explicitly indicate structured outputs support (per model), and OpenAI’s structured outputs mechanism is designed to enforce schema compliance. citeturn10search3turn10search6turn1search5  

Failure modes:
- If you accidentally route to `gpt-5.4-pro`, you lose structured outputs support—this is how teams “mysteriously” get JSON failure spikes after a “premium upgrade.” citeturn10search0  

Cost sensitivity: medium  
Latency sensitivity: medium

### Cross-file and cross-doc reasoning

Best models:
- `gpt-5.4` as the OpenAI default for complex reasoning/coding with very long context. citeturn10search5turn10search3  
- `claude-sonnet-4-6` when you want Claude’s agentic/coding strengths at a lower price than Opus. citeturn20search6turn26search3  
- `claude-opus-4-6` as the expensive escalation for “this must be right.” citeturn26search1turn26search3  

Why (and why they beat cheaper):
- This category is where retries are brutally expensive; a slightly pricier model that “gets it on the first shot” is cheaper in total spend.
- Long context reduces expensive multi-pass stitching.

Failure modes:
- False coherence: models can produce plausible cross-file narratives that are not grounded. Your validator/judge must aggressively request citations to file paths/line refs (as your RTE likely already does).

Cost sensitivity: medium-low  
Latency sensitivity: low-medium

### Validation, judging, contradiction detection

Best models:
- `gpt-5.4` (structured outputs supported if you want JSON verdict objects). citeturn10search3  
- `claude-sonnet-4-6` as a second judge to reduce “single-model blind spots.” citeturn20search6  

Why:
- You want conservative models that can articulate contradictions and missing evidence.
- Dual-judge is often cheaper than repeated extraction reruns.

Failure modes:
- Validator false positives if your schema set is too strict or the model is too “policy compliant.” Tune judge prompts to demand evidence keys instead of vibes.

Cost sensitivity: medium  
Latency sensitivity: low

### Code-aware reasoning

Best models:
- `gpt-5.4-mini` for day-to-day code extraction and repo navigation. citeturn5search14turn10search5  
- `claude-sonnet-4-6` for complex codebase reasoning at scale. citeturn20search6turn20search1  

Why:
- Both are positioned for coding and agent workflows; Sonnet is explicitly marketed for complex codebase navigation and agents. citeturn20search1turn20search6  

Failure modes:
- Tool call mismatches (wrong file paths) if your step scaffolding doesn’t constrain.
- Long outputs can exceed downstream parser limits; use max_tokens and strict schemas.

Cost sensitivity: medium  
Latency sensitivity: medium

### Repair pass for malformed JSON and partial outputs

Best models:
- `gpt-5.4-nano` → `gpt-5.4-mini` escalation depending on complexity. citeturn25search11turn10search6  
- On OpenRouter-only stacks, use **Response Healing plugin** for non-streaming schema mode to reduce invalid JSON risk (but keep deterministic rules about when it’s allowed). citeturn24search0turn24search9  

Why:
- Repair is a structured-output task, not a “reason harder” task. You want cheap + strict schema.

Failure modes:
- Repair model “fixes” content by inventing missing fields. Mitigation: require `additionalProperties: false`, and require explicit `null` allowances only where appropriate.

Cost sensitivity: high  
Latency sensitivity: medium

### Final synthesis with high confidence

Best models:
- `gpt-5.4` for final cross-artifact synthesis and explanation, optionally in JSON + a human-readable summary. citeturn10search3  
- `claude-opus-4-6` as “premium final check” when the output has to survive hostile review. citeturn26search1turn26search3  

Why:
- This is where you pay to reduce risk, not to win a benchmark.

Failure modes:
- Overly polished narrative that hides uncertainty. Require “unknowns” and “evidence keys used” fields in schema.

Cost sensitivity: low  
Latency sensitivity: low

## Cost tier portfolio and phase-step assignment matrix

### Tier 0 ultra cheap

Primary: `gpt-5-nano`  
Fallback: `ministral-3b-2512`  
Escalation trigger: Only if the output gates downstream routing (e.g., it sets which files get extracted) and confidence is low.

Why it beats the next cheaper option:
- There basically is no cheaper mainstream model with explicit structured outputs support at this scale; the key is that `gpt-5-nano` supports structured outputs and function calling even at the bottom price tier. citeturn9view0  

Anti-patterns:
- Any step that produces an artifact consumed by the validator gate without a second pass.
- Cross-file reasoning.

### Tier 1 low cost default

Primary: `mistral-small-2603`  
Fallback: `gpt-5.4-nano`  
Escalation trigger: schema mismatch > 0, or contradiction flags, or partial output.

Why it beats the next cheaper option:
- Compared with true nano-class models, Mistral Small 4 class provides more headroom while staying extremely cheap ($0.15 / $0.60) and supports structured outputs. citeturn6search15turn22search2  

Anti-patterns:
- High-stakes judge/validator.
- Complex cross-file synthesis.

### Tier 2 strong default

Primary: `gpt-5.4-mini`  
Fallback: `claude-sonnet-4-6`  
Escalation trigger: JSON failure after one repair attempt, or validator failure attributable to reasoning not extraction.

Why it beats the next cheaper option:
- Compared to `gpt-5.4-nano`, `gpt-5.4-mini` buys a large jump in capability for a moderate cost increase, and is explicitly positioned as the “strongest mini … for coding … and subagents.” citeturn5search14turn10search5  

Anti-patterns:
- Pure routing tags (wasteful).
- Extremely long multi-document synthesis where `gpt-5.4` is cheaper than cascading retries.

### Tier 3 premium

Primary: `gpt-5.4`  
Fallback: `claude-opus-4-6`  
Escalation trigger: validator failure after re-run, cross-file contradictions, or high uncertainty in final synthesis.

Why it beats the next cheaper option:
- Compared with `gpt-5.4-mini`, the 1.05M context window and top capability reduces multi-pass stitching and rework. citeturn10search3turn10search5  
- Opus is more expensive ($5/$25) than GPT‑5.4 ($2.50/$15), so it’s strictly for cases where the cheaper model has already failed or where the cost of an error dwarfs token spend. citeturn26search3turn10search3  

Anti-patterns:
- JSON-only repair (use cheaper strict models).
- Any step where output cannot be validated.

### Phase-step assignment matrix

You didn’t provide the exact step list from `run_extraction_v5.py`, so the matrix below uses **production-friendly step archetypes** mapped to the step IDs you referenced (A1, A2, …). The intent is that you align these archetypes to your real step names/IDs (your pipeline already supports `--phase` and `--step`, so the mapping layer is the missing glue).

| phase | step | task_type | primary_model | fallback | escalation | routing_mode | cost_class | notes |
|---|---|---|---|---|---|---|---|---|
| A | A1 | Cheap routing / classification | `gpt-5-nano` | `ministral-3b-2512` | → Tier 1 if confidence low | cost_minimal | Tier 0 | Keep prompts tiny; output strict JSON tags citeturn9view0turn22search7 |
| A | A2 | Repo inventory → structured manifest JSON | `gpt-5.4-nano` | `mistral-small-2603` | → `gpt-5.4-mini` on schema errors | balanced | Tier 1 | This should feed RUN_MANIFEST-like artifacts; schema-critical citeturn25search11turn6search15 |
| A | A3 | Plan / file targeting (cross-file reasoning) | `gpt-5.4-mini` | `claude-sonnet-4-6` | → `gpt-5.4` if contradictions | balanced | Tier 2 | Must cite file paths + rationale; avoid preview models here citeturn10search6turn20search6 |
| B | B1 | Bulk extraction per file (strict JSON) | `mistral-small-2603` | `gpt-5.4-nano` | → `gpt-5.4-mini` if repeated failures | balanced | Tier 1 | Main spend sink; optimize retry discipline citeturn6search15turn25search11 |
| B | B2 | Code-aware extraction (APIs, config, interfaces) | `gpt-5.4-mini` | `claude-sonnet-4-6` | → `gpt-5.4` for hard cases | balanced | Tier 2 | Prefer OpenAI for schema reliability; Claude for tough codebase reasoning citeturn5search14turn20search6 |
| C | C1 | Cross-file linking + contradiction detection | `gpt-5.4` | `claude-sonnet-4-6` | → `claude-opus-4-6` | premium | Tier 3 | Only escalate if validator-sensitive or high-impact contradictions citeturn10search3turn26search3 |
| C | C2 | Final synthesis (high confidence) | `gpt-5.4` | `claude-opus-4-6` | none beyond Tier 3 | premium | Tier 3 | If output must be JSON: avoid `gpt-5.4-pro` (no structured outputs) citeturn10search0turn10search3 |
| D | D1 | Repair pass (malformed JSON) | `gpt-5.4-nano` | `gpt-5.4-mini` | → `gpt-5.4` only if semantics missing | balanced | Tier 1/2 | Schema mode + `additionalProperties:false`; one retry only citeturn25search11turn10search6 |
| D | D2 | Validator / judge gate | `gpt-5.4` | `claude-sonnet-4-6` | → `claude-opus-4-6` | premium | Tier 3 | Produce a strict JSON verdict object if the gate consumes JSON citeturn10search3turn26search3 |

## Routing policies, escalation logic, and provider strategy

### Routing policies

Policies are defined as **step-level mappings + deterministic fallbacks**. The three required policies are below.

#### balanced

Core intent: “Don’t be cheap. Don’t be stupid. Don’t burn money on retries.”

- Tier 0 only for A1 routing tags.
- Bulk extraction in Tier 1.
- Any schema-critical artifact step uses models with structured outputs support and forces `json_schema` mode (OpenRouter or direct).

OpenRouter settings for JSON steps (if using OpenRouter):
- `provider.require_parameters: true` so the request is only routed to providers that support required parameters (prevents silent dropping of `response_format`). citeturn24search1turn24search2  
- `response_format.type: "json_schema"` with `strict: true`. citeturn24search0turn24search9  

#### cost_minimal

Core intent: “Stay under cap even if coverage degrades.”

- Default Tier 0 and Tier 1 models.
- Hard limit: **no Tier 3 escalation** unless the validator would abort the run without it.

Guardrails:
- If budget remaining < 20%, disable cross-file “nice to have” steps and only run validator-critical repairs.

#### premium

Core intent: “Maximum reliability; fewer attempts.”

- Default Tier 2/3 models.
- Aggressive escalation on first schema mismatch or validator failure.
- Uses a second judge (Sonnet) on critical contradictions.

### Escalation logic

A production routing brain needs **deterministic** escalation. Below is the rule set designed to minimize retry churn under cost caps.

**Error classes assumed** (adapt to your actual error codes):
- `E_JSON_PARSE` (not valid JSON)
- `E_SCHEMA_MISMATCH` (valid JSON, fails schema)
- `E_PARTIAL_OUTPUT` (truncated / missing required keys)
- `E_PROVIDER_ERROR` (timeouts / 5xx / rate limits)
- `E_VALIDATION_FAIL` (validator rejects artifact)

**Rules:**

- JSON failure (`E_JSON_PARSE`) on a JSON-critical step  
  - Retry once with the *same* model but `max_tokens` reduced and “no prose” reinforcement.  
  - If it fails again: escalate one tier (nano → mini → gpt‑5.4).  
  - Never escalate to `gpt-5.4-pro` for JSON repair because it does not support structured outputs. citeturn10search0  

- Schema mismatch (`E_SCHEMA_MISMATCH`)  
  - No blind retries. Immediate repair pass with `gpt-5.4-nano` in schema mode.  
  - If still failing: escalate to `gpt-5.4-mini`.  

- Partial output (`E_PARTIAL_OUTPUT`)  
  - If token limit hit: retry once with higher `max_tokens` (same model).  
  - If token limit not hit: escalate (this is usually a capability failure, not truncation).

- Provider failure (`E_PROVIDER_ERROR`)  
  - If using OpenRouter: switch provider slugs (ordered list) and keep model constant. citeturn24search1turn24search2  
  - If direct: fail over to OpenRouter for the same model family (e.g., direct `gpt-5.4-mini` → `openai/gpt-5.4-mini`).

- Validation failure (`E_VALIDATION_FAIL`)  
  - Determine blame: extraction vs reasoning vs coverage.  
  - If extraction: re-run the failing step with one-tier escalation (Tier 1 → Tier 2).  
  - If reasoning/contradiction: run judge (`gpt-5.4`) + second judge (`claude-sonnet-4-6`) and only re-run extraction on artifacts they flag as unsupported.

- Cost nearing cap  
  - If projected remaining cost < cost of escalation: downgrade and produce an explicit “degraded mode” artifact.  
  - Critical exception: validator gate steps can escalate once if and only if the alternative is aborting the run.

### OpenRouter vs direct provider strategy

When OpenRouter is better:
- **Multi-provider fallback and uptime smoothing** (OpenRouter tracks provider health and routes accordingly). citeturn24search4turn24search2  
- **Provider selection and parameter enforcement** (require parameter support on JSON steps). citeturn24search1turn24search2  
- **Unified structured outputs and schema mode** when you use many providers behind one interface. citeturn24search0turn24search9  

When direct provider is better:
- **Predictable behavior** (fewer hidden provider differences).
- **Stable debugging** (provider errors map more directly to root cause).
- **Access to provider-specific features** that routers sometimes normalize imperfectly.

Hybrid (recommended):
- Default: OpenRouter for Tier 0–2 steps.  
- Direct: JSON-critical manifest/ledger artifacts + validator steps, with OpenRouter as a deterministic fallback lane.

## Spend and cost-cap strategy plus final portfolio recommendation

### Spend strategy under `--max-cost-usd`

The design goal is to prevent “death by retries” because retries are the silent killer of cost caps.

Step categories that should **never escalate** under tight budget:
- Pure routing tags (A1): if it fails, fall back to a default safe routing label and move on.
- Non-validator “nice-to-have” enrichments.

Steps that justify escalation:
- Any step that produces artifacts consumed by the validator gate (because failing late wastes the whole run).
- Cross-file contradiction resolution that would otherwise block final synthesis.

Concrete budget gates:
- **>60% budget remaining:** normal behavior (balanced).  
- **60–30%:** disable Tier 3 escalations except validator steps.  
- **30–10%:** force Tier 0/1; only one repair attempt per failing step.  
- **<10%:** abort early with explicit degraded-mode artifacts rather than thrashing.

### Final production portfolios

#### Direct-only stack

Use direct provider APIs only:

- Tier 0: `gpt-5-nano`
- Tier 1: `gpt-5.4-nano`
- Tier 2: `gpt-5.4-mini`
- Tier 3: `gpt-5.4` then `claude-opus-4-6` only if you accept running multiple providers directly

This is simplest but loses OpenRouter’s cross-provider uptime routing. citeturn10search3turn24search2

#### OpenRouter-only stack

Use OpenRouter model IDs only:

- Tier 0: `openai/gpt-5.4-nano` (or `openai/gpt-5-nano` if exposed)
- Tier 1: `mistralai/mistral-small-2603`
- Tier 2: `openai/gpt-5.4-mini`
- Tier 3: `openai/gpt-5.4` then `anthropic/claude-opus-4.6`

Must enable:
- `provider.require_parameters: true` on all schema steps
- `response_format: json_schema` with strict mode citeturn24search0turn24search2

#### Hybrid stack recommended

- OpenRouter for Tier 0–2 where possible.
- Direct OpenAI for schema-critical core artifacts (manifest/ledger) if you’ve historically seen provider variance.
- Direct Anthropic only for premium rescue; otherwise via OpenRouter.

This hybrid approach exploits OpenRouter’s routing and parameter enforcement while keeping the “truth-critical spine” on the most predictable endpoints. citeturn24search2turn24search1

## Config-ready JSON and confidence

### Config JSON

```json
{
  "tiers": [
    {
      "tier": 0,
      "name": "ultra_cheap",
      "primary_model": "gpt-5-nano",
      "fallback_model": "ministral-3b-2512",
      "intended_use": ["routing", "tagging", "cheap retries"],
      "escalation_trigger": ["low_confidence_routing", "downstream_gate_depends_on_tags"],
      "anti_patterns": ["cross_file_reasoning", "validator_outputs", "json_artifacts_without_repair_lane"]
    },
    {
      "tier": 1,
      "name": "low_cost_default",
      "primary_model": "mistral-small-2603",
      "fallback_model": "gpt-5.4-nano",
      "intended_use": ["bulk_extraction", "simple_structured_tasks"],
      "escalation_trigger": ["schema_mismatch", "partial_output", "repeat_failure_same_step"],
      "anti_patterns": ["final_synthesis", "high_stakes_judging"]
    },
    {
      "tier": 2,
      "name": "strong_default",
      "primary_model": "gpt-5.4-mini",
      "fallback_model": "claude-sonnet-4-6",
      "intended_use": ["json_under_pressure", "code_aware_reasoning", "moderate_cross_file_reasoning"],
      "escalation_trigger": ["second_schema_failure", "validator_fail_reasoning", "contradiction_detected"],
      "anti_patterns": ["pure_routing", "cheap_bulk_when_tier1_succeeds"]
    },
    {
      "tier": 3,
      "name": "premium",
      "primary_model": "gpt-5.4",
      "fallback_model": "claude-opus-4-6",
      "intended_use": ["hard_cross_file_reasoning", "validator_judging", "final_synthesis_high_confidence"],
      "escalation_trigger": ["validator_fail_persistent", "high_impact_contradiction", "missing_evidence_blocks_release"],
      "anti_patterns": ["json_repair_only", "high_volume_bulk_extraction"]
    }
  ],
  "phase_step_assignments": [
    {
      "phase": "A",
      "step": "A1",
      "task_type": "cheap_routing_classification",
      "primary_model": "gpt-5-nano",
      "fallback": "ministral-3b-2512",
      "escalation": "mistral-small-2603",
      "routing_mode": "cost_minimal",
      "cost_class": "tier0",
      "json_critical": true,
      "notes": "Keep prompts tiny; output strict JSON tags that drive downstream routing."
    },
    {
      "phase": "A",
      "step": "A2",
      "task_type": "repo_inventory_manifest_json",
      "primary_model": "gpt-5.4-nano",
      "fallback": "mistral-small-2603",
      "escalation": "gpt-5.4-mini",
      "routing_mode": "balanced",
      "cost_class": "tier1",
      "json_critical": true,
      "notes": "Produces manifest-like artifacts; schema mismatch triggers immediate repair lane."
    },
    {
      "phase": "A",
      "step": "A3",
      "task_type": "plan_and_targeting_cross_file",
      "primary_model": "gpt-5.4-mini",
      "fallback": "claude-sonnet-4-6",
      "escalation": "gpt-5.4",
      "routing_mode": "balanced",
      "cost_class": "tier2",
      "json_critical": true,
      "notes": "Must cite file paths and justify selection; avoid preview models by default."
    },
    {
      "phase": "B",
      "step": "B1",
      "task_type": "bulk_extraction_high_volume",
      "primary_model": "mistral-small-2603",
      "fallback": "gpt-5.4-nano",
      "escalation": "gpt-5.4-mini",
      "routing_mode": "balanced",
      "cost_class": "tier1",
      "json_critical": true,
      "notes": "Main spend sink; enforce strict schemas; cap retries."
    },
    {
      "phase": "B",
      "step": "B2",
      "task_type": "code_aware_extraction",
      "primary_model": "gpt-5.4-mini",
      "fallback": "claude-sonnet-4-6",
      "escalation": "gpt-5.4",
      "routing_mode": "balanced",
      "cost_class": "tier2",
      "json_critical": true,
      "notes": "Prefer structured outputs; constrain tool usage to repo files only."
    },
    {
      "phase": "C",
      "step": "C1",
      "task_type": "cross_file_linking_contradiction_detection",
      "primary_model": "gpt-5.4",
      "fallback": "claude-sonnet-4-6",
      "escalation": "claude-opus-4-6",
      "routing_mode": "premium",
      "cost_class": "tier3",
      "json_critical": true,
      "notes": "Escalate only on high-impact contradictions or validator dependency."
    },
    {
      "phase": "C",
      "step": "C2",
      "task_type": "final_synthesis_high_confidence",
      "primary_model": "gpt-5.4",
      "fallback": "claude-opus-4-6",
      "escalation": null,
      "routing_mode": "premium",
      "cost_class": "tier3",
      "json_critical": false,
      "notes": "If final output must be JSON, do not use gpt-5.4-pro (no structured outputs)."
    },
    {
      "phase": "D",
      "step": "D1",
      "task_type": "repair_json_malformed_or_partial",
      "primary_model": "gpt-5.4-nano",
      "fallback": "gpt-5.4-mini",
      "escalation": "gpt-5.4",
      "routing_mode": "balanced",
      "cost_class": "tier1",
      "json_critical": true,
      "notes": "One retry max; enforce additionalProperties=false."
    },
    {
      "phase": "D",
      "step": "D2",
      "task_type": "validator_judge_gate",
      "primary_model": "gpt-5.4",
      "fallback": "claude-sonnet-4-6",
      "escalation": "claude-opus-4-6",
      "routing_mode": "premium",
      "cost_class": "tier3",
      "json_critical": true,
      "notes": "Emit strict JSON verdict object with evidence keys."
    }
  ],
  "routing_policies": [
    {
      "name": "balanced_hybrid",
      "provider_mode": "hybrid",
      "default_provider": "openrouter",
      "step_overrides": {
        "A2": { "provider": "direct", "model": "gpt-5.4-nano" },
        "D2": { "provider": "direct", "model": "gpt-5.4" }
      },
      "json_mode": "json_schema_strict",
      "openrouter_provider_controls": {
        "require_parameters": true,
        "allow_fallbacks": true
      },
      "escalation_ladder": ["tier0", "tier1", "tier2", "tier3"]
    },
    {
      "name": "cost_minimal_hybrid",
      "provider_mode": "openrouter_preferred",
      "default_provider": "openrouter",
      "json_mode": "json_schema_strict",
      "openrouter_provider_controls": {
        "require_parameters": true,
        "allow_fallbacks": true
      },
      "caps": {
        "max_tier": 2,
        "no_tier3_except_steps": ["D2"]
      },
      "escalation_ladder": ["tier0", "tier1", "tier2"]
    },
    {
      "name": "premium_hybrid",
      "provider_mode": "hybrid",
      "default_provider": "direct",
      "fallback_provider": "openrouter",
      "json_mode": "json_schema_strict",
      "openrouter_provider_controls": {
        "require_parameters": true,
        "allow_fallbacks": true
      },
      "escalation_ladder": ["tier2", "tier3"]
    }
  ],
  "escalation_rules": [
    {
      "when": "E_JSON_PARSE",
      "action": [
        { "type": "retry", "max_attempts": 1, "same_model": true, "adjustments": ["lower_max_tokens", "reinforce_no_prose"] },
        { "type": "escalate_tier", "max_tiers": 1 }
      ]
    },
    {
      "when": "E_SCHEMA_MISMATCH",
      "action": [
        { "type": "repair_pass", "model": "gpt-5.4-nano", "schema_mode": "strict" },
        { "type": "escalate_model", "to": "gpt-5.4-mini" }
      ]
    },
    {
      "when": "E_PARTIAL_OUTPUT",
      "action": [
        { "type": "retry", "max_attempts": 1, "same_model": true, "adjustments": ["increase_max_tokens_if_truncated"] },
        { "type": "escalate_tier", "max_tiers": 1 }
      ]
    },
    {
      "when": "E_PROVIDER_ERROR",
      "action": [
        { "type": "switch_provider", "order": ["preferred", "fallbacks"], "lock_model": true }
      ]
    },
    {
      "when": "E_VALIDATION_FAIL",
      "action": [
        { "type": "classify_failure", "dimensions": ["extraction", "reasoning", "coverage"] },
        { "type": "rerun_targeted_steps", "max_steps": 3, "escalate_tier_if_needed": true }
      ]
    },
    {
      "when": "COST_NEAR_CAP",
      "thresholds": { "warn": 0.7, "degrade": 0.9 },
      "action": [
        { "type": "disable_escalation", "max_tier": 1, "except_steps": ["D2"] },
        { "type": "abort_on_retry_churn", "max_retries_per_step": 2 }
      ]
    }
  ],
  "provider_strategy": {
    "when_openrouter_is_better": [
      "multi_provider_fallback",
      "uptime_smoothing",
      "parameter_enforcement_for_json",
      "price_arbitrage"
    ],
    "when_direct_is_better": [
      "predictable_behavior",
      "debuggability",
      "stable_baselines_for_validator_steps"
    ],
    "hybrid_default": {
      "default_lane": "openrouter",
      "truth_core_steps": ["A2", "D2"],
      "premium_rescue": "direct_then_openrouter_fallback"
    }
  },
  "cost_cap_strategy": {
    "principles": [
      "never_die_by_retries",
      "escalate_only_when_gate_depends_on_it",
      "prefer_targeted_reruns_over_full_phase_reruns"
    ],
    "step_never_escalate": ["A1"],
    "step_can_escalate_once": ["A2", "D1", "D2"],
    "budget_gates": [
      { "remaining_fraction_gte": 0.6, "mode": "normal" },
      { "remaining_fraction_between": [0.3, 0.6], "mode": "no_tier3_except_validator" },
      { "remaining_fraction_between": [0.1, 0.3], "mode": "tier0_1_only_one_repair" },
      { "remaining_fraction_lt": 0.1, "mode": "abort_with_degraded_artifacts" }
    ]
  },
  "monthly_revalidation_targets": [
    "json_parse_failure_rate_by_step_and_model",
    "schema_mismatch_rate_by_step_and_model",
    "provider_uptime_and_error_rate_by_model",
    "cost_per_successful_step_and_retry_churn",
    "deprecation_watchlist_scan_for_google_and_anthropic",
    "pricing_drift_check_against_pricing_yaml"
  ]
}
```

### Confidence and unknowns

High confidence (supported by current provider docs and routing-layer docs):
- OpenAI model IDs, pricing, context windows, and structured outputs support per model card. citeturn10search3turn5search14turn9view0  
- Anthropic model IDs, pricing table, and lifecycle status (“not sooner than” retirement dates). citeturn26search3turn21view0turn20search6  
- OpenRouter structured outputs (`json_schema` mode), provider routing controls, and billing model. citeturn24search0turn24search2turn24search5  
- Google Gemini 3 preview model codes/capabilities and Google’s explicit deprecation schedules (notably Gemini 2.5 Pro). citeturn23search3turn23search9turn23search0  
- xAI Grok 4.20 and Grok 4.1 Fast model IDs, context, and token pricing from xAI’s API page. citeturn18view0turn12view0  
- Mistral model IDs and structured outputs support from Mistral docs. citeturn22search0turn22search2  

Medium confidence (requires your repo to finalize):
- Exact mapping of your real RTE step IDs (A1/A2/…) to the archetypes in the matrix. The routing brain is implementable, but the exact step table should be aligned to your `run_extraction_v5.py` step registry.  

Low confidence / watch items (market volatility):
- Google model stability: Gemini 3 is preview and may drift; Gemini 2.5 models are near their “earliest shutdown” windows. citeturn23search0turn23search9  
- Any claims about “lowest hallucination” or benchmark superiority should not be treated as production truth without your own eval harness; treat them as vendor framing unless validated in your pipeline.