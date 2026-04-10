---
id: run-prescan-howto
title: How to Run Prescan
type: how-to
owner: extraction-platform
date: 2026-04-07
status: stable
prelude: Step-by-step guide to running prescan intelligence gathering on your codebase before extraction
---

# How to Run Prescan

Prescan is a pre-extraction intelligence engine that analyzes your codebase to identify redundancy, discover features, and optimize extraction strategy. Run prescan before extraction to get comprehensive context.

## Prerequisites

1. **Python 3.11+** with poetry/pip
2. **API Keys** for LLM providers (XAI, OpenAI, Gemini, or OpenRouter)
3. **Repository** to analyze (can be local or cloned)

## Setup

### Install dependencies
```bash
cd services/repo-truth-extractor
pip install -e .
# or with poetry
poetry install
```

### Set API keys
```bash
# For XAI (default, recommended for cost)
export XAI_API_KEY=your-xai-api-key

# For OpenAI (optional fallback)
export OPENAI_API_KEY=your-openai-api-key

# For Gemini (optional)
export GEMINI_API_KEY=your-gemini-api-key
```

## Quick Start

### Run full prescan
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --output-dir extraction/prescan_output
```

This runs:
- ✅ Corpus walk (enumerate files)
- ✅ Classification (authority, lifecycle)
- ✅ Git enrichment (history, authors)
- ✅ Duplicate detection
- ✅ Code intelligence (AST analysis)
- ✅ All grok passes (dedup, discover, feasibility, optimize)
- ✅ Cost estimation

**Output**: `extraction/prescan_output/prescan_intelligence.json` (main output file)

### Dry run (no LLM calls)
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --output-dir /tmp/prescan_test \
  --dry-run
```

**Time**: ~10 seconds
**Output**: Corpus summary, no grok passes

### Skip expensive operations
```bash
# Skip code analysis (5-10 min saved)
python run_prescan.py \
  --repo-root /path/to/repo \
  --no-code

# Skip git enrichment (1-2 min saved)
python run_prescan.py \
  --repo-root /path/to/repo \
  --no-git

# Both
python run_prescan.py \
  --repo-root /path/to/repo \
  --no-code --no-git
```

## Common Use Cases

### Analyze a monorepo (large codebase)
```bash
python run_prescan.py \
  --repo-root /path/to/monorepo \
  --output-dir prescan_output \
  --max-tokens-per-batch 500000 \
  --batch-mode \
  --passes dedup,discover
```

**Options explained:**
- `--max-tokens-per-batch 500000` — Smaller batches for memory efficiency
- `--batch-mode` — Partition corpus into manageable chunks
- `--passes dedup,discover` — Skip expensive feasibility/optimize passes

### Analyze with project-specific filters
```bash
python run_prescan.py \
  --repo-root . \
  --output-dir prescan_output
```

Then edit `lib/prescan/models.py` config to customize:
```python
config.include_globs = [
    "src/**/*.py",
    "tests/**/*.py",
    "docs/**/*.md",
]
config.exclude_globs = [
    "**/__pycache__/**",
    "**/venv/**",
    "build/**",
    "dist/**",
]
```

### Incremental prescan (reuse previous results)
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --output-dir prescan_output \
  --incremental \
  --passes dedup,discover
```

**What it does:**
- Loads previous `prescan_intelligence.json`
- Reuses code analysis for unchanged files
- Re-analyzes only changed files
- Saves 20-40% time on large codebases

### Prescan for specific language
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --output-dir prescan_output \
  --no-code  # Skip code analysis
```

Then manually set languages:
```python
config.code_languages = ["typescript", "javascript"]
```

## Understanding Output

### Main intelligence file
```bash
# View summary
cat extraction/prescan_output/prescan_intelligence.json | jq .corpus_summary

# Check duplicate candidates
cat extraction/prescan_output/prescan_intelligence.json | jq .duplicate_groups

# View cost estimate
cat extraction/prescan_output/prescan_intelligence.json | jq .cost_estimate
```

### All artifacts
```bash
ls -lh extraction/prescan_output/
```

| File | Size | Purpose |
|------|------|---------|
| `prescan_intelligence.json` | 50-500KB | Main intelligence output |
| `corpus_manifest.json` | 100KB-2MB | Per-file metadata |
| `code_graph.json` | 50-500KB | Dependency graph |
| `prescan_routing_plan.json` | <10KB | LLM model assignments |
| `prescan_batch_plan.json` | <50KB | Token-aware batches |

## Troubleshooting

### "No available routes for required tier"
**Cause**: No LLM provider credentials set
**Fix**: Export API keys
```bash
export XAI_API_KEY=your-key
# or
export OPENAI_API_KEY=your-key
```

### "Process exhausted memory"
**Cause**: Corpus too large for available RAM
**Fix**: Reduce batch size
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --max-tokens-per-batch 300000  # Smaller batches
```

Or skip code analysis:
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --no-code
```

### "Git enrichment failed"
**Cause**: Repository not initialized or .git missing
**Fix**: Skip git enrichment
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --no-git
```

### "Code analysis timed out"
**Cause**: Very large Python/TS/JS file (>1MB)
**Fix**: Skip code analysis or use smaller repo:
```bash
python run_prescan.py \
  --repo-root /path/to/repo \
  --no-code
```

### "JSON validation failed on intelligence output"
**Cause**: Corrupted or incomplete output
**Fix**: Re-run prescan:
```bash
rm -rf prescan_output/
python run_prescan.py \
  --repo-root /path/to/repo \
  --verbose
```

## Via dopemux CLI

If you have dopemux installed:

```bash
dopemux prescan /path/to/repo \
  --output extraction/prescan_output \
  --passes dedup,discover,feasibility,optimize
```

For options:
```bash
dopemux prescan --help
```

## Next Steps

After prescan completes:

1. **Review intelligence** — Examine `prescan_intelligence.json`
2. **Check skip candidates** — Review `extraction_hints.skip_duplicates`
3. **Review cost estimate** — Plan token budget for extraction
4. **Run extraction** — Use prescan output for extraction routing
   ```bash
   python services/repo-truth-extractor/run_extraction_v5.py \
     --repo-root /path/to/repo \
     --prescan-dir extraction/prescan_output
   ```

## Tips

- **First time?** Run with `--dry-run` to check corpus without LLM costs
- **Large repo?** Start with `--no-code --no-git` for fast baseline
- **Cost conscious?** Use XAI (cheaper) or run only `--passes dedup`
- **Tight deadline?** Skip grok passes: `--passes none`
- **Iterating?** Use `--incremental` to reuse results

## See Also

- [Prescan Pipeline Reference](../03-reference/extraction/prescan-pipeline.md) — Full technical docs
- [Extraction Pipeline](./extraction-pipeline.md) — Pre/post-extraction workflow
- [Cost Estimation](../03-reference/cost-estimation.md) — Understanding prescan costs
