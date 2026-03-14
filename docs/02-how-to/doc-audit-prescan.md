---
title: Running the Documentation Pre-Scan Audit
category: how-to
tags:
- documentation
- audit
- grok
- xai
- litellm
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
  surface in the repo by authority class (canonical/historical/operational/audit/
  template/generated), then optionally call Grok 4.20 Beta or produce a LiteLLM
  handoff bundle for downstream model analysis.
---
# Running the Documentation Pre-Scan Audit

The pre-scan audit inventories every text file in the repo, classifies it by authority class, and optionally sends the corpus to Grok 4.20 Beta for deeper analysis.

**Key guarantee:** `docs/archive/` and all historical docs are *included*, not excluded — these contain forgotten plans and ideas worth rediscovering.

## Prerequisites

- Python 3.11+ (uses stdlib `tomllib`)
- `openai>=1.0.0` — already in `pyproject.toml` (only needed for `direct` mode)
- `XAI_API_KEY` in environment — only for `direct` mode

## Quick Start

```bash
# Step 1: Dry run — safe, no API calls
python scripts/doc_audit_prescan.py dry-run --verbose

# Step 2: Inspect results
cat extraction/prescan/corpus_stats.json | python -m json.tool

# Step 3a: Send to Grok directly (needs XAI_API_KEY)
python scripts/doc_audit_prescan.py direct --force

# Step 3b: OR write a handoff bundle for LiteLLM/CLI agent
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

## Corpus Size Gate

The default limit is 50MB. The current repo corpus is ~54MB, so you need `--force`:

```bash
python scripts/doc_audit_prescan.py dry-run --force
```

Alternatively, add tighter exclude globs to `scripts/doc_audit_prescan.toml` to bring it under the limit.

## Inspecting Results

```bash
# Class breakdown
python -c "import json; d=json.load(open('extraction/prescan/corpus_stats.json')); [print(f'{k}: {v}') for k,v in d['by_class'].items()]"

# How many historical docs
grep -c '"authority_class": "historical"' extraction/prescan/corpus_manifest.json

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

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `🛑 Corpus size exceeds limit` | Add `--force` or tighten exclude globs |
| `❌ XAI_API_KEY not found` | Set env var or switch to `handoff` mode |
| `❌ 'openai' package not installed` | `pip install openai>=1.0.0` |
| Walk takes >60s | Expected — ~150K files are scanned |
