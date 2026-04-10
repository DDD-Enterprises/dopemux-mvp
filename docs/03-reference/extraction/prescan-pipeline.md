---
id: prescan-pipeline-ref
title: Prescan Pipeline Reference
type: reference
owner: extraction-platform
author: '@hu3mann'
date: 2026-04-07
last_review: 2026-04-09
next_review: 2026-07-08
status: stable
prelude: Complete reference for the prescan library architecture, configuration, intelligence schema, and integration with v5 extractor
---

# Prescan Pipeline Reference

The prescan library provides pre-extraction intelligence gathering for the repo-truth-extractor. It analyzes a codebase to identify redundancy, discover hidden features, assess extraction feasibility, and optimize extraction parameters.

## Architecture Overview

Prescan operates in 11 sequential stages:

1. **Corpus Walk** — Enumerate files respecting ignore patterns
2. **Classification** — Categorize files by authority (source, test, config, artifact, etc.)
3. **Git Enrichment** — Annotate with commit history, lifecycle stage, authorship
4. **Duplicate Detection** — Group duplicate/near-duplicate files
5. **Version Chain Detection** — Identify version sequences (v1, v2, etc.)
6. **Code Intelligence (AST)** — Extract function signatures, complexity, imports
7. **Dependency Graph** — Build call graph and import relationships
8. **Feature Gap Analysis** — Find TODO markers, stubs, draft docs, proposed ADRs
9. **Cost Estimation** — Estimate extraction costs for each pass
10. **Batch Planning** — Partition corpus into token-aware batches
11. **Grok Passes** — Multi-stage LLM analysis (dedup, discover, feasibility, optimize)

## Core Components

### PrescanEngine

**Location**: `lib/prescan/engine.py`

Orchestrates the full pipeline. Main entry point.

```python
from lib.prescan import PrescanEngine, PrescanConfig

config = PrescanConfig(
    repo_root=Path("/path/to/repo"),
    output_dir=Path("extraction/prescan_output"),
    enable_code_prescan=True,
    enable_git_enrichment=True,
    batch_mode=True,
    cost_estimate=True,
)

engine = PrescanEngine(config)
result = engine.run(
    passes=["dedup", "discover", "feasibility", "optimize"],
    incremental=False,
)

if result.success:
    print(f"Analyzed {result.file_count} files in {result.duration_seconds}s")
    intelligence = json.load(result.intelligence_path.open())
```

### PrescanConfig

**Location**: `lib/prescan/models.py`

Configuration dataclass controlling pipeline behavior.

```python
@dataclass
class PrescanConfig:
    repo_root: Path              # Repository to scan
    output_dir: Path             # Output directory for artifacts

    # Corpus filtering
    max_file_size: int = 100 * 1024           # Skip files >100KB
    max_corpus_size: int = 50 * 1024 * 1024  # Skip if corpus >50MB
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)

    # LLM configuration
    model: str = "grok-4.20-beta-0309-non-reasoning"
    provider: str = "xai"
    api_key_env: str = "XAI_API_KEY"
    temperature: float = 0.1
    max_response_tokens: int = 200000

    # Feature flags
    enable_code_prescan: bool = True
    enable_git_enrichment: bool = True
    cost_estimate: bool = True
    batch_mode: bool = True
    incremental: bool = False
    deep_mode: bool = False

    # Batching
    max_tokens_per_batch: int = 1_500_000
    chars_per_token: float = 4.0

    # Incremental mode
    incremental_baseline: str | None = None
```

### Intelligence Schema

**Output**: `prescan_intelligence.json`

Complete context summary for extraction.

```json
{
  "version": "2.0.0",
  "generated_at": "2026-04-07T12:34:56Z",
  "repo_root": "/path/to/repo",

  "corpus_summary": {
    "total_files_scanned": 1250,
    "included_files": 980,
    "excluded_files": 270,
    "ghost_files": 15,
    "total_included_size_bytes": 52_000_000,
    "by_authority_class": {
      "source": 450,
      "test": 380,
      "config": 120,
      "artifact": 30
    },
    "by_extension": {
      "py": 520,
      "ts": 280,
      "json": 140,
      "md": 40
    },
    "corpus_health_score": 92
  },

  "lifecycle_distribution": {
    "active": 780,
    "stale": 150,
    "frozen": 50,
    "unknown": 0
  },

  "duplicate_groups": {
    "dup-001": ["file1.py", "file1_backup.py"],
    "dup-002": ["config.json", "config.old.json"]
  },

  "version_chains": {
    "chain-001": [
      {"path": "v0.1/module.py", "ordinal": 0, "is_latest": false},
      {"path": "v0.2/module.py", "ordinal": 1, "is_latest": false},
      {"path": "module.py", "ordinal": 2, "is_latest": true}
    ]
  },
  "version_chain_count": 12,
  "compression_potential_files": 8,

  "ghost_files": [
    {
      "path": "deleted-feature.py",
      "deleted_at_sha": "abc123def",
      "deleted_date": "2025-06-15",
      "recovery_source": "git-history"
    }
  ],

  "planned_features": {
    "proposed_adrs": ["docs/adr/0042-new-auth.md"],
    "stub_files": ["src/payment_processor.py"],
    "todo_files": ["src/search_index.py"],
    "draft_docs": ["docs/guides/advanced-usage.md"]
  },

  "code_intelligence": {
    "analyzed_files": 450,
    "api_surfaces": ["FastAPI", "Click", "Typer"],
    "dependency_clusters": [["auth.py", "session.py", "jwt.py"]],
    "topological_order": ["core", "middleware", "routes"]
  },

  "extraction_hints": {
    "skip_duplicates": ["file_backup.py", "config.old.json"],
    "high_churn_files": ["schema_migrations.py", "config.py"],
    "compress_candidates": []
  },

  "cost_estimate": {
    "dedup_pass": {"input_tokens": 50000, "output_tokens": 5000, "estimated_cost_usd": 0.50},
    "discover_pass": {"input_tokens": 75000, "output_tokens": 12000, "estimated_cost_usd": 0.90},
    "total_estimated_cost_usd": 3.50
  },

  "grok_passes": {
    "dedup": { "result_summary": "..." },
    "discover": { "result_summary": "..." },
    "feasibility": { "result_summary": "..." },
    "optimize": { "result_summary": "..." }
  }
}
```

## Grok Passes

Multi-stage LLM passes that refine extraction strategy.

### Dedup Pass
Identifies and ranks duplicates for safe skipping.
- Required tier: `cheap_structured`
- Input: Duplicate groups, version chains
- Output: Ranking, skip candidates

### Discover Pass
Finds hidden features, undocumented APIs, edge cases.
- Required tier: `cheap_structured`
- Input: Code signatures, imports
- Output: Feature discoveries, risk flags

### Feasibility Pass
Assesses extraction difficulty per component.
- Required tier: `balanced_analysis`
- Input: Code complexity, dependencies
- Output: Feasibility scores, warnings

### Optimize Pass
Generates optimal extraction strategy with cost/quality tradeoff.
- Required tier: `premium_planning`
- Input: All prior intelligence
- Output: Final extraction plan with token budgets

## Output Artifacts

| File | Purpose | Format |
|------|---------|--------|
| `prescan_intelligence.json` | Main intelligence output | JSON |
| `corpus_manifest.json` | Per-file metadata | JSON |
| `code_graph.json` | Dependency relationships | JSON |
| `prescan_provider_model_catalog.json` | Available LLM providers | JSON |
| `prescan_routing_plan.json` | Model assignments per pass | JSON |
| `prescan_batch_plan.json` | Token-aware partitions | JSON |

## Integration with v5 Extractor

The `IntelligenceRouter` bridges prescan output to `run_extraction_v5.py`.

```python
from lib.intelligence_router import IntelligenceRouter

router = IntelligenceRouter(
    prescan_output_dir=Path("extraction/prescan_output"),
)

# Get routing hints for extraction
skip_files = router.get_skip_candidates()        # Duplicates to skip
prioritized = router.get_prioritized_order()    # Optimal processing order
batches = router.get_token_aware_batches()      # Pre-planned token batches
```

## Configuration Options

### Corpus Filtering
```python
config.include_globs = ["src/**/*.py", "tests/**/*.py"]
config.exclude_globs = ["**/*.pyc", "**/venv/**"]
```

### Code Intelligence
```python
config.enable_code_prescan = True           # AST analysis
config.code_languages = ["python", "typescript"]
```

### Git Enrichment
```python
config.enable_git_enrichment = True         # Commit history, authors
```

### Batching
```python
config.batch_mode = True
config.max_tokens_per_batch = 1_500_000    # 1.5M tokens per batch
config.chars_per_token = 4.0                # Estimation ratio
```

### Incremental Mode
```python
config.incremental = True
config.incremental_baseline = "HEAD~5"  # Reanalyze last 5 commits
```

### Deep Mode
```python
config.deep_mode = True  # Include archived/historical files
```

## Running Prescan

### Via dopemux CLI
```bash
dopemux prescan /path/to/repo --output extraction/prescan_output
```

### Via Standalone CLI
```bash
cd services/repo-truth-extractor
python run_prescan.py \
  --repo-root /path/to/repo \
  --output-dir extraction/prescan_output \
  --passes dedup,discover,feasibility,optimize \
  --code --git --incremental
```

### Programmatically
```python
from lib.prescan import PrescanEngine, PrescanConfig

config = PrescanConfig(repo_root=Path("."), output_dir=Path("prescan_out"))
engine = PrescanEngine(config)
result = engine.run(passes=["dedup", "discover"])
print(result.intelligence_path)
```

## Troubleshooting

### No LLM providers available
Ensure API key environment variables are set:
```bash
export XAI_API_KEY=your-key
export OPENAI_API_KEY=your-key
```

### Memory exhaustion on large repos
Reduce `max_corpus_size` or `max_tokens_per_batch`:
```python
config.max_corpus_size = 20 * 1024 * 1024  # 20MB limit
config.max_tokens_per_batch = 500_000      # Smaller batches
```

### Missing git metadata
Run with `--no-git` flag:
```bash
python run_prescan.py --repo-root . --no-git
```

## See Also

- [How to Run Prescan](../02-how-to/extraction/run-prescan.md) — Quick start guide
- [Extraction Pipeline](./pipeline-phases.md) — Pre-extraction to post-processing
- [IntelligenceRouter](./intelligence-router.md) — Prescan output integration
