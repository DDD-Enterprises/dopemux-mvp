# DR-05 Report: API Fallback, Privacy, and Cost

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Track:** `DR-05-API-FALLBACK-PRIVACY-AND-COST`  
**Research date:** 2026-07-13  
**Status:** `COMPLETE_WITH_UNKNOWNS`

## 1. Executive disposition

| Label | Material claim |
|---|---|
| `OBSERVED` | The local capability probe was static-only. No model, OpenRouter, provider API, account-login, or credential test was run. OpenRouter remains a future `API_FALLBACK` route, not an observed executable lane. See `PROBE_SUMMARY.md`, `ROUTING_CONSTRAINTS.md`, `MODEL_IDENTITY_OBSERVATIONS.json`, and `BLOCKERS_AND_UNKNOWNS.json`. |
| `CLAIMED` | Current official plan documentation exposes rolling windows, usage bars, reset notifications, dynamic compute-based limits, shared agentic pools, fair-use qualifications, or credits. It does not provide a stable cross-vendor conversion from each subscription request to a comparable unit of plan credit. |
| `INFERRED` | Subscription plans are unsuitable as the sole substrate for unattended, high-frequency audit automation because their limits and marginal consumption are not deterministic enough for pre-run admission control, cost proof, or reliable queue planning. |
| `CLAIMED` | Direct APIs expose substantially stronger governance surfaces: structured output controls, request or response identifiers, token or cost usage, rate-limit telemetry, model metadata, and organization/project controls. |
| `PROPOSED` | Use direct provider APIs as exceptional, explicitly approved fallback. Keep OpenRouter disabled for secret-bearing, client-data, security-sensitive, or release-authority routes unless a separately approved exception pins the exact model and provider endpoint, disables fallbacks, enforces data and price policy, and validates returned provenance. |
| `UNKNOWN` | Exact per-request subscription debit, consumer-plan concurrency ceilings, local runner total cost, and the fitness of any cheap model for Dopemux audit work remain unknown until provider telemetry or a bounded evaluation supplies evidence. |

**Decision:** API fallback can be designed, but it must fail closed. Subscription availability is an availability signal, not a budget ledger. OpenRouter is a broker and provenance source, not a model-identity or privacy oracle.

## 2. Questions answered

| ID | Question | Disposition |
|---|---|---|
| Q1 | What subscription limits and rolling windows are published? | `ANSWERED` for the reviewed OpenAI/Codex, Claude, and Gemini app surfaces; exact entitlements remain plan- and product-specific. |
| Q2 | Are plan credits exposed per request, and what is measurable? | `PARTIAL`: usage bars, banners, shared pools, reset times, and some credit totals are exposed; a stable, comparable per-request debit is not documented. |
| Q3 | How should exhaustion and unattended risk be represented? | `ANSWERED`: represent operational states and reset evidence, not invented credits. |
| Q4 | Can OpenRouter pin provider/model, disable fallbacks, and report provenance? | `ANSWERED` from official routing and API reference documentation. |
| Q5 | What privacy, ZDR, structured-output, and price controls exist? | `ANSWERED_WITH_LIMITS`: controls exist, but their guarantees stop at documented provider and feature boundaries. |
| Q6 | What do direct APIs expose for output, accounting, IDs, and model metadata? | `ANSWERED` for OpenAI, Anthropic, and Gemini APIs. |
| Q7 | Which routes fit each privacy class? | `PROPOSED` policy based on official retention and routing controls. |
| Q8 | How should hard cost caps and total cost be modeled? | `ANSWERED_WITH_UNKNOWNS`: formulas and gates are defined; operator-specific inputs remain unknown. |
| Q9 | Which routes should be public, low-risk only? | `ANSWERED`: low-cost multi-provider OpenRouter routes and unqualified cheap challengers. |

## 3. Subscription economics

### 3.1 Published behavior

| Surface | Label | Published behavior | Audit implication | Sources |
|---|---|---|---|---|
| OpenAI Codex through ChatGPT plans | `CLAIMED` | Codex is included across ChatGPT plans; usage varies by plan and task size, complexity, model, and execution location. Codex and other agentic products can draw from a shared agentic usage and credit pool. | A request cannot be admitted from a fixed “one task = N credits” rule. | S-OAI-CODEX |
| OpenAI Business base-model access | `CLAIMED` | “Virtually unlimited” access is qualified by service terms and prohibitions including abusive automated extraction, credential sharing, and powering third-party services. Model-specific caps also exist. | “Unlimited” must never be translated into unattended automation permission or infinite capacity. | S-OAI-BUSINESS |
| Claude paid plans | `CLAIMED` | Message consumption varies with prompt length, attachments, conversation length, tools, model, and effort. Usage settings expose five-hour-session and weekly progress, reset information, and in some cases usage credits. | Plan state can be observed, but marginal request cost is not deterministic. | S-ANTH-USAGE |
| Gemini Apps | `CLAIMED` | Limits are compute-based, depend on prompt complexity, model/features, and chat length, refresh every five hours until a weekly limit, and may change without notice. The UI provides near-limit and reset notifications. | Use status and reset evidence only. Do not infer hidden quota units. | S-GOOG-APP |

### 3.2 What may be measured

| Label | Measurement | Policy |
|---|---|---|
| `OBSERVED` | Monthly subscription price actually paid | Record from billing records, not from model-token estimates. |
| `CLAIMED` | Published plan caps, five-hour or weekly windows, UI progress bars, reset timestamps, banners, and explicitly displayed credit balances | Record with timestamp, plan, product, and source surface. |
| `UNKNOWN` | A cross-vendor, per-request subscription-credit debit | Store `null` or `UNKNOWN`. Never back-solve it from tokens, latency, or throttling. |
| `UNKNOWN` | Consumer-plan concurrency ceiling unless an official source states it for the exact product and plan | Do not invent a worker count. Gate concurrency conservatively and treat 429/limit banners as environment events. |
| `PROPOSED` | Plan route state | Use `AVAILABLE`, `DEGRADED`, `THROTTLED_UNTIL`, `EXHAUSTED`, `TERMS_BLOCKED`, or `UNKNOWN`; attach the observed evidence and timestamp. |

### 3.3 Unattended-use risk

| Label | Risk | Required behavior |
|---|---|---|
| `INFERRED` | Dynamic limits and fair-use controls can halt or degrade unattended queues unpredictably. | Plan-backed routes may be operator-triggered only until the relevant vendor-policy and telemetry track proves an unattended deployment mode. |
| `INFERRED` | Retrying plan throttles can amplify account risk and operator burden. | Do not loop aggressively. Respect reset evidence; do not evade limits with account rotation or credential sharing. |
| `PROPOSED` | Environment failure must remain separate from audit-quality failure. | A throttle, login expiry, or runner outage must not silently escalate to a more expensive model. Require a separate fallback authorization. |

## 4. OpenRouter controls and limits

### 4.1 Enforceable request controls

| Control | Label | Use in an audit route | Source |
|---|---|---|---|
| `model` | `CLAIMED` | Pin one exact model slug. Do not use auto-routing for judge/audit authority. | S-OR-CHAT, S-OR-ROUTING |
| `provider.only` or exact `provider.order` endpoint slug | `CLAIMED` | Restrict acceptable provider endpoints. Prefer exact endpoint slugs when region or variant matters. | S-OR-ROUTING |
| `allow_fallbacks: false` | `CLAIMED` | Prevent silent provider failover. Required when provenance, privacy, or independence matters. | S-OR-ROUTING |
| `require_parameters: true` | `CLAIMED` | Exclude providers that would ignore requested parameters such as JSON formatting. | S-OR-ROUTING |
| `data_collection: "deny"` | `CLAIMED` | Filter to providers OpenRouter classifies as not collecting user data. | S-OR-ROUTING |
| `zdr: true` | `CLAIMED` | Restrict routing to endpoints marked ZDR. | S-OR-ROUTING |
| `max_price` | `CLAIMED` | Bound acceptable provider unit pricing. This is not a total-request-dollar cap. | S-OR-ROUTING |
| `X-OpenRouter-Metadata: enabled` | `CLAIMED` | Return routing metadata, including the selected endpoint, requested model, strategy, and provider summary. | S-OR-CHAT |

### 4.2 Provenance that must be captured

| Label | Field | Required proof use |
|---|---|---|
| `CLAIMED` | Response `id`, `model`, `usage`, `usage.cost`, and `openrouter_metadata` | Bind the result to the returned model and selected provider, and reconcile estimated versus actual cost. |
| `CLAIMED` | Generation metadata `provider_name`, `request_id`, `upstream_id`, `total_cost`, and native token fields | Preserve broker and upstream tracing for incident review and billing reconciliation. |
| `PROPOSED` | Requested route profile hash and normalized response-metadata hash | Detect policy drift or provenance mismatch. |
| `PROPOSED` | Fail-closed comparison | Reject the result if actual provider/model metadata is missing or differs from the approved route. |

### 4.3 Why OpenRouter is not an oracle

| Label | Finding |
|---|---|
| `CLAIMED` | OpenRouter states that its provider data-policy tags are its best knowledge and are not a definitive source of third-party policy. |
| `INFERRED` | `data_collection: "deny"` and `zdr: true` are useful router filters, not substitutes for the upstream provider’s contract, retention documentation, or compliance review. |
| `INFERRED` | Returned broker metadata is evidence of what OpenRouter reports it routed, but it is not provider-attested model identity. |
| `PROPOSED` | Treat OpenRouter as controlled API transport only. It must not certify audit independence, model identity, provider compliance, or release authority. |

## 5. Recommended OpenRouter route profiles

| Profile | Label | Required settings | Allowed data class | Disposition |
|---|---|---|---|---|
| `OR-PUBLIC-CHEAP-CHALLENGER` | `PROPOSED` | Exact model allowlist; provider allowlist; `require_parameters: true`; explicit `max_price`; bounded input/output tokens; metadata enabled; fallback only inside the approved public-only set. | Public repository, low-risk, non-authoritative challenge. | Allowed after evaluation. |
| `OR-PUBLIC-STRICT-REVIEW` | `PROPOSED` | Exact model and provider endpoint; `allow_fallbacks: false`; `require_parameters: true`; `data_collection: "deny"`; `zdr: true`; `max_price`; metadata enabled. | Public repository where reproducibility matters. | Allowed after configuration test and evaluation. |
| `OR-PRIVATE-EXCEPTION` | `PROPOSED` | All strict settings plus legal/security approval of OpenRouter and the exact upstream endpoint, explicit retention evidence, redaction/secret scan, and human approval per run. | Private repository without suspected secrets. | Default deny; exception only. |
| `OR-SENSITIVE-DENY` | `PROPOSED` | No route. | Possible secrets, client data, security-sensitive diffs, credentials, regulated data, or release authority. | Denied by default. |

**Low-cost model posture:** `PROPOSED` candidates such as OpenAI nano/mini-class models, Claude Haiku-class models, and Gemini Flash-Lite-class models may be evaluated as classifiers or challengers. No low-cost model is pre-certified by this research for final audit authority.

## 6. Direct API comparison

| Capability | OpenAI API | Anthropic API | Gemini API |
|---|---|---|---|
| Structured output | `CLAIMED`: JSON Schema structured outputs with strict mode. | `CLAIMED`: JSON outputs and strict tool use; documented edge cases remain. | `CLAIMED`: responses can adhere to a supported subset of JSON Schema. |
| Usage accounting | `CLAIMED`: response usage plus project/admin cost and governance surfaces. | `CLAIMED`: response token fields plus organization Usage & Cost Admin API. | `CLAIMED`: `usageMetadata` reports token usage. |
| Request/response tracing | `CLAIMED`: `x-request-id`, optional caller `X-Client-Request-Id`, and rate-limit headers. | `CLAIMED`: unique `request-id` header; errors include `request_id`. | `CLAIMED`: `responseId`; a general request-ID-header contract was not established in reviewed docs. |
| Model metadata | `CLAIMED`: requested model and versioned model IDs where used. | `CLAIMED`: requested model and model-specific response context; exact provider-attested identity still depends on the direct endpoint contract. | `CLAIMED`: `modelVersion` and `modelStatus` in response metadata. |
| Organization/project controls | `CLAIMED`: model allowlist/denylist, spend alerts, project retention controls, audit logs, and rate-limit operations. | `CLAIMED`: monthly spend caps, lower configurable spend limits, workspace rate/spend limits, and rate-limit API. | `CLAIMED`: billing-account and project spend caps, with documented enforcement latency and overage caveats. |
| ZDR/retention | `CLAIMED`: approved ZDR/MAM controls; endpoint and feature exceptions; `store` forced false for eligible chat/responses routes under ZDR. | `CLAIMED`: organization ZDR arrangement; eligible Messages/Token Counting routes; stateful and covered-model exceptions. | `CLAIMED`: Paid Services are not used to improve products; achieving zero data retention requires feature-specific configuration and avoidance. |

### 6.1 Hard-cap reality check

| Label | Finding |
|---|---|
| `CLAIMED` | OpenAI project spend alerts notify at a threshold; the reviewed documentation does not describe them as a synchronous request-blocking cap. |
| `CLAIMED` | Anthropic organization spend limits pause API usage when the monthly cap is reached, and customers can set a lower limit. |
| `CLAIMED` | Gemini project spend caps are experimental and may permit roughly ten minutes of overage; long-running tasks can exceed the project cap. Billing-account tier caps pause service at the account level. |
| `CLAIMED` | OpenRouter `max_price` filters provider unit pricing, not total request spend. |
| `PROPOSED` | Therefore, Dopemux must implement caller-side preflight admission and postflight reconciliation even when a provider offers native budget controls. |

## 7. API fallback trigger policy

A fallback request is eligible only when all gates pass.

1. `PROPOSED` **Task gate:** the requested work requires semantic review that mechanical validation cannot provide.
2. `PROPOSED` **Reason gate:** fallback reason is one of `PLAN_THROTTLED`, `PLAN_UNAVAILABLE`, `STRUCTURED_OUTPUT_REQUIRED`, `PROVENANCE_REQUIRED`, or `OPERATOR_APPROVED_EXCEPTION`. Environment failure alone does not select a higher-cost model.
3. `PROPOSED` **Privacy gate:** data is classified and the route is permitted by the matrix below.
4. `PROPOSED` **Identity gate:** exact provider, model, endpoint, and required response metadata are known and approved.
5. `PROPOSED` **Cost gate:** worst-case preflight estimate fits per-request, daily, and monthly remaining budgets.
6. `PROPOSED` **Quality gate:** the model/route has a current Dopemux evaluation certificate for the intended role.
7. `PROPOSED` **Human gate:** client data, sensitive diffs, and any result affecting release or merge readiness require human approval.
8. `PROPOSED` **Postflight gate:** actual usage/cost and returned provenance are reconciled. Any mismatch invalidates the result as governed proof.

## 8. Privacy and authority matrix

| Work class | Subscription product | OpenRouter | Direct API | Authority result |
|---|---|---|---|---|
| Public repository, low risk | `PROPOSED`: interactive/operator-triggered use may be allowed if vendor terms permit. | `PROPOSED`: allowed through approved public profiles. | `PROPOSED`: allowed; preferred when traceability or automation is required. | Model output is advisory evidence. |
| Private repository, no suspected secrets | `PROPOSED`: operator-triggered only, under applicable commercial/workspace terms. | `PROPOSED`: default deny; explicit approved exception only. | `PROPOSED`: preferred through an approved commercial project with documented retention. | Human remains decision authority. |
| Possible secrets | `PROPOSED`: deny egress until secret triage/redaction. | `PROPOSED`: deny. | `PROPOSED`: direct approved endpoint only after redaction or explicit security approval; use ZDR-compatible features where required. | Fail closed. |
| Client data | `PROPOSED`: deny consumer-plan routes; commercial contract review required. | `PROPOSED`: deny by default. | `PROPOSED`: direct commercial API only after client, legal, and privacy approval. | Human approval mandatory. |
| Security-sensitive diff | `PROPOSED`: do not use as unattended authority. | `PROPOSED`: deny by default. | `PROPOSED`: direct approved API, bounded tools, documented retention, independent human/security review. | No automatic merge-readiness claim. |
| Release authority | `PROPOSED`: not permitted. | `PROPOSED`: not permitted. | `PROPOSED`: API output may inform review but cannot hold release authority. | Human operator and existing governance contracts retain authority. |

## 9. What ZDR does and does not mean

| Label | Finding |
|---|---|
| `CLAIMED` | OpenAI ZDR requires approval, excludes customer content from abuse-monitoring logs, forces `store=false` on eligible chat/responses routes, and still has endpoint/feature exceptions such as background storage and third-party MCP retention. |
| `CLAIMED` | Anthropic ZDR is organization-enabled, does not store prompts/responses at rest after the API response for eligible routes, and excludes stateful features, consumer products, and covered models requiring retention. |
| `CLAIMED` | Gemini Paid Services do not use prompts/responses to improve products, but zero-retention behavior requires avoiding or configuring stateful features such as stored Interactions, grounding, File API storage, and explicit context caching. |
| `INFERRED` | ZDR does not mean “data never exists,” “no transient processing,” “all tools are covered,” or “the router enforces the upstream contract.” |
| `PROPOSED` | The route proof must list every enabled feature and its retention status. An unknown feature-retention status blocks sensitive egress. |

## 10. Hard cost-cap model

### 10.1 Preflight estimate

`PROPOSED`

```text
estimated_run_max =
    input_tokens_max  * current_input_unit_price
  + output_tokens_max * current_output_unit_price
  + cache_write_max   * current_cache_write_unit_price
  + cache_storage_max * current_cache_storage_unit_price
  + tool_call_max     * current_tool_unit_price
  + search_call_max   * current_search_unit_price
  + router_or_region_uplift_max
  + retry_budget_max
```

Prices must come from a versioned, timestamped price catalog refreshed from current official pricing. Unknown price components block the route unless the operator explicitly approves a conservative ceiling.

### 10.2 Admission gates

`PROPOSED`

```text
reject if estimated_run_max > request_cap_remaining
reject if spent_today + reserved_today + estimated_run_max > daily_cap
reject if spent_month + reserved_month + estimated_run_max > monthly_cap
reject if input_tokens_estimate > input_token_cap
reject if output_tokens_max > output_token_cap
reject if retries_requested > retry_cap
```

Reserve the estimate atomically before dispatch. Release unused reservation after postflight accounting. A provider budget alert is not a substitute for this reservation ledger.

### 10.3 Postflight reconciliation

`PROPOSED`

Record:

- provider, model, endpoint, request/response IDs;
- input, cached, output, reasoning, tool, and search usage where exposed;
- provider-reported cost and independently recomputed cost;
- variance and price-catalog version;
- retry count and failed-run cost;
- operator intervention time.

A material variance, missing provenance, or stale price catalog invalidates automatic continuation.

## 11. Total-cost model

`PROPOSED`

```text
total_cost_period =
    subscription_fees_paid
  + metered_api_cost
  + router_fees_or_markups
  + runner_hardware_amortization
  + electricity_kwh * local_electricity_rate
  + maintenance_hours * operator_loaded_hourly_rate
  + failed_run_hours * operator_loaded_hourly_rate
  + incident_and_retry_cost
```

| Label | Component | Measurement rule |
|---|---|---|
| `OBSERVED` | Subscription fee | Use actual invoices. Keep separate from usage limits and API spend. |
| `CLAIMED` | API usage and cost | Use provider response metadata and admin/billing APIs. |
| `UNKNOWN` | Hardware amortization | Requires purchase price, usable life, residual value, and utilization. |
| `UNKNOWN` | Electricity | Requires measured watts, duty cycle, and local tariff. |
| `UNKNOWN` | Maintenance and failure burden | Requires operator time logs and a loaded hourly rate. |
| `PROPOSED` | Latency | Report separately as queue, inference, retry, and operator-wait time; do not convert to dollars without an approved rate. |
| `PROPOSED` | Account/quota risk | Track as incidents, blocked hours, and route disablements rather than a fictional monetary reserve. |

## 12. Unknown-measurement policy

1. `PROPOSED` Store unavailable measurements as `null` with `status: "UNKNOWN"`, not zero.
2. `PROPOSED` Never convert tokens into subscription credits unless the vendor publishes the mapping for the exact product and plan.
3. `PROPOSED` Never infer plan capacity from a small number of successful runs.
4. `PROPOSED` Distinguish `NOT_EXPOSED`, `NOT_COLLECTED`, `NOT_APPLICABLE`, `STALE`, and `UNKNOWN`.
5. `PROPOSED` Preserve source date, plan, model, route, and UI/API surface for every quota observation.
6. `PROPOSED` Expire pricing and privacy evidence on vendor change, model retirement, route change, or a maximum review interval defined by synthesis.
7. `PROPOSED` A missing cost or privacy field blocks sensitive or authoritative fallback. Public challenger routes may proceed only under an explicit conservative cap.

## 13. Contradictions and carried tensions

| ID | Label | Tension | Disposition |
|---|---|---|---|
| C-01 | `CONFLICTING` | OpenRouter can enforce endpoints tagged ZDR/data-deny, while its documentation says provider-policy tags are not definitive third-party policy sources. | Carry forward. Router filters are necessary but insufficient. |
| C-02 | `CONFLICTING` | Products describe access as unlimited or expanded, while fair-use, shared pools, dynamic compute limits, and automation restrictions remain. | Resolve operationally by treating plan capacity as non-deterministic and terms-scoped. |
| C-03 | `CONFLICTING` | Gemini calls project spend controls “caps,” but documents enforcement latency and long-running-task overages. | Do not treat them as a synchronous hard stop. |
| C-04 | `CONFLICTING` | OpenAI exposes “spend limit alerts,” but the reviewed documentation describes notification, not request blocking. | Use alerts as observability only; enforce local admission caps. |

## 14. Unresolved unknowns

| ID | Label | Unknown | Blocking scope | Needed evidence |
|---|---|---|---|---|
| U-01 | `UNKNOWN` | Exact per-request debit from each subscription plan. | Subscription budget accounting. | Vendor per-request ledger or official mapping. |
| U-02 | `UNKNOWN` | Exact concurrency ceiling for each consumer/seat plan. | Unattended worker count. | Current plan-specific official documentation or vendor clarification. |
| U-03 | `UNKNOWN` | Local runner hardware, energy, and maintenance cost. | Total-cost comparison. | Metered host data and operator rates. |
| U-04 | `UNKNOWN` | Contractual retention and compliance posture of the exact future OpenRouter upstream endpoint. | Any private-data OpenRouter route. | Current upstream terms, DPA/ZDR evidence, and approved endpoint inventory. |
| U-05 | `UNKNOWN` | Dopemux audit quality of low-cost challenger models. | Route certification. | Bounded benchmark and shadow evaluation from DR-04 policy. |
| U-06 | `UNKNOWN` | Whether the actual repository/client-data contract permits each direct API. | Private/client data egress. | Legal/client approval and data-processing terms. |
| U-07 | `UNKNOWN` | A generic Gemini request-ID response-header contract equivalent to OpenAI/Anthropic. | Cross-provider trace normalization. | Current official API reference or observed approved test later. |

## 15. Activities not run

- `NOT_RUN`: provider API calls, OpenRouter calls, account login, credential inspection, subscription-usage sampling, benchmark execution, price scraping, and billing-console inspection.
- `NOT_RUN`: local hardware power measurement and operator-time study.
- `NOT_RUN`: final model selection or architecture synthesis.

These omissions follow `RUN-CONTROL.md` and preserve the local static-only evidence posture.

## 16. Recommendations

| ID | Label | Recommendation | Status |
|---|---|---|---|
| R-01 | `PROPOSED` | Treat plan-backed usage as operator-triggered capacity with non-deterministic limits, not as a metered automation budget. | Carry to synthesis. |
| R-02 | `PROPOSED` | Make direct APIs the default exceptional fallback for private or governed work. | Carry to synthesis. |
| R-03 | `PROPOSED` | Restrict OpenRouter to public/low-risk routes by default; require a formal exception for private work. | Carry to synthesis. |
| R-04 | `PROPOSED` | Pin exact model/provider endpoint, disable fallbacks, enforce parameters/data/ZDR/price policy, and validate returned metadata. | Required before enablement. |
| R-05 | `PROPOSED` | Implement caller-side atomic budget reservation, token bounds, retry limits, and postflight reconciliation. | Required before API automation. |
| R-06 | `PROPOSED` | Fail closed when price, retention, actual provider/model, request IDs, or route certificate are missing or stale. | Required. |
| R-07 | `PROPOSED` | Require secret scanning/redaction and human approval before any sensitive egress. | Required. |
| R-08 | `PROPOSED` | Preserve human release/merge authority; model routes produce evidence only. | Required. |
| R-09 | `PROPOSED` | Maintain a dated official-source catalog for price, retention, model, and routing facts; expire route certification on material change. | Required for ongoing operation. |

## 17. Synthesis implications

- API fallback must remain a distinct route from plan-authenticated CLIs.
- OpenRouter must remain controlled fallback transport, never a trust or identity authority.
- The proof contract must record requested and actual model/provider, route profile, request IDs, cost, data policy, and fallback reason.
- Sensitive data should default to direct approved APIs, with feature-level retention checks and human approval.
- Environment failures must not automatically promote model tier or spend.
- Mechanical validation remains a first-class route and must not be displaced by cheap API calls.
- Cost gates require local reservation and reconciliation because native provider controls differ and are not uniformly hard.
- Low-cost challenger roles require evaluation certification; price alone is not competence evidence.

## 18. Local evidence relationship

| Local artifact | Relationship |
|---|---|
| `PROBE_SUMMARY.md` | `SUPPORTS`: confirms no live model/API calls and mechanical validation as the only observed usable lane. |
| `ROUTING_CONSTRAINTS.md` | `SUPPORTS`: requires OpenRouter provider/model, price, data policy, retention, and fallback provenance to be pinned. |
| `AUTHENTICATION_AND_TERMS_MATRIX.md` | `EXTENDS`: local OpenRouter auth, retention, and provider controls were unknown; this report supplies external documented controls but does not make a live route observed. |
| `MODEL_IDENTITY_OBSERVATIONS.json` | `SUPPORTS`: observed model identity remains unknown because no live call occurred. |
| `BLOCKERS_AND_UNKNOWNS.json` | `EXTENDS`: provides policy recommendations while preserving local unknowns and the no-call boundary. |

## 19. Source ledger

All web sources are official vendor documentation, pricing, help, or API references. Access date: **2026-07-13**.

| ID | Publisher | Source | Class | Updated when available | URL |
|---|---|---|---|---|---|
| S-OR-ROUTING | OpenRouter | Provider Routing | Official documentation | Not stated | https://openrouter.ai/docs/guides/routing/provider-selection |
| S-OR-CHAT | OpenRouter | Create a chat completion | Official documentation | Not stated | https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion |
| S-OR-GEN | OpenRouter | Get request & usage metadata for a generation | Official documentation | Not stated | https://openrouter.ai/docs/api/api-reference/generations/get-request-%26-usage-metadata-for-a-generation |
| S-OAI-CODEX | OpenAI | Using Codex with your ChatGPT plan | Official documentation | Not stated | https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan |
| S-OAI-BUSINESS | OpenAI | ChatGPT Business: Models & Limits | Official documentation | Not stated | https://help.openai.com/en/articles/12003714-chatgpt-business-models-limits |
| S-OAI-DATA | OpenAI | Data controls in the OpenAI platform | Official security/privacy documentation | Not stated | https://developers.openai.com/api/docs/guides/your-data |
| S-OAI-STRUCT | OpenAI | Structured model outputs | Official documentation | Not stated | https://developers.openai.com/api/docs/guides/structured-outputs |
| S-OAI-API | OpenAI | API overview | Official documentation | Not stated | https://developers.openai.com/api/reference/overview |
| S-OAI-ADMIN | OpenAI | Admin APIs | Official documentation | Not stated | https://developers.openai.com/api/docs/guides/admin-apis |
| S-OAI-PRICE | OpenAI | API pricing | Official pricing | Not stated | https://developers.openai.com/api/docs/pricing |
| S-ANTH-USAGE | Anthropic | Usage limit best practices | Official documentation | 2026-06-02 | https://support.claude.com/en/articles/9797557-usage-limit-best-practices |
| S-ANTH-RATE | Anthropic | Rate limits | Official documentation | Not stated | https://platform.claude.com/docs/en/api/rate-limits |
| S-ANTH-COST | Anthropic | Usage and Cost API | Official documentation | Not stated | https://platform.claude.com/docs/en/manage-claude/usage-cost-api |
| S-ANTH-STRUCT | Anthropic | Structured outputs | Official documentation | Not stated | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| S-ANTH-DATA | Anthropic | API and data retention | Official security/privacy documentation | Not stated | https://platform.claude.com/docs/en/manage-claude/api-and-data-retention |
| S-ANTH-ERROR | Anthropic | Errors and request IDs | Official documentation | Not stated | https://platform.claude.com/docs/en/api/errors |
| S-ANTH-PRICE | Anthropic | Pricing | Official pricing | Not stated | https://platform.claude.com/docs/en/about-claude/pricing |
| S-GOOG-APP | Google | Gemini Apps limits & upgrades | Official documentation | Not stated | https://support.google.com/gemini/answer/16275805?hl=en |
| S-GOOG-RATE | Google | Gemini API rate limits | Official documentation | Not stated | https://ai.google.dev/gemini-api/docs/rate-limits |
| S-GOOG-STRUCT | Google | Gemini API structured outputs | Official documentation | Not stated | https://ai.google.dev/gemini-api/docs/structured-output |
| S-GOOG-GEN | Google | GenerateContent response reference | Official documentation | Not stated | https://ai.google.dev/api/generate-content |
| S-GOOG-ZDR | Google | Zero data retention in the Gemini Developer API | Official security/privacy documentation | 2026-05-28 | https://ai.google.dev/gemini-api/docs/zdr |
| S-GOOG-BILL | Google | Gemini API billing | Official pricing/billing | Not stated | https://ai.google.dev/gemini-api/docs/billing |
| S-GOOG-PRICE | Google | Gemini Developer API pricing | Official pricing | Not stated | https://ai.google.dev/gemini-api/docs/pricing |
