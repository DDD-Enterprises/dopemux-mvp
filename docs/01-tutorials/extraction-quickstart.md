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
updated: 2026-07-27
date: 2026-03-14
author: Dopemux Team
id: extraction-quickstart
type: tutorial
owner: '@hu3mann'
last_review: '2026-07-27'
next_review: '2026-10-27'
prelude: >
  End-to-end tutorial for running your first documentation extraction — from
  repository pre-scan through cost estimation to phase-by-phase extraction
  using the dopemux rte wizard.
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
dopemux rte wizard
```

> `dopemux rte` is the canonical namespace for Repo Truth Extractor
> operations. `dopemux audit wizard` still works — it is the exact same
> command — but new instructions in this tutorial use `rte`.

The wizard walks you through 9 numbered stages (0–8):

0. **🔬 Welcome** — Verifies your Python, git, and system setup
1. **🩺 Repo Health** — Checks your git branch, working tree status
2. **📊 Corpus Audit** — Runs the canonical v5 integrated prescan and shows a summary table
3. **⚙️ Prompt Setup** — Validates your promptset configuration
4. **🔑 Provider Overrides** — Optional session-local API key overrides
5. **💰 Cost Profile** — The fun part! Choose from 8 routing policies:

   | Policy | Approx. Cost | Best For |
   |--------|-------------|----------|
   | cost | Lowest (wizard default) | Testing, exploration, bounded first runs |
   | balanced_openrouter | Mid-range | Production runs |
   | quality | Higher | Critical documentation |
   | optimal | Highest | Maximum accuracy |

6. **🧩 Partition Preview** — See how files map to the 14 extraction phases
7. **🚀 Extraction** — In preview mode, shows what WOULD happen
8. **🏆 Summary** — Complete overview of the planned extraction

> 💡 **Tip:** The wizard includes educational panels explaining each concept. To skip them: `dopemux rte wizard --no-educate`

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

A live run costs real money and can take **hours, not minutes** for the full
14-phase pipeline — read this whole step before you commit.

Live phase execution is gated behind two separate, deliberate opt-ins:

1. The `--execute` flag on the wizard invocation itself.
2. The `DPMX_LIVE_OK=1` environment variable, checked right before the first
   phase prompt. Without it, `--execute` fails closed with an explicit error
   instead of silently running in preview mode.

```bash
DPMX_LIVE_OK=1 dopemux rte wizard --execute --routing-policy cost
```

(`balanced_openrouter` is a valid, pricier policy — it is **not** the
wizard's default; the wizard defaults `--routing-policy` to `cost` when you
omit the flag.)

The wizard will:

- Show you the estimated cost before proceeding
- Ask for confirmation before EACH phase
- Display live output as each phase runs
- Show a final summary with timing and results

### Budget-conscious first run

Keep `--workers 1` (the default) for your first live run — it keeps output
deterministic and easy to follow. Higher worker counts increase parallelism
(and therefore concurrent spend) once you're comfortable with the flow.

```bash
DPMX_LIVE_OK=1 dopemux rte wizard --execute --routing-policy cost --workers 1
```

### High-quality production run

```bash
DPMX_LIVE_OK=1 dopemux rte wizard --execute --routing-policy quality --workers 1
```

## Step 5: Check Your Results

After extraction, check the status:

```bash
dopemux audit status
```

`dopemux rte status --run-id <RUN_ID>` is the more capable equivalent (works
across v5/v4/v3 pipelines and supports `--json`), but pass an explicit
`--run-id` — invoking it with no arguments does not simply read the latest
run the way `dopemux audit status` does.

Results are stored in `extraction/repo-truth-extractor/v5/runs/<RUN_ID>/` with one subdirectory per phase.

## What's Next?

- **Explore results:** Browse the extraction output in `extraction/repo-truth-extractor/v5/runs/`
- **Re-run specific phases:** `dopemux rte run --phase D --resume` re-runs just the docs phase and resumes from where a prior attempt left off (`--resume` is on by default). `dopemux extract truth-run` is a **disabled legacy command** — it raises "Legacy command disabled. Use `dopemux rte run`..." unconditionally.
- **Diagnose failed partitions:** `dopemux rte doctor --run-id <RUN_ID>` inspects a run and plans deterministic re-processing.
- **Adjust routing:** Try different policies to balance cost vs. quality
- **Deep dive:** Read the [Extraction Wizard Reference](../03-reference/extraction-wizard.md) for all options

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Corpus over 50 MB | `dopemux audit prescan --force` |
| Missing promptset | Wizard Stage 3 guides setup |
| API key errors | Check `.env` for provider keys |
| Phase fails | `dopemux rte run --phase <X> --resume` (default) or `dopemux rte doctor --run-id <RUN_ID>` to diagnose failed partitions |
| `--execute` fails at the first phase prompt | Set `DPMX_LIVE_OK=1` in your shell before invoking the wizard — it is a separate consent gate from `--execute` |

## Related Guides

- [Using the Extraction Wizard](../02-how-to/extraction-wizard.md) — task-oriented how-to
- [Extraction Wizard Reference](../03-reference/extraction-wizard.md) — complete CLI reference
- [Running the Documentation Pre-Scan Audit](../02-how-to/doc-audit-prescan.md) — prescan deep-dive
