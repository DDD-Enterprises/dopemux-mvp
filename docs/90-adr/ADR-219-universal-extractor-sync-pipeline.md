---
title: 'ADR-219: Universal Repo-Truth-Extractor Sync Pipeline'
type: adr
status: active
prelude: Architecture decision for making the repo-truth-extractor work on any codebase
  via feature detection, interactive discovery, and template-driven prompt generation.
tags:
- extractor
- universal
- promptgen
- architecture
id: ADR-219-universal-extractor-sync-pipeline
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-06'
last_review: '2026-03-06'
next_review: '2026-06-04'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-219: Universal Repo-Truth-Extractor Sync Pipeline

## Status
**Active** — Implemented in `services/repo-truth-extractor/lib/promptgen/`

## Context
The repo-truth-extractor v3/v4/v5 pipeline has 98+ prompts hardcoded for dopemux-mvp. Of these, only 34 are truly universal, 13 need scope templatization, and 51 are dopemux-specific. To ship the extractor as a product that works on any codebase, we need:

1. Automatic feature detection to identify what a repo contains
2. Interactive developer confirmation (auto-detection misses things)
3. Template-driven prompt generation with per-repo scope resolution
4. Dynamic contract generation (promptset.yaml, artifacts.yaml, model_map.yaml)
5. Referential integrity validation as a hard gate

## Decision

### Sync Pipeline Architecture

The sync pipeline runs as a linear sequence of stages:

```
fingerprint → feature-detect → phase-plan → interactive-discovery
→ scope-resolve → template-render → contract-generate → integrity-validate
```

Each stage produces a JSON artifact that feeds the next stage.

### Module Design

Eight new modules in `lib/promptgen/`:

| Module | Output | Purpose |
|--------|--------|---------|
| `feature_detector.py` | `AUTO_FEATURES.json` | 30 built-in rules detecting HTTP APIs, databases, CI, etc. |
| `phase_applicability.py` | `PHASE_PLAN.json` | Determine which of 15 phases apply |
| `scope_resolver.py` | `SCOPE_RESOLUTION.json` | Per-step scan root resolution |
| `interactive_discovery.py` | `FEATURE_MAP.json` | Developer-in-the-loop confirmation |
| `template_renderer.py` | Rendered prompts | Jinja2 template rendering |
| `contract_generator.py` | `promptset.yaml`, `artifacts.yaml`, `model_map.yaml` | Dynamic contract generation |
| `integrity_validator.py` | `INTEGRITY_REPORT.json` | Tier 0 referential integrity |
| `sync_engine.py` | `SYNC_MANIFEST.json` | Orchestrator chaining all stages |

### Three-Tier Prompt Classification

- **Universal** (34 prompts): Work on any codebase without modification
- **Scope-specific** (13 prompts): Need path templatization via `{{ scopes.XX }}`
- **Dopemux-only** (51 prompts): Only included when `is_dopemux_repo` is true

### Phase Gating

Each of 15 phases has a `universality` classification:
- `universal`: Always included (A, D, C, E, G, Q, R, X, Z, S)
- `dopemux_only`: Only for dopemux repos (H, T)
- `conditional`: Feature-gated (W, B, M)

Steps within included phases can be individually gated by feature presence.

### CLI Surface

```bash
dopemux extractor init --repo <path>     # Run sync pipeline
dopemux extractor validate --output-dir   # Validate generated promptset
dopemux extractor status --output-dir     # Show sync status
dopemux extractor run --promptset-root    # Execute extraction
```

### v5 Integration

The v5 runner gains `--promptset-root <path>` flag (wires to `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` env var) to consume generated promptsets.

## Consequences

### Positive
- Extractor works on any codebase, not just dopemux
- Interactive discovery catches features auto-detection misses
- Integrity validation prevents broken promptsets from reaching LLMs
- Base prompt templates are version-controlled and auditable
- Feature detection is extensible via custom `FeatureRule` objects

### Negative
- Template rendering adds a new dependency (Jinja2, optional with fallback)
- Interactive mode requires a TTY (non-interactive fallback provided)
- Phase gating adds complexity to the already large pipeline
- 51 dopemux-specific prompts remain hardcoded

### Risks
- Template variables in prompts could break if context schema changes
- Feature detection may miss novel patterns (mitigated by interactive discovery)
- Generated contracts need re-validation after any template change
