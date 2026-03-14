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
import ast as _ast
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

logger = logging.getLogger(__name__)

# ─── SECTION 1: Constants ───────────────────────────────────────────

SCRIPT_VERSION = "3.0.0"

DEFAULT_MAX_FILE_SIZE = 100 * 1024  # 100KB
DEFAULT_MAX_CORPUS_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_LARGE_JSON_THRESHOLD = 500 * 1024  # 500KB
XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.20-beta-0309-non-reasoning"

TEXT_EXTENSIONS = frozenset(
    {
        ".md",
        ".mdx",
        ".txt",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
        ".py",
        ".sh",
        ".cfg",
        ".ini",
        ".rst",
        ".csv",
        ".env",
        ".html",
        ".css",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
    }
)

BINARY_EXTENSIONS = frozenset(
    {
        ".pyc",
        ".pyo",
        ".so",
        ".dylib",
        ".dll",
        ".exe",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".bmp",
        ".webp",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".otf",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".rar",
        ".mp3",
        ".mp4",
        ".wav",
        ".avi",
        ".mov",
        ".mkv",
        ".sqlite",
        ".db",
        ".sqlite3",
        ".pickle",
        ".pkl",
        ".npy",
        ".npz",
        ".wasm",
        ".o",
        ".a",
        ".lib",
    }
)

# Directories always excluded — matched against any path component
HARDCODED_EXCLUDE_DIRS = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        ".tox",
        ".eggs",
        ".egg-info",
        ".DS_Store",
    }
)

AUTHORITY_CLASSES = (
    "canonical",
    "historical",
    "operational",
    "audit",
    "template",
    "generated",
    "noise",
    "ghost",
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
            )
            .decode()
            .strip()
        ).resolve()

    # Load TOML config
    config_path = (
        Path(cli_args.config)
        if cli_args.config
        else repo_root / "scripts" / "doc_audit_prescan.toml"
    )
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

    # ── Git enrichment ──
    last_commit_date: str | None = None
    last_commit_sha: str | None = None
    first_commit_date: str | None = None
    commit_count: int = 0
    last_author: str | None = None
    days_since_modified: int | None = None
    churn_score: float = 0.0
    contributor_count: int = 0
    lifecycle_stage: str = ""  # fresh|active|stale|frozen|unknown
    was_renamed: bool = False
    previous_paths: list[str] = field(default_factory=list)

    # ── Duplicate detection ──
    duplicate_group_id: str | None = None
    is_duplicate: bool = False
    canonical_duplicate: str | None = None

    # ── Version chain ──
    version_chain_id: str | None = None
    version_ordinal: int = 0
    is_latest_version: bool = True

    # ── Feature gaps ──
    has_todo_markers: bool = False
    has_stub_methods: bool = False
    is_draft_doc: bool = False
    is_proposed_adr: bool = False

    # ── Ghost recovery ──
    is_ghost: bool = False
    deleted_at_sha: str | None = None
    deleted_date: str | None = None
    recovery_source: str = ""

    # ── Code intelligence ──
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
            entry.exclude_reason = (
                f"large_json_blob:{size}>{config.large_json_threshold}"
            )
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
        "model_map_v2_tp008.yaml",
        "pyproject.toml",
        "compose.yml",
        "dopemux.toml",
        "litellm.config",
        "Makefile",
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


# ─── SECTION 5.5: Git Intelligence ──────────────────────────────────

_COMMIT_SEP = "!!!COMMIT!!!"


def _parse_git_log_for_files(
    repo_root: Path,
) -> dict[str, list[tuple[str, str, str]]]:
    """
    Single git log call → {rel_path: [(sha, author, date), ...]} newest-first.
    """
    try:
        raw = subprocess.check_output(
            [
                "git",
                "log",
                f"--format={_COMMIT_SEP}%H|%an|%ad",
                "--date=short",
                "--name-only",
                "--diff-filter=AMRC",
            ],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            timeout=120,
        ).decode(errors="replace")
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return {}

    per_file: dict[str, list[tuple[str, str, str]]] = {}
    current: tuple[str, str, str] | None = None

    for line in raw.splitlines():
        if line.startswith(_COMMIT_SEP):
            header = line[len(_COMMIT_SEP) :]
            parts = header.split("|", 2)
            sha = parts[0] if parts else ""
            author = parts[1] if len(parts) > 1 else ""
            date = parts[2].strip() if len(parts) > 2 else ""
            current = (sha, author, date)
        elif line.strip() and current:
            per_file.setdefault(line.strip(), []).append(current)

    return per_file


def _parse_renames(repo_root: Path) -> dict[str, list[str]]:
    """Returns {new_path: [old_path1, ...]} from git rename history."""
    try:
        raw = subprocess.check_output(
            ["git", "log", "--diff-filter=R", "--name-status", "--format="],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            timeout=60,
        ).decode(errors="replace")
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return {}

    renames: dict[str, list[str]] = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("R"):
            parts = line.split("\t")
            if len(parts) == 3:
                old_path, new_path = parts[1], parts[2]
                renames.setdefault(new_path, []).append(old_path)
    return renames


def enrich_with_git(entries: list[FileEntry], repo_root: Path) -> None:
    """Enrich FileEntry list with git metadata. Modifies entries in-place."""
    per_file = _parse_git_log_for_files(repo_root)
    renames = _parse_renames(repo_root)
    today = dt.date.today()

    for entry in entries:
        if entry.is_ghost:
            continue
        commits = per_file.get(entry.rel_path, [])
        if not commits:
            entry.lifecycle_stage = "unknown"
            continue

        entry.last_commit_sha = commits[0][0]
        entry.last_author = commits[0][1]
        entry.last_commit_date = commits[0][2]
        entry.first_commit_date = commits[-1][2]
        entry.commit_count = len(commits)
        entry.contributor_count = len({c[1] for c in commits})

        try:
            last_d = dt.date.fromisoformat(entry.last_commit_date)
            entry.days_since_modified = (today - last_d).days
        except (ValueError, TypeError):
            pass

        if entry.first_commit_date and entry.days_since_modified is not None:
            try:
                first_d = dt.date.fromisoformat(entry.first_commit_date)
                age_days = max((today - first_d).days, 1)
                entry.churn_score = round(entry.commit_count / (age_days / 30), 3)
            except (ValueError, TypeError):
                pass

        dsm = entry.days_since_modified
        if dsm is not None:
            if dsm < 30:
                entry.lifecycle_stage = "fresh"
            elif dsm < 90:
                entry.lifecycle_stage = "active"
            elif dsm < 365:
                entry.lifecycle_stage = "stale"
            else:
                entry.lifecycle_stage = "frozen"

        prev = renames.get(entry.rel_path, [])
        if prev:
            entry.was_renamed = True
            entry.previous_paths = prev[:5]


def recover_ghost_files(
    existing_paths: set[str],
    repo_root: Path,
    max_ghosts: int = 50,
) -> list[FileEntry]:
    """
    Recover recently-deleted doc files from git history.
    Returns synthetic ghost FileEntry list (authority_class='ghost').
    """
    _GHOST_SEP = "!!!DEL!!!"
    ghost_exts = {".md", ".yaml", ".yml", ".toml", ".py", ".rst", ".txt"}
    ghost_exclude = {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "htmlcov",
        "extraction",
        "runs",
        "tmp",
        "dist",
        "build",
    }

    try:
        raw = subprocess.check_output(
            [
                "git",
                "log",
                "--diff-filter=D",
                "--name-only",
                f"--format={_GHOST_SEP}%H|%ad",
                "--date=short",
            ],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            timeout=60,
        ).decode(errors="replace")
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return []

    ghosts: list[FileEntry] = []
    seen_paths: set[str] = set()
    current_meta: tuple[str, str] = ("", "")

    for line in raw.splitlines():
        if line.startswith(_GHOST_SEP):
            parts = line[len(_GHOST_SEP) :].split("|", 1)
            sha = parts[0] if parts else ""
            date = parts[1].strip() if len(parts) > 1 else ""
            current_meta = (sha, date)
        elif line.strip() and current_meta[0]:
            fp = line.strip()
            ext = Path(fp).suffix.lower()
            if ext not in ghost_exts:
                continue
            if fp in existing_paths or fp in seen_paths:
                continue
            parts_fp = PurePosixPath(fp).parts
            if any(p in ghost_exclude for p in parts_fp):
                continue
            seen_paths.add(fp)
            ghost = FileEntry(
                rel_path=fp,
                size_bytes=0,
                extension=ext,
                authority_class="ghost",
                include=True,
                directory_class=parts_fp[0] if len(parts_fp) > 1 else "root",
                is_ghost=True,
                deleted_at_sha=current_meta[0],
                deleted_date=current_meta[1],
                recovery_source="git_history",
            )
            ghosts.append(ghost)
            if len(ghosts) >= max_ghosts:
                break

    return ghosts


def detect_duplicates(entries: list[FileEntry]) -> int:
    """
    Group included files by SHA256 hash.
    Marks duplicate_group_id/is_duplicate/canonical_duplicate in-place.
    Returns number of duplicate groups found.
    """
    hash_groups: dict[str, list[FileEntry]] = {}
    for e in entries:
        if e.include and e.content_hash and not e.is_ghost:
            hash_groups.setdefault(e.content_hash, []).append(e)

    groups_found = 0
    for h, group in hash_groups.items():
        if len(group) < 2:
            continue
        groups_found += 1
        group_id = h[:8]
        canonical = min(group, key=lambda x: len(x.rel_path))
        for e in group:
            e.duplicate_group_id = group_id
            if e is canonical:
                e.is_duplicate = False
            else:
                e.is_duplicate = True
                e.canonical_duplicate = canonical.rel_path

    return groups_found


_VERSION_PATTERNS = [  # noqa: E501
    (re.compile(r"^(.+?)[-_]v(\d+)(\.|$)"), "v-suffix"),
    (re.compile(r"^(.+?)[-_](\d+)(\.|$)"), "num-suffix"),
    (
        re.compile(r"^(.+?)[-_](old|new|bak|backup|orig|copy)(\.|$)", re.I),
        "name-suffix",
    ),
    (re.compile(r"^(.+?)\.(v\d+)$"), "dotversion"),
]


def detect_version_chains(entries: list[FileEntry]) -> int:
    """
    Detect version chains from filename patterns (-v2, -2, -old, etc.).
    Assigns version_chain_id/version_ordinal/is_latest_version in-place.
    Returns number of chains found.
    """
    by_dir: dict[str, list[FileEntry]] = {}
    for e in entries:
        if not e.include and not e.is_ghost:
            continue
        d = str(PurePosixPath(e.rel_path).parent)
        by_dir.setdefault(d, []).append(e)

    chain_map: dict[str, list[FileEntry]] = {}
    for dir_path, dir_entries in by_dir.items():
        for e in dir_entries:
            fname = PurePosixPath(e.rel_path).stem
            ext = e.extension
            for pattern, _ in _VERSION_PATTERNS:
                m = pattern.match(fname)
                if m:
                    base = m.group(1)
                    chain_key = f"{dir_path}::{base}{ext}"
                    chain_map.setdefault(chain_key, []).append(e)
                    break

    chains_found = 0
    for chain_key, chain_entries in chain_map.items():
        if len(chain_entries) < 2:
            continue
        chains_found += 1
        chain_id = hashlib.sha256(chain_key.encode()).hexdigest()[:8]

        def _version_key(e: FileEntry) -> int:
            m = re.search(r"(\d+)$", PurePosixPath(e.rel_path).stem)
            return int(m.group(1)) if m else 0

        sorted_chain = sorted(chain_entries, key=_version_key)
        last_idx = len(sorted_chain) - 1
        for ordinal, e in enumerate(sorted_chain):
            e.version_chain_id = chain_id
            e.version_ordinal = ordinal
            e.is_latest_version = ordinal == last_idx

    return chains_found


def scan_feature_gaps(entries: list[FileEntry], repo_root: Path) -> None:
    """
    Scan included files for planned-but-unimplemented feature signals.
    Marks has_todo_markers/has_stub_methods/is_draft_doc/is_proposed_adr.
    """
    _TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|NOT[_ ]IMPLEMENTED)\b", re.I)
    _STUB_RE = re.compile(r"raise\s+NotImplementedError")
    _DRAFT_RE = re.compile(r"^status:\s*(draft|proposed|wip)\b", re.I | re.M)
    _ADR_RE = re.compile(r"^(status|type):\s*(proposed|draft)\b", re.I | re.M)

    for e in entries:
        if not e.include or e.is_ghost:
            continue
        try:
            text = (repo_root / e.rel_path).read_text(
                encoding="utf-8", errors="replace"
            )
        except (OSError, PermissionError):
            continue

        if _TODO_RE.search(text):
            e.has_todo_markers = True
        if _STUB_RE.search(text):
            e.has_stub_methods = True
        if _DRAFT_RE.search(text):
            e.is_draft_doc = True
        if "90-adr" in e.rel_path and _ADR_RE.search(text):
            e.is_proposed_adr = True


def detect_co_change_groups(entries: list[FileEntry], repo_root: Path) -> list[dict]:
    """
    Build co-change groups from git commit history.
    Returns top-50 groups [{group_id, files, commit_count}] sorted by frequency.
    """
    _CC_SEP = "!!!CC!!!"
    included_paths = {e.rel_path for e in entries if e.include}

    try:
        raw = subprocess.check_output(
            [
                "git",
                "log",
                f"--format={_CC_SEP}%H",
                "--name-only",
                "--diff-filter=AMRC",
            ],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            timeout=120,
        ).decode(errors="replace")
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return []

    current_files: list[str] = []
    co_counts: dict[frozenset, int] = {}

    for line in raw.splitlines():
        if line.startswith(_CC_SEP):
            if len(current_files) >= 2:
                in_commit = [f for f in current_files if f in included_paths]
                if len(in_commit) >= 2:
                    key = frozenset(in_commit[:10])
                    co_counts[key] = co_counts.get(key, 0) + 1
            current_files = []
        elif line.strip():
            current_files.append(line.strip())

    groups = [
        {
            "group_id": hashlib.sha256("|".join(sorted(files)).encode()).hexdigest()[
                :8
            ],
            "files": sorted(files),
            "commit_count": count,
        }
        for files, count in co_counts.items()
        if count >= 3
    ]
    groups.sort(key=lambda g: g["commit_count"], reverse=True)
    return groups[:50]


# ─── SECTION 5.6: Code Intelligence ────────────────────────────────────


def analyze_python_ast(filepath: Path) -> dict[str, Any]:
    """Parse a Python file with stdlib ast and extract structural metadata."""
    result: dict[str, Any] = {
        "functions": [],
        "classes": [],
        "imports": [],
        "decorators": [],
        "has_main_guard": False,
        "docstring_count": 0,
        "total_defs": 0,
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = _ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return result

    for node in _ast.walk(tree):
        if isinstance(node, _ast.FunctionDef | _ast.AsyncFunctionDef):
            result["functions"].append(node.name)
            result["total_defs"] += 1
            if _ast.get_docstring(node):
                result["docstring_count"] += 1
            for dec in node.decorator_list:
                dec_name = _decorator_name(dec)
                if dec_name:
                    result["decorators"].append(dec_name)
        elif isinstance(node, _ast.ClassDef):
            result["classes"].append(node.name)
            result["total_defs"] += 1
            if _ast.get_docstring(node):
                result["docstring_count"] += 1
        elif isinstance(node, _ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name)
        elif isinstance(node, _ast.ImportFrom):
            if node.module:
                result["imports"].append(node.module)
        elif isinstance(node, _ast.If):
            # Detect if __name__ == "__main__"
            if _is_main_guard(node):
                result["has_main_guard"] = True

    return result


def _decorator_name(node: _ast.expr) -> str:
    """Extract decorator name from AST node."""
    if isinstance(node, _ast.Name):
        return node.id
    if isinstance(node, _ast.Attribute):
        return f"{_decorator_name(node.value)}.{node.attr}" if isinstance(
            node.value, (_ast.Name, _ast.Attribute)
        ) else node.attr
    if isinstance(node, _ast.Call):
        return _decorator_name(node.func)
    return ""


def _is_main_guard(node: _ast.If) -> bool:
    """Check if an If node is 'if __name__ == "__main__"'."""
    try:
        test = node.test
        if isinstance(test, _ast.Compare):
            left = test.left
            if isinstance(left, _ast.Name) and left.id == "__name__":
                return True
            if (
                test.comparators
                and isinstance(test.comparators[0], _ast.Name)
                and test.comparators[0].id == "__name__"
            ):
                return True
    except (AttributeError, IndexError):
        pass
    return False


_ENTRY_POINT_DECORATORS = frozenset({
    "click.command", "click.group",
    "app.get", "app.post", "app.put", "app.delete", "app.patch",
    "app.route", "app.api_route", "app.websocket",
    "router.get", "router.post", "router.put", "router.delete",
    "router.patch", "router.route", "router.api_route",
    "main", "cli",
})


def enrich_with_code_intelligence(
    entries: list[FileEntry], repo_root: Path
) -> dict[str, Any]:
    """
    Run full code intelligence: AST analysis, import graph,
    entry point detection, test mapping, and complexity scoring.
    Returns aggregate code intelligence dict for the report.
    """
    py_entries = [
        e for e in entries
        if e.rel_path.endswith(".py") and e.include and not e.is_ghost
    ]
    logger.info(f"  • Analysing {len(py_entries)} Python files with AST...")

    # ── Phase 1: AST analysis + populate FileEntry fields ──
    ast_cache: dict[str, dict] = {}
    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        info = analyze_python_ast(fp)
        ast_cache[e.rel_path] = info
        e.function_count = len(info["functions"])
        e.class_count = len(info["classes"])
        e.import_count = len(info["imports"])
        total_defs = info["total_defs"]
        e.docstring_coverage = (
            info["docstring_count"] / total_defs if total_defs > 0 else 0.0
        )
        # Entry point detection
        if info["has_main_guard"]:
            e.is_entry_point = True
        for dec in info["decorators"]:
            if any(ep in dec for ep in _ENTRY_POINT_DECORATORS):
                e.is_entry_point = True
                break

    # ── Phase 2: Import graph ──
    logger.info("  • Building import graph...")
    import_graph = _build_import_graph(py_entries, ast_cache, repo_root)

    # ── Phase 3: Test mapping ──
    logger.info("  • Mapping tests to implementations...")
    _map_tests(py_entries)

    # ── Phase 4: Complexity scoring ──
    logger.info("  • Computing complexity scores...")
    _compute_complexity(py_entries, repo_root)

    # ── Phase 5: Primary author ──
    logger.info("  • Detecting primary authors...")
    _detect_primary_authors(py_entries, repo_root)

    # ── Aggregate ──
    entry_points = [e.rel_path for e in py_entries if e.is_entry_point]
    orphans = [e.rel_path for e in py_entries if e.is_orphan]
    hubs = sorted(
        [
            {"path": e.rel_path, "imported_by": e.imported_by_count}
            for e in py_entries
            if e.imported_by_count >= 5
        ],
        key=lambda x: x["imported_by"],
        reverse=True,
    )
    tested_count = sum(1 for e in py_entries if e.tested_by)
    untested = [
        e.rel_path for e in py_entries
        if not e.tested_by and e.is_entry_point
    ]
    complexity_hotspots = sorted(
        [
            {"path": e.rel_path, "score": round(e.complexity_score, 2)}
            for e in py_entries
            if e.complexity_score > 0.6
        ],
        key=lambda x: x["score"],
        reverse=True,
    )[:20]

    total_docstrings = sum(e.docstring_coverage for e in py_entries)
    avg_docstring_cov = total_docstrings / len(py_entries) if py_entries else 0

    return {
        "total_python_files": len(py_entries),
        "entry_points": entry_points[:50],
        "entry_point_count": len(entry_points),
        "orphan_files": orphans[:50],
        "orphan_count": len(orphans),
        "hub_files": hubs[:20],
        "hub_count": len(hubs),
        "circular_imports": import_graph.get("circular", [])[:20],
        "circular_count": len(import_graph.get("circular", [])),
        "untested_entry_points": untested[:30],
        "test_coverage_ratio": round(
            tested_count / len(py_entries) if py_entries else 0, 2
        ),
        "complexity_hotspots": complexity_hotspots,
        "import_graph_summary": {
            "nodes": import_graph["nodes"],
            "edges": import_graph["edges"],
            "components": import_graph.get("components", 0),
        },
        "avg_docstring_coverage": round(avg_docstring_cov, 2),
    }


def _build_import_graph(
    py_entries: list[FileEntry],
    ast_cache: dict[str, dict],
    repo_root: Path,
) -> dict[str, Any]:
    """Build directed import graph; detect orphans, hubs, circular imports."""
    # Map module paths to rel_paths
    path_to_module: dict[str, str] = {}
    module_to_path: dict[str, str] = {}
    for e in py_entries:
        mod = e.rel_path.replace("/", ".").replace("\\", ".")
        if mod.endswith(".py"):
            mod = mod[:-3]
        if mod.endswith(".__init__"):
            mod = mod[:-9]
        path_to_module[e.rel_path] = mod
        module_to_path[mod] = e.rel_path

    # Build adjacency (who imports whom)
    adjacency: dict[str, set[str]] = defaultdict(set)
    reverse_adj: dict[str, set[str]] = defaultdict(set)
    edge_count = 0

    for e in py_entries:
        info = ast_cache.get(e.rel_path, {})
        for imp in info.get("imports", []):
            # Try to resolve import to a file in the repo
            target = _resolve_import(imp, module_to_path)
            if target and target != e.rel_path:
                adjacency[e.rel_path].add(target)
                reverse_adj[target].add(e.rel_path)
                edge_count += 1

    # Populate imported_by_count and is_orphan
    for e in py_entries:
        e.imported_by_count = len(reverse_adj.get(e.rel_path, set()))
        if e.imported_by_count == 0 and not e.is_entry_point:
            # Not imported by anyone and not an entry point
            if not e.rel_path.endswith("__init__.py"):
                e.is_orphan = True

    # Detect circular imports (simple: A→B→A)
    circular: list[list[str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for src, targets in adjacency.items():
        for tgt in targets:
            if tgt in adjacency and src in adjacency[tgt]:
                pair = tuple(sorted([src, tgt]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    circular.append(list(pair))

    # Connected components (simple BFS)
    visited: set[str] = set()
    components = 0
    all_nodes = set(adjacency.keys()) | set(reverse_adj.keys())
    for node in all_nodes:
        if node in visited:
            continue
        components += 1
        queue = [node]
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(adjacency.get(current, set()) - visited)
            queue.extend(reverse_adj.get(current, set()) - visited)

    return {
        "nodes": len(all_nodes),
        "edges": edge_count,
        "circular": circular,
        "components": components,
    }


def _resolve_import(imp: str, module_to_path: dict[str, str]) -> str | None:
    """Try to resolve an import string to a repo-relative file path."""
    # Try exact match
    if imp in module_to_path:
        return module_to_path[imp]
    # Try progressively shorter prefixes (e.g. dopemux.cli → src.dopemux.cli)
    parts = imp.split(".")
    for prefix_mod, path in module_to_path.items():
        prefix_parts = prefix_mod.split(".")
        if len(parts) <= len(prefix_parts) and prefix_parts[-len(parts):] == parts:
            return path
    return None


def _map_tests(py_entries: list[FileEntry]) -> None:
    """Map test files to implementation files by naming convention."""
    test_entries: dict[str, FileEntry] = {}
    impl_entries: dict[str, FileEntry] = {}

    for e in py_entries:
        basename = Path(e.rel_path).stem
        if basename.startswith("test_"):
            impl_name = basename[5:]  # strip "test_"
            test_entries[impl_name] = e
        elif basename.endswith("_test"):
            impl_name = basename[:-5]
            test_entries[impl_name] = e
        else:
            impl_entries[basename] = e

    for impl_name, test_entry in test_entries.items():
        test_entry.tests_file = impl_entries.get(impl_name, FileEntry(
            rel_path="", size_bytes=0, extension=""
        )).rel_path or None
        if impl_name in impl_entries:
            impl_entries[impl_name].tested_by = test_entry.rel_path


def _compute_complexity(py_entries: list[FileEntry], repo_root: Path) -> None:
    """Compute a composite complexity score 0-1 for each Python file."""
    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        loc = len(lines)
        # Score components (all 0-1):
        # - LOC: >500 = 1.0, <50 = 0.0
        loc_score = min(1.0, max(0.0, (loc - 50) / 450))
        # - Function density: >20 = 1.0
        func_score = min(1.0, e.function_count / 20)
        # - Class count: >5 = 1.0
        class_score = min(1.0, e.class_count / 5)
        # - Low docstring coverage = higher complexity
        doc_score = 1.0 - e.docstring_coverage
        # Composite (weighted)
        e.complexity_score = round(
            0.35 * loc_score + 0.25 * func_score + 0.15 * class_score + 0.25 * doc_score,
            3,
        )


def _detect_primary_authors(py_entries: list[FileEntry], repo_root: Path) -> None:
    """Detect primary author (most commits) per file via git shortlog."""
    paths = [e.rel_path for e in py_entries if not e.is_ghost]
    if not paths:
        return
    # Batch: git log for all files at once, parse per-file
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H %aN", "--name-only", "--no-merges", "-n", "500"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return
    except (subprocess.TimeoutExpired, OSError):
        return

    file_authors: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    current_author = ""
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0:40].replace(" ", "").isalnum() and " " in line[:42]:
            # Commit line: <sha> <author>
            parts = line.split(" ", 1)
            if len(parts) == 2 and len(parts[0]) == 40:
                current_author = parts[1]
        elif current_author:
            file_authors[line][current_author] += 1

    path_set = {e.rel_path for e in py_entries}
    for e in py_entries:
        if e.rel_path in file_authors:
            authors = file_authors[e.rel_path]
            if authors:
                e.primary_author = max(authors, key=authors.get)


# ─── SECTION 5.7: Architecture Intelligence ───────────────────────────


def enrich_with_arch_intelligence(
    entries: list[FileEntry], repo_root: Path
) -> dict[str, Any]:
    """Run architecture intelligence: compose topology, service registry,
    event flows, API surface. Returns aggregate dict for report."""

    logger.info("  • Parsing compose.yml topology...")
    compose_data = _parse_compose_topology(repo_root)

    logger.info("  • Parsing service registry...")
    registry_data = _parse_service_registry(repo_root)

    logger.info("  • Mapping files to services...")
    file_service_map = _map_files_to_services(entries, compose_data, registry_data)

    logger.info("  • Detecting event flow patterns...")
    event_flows = _detect_event_flows(entries, repo_root)

    logger.info("  • Detecting API surface...")
    api_endpoints = _detect_api_surface(entries, repo_root)

    # Build port map
    port_map: dict[str, str] = {}
    for svc in compose_data.get("services", []):
        for port in svc.get("ports", []):
            host_port = str(port).split(":")[0]
            port_map[host_port] = svc["name"]

    # Service dependency graph
    dep_graph: dict[str, list[str]] = {}
    for svc in compose_data.get("services", []):
        deps = svc.get("depends_on", [])
        if deps:
            dep_graph[svc["name"]] = deps

    # Service-level file groupings for partition hints
    service_partitions: dict[str, list[str]] = defaultdict(list)
    for path, svc_name in file_service_map.items():
        service_partitions[svc_name].append(path)

    return {
        "services": compose_data.get("services", []),
        "service_count": len(compose_data.get("services", [])),
        "service_dependency_graph": dep_graph,
        "api_endpoints": api_endpoints[:100],
        "api_endpoint_count": len(api_endpoints),
        "event_flows": event_flows[:50],
        "event_flow_count": len(event_flows),
        "port_map": port_map,
        "file_service_map_count": len(file_service_map),
        "service_partitions": {
            k: sorted(v)[:50] for k, v in sorted(
                service_partitions.items(), key=lambda x: len(x[1]), reverse=True
            )
        },
    }


def _parse_compose_topology(repo_root: Path) -> dict[str, Any]:
    """Parse compose.yml for services, ports, depends_on, build contexts."""
    compose_path = repo_root / "compose.yml"
    if not compose_path.exists():
        compose_path = repo_root / "docker-compose.yml"
    if not compose_path.exists():
        return {"services": []}

    try:
        import yaml
        with open(compose_path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return {"services": []}

    if not isinstance(data, dict):
        return {"services": []}

    services_raw = data.get("services", {})
    if not isinstance(services_raw, dict):
        return {"services": []}

    services = []
    for name, cfg in services_raw.items():
        if not isinstance(cfg, dict):
            continue
        # Extract ports
        ports = []
        for p in cfg.get("ports", []):
            ports.append(str(p))

        # Extract depends_on
        deps = cfg.get("depends_on", [])
        if isinstance(deps, dict):
            deps = list(deps.keys())
        elif not isinstance(deps, list):
            deps = []

        # Build context
        build = cfg.get("build", "")
        if isinstance(build, dict):
            build_ctx = build.get("context", "")
        else:
            build_ctx = str(build)

        services.append({
            "name": name,
            "ports": ports,
            "depends_on": deps,
            "build_context": build_ctx,
            "image": cfg.get("image", ""),
            "has_healthcheck": "healthcheck" in cfg,
            "networks": list(cfg.get("networks", {}).keys())
            if isinstance(cfg.get("networks"), dict)
            else cfg.get("networks", []),
        })

    return {"services": services}


def _parse_service_registry(repo_root: Path) -> dict[str, Any]:
    """Parse services/registry.yaml for canonical service metadata."""
    reg_path = repo_root / "services" / "registry.yaml"
    if not reg_path.exists():
        return {"services": {}}
    try:
        import yaml
        with open(reg_path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {"services": {}}
    except Exception:
        return {"services": {}}


def _map_files_to_services(
    entries: list[FileEntry],
    compose_data: dict[str, Any],
    registry_data: dict[str, Any],
) -> dict[str, str]:
    """Assign files to owning service based on paths and build contexts."""
    file_map: dict[str, str] = {}

    # Build context prefixes from compose
    svc_prefixes: list[tuple[str, str]] = []
    for svc in compose_data.get("services", []):
        ctx = svc.get("build_context", "")
        if ctx and ctx != ".":
            svc_prefixes.append((ctx.rstrip("/") + "/", svc["name"]))

    # services/ directory mapping
    svc_prefixes.append(("services/", ""))

    # Sort by prefix length (longest first for specificity)
    svc_prefixes.sort(key=lambda x: len(x[0]), reverse=True)

    for e in entries:
        if not e.include or e.is_ghost:
            continue
        assigned = False
        for prefix, svc_name in svc_prefixes:
            if e.rel_path.startswith(prefix):
                if svc_name:
                    file_map[e.rel_path] = svc_name
                else:
                    # Infer from services/<name>/... pattern
                    parts = e.rel_path.split("/")
                    if len(parts) >= 2:
                        file_map[e.rel_path] = parts[1]
                assigned = True
                break
        if not assigned:
            if e.rel_path.startswith("src/"):
                file_map[e.rel_path] = "core"
            elif e.rel_path.startswith("docker/"):
                file_map[e.rel_path] = "docker-infra"
            elif e.rel_path.startswith("docs/"):
                file_map[e.rel_path] = "documentation"

    return file_map


_EVENT_PATTERNS = [
    (r'\.publish\s*\(\s*["\']([^"\']+)', "publish"),
    (r'\.subscribe\s*\(\s*["\']([^"\']+)', "subscribe"),
    (r'\.emit\s*\(\s*["\']([^"\']+)', "emit"),
    (r'event_bus\.fire\s*\(\s*["\']([^"\']+)', "fire"),
    (r'on_event\s*\(\s*["\']([^"\']+)', "on_event"),
    (r'EventType\.(\w+)', "event_type"),
]


def _detect_event_flows(
    entries: list[FileEntry], repo_root: Path
) -> list[dict[str, str]]:
    """Scan Python files for publish/subscribe/emit patterns."""
    flows: list[dict[str, str]] = []
    py_entries = [
        e for e in entries
        if e.rel_path.endswith(".py") and e.include and not e.is_ghost
    ]

    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern, action in _EVENT_PATTERNS:
            for match in re.finditer(pattern, content):
                flows.append({
                    "file": e.rel_path,
                    "action": action,
                    "event": match.group(1),
                })

    return flows


_API_ROUTE_PATTERNS = [
    (r'@(?:app|router)\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)',
     "decorator"),
    (r'\.add_api_route\s*\(\s*["\']([^"\']+)["\'].*methods=\[([^\]]+)',
     "add_route"),
]


def _detect_api_surface(
    entries: list[FileEntry], repo_root: Path
) -> list[dict[str, str]]:
    """Find FastAPI/Flask route decorators and build endpoint inventory."""
    endpoints: list[dict[str, str]] = []
    py_entries = [
        e for e in entries
        if e.rel_path.endswith(".py") and e.include and not e.is_ghost
    ]

    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in re.finditer(
            r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
            content, re.IGNORECASE,
        ):
            endpoints.append({
                "file": e.rel_path,
                "method": match.group(1).upper(),
                "path": match.group(2),
            })

    return endpoints


# ─── SECTION 5.8: Feature Intelligence ─────────────────────────────────


def enrich_with_feature_intelligence(
    entries: list[FileEntry], repo_root: Path
) -> dict[str, Any]:
    """Run feature intelligence: flags, CLI commands, MCP tools, completeness.
    Returns aggregate dict for report."""

    logger.info("  • Scanning for feature flags...")
    feature_flags = _scan_feature_flags(entries, repo_root)

    logger.info("  • Tracing CLI command tree...")
    cli_commands = _trace_cli_commands(entries, repo_root)

    logger.info("  • Inventorying MCP tools...")
    mcp_tools = _inventory_mcp_tools(entries, repo_root)

    logger.info("  • Scoring feature completeness...")
    completeness = _score_feature_completeness(
        feature_flags, cli_commands, mcp_tools, entries
    )

    return {
        "feature_flags": feature_flags[:100],
        "feature_flag_count": len(feature_flags),
        "cli_commands": cli_commands[:100],
        "cli_command_count": len(cli_commands),
        "mcp_tools": mcp_tools[:100],
        "mcp_tool_count": len(mcp_tools),
        "completeness_scores": completeness,
    }


def _scan_feature_flags(
    entries: list[FileEntry], repo_root: Path
) -> list[dict[str, Any]]:
    """Find ENABLE_*/FEATURE_* environment variables across the codebase."""
    flag_map: dict[str, dict[str, Any]] = {}

    # Scan Python files for os.getenv/os.environ
    py_entries = [
        e for e in entries
        if e.rel_path.endswith(".py") and e.include and not e.is_ghost
    ]
    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in re.finditer(
            r'(?:os\.(?:getenv|environ\.get))\s*\(\s*["\']'
            r'((?:ENABLE|FEATURE|DISABLE)_\w+)["\']'
            r'(?:\s*,\s*["\']?([^"\')\s,]+))?',
            content,
        ):
            flag_name = match.group(1)
            default_val = match.group(2) or ""
            if flag_name not in flag_map:
                flag_map[flag_name] = {
                    "name": flag_name,
                    "default": default_val,
                    "read_in": [],
                    "set_in": [],
                }
            flag_map[flag_name]["read_in"].append(e.rel_path)

    # Scan compose.yml for environment vars
    compose_path = repo_root / "compose.yml"
    if compose_path.exists():
        try:
            content = compose_path.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(
                r'((?:ENABLE|FEATURE|DISABLE)_\w+)\s*[:=]\s*(\S+)', content
            ):
                flag_name = match.group(1)
                val = match.group(2)
                if flag_name not in flag_map:
                    flag_map[flag_name] = {
                        "name": flag_name,
                        "default": val,
                        "read_in": [],
                        "set_in": [],
                    }
                flag_map[flag_name]["set_in"].append("compose.yml")
        except OSError:
            pass

    # Scan .env files
    for env_file in [".env", ".env.example", ".env.dev"]:
        env_path = repo_root / env_file
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8", errors="replace")
                for match in re.finditer(
                    r'^((?:ENABLE|FEATURE|DISABLE)_\w+)\s*=\s*(.+)$',
                    content, re.MULTILINE,
                ):
                    flag_name = match.group(1)
                    val = match.group(2).strip()
                    if flag_name not in flag_map:
                        flag_map[flag_name] = {
                            "name": flag_name,
                            "default": val,
                            "read_in": [],
                            "set_in": [],
                        }
                    flag_map[flag_name]["set_in"].append(env_file)
            except OSError:
                pass

    return sorted(flag_map.values(), key=lambda x: x["name"])


def _trace_cli_commands(
    entries: list[FileEntry], repo_root: Path
) -> list[dict[str, Any]]:
    """Trace click.group → click.command chains to build command tree."""
    commands: list[dict[str, Any]] = []
    py_entries = [
        e for e in entries
        if e.rel_path.endswith(".py") and e.include and not e.is_ghost
    ]

    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Find @click.group()
        for match in re.finditer(
            r'@click\.group\s*\(([^)]*)\)\s*\ndef\s+(\w+)',
            content, re.DOTALL,
        ):
            group_name = match.group(2)
            commands.append({
                "type": "group",
                "name": group_name,
                "file": e.rel_path,
            })

        # Find @click.command() or @<group>.command()
        for match in re.finditer(
            r'@(?:\w+\.)?command\s*\(([^)]*)\)\s*\ndef\s+(\w+)',
            content, re.DOTALL,
        ):
            cmd_name = match.group(2)
            commands.append({
                "type": "command",
                "name": cmd_name,
                "file": e.rel_path,
            })

    return commands


def _inventory_mcp_tools(
    entries: list[FileEntry], repo_root: Path
) -> list[dict[str, Any]]:
    """Find MCP tool registrations in services/ and docker/ directories."""
    tools: list[dict[str, Any]] = []
    py_entries = [
        e for e in entries
        if e.rel_path.endswith(".py") and e.include and not e.is_ghost
    ]

    for e in py_entries:
        fp = repo_root / e.rel_path
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Pattern 1: Tool("name", ...) or Tool(name="name", ...)
        for match in re.finditer(
            r'Tool\s*\(\s*(?:name\s*=\s*)?["\']([^"\']+)["\']',
            content,
        ):
            tools.append({
                "tool": match.group(1),
                "file": e.rel_path,
                "server": _infer_server_name(e.rel_path),
            })

        # Pattern 2: "name": "tool_name" inside list_tools returns
        if "list_tools" in content or "ListToolsResult" in content:
            for match in re.finditer(
                r'["\']name["\']\s*:\s*["\']([^"\']+)["\']',
                content,
            ):
                tool_name = match.group(1)
                if not any(t["tool"] == tool_name and t["file"] == e.rel_path
                           for t in tools):
                    tools.append({
                        "tool": tool_name,
                        "file": e.rel_path,
                        "server": _infer_server_name(e.rel_path),
                    })

    return tools


def _infer_server_name(rel_path: str) -> str:
    """Infer MCP server name from file path."""
    parts = rel_path.split("/")
    if "mcp-servers" in rel_path or "mcp-servers-source" in rel_path:
        for i, p in enumerate(parts):
            if p.startswith("mcp-servers") and i + 1 < len(parts):
                return parts[i + 1]
    if parts[0] == "services" and len(parts) >= 2:
        return parts[1]
    return Path(rel_path).stem


def _score_feature_completeness(
    flags: list[dict],
    cli_commands: list[dict],
    mcp_tools: list[dict],
    entries: list[FileEntry],
) -> dict[str, float]:
    """Score feature completeness per service/area."""
    # Group features by area
    areas: dict[str, dict[str, int]] = defaultdict(
        lambda: {"features": 0, "tested": 0, "documented": 0}
    )

    # CLI commands → group by file's parent directory
    for cmd in cli_commands:
        area = Path(cmd["file"]).parts[0] if "/" in cmd["file"] else "root"
        areas[area]["features"] += 1

    # MCP tools → group by server
    for tool in mcp_tools:
        areas[tool["server"]]["features"] += 1

    # Feature flags → count by first read_in file's area
    for flag in flags:
        read_files = flag.get("read_in", [])
        if read_files:
            area = Path(read_files[0]).parts[0]
            areas[area]["features"] += 1

    # Check test coverage per area
    tested_paths = {e.rel_path for e in entries if e.tested_by}
    doc_paths = {
        e.rel_path for e in entries
        if e.rel_path.startswith("docs/") and e.include
    }

    scores: dict[str, float] = {}
    for area, counts in areas.items():
        if counts["features"] == 0:
            continue
        # Simple heuristic: base score from feature count,
        # bonus for tests and docs
        feature_count = counts["features"]
        has_tests = any(
            e.tested_by for e in entries
            if e.rel_path.startswith(area + "/")
        )
        has_docs = any(
            d.startswith(f"docs/") and area.replace("_", "-") in d
            for d in (e.rel_path for e in entries if e.rel_path.startswith("docs/"))
        )
        score = 0.4  # base
        if has_tests:
            score += 0.3
        if has_docs:
            score += 0.3
        scores[area] = round(score, 2)

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:20])


# ─── SECTION 5.9: Extraction Artifact Generation ──────────────────────


def generate_extraction_artifacts(
    entries: list[FileEntry],
    code_intel: dict[str, Any],
    arch_intel: dict[str, Any],
    feature_intel: dict[str, Any],
    config: PrescanConfig,
) -> list[Path]:
    """Generate extraction-ready artifact files for the extractor to consume."""
    artifacts: list[Path] = []

    # 1. Skip list: orphans + duplicates
    skip_files: dict[str, str] = {}
    for e in entries:
        if e.is_orphan and e.include:
            skip_files[e.rel_path] = "orphan (imported by nothing, not entry point)"
        if e.is_duplicate and e.include:
            skip_files[e.rel_path] = f"duplicate of group {e.duplicate_group_id}"

    skip_data = {
        "generated_by": f"doc_audit_prescan v{SCRIPT_VERSION}",
        "skip_files": list(skip_files.keys()),
        "skip_reason": skip_files,
        "total_skippable": len(skip_files),
        "estimated_savings_pct": round(
            len(skip_files) / max(1, len([e for e in entries if e.include])) * 100, 1
        ),
    }
    skip_path = config.output_dir / "extraction_skip_list.json"
    skip_path.write_text(json.dumps(skip_data, indent=2) + "\n")
    artifacts.append(skip_path)

    # 2. Routing hints: complex/hub → premium, simple/tested → economy
    premium: dict[str, str] = {}
    economy: dict[str, str] = {}
    for e in entries:
        if not e.include or e.is_ghost or not e.rel_path.endswith(".py"):
            continue
        reasons = []
        if e.imported_by_count >= 5:
            reasons.append(f"hub (imported by {e.imported_by_count} files)")
        if e.complexity_score > 0.7:
            reasons.append(f"high complexity ({e.complexity_score:.2f})")
        if e.is_entry_point:
            reasons.append("entry point")
        if reasons:
            premium[e.rel_path] = " + ".join(reasons)
        elif e.complexity_score < 0.3 and e.tested_by:
            economy[e.rel_path] = f"low complexity ({e.complexity_score:.2f}), tested"

    routing_data = {
        "generated_by": f"doc_audit_prescan v{SCRIPT_VERSION}",
        "premium_tier": list(premium.keys()),
        "premium_reason": premium,
        "premium_count": len(premium),
        "economy_tier": list(economy.keys()),
        "economy_reason": economy,
        "economy_count": len(economy),
    }
    routing_path = config.output_dir / "extraction_routing_hints.json"
    routing_path.write_text(json.dumps(routing_data, indent=2) + "\n")
    artifacts.append(routing_path)

    # 3. Partition hints: service-based groupings
    partition_data = {
        "generated_by": f"doc_audit_prescan v{SCRIPT_VERSION}",
        "service_partitions": arch_intel.get("service_partitions", {}),
        "service_count": len(arch_intel.get("service_partitions", {})),
        "suggestion": "Group files by owning service for coherent extraction",
    }
    partition_path = config.output_dir / "extraction_partition_hints.json"
    partition_path.write_text(json.dumps(partition_data, indent=2) + "\n")
    artifacts.append(partition_path)

    # Mirror to extractor 00_inputs
    extractor_inputs = config.repo_root / "services/repo-truth-extractor/runs/00_inputs"
    if extractor_inputs.is_dir():
        for artifact in artifacts:
            dest = extractor_inputs / artifact.name.upper()
            dest.write_text(artifact.read_text())
            logger.info(f"  🔗 Mirrored: {dest.name}")

    return artifacts


def build_intelligence_report(
    entries: list[FileEntry],
    co_change_groups: list[dict],
    config: PrescanConfig,
    meta: RunMetadata,
    *,
    code_intel: dict[str, Any] | None = None,
    arch_intel: dict[str, Any] | None = None,
    feature_intel: dict[str, Any] | None = None,
) -> Path:
    """
    Aggregate all intelligence into prescan_intelligence.json.
    Acts as the extraction bridge for run_extraction_v5.py.
    """
    included = [e for e in entries if e.include and not e.is_ghost]
    ghosts = [e for e in entries if e.is_ghost]

    # Duplicate summary
    dup_groups: dict[str, list[str]] = {}
    for e in included:
        if e.duplicate_group_id:
            dup_groups.setdefault(e.duplicate_group_id, []).append(e.rel_path)

    # Version chain summary
    chains: dict[str, list[dict]] = {}
    for e in entries:
        if e.version_chain_id:
            chains.setdefault(e.version_chain_id, []).append(
                {
                    "path": e.rel_path,
                    "ordinal": e.version_ordinal,
                    "is_latest": e.is_latest_version,
                    "commit_count": e.commit_count,
                    "last_commit_date": e.last_commit_date,
                }
            )

    # Feature gap summary
    planned_features = {
        "proposed_adrs": [e.rel_path for e in included if e.is_proposed_adr],
        "stub_files": [e.rel_path for e in included if e.has_stub_methods],
        "todo_files": [e.rel_path for e in included if e.has_todo_markers],
        "draft_docs": [e.rel_path for e in included if e.is_draft_doc],
    }

    # Lifecycle distribution
    lifecycle_counts: dict[str, int] = {}
    for e in included:
        if e.lifecycle_stage:
            lifecycle_counts[e.lifecycle_stage] = (
                lifecycle_counts.get(e.lifecycle_stage, 0) + 1
            )

    # Corpus health score (0-100)
    total = len(included) or 1
    dup_ratio = len([e for e in included if e.is_duplicate]) / total
    frozen_ratio = lifecycle_counts.get("frozen", 0) / total
    compression_potential = sum(max(0, len(v) - 1) for v in chains.values())
    ghost_bonus = min(len(ghosts) * 2, 10)
    corpus_health = max(0, int(80 - dup_ratio * 20 - frozen_ratio * 10 + ghost_bonus))

    report = {
        "schema_version": "3.0",
        "generated_at": meta.timestamp,
        "git_sha": meta.git_sha,
        "git_branch": meta.git_branch,
        "corpus_summary": {
            "included_files": len(included),
            "ghost_files": len(ghosts),
            "corpus_health_score": corpus_health,
            "total_size_bytes": sum(e.size_bytes for e in included),
        },
        "duplicate_groups": dup_groups,
        "version_chains": {
            cid: sorted(members, key=lambda x: x["ordinal"])
            for cid, members in chains.items()
        },
        "version_chain_count": len(chains),
        "compression_potential_files": compression_potential,
        "planned_features": planned_features,
        "lifecycle_distribution": lifecycle_counts,
        "co_change_groups": co_change_groups[:20],
        "ghost_files": [
            {
                "path": g.rel_path,
                "deleted_date": g.deleted_date,
                "deleted_at_sha": g.deleted_at_sha,
            }
            for g in ghosts
        ],
        "extraction_hints": {
            "skip_duplicates": [e.rel_path for e in included if e.is_duplicate],
            "version_chain_compress": [
                {
                    "chain_id": cid,
                    "latest": next(
                        (m["path"] for m in members if m["is_latest"]), None
                    ),
                    "superseded": [m["path"] for m in members if not m["is_latest"]],
                }
                for cid, members in chains.items()
            ],
            "planned_feature_files": (
                planned_features["proposed_adrs"] + planned_features["stub_files"]
            ),
            "high_churn_files": [
                e.rel_path
                for e in sorted(included, key=lambda x: x.churn_score, reverse=True)
                if e.churn_score > 1.0
            ][:20],
        },
    }

    # ── Merge code/arch/feature intelligence if available ──
    if code_intel:
        report["code_intelligence"] = code_intel
        hints = report["extraction_hints"]
        hints["orphan_files"] = code_intel.get("orphan_files", [])[:30]
        hints["hub_files"] = [h["path"] for h in code_intel.get("hub_files", [])]
        hints["complexity_hotspots"] = [
            h["path"] for h in code_intel.get("complexity_hotspots", [])
        ]
        hints["untested_entry_points"] = code_intel.get("untested_entry_points", [])

    if arch_intel:
        report["architecture"] = arch_intel
        hints = report["extraction_hints"]
        hints["service_partitions"] = arch_intel.get("service_partitions", {})

    if feature_intel:
        report["features"] = feature_intel

    out_path = config.output_dir / "prescan_intelligence.json"
    out_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )

    # Mirror to extractor 00_inputs if it exists
    extractor_inputs = config.repo_root / "services/repo-truth-extractor/runs/00_inputs"
    if extractor_inputs.is_dir():
        dest = extractor_inputs / "PRESCAN_INTELLIGENCE.json"
        dest.write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        logger.info(f"🔗 Extraction bridge: {dest}")

    return out_path


# ─── SECTION 6: Manifest Builder ────────────────────────────────────


def _get_git_info(repo_root: Path) -> tuple[str, str]:
    """Return (sha, branch) from git."""
    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        sha = "UNKNOWN"
    try:
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
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
        )
        + "\n"
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
        stats.by_directory[e.directory_class] = (
            stats.by_directory.get(e.directory_class, 0) + 1
        )

    (config.output_dir / "corpus_stats.json").write_text(
        json.dumps(asdict(stats), indent=2, sort_keys=True) + "\n"
    )

    # ── run_metadata.json ──
    sha, branch = _get_git_info(config.repo_root)
    config_str = json.dumps(
        asdict(config) if hasattr(config, "__dataclass_fields__") else str(config),
        sort_keys=True,
        default=str,
    )
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
        preview = preview.encode("utf-8")[:MAX_PREVIEW_BYTES].decode(
            "utf-8", errors="replace"
        )
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
        "# Documentation Authority Audit Corpus",
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
            "❌ 'openai' package not installed.\n" "   pip install openai>=1.0.0"
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
                "prompt_tokens": (
                    response.usage.prompt_tokens if response.usage else None
                ),
                "completion_tokens": (
                    response.usage.completion_tokens if response.usage else None
                ),
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


def _print_intelligence_report(intel_path: Path) -> None:
    """Render prescan_intelligence.json as a stunning Rich terminal display."""
    import json as _json

    try:
        with open(intel_path) as _f:
            intel = _json.load(_f)
    except (OSError, ValueError):
        return

    try:
        from rich.box import ROUNDED, HEAVY
        from rich.columns import Columns
        from rich.console import Console as RichConsole
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        rcon = RichConsole()
        summary = intel.get("corpus_summary", {})
        lifecycle = intel.get("lifecycle_distribution", {})
        planned = intel.get("planned_features", {})
        hints = intel.get("extraction_hints", {})
        dup_groups = intel.get("duplicate_groups", {})
        co_groups = intel.get("co_change_groups", [])

        health = summary.get("corpus_health_score", 0)
        total_files = summary.get("included_files", 0)
        ghost_count = summary.get("ghost_files", 0)
        git_branch = intel.get("git_branch", "?")
        git_sha = (intel.get("git_sha") or "?")[:10]
        chain_count = intel.get("version_chain_count", 0)
        compress_n = intel.get("compression_potential_files", 0)
        skip_n = len(hints.get("skip_duplicates", []))
        dup_n = sum(len(v) - 1 for v in dup_groups.values())
        hichurn_n = len(hints.get("high_churn_files", []))
        adr_n = len(planned.get("proposed_adrs", []))
        stub_n = len(planned.get("stub_files", []))
        todo_n = len(planned.get("todo_files", []))
        draft_n = len(planned.get("draft_docs", []))

        # ── health gauge ─────────────────────────────────────────────────
        if health >= 75:
            bar_color, hlabel = "bright_green", "HEALTHY"
        elif health >= 50:
            bar_color, hlabel = "yellow", "FAIR"
        else:
            bar_color, hlabel = "red", "NEEDS ATTENTION"
        filled = round(health / 5)
        gauge = "█" * filled + "░" * (20 - filled)

        gen_ts = intel.get("generated_at", "")[:19].replace("T", "  ")
        header = (
            f"\n  [{bar_color}]{gauge}[/{bar_color}]"
            f"  [bold {bar_color}]{health}/100  {hlabel}[/bold {bar_color}]\n"
            f"  [dim]git: {git_sha}  •  branch: {git_branch}  •  {gen_ts}[/dim]\n"
        )
        rcon.print()
        rcon.print(Panel(
            header,
            title="[bold white]🧠  PRE-EXTRACTION INTELLIGENCE REPORT[/bold white]",
            border_style="bright_cyan",
            box=HEAVY,
            padding=(0, 2),
        ))

        # ── side-by-side panels ───────────────────────────────────────────
        left = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        left.add_column("Label", style="dim", min_width=26)
        left.add_column("Value", justify="right")

        def _nfmt(n: int, warn: int = 0) -> str:
            if warn and n > warn:
                return f"[bold yellow]{n:,}[/bold yellow]"
            return f"[bold]{n:,}[/bold]"

        left.add_row("Total included files",         _nfmt(total_files))
        left.add_row("Ghost files  👻",              _nfmt(ghost_count))
        left.add_row("Redundant files (dupes)",       _nfmt(dup_n, warn=50))
        left.add_row("Skip candidates",               _nfmt(skip_n, warn=100))
        left.add_row("Version chains",                _nfmt(chain_count))
        left.add_row("Compressible version files",    _nfmt(compress_n))
        left.add_row("High-churn files  🔥",         _nfmt(hichurn_n))
        left.add_row("Co-change groups",              _nfmt(len(co_groups)))

        right = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        right.add_column("Label", style="dim", min_width=24)
        right.add_column("Value", justify="right")

        def _pfmt(n: int, icon: str) -> str:
            c = "magenta" if n > 0 else "dim"
            return f"[{c}]{icon}  {n:,}[/{c}]"

        right.add_row("Proposed ADRs",          _pfmt(adr_n,   "📋"))
        right.add_row("Stub implementations",   _pfmt(stub_n,  "🔧"))
        right.add_row("Files with TODOs",       _pfmt(todo_n,  "📌"))
        right.add_row("Draft / proposed docs",  _pfmt(draft_n, "📝"))
        total_planned = adr_n + stub_n + draft_n
        right.add_section()
        fc = "magenta" if total_planned > 0 else "dim"
        right.add_row(
            "[bold]Total planned work items[/bold]",
            f"[bold {fc}]{total_planned:,}[/bold {fc}]",
        )

        rcon.print(Columns([
            Panel(left,  title="[bold cyan]📦 Corpus Profile[/bold cyan]",
                  border_style="cyan", box=ROUNDED, padding=(0, 1)),
            Panel(right, title="[bold magenta]🗺  Planned Features[/bold magenta]",
                  border_style="magenta", box=ROUNDED, padding=(0, 1)),
        ], equal=True, expand=True))

        # ── lifecycle bar chart ───────────────────────────────────────────
        if lifecycle:
            _LC_META = {
                "fresh":   ("🌱", "bright_green"),
                "active":  ("🔥", "green"),
                "stale":   ("🌤", "yellow"),
                "frozen":  ("🧊", "blue"),
                "unknown": ("❓", "dim"),
            }
            lc_table = Table(
                box=ROUNDED, border_style="dim cyan",
                title="[bold]📅  File Lifecycle Distribution[/bold]",
                padding=(0, 1),
            )
            lc_table.add_column("Stage",   min_width=10)
            lc_table.add_column("Bar",     min_width=28)
            lc_table.add_column("Files",   justify="right", min_width=6)
            lc_table.add_column("%",       justify="right", min_width=5)

            lc_total = sum(lifecycle.values()) or 1
            _order = ["fresh", "active", "stale", "frozen", "unknown"]
            for stage in sorted(lifecycle, key=lambda s: _order.index(s) if s in _order else 99):
                count = lifecycle[stage]
                icon, color = _LC_META.get(stage, ("•", "white"))
                frac = count / lc_total
                bf = round(frac * 26)
                bar = (
                    f"[{color}]" + "█" * bf + "[/]"
                    + "[dim]" + "░" * (26 - bf) + "[/dim]"
                )
                lc_table.add_row(
                    f"{icon}  [{color}]{stage}[/{color}]",
                    bar, f"{count:,}", f"[dim]{frac*100:.0f}%[/dim]",
                )
            rcon.print(lc_table)

        # ── extraction hints ──────────────────────────────────────────────
        if skip_n or compress_n or ghost_count or total_planned or hichurn_n:
            token_est = min(
                int((skip_n / max(total_files, 1)) * 100 * 0.6
                    + (compress_n / max(total_files, 1)) * 100 * 0.3), 65
            )
            _SAVLABELS = [
                (50, "bold green", "🚀 MAJOR SAVINGS"),
                (25, "green",      "💚 GOOD SAVINGS"),
                (10, "yellow",     "💛 MODERATE"),
                (0,  "dim",        "—  MINIMAL"),
            ]
            s_color, s_label = next(
                (c, l) for t, c, l in _SAVLABELS if token_est >= t
            )
            lines = []
            if skip_n:
                lines.append(
                    f"  [bold yellow]💰 {skip_n:,} files SKIPPED[/bold yellow]"
                    f" [dim](exact duplicates — zero extraction cost)[/dim]"
                )
            if compress_n:
                lines.append(
                    f"  [bold cyan]🗜  {compress_n:,} files COMPRESSED[/bold cyan]"
                    f" [dim](version chains → evolution summaries)[/dim]"
                )
            if ghost_count:
                lines.append(
                    f"  [dim]👻 {ghost_count} ghost files[/dim]"
                    f" [dim](run --passes discover to assess recovery value)[/dim]"
                )
            if total_planned:
                lines.append(
                    f"  [bold magenta]📋 {total_planned} planned features[/bold magenta]"
                    f" [dim]→ Phase X + T priority routing[/dim]"
                )
            if hichurn_n:
                lines.append(
                    f"  [bold]🔥 {hichurn_n} high-churn files[/bold]"
                    f" [dim]→ premium model routing recommended[/dim]"
                )
            lines += [
                "",
                f"  Estimated token reduction:  "
                f"[bold {s_color}]{token_est}%  {s_label}[/bold {s_color}]",
            ]
            rcon.print(Panel(
                "\n".join(lines),
                title="[bold green]💡  Extraction Hints[/bold green]",
                border_style="green", box=ROUNDED, padding=(0, 1),
            ))

        # ── co-change groups ──────────────────────────────────────────────
        if co_groups:
            cg_table = Table(
                box=ROUNDED, border_style="dim",
                title="[bold]🔗  Top Co-Change Groups[/bold]",
                padding=(0, 1), show_lines=True,
            )
            cg_table.add_column("Commits", justify="right", min_width=7)
            cg_table.add_column("Files in Group", min_width=48)
            for group in co_groups[:6]:
                flines = "\n".join(
                    f"[dim cyan]{fp}[/dim cyan]"
                    for fp in sorted(group["files"])[:4]
                )
                if len(group["files"]) > 4:
                    flines += f"\n[dim]  … +{len(group['files']) - 4} more[/dim]"
                cg_table.add_row(f"[bold]{group['commit_count']}[/bold]", flines)
            rcon.print(cg_table)

        # ── code intelligence ─────────────────────────────────────────────
        code_intel = intel.get("code_intelligence", {})
        if code_intel:
            from rich.console import Group as RichGroup

            ci_tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
            ci_tbl.add_column("Metric", style="dim", min_width=28)
            ci_tbl.add_column("Value", justify="right")

            ci_tbl.add_row("Python files analysed", _nfmt(code_intel.get("total_python_files", 0)))
            ci_tbl.add_row("Entry points", _nfmt(code_intel.get("entry_point_count", 0)))
            ci_tbl.add_row("Orphan files", _nfmt(code_intel.get("orphan_count", 0), warn=10))
            ci_tbl.add_row("Hub files (≥5 importers)", _nfmt(code_intel.get("hub_count", 0)))
            ci_tbl.add_row("Circular imports", _nfmt(code_intel.get("circular_count", len(code_intel.get("circular_imports", []))), warn=1))

            cov_ratio = code_intel.get("test_coverage_ratio", 0)
            cov_pct = int(cov_ratio * 100)
            cv_c = "green" if cov_pct >= 60 else ("yellow" if cov_pct >= 30 else "red")
            ci_tbl.add_row("Test coverage (by file)", f"[{cv_c}]{cov_pct}%[/{cv_c}]")

            avg_doc = code_intel.get("avg_docstring_coverage", 0)
            dc = "green" if avg_doc >= 0.6 else ("yellow" if avg_doc >= 0.3 else "red")
            ci_tbl.add_row("Avg docstring coverage", f"[{dc}]{avg_doc:.0%}[/{dc}]")

            parts = [ci_tbl]

            hubs = code_intel.get("hub_files", [])[:5]
            if hubs:
                parts.append(Text(""))
                parts.append(Text("🔗 Top Import Hubs", style="bold"))
                for h in hubs:
                    parts.append(Text(f"  {h['path']}  ← {h['imported_by']} importers", style="cyan"))

            hotspots = code_intel.get("complexity_hotspots", [])[:5]
            if hotspots:
                parts.append(Text(""))
                parts.append(Text("🔥 Complexity Hotspots", style="bold"))
                for h in hotspots:
                    parts.append(Text(f"  {h['path']}  (score: {h.get('score', 0):.2f})", style="yellow"))

            rcon.print(Panel(
                RichGroup(*parts),
                title="[bold blue]💻 Code Intelligence[/bold blue]",
                border_style="blue", box=ROUNDED, padding=(0, 1),
            ))

        # ── architecture intelligence ─────────────────────────────────────
        arch_data = intel.get("architecture", {})
        if arch_data:
            from rich.console import Group as RichGroup

            ai_tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
            ai_tbl.add_column("Metric", style="dim", min_width=28)
            ai_tbl.add_column("Value", justify="right")

            ai_tbl.add_row("Services", _nfmt(arch_data.get("service_count", 0)))
            ai_tbl.add_row("API endpoints", _nfmt(arch_data.get("api_endpoint_count", 0)))
            ai_tbl.add_row("Event flows", _nfmt(arch_data.get("event_flow_count", 0)))
            ai_tbl.add_row("Files mapped to services", _nfmt(arch_data.get("mapped_file_count", arch_data.get("file_service_map_count", 0))))

            svc_list = arch_data.get("services", [])
            if svc_list and isinstance(svc_list, list):
                svc_tbl = Table(box=ROUNDED, border_style="dim", padding=(0, 1))
                svc_tbl.add_column("Service", style="bold cyan", min_width=22)
                svc_tbl.add_column("Ports", justify="right", min_width=10)
                partitions = arch_data.get("service_partitions", {})
                for svc_item in sorted(svc_list, key=lambda s: s.get("name", ""))[:12]:
                    sn = svc_item.get("name", "?")
                    raw_ports = svc_item.get("ports", [])
                    ports = ", ".join(str(p).split(":")[-1] for p in raw_ports) or "—"
                    fc = len(partitions.get(sn, []))
                    svc_tbl.add_row(sn, f"{ports}  ({fc} files)")

            parts = [ai_tbl]
            if svc_list:
                parts.append(Text(""))
                parts.append(svc_tbl)

            rcon.print(Panel(
                RichGroup(*parts),
                title="[bold green]🏗️  Architecture Intelligence[/bold green]",
                border_style="green", box=ROUNDED, padding=(0, 1),
            ))

        # ── feature intelligence ──────────────────────────────────────────
        feat_data = intel.get("features", {})
        if feat_data:
            from rich.console import Group as RichGroup

            fi_tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
            fi_tbl.add_column("Metric", style="dim", min_width=28)
            fi_tbl.add_column("Value", justify="right")

            fi_tbl.add_row("Feature flags", _nfmt(feat_data.get("feature_flag_count", 0)))
            fi_tbl.add_row("CLI commands", _nfmt(feat_data.get("cli_command_count", 0)))
            fi_tbl.add_row("MCP tools", _nfmt(feat_data.get("mcp_tool_count", 0)))
            fi_tbl.add_row("MCP servers", _nfmt(feat_data.get("mcp_server_count", 0)))

            avg_comp = feat_data.get("avg_completeness", 0)
            cc = "green" if avg_comp >= 0.7 else ("yellow" if avg_comp >= 0.4 else "red")
            fi_tbl.add_row("Avg completeness", f"[{cc}]{avg_comp:.0%}[/{cc}]")

            flags = feat_data.get("feature_flags", [])
            if flags:
                fl_tbl = Table(box=ROUNDED, border_style="dim", padding=(0, 1))
                fl_tbl.add_column("Flag", style="bold yellow", min_width=28)
                fl_tbl.add_column("Default", justify="center", min_width=8)
                for fl in flags[:10]:
                    fl_tbl.add_row(fl.get("name", "?"), str(fl.get("default", "?")))

            parts = [fi_tbl]
            if flags:
                parts.append(Text(""))
                parts.append(fl_tbl)

            mcp_servers = feat_data.get("mcp_servers", [])
            if mcp_servers:
                parts.append(Text(""))
                parts.append(Text("🔌 MCP Servers", style="bold"))
                for srv in mcp_servers[:8]:
                    parts.append(Text(f"  {srv.get('name', '?')}  ({srv.get('tool_count', 0)} tools)", style="cyan"))

            rcon.print(Panel(
                RichGroup(*parts),
                title="[bold yellow]🎯 Feature Intelligence[/bold yellow]",
                border_style="yellow", box=ROUNDED, padding=(0, 1),
            ))

        rcon.print()

    except ImportError:
        # plain-text minimal fallback
        summary = intel.get("corpus_summary", {})
        health = summary.get("corpus_health_score", 0)
        print(f"\n🧠 Intelligence Report  Health: {health}/100")
        dup_n = sum(len(v) - 1 for v in intel.get("duplicate_groups", {}).values())
        print(f"  Duplicates: {dup_n}  Chains: {intel.get('version_chain_count', 0)}")
        print(f"  Ghosts: {summary.get('ghost_files', 0)}")


def _print_summary(stats: CorpusStats, config: PrescanConfig) -> None:
    """Print ADHD-friendly summary — uses Rich if available, else plain text."""
    try:
        from rich.box import ROUNDED, HEAVY
        from rich.columns import Columns
        from rich.console import Console as RichConsole
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        rcon = RichConsole()

        # ── header ────────────────────────────────────────────────────────
        total_mb = stats.total_included_size / (1024 * 1024)
        limit_mb = config.max_corpus_size / (1024 * 1024)
        ok = stats.total_included_size <= config.max_corpus_size
        status_line = (
            f"  [bold green]✅  {stats.included_count:,} files · {total_mb:.1f} MB[/bold green]"
            f"  [dim](limit {limit_mb:.0f} MB)[/dim]"
            if ok else
            f"  [bold red]⚠️  {stats.included_count:,} files · {total_mb:.1f} MB[/bold red]"
            f"  [dim](limit {limit_mb:.0f} MB — EXCEEDED)[/dim]"
        )
        rcon.print(
            Panel(
                f"{status_line}\n  [dim]Excluded: {stats.excluded_count:,} files (noise/binaries/vendor)[/dim]",
                title="[bold white]📋  Corpus Classification Summary[/bold white]",
                border_style="bright_cyan",
                box=HEAVY,
                padding=(0, 2),
            )
        )

        # ── per-class table ───────────────────────────────────────────────
        CLASS_ICONS = {
            "canonical":  ("📘", "bright_blue"),
            "reference":  ("📗", "green"),
            "support":    ("📙", "yellow"),
            "ephemeral":  ("📄", "dim"),
            "noise":      ("🗑",  "dim red"),
            "code":       ("🐍", "cyan"),
            "config":     ("⚙️",  "magenta"),
            "ghost":      ("👻", "dim"),
        }
        cls_table = Table(
            box=ROUNDED,
            border_style="dim cyan",
            padding=(0, 1),
            show_header=True,
        )
        cls_table.add_column("Class",   min_width=12)
        cls_table.add_column("Bar",     min_width=24)
        cls_table.add_column("Files",   justify="right", min_width=6)
        cls_table.add_column("Size",    justify="right", min_width=9)

        max_count = max(
            (v["count"] for v in stats.by_class.values() if v["count"] > 0),
            default=1,
        )
        for cls in AUTHORITY_CLASSES:
            info = stats.by_class.get(cls, {"count": 0, "total_size": 0})
            if not info["count"]:
                continue
            icon, color = CLASS_ICONS.get(cls, ("•", "white"))
            frac = info["count"] / max(max_count, 1)
            filled = max(1, round(frac * 22))
            bar = f"[{color}]" + "█" * filled + "[/]" + "[dim]" + "░" * (22 - filled) + "[/dim]"
            cls_table.add_row(
                f"{icon}  [{color}]{cls}[/{color}]",
                bar,
                f"{info['count']:,}",
                f"[dim]{_human_size(info['total_size'])}[/dim]",
            )
        rcon.print(cls_table)

    except ImportError:
        # ── plain-text fallback ───────────────────────────────────────────
        print("\n📋 Classification Summary:")
        for cls in AUTHORITY_CLASSES:
            info = stats.by_class.get(cls, {"count": 0, "total_size": 0})
            if info["count"] > 0:
                print(f"  {cls:12s}: {info['count']:4d} files ({_human_size(info['total_size'])})")
        print(
            f"\n📦 Total corpus: {stats.included_count} files, "
            f"{_human_size(stats.total_included_size)}"
        )
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
        "mode",
        choices=["dry-run", "direct", "handoff"],
        help="Execution mode: dry-run (manifests only), direct (call Grok), handoff (write bundle)",
    )
    parser.add_argument("--repo-root", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--max-file-size", type=str, default=None)
    parser.add_argument("--max-corpus-size", type=str, default=None)
    parser.add_argument(
        "--include", action="append", default=[], help="Additional include glob"
    )
    parser.add_argument(
        "--exclude", action="append", default=[], help="Additional exclude glob"
    )
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--provider", type=str, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--force", action="store_true", help="Override corpus size limit"
    )
    parser.add_argument(
        "--git-passes",
        action="store_true",
        help="Enable git intelligence: history, ghost recovery, dedup, "
        "version chains, feature gaps, co-change groups",
    )
    parser.add_argument(
        "--max-ghosts",
        type=int,
        default=50,
        help="Max deleted files to recover as ghost entries (default: 50)",
    )
    parser.add_argument(
        "--skip-feature-gaps",
        action="store_true",
        help="Skip per-file TODO/stub content scan (faster for large repos)",
    )
    parser.add_argument(
        "--code-passes",
        action="store_true",
        help="Run code intelligence: AST analysis, import graph, entry points, "
        "test mapping, complexity scoring",
    )
    parser.add_argument(
        "--arch-passes",
        action="store_true",
        help="Run architecture intelligence: compose topology, service registry, "
        "event flows, API surface",
    )
    parser.add_argument(
        "--feature-passes",
        action="store_true",
        help="Run feature intelligence: feature flags, CLI commands, "
        "MCP tool inventory, completeness scoring",
    )
    parser.add_argument(
        "--full-passes",
        action="store_true",
        help="Run ALL intelligence passes (git + code + arch + features)",
    )

    args = parser.parse_args()

    # --full-passes enables everything
    if args.full_passes:
        args.git_passes = True
        args.code_passes = True
        args.arch_passes = True
        args.feature_passes = True

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

    # Git intelligence passes (opt-in via --git-passes)
    co_change_groups: list[dict] = []
    if args.git_passes:
        logger.info("🔍 Running git intelligence passes...")

        logger.info("  • Enriching with git history...")
        enrich_with_git(entries, config.repo_root)

        logger.info("  • Recovering ghost files...")
        existing_paths = {e.rel_path for e in entries}
        ghosts = recover_ghost_files(
            existing_paths, config.repo_root, max_ghosts=args.max_ghosts
        )
        if ghosts:
            entries.extend(ghosts)
            logger.info(f"    👻 Recovered {len(ghosts)} ghost files")

        logger.info("  • Detecting exact duplicates...")
        n_dup_groups = detect_duplicates(entries)
        if n_dup_groups:
            logger.info(f"    Found {n_dup_groups} duplicate groups")

        logger.info("  • Detecting version chains...")
        n_chains = detect_version_chains(entries)
        if n_chains:
            logger.info(f"    Found {n_chains} version chains")

        if not args.skip_feature_gaps:
            logger.info("  • Scanning for feature gaps...")
            scan_feature_gaps(entries, config.repo_root)
            gaps = sum(
                1
                for e in entries
                if e.has_todo_markers
                or e.has_stub_methods
                or e.is_draft_doc
                or e.is_proposed_adr
            )
            if gaps:
                logger.info(f"    Found {gaps} files with feature gaps")

        logger.info("  • Building co-change groups...")
        co_change_groups = detect_co_change_groups(entries, config.repo_root)
        if co_change_groups:
            logger.info(f"    Found {len(co_change_groups)} co-change groups")

    # Code intelligence passes (opt-in via --code-passes or --full-passes)
    code_intel: dict[str, Any] | None = None
    if args.code_passes:
        logger.info("💻 Running code intelligence passes...")
        code_intel = enrich_with_code_intelligence(entries, config.repo_root)
        logger.info(
            f"   ✓ {code_intel['total_python_files']} Python files analysed, "
            f"{code_intel['entry_point_count']} entry points, "
            f"{code_intel['orphan_count']} orphans, "
            f"{code_intel['hub_count']} hubs"
        )

    # Architecture intelligence passes (opt-in via --arch-passes or --full-passes)
    arch_intel: dict[str, Any] | None = None
    if args.arch_passes:
        logger.info("🏗️  Running architecture intelligence passes...")
        arch_intel = enrich_with_arch_intelligence(entries, config.repo_root)
        logger.info(
            f"   ✓ {arch_intel['service_count']} services, "
            f"{arch_intel['api_endpoint_count']} API endpoints, "
            f"{arch_intel['event_flow_count']} event flows"
        )

    # Feature intelligence passes (opt-in via --feature-passes or --full-passes)
    feature_intel: dict[str, Any] | None = None
    if args.feature_passes:
        logger.info("🎯 Running feature intelligence passes...")
        feature_intel = enrich_with_feature_intelligence(entries, config.repo_root)
        logger.info(
            f"   ✓ {feature_intel['feature_flag_count']} feature flags, "
            f"{feature_intel['cli_command_count']} CLI commands, "
            f"{feature_intel['mcp_tool_count']} MCP tools"
        )

    # Build manifests (always, for all modes)
    stats, meta = build_manifests(entries, config, mode)
    _print_summary(stats, config)
    logger.info(f"\n📄 Manifests written to {config.output_dir}/")

    # Intelligence report (any intelligence passes)
    has_any_intel = args.git_passes or args.code_passes or args.arch_passes or args.feature_passes
    if has_any_intel:
        intel_path = build_intelligence_report(
            entries, co_change_groups, config, meta,
            code_intel=code_intel,
            arch_intel=arch_intel,
            feature_intel=feature_intel,
        )
        logger.info(f"🧠 Intelligence report: {intel_path}")

        # Generate extraction artifacts if code or arch intelligence available
        if code_intel or arch_intel:
            logger.info("📋 Generating extraction artifacts...")
            artifacts = generate_extraction_artifacts(
                entries,
                code_intel or {},
                arch_intel or {},
                feature_intel or {},
                config,
            )
            logger.info(f"   ✓ {len(artifacts)} extraction artifact(s) written")

        _print_intelligence_report(intel_path)

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
    logger.info(
        f"   Payload: {payload_path} ({_human_size(payload_path.stat().st_size)})"
    )

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
