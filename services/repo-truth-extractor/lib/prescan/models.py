from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


def _root_and_nested_globs(*dir_names: str) -> tuple[str, ...]:
    patterns: list[str] = []
    for dir_name in dir_names:
        patterns.extend((f"{dir_name}/**", f"**/{dir_name}/**"))
    return tuple(patterns)


def _root_globs(*dir_names: str) -> tuple[str, ...]:
    return tuple(f"{dir_name}/**" for dir_name in dir_names)


DEFAULT_BASE_EXCLUDE_GLOBS = (
    ".git/**",
    "**/.git/**",
    "node_modules/**",
    "**/node_modules/**",
    ".venv/**",
    "**/.venv/**",
    "venv/**",
    "**/venv/**",
    "__pycache__/**",
    "**/__pycache__/**",
    "dist/**",
    "**/dist/**",
    "build/**",
    "**/build/**",
)

DEFAULT_GENERATED_OUTPUT_EXCLUDE_GLOBS = (
    # Root-only: these directory names also occur as legitimate source/doc trees
    # (e.g. src/dopemux/extraction, docs/02-how-to/extraction, docs/archive/claudedocs),
    # so excluding `**/<name>/**` would drop canonical sources.
    *_root_globs(
        "extraction",
        "claudedocs",
    ),
    # Root + nested: these names are unambiguously generated output trees in this
    # repo and have no legitimate non-generated occurrences.
    *_root_and_nested_globs(
        "proof",
        "out",
        "audit_prep",
        "_audit_out",
    ),
    "task-packets/generated/**",
    "**/task-packets/generated/**",
)

DEFAULT_OPERATOR_LOCAL_EXCLUDE_GLOBS = (
    ".codex/**",
    "**/.codex/**",
    ".conport/**",
    "**/.conport/**",
    ".dopemux/**",
    "**/.dopemux/**",
    ".dopetask/**",
    "**/.dopetask/**",
    ".pytest_cache/**",
    "**/.pytest_cache/**",
    ".mypy_cache/**",
    "**/.mypy_cache/**",
    ".ruff_cache/**",
    "**/.ruff_cache/**",
    ".tox/**",
    "**/.tox/**",
    ".eggs/**",
    "**/.eggs/**",
    "*.egg-info/**",
    "**/*.egg-info/**",
    "htmlcov/**",
    "**/htmlcov/**",
)

DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*.pem",
    "**/*.pem",
    "*.key",
    "**/*.key",
    "*.p12",
    "**/*.p12",
    "*.pfx",
    "**/*.pfx",
    "id_rsa",
    "**/id_rsa",
    "id_ed25519",
    "**/id_ed25519",
)

# Repo-visible env templates that look like secret-bearing files but are intentionally
# committed (placeholders only). These are kept in the prescan corpus and treated as text.
# See docs/02-how-to/create-llm-archive.md for the parallel rule on .env handling.
DEFAULT_SECRET_BEARING_ALLOWLIST_BASENAMES = (
    ".env.example",
    ".env.template",
    ".env.sample",
)

DEFAULT_PRESCAN_EXCLUDE_GLOBS = (
    *DEFAULT_BASE_EXCLUDE_GLOBS,
    *DEFAULT_GENERATED_OUTPUT_EXCLUDE_GLOBS,
    *DEFAULT_OPERATOR_LOCAL_EXCLUDE_GLOBS,
    *DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS,
)


@dataclass
class FileEntry:
    rel_path: str
    size_bytes: int
    extension: str
    include: bool = True
    exclude_reason: str | None = None
    directory_class: str = "root"
    content_hash: str | None = None
    authority_class: str = "unknown"
    lifecycle_stage: str = "active"
    is_ghost: bool = False
    deleted_at_sha: str | None = None
    deleted_date: str | None = None
    recovery_source: str | None = None
    duplicate_group_id: str | None = None
    is_duplicate: bool = False
    canonical_duplicate: str | None = None
    version_chain_id: str | None = None
    version_ordinal: int | None = None
    is_latest_version: bool = True
    is_proposed_adr: bool = False
    has_stub_methods: bool = False
    has_todo_markers: bool = False
    is_draft_doc: bool = False
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    docstring_coverage: float = 0.0
    complexity_score: float = 0.0
    churn_score: float = 0.0
    contributor_count: int = 0
    last_commit_date: str | None = None
    tested_by: list[str] = field(default_factory=list)
    git_metadata: dict = field(default_factory=dict)
    code_intel: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        if self.is_ghost:
            payload["path"] = self.rel_path
        return payload

@dataclass
class PrescanConfig:
    repo_root: Path
    output_dir: Path
    include_globs: list[str] = field(default_factory=lambda: ["**/*"])
    exclude_globs: list[str] = field(
        default_factory=lambda: list(DEFAULT_PRESCAN_EXCLUDE_GLOBS)
    )
    max_file_size: int = 5 * 1024 * 1024
    large_json_threshold: int = 256 * 1024
    max_corpus_size: int = 500 * 1024 * 1024
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
    online_authorized: bool | None = None
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

    def __post_init__(self) -> None:
        if self.online_authorized is not None:
            self.allow_online_llm = bool(self.online_authorized)

@dataclass
class PrescanResult:
    success: bool
    duration_seconds: float
    file_count: int = 0
    code_files_analyzed: int = 0
    included_count: int = 0
    intelligence_path: Path | None = None
    manifest_path: Path | None = None
    code_graph_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

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
