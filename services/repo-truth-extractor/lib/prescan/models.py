from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

@dataclass
class FileEntry:
    rel_path: str
    size_bytes: int
    extension: str
    include: bool = True
    exclude_reason: str | None = None
    authority_class: str = "unknown"
    directory_class: str = "root"
    lifecycle_stage: str = "active"
    content_hash: str | None = None
    is_ghost: bool = False
    deleted_at_sha: str | None = None
    deleted_date: str | None = None
    recovery_source: str | None = None
    is_proposed_adr: bool = False
    has_stub_methods: bool = False
    has_todo_markers: bool = False
    is_draft_doc: bool = False
    duplicate_group_id: str | None = None
    is_duplicate: bool = False
    canonical_duplicate: str | None = None
    version_chain_id: str | None = None
    version_ordinal: int = 0
    is_latest_version: bool = True
    last_commit_sha: str | None = None
    last_author: str | None = None
    last_commit_date: str | None = None
    first_commit_date: str | None = None
    commit_count: int = 0
    contributor_count: int = 0
    days_since_modified: int | None = None
    churn_score: float = 0.0
    was_renamed: bool = False
    previous_paths: list[str] = field(default_factory=list)
    tested_by: list[str] = field(default_factory=list)
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    complexity_score: float = 0.0
    docstring_coverage: float = 0.0
    git_metadata: dict = field(default_factory=dict)
    code_intel: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class PrescanConfig:
    repo_root: Path
    output_dir: Path
    include_globs: list[str] = field(default_factory=lambda: ["**/*"])
    exclude_globs: list[str] = field(default_factory=lambda: [
        "SYSTEM_ARCHIVE/**",
        "docs/archive/**",
        "docs/archive/completed-projects/**",
        "node_modules/**",
        ".venv/**",
    ])
    max_file_size: int = 200 * 1024
    max_corpus_size: int = 1_000_000_000
    large_json_threshold: int = 100 * 1024
    chars_per_token: float = 4.0
    
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
    metadata: dict = field(default_factory=dict)
