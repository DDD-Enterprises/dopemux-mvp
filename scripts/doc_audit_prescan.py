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
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

logger = logging.getLogger(__name__)

# ─── SECTION 1: Constants ───────────────────────────────────────────

SCRIPT_VERSION = "2.0.0"

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


def build_intelligence_report(
    entries: list[FileEntry],
    co_change_groups: list[dict],
    config: PrescanConfig,
    meta: RunMetadata,
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
        "schema_version": "2.0",
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

    # Build manifests (always, for all modes)
    stats, meta = build_manifests(entries, config, mode)
    _print_summary(stats, config)
    logger.info(f"\n📄 Manifests written to {config.output_dir}/")

    # Intelligence report (git passes only)
    if args.git_passes:
        intel_path = build_intelligence_report(entries, co_change_groups, config, meta)
        logger.info(f"🧠 Intelligence report: {intel_path}")
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
