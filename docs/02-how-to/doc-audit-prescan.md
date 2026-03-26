---
title: Running the Documentation Pre-Scan Audit
category: how-to
tags:
- documentation
- audit
- grok
- xai
- litellm
- git-intelligence
created: 2026-03-14
updated: 2026-03-14
date: 2026-03-14
author: Dopemux Team
id: doc-audit-prescan
type: how-to
owner: '@hu3mann'
last_review: '2026-03-14'
next_review: '2026-06-14'
prelude: >
  Run the doc_audit_prescan.py script to inventory and classify every text
  surface in the repo by authority class, then run free intelligence passes
  (git, code, architecture, features) to detect duplicates, version chains,
  import graphs, service topology, feature flags, and more — optimising the
  downstream extraction run for cost, speed, and accuracy.
---
# Running the Documentation Pre-Scan Audit

The pre-scan audit inventories every text file in the repo, classifies it by authority class, and optionally runs deep git intelligence passes or calls Grok 4.20 Beta for AI-assisted analysis.

**Key guarantee:** `docs/archive/` and all historical docs are *included*, not excluded — these contain forgotten plans and ideas worth rediscovering.

## Prerequisites

- Python 3.11+ (uses stdlib `tomllib`)
- `rich>=13.0` — for terminal display (already in `pyproject.toml`)
- `openai>=1.0.0` — only for `direct` mode (already in `pyproject.toml`)
- `XAI_API_KEY` in environment — only for `direct` and Grok passes

## Quick Start

```bash
# Step 1: Dry run — safe, no API calls
python scripts/doc_audit_prescan.py dry-run --verbose

# Step 2: Full intelligence passes (free, ~60-90s)
python scripts/doc_audit_prescan.py dry-run --full-passes --force

# Step 3: Inspect the intelligence report
cat extraction/prescan/prescan_intelligence.json | python -m json.tool | head -60

# Step 4a: Run Grok multi-pass analysis (needs XAI_API_KEY)
python scripts/doc_audit_prescan_passes.py --passes all

# Step 4b: OR send to Grok directly for corpus-level classification
python scripts/doc_audit_prescan.py direct --force

# Step 4c: OR write a handoff bundle for LiteLLM/CLI agent
python scripts/doc_audit_prescan.py handoff --force
```

## Execution Modes

### `dry-run` (start here)

Walks the corpus, classifies every file, writes manifests. No network calls.

```bash
python scripts/doc_audit_prescan.py dry-run --verbose
```

Output in `extraction/prescan/`:
- `corpus_manifest.json` — every file with path, size, class, include/exclude reason
- `included_files.txt` — bare path list of included files
- `excluded_files.txt` — excluded paths with reasons
- `corpus_stats.json` — counts/sizes by class, extension, directory
- `run_metadata.json` — timestamp, git SHA, config hash

### `dry-run --git-passes` (recommended)

Adds a second pass using local git history. Free — no API calls.

```bash
python scripts/doc_audit_prescan.py dry-run --git-passes --force
```

Additional output: `extraction/prescan/prescan_intelligence.json` with:

| Field | Description |
|-------|-------------|
| `duplicate_groups` | Files with identical SHA256 hash — safe to skip in extraction |
| `version_chains` | Files with `-v2`, `-2`, `-old` suffixes — compress to evolution summary |
| `ghost_files` | Files deleted from git history — potential hidden context |
| `lifecycle_distribution` | Per-file fresh/active/stale/frozen classification |
| `co_change_groups` | Files always committed together (≥3 co-changes) |
| `planned_features` | TODOs, stubs, proposed ADRs, draft docs |
| `extraction_hints.skip_duplicates` | Exact dedup skip list for extractor |
| `extraction_hints.high_churn_files` | Files changing >1×/month → premium model routing |
| `corpus_health_score` | 0-100 composite health score |

**Ghost file recovery options:**

```bash
# Increase ghost file limit (default 50)
python scripts/doc_audit_prescan.py dry-run --git-passes --max-ghosts 200

# Skip per-file feature gap scan (faster for very large repos)
python scripts/doc_audit_prescan.py dry-run --git-passes --skip-feature-gaps
```

The terminal display renders a full Rich report with health gauge, lifecycle bars, extraction hints, and co-change groups automatically.

### `direct` (needs `XAI_API_KEY`)

Runs dry-run, packages content, calls Grok 4.20 Beta, writes `grok_response.json`.

```bash
export XAI_API_KEY=your-key
python scripts/doc_audit_prescan.py direct --force
```

### `handoff` (always works)

Runs dry-run, packages content, writes a self-contained bundle for a CLI agent or LiteLLM proxy.

```bash
python scripts/doc_audit_prescan.py handoff --force
# See extraction/prescan/handoff_bundle/instructions.md for next steps
```

## Grok Multi-Pass Analysis

`scripts/doc_audit_prescan_passes.py` runs up to four sequential Grok passes, each building on the last:

| Pass | Purpose | Grok input |
|------|---------|-----------|
| `dedup` | Confirm dedup groups; identify version chain compression strategy | Duplicate groups + version chains |
| `discover` | Uncover hidden features, drift, ghost file value, implied ADRs | Ghost files + feature gaps + co-change groups |
| `feasibility` | Evaluate extraction cost/benefit per authority class | Full intelligence report |
| `optimize` | Produce final routing map: skip / compress / premium / standard | Results of all prior passes |

```bash
# Run all passes
python scripts/doc_audit_prescan_passes.py --passes all

# Run specific passes
python scripts/doc_audit_prescan_passes.py --passes dedup,discover

# Custom model
python scripts/doc_audit_prescan_passes.py --passes all --model grok-4.20-beta-0309-non-reasoning
```

Pass results are merged back into `prescan_intelligence.json` under the `grok_passes` key.

## Corpus Size Gate

The default limit is 50MB. Use `--force` to override:

```bash
python scripts/doc_audit_prescan.py dry-run --force
```

Or add tighter exclude globs to `scripts/doc_audit_prescan.toml`.

## Inspecting Results

```bash
# Class breakdown
python -c "import json; d=json.load(open('extraction/prescan/corpus_stats.json')); [print(f'{k}: {v}') for k,v in d['by_class'].items()]"

# Intelligence report highlights
python -c "
import json
d = json.load(open('extraction/prescan/prescan_intelligence.json'))
s = d.get('corpus_summary', {})
print(f'Health: {s.get(\"corpus_health_score\")}/100')
print(f'Lifecycle: {d.get(\"lifecycle_distribution\")}')
print(f'Duplicate groups: {len(d.get(\"duplicate_groups\", {}))}')
print(f'Version chains: {d.get(\"version_chain_count\")}')
print(f'Ghost files: {s.get(\"ghost_files\")}')
"

# Files that were excluded and why
head -20 extraction/prescan/excluded_files.txt

# Check archive/ docs are included
grep 'archive' extraction/prescan/included_files.txt | wc -l
```

## Configuring the Corpus

Edit `scripts/doc_audit_prescan.toml` to add/remove glob patterns:

```toml
[corpus]
exclude_globs = [
    "some/path/**",   # add to tighten corpus
]
```

Or pass globs on the command line:

```bash
python scripts/doc_audit_prescan.py dry-run --exclude "reports/**" --max-corpus-size 60MB
```

## Integration with the Extraction Wizard

The extraction wizard (`dopemux extractor wizard`) runs the prescan automatically as Stage 2 and offers both the git intelligence passes and Grok classification upgrade interactively. The full Rich intelligence report is rendered inline when git passes complete.

The `prescan_intelligence.json` is also mirrored to `services/repo-truth-extractor/runs/00_inputs/PRESCAN_INTELLIGENCE.json` (if the extractor run directory exists) for downstream phase routing.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `🛑 Corpus size exceeds limit` | Add `--force` or tighten exclude globs |
| `❌ XAI_API_KEY not found` | Set env var or switch to `handoff` mode |
| `❌ 'openai' package not installed` | `pip install openai>=1.0.0` |
| Walk takes >60s | Expected — ~150K files are scanned |
| Git passes timeout | Add `--skip-feature-gaps` for repos >10K files |
| Ghost files return junk | Lower `--max-ghosts` or add path filters to `GHOST_EXCLUDE_PATHS` |

## v3.0: Code, Architecture, and Feature Intelligence

Version 3.0 adds three new local analysis passes — all free, no API calls:

### `--code-passes`

Analyses Python files with the stdlib `ast` module:

- **Import graph**: directed graph of all Python imports with orphan and hub detection
- **Entry point detection**: click commands, FastAPI routes, `if __name__` guards
- **Test mapping**: `test_*.py` → `*.py` matching
- **Complexity scoring**: per-file score (0-1) based on LOC, functions, classes, docstring coverage
- **Primary author**: git shortlog per file

```bash
python scripts/doc_audit_prescan.py dry-run --code-passes --force
```

### `--arch-passes`

Maps system topology from local config files:

- **Compose topology**: services, ports, depends_on, networks from `compose.yml`
- **Service registry**: port map + health endpoints from `services/registry.yaml`
- **Event flows**: regex scan for publish/subscribe/emit patterns
- **API surface**: FastAPI/Flask route decorator inventory

```bash
python scripts/doc_audit_prescan.py dry-run --arch-passes --force
```

### `--feature-passes`

Inventories feature surface area:

- **Feature flags**: `ENABLE_*`/`FEATURE_*` env vars and their defaults
- **CLI command tree**: click groups and commands
- **MCP tool inventory**: tool registrations across all MCP servers
- **Completeness scoring**: cross-references tests, docs, and flags per feature

```bash
python scripts/doc_audit_prescan.py dry-run --feature-passes --force
```

### `--full-passes` (recommended)

Runs ALL passes (git + code + arch + features) in one command:

```bash
python scripts/doc_audit_prescan.py dry-run --full-passes --force
```

This produces:
- `prescan_intelligence.json` — complete intelligence report with all sections
- `extraction_skip_list.json` — orphans + duplicates → safe to skip
- `extraction_routing_hints.json` — complexity hotspots → premium model routing
- `extraction_partition_hints.json` — service-based file groupings

## Extraction Artifacts

When code or architecture passes run, the prescan generates advisory artifacts:

| Artifact | Purpose |
|----------|---------|
| `extraction_skip_list.json` | Files to skip (orphans, duplicates) with reasons |
| `extraction_routing_hints.json` | Premium vs economy model routing based on complexity/hub status |
| `extraction_partition_hints.json` | Service-based partition suggestions |

These are written to `extraction/prescan/` and mirrored to `services/repo-truth-extractor/runs/00_inputs/` if available.

The extraction wizard (Stage 6) automatically passes `--prescan-file` to the extractor when these artifacts exist.
