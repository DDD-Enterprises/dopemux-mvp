from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class FileEntry:
    rel_path: str
    size_bytes: int
    extension: str
    authority_class: str = "unknown"
    include: bool = True
    exclude_reason: str | None = None
    content_hash: str | None = None
    directory_class: str = ""

    # Git enrichment
    last_commit_date: str | None = None
    last_commit_sha: str | None = None
    first_commit_date: str | None = None
    commit_count: int = 0
    last_author: str | None = None
    days_since_modified: int | None = None
    churn_score: float = 0.0
    contributor_count: int = 0
    lifecycle_stage: str = "active"
    was_renamed: bool = False
    previous_paths: list[str] = field(default_factory=list)

    # Duplicate detection
    duplicate_group_id: str | None = None
    is_duplicate: bool = False
    canonical_duplicate: str | None = None

    # Version chain
    version_chain_id: str | None = None
    version_ordinal: int = 0
    is_latest_version: bool = True

    # Feature gap signals
    has_todo_markers: bool = False
    has_stub_methods: bool = False
    is_draft_doc: bool = False
    is_proposed_adr: bool = False

    # Ghost recovery
    is_ghost: bool = False
    deleted_at_sha: str | None = None
    deleted_date: str | None = None
    recovery_source: str = ""

    # Code intelligence
    import_count: int = 0
    imported_by_count: int = 0
    is_entry_point: bool = False
    function_count: int = 0
    class_count: int = 0
    docstring_coverage: float = 0.0
    complexity_score: float = 0.0
    is_orphan: bool = False
    tested_by: str | None = None
    tests_file: str | None = None
    primary_author: str | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PrescanConfig:
    repo_root: Path
    output_dir: Path

    # Corpus constraints
    max_file_size: int = 100 * 1024
    max_corpus_size: int = 50 * 1024 * 1024
    large_json_threshold: int = 500 * 1024
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)

    # Model/provider
    provider: str = "xai"
    model: str = "grok-4.20-beta-0309-non-reasoning"
    api_key_env: str = "XAI_API_KEY"
    xai_base_url: str = "https://api.x.ai/v1"
    temperature: float = 0.0
    max_response_tokens: int = 200000
    litellm_proxy_url: str = "http://localhost:4000"

    # Execution modes
    force: bool = False
    enable_code_prescan: bool = True
    enable_git_enrichment: bool = True
    incremental: bool = False
    incremental_baseline: str | None = None
    allow_online_llm: bool = False
    allow_scope_reduction: bool = False

    # Batching
    batch_mode: bool = True
    max_tokens_per_batch: int = 1_500_000
    chars_per_token: float = 4.0

    # Deep mode
    deep_mode: bool = False
    deep_include_globs: list[str] = field(
        default_factory=lambda: [
            "SYSTEM_ARCHIVE/**",
            "docs/archive/**",
            "docs/archive/completed-projects/**",
        ]
    )

    # Analysis/meta
    cost_estimate: bool = True
    verbose: bool = False
    code_languages: list[str] = field(
        default_factory=lambda: ["python", "typescript", "javascript"]
    )


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

    # Extraction hints
    skip_duplicate_paths: list[str] = field(default_factory=list)
    version_chains: dict[str, list[str]] = field(default_factory=dict)

    # Batching results
    batch_plan_path: Path | None = None
    batch_count: int = 0

    # Deep mode results
    archaeology_report_path: Path | None = None

    # Code intelligence
    code_report_path: Path | None = None
