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
last_review: '2026-06-04'
next_review: '2026-09-04'
prelude: 'RTE cost profiles: pick the right --cost-profile and tune optimizers (how-to)
  for dopemux documentation and developer workflows.'
---
# RTE cost profiles

The Repo Truth Extractor exposes 11 cost profiles via the `--cost-profile` CLI flag. Each profile selects, **per cell**, the concrete provider+model that runs — plus service_tier defaults, cached-input behavior, batch usage, escalation depth, and a default cost cap.

### How profile model-switching works (Plan B)

`promptsets/v4/model_map.yaml` no longer hardcodes the lead model per step. Each step's **lead primary route** is a profile-agnostic placeholder for its lane: `${BULK_DOCS_MODEL}` (BULK_DOCS_GENERAL, non-strict), `${BULK_CODE_MODEL}` (BULK_CODE_HEAVY, non-strict), `${CE_MODEL}` (CE, strict), `${SYNTH_MODEL}` (AGG, strict). At dispatch the active profile's `cell_aliases` resolves each placeholder to a concrete `provider/model`, deriving provider, model AND api_key_env (direct-provider per profile). Hardcoded fallback routes below each lead are unchanged.

> **Strict cells are OpenAI-only.** `CE` + `AGG` steps require OpenAI-style strict JSON-schema passthrough, which only OpenAI models provide here (direct `openai/*` or `openrouter/openai/*`). So `CE_MODEL`/`SYNTH_MODEL` always resolve to OpenAI; a fail-closed guard rejects xai/gemini/anthropic on a strict cell **before any spend**. Provider diversity (Gemini, xAI) lives on the non-strict bulk lanes.

### Repair & sidefill also follow the profile (Increment 3)

The same placeholder mechanism now drives the **repair** and **sidefill** recovery routes, not just primary. Each lane's repair/sidefill lead resolves to its profile cell (`CE`/`AGG` → strict OpenAI; bulk → the profile's bulk model), with the original hardcoded model kept as a fallback.

> **Bulk repair/sidefill are now active.** Previously the recovery dispatch hard-required a strict route, so non-strict bulk lanes never selected one and bulk repair/sidefill **never ran**. Recovery strictness is now lane-aware, so bulk failures get a profile-driven recovery attempt — its output is still validated by the same contract gate as bulk primary. This adds conditional LLM calls (and cost) on bulk-lane failures that did not occur before. The 7 phase-M steps that deliberately repair with a strict OpenAI model stay pinned (not profile-driven). The full-repo `--print-cost-preview` prices primary routes only; reconcile `SPEND_LEDGER.json` after the first bounded `--execute` run before unattended use.

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

Bulk columns show the non-strict lane model; strict CE/SYNTH are always OpenAI.

| Profile | Bulk docs | Bulk code | CE / SYNTH (strict, OpenAI) | Tier | Cap |
|---|---|---|---|---|---|
| `economy` | `gpt-5.4-mini` | `gpt-5.4-mini` | `gpt-5.1-codex-mini` / `gpt-5.4` | `flex` | $5 |
| `value-default` (DEFAULT) | `gpt-5.4-mini` | `gpt-5.3-codex` | `gpt-5.3-codex` / `gpt-5.5` | `default` | none |
| `quality` | `gpt-5.4` | `gpt-5.5` | `gpt-5.5` / `gpt-5.5` | `priority` | none |
| `experimental` | `gemini-3.5-flash` | `gpt-5.5` | `gpt-5.5` / `gpt-5.5` | `default` | $25 |
| `gemini-value` | `gemini-3-flash-preview` | `gemini-3.1-pro-preview` | `gpt-5.3-codex` / `gpt-5.5` | `flex` | $8 |
| `grok-fast` | `xai/grok-4-fast` | `xai/grok-4.3` | `gpt-5.3-codex` / `gpt-5.4` | `flex` | $6 |
| `openrouter-resilient` | `openrouter/openai/gpt-5.4-mini` | `openrouter/openai/gpt-5.3-codex` | `openrouter/openai/gpt-5.3-codex` / `gpt-5.4` | `default` | $20 |
| `openai-heavy` | `gpt-5.4-mini` | `gpt-5.3-codex` | `gpt-5.3-codex` / `gpt-5.5` | `default` | $15 |
| `balanced-mix` | `gemini-3-flash-preview` | `xai/grok-4.3` | `gpt-5.3-codex` / `gpt-5.5` | `default` | $12 |
| `quality-mix` | `gpt-5.4` | `gpt-5.3-codex` | `gpt-5.5` / `gpt-5.5` | `priority` | $30 |
| `budget-mix` | `gemini-3-flash-preview` | `xai/grok-4-fast` | `gpt-5.3-codex` / `gpt-5.4` | `flex` | $6 |

`--cost-profile` choices derive dynamically from the registry, so all 11 appear in `--help`. Costs depend on cache hit and repair rates.

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

Every profile defines the same four **profile-agnostic** cell keys — `BULK_DOCS_MODEL`, `BULK_CODE_MODEL`, `CE_MODEL`, `SYNTH_MODEL`. `model_map.yaml` lead routes reference them as `${CELL}` placeholders. Override one for a run via:

```bash
# Swap the bulk-docs model to a different Gemini variant just for this run
dopemux rte run --phase A --execute --cost-profile gemini-value \
  --model-alias BULK_DOCS_MODEL=gemini/gemini-3.5-flash
```

The alias value is `provider/model` (anthropic only via `openrouter/`). Override a strict cell only with an OpenAI model — the fail-closed guard rejects non-OpenAI on `CE_MODEL`/`SYNTH_MODEL` before spend.

Or via env var (same key name): `BULK_DOCS_MODEL=gemini/gemini-3.5-flash dopemux rte run ...`.

Precedence: CLI override > env var > profile's `cell_aliases` default.

### Default cell aliases per profile

| Profile | BULK_DOCS_MODEL | BULK_CODE_MODEL | CE_MODEL | SYNTH_MODEL |
|---|---|---|---|---|
| `economy` | `openai/gpt-5.4-mini` | `openai/gpt-5.4-mini` | `openai/gpt-5.1-codex-mini` | `openai/gpt-5.4` |
| `value-default` | `openai/gpt-5.4-mini` | `openai/gpt-5.3-codex` | `openai/gpt-5.3-codex` | `openai/gpt-5.5` |
| `quality` | `openai/gpt-5.4` | `openai/gpt-5.5` | `openai/gpt-5.5` | `openai/gpt-5.5` |
| `experimental` | `gemini/gemini-3.5-flash` | `openai/gpt-5.5` | `openai/gpt-5.5` | `openai/gpt-5.5` |
| `gemini-value` | `gemini/gemini-3-flash-preview` | `gemini/gemini-3.1-pro-preview` | `openai/gpt-5.3-codex` | `openai/gpt-5.5` |
| `grok-fast` | `xai/grok-4-fast` | `xai/grok-4.3` | `openai/gpt-5.3-codex` | `openai/gpt-5.4` |
| `openrouter-resilient` | `openrouter/openai/gpt-5.4-mini` | `openrouter/openai/gpt-5.3-codex` | `openrouter/openai/gpt-5.3-codex` | `openrouter/openai/gpt-5.4` |
| `openai-heavy` | `openai/gpt-5.4-mini` | `openai/gpt-5.3-codex` | `openai/gpt-5.3-codex` | `openai/gpt-5.5` |
| `balanced-mix` | `gemini/gemini-3-flash-preview` | `xai/grok-4.3` | `openai/gpt-5.3-codex` | `openai/gpt-5.5` |
| `quality-mix` | `openai/gpt-5.4` | `openai/gpt-5.3-codex` | `openai/gpt-5.5` | `openai/gpt-5.5` |
| `budget-mix` | `gemini/gemini-3-flash-preview` | `xai/grok-4-fast` | `openai/gpt-5.3-codex` | `openai/gpt-5.4` |

### Cost cap interaction

`value-default` and `quality` ship uncapped (operator sets `--max-cost-usd` explicitly); every other profile carries a default cap (economy $5, budget-mix/grok-fast $6, gemini-value $8, balanced-mix $12, openai-heavy $15, openrouter-resilient $20, experimental $25, quality-mix $30). The profile default applies only if `--max-cost-usd` is not passed. Operator-set caps always win.

The `value-default` and `quality` profiles have NO default cap because the cost depends heavily on the phase scope. Set `--max-cost-usd` explicitly for large runs.

## Why `value-default` is the new default

Per the [Phase D consensus](../../06-research/extraction/rte-cost-profile-redesign/routing-consensus-2026-05.md):

1. The prior `balanced_openrouter` policy was chosen pre-audit, before the current model lineup was available.
2. `balanced_openrouter` routed synthesis/aggregation phases to bulk-tier models — the F2-HIGH-1 audit finding. `value-default` routes strict CE/AGG to `gpt-5.3-codex` / `gpt-5.5` (OpenAI is the only strict-JSON-passthrough provider for these lanes).
3. `value-default` enables cached-input by default (90% discount on repeated prompt prefixes) and flex tier on non-blocking bulk lanes (50% off). Neither was previously wired.
4. Want Claude/Gemini synthesis quality? Those models aren't strict-JSON capable, so they can only serve the non-strict bulk lanes today (use `gemini-value`, `balanced-mix`, etc.). Giving them a synthesis home would require relaxing AGG strictness — a separate change.

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
