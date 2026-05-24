---
id: routing-consensus-2026-05
title: Routing Consensus 2026 05
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-24'
last_review: '2026-05-24'
next_review: '2026-08-22'
prelude: Routing Consensus 2026 05 (reference) for dopemux documentation and developer
  workflows.
---
# Routing Design Consensus — May 2026 (Final)

**Phase D output** — two consensus sessions:
- Session 1 (`09b2be1a-c258-41ef-95ef-70eb58efc141`): `gpt-5.2` (neutral, 8/10 confidence). `gemini-3-pro-preview` failed on free-tier quota.
- Session 2 (`5a0eb765-219b-4a78-9d0d-a2647c662881`): `anthropic/claude-opus-4.5` (against, 7/10) + `gpt-5.2-pro` (neutral, 8/10).

**Reviewed design**: `routing-design-2026-05.md`.

---

## Final consensus (3-model convergent recommendations)

The three reviewers converge on these adjustments. Quoted text is paraphrased to the shortest accurate form; full text in raw session transcripts.

### 1. Provider concentration — **Route CE through OpenRouter by default; drop the circuit breaker**

All three reviewers reject the proposed OpenAI 5xx circuit breaker as over-engineered for a problem with a simpler architectural answer.

| Reviewer | Position |
|---|---|
| gpt-5.2 | Shift CE medium/high to OR-primary; add circuit breaker for additional 5xx defense |
| claude-opus-4.5 (against) | **Kill the breaker.** Route CE through OR by default in all profiles. OR's multi-upstream handles failover correctly. Breakers in app code accrete maintenance debt. |
| gpt-5.2-pro | Agreed: **per-request failover + manual kill-switch** beats a stateful app-level breaker. Breakers in `llm_runtime.py` are a layering smell when OR already provides multi-provider routing. |

**Final adjustment**:
- value-default `(CE, *)` cells → **primary through OpenRouter** for all 3 CE-cell levels (medium, high; low is Z0-only and acceptable to keep direct).
- Add **per-request failover**: if primary route fails (timeout / 5xx / 429), retry once on the next route in the ladder before declaring contract-failed. This already happens implicitly via `escalation_max_hops`, but make the first-retry behavior explicit and immediate (not subject to backoff).
- Add **manual kill-switch CLI flag**: `--disable-provider <openai|anthropic|gemini|xai>` for ops-runbook use during known outages.
- **No circuit breaker logic.** Drop Risk 1 mitigation step from prior design.

### 2. Opus 4.6 vs 4.7 — **Pick one (4.6); use cell-level aliases for future swaps**

All three reject the A/B opt-in framework as premature optimization.

| Reviewer | Position |
|---|---|
| gpt-5.2 | Opus 4.6 default; 4.7 opt-in per-step with measured A/B evidence |
| claude-opus-4.5 (against) | **No A/B machinery.** Pick 4.6, revisit when 4.8 ships |
| gpt-5.2-pro | **Cell-level model aliases** (e.g., `QUALITY_SYNTH_CRITICAL_MODEL=anthropic/claude-opus-4.6`) swappable centrally + small set of "canary steps" for new-model evaluation |

**Final adjustment**:
- `quality × (SYNTH, critical)` primary → **`anthropic/claude-opus-4.6`** (not 4.7).
- Add **cell-aliased model selection**: each cell can reference a named alias (e.g., `QUALITY_SYNTH_CRITICAL_MODEL`) read from env or `cost_profile.alias_overrides`. Default alias values defined in `cost_profiles.yaml`; operators can override via env var or `--model-alias K=V` CLI flag.
- Define **3-5 canary steps** (e.g., R7, S0, T0) that always run on the candidate alternate model alongside the alias-selected model. PROOF_PACK reports both outputs side-by-side for evaluation. When a candidate consistently wins on canaries, roll the alias centrally.
- **No per-step opus-4.7 opt-in flag.** Drop that workflow.

### 3. Step tags — **Bounded routing intents, not "sanctioned extension"**

| Reviewer | Position |
|---|---|
| gpt-5.2 | Tags + governance (warn @12, fail @15) |
| claude-opus-4.5 (against) | Tags = override predicates. Drop governance theater; log + review quarterly; promote frequent tags to dimensions |
| gpt-5.2-pro | Tags are bounded routing intents. Hard cap at ~8 total tags. Each tag deterministically maps to a *small* delta (bump tier by 1, force schema-capable, force long-context). Each tag usage declares rationale (metric or incident link). |

**Final adjustment**:
- Define **fixed enum** of ≤8 tags. Initial set: `low_temp`, `long_context`, `schema_critical`, `tooling_heavy`, `control_plane`, `security_sensitive`, `eval_canary`, `direct_openai_required` (this last one solves the "I need direct OpenAI cache access" case from #1).
- Each tag maps to a **deterministic delta**:
  - `long_context` → filter routes to those with `context_window >= 1_000_000`
  - `schema_critical` → filter to `supports_json_schema_strict: true`
  - `control_plane` → force capability_tier to at least `critical`; require post-step validator pass
  - `security_sensitive` → same as `control_plane` + restrict to a vetted model allowlist
  - `eval_canary` → run candidate alias model alongside default; emit both to PROOF_PACK
  - `direct_openai_required` → escape hatch from OR-default; use direct OpenAI route
  - `low_temp` → override temperature to 0.0 if model supports it
  - `tooling_heavy` → prefer Anthropic tool_use mode in repair routes
- Each step entry using a tag must include `tag_rationale: <one-line metric or incident link>`.
- Log all tag usage to PROOF_PACK; quarterly review surfaces tags used >8 times for promotion to dimensions.
- **Drop "governance theater" wording** from docs; the cap + rationale-required pattern IS the governance.

### 4. Matrix aggregation — **Tighten capability_tier definition; add `impact_class` flag**

The strongest critique from all three: the matrix can hide step-level failure-cost heterogeneity.

| Reviewer | Position |
|---|---|
| gpt-5.2 | Implicit (didn't push back) |
| claude-opus-4.5 (against) | Split `critical` into `critical_structural` (hard-fail) vs `critical_quality` (aggressive-fallback). R0 ≠ R11. |
| gpt-5.2-pro | Tighten `capability_tier` to include impact/correctness, not just model strength. Add lightweight "impact class" gate: `control_plane` / `security_sensitive` steps must be `critical` AND pass stricter validation. Add post-step validators for the most damaging outputs (truth-map integrity, security claims). |

**Final adjustment** (synthesizes both views):
- Add a step-level **`impact_class`** field: `routine | important | structural | security_sensitive`. Each step in `model_map.yaml` declares this.
- Add an **enforcement rule** in the promptset audit: steps with `impact_class ∈ {structural, security_sensitive}` MUST be `capability_tier=critical`. Audit fails closed if not.
- Reclassify the affected steps (R0 = `structural`; R11 = `security_sensitive`; S0 = `structural`; T0 = `structural`).
- **Do NOT split the `critical` tier into `critical_structural`/`critical_quality`** — instead, the `impact_class` flag carries that distinction and influences routing via the `control_plane`/`security_sensitive` tags (see #3 above) without adding matrix cells.
- Defer post-step validators (truth-map integrity, security-claim verification) to a separate task packet — out of this redesign's scope.

### 5. Layering separation (gpt-5.2-pro's framing — adopt cleanly)

Successful LLM-ops separates three concerns:
- **Selection** = cost/quality tier (cost profile × cell × tags) — this redesign's scope
- **Resilience** = fallbacks, retries, hedging — keep simple (per-request failover, no breaker)
- **Validation** = schema, invariants, safety checks — separate concern (defer to task packet)

The current redesign mixes Selection + Resilience by putting circuit-breaker logic in `llm_runtime.py`. Final design **pulls resilience to per-request retry only**; if more is needed, do it at the OR/gateway layer or as a future task.

---

## Adjustments to apply to design and implementation

### Change A: value-default CE cells route through OR primary

```yaml
# (CE, medium) value-default
primary_routes:
  - {provider: openrouter, model_id: openai/gpt-5.3-codex, api_key_env: OPENROUTER_API_KEY, service_tier: null, strict_json_schema: true, cache_strategy: none}
  - {provider: openai, model_id: gpt-5.3-codex, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
  - {provider: openai, model_id: gpt-5.4, api_key_env: OPENAI_API_KEY, service_tier: default, strict_json_schema: true, cache_strategy: auto}
# (CE, high) value-default: same pattern — OR primary, direct OpenAI as second
```

Steps marked with `direct_openai_required` tag (when explicit cache access matters) skip the OR primary and go direct.

### Change B: Drop circuit breaker. Add per-request failover + kill-switch.

In `llm_runtime.py` `call_llm()`:
- Existing retry/backoff stays.
- NEW: when a route returns timeout / 5xx / 429, immediately try the **next route in the ladder** ONCE before invoking standard backoff retries. This is what gpt-5.2-pro called "per-request failover."
- NEW: read `disabled_providers: Set[str]` from cfg (populated by `--disable-provider` CLI flag); skip any route whose provider is in this set.

No circuit breaker. No 5xx rate tracking. No degradation state.

### Change C: Cell-level model aliases (Phase E6 + E7)

```yaml
cost_profiles:
  quality:
    cell_aliases:
      QUALITY_SYNTH_CRITICAL_MODEL: "anthropic/claude-opus-4.6"
      QUALITY_SYNTH_HIGH_MODEL: "anthropic/claude-opus-4.6"
      QUALITY_CE_MEDIUM_MODEL: "openai/gpt-5.5"
      ...
```

Each ladder route can use `model_id: ${QUALITY_SYNTH_CRITICAL_MODEL}` syntax to reference an alias. Operators override via env var or `--model-alias K=V`.

### Change D: Tag definitions (Phase E8)

```yaml
# In promptsets/v4/model_map.yaml v3
tag_definitions:
  long_context:
    rationale: "Step prompt + inputs exceed 100K tokens routinely; route must support 1M context."
    routing_delta:
      filter_route_context_window_min: 1000000
  schema_critical:
    rationale: "Strict json_schema must be enforced; routes must be verified strict-capable."
    routing_delta:
      filter_supports_json_schema_strict: true
  control_plane:
    rationale: "Step output is a control-plane truth artifact; failure breaks downstream synthesis."
    routing_delta:
      require_min_capability_tier: critical
      require_post_step_validator: control_plane_truth_check
  security_sensitive:
    rationale: "Step handles security-relevant facts; misclassification has externality cost."
    routing_delta:
      require_min_capability_tier: critical
      route_allowlist: [anthropic/claude-opus-*, openai/gpt-5.5*, openai/gpt-5.5-pro]
  eval_canary:
    rationale: "Step is used to A/B candidate alternate models against current alias."
    routing_delta:
      enable_canary_dual_run: true
  direct_openai_required:
    rationale: "Step needs OpenAI direct (flex/priority/cache); cannot tolerate OR aggregator path."
    routing_delta:
      filter_provider: openai
  low_temp:
    rationale: "Deterministic output required; temperature must be 0.0 where model supports it."
    routing_delta:
      temperature_override: 0.0
  tooling_heavy:
    rationale: "Step makes many tool calls; prefer Anthropic tool_use mode in repair routes."
    routing_delta:
      prefer_repair_provider: anthropic

tag_governance:
  max_distinct_tags_in_use: 8
  require_tag_rationale_per_step: true
  promotion_threshold_to_dimension: 8  # if a tag is used by >8 steps, escalate to matrix dimension review
```

### Change E: impact_class field

Each step entry in `model_map.yaml` gets:

```yaml
- step_id: R0
  impact_class: structural  # NEW
  capability_tier: critical  # NEW (enforced by impact_class rule)
  tags: [control_plane]      # NEW
  tag_rationale: "Truth-map drives entire downstream synthesis stack."
  # ... existing fields ...
```

Audit rule in promptset linter:
```python
if step.get("impact_class") in {"structural", "security_sensitive"}:
    assert step.get("capability_tier") == "critical", \
        f"{step_id}: impact_class={impact_class} requires capability_tier=critical"
```

### Change F: Cell-aliased Cell (SYNTH, critical) primary for quality

```yaml
# quality × (SYNTH, critical)
primary_routes:
  - {provider: openrouter, model_id: "${QUALITY_SYNTH_CRITICAL_MODEL}", api_key_env: OPENROUTER_API_KEY, strict_json_schema: false, cache_strategy: cache_control_explicit}
  - {provider: openai, model_id: "${QUALITY_SYNTH_CRITICAL_FALLBACK_MODEL}", api_key_env: OPENAI_API_KEY, service_tier: priority, strict_json_schema: false, cache_strategy: auto}
# Default aliases (override via env or CLI):
#   QUALITY_SYNTH_CRITICAL_MODEL=anthropic/claude-opus-4.6
#   QUALITY_SYNTH_CRITICAL_FALLBACK_MODEL=gpt-5.5-pro
```

---

## Risks NOT raised by reviewers — log for future task packets

- **xAI batch API support unverified** (consensus didn't address). Stay conservative: `enable_batch_when_supported=false` for xAI provider routes.
- **Prompt-cache hit rate observability** (consensus didn't address). E2 spend ledger update must surface per-cell cache hit rate in spend_ledger.json so operator can verify estimated cost vs actual.
- **Post-step validators for control-plane / security-sensitive outputs** (gpt-5.2-pro flagged). Deferred to task packet `TP-RTE-OUTPUT-VALIDATORS`.

---

## Final design status

The two consensus sessions converge cleanly. All three reviewers agree the matrix + cost-profile structure is sound; disagreement is only on auxiliary mechanisms (circuit breaker, A/B framework, tag governance). The simplifications they recommend are net-cleaner than the original design.

Phase E implementation now uses:
- **E1 (pricing.yaml)** — done as planned
- **E2 (spend_ledger.py)** — add per-cell cache hit rate to ledger
- **E3 (structured_output_contracts.py)** — add `anthropic_tool_use` schema variant; tag-driven schema filtering
- **E4 (llm_runtime.py)** — per-request failover; `--disable-provider` plumbing; capture cached_tokens; tag-aware temperature override
- **E5 (batch_clients.py)** — service_tier passthrough (unchanged)
- **E6 (run_extraction_v5.py cost profiles)** — cell-aliased model selection; tag-driven routing deltas
- **E7 (run_extraction_v5.py ladders rewrite)** — ladders reference cell aliases; per-request failover semantics
- **E8 (model_map.yaml v3)** — `lane_defaults`, `tag_definitions`, `impact_class` field, `tag_rationale` per step using tags
- **E9 (tests)** — add tag-routing-delta test; add impact_class enforcement test
- **E10 (docs)** — operator guide explicitly covers cell aliases, kill-switch, tag governance

**Phase D complete.** Resume Phase E2 implementation.
