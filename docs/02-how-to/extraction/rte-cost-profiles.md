---
id: how-to-rte-cost-profiles
title: 'RTE cost profiles: pick the right --cost-profile and tune optimizers'
type: how-to
owner: rte-routing
date: 2026-05-23
adhd_complexity: 0.4
adhd_energy: medium
relates_to:
- docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md
- docs/06-research/extraction/rte-cost-profile-redesign/routing-design-2026-05.md
author: '@hu3mann'
last_review: '2026-05-24'
next_review: '2026-08-22'
prelude: 'RTE cost profiles: pick the right --cost-profile and tune optimizers (how-to)
  for dopemux documentation and developer workflows.'
---
# RTE cost profiles

The Repo Truth Extractor exposes 4 cost profiles via the `--cost-profile` CLI flag. Each profile selects model tiers, service_tier defaults, cached-input behavior, batch usage, escalation depth, and a default cost cap.

## TL;DR

```bash
# Default — best cost/quality ratio
dopemux rte run --phase A --execute   # implicitly --cost-profile value-default

# Cheapest
dopemux rte run --phase A --execute --cost-profile economy

# Production go/no-go runs
dopemux rte run --phase A --execute --cost-profile quality

# Opt-in for bleed-edge frontier models
dopemux rte run --phase A --execute --cost-profile experimental
```

## Profiles at a glance

| Profile | Models | Tier | Cache | Batch | Cost vs prior default |
|---|---|---|---|---|---|
| `economy` | cheap (`gpt-5.1-codex-mini`, `claude-haiku-4.5`, `grok-4-fast`) | `flex` (50% off, async 24h) | on | on | ~75% cheaper |
| `value-default` (DEFAULT) | mid-tier (`gpt-5.3-codex`, `claude-sonnet-4.6`, `gpt-5.4-mini`) | `default` for CE/SYNTH; `flex` for bulk | on | on for bulk | ~50% cheaper |
| `quality` | premium (`gpt-5.5`, `claude-opus-4.6`) | `priority` (2.5× faster, 2.5× cost) | on | off | ~50% more expensive |
| `experimental` | frontier (`gpt-5.5-pro`, `claude-opus-4.7`, `gemini-3.5-flash`) | `default` | on | off | ~25% cheaper than prior default |

Cost vs prior default is estimated; actual cost depends on cache hit rate and repair rate. See [routing-design-2026-05.md](../../06-research/extraction/rte-cost-profile-redesign/routing-design-2026-05.md) for the assumptions.

## When to pick each profile

**Use `economy` when:**
- Doing exploratory or validation-first runs.
- Cost matters more than wall-clock time (flex is async 24h).
- Operator accepts ~5-10% higher contract-fail rate as a cost-quality trade.
- NEVER use for production reports — synthesis quality degrades.

**Use `value-default` when:**
- Normal repo-truth-extractor runs. This is the new default.
- You want optimizer benefits without explicit tuning.
- You want flex savings on bulk lanes without flex latency on critical lanes.

**Use `quality` when:**
- Production go/no-go decisions or customer-facing deliverables.
- Latency matters (priority tier gives consistent fast responses).
- You can absorb 3-5× the cost of `value-default`.

**Use `experimental` when:**
- Evaluating newest frontier models before they're proven on canary steps.
- Internal benchmarking only — NOT for shipped artifacts.
- You've read the profile's `warning` notes (opus 4.7 tokenization tax, etc.).

## Legacy `--routing-policy` flag

The legacy `--routing-policy` flag still works for one release with a deprecation warning. Use this mapping to migrate:

| Legacy `--routing-policy` | Migrate to |
|---|---|
| `cost` | `--cost-profile economy` |
| `balanced`, `balanced_openrouter`, `balanced_grok_openrouter`, `openrouter`, `gemini_primary` | `--cost-profile value-default` |
| `quality`, `optimal` | `--cost-profile quality` |

If you pass both `--cost-profile` and `--routing-policy`, the cost profile wins.

## Optimizer fields you can tune

### `--disable-provider PROVIDER` — manual kill-switch

When a provider has a known outage, disable it for the run:

```bash
dopemux rte run --phase A --execute --cost-profile value-default --disable-provider openai
```

Routes whose provider matches the disabled list are skipped. The runtime falls through to the next ladder rung. Repeat the flag for multiple providers.

Valid providers: `openai`, `anthropic`, `gemini`, `xai`, `openrouter`.

### `--model-alias ALIAS=MODEL_ID` — swap a cell-level model

Each cost profile defines named cell aliases (e.g., `QUALITY_SYNTH_CRITICAL_MODEL`). Routes in `model_map.yaml` v3 can reference these via `${ALIAS_NAME}` placeholders. Operators override via:

```bash
# Swap quality's SYNTH-critical model to opus 4.7 just for this run
dopemux rte run --phase A --execute --cost-profile quality \
  --model-alias QUALITY_SYNTH_CRITICAL_MODEL=anthropic/claude-opus-4.7
```

Or via env var (same key name):

```bash
QUALITY_SYNTH_CRITICAL_MODEL=anthropic/claude-opus-4.7 \
  dopemux rte run --phase A --execute --cost-profile quality
```

Precedence: CLI override > env var > profile's `cell_aliases` default.

### Default cell aliases per profile

| Profile | Alias | Default model |
|---|---|---|
| `economy` | `ECONOMY_CE_MEDIUM_MODEL` | `openai/gpt-5.1-codex-mini` |
| `economy` | `ECONOMY_SYNTH_HIGH_MODEL` | `anthropic/claude-haiku-4.5` |
| `economy` | `ECONOMY_SYNTH_CRITICAL_MODEL` | `anthropic/claude-sonnet-4.5` |
| `economy` | `ECONOMY_BULK_EXTRACT_MODEL` | `openai/gpt-5.4-mini` |
| `value-default` | `VALUE_DEFAULT_CE_MEDIUM_MODEL` | `openai/gpt-5.3-codex` |
| `value-default` | `VALUE_DEFAULT_CE_HIGH_MODEL` | `openai/gpt-5.4` |
| `value-default` | `VALUE_DEFAULT_SYNTH_HIGH_MODEL` | `anthropic/claude-sonnet-4.6` |
| `value-default` | `VALUE_DEFAULT_SYNTH_CRITICAL_MODEL` | `anthropic/claude-opus-4.6` |
| `value-default` | `VALUE_DEFAULT_BULK_EXTRACT_MODEL` | `openai/gpt-5.4-mini` |
| `quality` | `QUALITY_CE_MEDIUM_MODEL` | `openai/gpt-5.5` |
| `quality` | `QUALITY_CE_HIGH_MODEL` | `openai/gpt-5.5` |
| `quality` | `QUALITY_SYNTH_HIGH_MODEL` | `anthropic/claude-opus-4.6` |
| `quality` | `QUALITY_SYNTH_CRITICAL_MODEL` | `anthropic/claude-opus-4.6` |
| `quality` | `QUALITY_SYNTH_CRITICAL_FALLBACK_MODEL` | `openai/gpt-5.5-pro` |
| `experimental` | `EXPERIMENTAL_CE_MEDIUM_MODEL` | `openai/gpt-5.5` |
| `experimental` | `EXPERIMENTAL_SYNTH_HIGH_MODEL` | `anthropic/claude-opus-4.7` |
| `experimental` | `EXPERIMENTAL_SYNTH_CRITICAL_MODEL` | `anthropic/claude-opus-4.7` |

### Cost cap interaction

Each profile has a `max_cost_usd_default`:

| Profile | Default cap |
|---|---|
| `economy` | `$5.00` |
| `value-default` | none (operator must set explicitly) |
| `quality` | none (operator must set explicitly) |
| `experimental` | `$25.00` |

The profile default applies only if `--max-cost-usd` is not passed. Operator-set caps always win.

The `value-default` and `quality` profiles have NO default cap because the cost depends heavily on the phase scope. Set `--max-cost-usd` explicitly for large runs.

## Why `value-default` is the new default

Per the [Phase D consensus](../../06-research/extraction/rte-cost-profile-redesign/routing-consensus-2026-05.md):

1. The prior `balanced_openrouter` policy was chosen pre-audit, before frontier models (gpt-5.5, claude-opus-4.6, gemini-3.5-flash) were available.
2. `balanced_openrouter` routed R/S synthesis phases to bulk-tier models — the F2-HIGH-1 audit finding. `value-default` routes them to `claude-sonnet-4.6` / `claude-opus-4.6`.
3. `value-default` enables cached-input by default (90% discount on repeated prompt prefixes) and flex tier on non-blocking EXTRACT/AGG lanes (50% off). Neither was previously wired.
4. CE-medium and CE-high cells in `value-default` route through OpenRouter primary for resilience against OpenAI outages, with direct OpenAI as escape hatch via the `direct_openai_required` tag.

## Verifying your config

```bash
# Show resolved routing for a phase without running it
dopemux rte run --phase A --dry-run --cost-profile value-default --print-phase-routing

# Show the full resolved config (cost profile + routes + caps)
dopemux rte run --phase A --dry-run --cost-profile value-default --print-config
```

Both commands are introspection-only — they do NOT run prescan, LLMs, or write run artifacts.

## See also

- [ADR: RTE cost profiles + optimizer wiring](../../90-adr/rte-cost-profiles-and-optimizer-wiring.md)
- [Verified model inventory (May 2026)](../../06-research/extraction/rte-cost-profile-redesign/verified-model-inventory-2026-05.md)
- [Routing design (Phase C)](../../06-research/extraction/rte-cost-profile-redesign/routing-design-2026-05.md)
- [Routing consensus (Phase D)](../../06-research/extraction/rte-cost-profile-redesign/routing-consensus-2026-05.md)
