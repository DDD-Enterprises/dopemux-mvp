#!/usr/bin/env python3
"""
Pre-scan documentation authority/noise audit.

Inventories repo text surfaces, classifies by authority class,
and optionally calls Grok 4.20 Beta or writes a LiteLLM handoff bundle.

Usage:
  python scripts/doc_audit_prescan.py dry-run [--verbose]
  python scripts/doc_audit_prescan.py direct [--model MODEL]
  python scripts/doc_audit_prescan.py handoff [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

logger = logging.getLogger(__name__)

# ─── SECTION 1: Constants ───────────────────────────────────────────

SCRIPT_VERSION = "1.0.0"

DEFAULT_MAX_FILE_SIZE = 100 * 1024          # 100KB
DEFAULT_MAX_CORPUS_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_LARGE_JSON_THRESHOLD = 500 * 1024   # 500KB
XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.20-beta-0309-non-reasoning"

TEXT_EXTENSIONS = frozenset({
    ".md", ".mdx", ".txt", ".yaml", ".yml", ".toml", ".json",
    ".py", ".sh", ".cfg", ".ini", ".rst", ".csv", ".env",
    ".html", ".css", ".js", ".ts", ".tsx", ".jsx",
})

BINARY_EXTENSIONS = frozenset({
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".sqlite", ".db", ".sqlite3",
    ".pickle", ".pkl", ".npy", ".npz",
    ".wasm", ".o", ".a", ".lib",
})

# Directories always excluded — matched against any path component
HARDCODED_EXCLUDE_DIRS = frozenset({
    "node_modules", ".venv", "venv", "__pycache__", ".git",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "htmlcov", ".tox", ".eggs", ".egg-info",
    ".DS_Store",
})

AUTHORITY_CLASSES = (
    "canonical", "historical", "operational",
    "audit", "template", "generated", "noise",
)

# ─── SECTION 2: Configuration ───────────────────────────────────────

def parse_size(s: str) -> int:
    """Parse human size string to bytes. E.g., '100KB' -> 102400."""
    s = s.strip().upper()
    multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if s.endswith(suffix):
            return int(float(s[: -len(suffix)].strip()) * mult)
    return int(s)  # bare number = bytes


@dataclass
class PrescanConfig:
    repo_root: Path
    output_dir: Path
    max_file_size: int
    max_corpus_size: int
    large_json_threshold: int
    include_globs: list[str]
    exclude_globs: list[str]
    model: str
    provider: str
    xai_base_url: str
    api_key_env: str
    temperature: float
    max_response_tokens: int
    litellm_proxy_url: str
    verbose: bool
    force: bool


def load_config(cli_args: argparse.Namespace) -> PrescanConfig:
    """Load TOML config and merge with CLI overrides."""
    # Determine repo root
    if cli_args.repo_root:
        repo_root = Path(cli_args.repo_root).resolve()
    else:
        repo_root = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        ).resolve()

    # Load TOML config
    config_path = Path(cli_args.config) if cli_args.config else repo_root / "scripts" / "doc_audit_prescan.toml"
    toml_data: dict[str, Any] = {}
    if config_path.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(config_path, "rb") as f:
            toml_data = tomllib.load(f)

    corpus_cfg = toml_data.get("corpus", {})
    model_cfg = toml_data.get("model", {})
    output_cfg = toml_data.get("output", {})

    # Merge: CLI > TOML > defaults
    return PrescanConfig(
        repo_root=repo_root,
        output_dir=(
            Path(cli_args.output_dir).resolve()
            if cli_args.output_dir
            else repo_root / output_cfg.get("default_dir", "extraction/prescan")
        ),
        max_file_size=(
            parse_size(cli_args.max_file_size)
            if cli_args.max_file_size
            else parse_size(corpus_cfg.get("max_file_size", "100KB"))
        ),
        max_corpus_size=(
            parse_size(cli_args.max_corpus_size)
            if cli_args.max_corpus_size
            else parse_size(corpus_cfg.get("max_corpus_size", "50MB"))
        ),
        large_json_threshold=corpus_cfg.get("large_json_threshold", {}).get(
            "max_bytes", DEFAULT_LARGE_JSON_THRESHOLD
        ),
        include_globs=cli_args.include + corpus_cfg.get("include_globs", []),
        exclude_globs=cli_args.exclude + corpus_cfg.get("exclude_globs", []),
        model=cli_args.model or model_cfg.get("default", DEFAULT_MODEL),
        provider=cli_args.provider or model_cfg.get("provider", "xai"),
        xai_base_url=model_cfg.get("base_url", XAI_BASE_URL),
        api_key_env=model_cfg.get("api_key_env", "XAI_API_KEY"),
        temperature=model_cfg.get("temperature", 0.1),
        max_response_tokens=model_cfg.get("max_response_tokens", 200000),
        litellm_proxy_url=model_cfg.get("litellm_fallback", {}).get(
            "proxy_url", "http://localhost:4000"
        ),
        verbose=cli_args.verbose,
        force=cli_args.force,
    )

# ─── SECTION 3: Data Models ─────────────────────────────────────────

@dataclass
class FileEntry:
    rel_path: str
    size_bytes: int
    extension: str
    authority_class: str = ""
    include: bool = True
    exclude_reason: str | None = None
    content_hash: str | None = None
    directory_class: str = ""  # top-level directory bucket

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CorpusStats:
    total_files_scanned: int = 0
    included_count: int = 0
    excluded_count: int = 0
    total_included_size: int = 0
    by_class: dict[str, dict[str, int]] = field(default_factory=dict)
    by_extension: dict[str, int] = field(default_factory=dict)
    by_directory: dict[str, int] = field(default_factory=dict)


@dataclass
class RunMetadata:
    timestamp: str = ""
    mode: str = ""
    config_hash: str = ""
    git_sha: str = ""
    git_branch: str = ""
    repo_root: str = ""
    script_version: str = SCRIPT_VERSION

# ─── SECTION 4: Corpus Walker ───────────────────────────────────────

def _is_excluded_dir(path: Path, repo_root: Path) -> bool:
    """Check if any path component is a hardcoded exclude."""
    rel = path.relative_to(repo_root)
    for part in rel.parts:
        if part in HARDCODED_EXCLUDE_DIRS:
            return True
        # Handle .egg-info suffix
        if part.endswith(".egg-info"):
            return True
    return False


def _matches_any_glob(rel_path_str: str, globs: list[str]) -> bool:
    """Check if relative path matches any glob pattern."""
    for pattern in globs:
        if fnmatch.fnmatch(rel_path_str, pattern):
            return True
        # Also check if any parent path matches
        if fnmatch.fnmatch(rel_path_str + "/", pattern):
            return True
    return False


def _sha256_file(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_corpus(config: PrescanConfig) -> list[FileEntry]:
    """Walk repo and build list of FileEntry objects."""
    entries: list[FileEntry] = []
    repo_root = config.repo_root

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue

        # Skip excluded directories
        if _is_excluded_dir(path, repo_root):
            continue

        rel_path = str(path.relative_to(repo_root))
        ext = path.suffix.lower()
        size = path.stat().st_size

        entry = FileEntry(
            rel_path=rel_path,
            size_bytes=size,
            extension=ext,
        )

        # Exclusion checks (in priority order)
        if ext in BINARY_EXTENSIONS:
            entry.include = False
            entry.exclude_reason = f"binary_extension:{ext}"
        elif _matches_any_glob(rel_path, config.exclude_globs):
            entry.include = False
            entry.exclude_reason = "matched_exclude_glob"
        elif size > config.max_file_size:
            entry.include = False
            entry.exclude_reason = f"size_exceeds_max:{size}>{config.max_file_size}"
        elif ext == ".json" and size > config.large_json_threshold:
            entry.include = False
            entry.exclude_reason = f"large_json_blob:{size}>{config.large_json_threshold}"
        elif ext not in TEXT_EXTENSIONS and ext != "":
            # Unknown extension — exclude unless it's small and looks textual
            entry.include = False
            entry.exclude_reason = f"unknown_extension:{ext}"

        # Compute hash for included files
        if entry.include:
            try:
                entry.content_hash = _sha256_file(path)
            except (OSError, PermissionError) as e:
                entry.include = False
                entry.exclude_reason = f"read_error:{e}"

        # Set directory class (top-level directory for grouping)
        parts = PurePosixPath(rel_path).parts
        entry.directory_class = parts[0] if len(parts) > 1 else "root"

        entries.append(entry)

    return entries

# ─── SECTION 5: Classifier ──────────────────────────────────────────

def classify_file(entry: FileEntry) -> str:
    """Classify a file into an authority class. First match wins."""
    p = PurePosixPath(entry.rel_path)
    parts_lower = [part.lower() for part in p.parts]
    name = p.name
    name_lower = name.lower()
    ext = entry.extension

    # If already excluded, classify as noise
    if not entry.include:
        return "noise"

    # ── noise ──
    if ext in BINARY_EXTENSIONS:
        return "noise"

    # ── generated ──
    if "runs" in parts_lower and any(
        x in ("extraction", "repo-truth-extractor") for x in parts_lower
    ):
        return "generated"
    if name_lower.startswith("latest_run_id"):
        return "generated"
    if "doctor" in parts_lower and ext == ".json":
        return "generated"
    if parts_lower[0] == "out" if parts_lower else False:
        return "generated"

    # ── template ──
    if "templates" in parts_lower:
        return "template"
    if ".claude" in parts_lower and "prompts" in parts_lower:
        return "template"
    if ".claude" in parts_lower and "modules" in parts_lower:
        return "template"
    if "upgrades" in parts_lower and "promptgen" in parts_lower:
        return "template"
    if "promptsets" in parts_lower:
        return "template"

    # ── historical ──
    if "archive" in parts_lower:
        return "historical"
    if "deprecated" in " ".join(parts_lower):
        return "historical"
    if "system_archive" in parts_lower:
        return "historical"
    if "completed-projects" in parts_lower:
        return "historical"
    if "implementation-history" in parts_lower:
        return "historical"
    if "old" in parts_lower and "sessions" in parts_lower:
        return "historical"

    # ── audit ──
    if parts_lower and parts_lower[0] == "reports":
        return "audit"
    if parts_lower and parts_lower[0] == "proof":
        return "audit"
    if "audit" in name_lower:
        return "audit"
    if "_audit_" in name_lower:
        return "audit"

    # ── operational ──
    if any(x in ("92-runbooks", "runbooks") for x in parts_lower):
        return "operational"
    if any(x in ("02-how-to", "01-tutorials") for x in parts_lower):
        return "operational"
    if name in ("INSTALL.md", "QUICK_START.md", "SETUP.md"):
        return "operational"
    if name == "README.md":
        return "operational"
    if "deploy" in parts_lower:
        return "operational"

    # ── canonical ──
    if "planes" in parts_lower:
        return "canonical"
    if any(x in ("03-reference", "04-explanation") for x in parts_lower):
        return "canonical"
    if any(x in ("90-adr", "91-rfc") for x in parts_lower):
        return "canonical"
    if name == "CLAUDE.md":
        return "canonical"
    if name in (
        "model_map_v2_tp008.yaml", "pyproject.toml", "compose.yml",
        "dopemux.toml", "litellm.config", "Makefile",
    ):
        return "canonical"

    # ── Fallbacks by directory ──
    if parts_lower and parts_lower[0] == "docs":
        return "canonical"
    if parts_lower and parts_lower[0] == ".claude":
        return "canonical"
    if parts_lower and parts_lower[0] == "upgrades":
        return "canonical"
    if parts_lower and parts_lower[0] == "scripts" and ext == ".md":
        return "operational"
    if parts_lower and parts_lower[0] == "scripts":
        return "operational"
    if len(p.parts) == 1 and ext in (".yaml", ".yml", ".toml"):
        return "canonical"

    # ── default ──
    return "generated"


def classify_all(entries: list[FileEntry]) -> None:
    """Classify all entries in-place."""
    for entry in entries:
        entry.authority_class = classify_file(entry)

# ─── SECTION 6: Manifest Builder ────────────────────────────────────

def _get_git_info(repo_root: Path) -> tuple[str, str]:
    """Return (sha, branch) from git."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sha = "UNKNOWN"
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        branch = "UNKNOWN"
    return sha, branch


def _human_size(n: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} TB"


def build_manifests(
    entries: list[FileEntry], config: PrescanConfig, mode: str
) -> tuple[CorpusStats, RunMetadata]:
    """Write all manifest files and return stats + metadata."""
    config.output_dir.mkdir(parents=True, exist_ok=True)

    included = [e for e in entries if e.include]
    excluded = [e for e in entries if not e.include]

    # ── corpus_manifest.json ──
    manifest_data = [e.to_dict() for e in sorted(entries, key=lambda x: x.rel_path)]
    (config.output_dir / "corpus_manifest.json").write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )

    # ── included_files.txt ──
    (config.output_dir / "included_files.txt").write_text(
        "\n".join(e.rel_path for e in sorted(included, key=lambda x: x.rel_path)) + "\n"
    )

    # ── excluded_files.txt ──
    (config.output_dir / "excluded_files.txt").write_text(
        "\n".join(
            f"{e.rel_path}\t{e.exclude_reason or 'unknown'}"
            for e in sorted(excluded, key=lambda x: x.rel_path)
        ) + "\n"
    )

    # ── corpus_stats.json ──
    stats = CorpusStats(
        total_files_scanned=len(entries),
        included_count=len(included),
        excluded_count=len(excluded),
        total_included_size=sum(e.size_bytes for e in included),
    )
    for e in included:
        cls = e.authority_class
        if cls not in stats.by_class:
            stats.by_class[cls] = {"count": 0, "total_size": 0}
        stats.by_class[cls]["count"] += 1
        stats.by_class[cls]["total_size"] += e.size_bytes

        stats.by_extension[e.extension] = stats.by_extension.get(e.extension, 0) + 1
        stats.by_directory[e.directory_class] = stats.by_directory.get(e.directory_class, 0) + 1

    (config.output_dir / "corpus_stats.json").write_text(
        json.dumps(asdict(stats), indent=2, sort_keys=True) + "\n"
    )

    # ── run_metadata.json ──
    sha, branch = _get_git_info(config.repo_root)
    config_str = json.dumps(asdict(config) if hasattr(config, '__dataclass_fields__') else str(config), sort_keys=True, default=str)
    meta = RunMetadata(
        timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
        mode=mode,
        config_hash=hashlib.sha256(config_str.encode()).hexdigest()[:16],
        git_sha=sha,
        git_branch=branch,
        repo_root=str(config.repo_root),
    )
    (config.output_dir / "run_metadata.json").write_text(
        json.dumps(asdict(meta), indent=2, sort_keys=True) + "\n"
    )

    return stats, meta

# ─── SECTION 7: Payload Packager ────────────────────────────────────

MAX_PREVIEW_LINES = 200
MAX_PREVIEW_BYTES = 8192

SYSTEM_PROMPT = """\
You are a documentation authority auditor for a software repository.
Analyze each file's content and metadata to confirm or revise its authority classification.

Authority classes:
- canonical: Active architecture docs, current PRDs, live configs, system specs
- historical: Archived plans, old strategies, past decisions (valuable for rediscovery)
- operational: Runbooks, how-tos, setup guides, README files
- audit: Reports, analysis outputs, proof bundles
- template: Prompt templates, skill templates, schema files
- generated: Auto-generated outputs, extraction results
- noise: Truly irrelevant (vendored deps, caches, binaries, test artifacts)

IMPORTANT: "historical" is NOT noise. These contain forgotten plans and ideas
that should be preserved for future development reconsideration.

Return valid JSON:
{
  "classifications": [
    {
      "path": "relative/file/path",
      "proposed_class": "class from pre-scanner",
      "confirmed_class": "your assessment",
      "confidence": 0.0-1.0,
      "reasoning": "brief explanation (max 50 words)",
      "signals": ["authority signal 1", "authority signal 2"]
    }
  ]
}
"""


def _read_preview(path: Path) -> str:
    """Read first N lines or N bytes of a file, whichever is smaller."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return "[UNREADABLE]"

    lines = text.splitlines(keepends=True)
    preview_lines = lines[:MAX_PREVIEW_LINES]
    preview = "".join(preview_lines)
    if len(preview.encode("utf-8")) > MAX_PREVIEW_BYTES:
        preview = preview.encode("utf-8")[:MAX_PREVIEW_BYTES].decode("utf-8", errors="replace")
    return preview


def package_payload(
    entries: list[FileEntry], config: PrescanConfig, meta: RunMetadata
) -> Path:
    """Build audit_payload.md with truncated file contents grouped by class."""
    included = [e for e in entries if e.include]
    by_class: dict[str, list[FileEntry]] = {}
    for e in included:
        by_class.setdefault(e.authority_class, []).append(e)

    lines: list[str] = [
        f"# Documentation Authority Audit Corpus",
        f"Generated: {meta.timestamp}",
        f"Git SHA: {meta.git_sha}",
        f"Files: {len(included)} | Total Size: {_human_size(sum(e.size_bytes for e in included))}",
        "",
    ]

    for cls in AUTHORITY_CLASSES:
        class_entries = by_class.get(cls, [])
        if not class_entries:
            continue
        lines.append(f"## {cls} ({len(class_entries)} files)")
        lines.append("")
        for e in sorted(class_entries, key=lambda x: x.rel_path):
            lines.append(f"### {e.rel_path} [{_human_size(e.size_bytes)}]")
            lines.append("```")
            preview = _read_preview(config.repo_root / e.rel_path)
            lines.append(preview.rstrip())
            lines.append("```")
            lines.append("")

    payload_path = config.output_dir / "audit_payload.md"
    payload_path.write_text("\n".join(lines), encoding="utf-8")
    return payload_path

# ─── SECTION 8: Direct Grok Caller ──────────────────────────────────

def call_grok_direct(payload_path: Path, config: PrescanConfig) -> dict | None:
    """Call Grok 4.20 Beta directly via xAI API. Returns parsed response or None."""
    api_key = os.environ.get(config.api_key_env)
    if not api_key:
        logger.error(
            f"❌ {config.api_key_env} not found in environment.\n"
            f"   Set it or use 'handoff' mode instead."
        )
        return None

    try:
        import openai
    except ImportError:
        logger.error(
            "❌ 'openai' package not installed.\n"
            "   pip install openai>=1.0.0"
        )
        return None

    payload_text = payload_path.read_text(encoding="utf-8")
    logger.info(f"📡 Calling {config.model} via {config.xai_base_url}...")
    logger.info(f"   Payload size: {_human_size(len(payload_text.encode()))}")

    client = openai.OpenAI(api_key=api_key, base_url=config.xai_base_url)

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload_text},
            ],
            temperature=config.temperature,
            response_format={"type": "json_object"},
        )
        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        out_path = config.output_dir / "grok_response.json"
        out_path.write_text(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        logger.info(f"✅ Response written to {out_path}")

        # Also save raw response metadata
        raw_meta = {
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
            },
            "finish_reason": response.choices[0].finish_reason,
        }
        (config.output_dir / "grok_call_metadata.json").write_text(
            json.dumps(raw_meta, indent=2) + "\n"
        )

        return result

    except Exception as e:
        logger.error(f"❌ API call failed: {e}")
        # Save error for debugging
        (config.output_dir / "grok_error.json").write_text(
            json.dumps({"error": str(e), "type": type(e).__name__}, indent=2) + "\n"
        )
        return None

# ─── SECTION 9: LiteLLM Handoff Builder ─────────────────────────────

def build_handoff_bundle(
    entries: list[FileEntry],
    payload_path: Path,
    config: PrescanConfig,
    meta: RunMetadata,
) -> Path:
    """Build a complete handoff bundle for CLI agent execution via LiteLLM."""
    bundle_dir = config.output_dir / "handoff_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    corpus_dir = bundle_dir / "corpus"
    corpus_dir.mkdir(exist_ok=True)

    # ── prompt.md ──
    (bundle_dir / "prompt.md").write_text(
        f"# System Prompt\n\n{SYSTEM_PROMPT}\n\n"
        f"# User Prompt\n\n"
        f"See the corpus files in the corpus/ directory, organized by authority class.\n"
        f"The audit_payload.md in the parent directory contains the full packaged corpus.\n"
    )

    # ── corpus/ per-class files ──
    included = [e for e in entries if e.include]
    by_class: dict[str, list[FileEntry]] = {}
    for e in included:
        by_class.setdefault(e.authority_class, []).append(e)

    for cls, class_entries in by_class.items():
        lines = [f"# {cls.upper()} — {len(class_entries)} files\n"]
        for e in sorted(class_entries, key=lambda x: x.rel_path):
            lines.append(f"## {e.rel_path} [{_human_size(e.size_bytes)}]")
            lines.append("```")
            preview = _read_preview(config.repo_root / e.rel_path)
            lines.append(preview.rstrip())
            lines.append("```\n")
        (corpus_dir / f"{cls}.md").write_text("\n".join(lines), encoding="utf-8")

    # ── manifest.json (copy of corpus manifest) ──
    src_manifest = config.output_dir / "corpus_manifest.json"
    if src_manifest.exists():
        (bundle_dir / "manifest.json").write_text(src_manifest.read_text())

    # ── routing.json ──
    litellm_model = config.model
    if not litellm_model.startswith("xai/"):
        litellm_model = f"xai/{config.model}"
    routing = {
        "model": litellm_model,
        "provider": config.provider,
        "base_url": config.xai_base_url,
        "litellm_proxy_url": config.litellm_proxy_url,
        "max_tokens": config.max_response_tokens,
        "temperature": config.temperature,
        "response_format": {"type": "json_object"},
        "api_key_env": config.api_key_env,
    }
    (bundle_dir / "routing.json").write_text(
        json.dumps(routing, indent=2, sort_keys=True) + "\n"
    )

    # ── instructions.md ──
    instructions = f"""\
# Handoff Instructions

## Option 1: Direct xAI call (Python)

```python
import openai, json

client = openai.OpenAI(
    api_key=os.environ["{config.api_key_env}"],
    base_url="{config.xai_base_url}",
)

payload = open("{payload_path.name}").read()

response = client.chat.completions.create(
    model="{config.model}",
    messages=[
        {{"role": "system", "content": open("handoff_bundle/prompt.md").read()}},
        {{"role": "user", "content": payload}},
    ],
    temperature={config.temperature},
    response_format={{"type": "json_object"}},
)

result = json.loads(response.choices[0].message.content)
json.dump(result, open("grok_response.json", "w"), indent=2)
```

## Option 2: Via LiteLLM proxy

```bash
# Start LiteLLM proxy (if not running)
litellm --config litellm.config --port 4000

# Call via proxy
curl {config.litellm_proxy_url}/chat/completions \\
  -H "Content-Type: application/json" \\
  -d @request.json
```

## Option 3: Hand to CLI agent

Provide the agent with:
1. This handoff_bundle/ directory
2. The routing.json for model/provider config
3. The audit_payload.md as input
4. Ask it to return grok_response.json with the classification results
"""
    (bundle_dir / "instructions.md").write_text(instructions)

    # ── checksums.json ──
    checksums: dict[str, str] = {}
    for fpath in sorted(bundle_dir.rglob("*")):
        if fpath.is_file() and fpath.name != "checksums.json":
            rel = str(fpath.relative_to(bundle_dir))
            checksums[rel] = _sha256_file(fpath)
    # Also checksum the payload
    if payload_path.exists():
        checksums[f"../{payload_path.name}"] = _sha256_file(payload_path)

    (bundle_dir / "checksums.json").write_text(
        json.dumps(checksums, indent=2, sort_keys=True) + "\n"
    )

    return bundle_dir

# ─── SECTION 10: CLI Entry Point ────────────────────────────────────

def _print_summary(stats: CorpusStats, config: PrescanConfig) -> None:
    """Print ADHD-friendly summary to stdout."""
    print(f"\n📋 Classification Summary:")
    for cls in AUTHORITY_CLASSES:
        info = stats.by_class.get(cls, {"count": 0, "total_size": 0})
        if info["count"] > 0:
            print(f"  {cls:12s}: {info['count']:4d} files ({_human_size(info['total_size'])})")
    print(f"\n📦 Total corpus: {stats.included_count} files, {_human_size(stats.total_included_size)}")
    if stats.total_included_size > config.max_corpus_size:
        print(f"⚠️  Exceeds {_human_size(config.max_corpus_size)} limit!")
    else:
        print(f"✅ Under {_human_size(config.max_corpus_size)} limit")
    print(f"🚫 Excluded: {stats.excluded_count} files")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="doc_audit_prescan",
        description="Pre-scan documentation authority/noise audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  %(prog)s dry-run --verbose\n"
               "  %(prog)s direct --model grok-4.20-beta\n"
               "  %(prog)s handoff --output-dir /tmp/audit\n",
    )
    parser.add_argument(
        "mode", choices=["dry-run", "direct", "handoff"],
        help="Execution mode: dry-run (manifests only), direct (call Grok), handoff (write bundle)",
    )
    parser.add_argument("--repo-root", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--max-file-size", type=str, default=None)
    parser.add_argument("--max-corpus-size", type=str, default=None)
    parser.add_argument("--include", action="append", default=[], help="Additional include glob")
    parser.add_argument("--exclude", action="append", default=[], help="Additional exclude glob")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--provider", type=str, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--force", action="store_true", help="Override corpus size limit")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    mode = args.mode
    logger.info(f"🚀 Starting pre-scan audit (mode: {mode})")

    # Load config
    config = load_config(args)
    logger.info(f"📂 Repo root: {config.repo_root}")
    logger.info(f"📁 Output dir: {config.output_dir}")

    # Walk corpus
    logger.info("📊 Walking corpus...")
    entries = walk_corpus(config)
    logger.info(f"   Scanned {len(entries)} files")

    # Classify
    classify_all(entries)

    # Build manifests (always, for all modes)
    stats, meta = build_manifests(entries, config, mode)
    _print_summary(stats, config)
    logger.info(f"\n📄 Manifests written to {config.output_dir}/")

    # Corpus size safety gate
    if stats.total_included_size > config.max_corpus_size and not config.force:
        logger.error(
            f"\n🛑 Corpus size ({_human_size(stats.total_included_size)}) exceeds "
            f"limit ({_human_size(config.max_corpus_size)}).\n"
            f"   Use --force to override, or add --exclude patterns."
        )
        return 1

    # Mode-specific execution
    if mode == "dry-run":
        logger.info("✅ Dry run complete. Review manifests before proceeding.")
        return 0

    # Package payload (needed for both direct and handoff)
    logger.info("📦 Packaging audit payload...")
    payload_path = package_payload(entries, config, meta)
    logger.info(f"   Payload: {payload_path} ({_human_size(payload_path.stat().st_size)})")

    if mode == "direct":
        result = call_grok_direct(payload_path, config)
        if result is None:
            logger.error("❌ Direct call failed. Try 'handoff' mode instead.")
            return 1
        n_classifications = len(result.get("classifications", []))
        logger.info(f"✅ Received {n_classifications} classifications from Grok")
        return 0

    if mode == "handoff":
        bundle_dir = build_handoff_bundle(entries, payload_path, config, meta)
        logger.info(f"\n✅ Handoff bundle written to {bundle_dir}/")
        logger.info("   See handoff_bundle/instructions.md for next steps.")
        return 0

    return 1  # Should not reach here


if __name__ == "__main__":
    sys.exit(main())
