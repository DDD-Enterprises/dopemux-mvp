---
title: "Extraction Wizard — Reference"
category: reference
tags:
  - extraction
  - wizard
  - audit
  - cli
  - cost-estimation
  - routing
created: 2026-03-14
updated: 2026-03-14
date: 2026-03-14
author: Dopemux Team
id: extraction-wizard-reference
type: reference
owner: '@hu3mann'
last_review: '2026-03-14'
next_review: '2026-06-14'
prelude: >
  Complete reference for the dopemux audit wizard — an interactive CLI that
  guides users through repository health checks, corpus classification, cost
  estimation across 8 routing policies, and phase-by-phase extraction using
  the repo-truth-extractor pipeline.
---

# Extraction Wizard — Reference

## CLI Commands

### `dopemux audit` — Command Group

```
Usage: dopemux audit [OPTIONS] COMMAND [ARGS]...

Commands:
  prescan  📊 Run documentation corpus pre-scan audit
  wizard   🧙 Guided extraction wizard — interactive walkthrough
  status   📋 Show status of last extraction run
```

### `dopemux audit prescan`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | off | Show detailed output |
| `--force` | flag | off | Skip corpus size safety limit (50 MB) |
| `--config` | PATH | None | Custom TOML config path |

### `dopemux audit wizard`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--execute` | flag | off | Enable actual extraction |
| `--educate/--no-educate` | flag | on | Educational explanations |
| `--routing-policy` | text | balanced_openrouter | Routing policy name |
| `-w, --workers` | int | 10 | Partition worker count |

### `dopemux audit status`

No options. Shows latest run ID, directory, phases completed, and total size.

---

## Wizard Stages

| # | Name | Icon | Module | Description |
|---|------|------|--------|-------------|
| 0 | Welcome | 🔬 | `preflight.py` | System checks — Python version, git, dependencies |
| 1 | Repo Health | 🩺 | `preflight.py` | Git status, branch, working tree cleanliness |
| 2 | Corpus Audit | 📊 | `corpus.py` | Runs prescan subprocess, parses JSON stats |
| 3 | Prompt Setup | ⚙️ | `prompts.py` | Promptset validation and interactive initialization |
| 4 | Cost Profile | 💰 | `cost_profiles.py` | Interactive routing policy selection with estimates |
| 5 | Partition Preview | 🧩 | `partitions.py` | File→phase mapping and partition estimates |
| 6 | Extraction | 🚀 | `extraction.py` | Per-phase truth-run delegation with confirmation |
| 7 | Summary | 🏆 | `summary.py` | Telemetry parsing and completion display |

---

## Extraction Phases

The pipeline defines **14 phases** executed in order. Phases A–G produce primary extractions; Q–S are meta phases that operate on prior outputs.

| Phase | Name | Icon | Description |
|-------|------|------|-------------|
| A | Repo Control Plane | 🏗️ | Repo structure, entry points, configuration |
| H | Home Control Plane | 🏠 | User/home directory config and dotfiles |
| D | Docs Pipeline | 📚 | Documentation files and relationships |
| C | Code Surfaces | 💻 | Code interfaces, APIs, public surfaces |
| E | Execution Plane | ⚡ | Runtime behavior, scripts, execution paths |
| W | Workflow Plane | 🔄 | CI/CD workflows, GitHub Actions, automation |
| B | Boundary Contracts | 🔒 | API contracts, schema boundaries, interfaces |
| G | Governance Plane | 📋 | Governance rules, policies, compliance |
| Q | Quality Assurance | ✅ | Cross-checks extraction quality/consistency |
| R | Arbitration | ⚖️ | Reconciles conflicts between phases |
| X | Feature Index | 🗂️ | Searchable feature index from extractions |
| T | Task Packets | 📦 | Task-oriented work packets from findings |
| Z | Handoff Freeze | 🧊 | Frozen snapshot for handoff |
| S | Synthesis | 🧬 | Final synthesis combining all phases |

> **Note:** Meta phases (R, X, Z, S) have no direct file mapping and operate exclusively on outputs of earlier phases.

---

## Authority Classes

Every file in the corpus is classified into one of six authority classes during the prescan audit.

| Class | Icon | Color | Description |
|-------|------|-------|-------------|
| canonical | 🟢 | green | Primary source-of-truth documentation and code |
| historical | 🔵 | blue | Archived content providing historical context |
| operational | 🟡 | yellow | Scripts, configs, and operational tooling |
| audit | 🟠 | dark_orange | Audit reports, analysis artifacts, review notes |
| template | 🟣 | magenta | Templates, examples, and boilerplate |
| generated | ⚪ | white | Auto-generated files (lock files, builds, caches) |

---

## Routing Policies

Eight routing policies control which models handle each extraction tier. The default policy is `balanced_openrouter`.

| Policy | Description | Bulk Tier | Extract Tier | Synthesis Tier | QA Tier |
|--------|-------------|-----------|-------------|---------------|---------|
| cost | Budget | gpt-5-nano | gemini-2.5-flash | gpt-5-mini | grok-code-fast-1 |
| balanced | Mid-range | gpt-5-mini | gpt-5.1 | gemini-2.5-pro | gpt-5.2 |
| balanced_openrouter | Default (v5) | gpt-5-mini | gpt-5.1 | gemini-2.5-pro | gpt-5.2 |
| balanced_grok_openrouter | Grok primary | grok-code-fast-1 | grok-4-1-fast | gemini-2.5-pro | gpt-5.1 |
| quality | Premium | gpt-5.1 | gpt-5.2 | gemini-3-pro | claude-sonnet-4-5 |
| openrouter | Pure OR | gpt-5-mini | gpt-5.1 | gemini-2.5-pro | gpt-5.2 |
| gemini_primary | Gemini-first | gemini-3-flash | gemini-3-pro | gemini-2.5-pro | gpt-5.1 |
| optimal | Best | grok-4.20-beta | gpt-5.4 | gemini-3-pro | claude-sonnet-4-5 |

### Tier Weights for Cost Estimation

| Tier | Weight |
|------|--------|
| Bulk | 50% |
| Extract | 30% |
| Synthesis | 15% |
| QA | 5% |

---

## Model Pricing

Per 1 M tokens.

| Model | Input | Output |
|-------|-------|--------|
| gpt-5-nano | $0.10 | $0.40 |
| gpt-5-mini | $0.40 | $1.60 |
| gpt-5.1 | $1.00 | $4.00 |
| gpt-5.2 | $2.00 | $8.00 |
| gpt-5.4 | $5.00 | $20.00 |
| gemini-2.5-flash | $0.15 | $0.60 |
| gemini-2.5-pro | $1.25 | $10.00 |
| gemini-3-pro | $1.25 | $10.00 |
| gemini-3-flash | $0.10 | $0.40 |
| grok-code-fast-1 | $0.10 | $0.40 |
| grok-4-1-fast-non-reasoning | $0.50 | $2.00 |
| grok-4.20-beta (non-reasoning) | $2.00 | $8.00 |
| grok-4.20-beta (reasoning) | $3.00 | $15.00 |
| claude-sonnet-4-5 | $3.00 | $15.00 |
| claude-opus-4-6 | $15.00 | $75.00 |

---

## Package Structure

```
src/dopemux/ux/wizard/
├── __init__.py          # Exports WizardRunner
├── stages.py            # StageStatus, StageResult, WizardState dataclasses + constants
├── display.py           # Rich rendering helpers (10 functions)
├── preflight.py         # Stages 0-1: welcome + repo health
├── corpus.py            # Stage 2: prescan audit
├── prompts.py           # Stage 3: promptset validation
├── cost_profiles.py     # Stage 4: routing policies + cost estimation
├── partitions.py        # Stage 5: file→phase mapping
├── extraction.py        # Stage 6: phase-by-phase extraction
├── summary.py           # Stage 7: telemetry + completion
└── runner.py            # WizardRunner orchestrator class
```

---

## Safety Constraints

- **Preview-only by default** — no API calls are made without the `--execute` flag.
- **Per-phase confirmation** — each extraction phase requires interactive confirmation before proceeding.
- **Static routing snapshot** — `ROUTING_LADDERS` is defined as a static snapshot inside the wizard to avoid importing `run_extraction_v5.py`, which has import-time side effects.
- **No direct v5 execution** — `run_extraction_v5.py` is **never** executed directly. All extraction is delegated through `dopemux extract truth-run`.
- ⚠️ **CRITICAL:** Accidental direct execution of v5 can cost **$10+** in provider preflight probes. See the workspace safety instructions for details.

---

## Related

- [Using the Extraction Wizard](../02-how-to/extraction-wizard.md)
- [Extraction Quickstart](../01-tutorials/extraction-quickstart.md)
- [Running the Documentation Pre-Scan Audit](../02-how-to/doc-audit-prescan.md)
- [doc_audit_prescan.py Reference](doc-audit-prescan.md)
