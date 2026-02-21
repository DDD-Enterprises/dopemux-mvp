from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .hashing import sha256_bytes

REPO_FINGERPRINT_FILENAME = "REPO_FINGERPRINT.json"
BUILD_SURFACE_FILENAME = "BUILD_SURFACE.json"
ENTRYPOINT_CANDIDATES_FILENAME = "ENTRYPOINT_CANDIDATES.json"
DEPENDENCY_GRAPH_HINTS_FILENAME = "DEPENDENCY_GRAPH_HINTS.json"

DEFAULT_INCLUDE_GLOBS = [
    "pyproject.toml",
    "dopemux.toml",
    "compose.yml",
    "docker-compose*.yml",
    ".claude/**",
    ".dopemux/**",
    ".taskx/**",
    ".github/**",
    "config/**",
    "scripts/**",
    "tools/**",
    "compose/**",
    "docker/**",
    "services/**",
    "shared/**",
    "plugins/**",
    "src/**",
    "tests/**",
    "docs/**",
    "AGENTS.md",
    "README.md",
    "QUICK_START.md",
    "INSTALL.md",
    "CHANGELOG.md",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "requirements.txt",
    "uv.lock",
]

DEFAULT_EXCLUDE_GLOBS = [
    "**/.git/**",
    "**/.venv/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.DS_Store",
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.webp",
    "**/*.gif",
    "**/*.pdf",
    "**/*.zip",
    "**/*.log",
]

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".php",
    ".rb",
    ".sh",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".sql",
}

LANGUAGE_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".sh": "shell",
    ".sql": "sql",
    ".md": "markdown",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
}


@dataclass(frozen=True)
class ScanConfig:
    max_files: int = 2000
    include_globs: Tuple[str, ...] = tuple(DEFAULT_INCLUDE_GLOBS)
    exclude_globs: Tuple[str, ...] = tuple(DEFAULT_EXCLUDE_GLOBS)
    top_dirs_limit: int = 25


def deterministic_generated_at(run_id: str) -> str:
    seed = int(hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8], 16)
    return datetime.fromtimestamp(seed, timezone.utc).replace(microsecond=0).isoformat()


def _relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _matches_exclude(relpath: str, name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(relpath, pat) or fnmatch.fnmatch(name, pat) for pat in patterns)


def _read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_bytes()[:limit].decode("utf-8", errors="ignore")
    except Exception:
        return ""


def select_files(root: Path, cfg: ScanConfig) -> List[Dict[str, Any]]:
    selected: Dict[str, Dict[str, Any]] = {}
    for include_glob in cfg.include_globs:
        for candidate in sorted(root.glob(include_glob), key=lambda p: p.as_posix()):
            if not candidate.is_file():
                continue
            try:
                rel = _relpath(candidate, root)
            except Exception:
                continue
            if _matches_exclude(rel, candidate.name, cfg.exclude_globs):
                continue
            if rel in selected:
                continue
            try:
                st = candidate.stat()
            except Exception:
                continue
            selected[rel] = {
                "path": candidate,
                "relpath": rel,
                "size": int(st.st_size),
                "suffix": candidate.suffix.lower(),
                "name": candidate.name,
            }
    rows = [selected[key] for key in sorted(selected)]
    if cfg.max_files > 0:
        rows = rows[: cfg.max_files]
    return rows


def _size_bucket(size: int) -> str:
    if size <= 1_024:
        return "le_1kb"
    if size <= 10_240:
        return "le_10kb"
    if size <= 102_400:
        return "le_100kb"
    if size <= 1_048_576:
        return "le_1mb"
    return "gt_1mb"


def _path_clusters(rows: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    clusters: Dict[str, Dict[str, int]] = defaultdict(lambda: {"files": 0, "bytes": 0})
    for row in rows:
        rel = str(row["relpath"])
        top = rel.split("/", 1)[0]
        clusters[top]["files"] += 1
        clusters[top]["bytes"] += int(row["size"])
    ranked = sorted(
        (
            {"path": path, "file_count": stats["files"], "total_bytes": stats["bytes"]}
            for path, stats in clusters.items()
        ),
        key=lambda x: (-int(x["file_count"]), -int(x["total_bytes"]), str(x["path"])),
    )
    return ranked[: max(1, top_n)]


def _build_surface(rows: List[Dict[str, Any]], root: Path, generated_at: str, run_id: str) -> Dict[str, Any]:
    relpaths = [str(row["relpath"]) for row in rows]
    present = set(relpaths)

    def pick(patterns: Iterable[str]) -> List[str]:
        out = []
        for rel in relpaths:
            if any(fnmatch.fnmatch(rel, pattern) for pattern in patterns):
                out.append(rel)
        return sorted(set(out))

    lockfiles = pick(["*lock*.json", "*lock*.yaml", "*lock", "poetry.lock", "uv.lock", "go.sum", "Cargo.lock"])
    build_files = pick([
        "pyproject.toml",
        "requirements*.txt",
        "package.json",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle*",
        "Makefile",
    ])
    dockerfiles = pick(["**/Dockerfile*", "compose.yml", "docker-compose*.yml"])
    ci_configs = pick([".github/workflows/*.yml", ".github/workflows/*.yaml"])

    build_systems = []
    if "pyproject.toml" in present:
        build_systems.append("python_pyproject")
    if "package.json" in present:
        build_systems.append("node_package_json")
    if "go.mod" in present:
        build_systems.append("go_modules")
    if "Cargo.toml" in present:
        build_systems.append("rust_cargo")

    return {
        "version": "BUILD_SURFACE_V1",
        "generated_at": generated_at,
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "build_systems": sorted(build_systems),
        "build_files": build_files,
        "lockfiles": lockfiles,
        "ci_configs": ci_configs,
        "dockerfiles": dockerfiles,
    }


def _entrypoint_candidates(rows: List[Dict[str, Any]], root: Path, generated_at: str, run_id: str) -> Dict[str, Any]:
    candidates: List[Dict[str, str]] = []
    for row in rows:
        rel = str(row["relpath"])
        suffix = str(row["suffix"])

        if rel.endswith("pyproject.toml"):
            text = _read_text(root / rel)
            if "[project.scripts]" in text:
                candidates.append({"path": rel, "kind": "python_console_scripts", "signal": "[project.scripts]"})

        if suffix == ".py":
            text = _read_text(root / rel)
            if "if __name__ == \"__main__\"" in text:
                candidates.append({"path": rel, "kind": "python_main_module", "signal": "__main__"})
            if "typer.Typer(" in text or "@click.command" in text:
                candidates.append({"path": rel, "kind": "python_cli", "signal": "click_or_typer"})

        if rel.endswith("package.json"):
            text = _read_text(root / rel)
            try:
                payload = json.loads(text)
            except Exception:
                payload = {}
            if isinstance(payload, dict):
                if payload.get("bin"):
                    candidates.append({"path": rel, "kind": "node_bin", "signal": "package.json#bin"})
                scripts = payload.get("scripts")
                if isinstance(scripts, dict) and any(k in scripts for k in ["start", "dev", "serve"]):
                    candidates.append({"path": rel, "kind": "node_scripts", "signal": "package.json#scripts"})

    dedup = {(row["path"], row["kind"], row["signal"]): row for row in candidates}
    ordered = [dedup[key] for key in sorted(dedup)]
    return {
        "version": "ENTRYPOINT_CANDIDATES_V1",
        "generated_at": generated_at,
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "candidates": ordered,
    }


def _dependency_hints(rows: List[Dict[str, Any]], root: Path, generated_at: str, run_id: str) -> Dict[str, Any]:
    relpaths = [str(row["relpath"]) for row in rows]

    node_workspaces: List[str] = []
    if "package.json" in relpaths:
        text = _read_text(root / "package.json")
        try:
            payload = json.loads(text)
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            ws = payload.get("workspaces")
            if isinstance(ws, list):
                node_workspaces = sorted(str(item) for item in ws if str(item).strip())
            elif isinstance(ws, dict):
                pkgs = ws.get("packages")
                if isinstance(pkgs, list):
                    node_workspaces = sorted(str(item) for item in pkgs if str(item).strip())

    python_roots = sorted({rel.split("/", 1)[0] for rel in relpaths if rel.endswith(".py")})
    node_roots = sorted({rel.split("/", 1)[0] for rel in relpaths if rel.endswith((".js", ".ts", ".tsx", ".jsx"))})

    return {
        "version": "DEPENDENCY_GRAPH_HINTS_V1",
        "generated_at": generated_at,
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "lockfiles": sorted(
            rel
            for rel in relpaths
            if rel.endswith(("lock", "lock.json", "lock.yaml")) or rel in {"poetry.lock", "uv.lock", "go.sum", "Cargo.lock"}
        ),
        "workspace_hints": {
            "node_workspaces": node_workspaces,
            "python_source_roots": python_roots,
            "node_source_roots": node_roots,
            "go_modules": sorted(rel for rel in relpaths if rel.endswith("go.mod")),
            "cargo_workspaces": sorted(rel for rel in relpaths if rel.endswith("Cargo.toml")),
        },
    }


def build_stage0_artifacts(root: Path, run_id: str, cfg: ScanConfig | None = None) -> Dict[str, Dict[str, Any]]:
    config = cfg or ScanConfig()
    rows = select_files(root, config)
    generated_at = deterministic_generated_at(run_id)

    size_hist = Counter()
    ext_counts = Counter()
    lang_counts = Counter()
    total_bytes = 0
    files_hash_lines: List[str] = []

    for row in rows:
        size = int(row["size"])
        suffix = str(row["suffix"])
        rel = str(row["relpath"])
        total_bytes += size
        size_hist[_size_bucket(size)] += 1
        if suffix:
            ext_counts[suffix] += 1
        lang = LANGUAGE_BY_EXT.get(suffix)
        if lang:
            lang_counts[lang] += 1
        try:
            digest = sha256_bytes((root / rel).read_bytes())
        except Exception:
            digest = "UNREADABLE"
        files_hash_lines.append(f"{rel}:{digest}")

    fingerprint = {
        "version": "REPO_FINGERPRINT_V1",
        "generated_at": generated_at,
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "totals": {
            "total_files": len(rows),
            "total_bytes": total_bytes,
        },
        "filetype_counts": dict(sorted(ext_counts.items())),
        "language_counts": dict(sorted(lang_counts.items())),
        "size_histogram": dict(sorted(size_hist.items())),
        "path_clusters": _path_clusters(rows, config.top_dirs_limit),
        "selected_files_set_sha256": sha256_bytes("\n".join(sorted(files_hash_lines)).encode("utf-8")),
    }

    return {
        REPO_FINGERPRINT_FILENAME: fingerprint,
        BUILD_SURFACE_FILENAME: _build_surface(rows, root, generated_at, run_id),
        ENTRYPOINT_CANDIDATES_FILENAME: _entrypoint_candidates(rows, root, generated_at, run_id),
        DEPENDENCY_GRAPH_HINTS_FILENAME: _dependency_hints(rows, root, generated_at, run_id),
    }
