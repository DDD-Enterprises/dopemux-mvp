#!/usr/bin/env python3
"""
Orphan file analyzer and cleanup utility for this repository.

Finds and optionally removes common orphan artifacts:
- .DS_Store files
- __pycache__ directories and *.pyc files
- Coverage artifacts (.coverage, htmlcov/)
- Build/packaging leftovers (*.egg-info)
- Temp/embeddings/test .db files in repo root
- Known temp dirs (e.g., tmp-doc-ingest)

Also reports Python modules under src/ not referenced by imports elsewhere
(heuristic only; does not delete code by default).

Usage:
  Dry run (default):
    python scripts/orphan_cleanup.py

  Apply deletions for safe artifacts only:
    python scripts/orphan_cleanup.py --apply

  Include module deletion (NOT recommended; report-only by default):
    python scripts/orphan_cleanup.py --apply --delete-modules
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_rg(pattern: str, paths: Iterable[Path]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            [
                "rg",
                "-n",
                "-S",
                "-g",
                "!**/.git/**",
                "-g",
                "!**/.venv/**",
                pattern,
                *[str(p) for p in paths],
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", "ripgrep (rg) not found in PATH"


def find_paths(patterns: List[str]) -> List[Path]:
    matches: Set[Path] = set()
    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip common heavy/irrelevant dirs
        parts = Path(root).parts
        if any(
            p in {".git", "node_modules", "dist", "build", ".next", ".nuxt"}
            for p in parts
        ) or any(
            # skip any virtualenv-like or site-packages paths
            re.search(r"(^|\.)venv|_venv|site-packages", p, re.I) for p in parts
        ):
            continue

        for f in files:
            fp = Path(root) / f
            for pat in patterns:
                if pat == ".DS_Store" and f == ".DS_Store":
                    matches.add(fp)
                elif pat == "*.pyc" and f.endswith(".pyc"):
                    matches.add(fp)
                elif pat == ".coverage" and f == ".coverage" and Path(root) == REPO_ROOT:
                    matches.add(fp)
                elif pat == "*.db-root" and Path(root) == REPO_ROOT and f.endswith(".db"):
                    # Restrict to known temp/test/embedding DBs
                    if re.search(r"(milvus|embedding)", f, re.I) or f.startswith("dopemux_"):
                        matches.add(fp)
        # Directories
        for d in list(dirs):
            dp = Path(root) / d
            if d == "__pycache__":
                matches.add(dp)
            if d.endswith(".egg-info") and "src" in dp.parts:
                matches.add(dp)
            if d == "htmlcov" and Path(root) == REPO_ROOT:
                matches.add(dp)
            if d == "tmp-doc-ingest" and Path(root) == REPO_ROOT:
                matches.add(dp)
    return sorted(matches)


@dataclass
class AnalysisReport:
    ds_store: List[Path] = field(default_factory=list)
    pycache: List[Path] = field(default_factory=list)
    pyc_files: List[Path] = field(default_factory=list)
    coverage: List[Path] = field(default_factory=list)
    egg_info: List[Path] = field(default_factory=list)
    temp_dbs: List[Path] = field(default_factory=list)
    temp_dirs: List[Path] = field(default_factory=list)
    unreferenced_modules: List[Path] = field(default_factory=list)


def find_unreferenced_modules() -> List[Path]:
    src_root = REPO_ROOT / "src"
    if not src_root.exists():
        return []

    # Collect python files under src excluding __init__.py and archived paths
    candidates: List[Tuple[str, Path]] = []
    for p in src_root.rglob("*.py"):
        if p.name == "__init__.py":
            continue
        # Skip archived folders
        if any(part == "archived" for part in p.parts):
            continue
        # Build module path like dopemux.pkg.mod
        try:
            rel = p.relative_to(src_root)
        except ValueError:
            continue
        mod = ".".join(("dopemux",) + rel.with_suffix("").parts)
        candidates.append((mod, p))

    # Search references for each module
    unref: List[Path] = []
    search_paths = [REPO_ROOT / "src", REPO_ROOT / "scripts", REPO_ROOT / "tests"]
    for mod, path in candidates:
        pattern = rf"\b(import\s+{re.escape(mod)}\b|from\s+{re.escape(mod)}\b)"
        code, out, err = run_rg(pattern, search_paths)
        if code == 127:
            # rg missing — skip analysis
            return []
        if code != 0 or not out.strip():
            # No references found
            unref.append(path)
    return unref


def analyze() -> AnalysisReport:
    rep = AnalysisReport()
    paths = find_paths([
        ".DS_Store",
        "*.pyc",
        ".coverage",
        "*.db-root",
    ])

    for p in paths:
        if p.is_dir():
            if p.name == "__pycache__":
                rep.pycache.append(p)
            elif p.name.endswith(".egg-info"):
                rep.egg_info.append(p)
            elif p.name == "htmlcov":
                rep.coverage.append(p)
            elif p.name == "tmp-doc-ingest":
                rep.temp_dirs.append(p)
        else:
            if p.name == ".DS_Store":
                rep.ds_store.append(p)
            elif p.suffix == ".pyc":
                rep.pyc_files.append(p)
            elif p.name == ".coverage":
                rep.coverage.append(p)
            elif p.suffix == ".db":
                rep.temp_dbs.append(p)

    rep.unreferenced_modules = find_unreferenced_modules()
    return rep


def delete_path(p: Path) -> None:
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
    else:
        try:
            p.unlink(missing_ok=True)
        except TypeError:
            # Python <3.8 compatibility not required here, but keep safe
            if p.exists():
                p.unlink()


def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze and clean orphan files")
    ap.add_argument("--apply", action="store_true", help="Apply safe deletions")
    ap.add_argument(
        "--delete-modules",
        action="store_true",
        help="Also delete unreferenced modules (NOT recommended)",
    )
    args = ap.parse_args()

    rep = analyze()

    def rels(paths: List[Path]) -> List[str]:
        return [str(p.relative_to(REPO_ROOT)) for p in sorted(paths)]

    print("Orphan analysis summary:\n")
    print(f".DS_Store files: {len(rep.ds_store)}")
    for s in rels(rep.ds_store):
        print(f"  - {s}")
    print(f"__pycache__ dirs: {len(rep.pycache)}")
    for s in rels(rep.pycache):
        print(f"  - {s}")
    print(f"*.pyc files: {len(rep.pyc_files)}")
    for s in rels(rep.pyc_files):
        print(f"  - {s}")
    print(f"Coverage artifacts: {len(rep.coverage)}")
    for s in rels(rep.coverage):
        print(f"  - {s}")
    print(f"*.egg-info dirs: {len(rep.egg_info)}")
    for s in rels(rep.egg_info):
        print(f"  - {s}")
    print(f"Temp/embeddings/test .db files (root): {len(rep.temp_dbs)}")
    for s in rels(rep.temp_dbs):
        print(f"  - {s}")
    print(f"Temp dirs: {len(rep.temp_dirs)}")
    for s in rels(rep.temp_dirs):
        print(f"  - {s}")
    print(f"Unreferenced Python modules (heuristic): {len(rep.unreferenced_modules)}")
    for s in rels(rep.unreferenced_modules):
        print(f"  - {s}")

    if not args.apply:
        print("\nDry run only. Use --apply to remove safe artifacts.")
        return

    print("\nApplying safe deletions (no code modules):")
    to_delete = (
        rep.ds_store
        + rep.pycache
        + rep.pyc_files
        + rep.coverage
        + rep.egg_info
        + rep.temp_dbs
        + rep.temp_dirs
    )
    for p in to_delete:
        print(f"  deleting {p}")
        delete_path(p)

    if args.delete_modules and rep.unreferenced_modules:
        print("\nDeleting unreferenced modules as requested:")
        for p in rep.unreferenced_modules:
            print(f"  deleting {p}")
            delete_path(p)

    print("\nCleanup complete.")


if __name__ == "__main__":
    main()
