# Telemetry and Usage Architecture

## Required usage fields

```text
visible_prompt_tokens
effective_input_tokens
cached_input_tokens
output_tokens
reasoning_output_tokens
runner_overhead_tokens
plan_credits
api_cost
estimated_cost
measurement_source
measurement_confidence
pricing_version
```

## Separation rules

- **PROPOSED:** Every value includes scope (`REQUEST`, `SESSION`, `ROLLUP`), exactness (`EXACT`, `ESTIMATED`, `UNAVAILABLE`, `MIXED`), and source.
- **PROPOSED:** Missing values remain unavailable. They are not set to zero.
- **PROPOSED:** Estimated cost is never labeled actual API cost.
- **PROPOSED:** Plan credits are never derived from tokens without a provider-published conversion tied to the relevant plan and date.
- **PROPOSED:** Runner overhead tokens are never inferred by subtracting visible prompt length from effective input tokens.
- **PROPOSED:** Cached input is recorded separately and not double-counted into a second “savings” total without provider semantics.

## Field definitions

| Field | Label | Definition |
|---|---|---|
| `visible_prompt_tokens` | **PROPOSED** | Tokens in operator-visible task/context when a trusted tokenizer or provider field can measure them. |
| `effective_input_tokens` | **PROPOSED** | Provider/runner reported input tokens including hidden/system/context overhead as defined by that source. |
| `cached_input_tokens` | **PROPOSED** | Source-reported cached input tokens; semantics are provider-specific. |
| `output_tokens` | **PROPOSED** | Source-reported generated output tokens. |
| `reasoning_output_tokens` | **PROPOSED** | Source-reported reasoning tokens, if exposed. |
| `runner_overhead_tokens` | **PROPOSED** | Independently measured runner/system overhead only. |
| `plan_credits` | **PROPOSED** | Directly observed plan-credit consumption or balance delta. |
| `api_cost` | **PROPOSED** | Provider/proxy billing cost attributed to the request. |
| `estimated_cost` | **PROPOSED** | Local estimate using a versioned price record. |
| `measurement_source` | **PROPOSED** | Runner, provider, proxy, Freeflow, RTE, operator, or benchmark source. |
| `measurement_confidence` | **PROPOSED** | `HIGH|MEDIUM|LOW|UNKNOWN` based on source semantics. |
| `pricing_version` | **PROPOSED** | Hash/version/date of price data used for an estimate. |

## Source normalization

### LiteLLM and Freeflow

- **OBSERVED:** LiteLLM trace code can expose prompt, completion, total, reasoning, and cached token fields when callbacks are enabled.
- **OBSERVED:** Freeflow records usage and locally estimated cost for its admission slice.
- **PROPOSED:** LiteLLM observations become request-level usage records with proxy source.
- **PROPOSED:** Freeflow cost remains `estimated_cost` and points to the relevant pricing version.
- **PROPOSED:** Freeflow quota/credit state is referenced, not copied into router state.

### RTE

- **OBSERVED:** RTE records run route metadata, usage/spend artifacts, and uses its own pricing/caveat fields.
- **PROPOSED:** RTE observations are imported by ref and normalized without replacing the RTE spend ledger.
- **PROPOSED:** RTE run-level and request-level observations remain separate.

### Runner-native telemetry

- **OBSERVED:** Codex smoke exposed effective input, cached input, output, and reasoning-output tokens but no credits/cost or attested model.
- **PROPOSED:** Record exactly those fields and leave all others unavailable.
- **OBSERVED:** Claude JSON envelopes can contain usage, model usage, and total cost fields, but the contained smoke did not reach a provider.
- **PROPOSED:** Zero usage/cost in an auth-failed call is scoped to that failed attempt, not proof of normal route cost.
- **UNKNOWN:** Gemini and AGY usage/cost fields are not locally proven.

### Provider billing

- **PROPOSED:** Provider-native usage/cost, when available and request-linked, has higher confidence than local estimates.
- **PROPOSED:** Billing rollups may arrive later than request completion and append a superseding observation rather than mutating the original.
- **PROPOSED:** Currency and tax semantics remain provider/account specific and must be explicit.

## Observation pipeline

```text
runner/proxy/provider/RTE/Freeflow evidence
                 |
                 v
source-specific parser
                 |
                 v
validation and redaction
                 |
                 v
UsageObservation append
                 |
                 +--> decision inspection
                 +--> benchmark metrics
                 +--> policy promotion evidence
                 +--> cost/credit guard feedback
```

## Avoiding double counting

- **PROPOSED:** Each observation carries a correlation key and source lineage.
- **PROPOSED:** Request-level, session-level, and provider billing records are not summed unless a rollup rule explicitly maps them.
- **PROPOSED:** A LiteLLM record and provider billing record for the same request are alternate measurements, not two costs.
- **PROPOSED:** Cached tokens remain part of provider-defined effective input when the source says so; the router does not subtract them unless a documented metric specifically asks for uncached tokens.

## Cost and credit policy behavior

- **PROPOSED:** Hard API cost ceiling blocks a route whose conservative estimate exceeds the ceiling.
- **PROPOSED:** Unknown API cost requires operator acceptance for low-risk advisory use and blocks cost-constrained automation.
- **PROPOSED:** Unknown plan credits require operator confirmation for plan-backed execution and block automatic paid fallback.
- **PROPOSED:** A credit or cost error does not trigger a stronger model. It triggers same-tier alternate, direct operator choice, or block.
- **PROPOSED:** Premium models require a policy reason such as high complexity, security, release judgment, repeated quality failure, or supervisor escalation.

## Latency telemetry

- **PROPOSED:** Record queue time, startup time, time-to-first-byte when exposed, model completion time, wrapper overhead, and wall time separately.
- **PROPOSED:** Missing internal stages remain unavailable.
- **PROPOSED:** Candidate ranking may use historical latency only after enough samples exist and no safety/certification requirement is weakened.

## Context and token overhead

- **OBSERVED:** The Codex probe showed runner/system context can dominate a tiny visible prompt.
- **PROPOSED:** Benchmark routes must track visible task/context size separately from effective provider input.
- **PROPOSED:** Policy may penalize routes with persistent high effective-input overhead for cheap reads, but only using measured distributions.
- **PROPOSED:** Context minimization uses refs, bounded manifests, and stage summaries instead of full transcript chaining.

## Router journal storage

- **PROPOSED:** Router SQLite stores normalized numeric observations, source/confidence, correlation refs, and hashes.
- **PROPOSED:** Raw provider payloads and full transcripts stay in external evidence/proof locations.
- **PROPOSED:** Secret-bearing metadata is redacted before normalization.
- **PROPOSED:** Append-only correction records supersede bad parsing or late billing data.

## Metrics exposed to operators

- **PROPOSED:** Per decision: known/unknown token fields, estimated/actual cost, plan-credit posture, latency, source/confidence, and caveats.
- **PROPOSED:** Per route: sample count, success/validation/audit rates, median and p95 latency, median tokens, exact/estimated cost coverage, override rate, escalation rate, and severe failure count.
- **PROPOSED:** Dashboard output never implies precision beyond source confidence.

## Pricing updates

- **PROPOSED:** Pricing records are versioned and independently reviewable.
- **PROPOSED:** Updating pricing does not rewrite past estimates. A recalculated comparison may be a separate analytical record.
- **PROPOSED:** Policy certification captures the pricing version used.
- **PROPOSED:** Missing or stale pricing can block cost-sensitive promotion but not deterministic offline explanation.
