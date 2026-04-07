---
id: V5_EXTRACTION_PIPELINE_UPGRADE_DESIGN
title: V5 Extraction Pipeline Upgrade Design
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-04-06'
next_review: '2026-07-06'
prelude: V5 Extraction Pipeline Upgrade Design (explanation) for dopemux documentation
  and developer workflows.
---
# V5 Extraction Pipeline Upgrade -- Architecture & Design Document

**Status**: COMPLETED
**Date**: 2026-03-18
**Scope**: Prescan CLI integration, code-focused prescan, AST-enhanced intelligence, intelligent input bundling, pipeline integration points

## 0. Current branch reality check

This design document predates the bounded runtime validation packets. The
current branch has additionally proven one narrow live lane:

- phase `A`
- step `A2`
- routing `balanced_grok_openrouter`

What is runtime-earned on this branch:

- validator and live command coherence for that bounded lane
- truthful `COST_ABORTED` propagation from raw failures into aggregate artifacts
- repair-provenance rollups that count one logical repair event once
- explicit output-safety at JSON write and response-repair log sinks

What remains broader design intent rather than universally re-proven:

- every other policy lane
- every other phase/step combination
- universal extractor behavior outside the bounded lane

---

## 1. Architecture Overview

### 1.1 Current State (As-Is)

```
[standalone script]          [CLI]                     [v5 runner]
doc_audit_prescan.py ──> extraction/prescan/    (not connected)    run_extraction_v5.py
doc_audit_prescan_passes.py                     (not connected)    lib/promptgen/sync_engine.py
                                                                   lib/promptgen/feature_detector.py
                                                                   lib/chunking.py

[dope-context]
code_chunker.py (Tree-sitter, Python/JS/TS)
grok_generator.py (FREE Grok context generation)
```

**Key gaps**: The three systems (prescan scripts, CLI, v5 runner) are islands. Prescan intelligence is generated but never consumed by the extraction pipeline. Code analysis is Python-only via `ast` module.

### 1.2 Target State (To-Be)

```
                              dopemux extractor prescan
                                       |
                     +----------------------------------+
                     |         Prescan Engine            |
                     |  (doc prescan + code prescan)     |
                     +----------------------------------+
                                       |
                          prescan_intelligence.json
                          code_intelligence.json
                                       |
                     +----------------------------------+
                     |      Intelligence Router          |
                     |  (merges prescan into pipeline)   |
                     +----------------------------------+
                           /          |           \
                    sync_engine   chunking.py   run_extraction_v5.py
                    (enhanced     (smart         (phase routing,
                     features)    bundling)       skip/compress)
```

### 1.3 Data Flow (Full Pipeline)

```
1. dopemux extractor prescan [--passes dedup,discover,feasibility,optimize]
   |
   +--> walk_corpus() -----> FileEntry[] (doc + code files)
   +--> classify_files() --> authority_class per file
   +--> enrich_git() ------> lifecycle, churn, version chains
   +--> code_prescan() ----> Tree-sitter AST analysis (multi-language)
   +--> [optional] grok_passes() --> dedup/discover/feasibility/optimize
   |
   v
   extraction/prescan/
     prescan_intelligence.json   (doc intelligence + code intelligence)
     corpus_manifest.json        (per-file metadata)
     code_graph.json             (dependency graph, edges, clusters)
     pass_*_result.json          (Grok pass outputs)

2. dopemux extractor init [--prescan extraction/prescan]
   |
   +--> sync_engine reads prescan_intelligence.json
   +--> feature_detector enhanced with code_intelligence
   +--> phase_applicability uses OPTIMIZE routing overrides
   +--> scope_resolver uses dependency graph for grouping
   +--> template_renderer uses prescan skip/compress lists
   |
   v
   promptsets/generated/<repo-hash>/
     promptset.yaml (with prescan-informed phase plan)

3. dopemux extractor run [--prescan extraction/prescan]
   |
   +--> intelligence_router reads prescan_intelligence.json
   +--> chunking.py uses code_graph for smart bundling
   +--> skip_list applied before partitioning
   +--> compress_chains send summaries instead of files
   +--> model_routing_hints select fast vs premium per partition
```

---

## 2. Component Designs

### 2.1 Prescan Engine (refactored from scripts/)

**Location**: `services/repo-truth-extractor/lib/prescan/`

This is a library extraction of the standalone scripts into importable modules. The scripts themselves become thin CLI wrappers.

#### Module Structure

```
services/repo-truth-extractor/lib/prescan/
  __init__.py
  engine.py           # Main PrescanEngine class (orchestrates all steps)
  corpus_walker.py    # walk_corpus() -- file discovery + exclusion
  classifier.py       # classify_file() -- authority class assignment
  git_enricher.py     # enrich_git_metadata() -- lifecycle, churn, rename tracking
  duplicate_detector.py  # detect_duplicates() -- SHA256 + version chains
  code_prescan.py     # CodePrescan class (Tree-sitter multi-language analysis)
  dependency_graph.py # DependencyGraph class (import/require/use edges)
  grok_passes.py      # run_passes() -- Grok 4.20 intelligence passes
  models.py           # FileEntry, PrescanConfig, PrescanResult dataclasses
  schemas.py          # JSON schema definitions for outputs
```

#### PrescanEngine Interface

```python
@dataclass
class PrescanConfig:
    repo_root: Path
    output_dir: Path
    max_file_size: int = 100 * 1024
    max_corpus_size: int = 50 * 1024 * 1024
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)
    code_languages: list[str] = field(default_factory=lambda: ["python", "typescript", "javascript", "go", "rust"])
    enable_code_prescan: bool = True
    enable_git_enrichment: bool = True
    incremental: bool = False          # Only re-analyze changed files
    incremental_baseline: str | None = None  # Git ref for diff base (default: HEAD~1)

@dataclass
class PrescanResult:
    success: bool
    intelligence_path: Path | None      # prescan_intelligence.json
    manifest_path: Path | None          # corpus_manifest.json
    code_graph_path: Path | None        # code_graph.json
    file_count: int
    included_count: int
    code_files_analyzed: int
    duration_seconds: float
    warnings: list[str]
    errors: list[str]

class PrescanEngine:
    def __init__(self, config: PrescanConfig): ...

    def run(self) -> PrescanResult:
        """Run full prescan pipeline."""
        ...

    def run_incremental(self, changed_files: list[str]) -> PrescanResult:
        """Re-analyze only changed files, merge with cached baseline."""
        ...
```

#### Migration Path

The existing `scripts/doc_audit_prescan.py` (900+ lines) splits into:
- `corpus_walker.py`: lines ~342-434 (walk_corpus, exclusion logic)
- `classifier.py`: lines ~440-600 (classify_file, authority rules)
- `git_enricher.py`: lines ~600-900 (git metadata, lifecycle, churn)
- `duplicate_detector.py`: lines ~900-1038 (SHA256 groups, version chains)
- `code_prescan.py`: NEW (replaces the Python-only `enrich_with_code_intelligence`)
- `models.py`: lines ~254-340 (FileEntry, PrescanConfig, etc.)

The `scripts/doc_audit_prescan_passes.py` becomes `grok_passes.py` with the same logic but importable.

The original scripts remain as thin wrappers:
```python
# scripts/doc_audit_prescan.py (after migration)
from services.repo_truth_extractor.lib.prescan.engine import PrescanEngine
# ... argparse, then engine.run()
```

### 2.2 Code-Focused Prescan

**Location**: `services/repo-truth-extractor/lib/prescan/code_prescan.py`

Replaces the current Python-only `enrich_with_code_intelligence()` in the prescan script (which uses the stdlib `ast` module). The new version uses Tree-sitter for multi-language support.

#### CodePrescan Interface

```python
@dataclass
class CodeSymbol:
    name: str
    kind: Literal["function", "class", "method", "variable", "constant", "type"]
    file_path: str
    start_line: int
    end_line: int
    signature: str | None = None      # Full function signature
    decorators: list[str] = field(default_factory=list)
    parent_class: str | None = None   # For methods
    docstring: str | None = None      # First docstring line
    complexity: float = 0.0           # 0.0-1.0 (cyclomatic + cognitive normalized)
    is_exported: bool = False         # Public API surface
    is_test: bool = False

@dataclass
class CodeFileAnalysis:
    file_path: str
    language: str
    symbols: list[CodeSymbol]
    imports: list[str]                # Raw import strings
    resolved_imports: list[str]       # Resolved to repo-relative paths
    is_entry_point: bool
    is_test_file: bool
    api_surfaces: list[dict]          # FastAPI routes, Click commands, MCP tools
    complexity_score: float           # File-level aggregate
    function_count: int
    class_count: int
    line_count: int
    docstring_coverage: float         # 0.0-1.0
    design_patterns: list[str]        # Detected patterns (singleton, factory, etc.)

@dataclass
class CodePrescanResult:
    files_analyzed: int
    languages: dict[str, int]         # {python: 150, typescript: 30, ...}
    entry_points: list[str]
    hub_files: list[dict]             # [{path, imported_by_count}]
    orphan_files: list[str]           # Exported but never imported
    dead_code_candidates: list[str]   # Exported but never imported, not entry points
    complexity_hotspots: list[dict]   # [{path, score}] where score > 0.6
    test_coverage_map: dict[str, str] # {source_path: test_path}
    untested_files: list[str]
    api_surfaces: list[dict]          # All detected API endpoints/commands
    design_patterns: dict[str, list[str]]  # {pattern: [files]}

class CodePrescan:
    """Multi-language AST analysis using Tree-sitter."""

    SUPPORTED_LANGUAGES = {
        "python": [".py"],
        "typescript": [".ts", ".tsx"],
        "javascript": [".js", ".jsx"],
        "go": [".go"],
        "rust": [".rs"],
    }

    def __init__(self, repo_root: Path, languages: list[str] | None = None): ...

    def analyze_file(self, file_path: Path) -> CodeFileAnalysis | None:
        """Analyze a single file with Tree-sitter."""
        ...

    def analyze_all(self, file_entries: list[FileEntry]) -> CodePrescanResult:
        """Analyze all code files, build dependency graph."""
        ...

    def detect_api_surfaces(self, analysis: CodeFileAnalysis) -> list[dict]:
        """Detect FastAPI routes, Click commands, MCP tools, etc."""
        ...
```

#### Tree-sitter Integration

Reuse the existing `services/dope-context/src/preprocessing/code_chunker.py` parser initialization pattern:

```python
# Tree-sitter language loading (same pattern as code_chunker.py)
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser

# Add Go and Rust support
try:
    import tree_sitter_go as tsgo
    import tree_sitter_rust as tsrust
except ImportError:
    tsgo = tsrust = None  # Graceful degradation
```

#### API Surface Detection

```python
# Pattern registry for API surface detection
API_SURFACE_PATTERNS = {
    "fastapi_route": {
        "languages": ["python"],
        "tree_sitter_query": '(decorator (attribute object: (identifier) @obj attribute: (identifier) @method)) @dec',
        "filter": lambda obj, method: obj in ("app", "router") and method in ("get", "post", "put", "delete", "patch"),
    },
    "click_command": {
        "languages": ["python"],
        "tree_sitter_query": '(decorator (call function: (attribute attribute: (identifier) @name))) @dec',
        "filter": lambda name: name in ("command", "group"),
    },
    "mcp_tool": {
        "languages": ["python"],
        "content_patterns": [r"@server\.tool\(", r"@mcp\.tool\("],
    },
}
```

#### Complexity Scoring

Normalized 0.0-1.0 combining:
- **Cyclomatic complexity**: Branch count (if/for/while/case/except)
- **Cognitive complexity**: Nesting depth penalty, boolean operator chains
- **Parameter count**: Functions with >5 params get penalty
- **Line count**: Normalized by language median function length

```python
def compute_complexity(node: Node, language: str) -> float:
    cyclomatic = count_branches(node)
    cognitive = compute_cognitive_complexity(node)
    params = count_parameters(node)

    # Normalize each to 0-1 range using language-specific thresholds
    THRESHOLDS = {
        "python": {"cyclomatic_max": 15, "cognitive_max": 20, "params_max": 8},
        "typescript": {"cyclomatic_max": 12, "cognitive_max": 18, "params_max": 6},
    }
    t = THRESHOLDS.get(language, THRESHOLDS["python"])

    c_norm = min(cyclomatic / t["cyclomatic_max"], 1.0)
    cog_norm = min(cognitive / t["cognitive_max"], 1.0)
    p_norm = min(max(params - 3, 0) / t["params_max"], 1.0)

    return round(0.4 * c_norm + 0.4 * cog_norm + 0.2 * p_norm, 3)
```

### 2.3 Dependency Graph

**Location**: `services/repo-truth-extractor/lib/prescan/dependency_graph.py`

```python
@dataclass
class DependencyEdge:
    source: str          # Importing file (repo-relative)
    target: str          # Imported file (repo-relative)
    import_type: Literal["direct", "from", "dynamic", "require", "use"]
    symbols: list[str]   # Specific symbols imported (if from-import)

@dataclass
class DependencyCluster:
    """Group of tightly coupled files."""
    id: str
    files: list[str]
    internal_edges: int
    external_edges: int
    cohesion_score: float  # internal / (internal + external)

class DependencyGraph:
    """Directed dependency graph with cluster detection."""

    def __init__(self): ...

    def add_edge(self, edge: DependencyEdge): ...

    def get_importers(self, file_path: str) -> list[str]:
        """Who imports this file?"""
        ...

    def get_imports(self, file_path: str) -> list[str]:
        """What does this file import?"""
        ...

    def detect_clusters(self, min_cohesion: float = 0.6) -> list[DependencyCluster]:
        """Find tightly coupled file groups using Tarjan's algorithm."""
        ...

    def detect_circular_imports(self) -> list[list[str]]:
        """Find all cycles in the import graph."""
        ...

    def topological_order(self) -> list[str]:
        """Return files in dependency order (foundations first)."""
        ...

    def impact_score(self, file_path: str) -> float:
        """How many files are transitively affected by changing this file?"""
        ...

    def to_json(self) -> dict:
        """Serialize for prescan output."""
        ...
```

### 2.4 Intelligence Router

**Location**: `services/repo-truth-extractor/lib/intelligence_router.py`

This is the bridge between prescan output and the extraction pipeline. It reads prescan_intelligence.json and modifies pipeline behavior.

```python
@dataclass
class RoutingDecision:
    file_path: str
    action: Literal["include", "skip", "compress", "reroute"]
    target_phase: str | None = None     # Override phase routing
    model_hint: str | None = None       # "fast" or "premium"
    compression_summary: str | None = None  # For compress action
    reason: str = ""

@dataclass
class BundlingHint:
    """How to group files for a chunk."""
    cluster_id: str
    files: list[str]
    rationale: str                       # Why these files together
    estimated_tokens: int
    dependency_order: list[str]          # Process in this order within chunk

class IntelligenceRouter:
    """Reads prescan intelligence and produces pipeline directives."""

    def __init__(self, prescan_dir: Path): ...

    @classmethod
    def from_prescan_output(cls, prescan_dir: Path) -> "IntelligenceRouter":
        """Load from standard prescan output directory."""
        ...

    def get_routing_decisions(self) -> list[RoutingDecision]:
        """Get per-file routing: skip, compress, reroute, or include."""
        ...

    def get_bundling_hints(self, phase: str) -> list[BundlingHint]:
        """Get intelligent file groupings for a phase's chunking."""
        ...

    def get_skip_list(self) -> list[str]:
        """Files to skip entirely (exact duplicates, pure noise)."""
        ...

    def get_compress_chains(self) -> list[dict]:
        """Version chains to send as summaries instead of full files."""
        ...

    def get_phase_routing_overrides(self) -> dict[str, str]:
        """File path -> recommended phase overrides."""
        ...

    def get_model_routing_hints(self) -> dict[str, str]:
        """Partition pattern -> 'fast' or 'premium'."""
        ...

    def get_dependency_order(self, files: list[str]) -> list[str]:
        """Sort files in dependency order (foundations first)."""
        ...

    def estimate_token_savings(self) -> dict:
        """Estimate how much the routing decisions save."""
        ...
```

### 2.5 Enhanced Chunking

**Location**: Modify existing `services/repo-truth-extractor/lib/chunking.py`

Current `plan_chunks_for_step()` is purely size-based. Enhance with intelligence-aware grouping.

```python
def plan_chunks_for_step(
    partitions: list[dict],
    inventory_by_path: dict[str, dict],
    max_files: int,
    max_chars: int,
    intelligence_router: IntelligenceRouter | None = None,  # NEW
) -> list[dict]:
    """
    Plan file chunks for a step.

    If intelligence_router is provided:
    - Apply skip_list (remove files before chunking)
    - Apply compress_chains (replace files with summaries)
    - Use bundling_hints to group related files together
    - Use dependency_order within each chunk
    - Apply smart_truncation for high-complexity files
    """
    ...
```

#### Smart Truncation

For code files where full content exceeds token budget, use AST to keep signatures and skip bodies:

```python
def smart_truncate(file_path: str, max_tokens: int, code_analysis: CodeFileAnalysis) -> str:
    """
    Truncate a code file intelligently using AST knowledge.

    Strategy (in order of preference):
    1. Full file if within budget
    2. Keep all signatures + docstrings, skip function bodies
    3. Keep public API signatures only + module docstring
    4. Keep class/function names only (structural skeleton)
    """
    ...
```

---

## 3. CLI Command Specifications

### 3.1 `dopemux extractor prescan`

```
dopemux extractor prescan [OPTIONS]

Options:
  -r, --repo PATH           Target repository (default: current directory)
  -o, --output PATH         Output directory (default: extraction/prescan)
  --passes TEXT              Grok passes: dedup,discover,feasibility,optimize or 'all' or 'none'
                             (default: none -- base prescan only, no LLM costs)
  --code / --no-code         Enable code-focused prescan with Tree-sitter (default: --code)
  --languages TEXT           Languages for code prescan (default: python,typescript,javascript)
  --git / --no-git           Enable git metadata enrichment (default: --git)
  --incremental              Only re-analyze files changed since last prescan
  --diff-base TEXT           Git ref for incremental diff base (default: HEAD~1)
  --model TEXT               Grok model for passes (default: grok-4.20-beta-0309-non-reasoning)
  --cost-estimate            Show estimated cost before running Grok passes (requires confirmation)
  --parallel-passes          Run independent Grok passes in parallel (dedup+discover are independent)
  --verbose / -v             Verbose output
  --json                     Output prescan summary as JSON to stdout

Examples:
  # Base prescan only (zero cost, ~30 seconds)
  dopemux extractor prescan

  # Base prescan + all Grok passes (~$0.10-0.24)
  dopemux extractor prescan --passes all --cost-estimate

  # Code-only prescan (no docs, no Grok)
  dopemux extractor prescan --no-git --passes none

  # Incremental prescan (only changed files)
  dopemux extractor prescan --incremental --diff-base main

  # Full pipeline: prescan -> init -> run
  dopemux extractor prescan --passes all
  dopemux extractor init --prescan extraction/prescan
  dopemux extractor run --prescan extraction/prescan
```

### 3.2 Enhanced `dopemux extractor init`

Add `--prescan` flag to consume prescan intelligence:

```
dopemux extractor init [existing options...] --prescan PATH

New Options:
  --prescan PATH            Path to prescan output directory. If provided:
                            - feature_detector reads code_intelligence for enhanced detection
                            - phase_applicability uses OPTIMIZE routing overrides
                            - scope_resolver uses dependency graph for grouping
                            - skip/compress lists applied during prompt generation
```

### 3.3 Enhanced `dopemux extractor run`

Add `--prescan` flag for runtime intelligence:

```
dopemux extractor run [existing options...] --prescan PATH

New Options:
  --prescan PATH            Path to prescan output directory. If provided:
                            - Skip list applied before partitioning
                            - Compress chains send summaries instead of files
                            - Model routing hints select fast vs premium per partition
                            - Dependency ordering applied within chunks
```

---

## 4. Data Contracts (JSON Schemas)

### 4.1 prescan_intelligence.json

```json
{
  "$schema": "prescan_intelligence_v2",
  "version": "2.0.0",
  "generated_at": "2026-03-16T10:00:00Z",
  "repo_root": "/abs/path",
  "git_sha": "abc123",
  "git_branch": "dev",

  "corpus_summary": {
    "total_files_scanned": 1500,
    "included_files": 800,
    "excluded_files": 700,
    "total_included_size_bytes": 5000000,
    "by_authority_class": {"canonical": 50, "operational": 200, "...": "..."},
    "by_extension": {".py": 300, ".md": 150, ".ts": 50, "...": "..."},
    "corpus_health_score": 72
  },

  "lifecycle_distribution": {
    "fresh": 100,
    "active": 300,
    "stale": 200,
    "frozen": 150,
    "unknown": 50
  },

  "duplicate_groups": {
    "sha256_abc123": ["path/a.md", "path/b.md"]
  },

  "version_chains": {
    "chain_xyz": [
      {"path": "doc-v1.md", "ordinal": 1, "is_latest": false},
      {"path": "doc-v2.md", "ordinal": 2, "is_latest": true}
    ]
  },

  "planned_features": {
    "proposed_adrs": ["docs/90-adr/ADR-XXX.md"],
    "stub_files": ["src/feature/stub.py"],
    "todo_files": ["src/feature/incomplete.py"],
    "draft_docs": ["docs/draft-feature.md"]
  },

  "extraction_hints": {
    "skip_duplicates": ["path/b.md"],
    "high_churn_files": ["src/hot.py"],
    "compress_candidates": ["doc-v1.md"]
  },

  "code_intelligence": {
    "total_files_analyzed": 350,
    "languages": {"python": 280, "typescript": 50, "javascript": 20},
    "entry_points": ["src/dopemux/cli.py", "services/api/main.py"],
    "entry_point_count": 15,
    "hub_files": [{"path": "src/dopemux/console.py", "imported_by": 42}],
    "hub_count": 8,
    "orphan_files": ["src/unused/old_util.py"],
    "orphan_count": 12,
    "dead_code_candidates": ["src/unused/old_util.py"],
    "complexity_hotspots": [{"path": "src/dopemux/cli.py", "score": 0.85}],
    "test_coverage_map": {"src/dopemux/cli.py": "tests/test_cli.py"},
    "untested_files": ["src/dopemux/new_feature.py"],
    "api_surfaces": [
      {"type": "fastapi_route", "method": "GET", "path": "/health", "file": "services/api/main.py"},
      {"type": "click_command", "name": "extractor", "file": "src/dopemux/commands/extractor_commands.py"},
      {"type": "mcp_tool", "name": "search_code", "file": "services/dope-context/main.py"}
    ],
    "import_graph_summary": {
      "nodes": 350,
      "edges": 1200,
      "components": 5,
      "largest_component_size": 280
    },
    "avg_docstring_coverage": 0.42,
    "avg_complexity": 0.35
  },

  "grok_passes": {
    "dedup": {"...": "pass result"},
    "discover": {"...": "pass result"},
    "feasibility": {"...": "pass result"},
    "optimize": {
      "skip_list": ["noise/file.md"],
      "compress_chains": [{"chain_id": "xyz", "send_summary_instead": true, "summary_hint": "..."}],
      "phase_routing_overrides": [{"path": "docs/90-adr/ADR-207.md", "recommended_phase": "X", "reason": "..."}],
      "model_routing_hints": [{"partition_pattern": "docs/90-adr/*", "recommended_model": "premium", "reason": "..."}],
      "estimated_savings": {"files_skipped": 50, "files_compressed": 12, "estimated_token_reduction_pct": 18}
    }
  }
}
```

### 4.2 code_graph.json

```json
{
  "$schema": "code_graph_v1",
  "version": "1.0.0",
  "generated_at": "2026-03-16T10:00:00Z",
  "node_count": 350,
  "edge_count": 1200,

  "edges": [
    {"source": "src/dopemux/cli.py", "target": "src/dopemux/console.py", "type": "from", "symbols": ["console"]},
    {"source": "src/dopemux/cli.py", "target": "src/dopemux/commands/extractor_commands.py", "type": "from", "symbols": ["extractor"]}
  ],

  "clusters": [
    {
      "id": "cluster_cli",
      "files": ["src/dopemux/cli.py", "src/dopemux/commands/extractor_commands.py", "src/dopemux/console.py"],
      "internal_edges": 8,
      "external_edges": 3,
      "cohesion_score": 0.73
    }
  ],

  "topological_order": [
    "src/dopemux/console.py",
    "src/dopemux/commands/extractor_commands.py",
    "src/dopemux/cli.py"
  ]
}
```

### 4.3 corpus_manifest.json

Same schema as current, but each entry gains new fields:

```json
{
  "rel_path": "src/dopemux/cli.py",
  "size_bytes": 15000,
  "extension": ".py",
  "authority_class": "canonical",
  "include": true,
  "content_hash": "sha256:abc...",
  "lifecycle_stage": "active",
  "churn_score": 0.8,

  "code_analysis": {
    "language": "python",
    "function_count": 12,
    "class_count": 2,
    "complexity_score": 0.65,
    "is_entry_point": true,
    "is_test_file": false,
    "import_count": 15,
    "imported_by_count": 8,
    "is_orphan": false,
    "docstring_coverage": 0.6,
    "api_surfaces": [{"type": "click_command", "name": "extractor"}],
    "design_patterns": ["command_pattern"],
    "tested_by": "tests/test_extractor_commands.py"
  }
}
```

---

## 5. Pipeline Integration Points

### 5.1 sync_engine.py Enhancement

The sync engine's `run_sync()` function gains a `prescan_dir` parameter:

```python
def run_sync(
    *,
    repo_root: Path,
    prescan_dir: Path | None = None,  # NEW
    # ... existing params ...
) -> SyncResult:
    """
    If prescan_dir is provided:
    1. Load prescan_intelligence.json
    2. Pass code_intelligence to feature_detector for enhanced detection
    3. Pass OPTIMIZE results to phase_applicability for routing overrides
    4. Pass dependency graph to scope_resolver for intelligent grouping
    5. Pass skip/compress lists to template_renderer
    """
```

### 5.2 feature_detector.py Enhancement

Current detection uses only glob patterns + regex content matching. With code intelligence:

```python
def detect_features(
    repo_root: Path,
    *,
    code_intelligence: dict | None = None,  # NEW
) -> dict:
    """
    Enhanced detection:
    - If code_intelligence.api_surfaces contains fastapi_route entries,
      boost confidence of http_api_python feature to "confirmed" (not just glob-detected)
    - Use import_graph to discover frameworks not caught by globs
    - Use code_intelligence.languages to skip irrelevant language rules
    - Use entry_points to detect CLI frameworks (click, argparse, typer)
    """
```

### 5.3 chunking.py Enhancement

The core change to `plan_chunks_for_step()`:

```python
def plan_chunks_for_step(
    partitions: list[dict],
    inventory_by_path: dict[str, dict],
    max_files: int,
    max_chars: int,
    intelligence_router: IntelligenceRouter | None = None,  # NEW
) -> list[dict]:
    """
    New behavior when intelligence_router is provided:

    1. FILTER: Remove skip_list files from all partitions
    2. REPLACE: Substitute compress_chain files with their summaries
    3. GROUP: Use bundling_hints to pre-group related files
       - Module + its tests together
       - Dependency clusters together
       - Foundation files before dependents
    4. ORDER: Within each chunk, sort by topological_order
    5. TRUNCATE: For code files exceeding budget, use smart_truncation
    """
```

### 5.4 run_extraction_v5.py Integration

The v5 runner needs minimal changes. The intelligence_router is loaded once at startup and threaded through to chunking:

```python
# In the runner's main flow, after loading config:
intelligence_router = None
if args.prescan:
    from lib.intelligence_router import IntelligenceRouter
    intelligence_router = IntelligenceRouter.from_prescan_output(Path(args.prescan))
    logger.info(f"Loaded prescan intelligence: {intelligence_router.estimate_token_savings()}")

# When calling plan_chunks_for_step:
chunks = plan_chunks_for_step(
    partitions=partitions,
    inventory_by_path=inventory,
    max_files=step_config.max_files,
    max_chars=step_config.max_chars,
    intelligence_router=intelligence_router,  # NEW
)
```

---

## 6. File Placement Decisions

### New Files

| File | Location | Rationale |
|------|----------|-----------|
| `engine.py` | `services/repo-truth-extractor/lib/prescan/` | Core prescan logic, importable by CLI and scripts |
| `corpus_walker.py` | `services/repo-truth-extractor/lib/prescan/` | Extracted from prescan.py |
| `classifier.py` | `services/repo-truth-extractor/lib/prescan/` | Extracted from prescan.py |
| `git_enricher.py` | `services/repo-truth-extractor/lib/prescan/` | Extracted from prescan.py |
| `duplicate_detector.py` | `services/repo-truth-extractor/lib/prescan/` | Extracted from prescan.py |
| `code_prescan.py` | `services/repo-truth-extractor/lib/prescan/` | NEW: Tree-sitter multi-language |
| `dependency_graph.py` | `services/repo-truth-extractor/lib/prescan/` | NEW: Import graph + clusters |
| `grok_passes.py` | `services/repo-truth-extractor/lib/prescan/` | Extracted from prescan_passes.py |
| `models.py` | `services/repo-truth-extractor/lib/prescan/` | Shared dataclasses |
| `schemas.py` | `services/repo-truth-extractor/lib/prescan/` | JSON schema definitions |
| `intelligence_router.py` | `services/repo-truth-extractor/lib/` | Bridge: prescan output -> pipeline input |

### Modified Files

| File | Change |
|------|--------|
| `src/dopemux/commands/extractor_commands.py` | Add `prescan` subcommand, add `--prescan` to `init` and `run` |
| `services/repo-truth-extractor/lib/chunking.py` | Add `intelligence_router` parameter |
| `services/repo-truth-extractor/lib/promptgen/sync_engine.py` | Add `prescan_dir` parameter |
| `services/repo-truth-extractor/lib/promptgen/feature_detector.py` | Add `code_intelligence` parameter |
| `services/repo-truth-extractor/run_extraction_v5.py` | Add `--prescan` CLI arg, load intelligence_router |
| `scripts/doc_audit_prescan.py` | Thin wrapper, delegates to `lib/prescan/engine.py` |
| `scripts/doc_audit_prescan_passes.py` | Thin wrapper, delegates to `lib/prescan/grok_passes.py` |

### Files NOT Changed

The existing dope-context Tree-sitter code (`services/dope-context/src/preprocessing/code_chunker.py`) is a reference implementation but NOT shared directly. The prescan's `code_prescan.py` reuses the same Tree-sitter initialization pattern but has different output requirements (it needs symbols, signatures, complexity scores, not chunks for vector embedding). Sharing would create an unwanted coupling between the indexing pipeline and the extraction pipeline.

---

## 7. Incremental Prescan Design

### Changed-File Detection

```python
def detect_changed_files(repo_root: Path, baseline_ref: str = "HEAD~1") -> list[str]:
    """Use git diff to find files changed since baseline."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", baseline_ref],
        capture_output=True, text=True, cwd=repo_root
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
```

### Cache Strategy

```
extraction/prescan/
  prescan_intelligence.json     # Full intelligence (merged)
  corpus_manifest.json          # Full manifest (merged)
  code_graph.json               # Full graph (merged)
  .cache/
    file_analysis_cache.json    # Per-file analysis results keyed by content_hash
    baseline_sha.txt            # Git SHA of last full prescan
```

On incremental run:
1. Load cached `file_analysis_cache.json`
2. For changed files: re-analyze, update cache
3. For deleted files: remove from cache
4. For unchanged files: reuse cached analysis
5. Rebuild dependency graph (always, since edges may change)
6. Merge into full prescan_intelligence.json

---

## 8. Parallel Grok Pass Execution

The four passes have these dependencies:

```
dedup ──────────────────┐
                        ├──> optimize (needs all prior results)
discover ───────────────┤
                        │
feasibility ────────────┘
```

`dedup`, `discover`, and `feasibility` are independent of each other. Only `optimize` depends on all three.

Implementation:

```python
import asyncio

async def run_passes_parallel(passes: list[str], ...):
    independent = [p for p in passes if p != "optimize"]
    results = {}

    # Run independent passes in parallel
    if independent:
        tasks = [_call_grok_async(p, ...) for p in independent]
        for p, result in zip(independent, await asyncio.gather(*tasks)):
            results[p] = result

    # Run optimize last (needs all prior results)
    if "optimize" in passes:
        results["optimize"] = await _call_grok_async("optimize", ..., prior_results=results)

    return results
```

---

## 9. Cost Estimation

### Pre-Run Cost Estimate

```python
def estimate_prescan_cost(config: PrescanConfig, passes: list[str]) -> dict:
    """Estimate cost before running. No LLM calls."""
    # Base prescan: $0.00 (local computation only)
    # Grok passes: estimate from corpus size
    corpus_size = sum(f.size_bytes for f in walk_corpus(config) if f.include)

    estimates = {
        "base_prescan": 0.00,
        "dedup": _estimate_pass_cost("dedup", corpus_size),
        "discover": _estimate_pass_cost("discover", corpus_size),
        "feasibility": _estimate_pass_cost("feasibility", corpus_size),
        "optimize": _estimate_pass_cost("optimize", corpus_size),
    }

    return {
        "total_estimated_usd": sum(estimates[p] for p in ["base_prescan"] + passes),
        "breakdown": {p: estimates[p] for p in passes},
        "corpus_files": corpus_size,
    }

def _estimate_pass_cost(pass_id: str, corpus_bytes: int) -> float:
    """Rough cost estimate based on payload size and Grok pricing."""
    # Grok 4.20: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
    INPUT_COST_PER_1K = 0.003
    OUTPUT_COST_PER_1K = 0.015
    EST_OUTPUT_TOKENS = {"dedup": 2000, "discover": 3000, "feasibility": 2500, "optimize": 2000}

    input_tokens = corpus_bytes // 4  # Rough: 4 bytes per token
    # Passes only send relevant subsets, not full corpus
    PAYLOAD_FRACTION = {"dedup": 0.15, "discover": 0.25, "feasibility": 0.10, "optimize": 0.05}

    effective_input = int(input_tokens * PAYLOAD_FRACTION.get(pass_id, 0.1))
    input_cost = (effective_input / 1000) * INPUT_COST_PER_1K
    output_cost = (EST_OUTPUT_TOKENS.get(pass_id, 2000) / 1000) * OUTPUT_COST_PER_1K

    return round(input_cost + output_cost, 4)
```

---

## 10. Implementation Priority Ordering

### Phase 1: Foundation (Week 1-2)

**Goal**: Extract prescan into importable library, wire into CLI.

1. **Create `lib/prescan/` package** -- extract from `scripts/doc_audit_prescan.py`
   - `models.py` (FileEntry, PrescanConfig, PrescanResult)
   - `corpus_walker.py` (walk_corpus)
   - `classifier.py` (classify_file)
   - `git_enricher.py` (git metadata)
   - `duplicate_detector.py` (SHA256 groups, version chains)
   - `engine.py` (PrescanEngine orchestrating above)
   - `grok_passes.py` (extracted from prescan_passes.py)

2. **Add `dopemux extractor prescan` CLI command**
   - Basic command wiring in `extractor_commands.py`
   - Calls PrescanEngine, saves to extraction/prescan/

3. **Update scripts/ to be thin wrappers**
   - `doc_audit_prescan.py` -> delegates to `lib/prescan/engine.py`
   - `doc_audit_prescan_passes.py` -> delegates to `lib/prescan/grok_passes.py`

**Verification**: `dopemux extractor prescan` produces same output as `python scripts/doc_audit_prescan.py dry-run`.

### Phase 2: Code Intelligence (Week 3-4)

**Goal**: Multi-language Tree-sitter analysis.

4. **Create `code_prescan.py`** -- Tree-sitter based analysis
   - Python, TypeScript, JavaScript support (reuse dope-context's Tree-sitter init pattern)
   - Function/class/method extraction with signatures
   - Complexity scoring (cyclomatic + cognitive)
   - API surface detection (FastAPI, Click, MCP)

5. **Create `dependency_graph.py`** -- Import graph construction
   - Multi-language import resolution
   - Cluster detection (Tarjan's)
   - Topological ordering
   - Impact scoring

6. **Integrate into PrescanEngine** -- code_prescan runs as part of `engine.run()`

**Verification**: Prescan produces `code_intelligence` section in prescan_intelligence.json with accurate function counts, complexity scores, and dependency edges.

### Phase 3: Pipeline Integration (Week 5-6)

**Goal**: Prescan intelligence feeds into extraction.

7. **Create `intelligence_router.py`** -- Bridge between prescan and pipeline
   - Reads prescan_intelligence.json
   - Produces RoutingDecision and BundlingHint lists

8. **Enhance `chunking.py`** -- Intelligence-aware chunking
   - Skip list filtering
   - Compress chain substitution
   - Dependency-aware grouping
   - Smart truncation for code files

9. **Enhance `sync_engine.py`** -- Prescan-informed prompt generation
   - `--prescan` parameter on `extractor init`
   - Code intelligence enhances feature_detector
   - OPTIMIZE routing overrides modify phase plan

10. **Enhance `run_extraction_v5.py`** -- Runtime intelligence
    - `--prescan` CLI argument
    - Load IntelligenceRouter at startup
    - Thread through to chunking calls

**Verification**: `dopemux extractor prescan --passes all && dopemux extractor init --prescan extraction/prescan && dopemux extractor run --prescan extraction/prescan` completes with measurable token savings from skip/compress/routing.

### Phase 4: Optimization (Week 7-8)

**Goal**: Incremental prescan, parallel passes, cost estimation, dope-context integration.

11. **Incremental prescan** -- `--incremental` flag
    - Git diff changed-file detection
    - File analysis cache with content_hash keys
    - Merge into full intelligence

12. **Parallel Grok passes** -- `--parallel-passes` flag
    - Async execution of independent passes
    - Sequential optimize pass after all others

13. **Cost estimation** -- `--cost-estimate` flag
    - Pre-run token/cost estimation
    - Confirmation prompt before Grok calls

14. **Dope-context integration** -- Semantic search during extraction
    - If dope-context indexed, use search_code for finding related files
    - Feed complexity scores from dope-context into prescan

**Verification**: Incremental prescan on a 5-file change completes in <5 seconds vs ~30 seconds for full. Parallel passes complete ~40% faster than sequential for 3+ passes.

---

## 11. Risk Assessment and Trade-offs

### Risk: Tree-sitter Dependency Availability

**Problem**: Go and Rust tree-sitter bindings may not be installed.
**Mitigation**: Graceful degradation. The `code_prescan.py` initializes parsers opportunistically. Missing languages are logged as warnings and those files get line-based fallback analysis (function counting via regex). Python/JS/TS are mandatory; Go/Rust are optional.

### Risk: Prescan Output Size

**Problem**: For large repos (10K+ files), prescan_intelligence.json could be several MB.
**Mitigation**: The intelligence_router loads lazily and indexes by file path. The full JSON is only read once at startup. Corpus_manifest entries for excluded files are stripped of analysis data to reduce size.

### Risk: Cache Invalidation for Incremental Prescan

**Problem**: Import graph edges may change when a file that is NOT in the changed set adds or removes an import of a changed file.
**Mitigation**: The dependency graph is always rebuilt fully even during incremental prescan. Only per-file AST analysis is cached. Graph construction is fast (<2 seconds for 500 files).

### Trade-off: Shared vs Separate Tree-sitter Code

**Decision**: Separate code in `code_prescan.py` rather than importing from dope-context.
**Rationale**: The prescan needs symbol extraction with signatures, complexity scoring, and decorator detection. Dope-context's `code_chunker.py` is optimized for vector embedding chunks. Sharing would create a coupling between two independent pipelines with different output requirements. The Tree-sitter initialization pattern (10 lines) is acceptable to duplicate.

### Trade-off: Library Extraction vs Script Enhancement

**Decision**: Extract into `lib/prescan/` package rather than enhancing scripts in-place.
**Rationale**: The CLI needs to import prescan logic. Python scripts cannot be reliably imported (they have `if __name__ == "__main__"` guards and sys.path manipulation). A proper package with `__init__.py` is the clean solution. The scripts become thin wrappers that retain backward compatibility.

---

## 12. Testing Strategy

### Unit Tests

```
tests/repo-truth-extractor/prescan/
  test_corpus_walker.py       # File discovery, exclusion logic
  test_classifier.py          # Authority class assignment
  test_code_prescan.py        # Tree-sitter analysis per language
  test_dependency_graph.py    # Graph construction, cycle detection, clustering
  test_intelligence_router.py # Routing decisions, bundling hints
  test_incremental.py         # Cache hit/miss, merge logic
```

### Integration Tests

```
tests/repo-truth-extractor/
  test_prescan_to_init.py     # prescan output feeds into sync_engine
  test_prescan_to_run.py      # intelligence_router modifies chunking behavior
  test_full_pipeline.py       # prescan -> init -> run end-to-end
```

### Fixture Strategy

Create a small test repo fixture (20-30 files across Python/TS/JS) with known structure:
- Known duplicate pairs
- Known version chains
- Known entry points and orphans
- Known circular imports
- Known API surfaces

This enables deterministic testing of all analysis components.
