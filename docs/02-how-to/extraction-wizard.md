---
title: "Using the Extraction Wizard"
category: how-to
tags:
  - extraction
  - wizard
  - audit
  - documentation
  - cli
created: 2026-03-14
updated: 2026-03-14
date: 2026-03-14
author: Dopemux Team
id: extraction-wizard
type: how-to
owner: '@hu3mann'
last_review: '2026-03-14'
next_review: '2026-06-14'
prelude: >
  Use the dopemux audit wizard to walk through the complete extraction pipeline
  interactively — from repository health checks through corpus audit, cost
  estimation, and phase-by-phase extraction with educational explanations.
---

# Using the Extraction Wizard

The `dopemux audit wizard` command walks you through the entire extraction
pipeline in an interactive, stage-by-stage flow. By default it runs in
**preview mode** — no API calls are made and nothing is extracted — so you can
safely explore costs, partitions, and pipeline health before committing
resources.

## Quick Start

```bash
# Preview mode (safe, no API calls)
dopemux audit wizard

# With extraction enabled
DPMX_LIVE_OK=1 dopemux audit wizard --execute

# Skip educational panels
dopemux audit wizard --no-educate

# Custom routing policy and workers
DPMX_LIVE_OK=1 dopemux audit wizard --execute --routing-policy quality --workers 1
```

## Prerequisites

- **Python 3.11+**
- **dopemux** installed (`pip install -e .`)
- A **Git repository** (the wizard checks repo health at startup)
- For extraction: **API keys** configured for your chosen routing policy

## The 8 Stages

The wizard progresses through nine numbered stages. Each stage performs a
discrete step in the extraction pipeline and can optionally display an
educational panel explaining what is happening.

| # | Emoji | Stage | What it does |
|---|-------|-------|--------------|
| 0 | 🔬 | **Welcome** | System checks — verifies Python version and git availability |
| 1 | 🩺 | **Repo Health** | Checks git status, current branch, and working-tree cleanliness |
| 2 | 📊 | **Corpus Audit** | Runs the canonical v5 integrated Phase 0 prescan and records reusable prescan artifacts for the current wizard run |
| 3 | ⚙️ | **Prompt Setup** | Validates the promptset configuration used during extraction |
| 4 | 🔑 | **Provider Overrides** | Optional session-local API key overrides for OpenAI, OpenRouter, Gemini, xAI, and Anthropic |
| 5 | 💰 | **Cost Profile** | Interactive browsing and selection from 8 routing policies with per-policy cost estimates and tier-routing detail |
| 6 | 🧩 | **Partition Preview** | Shows the file → phase mapping and partition estimates across 14 extraction phases |
| 7 | 🚀 | **Extraction** | Phase-by-phase extraction with per-phase confirmation (requires the `--execute` flag) |
| 8 | 🏆 | **Summary** | Telemetry, completion stats, and suggested next steps |

## Common Workflows

### First-time audit (preview only)

Launch the wizard directly in preview mode. Stage 2 now runs the canonical v5
integrated prescan itself and reuses that output later in the wizard:

```bash
dopemux audit wizard --no-educate
```

### Budget-conscious extraction

Use the `cost` routing policy and fewer workers to minimise spend:

```bash
DPMX_LIVE_OK=1 dopemux audit wizard --execute --routing-policy cost --workers 1
```

### Full quality extraction

Maximise output quality with the `quality` policy and a larger worker pool:

```bash
DPMX_LIVE_OK=1 dopemux audit wizard --execute --routing-policy quality --workers 1
```

## CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--execute` | off | Enable actual extraction (default: preview only) |
| `--educate` / `--no-educate` | on | Show educational explanations at each stage |
| `--routing-policy` | `cost` | LLM routing policy for extraction |
| `-w`, `--workers` | `1` | Partition worker count |

## Safety Features

- **Preview by default** — the wizard makes no API calls and incurs no cost
  unless you pass `--execute`.
- **Explicit opt-in** — the `--execute` flag must be provided to enable
  extraction.
- **Live consent still required** — live phase execution also requires
  `DPMX_LIVE_OK=1` in the shell environment.
- **Session-local key overrides** — provider overrides entered in the wizard
  apply only to the spawned extraction subprocesses and do not modify local
  shell or repo config.
- **Canonical prescan reuse** — Stage 2 writes v5 prescan artifacts under the
  current run root, and Stage 7 reuses them with `--prescan-dir ... --skip-prescan`
  instead of recomputing Phase 0 for every phase launch.
- **Per-phase confirmation** — before each extraction phase the wizard asks
  for interactive confirmation.
- **No direct script execution** — the wizard never runs
  `run_extraction_v5.py` directly; it delegates to
  `dopemux upgrades run --pipeline-version v5 --ui rich --resume`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Corpus over 50 MB | Start with wizard preview mode and review the integrated Phase 0 prescan output before enabling `--execute` |
| Missing promptset | Stage 3 will guide you through promptset initialisation |
| API key errors | Verify provider credentials in your `.env` file |

## Related

- [Running the Documentation Pre-Scan Audit](doc-audit-prescan.md)
- [Extraction Quickstart Tutorial](../01-tutorials/extraction-quickstart.md)
- [Extraction Wizard Reference](../03-reference/extraction-wizard.md)
