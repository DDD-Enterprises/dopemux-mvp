---
title: "Extraction Quickstart"
category: tutorial
tags:
  - extraction
  - wizard
  - audit
  - getting-started
  - tutorial
created: 2026-03-14
updated: 2026-03-14
date: 2026-03-14
author: Dopemux Team
id: extraction-quickstart
type: tutorial
owner: '@hu3mann'
last_review: '2026-03-14'
next_review: '2026-06-14'
prelude: >
  End-to-end tutorial for running your first documentation extraction — from
  repository pre-scan through cost estimation to phase-by-phase extraction
  using the dopemux audit wizard.
---

# Extraction Quickstart

## What You'll Learn

By the end of this tutorial you'll have:

- Scanned your repository corpus and understood the 6 authority classes
- Selected a cost-optimized routing policy for your budget
- Run a preview of the complete extraction pipeline
- (Optionally) executed a real extraction across all 14 phases

## Prerequisites

- dopemux installed: `pip install -e .`
- A git repository to analyze
- For real extraction: API keys for at least one LLM provider

## Step 1: Scan Your Repository

The first step is understanding what's in your repo. The **prescan** tool walks every file and classifies it into one of 6 authority classes:

| Class | What it means |
|-------|--------------|
| 🟢 canonical | Source-of-truth docs and core code |
| 🔵 historical | Archived content, session notes, completed work |
| 🟡 operational | Scripts, configs, tooling |
| 🟠 audit | Reports, analysis artifacts, reviews |
| 🟣 template | Templates, examples, boilerplate |
| ⚪ generated | Lock files, builds, caches |

Run the prescan:

```bash
dopemux audit prescan --verbose
```

If your corpus exceeds 50 MB, add `--force`:

```bash
dopemux audit prescan --verbose --force
```

Check the output in `extraction/prescan/`:

- `corpus_manifest.json` — every included file with classification
- `corpus_stats.json` — aggregate statistics by authority class
- `run_metadata.json` — run configuration and timing

## Step 2: Launch the Wizard (Preview Mode)

Now launch the interactive wizard in preview mode (the default — safe, no API calls):

```bash
dopemux audit wizard
```

The wizard walks you through 8 stages:

1. **🔬 Welcome** — Verifies your Python, git, and system setup
2. **🩺 Repo Health** — Checks your git branch, working tree status
3. **📊 Corpus Audit** — Re-runs the prescan and shows a beautiful summary table
4. **⚙️ Prompt Setup** — Validates your promptset configuration
5. **💰 Cost Profile** — The fun part! Choose from 8 routing policies:

   | Policy | Approx. Cost | Best For |
   |--------|-------------|----------|
   | cost | Lowest | Testing, exploration |
   | balanced_openrouter | Mid-range (default) | Production runs |
   | quality | Higher | Critical documentation |
   | optimal | Highest | Maximum accuracy |

6. **🧩 Partition Preview** — See how files map to the 14 extraction phases
7. **🚀 Extraction** — In preview mode, shows what WOULD happen
8. **🏆 Summary** — Complete overview of the planned extraction

> 💡 **Tip:** The wizard includes educational panels explaining each concept. To skip them: `dopemux audit wizard --no-educate`

## Step 3: Understand the 14 Phases

The extraction pipeline processes your repo in 14 phases:

| Phase | Name | What it extracts |
|-------|------|-----------------|
| A | 🏗️ Repo Control Plane | Repo structure, entry points, configs |
| H | 🏠 Home Control Plane | User directory configs, dotfiles |
| D | 📚 Docs Pipeline | Documentation files and relationships |
| C | 💻 Code Surfaces | APIs, interfaces, public surfaces |
| E | ⚡ Execution Plane | Runtime behavior, scripts |
| W | 🔄 Workflow Plane | CI/CD, GitHub Actions |
| B | 🔒 Boundary Contracts | API contracts, schemas |
| G | 📋 Governance Plane | Policies, compliance |
| Q | ✅ Quality Assurance | Cross-check quality |
| R | ⚖️ Arbitration | Resolve conflicts |
| X | 🗂️ Feature Index | Build feature index |
| T | 📦 Task Packets | Generate work packets |
| Z | 🧊 Handoff Freeze | Create frozen snapshot |
| S | 🧬 Synthesis | Final combined truth |

Phases A–G extract from files directly. Phases Q–S are "meta" phases that process outputs from earlier phases.

## Step 4: Run a Real Extraction (Optional)

When you're ready to run for real, add `--execute`:

```bash
dopemux audit wizard --execute --routing-policy balanced_openrouter
```

The wizard will:

- Show you the estimated cost before proceeding
- Ask for confirmation before EACH phase
- Display live output as each phase runs
- Show a final summary with timing and results

### Budget-conscious first run

```bash
dopemux audit wizard --execute --routing-policy cost --workers 5
```

### High-quality production run

```bash
dopemux audit wizard --execute --routing-policy quality --workers 15
```

## Step 5: Check Your Results

After extraction, check the status:

```bash
dopemux audit status
```

Results are stored in `extraction/repo-truth-extractor/v5/runs/<RUN_ID>/` with one subdirectory per phase.

## What's Next?

- **Explore results:** Browse the extraction output in `extraction/repo-truth-extractor/v5/runs/`
- **Re-run specific phases:** Use `dopemux extract truth-run --phase D` to re-run just the docs phase
- **Adjust routing:** Try different policies to balance cost vs. quality
- **Deep dive:** Read the [Extraction Wizard Reference](../03-reference/extraction-wizard.md) for all options

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Corpus over 50 MB | `dopemux audit prescan --force` |
| Missing promptset | Wizard Stage 3 guides setup |
| API key errors | Check `.env` for provider keys |
| Phase fails | Re-run with `--resume` flag on truth-run |

## Related Guides

- [Using the Extraction Wizard](../02-how-to/extraction-wizard.md) — task-oriented how-to
- [Extraction Wizard Reference](../03-reference/extraction-wizard.md) — complete CLI reference
- [Running the Documentation Pre-Scan Audit](../02-how-to/doc-audit-prescan.md) — prescan deep-dive
