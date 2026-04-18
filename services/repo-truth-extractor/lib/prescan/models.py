from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

@dataclass
class FileEntry:
    rel_path: str
    size_bytes: int
    extension: str
    authority_class: str = "unknown"
    lifecycle_stage: str = "active"
    is_ghost: bool = False
    git_metadata: dict = field(default_factory=dict)
    code_intel: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class PrescanConfig:
    repo_root: Path
    output_dir: Path
    
    # ── Orchestration ──
    deep_mode: bool = False
    deep_include_globs: list[str] = field(default_factory=lambda: [
        "SYSTEM_ARCHIVE/**",
        "docs/archive/**",
        "docs/archive/completed-projects/**"
    ])
    
    # ── Enrichment ──
    enable_code_prescan: bool = True
    code_languages: list[str] = field(default_factory=lambda: ["python", "typescript", "javascript"])
    enable_git_enrichment: bool = True
    
    # ── Execution ──
    incremental: bool = False
    incremental_baseline: str | None = None
    allow_online_llm: bool = False
    allow_scope_reduction: bool = False
    
    # ── Batching ──
    batch_mode: bool = True
    max_tokens_per_batch: int = 1_500_000
    
    # ── Model & Provider ──
    provider: str = "xai"
    model: str = "grok-4.20-beta-0309-non-reasoning"
    api_key_env: str = "XAI_API_KEY"
    xai_base_url: str = "https://api.x.ai/v1"
    temperature: float = 0.0
    
    # ── Analysis ──
    cost_estimate: bool = True
    verbose: bool = False

@dataclass
class PrescanResult:
    success: bool
    duration_seconds: float
    file_count: int
    code_files_analyzed: int
    intelligence_path: Path | None = None
    manifest_path: Path | None = None
    code_graph_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # ── Extraction hints ──
    skip_duplicate_paths: list[str] = field(default_factory=list)
    version_chains: dict[str, list[str]] = field(default_factory=dict)
    
    # ── Batching results ──
    batch_plan_path: Path | None = None
    batch_count: int = 0

    # ── Deep mode results ──
    archaeology_report_path: Path | None = None

    # ── Code intelligence ──
    code_report_path: Path | None = None
